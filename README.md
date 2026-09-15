# IBM 7690 Clinical Workstation reference

Start with **[HANDBOOK_7690/README.md](HANDBOOK_7690/README.md)**: an implementation-oriented handbook for the 8086/Model25-based IBM 7690, including the clinical LCD/interface adapter, infrared touch circuit, keyboard/barcode gateway, diskette system, power behavior, BIOS boundaries, diagnostics and both supplied LEDTOUCH driver versions.

## Contents

| Path | Role |
|---|---|
| [HANDBOOK_7690/](HANDBOOK_7690/) | Integrated emulator writer's handbook, source/discrepancy register, verification report, machine-readable contract |
| [IBM_7690_Clinical_Workstation_Technical_Reference.pdf](IBM_7690_Clinical_Workstation_Technical_Reference.pdf) | Original primary technical reference;149 physical scanned spreads |
| [IBM_7690_Clinical_Workstation_Guide_to_Operations.pdf](IBM_7690_Clinical_Workstation_Guide_to_Operations.pdf) | Original operations manual;41 physical scanned spreads |
| [7690diag/](7690diag/) | Original21 loose customer-diagnostic files, associated with Version1.10 |
| [7690diag.jpg](7690diag.jpg) | Original diskette-label photograph |
| [7690KQPW.IMA](7690KQPW.IMA) | Original720-KiB mixed MS-DOS5.00 / diagnostic1.00 / KQPW disk, not a pristine1.10 diagnostic image |
| [DOCUMENTATION/OCR/](DOCUMENTATION/OCR/) | Searchable extraction of the PDFs' existing text layers; page index, hashes and extraction provenance |
| [DOCUMENTATION/BASELINE/](DOCUMENTATION/BASELINE/) | Selected unchanged Model25/BIOS reference copies and research JSON from `bios8530`, with provenance |
| [ANALYSIS/](ANALYSIS/) | Extracted mixed-image files, byte-accounted driver listings, diagnostic disassembly, evidence JSON and actual DOS screenshots |
| [TOOLS/](TOOLS/) | Source extraction, read-only FAT12 inspection, deterministic derived-disk construction, driver disassembly and original-instruction trace fixtures |
| [MEDIA/7690diag-pcdos320.img](MEDIA/7690diag-pcdos320.img) | Derived bootable PC DOS3.20 + loose1.10 diagnostic research image; [construction manifest](MEDIA/7690diag-pcdos320.img.json) |

## Evidence boundary

The original sources are preserved. Neither authentic7690 planar ROM nor16-KiB C000 interface-adapter ROM was supplied. Comparative Model25 ROM bytes are identified as comparative, not relabeled as target firmware.

The derived disk **boots DOS and executes SERVICES**, but generic QEMU/SeaBIOS correctly fails SERVICES' IBM7690 firmware check. This is not a claimed full7690 boot or diagnostic pass. Both touch drivers additionally run as original machine code in explicit synthetic fixtures; a separate actual-DOS smoke loads3.02 and reads the idle `POINT` record through a DOS client. See **[verification and screenshots](HANDBOOK_7690/VERIFICATION.md)** for exact exercised boundaries.

## Reproduce the core research

Run from this directory. Source extraction requires Poppler. Driver analysis uses pinned research dependencies without adding packages to the repository:

```sh
python3 TOOLS/extract_sources.py
python3 TOOLS/inspect_media.py 7690KQPW.IMA
uv run --with capstone==5.0.9 python TOOLS/disassemble_touch.py
uv run --with unicorn==2.1.4 python TOOLS/touch_trace.py --output /tmp/7690-touch-trace.json
uv run --with unicorn==2.1.4 python TOOLS/video_trace.py --output /tmp/7690-video-trace.json
uv run --with unicorn==2.1.4 python TOOLS/platform_trace.py --output /tmp/7690-platform-trace.json
```

The disassembler and trace fixture consume both versions; the extracted older file is retained at `ANALYSIS/7690KQPW/LEDTOUCH.SYS`. [DIAGNOSTICS.md](HANDBOOK_7690/DIAGNOSTICS.md) gives the exact DOS donor hash, boot-preservation rules, builder options and safe runtime commands. Builders refuse existing output paths. Use a disposable image or copy-on-write overlay for diagnostic menus that can write or format; never point them at a raw host device.
