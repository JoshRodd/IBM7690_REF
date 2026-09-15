#!/usr/bin/env python3
"""Execute original CPU0 ROM and clock-rejection paths, not a full module/POST.

Requires unicorn==2.1.4. Synthetic ROM contents and BIOS absence fixtures are
explicit; optional full comparative ROM inputs are read-only and hash-recorded.
"""
import argparse
import hashlib
import json
from pathlib import Path

import unicorn
from unicorn import x86_const as x86

ROOT = Path(__file__).resolve().parents[1]
CPU0_SHA = "8d8943a0fb9bdd6cbd7bb8733387796f3057e1a608a51766927faaf105cabac1"


def execute(module, entry, stops, rom=None, absent_function=None, unstable=False):
    uc = unicorn.Uc(unicorn.UC_ARCH_X86, unicorn.UC_MODE_16)
    uc.mem_map(0, 0x100000)
    uc.mem_write(0x20000, module)
    if rom is not None:
        if len(rom) != 65536:
            raise ValueError("ROM input must contain exactly65536bytes")
        uc.mem_write(0xF0000, rom)
    for register, value in ((x86.UC_X86_REG_CS, 0x2000), (x86.UC_X86_REG_DS, 0x2000),
                            (x86.UC_X86_REG_ES, 0x2000), (x86.UC_X86_REG_SS, 0x9000),
                            (x86.UC_X86_REG_SP, 0xFF00), (x86.UC_X86_REG_EFLAGS, 0x202)):
        uc.reg_write(register, value)
    result = {"entry": f"{entry:04X}", "instructions": 0, "bios_calls": []}

    def code(u, address, size, _):
        result["instructions"] += 1
        offset = address - 0x20000
        if offset in stops:
            result["stop"] = f"{offset:04X}"
            result["stop_meaning"] = stops[offset]
            result["al"] = f"{u.reg_read(x86.UC_X86_REG_AX) & 255:02X}"
            u.emu_stop()

    def interrupt(u, number, _):
        function = u.reg_read(x86.UC_X86_REG_AX) >> 8
        if number != 0x1A or function not in (4, 2):
            raise RuntimeError(f"Unexpected INT{number:02X}/AH{function:02X}")
        missing = function == absent_function
        result["bios_calls"].append({"interrupt": "1A", "ah": f"{function:02X}", "carry": missing})
        flags = u.reg_read(x86.UC_X86_REG_EFLAGS)
        u.reg_write(x86.UC_X86_REG_EFLAGS, (flags | 1) if missing else (flags & ~1))
        if function == 4 and not missing:
            u.reg_write(x86.UC_X86_REG_CX, 0x1990)
            u.reg_write(x86.UC_X86_REG_DX, 0x0101)

    reads = 0

    def read_fault(u, access, address, size, value, _):
        nonlocal reads
        reads += 1
        if reads == 2:
            u.mem_write(address, bytes([rom[0x6000] ^ 1]))
            result["read_fault"] = "Second read of F000:6000 changes returned data"

    uc.hook_add(unicorn.UC_HOOK_CODE, code)
    uc.hook_add(unicorn.UC_HOOK_INTR, interrupt)
    if unstable:
        uc.hook_add(unicorn.UC_HOOK_MEM_READ, read_fault, None, 0xF6000, 0xF6000)
    uc.emu_start(0x20000 + entry, 0, count=3_000_000)
    if "stop" not in result:
        raise RuntimeError("Instruction budget exhausted before declared boundary")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model25-rom", action="append", type=Path, default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    module = (ROOT / "7690diag/CPU0.DGS").read_bytes()
    if hashlib.sha256(module).hexdigest() != CPU0_SHA:
        raise RuntimeError("CPU0.DGS source hash mismatch")
    stops = {0x133: "ROM failure path, before saved-stack restoration", 0x1AE: "ROM tests complete; before NMI test"}
    checkerboard = bytes([0, 255]) * 32768
    balanced = bytearray(checkerboard)
    balanced[0x6000] = 1
    balanced[0x8001] = 254
    cases = [("synthetic_zero", bytes(65536), False, False),
             ("synthetic_ff", bytes([255]) * 65536, False, False),
             ("synthetic_checkerboard", checkerboard, False, True),
             ("synthetic_balanced_cross_block_error", bytes(balanced), False, False),
             ("synthetic_unstable_read", checkerboard, True, False)]
    observations = []
    for name, rom, unstable, expected_pass in cases:
        result = execute(module, 0x159, stops, rom=rom, unstable=unstable)
        assert (result["stop"] == "01AE") == expected_pass
        if not expected_pass:
            assert result["al"] == "05"
        observations.append({"source": name, "sha256": hashlib.sha256(rom).hexdigest(),
                             "whole_sum8": sum(rom) & 255, "result": result})
    for path in args.model25_rom:
        rom = path.read_bytes()
        observations.append({"source": str(path), "comparison_only": True,
                             "sha256": hashlib.sha256(rom).hexdigest(), "whole_sum8": sum(rom) & 255,
                             "result": execute(module, 0x159, stops, rom=rom)})
    clock = []
    for absent in (4, 2):
        result = execute(module, 0x25B, {0x8EC: "Common module error path"}, absent_function=absent)
        assert result["al"] == "3D"
        assert result["bios_calls"][-1] == {"interrupt": "1A", "ah": f"{absent:02X}", "carry": True}
        clock.append({"absent_bios_function": f"{absent:02X}", "result": result})
    report = {"schema": "ibm7690.platform-trace.v1", "engine": f"Unicorn {unicorn.__version__}",
              "scope": "Original CPU0 paths entered directly under synthetic ROM/BIOS fixtures; no full module, target firmware, RTC device, NMI, PIT/PIC/DMA or physical machine execution",
              "source": {"path": "7690diag/CPU0.DGS", "sha256": CPU0_SHA},
              "windows_hex": {f"{a:04X}-{b-1:04X}": module[a:b].hex() for a, b in
                              ((0x159, 0x1AE), (0x954, 0x987), (0x25B, 0x27D), (0x4BE, 0x4C3))},
              "rom_gate": observations, "clock_rejection": clock,
              "interpretation": "A zero whole-image checksum is insufficient: per8KiB checks, AND/OR coverage and read stability matter. A synthetic checkerboard passes this narrow gate, so passing it does not authenticate firmware. Absent clock services return AL3D via the real error path, not a skip."}
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
        print(f"Executed CPU0 prerequisite paths; evidence: {args.output}")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
