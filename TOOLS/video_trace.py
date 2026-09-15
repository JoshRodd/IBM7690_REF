#!/usr/bin/env python3
"""Execute preserved COLORFIX/LCD diagnostic code and a Model25 font-code extract.

Requires unicorn==2.1.4. Synthetic BIOS/DOS and LCD diagnostic-RAM boundaries,
not target-ROM boot, real LCD hardware, timing, scanout, or a complete DGS pass.
The 107-byte font window is explicitly comparative Model25 code, not 7690 ROM.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

import unicorn
from unicorn import x86_const as x86

ROOT = Path(__file__).resolve().parents[1]
FONT_ROM_SHA = "cfbdc2cd67c95c15b06be14e2e5f4bbd6991f3506428af64038b6381a1120166"
FONT_WINDOW = bytes.fromhex(
    "061f52ba00a08ec25a51530adb740e528cc281c20002fecb75f88ec25a8ac72ae452"
    "d1e28bfa8bf38bdd5a83f9007503e9ad00518bc85357268815478a372688354381c7"
    "ff01e2f03c0e7510b902002688154726883581c7ff01e2f35f83c7025b03d8fec259"
    "e2cb5b59c3"
)
SOURCES = {
    "colorfix": ("7690diag/COLORFIX.COM", "21f47f663254e2a08dde514d4741a291605f2eefa31fea6fda26c1c8ee912028"),
    "loose": ("7690diag/IBM7690.DGS", "e44671fa1565793365a748743e364b4be4027c12f012b9b687c8047b2459fa57"),
    "image": ("ANALYSIS/7690KQPW/IBM7690.DGS", "be20cd798aef2f63d4c094bf71ebf02376b53fc31011e80a0d8595fa5a3fe4f4"),
}


class Fixture:
    def __init__(self, image, segment=0x2000, origin=0):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_X86, unicorn.UC_MODE_16)
        self.uc.mem_map(0, 0x100000)
        self.segment = segment
        self.uc.mem_write(segment * 16 + origin, image)
        self.stop = segment * 16 + 0xFF00
        # Terminate translation too: zero-filled high ROM can prefetch beyond1MiB
        # before the code hook gets to stop at the synthetic return address.
        self.uc.mem_write(self.stop, b"\xf4")
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self.code)

    def code(self, uc, address, size, _):
        self.instructions += 1
        if address == self.stop:
            self.finished = True
            uc.emu_stop()

    def run(self, entry, **registers):
        self.finished = False
        self.instructions = 0
        defaults = dict(ax=0, bx=0, cx=0, dx=0, si=0, di=0, bp=0,
                        cs=self.segment, ds=self.segment, es=self.segment,
                        ss=0x9000, sp=0xFF00, eflags=0x202)
        defaults.update(registers)
        for name, value in defaults.items():
            self.uc.reg_write(getattr(x86, "UC_X86_REG_" + name.upper()), value)
        self.uc.mem_write(0x9FF00, struct.pack("<H", 0xFF00))
        self.uc.emu_start(self.segment * 16 + entry, 0, count=1_000_000)
        if not self.finished:
            raise RuntimeError(f"Instruction budget exhausted at entry {entry:04X}")
        return {name: self.uc.reg_read(getattr(x86, "UC_X86_REG_" + name.upper()))
                for name in ("ax", "bx", "cx", "dx", "eflags")}


def colorfix(image):
    rig = Fixture(image, origin=0x100)
    events = []
    rig.uc.mem_write(0x40, struct.pack("<HH", 0xFF00, 0x8000))
    rig.uc.mem_write(0x496, b"\xff")
    rig.uc.mem_write(0x489, b"\xff")

    def interrupt(uc, number, _):
        ax = uc.reg_read(x86.UC_X86_REG_AX)
        dx = uc.reg_read(x86.UC_X86_REG_DX)
        ds = uc.reg_read(x86.UC_X86_REG_DS)
        if number == 0x21 and ax >> 8 == 9:
            data = bytes(uc.mem_read(ds * 16 + dx, 512)).split(b"$", 1)[0]
            events.append({"dos": "AH09", "text": data.decode("ascii")})
        elif number == 0x21 and ax == 0x2510:
            uc.mem_write(0x40, struct.pack("<HH", dx, ds))
            events.append({"dos": "AX2510", "vector": f"{ds:04X}:{dx:04X}"})
        elif number == 0x27:
            events.append({"dos": "INT27", "resident_end": f"{dx:04X}"})
            rig.finished = True
            uc.emu_stop()
        else:
            raise RuntimeError(f"Unexpected interrupt {number:02X}, AX={ax:04X}")

    rig.uc.hook_add(unicorn.UC_HOOK_INTR, interrupt)
    rig.run(0x158)
    assert bytes(rig.uc.mem_read(0x496, 1)) == b"\xef"
    assert bytes(rig.uc.mem_read(0x489, 1)) == b"\xff"
    rig.stop = 0x8FF00  # Stop on entry to the saved old INT10, not a BIOS implementation.
    outputs = []
    for attribute in range(256):
        result = rig.run(0x124, ax=0x0941, bx=0x0200 | attribute)
        outputs.append(result["bx"] & 255)
        expected = attribute
        if (attribute & 15) != (attribute >> 4) and (attribute & 1) == ((attribute >> 4) & 1):
            expected ^= 1
        assert result["bx"] == 0x0200 | expected
    other_functions = {}
    for ah in (0, 1, 8, 0x0A, 0x0E, 0x11, 0x13, 0xFF):
        result = rig.run(0x124, ax=ah << 8, bx=0x0217)
        assert result["bx"] == 0x0217
        other_functions[f"{ah:02X}"] = f"{result['bx']:04X}"
    return {"events": events, "all_256_outputs_hex": [f"{n:02X}" for n in outputs],
            "changed": sum(a != b for a, b in enumerate(outputs)),
            "other_ah_bx": other_functions, "bda_0096": "EF", "bda_0089": "FF",
            "boundary": "DOS calls intercepted; stops at old INT10 entry; no video rendering"}


def font_staging():
    observations = []
    for height in (16, 14):
        rig = Fixture(FONT_WINDOW, segment=0xF000, origin=0x23A0)
        rig.uc.mem_write(0x30000, bytes(range(0x40, 0x40 + height * 3)))
        rig.run(0x23A0, es=0x3000, bp=0, bx=(height << 8) | 2, cx=3, dx=0x41)
        rows = []
        for row in range(16):
            address = 0xA0000 + 2 * 0x2000 + row * 0x200 + 0x41 * 2
            data = bytes(rig.uc.mem_read(address, 6))
            expected = bytes(value for glyph in range(3) for value in
                             (0x41 + glyph, 0x40 + glyph * height + min(row, height - 1)))
            assert data == expected
            rows.append({"row": row, "address": f"{address:05X}", "bytes": data.hex(" ")})
        observations.append({"height": height, "block": 2, "first_character": "41",
                             "characters": 3, "rows": rows, "instructions": rig.instructions})
    return {"source_rom_sha256": FONT_ROM_SHA, "source_offset": "23A0",
            "window_bytes": len(FONT_WINDOW), "window_sha256": hashlib.sha256(FONT_WINDOW).hexdigest(),
            "window_hex": FONT_WINDOW.hex(), "observations": observations,
            "boundary": "107 unchanged Model25 bytes; 3glyph input; staging only, no font-transfer engine or 7690 ROM"}


class DiagnosticRam(Fixture):
    """Literal row/column fixture, not a hardware decoder assertion."""
    def __init__(self, image, column_mask=255):
        super().__init__(image)
        self.index = self.row = self.column = 0
        self.column_mask = column_mask
        self.ram = {}
        self.transactions = []
        self.reads = []
        self.uc.hook_add(unicorn.UC_HOOK_INSN, self.input, None, 1, 0, x86.UC_X86_INS_IN)
        self.uc.hook_add(unicorn.UC_HOOK_INSN, self.output, None, 1, 0, x86.UC_X86_INS_OUT)

    def input(self, uc, port, size, _):
        assert size == 1
        if port == 0:
            return 0  # Discarded bus-delay read, not a DMA model.
        if port == 0xF304:
            return self.index
        if port == 0xF305 and self.index in (6, 7):
            key = (self.index, self.row, self.column)
            self.reads.append(key)
            return self.ram.get(key, 0)
        raise RuntimeError(f"Unexpected IN {port:04X}, index {self.index:02X}")

    def output(self, uc, port, size, value, _):
        assert size == 1
        if port == 0xF304:
            self.index = value
            return
        if port != 0xF305:
            raise RuntimeError(f"Unexpected OUT {port:04X}")
        self.transactions.append((self.index, value))
        if self.index == 4:
            self.column = value & self.column_mask
        elif self.index == 5:
            self.row = value
        elif self.index in (6, 7):
            self.ram[(self.index, self.row, self.column)] = value
        else:
            raise RuntimeError(f"Unexpected LCD data index {self.index:02X}")


def diagnostic_ram(images):
    observations = []
    for name, delta in (("loose", 0), ("image", 0x460)):
        rig = DiagnosticRam(images[name])
        rig.run(0x1460 + delta, si=0x55, di=0xAA)
        counts = Counter(index for index, value in rig.transactions)
        assert counts == {5: 128, 4: 8192, 6: 8192, 7: 8192}
        fill = {"counts": {f"{k:02X}": v for k, v in counts.items()},
                "first": rig.transactions[:10], "last": rig.transactions[-10:]}
        constant_good = rig.run(0x1552 + delta, si=0x55, di=0xAA)
        assert not constant_good["eflags"] & 1
        rig.ram[(6, 128, 64)] ^= 1
        constant_bad = rig.run(0x1552 + delta, si=0x55, di=0xAA)
        assert constant_bad["eflags"] & 1
        rig.run(0x14A1 + delta)
        address_good = rig.run(0x14E2 + delta)
        assert not address_good["eflags"] & 1
        rig.ram[(7, 128, 64)] ^= 1
        address_bad = rig.run(0x14E2 + delta)
        assert address_bad["eflags"] & 1
        aliased = DiagnosticRam(images[name], column_mask=0x3F)
        aliased.run(0x14A1 + delta)
        alias_result = aliased.run(0x14E2 + delta)
        assert alias_result["eflags"] & 1
        observations.append({"source": name, "offset_delta": f"{delta:04X}", "fill": fill,
                             "constant_good": constant_good, "constant_corrupt_upper": constant_bad,
                             "address_good": address_good, "address_corrupt_lower": address_bad,
                             "six_bit_column_alias_failure": alias_result})
    return {"fixture": "Full byte index/row/column latches; separate dictionaries for ports06/07; writes at column0 are real fixture writes; no timing or LCD scanout",
            "observations": observations,
            "alias_conclusion": "A simple6-bit column mask plus literal RAM writes fails because verifier writes zero at column0 before reading column64. This does not prove the real decoder is8bits; pipeline/strobe semantics remain OPEN.",
            "boundary": "Only original fill and verification routines; not orchestrator, sync/reset/readback, adapter BIOS or full DGS suite"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model25-rom", type=Path, help="Optionally verify retained window against the full original comparative ROM")
    args = parser.parse_args()
    images = {}
    for name, (path, digest) in SOURCES.items():
        images[name] = (ROOT / path).read_bytes()
        if hashlib.sha256(images[name]).hexdigest() != digest:
            raise RuntimeError(f"Source hash mismatch: {path}")
    if args.model25_rom:
        image = args.model25_rom.read_bytes()
        assert hashlib.sha256(image).hexdigest() == FONT_ROM_SHA
        assert image[0x23A0:0x240B] == FONT_WINDOW
    report = {"schema": "ibm7690.video-trace.v1", "engine": f"Unicorn {unicorn.__version__}",
              "scope": "Original-instruction experiments with synthetic devices, not target hardware execution",
              "sources": {name: {"path": path, "sha256": digest} for name, (path, digest) in SOURCES.items()},
              "colorfix": colorfix(images["colorfix"]), "font_staging": font_staging(),
              "lcd_diagnostic_ram": diagnostic_ram(images)}
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
        print(f"Executed preserved video routines; evidence: {args.output}")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
