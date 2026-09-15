# Sources, provenance, offsets, and contradictions

This handbook is an engineering synthesis of supplied primary publications and software, checked against the 8086 Model25 comparative corpus. Evidence is attached to a **particular artifact and boundary**. A shared IBM name, `FA` model byte, BIOS function number, port aperture or copyright string does not make two machines interchangeable.

## 1. Authority and conflict handling

1. **Original target binary** establishes what that exact software executes. Identify driver/module revision and byte origin. It can expose a bug or undocumented transaction; it does not automatically establish physical hardware behavior.
2. **Target primary page image** establishes what IBM actually printed. The book may still contain a genuine error or describe another firmware revision.
3. **Target operations manual** is particularly useful for shipped/user-visible configuration, media, operator workflow, options and power behavior. Conflicts with the technical reference remain explicit.
4. **Identified comparative ROM or primary Model25/30 document** supplies architectural context and concrete implementation leads. Label every transfer to7690; check target reservations and changes first.
5. **Existing research JSON, disassembly names and archived reverse engineering** are indexed leads, not a replacement for their cited bytes/pages.
6. **Executed fixtures** establish results under their declared synthetic boundary. They are not physical measurements or a full-machine test merely because they run real x86 instructions.

When sources disagree, retain the competing statements, the exact evidence, the implementation consequence and the unresolved measurement. Do not silently repair OCR, printed mistakes and actual program bugs in the same way: they are different classes of evidence.

## 2. Original supplied artifacts

All lengths are bytes; SHA-256 is over the complete original file. Full original loose-file identities and the source-preservation audit are in [SOURCE-SNAPSHOT.json](../ANALYSIS/SOURCE-SNAPSHOT.json) and [media_comparison.json](../ANALYSIS/media_comparison.json).

| Original artifact | Length | SHA-256 |
|---|---:|---|
| [Technical Reference](../IBM_7690_Clinical_Workstation_Technical_Reference.pdf) |51045276|`e45778aea663a09a9ebd029e6bcde3e0992fd9af58ddde567c174ab708e2fe4e`|
| [Guide to Operations](../IBM_7690_Clinical_Workstation_Guide_to_Operations.pdf) |11667542|`70521548cbedc6680525008de3004101d686456561f15a9d1eb0519e02c9f5e5`|
| [7690KQPW.IMA](../7690KQPW.IMA) |737280|`6b89fe1a982eb7e480fb1757ca0285d9889e0154f18611a8e57cc4a8bb8997fe`|
| [7690diag.jpg](../7690diag.jpg) |890456|`8510a07d4599922e09c37630ae161c0744233219373aac4d2f98e4145299356a`|

[7690diag/](../7690diag/) contains **21 files totaling94448 bytes**, not a sector image and not a bootable DOS distribution by itself. The photograph identifies the customer-level diagnostic product as **Version1.10**, part/label **SA12-7007-00**, copyright1981,1990. Host filesystem timestamps do not override that label or the executables' own banners.

The supplied720-KiB image is a later mixture: **MS-DOS5.00**, diagnostic marker **VERSION.100**, and **KQPW** software/files. It has no AUTOEXEC.BAT and its CONFIG.SYS contains `country=001` plus CRLF. Nineteen filenames occur in both software sets; fifteen are byte-identical and four differ. [DIAGNOSTICS.md](DIAGNOSTICS.md) gives the complete comparison and FAT12 provenance, including deleted/root/slack boundaries. An extracted directory does not preserve the image's sector layout, deleted entries, allocation or boot-chain evidence; keep the IMA.

### Touchscreen versions must remain distinct

| Distribution | Banner | Size | SHA-256 |
|---|---|---:|---|
| Loose diagnostic1.10 |LEDTOUCH3.02|8111|`bfb95e3a5d1a9ef87742b33b19d33fee2fbcb0718f04995f770b0a3c37d6d2df`|
| Mixed image diagnostic1.00 |LEDTOUCH2.4|7021|`1c3dc5a2c4a9c6d422f03f92db6b3bcc2b314939603a117594e9573eb7ee2613`|

The driver is `POINT` plus an INT33 service implementation, not a resident program named by the diskette version. Both binary identities, dispatch tables, named routines and byte coverage are in [TOUCH-BINARY.json](../ANALYSIS/TOUCH-BINARY.json).

## 3. PDF navigation: physical pages are not printed pages

The Technical Reference has **149 physical PDF pages**, the Operations guide **41**. Most are scans of **two printed pages side by side**; front matter and chapter boundaries break simple arithmetic. A citation such as **TR PDF100 / printed5-2–5-3** names one physical spread containing two printed pages. A PDF viewer fragment `#page=100` uses the physical page number, starting at1.

The PDFs already contain a useful text/OCR layer. [extract_sources.py](../TOOLS/extract_sources.py) runs Poppler `pdftotext -layout`; it does not claim to have reconstructed every table with fresh OCR. [INDEX.json](../DOCUMENTATION/OCR/INDEX.json) records source/text hashes, extractor version, physical-page count, each page's one-based LF-delimited starting text line and trailing visible locators. Blank pages and adjacent form-feed boundaries can share a line number. Printed labels and images remain the durable citation; line numbers are convenience locators for this extraction/version.

| Subject | Technical Reference physical PDF pages | Principal printed location |
|---|---|---|
| Architecture, CPU, planar/bus, memory, PIC/DMA/PIT |10–26|1-3 onward; specific table citations in BOOT |
| MCGA and LCD hardware |27–48|1-36–1-79|
| Diskette controller |49–62|1-80–1-107|
| Serial interface |62–69|1-107–1-121|
| Parallel interface |70–71|1-122–1-125|
| Beeper/earphone and connectors |72–73|1-126 onward|
| Power supply |75–76|2-2–2-5|
| Keyboard commands, raw mappings and sequences |78–91|3-2–3-28|
| Barcode hardware and programming |92–99|4-2–4-16|
| Optical registers |100|5-2–5-3|
| Driver installation, POINT and INT33 interface |101–107|5-4–5-17|
| BIOS interface and tables |108–142|Section6|
| Clinical INT10 extensions |118–119|6-21–6-22|
| No-RTC feature descriptor |132|6-49|
| Software date/time services |137|6-59|
| Clinical-mode mapping and power software |143–145|7-2–7-6|

Operations PDF15–16 covers clock/date guidance; PDF27 contains printed3-6–3-7 with error numbers; PDF35 contains printed4-12–4-13 barcode/card-holder instructions. The chapter-local source tables provide narrower locators and image-check lists.

### Inspect an actual spread

```sh
pdftoppm -f 100 -singlefile -scale-to 2600 -png \
  IBM_7690_Clinical_Workstation_Technical_Reference.pdf \
  /tmp/7690-touch-registers
```

Open the generated PNG, including both halves and footers. Rendering at a useful scale matters for `6B` versus `68`, `8F` versus `BF`, decimal versus hex operands, overbars/negative logic, superscripts, bit widths and timing units. A plausible OCR string is not enough to resolve any of those.

## 4. Comparative Model25 corpus

Original research root: **`/Users/josh/src/bios8530`**, unchanged. Its primary references, corpus, original ROM pairs, byte-preserving assembly and earlier emulator investigations were used as attributed context. [MODEL25.md](MODEL25.md) identifies exact upstream files and the target-versus-baseline decisions.

Retained unchanged local subset, with all copy hashes in [BASELINE/PROVENANCE.json](../DOCUMENTATION/BASELINE/PROVENANCE.json):

- [PS/2 Model25 Technical Reference, June1987](../DOCUMENTATION/BASELINE/PS2_Model_25_Technical_Reference_Jun87.pdf), SHA-256 `b4d3df94571cfa6299f45290d75374322c03d68ddba4370cce8e41ab7dd4f899`.
- [PS/2 and PC BIOS Interface Technical Reference, April1987](../DOCUMENTATION/BASELINE/PS2_and_PC_BIOS_Interface_Technical_Reference_Apr87.pdf), SHA-256 `950f2a5508f7092a7eaf0f6181464bc21d0d39e59a9bb63f02ee86ac8668cff2`.
- [hardware_spec.json](../DOCUMENTATION/BASELINE/hardware_spec.json), [model_differences.json](../DOCUMENTATION/BASELINE/model_differences.json), [rom_analysis.json](../DOCUMENTATION/BASELINE/rom_analysis.json), and [source_manifest.json](../DOCUMENTATION/BASELINE/source_manifest.json).

The imported upstream source manifest describes the **broader upstream corpus**, not a claim that all its listed files are retained in this repository. The retained model/ROM JSON remains upstream research, including candidate interpretations; the handbook's cited byte checks and explicit corrections are necessary context.

Two full comparative ROM identities used here:

| Image | SHA-256 | Provenance boundary |
|---|---|---|
| Model25 type1,65536 bytes |`cfbdc2cd67c95c15b06be14e2e5f4bbd6991f3506428af64038b6381a1120166`|Original pair00F2092/00F2093; not7690|
| Model25 type2,65536 bytes |`ed11efb8184ccf7055956ef34a6f81a496ac38e066d117f17df3fa2c79d9d2ee`|Original pair00F2122/00F2123; not7690|

Both have ASCII date06/26/87 and modelFA/submodel01 in the identified descriptor context. The baseline contains a runtime optional-clock probe and alternate descriptors: finding a descriptor-shaped byte sequence is not proof that it is the active one. [platform-evidence.json](../ANALYSIS/platform-evidence.json) retains raw instruction windows and hashes; [video_trace.py](../TOOLS/video_trace.py) retains the107-byte font-staging extract with full original-ROM identity. No complete comparative ROM is relabeled or distributed as a7690 image.

The PCJX and5140 handbooks were used for **organization, evidence discipline and implementation-oriented style**. Their machine-specific controllers, LCD aspect ratio, portable power/NMI, keyboard raw scans and ROM layout are not inherited7690 facts.

## 5. Binary coordinates and decoding conventions

| Artifact | Origin convention |
|---|---|
| `LEDTOUCH.SYS` | Offset0000 is the DOS device header; offsets in TOUCH/DRIVER_ABI are direct file offsets, no0100 bias |
| `*.COM` | File byte0 loads at PSP:0100; a file offset plus0100 gives its COM logical offset |
| `*.DGS` | DIAGS loads a module at offset0000, not COM0100; descriptor forms and far entry are documented in DIAGNOSTICS |
| Combined Model25 ROM | File offset equals F000-relative offset; physical address=F0000+offset |
| FAT image | Byte/sector offsets address the whole image, independent of a file's cluster chain |

Addresses and opcode/bit masks are hexadecimal when suffixed `h`, prefixed `0x`, or shown in a table explicitly labeled hex. Counts, bytes, dimensions and milliseconds are decimal unless marked otherwise. IBM's disk labels use nominal/unformatted marketing capacities; image byte lengths and geometry are the unambiguous storage quantities.

The [3.02 listing](../ANALYSIS/LEDTOUCH-3.02.lst) and [2.4 listing](../ANALYSIS/LEDTOUCH-2.4.lst) use recursive reachable-code discovery rooted in known entrypoints and dispatch tables. `C` rows are reached decoded instructions; `D` rows retain other bytes without pretending they are proven data or unreachable forever. Every input byte is accounted for once. Indirect targets are included only when established, not guessed by decoding every printable string as x86.

The older `*.ndisasm.txt` and diagnostic linear listings remain useful **search aids**. Linear x86 decoding also interprets strings/tables as plausible instructions. Re-start decoding at a verified routine boundary before citing behavior. Curated diagnostic routine extracts and JSON byte windows disambiguate the claims actually made.

## 6. Cross-chapter discrepancy register

This is an index, not a second competing register specification. Follow the linked owning chapter for complete values and control flow.

| Issue | Evidence / resolution | Implementation consequence |
|---|---|---|
| RAM control `68` versus `6B` | Primary image clearly6B; BOOT | Resolved OCR error, not a port alias |
| DMA aperture `80–BF` versus `80–8F` | Primary image clearly0080–008F | Do not map clock space as DMA |
| Shifted DMA page assignments | Target print80/81/82/87 conflicts with baseline and CPU0's81/82/83/87 accesses | Provisional inherited map with explicit channel-attribution uncertainty; BOOT/STORAGE |
|640-KiB target versus512-KiB parent default | Target configuration explicitly640 | Do not inherit Model25's smaller default |
| Target modelFA/submodel00 versus Model25FA/01 | Both are explicit evidence | No identity-byte patch as an authentic firmware substitute |
| RTC absent/present | TR no-RTC; Operations continuous clock; CPU0 actively requires clock/RAM/alarm | Material unresolved target revision/population conflict, not an optional diagnostic skip |
| BIOS DMA3 feature versus hardware DRQ3 unused | Both target statements exist | Distinguish generic BIOS capability from a populated fixed-disk device |
| Port62.2/65.0 fixed-disk assumptions | Target reserves those bits | No default integrated Model25/30 fixed disk |
| PIT1 “refresh timer” shorthand | Full description clocks PIT1 from diagnostic RAS, OUT unused | Do not wire PIT1 OUT as refresh source |
| Full-ROM checksum alone | CPU0 checks four8-KiB regions, whole ROM, read stability and AND/OR coverage | Zero-filled BASIC or cross-block checksum compensation can fail; MODEL25 |
| HD drive versus720-KiB-only BIOS type table | Operations1.44-MB drive; DSKT1 sector18 probe; generic TR table only type3 | Preserve HD/DD mechanics; exact target ROM override remains unknown |
| FDC command opcode collisions | Five genuine printed target errors; primary Model25 table and bytes give canonical encodings | Use STORAGE's explicit errata, not OCR or contradictory target opcodes |
| Mode5 maps to5 versus4 | TR Figures1-24 and7-1 disagree in actual images | Leave mode5 resolution OPEN; DGS separately establishes03→02 |
| LCD H/V pointer labels and width | Printed prose/diagram axes and stated widths conflict | Raw latches plus qualified mapping; do not invent an exact transform |
| LCD normal/base mode tables | Disjoint literal index sets, no documented bank selector | Do not invent an address bank-switch command |
| LCD power register | F305 index0D bits0/1; F302 optical enable is unrelated | One owner per power/control latch; VIDEO/TOUCH |
| LCD pixel aspect and tint | Raster640×480 documented; active glass and colors unmeasured | A square-pixel host surface is a presentation choice, not measurement |
| LCD grayscale/DAC/FRC | Built-in LCD takes pre-DAC digital data; no measured FRC | Do not infer analog RGB luminance or temporal dithering |
| LCD diagnostic readback masks | Actual DGS masked comparisons, including reserved indices | Not general writable masks or complete silicon specification |
| Column40h masked to0 | DGS verifier deliberately writes zeros at column0 before target reads | A simple6-bit alias plus literal RAM writes fails; physical strobe semantics still OPEN |
| COLORFIX “color map” | Actual utility changes BDA40:96 bit4, not40:89; AH09-only hook | Preserve observed side effect; purpose of that BDA write not guessed |
| Typematic equation/table | Genuine printed inconsistencies and duplicated entries | Keep explicit source table and baseline formula distinction; KEYBOARD |
| Keypad-plus sequence | Genuine printed command/sequence inconsistencies | Preserve chapter's source-specific branch, not a familiar desktop assumption |
| Set2 F0 continuation | Second byte typically2ms after interface re-enable,10ms worst case under stated interference | Do not start this timer at prefix emission or apply it universally |
| UART RI/overrun wording | Primary bit labels/prose conflict with other descriptions | Keep directional transition/error distinctions in PERIPHERALS |
| Disabled negative LCD rail | Primary says disabled−22.3V output goes to+5V | Not zero-volts off; electrical design must follow primary limits |
| F303 direction column | Printed I/O marks conflict with ADC-output description and actual IN instructions | CPU reads six-bit conversion result; no invented DAC write |
| ADC “busy” only | Runtime waits low; self-test also requires post-read bit3 high | Model conversion-ready versus consumed/re-arm state |
| Optical thresholds | Runtime dark−8; service dark−16; DGS dark−20 | Separate actual algorithms, no universal threshold constant |
| Calibration neighbor retries | First emitter retries retain current receiver from earlier passes | Do not re-canonicalize receiver state on every retry |
| Broad vertical occlusion | Both drivers reject middle usable Y byteFF | X18/Y8..15 is no-touch by default, not a centroid |
| LCD coordinate eligibility |2.4 skips only zero active height;3.02 skips signed<=199 | Version-specific transform guard |
| POINT rounding | Odd-divisor remainder4999 already rounds upward | Exact integer rule, not floating-point half-up |
| Mouse defaults/reset | Published defaults and preserved instructions differ | Version-specific ABI contract; do not reset fields the code retains |
| POINT request status | Actual successful partial reads return0200 in fixture | Distinguish driver request status from DOS handle API result |
| Initialization packet pointer | BX replaced by0201 before status store; actual DOS fallback still loads3.02 | Keep low-level caveat and separate actual-DOS observation |
|2.4 light-pen row | DIV usesCX/Y instead of loadedBX199 | Preserve defect in an exact ABI substitute; zero divisor can fault |
| DGS writesF306 | Actual `OR DX,4` with DX=F302 producesF306 | Record real transaction; no supplied decode establishes the intended effect |
| Loose1.10 versus image1.00 | Different drivers/SERVICES/IBM7690/display module payloads | Never compare offsets across versions without identity checks |
| Generated AUTOEXEC under DOS3.20 | `@ECHO OFF` produced a real error; `ECHO OFF` works | Derived builder corrected; original LEDINST remains archived unchanged |

## 7. Derived files and reproducibility

The retained [PC DOS research image](../MEDIA/7690diag-pcdos320.img) is **not original IBM diagnostic media**. Its exact donor is the sibling5140 collection's PC DOS3.20 image, SHA-256 `87b5cc84562cdf90b367c5c575680f3d37de92cc2f684033b15299015a568915`. Builder invariants preserve boot sector, original DOS root entries, chains and complete clusters/slack; every added file and synthetic timestamp is in the [manifest](../MEDIA/7690diag-pcdos320.img.json). Reproduction needs that exact donor; merely copying DOS filenames to a blank FAT image is not equivalent.

`ANALYSIS/7690KQPW/` is an extracted view of the unchanged supplied image. JSON ledgers and disassemblies are derived research, not source executables. Screenshots/text captures are observations of the named generic DOS scenarios, not a photographed7690. [VERIFICATION.md](VERIFICATION.md) lists commands, tools, scenarios and limitations; [MACHINE-CONTRACT.json](MACHINE-CONTRACT.json) links the principal machine and software facts.

## 8. Acquisition needed to close hardware questions

- Both planar ROM chips plus lane/orientation/board provenance; complete C000 interface-adapter ROM and any keyboard/barcode-controller firmware. Preserve original chips before making linear images.
- Board/adapter/keyboard labels, photographs and component identities, especially the clock/RAM/alarm implementation implied by CPU0 and the adapter's unpublished register decode.
- Original Version1.10 sector image, including boot/DOS/startup/deleted/slack provenance; a file-only reconstruction cannot recover it.
- Optical selector/strobe/ADC traces, conversion and settling timing, weak-path/ambient-light behavior, and the observed effect of the F306 diagnostic write.
- LCD active-area dimensions, measured appearance, scan/LP phase, buffer/control transitions, actual C000 per-mode status responses and cold-reset register state.
- Power-off clock persistence, rail transitions and battery-exhaustion reset behavior; keyboard command/timing and real modem/printer/barcode handshakes at the electrical boundary.

These are explicit evidence gaps, not placeholders for invented firmware, fake success paths, canned register values, or hidden emulator exceptions.
