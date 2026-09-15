#!/usr/bin/env python3
"""Recover reachable 16-bit LEDTOUCH code and label data without linear misdecode.

uv run --with capstone==5.0.9 python TOOLS/disassemble_touch.py
Known DOS/mouse dispatch tables supply indirect-call roots. A reachable listing
is static evidence, not proof that every branch executed or every byte is code.
"""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import struct

import capstone
from capstone.x86_const import X86_OP_IMM

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {
    "3.02": {
        "path": "7690diag/LEDTOUCH.SYS",
        "sha256": "bfb95e3a5d1a9ef87742b33b19d33fee2fbcb0718f04995f770b0a3c37d6d2df",
        "mouse_table": 0x0EE2, "resident_end": 0x1906,
        "symbols": {0x030B: "dos_strategy", 0x0316: "dos_interrupt", 0x043D: "point_record",
                    0x0541: "initialize", 0x0712: "optical_or_mouse_scan", 0x0A9B: "adc_read",
                    0x0AB8: "toggle_lcd_reversal", 0x0AFD: "ibm_mouse_poll",
                    0x0C0B: "ibm_mouse_packet_callback", 0x0F0A: "timer_hook",
                    0x0F3E: "int33", 0x1772: "mouse_poll", 0x1C20: "service_optical_scan",
                    0x1C7B: "service_receiver_dark", 0x1C9B: "service_emitter_lit",
                    0x1CBE: "service_adc_read", 0x1DB4: "initial_selftest"},
    },
    "2.4": {
        "path": "ANALYSIS/7690KQPW/LEDTOUCH.SYS",
        "sha256": "1c3dc5a2c4a9c6d422f03f92db6b3bcc2b314939603a117594e9573eb7ee2613",
        "mouse_table": 0x0C3D, "resident_end": 0x1560,
        "symbols": {0x030B: "dos_strategy", 0x0316: "dos_interrupt", 0x0429: "point_record",
                    0x051C: "initialize", 0x06D3: "optical_scan", 0x09CB: "adc_read",
                    0x0C65: "timer_hook", 0x0C99: "int33", 0x13DD: "mouse_poll",
                    0x184A: "service_optical_scan", 0x19DB: "initial_selftest"},
    },
}
MOUSE_NAMES = ["reset", "show", "hide", "position", "set_position", "press_info",
               "release_info", "horizontal_bounds", "vertical_bounds", "graphics_cursor",
               "text_cursor", "motion", "callback", "noop_13", "noop_14", "ratios",
               "noop_16", "noop_17", "large_cursor_unsupported", "noop_19"]


def decode(data, symbols, roots):
    engine = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)
    engine.detail = True
    todo = deque(roots)
    instructions = {}
    unresolved = []
    while todo:
        address = todo.popleft()
        while 0 <= address < len(data) and address not in instructions:
            instruction = next(engine.disasm(data[address:address + 15], address, count=1), None)
            if instruction is None:
                raise ValueError(f"Cannot decode reachable offset {address:04X}")
            instructions[address] = instruction
            jump = instruction.group(capstone.CS_GRP_JUMP)
            call = instruction.group(capstone.CS_GRP_CALL)
            # LOOP/JCXZ are not consistently classified as CS_GRP_JUMP.
            jump |= instruction.mnemonic.startswith("loop") or instruction.mnemonic in ("jcxz", "jecxz")
            if jump or call:
                if len(instruction.operands) == 1 and instruction.operands[0].type == X86_OP_IMM:
                    target = instruction.operands[0].imm & 0xFFFF
                    if target < len(data):
                        todo.append(target)
                        symbols.setdefault(target, f"loc_{target:04X}")
                else:
                    unresolved.append({"offset_hex": f"{address:04X}", "instruction": instruction.mnemonic + " " + instruction.op_str})
            if instruction.group(capstone.CS_GRP_RET) or instruction.mnemonic in ("iret", "iretw", "hlt", "jmp", "ljmp"):
                break
            address += instruction.size
    occupied = {}
    for address, instruction in sorted(instructions.items()):
        for byte in range(address, address + instruction.size):
            if byte in occupied:
                raise ValueError(f"Overlapping decodes at {address:04X} and {occupied[byte]:04X}")
            occupied[byte] = address
    return instructions, unresolved


def generate(version, profile):
    data = (ROOT / profile["path"]).read_bytes()
    if hashlib.sha256(data).hexdigest() != profile["sha256"]:
        raise ValueError("Driver hash mismatch: " + profile["path"])
    symbols = dict(profile["symbols"])
    dos = struct.unpack_from("<17H", data, 0x02E9)
    mouse = struct.unpack_from("<20H", data, profile["mouse_table"])
    for number, target in enumerate(dos):
        symbols.setdefault(target, f"dos_command_{number:02X}")
    for name, target in zip(MOUSE_NAMES, mouse):
        symbols.setdefault(target, "mouse_" + name)
    instructions, indirect = decode(data, symbols, list(symbols))
    lines = [f"; LEDTOUCH {version}; {profile['path']}", f"; SHA256 {profile['sha256']}",
             "; Offsets are SYS-file-relative. C=reachable decoded instruction; D=unclassified/data.",
             "; Code roots include both dispatch tables. Indirect transfers remain explicitly catalogued.",
             "; A code label establishes static reachability, not physical execution or a public ABI."]
    chunks = []
    address = 0
    while address < len(data):
        if address in symbols:
            lines.append("; " + symbols[address] + ":")
        if address in instructions:
            instruction = instructions[address]
            raw = bytes(instruction.bytes)
            text = "C " + instruction.mnemonic + " " + instruction.op_str
        else:
            end = min(address + 16, len(data))
            end = next((i for i in range(address + 1, end) if i in instructions or i in symbols), end)
            raw = data[address:end]
            text = "D " + "".join(chr(c) if 32 <= c < 127 else "." for c in raw)
        lines.append(f"{address:04X}  {raw.hex():32}  {text}")
        chunks.append(raw)
        address += len(raw)
    if b"".join(chunks) != data:
        raise ValueError("Disassembly byte coverage failed")
    contract = {
        "path": profile["path"], "sha256": profile["sha256"], "bytes": len(data),
        "resident_end_hex": f"{profile['resident_end']:04X}",
        "device_header_hex": data[:18].hex(),
        "dos_dispatch": {f"{i:02X}": f"{v:04X}" for i, v in enumerate(dos)},
        "mouse_dispatch": {f"{i:02X}": {"name": MOUSE_NAMES[i], "offset_hex": f"{v:04X}"} for i, v in enumerate(mouse)},
        "symbols": {name: f"{offset:04X}" for offset, name in profile["symbols"].items()},
        "reachable_instruction_count": len(instructions),
        "reachable_code_bytes": sum(i.size for i in instructions.values()),
        "indirect_transfers": indirect,
        "whole_file_byte_coverage": True,
    }
    return "\n".join(lines) + "\n", contract


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "ANALYSIS")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    contract = {"schema_version": 1, "evidence": "static binary decode, not emulator ROM contract", "profiles": {}}
    for version, profile in PROFILES.items():
        listing, item = generate(version, profile)
        name = f"LEDTOUCH-{version}.lst"
        (args.output_dir / name).write_text(listing)
        item["listing"] = name
        contract["profiles"][version] = item
    (args.output_dir / "TOUCH-BINARY.json").write_text(json.dumps(contract, indent=2) + "\n")
    print(json.dumps({v: {k: p[k] for k in ("bytes", "reachable_instruction_count", "reachable_code_bytes")} for v, p in contract["profiles"].items()}))


if __name__ == "__main__":
    main()
