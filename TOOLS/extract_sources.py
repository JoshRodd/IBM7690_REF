#!/usr/bin/env python3
"""Extract supplied PDF text without pretending OCR is numeric authority.

Requires Poppler pdftotext. Keeps form-feed boundaries and records one-based
physical PDF pages, footer locators, hashes and exact extraction command.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'TECHREF': 'IBM_7690_Clinical_Workstation_Technical_Reference.pdf',
    'OPERATIONS': 'IBM_7690_Clinical_Workstation_Guide_to_Operations.pdf',
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'DOCUMENTATION/OCR')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    index = {'schema_version': 1,
             'warning': 'Existing PDF OCR/text layer extracted with layout. Numeric and graphical evidence must be checked against page images. Physical pages are scanned spreads, not printed page numbers.',
             'tool_version': subprocess.run(['pdftotext', '-v'], capture_output=True, text=True, check=True).stderr.strip(),
             'sources': {}}
    for name, filename in SOURCES.items():
        destination = args.output_dir / (name + '.txt')
        subprocess.run(['pdftotext', '-layout', str(ROOT / filename), str(destination)], check=True)
        raw = destination.read_bytes()
        pages = raw.decode('utf-8').split('\f')
        if pages[-1] == '':
            pages.pop()
        line = 1
        entries = []
        for number, page in enumerate(pages, 1):
            text_lines = [row.strip() for row in page.splitlines() if row.strip()]
            entries.append({'physical_pdf_page': number, 'start_text_line': line,
                            'characters': len(page), 'footer_locators': text_lines[-3:]})
            line += page.count('\n')
        index['sources'][name] = {
            'source_path': filename, 'source_bytes': (ROOT / filename).stat().st_size,
            'source_sha256': sha256((ROOT / filename).read_bytes()),
            'text_filename': destination.name, 'text_sha256': sha256(raw),
            'physical_pdf_pages': len(pages), 'command': ['pdftotext', '-layout', filename, destination.name],
            'pages': entries,
        }
    (args.output_dir / 'INDEX.json').write_text(json.dumps(index, indent=2) + '\n')
    print(json.dumps({name: {'pages': info['physical_pdf_pages'], 'source_sha256': info['source_sha256']} for name, info in index['sources'].items()}))


if __name__ == '__main__':
    main()
