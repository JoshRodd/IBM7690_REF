#!/usr/bin/env python3
"""Execute preserved LEDTOUCH instructions against explicit synthetic inputs.

Research fixture, NOT an IBM 7690 emulator or electrical/timing model.
Run: uv run --with unicorn==2.1.4 python TOOLS/touch_trace.py
Only Unicorn is external. Original driver bytes are never patched.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
import struct

import unicorn
from unicorn import x86_const as x86

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {
    "3.02": {
        "path": "7690diag/LEDTOUCH.SYS",
        "sha256": "bfb95e3a5d1a9ef87742b33b19d33fee2fbcb0718f04995f770b0a3c37d6d2df",
        "scan": 0x0712, "adc": 0x0A9B, "selftest": 0x1DB4,
        "int33": 0x0F3E, "point": 0x043D, "raw_x": 0x0701,
        "raw_y": 0x0703, "bitmap": 0x0626, "usable": 0x0632,
        "timer": 0x0F0A, "old_timer": 0x0E1B,
        "mouse_callback": 0x0C0B,
    },
    "2.4": {
        "path": "ANALYSIS/7690KQPW/LEDTOUCH.SYS",
        "sha256": "1c3dc5a2c4a9c6d422f03f92db6b3bcc2b314939603a117594e9573eb7ee2613",
        "scan": 0x06D3, "adc": 0x09CB, "selftest": 0x19DB,
        "int33": 0x0C99, "point": 0x0429, "raw_x": 0x06CA,
        "raw_y": 0x06CC, "bitmap": 0x05F0, "usable": 0x05FC,
        "timer": 0x0C65, "old_timer": 0x0B76,
    },
}


def selector(index: int) -> int:
    """Driver scan-order index, NOT the two screen coordinate nibbles."""
    if not 0 <= index < 64:
        raise ValueError(index)
    return ((index // 8) << 4) | (index % 8)


class Rig:
    """Minimal real-mode loader, BIOS fixtures, and synthetic optical circuit."""

    BASE = 0x20000
    SEG = BASE >> 4
    STOP = 0xFF00

    def __init__(self, version: str = "3.02"):
        self.profile = PROFILES[version]
        self.version = version
        self.binary = (ROOT / self.profile["path"]).read_bytes()
        digest = hashlib.sha256(self.binary).hexdigest()
        if digest != self.profile["sha256"]:
            raise ValueError(f"Unrecognized driver: {digest}")
        self.uc = unicorn.Uc(unicorn.UC_ARCH_X86, unicorn.UC_MODE_16)
        self.uc.mem_map(0, 0x110000)
        self.uc.mem_write(self.BASE, self.binary)
        self.select_data = self.receiver = self.emitter = self.control = 0
        self.result = 63
        self.consumed = True
        self.blocked: set[int] = set()
        self.dark = 63
        self.lit = 0
        self.interface_present = True
        self.panel_present = True
        self.power_ok = True
        self.result_read_rearms = True
        self.conversion_completes = True
        self.mode = 3
        self.custom_lcd = False
        self.top, self.height, self.panel_height = 0, 400, 480
        self.key_pending = False
        self.io: list[tuple] = []
        self.interrupts: list[tuple] = []
        self.output: list[str] = []
        self.steps = 0
        self.coverage: collections.Counter[int] = collections.Counter()
        self.callbacks: list[dict] = []
        self.uc.mem_write(0x484, bytes([24]))
        self.uc.mem_write(0x449, bytes([self.mode]))
        self.uc.hook_add(unicorn.UC_HOOK_INSN, self._input, None, 1, 0, x86.UC_X86_INS_IN)
        self.uc.hook_add(unicorn.UC_HOOK_INSN, self._output, None, 1, 0, x86.UC_X86_INS_OUT)
        self.uc.hook_add(unicorn.UC_HOOK_INTR, self._interrupt)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._instruction)

    def reg(self, name, value=None):
        register = getattr(x86, "UC_X86_REG_" + name.upper())
        if value is None:
            return self.uc.reg_read(register)
        self.uc.reg_write(register, value)

    def word(self, offset, value=None):
        if value is None:
            return struct.unpack("<H", self.uc.mem_read(self.BASE + offset, 2))[0]
        self.uc.mem_write(self.BASE + offset, struct.pack("<H", value & 0xFFFF))

    def byte(self, offset, value=None):
        if value is None:
            return self.uc.mem_read(self.BASE + offset, 1)[0]
        self.uc.mem_write(self.BASE + offset, bytes([value & 255]))

    def bitmap(self, name="bitmap"):
        return bytes(self.uc.mem_read(self.BASE + self.profile[name], 8)).hex()

    def touch(self, horizontal=(), vertical=()):
        self.blocked = {selector(i) for i in horizontal} | {selector(40 + i) for i in vertical}

    def _input(self, uc, port, size, data):
        if size != 1:
            raise RuntimeError("Unexpected non-byte port access")
        if not self.interface_present and 0xF300 <= port <= 0xF303:
            value = 0xFF  # Explicit absent-bus fixture, not measured bus behavior.
        elif port == 0xF301:
            value = (0 if self.panel_present else 0x80) | (0x40 if self.select_data != 255 else 0)
            value |= 2 | int(self.power_ok)
        elif port == 0xF302:
            value = (self.control & 0xF7) | (8 if self.consumed else 0)
        elif port == 0xF303:
            value = self.result
            if self.result_read_rearms:
                self.consumed = True
        else:
            raise RuntimeError(f"Unmodeled IN {port:04X}")
        self.io.append(("in", self.reg("ip"), port, value, self.receiver, self.emitter))
        return value

    def _output(self, uc, port, size, value, data):
        if size != 1:
            raise RuntimeError("Unexpected non-byte port access")
        self.io.append(("out", self.reg("ip"), port, value, self.receiver, self.emitter))
        if not self.interface_present and 0xF300 <= port <= 0xF303:
            return
        if port == 0xF300:
            self.select_data = value
        elif port == 0xF302:
            # The fixture latches while the strobe is asserted. The drivers pulse
            # high then low; these experiments do not determine physical edge.
            if value & 4:
                self.receiver = self.select_data
            if value & 1:
                self.emitter = self.select_data
            if (self.control & 8) and not (value & 8) and self.conversion_completes:
                illuminated = bool(value & 2) and self.receiver == self.emitter
                illuminated &= self.receiver not in self.blocked
                self.result = self.lit if illuminated else self.dark
                self.consumed = False
            self.control = value
        else:
            raise RuntimeError(f"Unmodeled OUT {port:04X}")

    def _interrupt(self, uc, number, data):
        ax, bx = self.reg("ax"), self.reg("bx")
        self.interrupts.append((number, ax, bx, self.reg("cx"), self.reg("dx")))
        if number == 0x10:
            if ax == 0x11BA:
                if not self.custom_lcd:
                    self.reg("ah", 0)  # Unsupported extension isolates raw geometry.
                else:
                    self.reg("ah", 0xBA)
                    if bx >> 8 == 0:
                        self.reg("bx", self.top)
                        self.reg("cx", self.height)
                        self.reg("di", self.panel_height)
                    elif bx >> 8 == 1:
                        self.top = bx & 255
            elif ax >> 8 == 0x0F:
                self.reg("ax", 0x5000 | self.mode)
                self.reg("bx", 0)
            elif ax >> 8 == 0x0E:
                self.output.append(chr(ax & 255))
            elif ax >> 8 == 0:
                self.mode = ax & 255
                self.uc.mem_write(0x449, bytes([self.mode]))
            elif ax >> 8 in (1, 2):
                pass  # Cursor shape/location fixture; no display rendered.
            else:
                raise RuntimeError(f"Unmodeled INT10 AX={ax:04X}")
        elif number == 0x21:
            if ax >> 8 == 0x25:
                self.uc.mem_write((ax & 255) * 4, struct.pack("<HH", self.reg("dx"), self.reg("ds")))
            elif ax >> 8 == 9:
                address = self.reg("ds") * 16 + self.reg("dx")
                self.output.append(bytes(self.uc.mem_read(address, 1024)).split(b"$", 1)[0].decode("ascii"))
            else:
                raise RuntimeError(f"Unmodeled INT21 AX={ax:04X}")
        elif number == 0x15 and ax in (0xC200, 0xC201, 0xC207):
            self.reg("eflags", self.reg("eflags") & ~1)
            self.reg("ah", 0)  # Explicit successful pointing-device BIOS fixture.
        elif number == 0x16:
            if ax >> 8 == 1:
                self.key_pending = not self.key_pending
                self.reg("eflags", (self.reg("eflags") & ~0x40) | (0 if self.key_pending else 0x40))
            elif ax >> 8 == 0:
                self.reg("ax", 0x1C0D)  # Permit self-test failure prompts to return.
            else:
                raise RuntimeError(f"Unmodeled INT16 AX={ax:04X}")
        else:
            raise RuntimeError(f"Unmodeled INT{number:02X} AX={ax:04X}")

    def _instruction(self, uc, address, size, data):
        self.steps += 1
        self.coverage[address - self.BASE] += 1
        if address == self.BASE + self.STOP:
            self.uc.emu_stop()
        elif address == 0x80000:
            self.callbacks.append({r: self.reg(r) for r in ("ax", "bx", "cx", "dx", "si", "di")})

    def call(self, offset, kind="near", registers=None, stack_words=(), count=5_000_000):
        for name in ("ax", "bx", "cx", "dx", "si", "di", "bp"):
            self.reg(name, 0)
        for name in ("cs", "ds", "es"):
            self.reg(name, self.SEG)
        self.reg("ss", 0x9000)
        self.reg("sp", 0xFF00)
        self.reg("eflags", 2)
        frame = [self.STOP]
        if kind in ("far", "iret"):
            frame.append(self.SEG)
        if kind == "iret":
            frame.append(0x202)
        frame.extend(stack_words)
        self.uc.mem_write(0x9FF00, struct.pack("<" + "H" * len(frame), *frame))
        for name, value in (registers or {}).items():
            self.reg(name, value)
        before = self.steps
        self.uc.emu_start(self.BASE + offset, self.BASE + self.STOP + 1, count=count)
        if self.reg("cs") != self.SEG or self.reg("ip") != self.STOP:
            raise RuntimeError(f"No return: {self.reg('cs'):04X}:{self.reg('ip'):04X}")
        return {r: self.reg(r) for r in ("ax", "bx", "cx", "dx", "si", "di", "es")} | {"instructions": self.steps - before}

    def mouse(self, function, **registers):
        return self.call(self.profile["int33"], "iret", {"ax": function, **registers})

    def raw(self):
        result = self.call(self.profile["scan"])
        return {"xy": [self.word(self.profile["raw_x"]), self.word(self.profile["raw_y"])],
                "bitmap": self.bitmap(), "instructions": result["instructions"]}

    def point(self):
        self.call(self.profile["point"])
        return bytes(self.uc.mem_read(self.BASE + 0x281, self.word(0x27D))).decode("ascii")


class ChangingOpticalPathRig(Rig):
    """Canonical path22 fails; neighboring receiver21 works once, then fades."""

    def __init__(self, version):
        self.neighbor_samples = []
        super().__init__(version)

    def _output(self, uc, port, size, value, data):
        conversion = port == 0xF302 and (self.control & 8) and not (value & 8)
        super()._output(uc, port, size, value, data)
        if conversion and value & 2 and self.conversion_completes:
            if self.receiver == self.emitter == 0x22:
                self.result = self.dark
            if self.receiver == 0x21 and self.emitter == 0x22:
                self.result = self.lit if not self.neighbor_samples else self.dark
                self.neighbor_samples.append(self.result)


def run_experiments():
    report = {
        "schema_version": 1,
        "scope": "Actual preserved driver instructions with synthetic optical and BIOS fixtures; not full-machine, DOS boot, real hardware, or cycle timing verification.",
        "engine": {"name": "Unicorn", "version": unicorn.__version__},
        "fixtures": {"dark_adc": 63, "illuminated_adc": 0,
                     "adc_completion": "immediate on start-pulse falling edge; result read reasserts not-ready",
                     "lcd_extension": "unsupported except explicitly identified crop scenario",
                     "text_mode": 3, "bda_rows_minus_one": 24},
        "profiles": {},
    }
    for version in PROFILES:
        rig = Rig(version)
        selftest = rig.call(rig.profile["selftest"])
        assert "Test complete - OK" in "".join(rig.output)
        rig.raw()  # Calibrate untouched before introducing artificial contacts.
        rows = []
        for xs, ys in [([0], [0]), ([39], [23]), ([18], [11]), ([18, 19], [11, 12]),
                       ([0, 1], [0, 1]), ([38, 39], [22, 23]), ([2, 5], [3, 6]),
                       ([2, 18], [3, 20]), ([18], []), ([], [11]), ([], [])]:
            rig.touch(xs, ys)
            rows.append({"x_beams": xs, "y_beams": ys, **rig.raw()})
        assert rows[2]["xy"] == [4572, 4774]
        assert rows[3]["xy"] == [4699, 4991]
        assert rows[-1]["xy"] == [65535, 65535]
        axis = []
        for dimension, length in (("x", 40), ("y", 24)):
            for index in range(length):
                rig.touch([index] if dimension == "x" else [18], [index] if dimension == "y" else [11])
                xy = rig.raw()["xy"]
                assert xy[0 if dimension == "x" else 1] == 2 * index * (127 if dimension == "x" else 217)
                axis.append({"axis": dimension, "beam": index, "xy": xy})
        rig.touch()
        rig.mouse(0)
        rig.mouse(3)  # Reset can request another untouched calibration.
        api = []
        for xs, ys in [([0], [0]), ([39], [23]), ([18], [11]), ([], [])]:
            rig.touch(xs, ys)
            api.append({"x_beams": xs, "y_beams": ys, "registers": rig.mouse(3), "point": rig.point()})
        report["profiles"][version] = {
            "source": rig.profile["path"], "sha256": rig.profile["sha256"],
            "selftest": {"output": "".join(rig.output), "registers": selftest},
            "calibrated_usable_mask": rig.bitmap("usable"),
            "raw_cases": rows, "single_beam_axis_sweep": axis, "api_cases": api,
            "total_executed_instructions": rig.steps,
            "io_transactions": len(rig.io),
        }
    report["extended_3_02"] = extended_experiments()
    return report


def extended_experiments():
    results = {}
    rig = Rig()
    rig.mouse(0)
    rig.mouse(3)
    rig.mouse(0x59, bx=2, cx=1)
    rig.touch([18], [11])
    press = rig.mouse(3)
    rig.touch()
    release = rig.mouse(3)
    next_poll = rig.mouse(3)
    count = rig.mouse(5, bx=1)
    cleared = rig.mouse(5, bx=1)
    assert [press["bx"], release["bx"], next_poll["bx"]] == [1, 2, 0]
    assert [count["bx"], cleared["bx"]] == [1, 0]
    results["button_following"] = {
        "configured_release_mask": 2, "configured_tracking_mask": 1,
        "touch": press, "first_no_touch": release, "second_no_touch": next_poll,
        "right_press_count": count, "right_press_count_again": cleared,
    }
    rig.mouse(0)
    results["following_survives_reset"] = [rig.byte(0x0E19), rig.byte(0x0E1A)]
    assert results["following_survives_reset"] == [2, 1]

    rig = Rig()
    rig.mouse(0)
    rig.mouse(3)
    rig.uc.mem_write(0x80000, b"\xcb")  # Real FAR RET fixture for guest callback.
    rig.uc.mem_write(0x20, struct.pack("<HH", rig.STOP, rig.SEG))
    rig.mouse(12, cx=0x7F, es=0x8000, dx=0)
    rig.touch([18], [11])
    start = len(rig.io)
    tick1 = rig.call(rig.profile["timer"], "iret")
    after1 = len(rig.io)
    tick2 = rig.call(rig.profile["timer"], "iret")
    after2 = len(rig.io)
    assert after1 == start and after2 > after1
    assert rig.callbacks and rig.callbacks[-1]["cx"] == 292
    results["callback_timer"] = {
        "first_tick": tick1, "second_tick": tick2,
        "first_tick_io": after1 - start, "second_tick_io": after2 - after1,
        "callback_registers": rig.callbacks,
        "installed_int08": bytes(rig.uc.mem_read(0x20, 4)).hex(),
    }

    faults = []
    for version in PROFILES:
        for attribute in ("result_read_rearms", "conversion_completes"):
            rig = Rig(version)
            setattr(rig, attribute, False)
            rig.call(rig.profile["selftest"])
            assert "Touch Panel Needs Service" in "".join(rig.output)
            faults.append({
                "version": version, "fixture_change": attribute + "=False",
                "output": "".join(rig.output),
                "error_string_offset_si": rig.reg("si"),
                "port_transactions": len(rig.io),
            })
    results["adc_failure_paths"] = faults

    rig = Rig()
    rig.interface_present = False
    rig.call(rig.profile["selftest"])
    assert "using IBM mouse" in "".join(rig.output)
    rig.mouse(0)
    rig.mouse(3)
    rig.call(rig.profile["mouse_callback"], "far", stack_words=[0, 2, 4, 0])
    for _ in range(12):
        position = rig.mouse(3)
    assert [position["cx"], position["dx"]] == [326, 99]
    results["absent_interface_mouse_fallback"] = {
        "output": "".join(rig.output), "injected_packet": {"status": 0, "dx": 4, "dy": 2},
        "bios_int15_calls": [r for r in rig.interrupts if r[0] == 0x15],
        "position_after_quiet_countdown": position,
    }

    rig = Rig()
    rig.mouse(0)
    rig.mouse(3)
    rig.touch([18], [11])
    modifiers = []
    for flags in (0, 4, 8, 2, 14):
        rig.uc.mem_write(0x417, bytes([flags]))
        modifiers.append({"bda_417": flags, "buttons": rig.mouse(3)["bx"]})
    assert [r["buttons"] for r in modifiers] == [0, 1, 2, 4, 7]
    results["keyboard_buttons"] = modifiers

    rig = Rig()
    rig.mouse(0)
    rig.mouse(3)
    rig.mouse(7, cx=10, dx=10)
    rig.touch([0], [0])
    position = rig.mouse(3)
    assert position["cx"] == 11
    results["equal_horizontal_bounds"] = {
        "requested_min": 10, "requested_max": 10, "observed_position": position,
        "interpretation": "Driver max clamp is followed by <=min then min+1; not corrected by fixture.",
    }

    rig = Rig()
    rig.mouse(0)
    rig.mouse(3)
    rig.uc.mem_write(0x417, bytes([4]))
    rig.touch([18], [11])
    rig.mouse(3)
    rig.touch([20], [12])
    position = rig.mouse(5, bx=0)
    assert [position["bx"], position["cx"], position["dx"]] == [1, 325, 104]
    results["press_information_uses_current_position"] = position

    rig = Rig()
    rig.raw()
    rig.custom_lcd = True
    rig.top, rig.height, rig.panel_height = 40, 400, 480
    rig.touch([18], [11])
    crop = rig.raw()
    results["lcd_crop"] = {
        "bios_bx_top": 40, "bios_cx_active": 400, "bios_di_total": 480,
        "raw_without_crop": [4572, 4774], "with_crop": crop,
    }

    rig = Rig()
    rig.raw()
    rig.touch([18], [11])
    chunks = []
    for requested in (2, 3, 8):
        packet = bytearray(22)
        packet[0], packet[2] = 22, 4
        struct.pack_into("<HHH", packet, 14, 0, 0x7100, requested)
        rig.uc.mem_write(0x70000, bytes(packet))
        rig.call(0x030B, "far", {"es": 0x7000, "bx": 0})
        rig.call(0x0316, "far")
        packet = bytes(rig.uc.mem_read(0x70000, 22))
        returned = struct.unpack_from("<H", packet, 18)[0]
        chunks.append({
            "requested": requested, "returned": returned,
            "request_status": struct.unpack_from("<H", packet, 3)[0],
            "data": bytes(rig.uc.mem_read(0x71000, returned)).decode("ascii"),
        })
    assert "".join(r["data"] for r in chunks) == "1,037,012\r"
    assert [r["returned"] for r in chunks] == [2, 3, 5]
    results["dos_strategy_interrupt_partial_reads"] = chunks

    rig = Rig()
    rig.raw()
    rig.custom_lcd = True
    rig.height = 480
    rig.uc.mem_write(0x484, bytes([29]))
    rig.word(0x0710, 23)
    rig.touch([18], [21])
    record = rig.point()
    assert record == "1,037,028\r"
    results["odd_divisor_rounding"] = {
        "normalized_y": rig.word(0x0703), "rows_minus_one": 29,
        "quotient_remainder": list(divmod(9137 * 29, 9999)), "record": record,
    }
    guards = []
    for version in PROFILES:
        rig = Rig(version)
        rig.raw()
        rig.touch([18], range(8, 16))
        rejected = rig.raw()
        assert rejected["xy"] == [65535, 65535]
        rig.custom_lcd = True
        rig.top, rig.height, rig.panel_height = 0, 100, 480
        rig.touch([18], [11])
        cropped = rig.raw()
        assert cropped["xy"][1] == (4774 if version == "3.02" else 9999)
        guards.append({
            "version": version, "middle_y_byte_ff": rejected,
            "recognized_lcd_height_100": cropped,
        })
    results["versioned_crop_and_broad_occlusion_guards"] = guards

    installations = []
    for version in PROFILES:
        rig = Rig(version)
        packet = bytes([24]) + bytes(23)
        rig.uc.mem_write(0x70000, packet)
        rig.call(0x030B, "far", {"es": 0x7000, "bx": 0})
        rig.call(0x0316, "far")
        packet = bytes(rig.uc.mem_read(0x70000, 24))
        installations.append({
            "version": version, "fixture": "request at7000:0000; INT10 preserves BX",
            "packet_hex": packet.hex(), "request_status": struct.unpack_from("<H", packet, 3)[0],
            "word_at_request_segment_0204": struct.unpack("<H", rig.uc.mem_read(0x70204, 2))[0],
            "installed_int33": bytes(rig.uc.mem_read(0xCC, 4)).hex(),
            "output": "".join(rig.output),
        })
    results["dos_initialization_packet_caveat"] = installations
    calibration = []
    lightpen = []
    for version in PROFILES:
        rig = ChangingOpticalPathRig(version)
        rig.raw()
        emitter_table, receiver_table = (0x063E, 0x067E) if version == "3.02" else (0x0607, 0x0647)
        selected = [rig.byte(emitter_table + 18), rig.byte(receiver_table + 18)]
        assert rig.neighbor_samples[0] == 0 and 63 in rig.neighbor_samples
        assert selected == [0x21, 0x21] and rig.bitmap("usable") == "ffffffffffffffff"
        changing = {"selected_emitter_receiver": selected, "neighbor_samples": rig.neighbor_samples,
                    "usable_mask": rig.bitmap("usable")}
        rig = Rig(version)
        rig.touch([18], [11])
        rig.mouse(0)
        rig.raw()
        masked = rig.bitmap("usable")
        assert masked != "ffffffffffffffff"
        rig.touch()
        rig.mouse(0)
        rig.raw()
        assert rig.bitmap("usable") == masked
        calibration.append({"version": version, "changing_neighbor_path": changing,
                            "obstructed_calibration_usable_mask": masked,
                            "usable_mask_after_clear_input_and_reset": rig.bitmap("usable")})

        rig = Rig(version)
        rig.mouse(0)
        rig.raw()  # Calibrate with a clear bezel before injecting the contact.
        rig.touch([18], [11])
        rig.mouse(13)
        active = rig.mouse(0x58)
        assert active["dx"] >> 8 == (12 if version == "3.02" else 25)
        rig.touch()
        rig.mouse(4, cx=100, dx=0)
        try:
            zero = rig.mouse(0x58)
        except RuntimeError as error:
            if version != "2.4" or not str(error).startswith("Unmodeled INT00"):
                raise
            zero = {"interrupt": "00", "harness_exception": str(error)}
        else:
            assert version == "3.02"
        lightpen.append({"version": version, "active": active,
                         "after_set_position_zero_y_with_no_contact": zero})
    results["calibration_receiver_retention_and_mask_survival"] = calibration
    results["lightpen_version_comparison"] = lightpen
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write JSON evidence instead of stdout")
    args = parser.parse_args()
    report = run_experiments()
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
        print(f"Executed both preserved drivers; evidence: {args.output}")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
