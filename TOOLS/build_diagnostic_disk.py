#!/usr/bin/env python3
"""Derive a bootable PC DOS 3.20 + IBM 7690 v1.10 FAT12 disk without formatting.
Only accepts the documented donor. Never overwrites an output or source.
"""
import argparse
import json
import struct
from pathlib import Path
from inspect_media import FAT12, sha256

DONOR_SHA256 = '87b5cc84562cdf90b367c5c575680f3d37de92cc2f684033b15299015a568915'
KEEP = ('IBMBIO.COM', 'IBMDOS.COM', 'COMMAND.COM')
FILES = ('COLORFIX.COM', 'CPU0.DGS', 'DCOPY.COM', 'DFORMAT.COM', 'DIAGS.COM',
         'DISPLAY1.DGS', 'DSKT1.DGS', 'DTMEDTE.COM', 'IBM7690.DGS', 'LEDINST.BAT',
         'LEDTOUCH.SYS', 'NSTALL.EXE', 'PAR1.DGS', 'RBT.EXE', 'SER0.DGS',
         'SERVICES.COM', 'STG0.DGS', 'TXT.OK', 'US0KMAIN.DGS', 'US0PCN.DGS', 'VERSION.110')


def build(donor, loose, startup='menu', touch_driver=False):
    if sha256(donor) != DONOR_SHA256:
        raise ValueError('Donor SHA-256 differs from documented PCDOS32.IMG; refusing')
    disk = FAT12(donor)
    original = {e['name']: e for e in disk.entries()}
    kept = {name: original[name] for name in KEEP}
    if [(kept[n]['slot'], kept[n]['start_cluster'], kept[n]['attributes']) for n in KEEP[:2]] != [(0, 2, 0x27), (1, 18, 0x27)]:
        raise ValueError('Unexpected DOS boot-critical directory layout')
    actual = {p.name for p in loose.iterdir() if p.is_file() and not p.name.startswith('.')}
    if actual != set(FILES):
        raise ValueError('Loose file set differs: missing=' + str(sorted(set(FILES) - actual)) + ' extra=' + str(sorted(actual - set(FILES))))
    payloads = {name: (loose / name).read_bytes() for name in FILES}
    if payloads['VERSION.110'] != b'\r\n\x1a':
        raise ValueError('Unexpected VERSION.110 marker bytes')
    inputs = {name: {'size': len(data), 'sha256': sha256(data)} for name, data in payloads.items()}
    autoexec = b'ECHO OFF\r\nECHO Derived PC DOS 3.20 / IBM 7690 v1.10 research disk\r\n'
    if startup == 'menu':
        autoexec += b'SERVICES\r\n'
    else:
        autoexec += b'ECHO Type SERVICES only on a compatible IBM firmware and hardware model.\r\n'
    payloads['AUTOEXEC.BAT'] = autoexec
    if touch_driver:
        payloads['CONFIG.SYS'] = b'DEVICE=LEDTOUCH.SYS\r\n'
    # Retain boot code, both original system entries, COMMAND's entry and their
    # entire cluster contents/chains. Reclaim everything else on an in-memory copy.
    occupied = {c for e in kept.values() for c in e['chain']}
    disk.data[disk.root_sector * disk.bps:disk.data_sector * disk.bps] = bytes(disk.root_sectors * disk.bps)
    for e in kept.values():
        off = e['root_offset']
        disk.data[off:off + 32] = bytes.fromhex(e['entry_hex'])
    for c in range(2, disk.clusters + 2):
        if c not in occupied:
            disk.set_fat(c, 0)
            off = disk.cluster_offset(c)
            disk.data[off:off + disk.cluster_bytes] = bytes(disk.cluster_bytes)
    free = [c for c in range(2, disk.clusters + 2) if c not in occupied]
    slots = [s for s in range(disk.roots) if s not in {e['slot'] for e in kept.values()}]
    needed = sum((len(data) + disk.cluster_bytes - 1) // disk.cluster_bytes for data in payloads.values())
    if needed > len(free) or len(payloads) > len(slots):
        raise ValueError('Files do not fit the donor geometry')
    next_cluster = 0
    for slot, (name, data) in zip(slots, sorted(payloads.items())):
        count = (len(data) + disk.cluster_bytes - 1) // disk.cluster_bytes
        chain = free[next_cluster:next_cluster + count]
        next_cluster += count
        for i, c in enumerate(chain):
            disk.set_fat(c, chain[i + 1] if i + 1 < count else 0xfff)
            off = disk.cluster_offset(c)
            chunk = data[i * disk.cluster_bytes:(i + 1) * disk.cluster_bytes]
            disk.data[off:off + len(chunk)] = chunk
        base, ext = name.rsplit('.', 1)
        row = bytearray(32)
        row[:11] = (base.ljust(8) + ext.ljust(3)).encode('ascii')
        row[11] = 0x20
        # Deterministic DOS timestamp: 1990-01-01 00:00:00. Not a source timestamp.
        struct.pack_into('<HHHI', row, 22, 0, (10 << 9) | (1 << 5) | 1, chain[0] if chain else 0, len(data))
        off = disk.root_sector * disk.bps + slot * 32
        disk.data[off:off + 32] = row
    result = bytes(disk.data)
    check = FAT12(result)
    entries = {e['name']: e for e in check.entries()}
    if result[:512] != donor[:512] or not check.report()['fat_copies_equal']:
        raise ValueError('Boot sector or FAT preservation failure')
    for name, e in kept.items():
        if entries[name]['entry_hex'] != e['entry_hex'] or entries[name]['chain'] != e['chain'] or entries[name]['payload'] != e['payload']:
            raise ValueError('DOS preservation failure: ' + name)
        for c in e['chain']:
            off = disk.cluster_offset(c)
            if result[off:off + disk.cluster_bytes] != donor[off:off + disk.cluster_bytes]:
                raise ValueError('DOS cluster slack changed: ' + name)
    for name, data in payloads.items():
        if entries[name]['payload'] != data:
            raise ValueError('File round-trip failure: ' + name)
    manifest = {'kind': 'derived research disk, not original IBM diagnostic media', 'donor_sha256': DONOR_SHA256, 'output_sha256': sha256(result), 'startup': startup, 'touch_driver_loaded': touch_driver, 'new_file_timestamp': '1990-01-01T00:00:00 (synthetic DOS local time)', 'loose_inputs': inputs, 'media': check.report()}
    return result, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--donor', type=Path, required=True)
    parser.add_argument('--loose', type=Path, default=Path(__file__).resolve().parents[1] / '7690diag')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, help='Defaults to OUTPUT.json')
    parser.add_argument('--startup', choices=('menu', 'prompt'), default='menu')
    parser.add_argument('--touch-driver', action='store_true', help='Load LEDTOUCH.SYS at boot; omit for direct-hardware diagnostics')
    args = parser.parse_args()
    manifest_path = args.manifest or args.output.with_suffix(args.output.suffix + '.json')
    if args.output.exists() or manifest_path.exists() or args.output.resolve() == manifest_path.resolve():
        parser.error('Output and manifest must be distinct new paths')
    result, manifest = build(args.donor.read_bytes(), args.loose, args.startup, args.touch_driver)
    # Exclusive creation protects against a concurrent writer too. No raw device IO.
    with args.output.open('xb') as out:
        out.write(result)
    with manifest_path.open('x') as out:
        json.dump(manifest, out, indent=2)
        out.write('\n')
    print(json.dumps({'output': str(args.output), 'sha256': manifest['output_sha256'], 'bytes': len(result), 'free_bytes': manifest['media']['free_clusters'] * 1024, 'manifest': str(manifest_path)}))


if __name__ == '__main__':
    main()
