#!/usr/bin/env python3
"""Read-only FAT12 inventory; offsets are bytes from image start."""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def sha256(data):
    return hashlib.sha256(data).hexdigest()


class FAT12:
    def __init__(self, data):
        self.data = bytearray(data)
        b = self.data
        self.bps, self.spc, self.reserved, self.fats, self.roots, total, self.media, self.spf, self.spt, self.heads = struct.unpack_from('<HBHBHHBHHH', b, 11)
        self.total = total or struct.unpack_from('<I', b, 32)[0]
        if self.bps != 512 or self.spc == 0 or self.spc & (self.spc - 1) or not self.fats or not self.spf:
            raise ValueError('Unsupported or invalid FAT BPB')
        self.root_sector = self.reserved + self.fats * self.spf
        self.root_sectors = (self.roots * 32 + self.bps - 1) // self.bps
        self.data_sector = self.root_sector + self.root_sectors
        self.cluster_bytes = self.bps * self.spc
        self.clusters = (self.total - self.data_sector) // self.spc
        if not 0 < self.clusters < 4085 or len(b) != self.total * self.bps:
            raise ValueError('Not an exact-length FAT12 image')
        self.fat_start = self.reserved * self.bps
        self.fat_bytes = self.spf * self.bps
        if (self.clusters + 2) * 3 // 2 + 1 > self.fat_bytes:
            raise ValueError('FAT too small')

    def fat(self, cluster):
        off = self.fat_start + cluster * 3 // 2
        value = struct.unpack_from('<H', self.data, off)[0]
        return (value >> 4 if cluster & 1 else value) & 0xfff

    def set_fat(self, cluster, value):
        for copy in range(self.fats):
            off = self.fat_start + copy * self.fat_bytes + cluster * 3 // 2
            old = struct.unpack_from('<H', self.data, off)[0]
            new = (old & 0x000f) | (value << 4) if cluster & 1 else (old & 0xf000) | value
            struct.pack_into('<H', self.data, off, new)

    def chain(self, start):
        result = []
        while start:
            if start in result or not 2 <= start < self.clusters + 2:
                raise ValueError('Invalid or cyclic FAT chain')
            result.append(start)
            nxt = self.fat(start)
            if nxt >= 0xff8:
                return result
            if nxt < 2 or nxt >= 0xff0:
                raise ValueError('Broken FAT chain')
            start = nxt
        return result

    def cluster_offset(self, cluster):
        return (self.data_sector + (cluster - 2) * self.spc) * self.bps

    def entries(self):
        result = []
        for slot in range(self.roots):
            off = self.root_sector * self.bps + slot * 32
            row = self.data[off:off + 32]
            if row[0] == 0:
                break
            if row[0] == 0xe5 or row[11] == 0x0f:
                continue
            base, ext = bytes(row[:8]).decode('cp437').rstrip(), bytes(row[8:11]).decode('cp437').rstrip()
            name = bytes(row[:11]).decode('cp437').rstrip() if row[11] & 8 else base + ('.' + ext if ext else '')
            cluster = struct.unpack_from('<H', row, 26)[0]
            size = struct.unpack_from('<I', row, 28)[0]
            chain = self.chain(cluster) if not row[11] & 8 else []
            payload = b''.join(bytes(self.data[self.cluster_offset(c):self.cluster_offset(c) + self.cluster_bytes]) for c in chain)[:size]
            if len(payload) != size:
                raise ValueError('File size exceeds chain: ' + name)
            result.append({'name': name, 'slot': slot, 'root_offset': off, 'attributes': row[11], 'entry_hex': bytes(row).hex(), 'start_cluster': cluster, 'size': size, 'chain': chain, 'sha256': sha256(payload), 'payload': payload})
        return result

    def report(self):
        return {'size': len(self.data), 'sha256': sha256(self.data), 'boot_sha256': sha256(self.data[:512]), 'boot_signature': bytes(self.data[510:512]).hex(), 'oem': bytes(self.data[3:11]).decode('ascii', 'replace'), 'bpb': {'bytes_per_sector': self.bps, 'sectors_per_cluster': self.spc, 'reserved_sectors': self.reserved, 'fat_copies': self.fats, 'root_entries': self.roots, 'total_sectors': self.total, 'media': self.media, 'sectors_per_fat': self.spf, 'sectors_per_track': self.spt, 'heads': self.heads}, 'layout': {'fat_sector': self.reserved, 'root_sector': self.root_sector, 'root_sectors': self.root_sectors, 'data_sector': self.data_sector, 'data_clusters': self.clusters}, 'fat_copies_equal': all(self.data[self.fat_start:self.fat_start + self.fat_bytes] == self.data[self.fat_start + i * self.fat_bytes:self.fat_start + (i + 1) * self.fat_bytes] for i in range(1, self.fats)), 'free_clusters': sum(self.fat(c) == 0 for c in range(2, self.clusters + 2)), 'root': [{k: v for k, v in e.items() if k != 'payload'} for e in self.entries()]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    text = json.dumps(FAT12(args.image.read_bytes()).report(), indent=2) + '\n'
    if args.output:
        with args.output.open('x') as out:
            out.write(text)
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
