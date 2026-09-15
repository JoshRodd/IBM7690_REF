# Verification: performed work, reproducible experiments, and limits

This is a record of **observed results**, not a list of tests an emulator might eventually pass. Downstream whole-machine gates are in the [handbook entrypoint](README.md). Authentic7690 planar/C000 ROM execution, a complete diagnostic pass and physical hardware behavior were **not** demonstrated.

## 1. Result matrix

| Work | Performed result | Evidence boundary |
|---|---|---|
| Primary-document extraction |149 Technical Reference and41 Operations physical pages; source/text hashes and page locators recorded | Existing OCR/text layer extracted; numerical authority remains the rendered image |
| Critical primary tables and contradictions | Image checks across planar, MCGA/LCD, FDC, keyboard, barcode, UART/LPT, power and BIOS pages; chapter-local lists identify them | Not every diagram has been electrically measured or every printed claim independently verified on hardware |
| Original-source preservation |25 supplied files matched the recorded inventory/comparison; exact external DOS donor unchanged | Whole-file identities, not a claim to recover a missing original1.10 sector image |
| Derived disk construction | Deterministic menu image rebuilt twice byte-identically;21 diagnostic and3 DOS payloads independently recovered with mtools | FAT/image correctness and preservation; boot proof is separate below |
| Builder refusal paths | Existing output, existing manifest, same output/manifest path and altered donor refused; sentinel bytes preserved and no unintended output created | Specific exercised filesystem cases, not an atomic two-file transaction guarantee under every possible race |
| Driver disassembly | Both originals decoded from known roots/dispatch targets with all bytes accounted for | Reached code versus unclassified bytes, not a declaration that every indirect path is discovered |
| Original touch-driver execution | Both self-tests, all64 single-beam positions, masks/geometry, selected APIs, calibration faults, callbacks and failures executed | Unicorn with explicit optical/BIOS fixtures, not a calibrated electrical model or full DOS machine |
| Original video-software execution | COLORFIX all256 attributes, Model25 font staging, both DGS revisions' LCD fill/verify routines and corruption/alias failures | Synthetic DOS/BIOS/diagnostic-RAM boundaries; no LCD scanout or C000 firmware |
| Original CPU0 prerequisites | ROM gate success/failure distinctions and absent-clock error paths executed | Direct routine entry; not normal complete CPU0 execution or POST |
| Actual PC DOS3.20 boot | Corrected prompt derivative reaches prompt, VER/DIR/TYPE work; retained menu derivative automatically reaches SERVICES' firmware refusal | Generic QEMU PC/SeaBIOS, not7690 hardware |
| Actual DOS driver/client | Unpatched3.02 loads via CONFIG, selects IBM-mouse fallback, real DOS client reads idle POINT record | Absent optical hardware; active optical input under DOS not exercised |
| Supplied mixed image boot | MS-DOS5.00 date/time prompts and VER observed with original image read-only | KQPW application and its host communications not run |

Machine-readable evidence: [SOURCE-SNAPSHOT.json](../ANALYSIS/SOURCE-SNAPSHOT.json), [MEDIA-PROOF.json](../ANALYSIS/MEDIA-PROOF.json), [TOUCH-BINARY.json](../ANALYSIS/TOUCH-BINARY.json), [TOUCH-TRACE.json](../ANALYSIS/TOUCH-TRACE.json), [VIDEO-TRACE.json](../ANALYSIS/VIDEO-TRACE.json), [PLATFORM-TRACE.json](../ANALYSIS/PLATFORM-TRACE.json), and [DOS-BOOT-TRACE.json](../ANALYSIS/DOS-BOOT-TRACE.json).

## 2. Research environment and repeatability

The executed environment used:

| Tool | Observed version / use |
|---|---|
|Python|3.14.7 for standard-library tools;3.13.14 in the isolated binary-analysis environment|
|Unicorn|2.1.4, x86 16-bit instruction execution|
|Capstone|5.0.9, rooted disassembly|
|Poppler pdftotext|26.08.0, layout-preserving text extraction|
|GNU mtools mcopy|4.0.49, independent FAT extraction|
|NASM|3.02, disposable actual-DOS POINT consumer|
|QEMU|11.0.3, `qemu-system-i386` generic PC|
|SeaBIOS|`rel-1.17.0-0-gb52ca86e094d-prebuilt.qemu.org`, actual displayed banner|

The local research interpreter was `/tmp/ibm7690-analysis/bin/python`. That temporary path is **not a repository dependency**. The following `uv` commands obtain the pinned analysis packages without adding a virtual environment to the reference tree. Run from the repository root, and direct new reports to disposable/derived paths, never to an input binary.

```sh
python3 TOOLS/extract_sources.py
python3 TOOLS/inspect_media.py 7690KQPW.IMA
uv run --with capstone==5.0.9 python TOOLS/disassemble_touch.py
uv run --with unicorn==2.1.4 python TOOLS/touch_trace.py \
  --output /tmp/7690-touch-trace.json
uv run --with unicorn==2.1.4 python TOOLS/video_trace.py \
  --output /tmp/7690-video-trace.json
uv run --with unicorn==2.1.4 python TOOLS/platform_trace.py \
  --output /tmp/7690-platform-trace.json
```

The exact interpreter versions need not be assumed to reproduce arithmetic, but the recorded engine versions define the executed evidence. Unicorn is **not an8086 cycle/bus simulator**; no wall time or instruction count in a report is a physical settling, serial or display timing measurement. Research fixtures fail on unexpected ports/interrupts and bound execution rather than silently inventing a success response. Their explicitly intercepted BIOS/DOS services are described below.

The documented `uv run --with ...` commands were also executed, not merely suggested. Touch and video reports reproduced the retained files byte-for-byte; the self-contained platform cases matched the retained synthetic cases and clock failures; regenerated disassembly metadata was unchanged. Thus the temporary research interpreter is not required for these reproduction paths. Final audit records include those comparisons.

## 3. Source and media proof

### 3.1 Originals and extracted files

The25 supplied files are the two PDFs, image, photograph and21 loose diagnostic payloads. [SOURCE-SNAPSHOT.json](../ANALYSIS/SOURCE-SNAPSHOT.json) preserves their exact lengths/hashes. Selected baseline copies match their original upstream bytes; [PROVENANCE.json](../DOCUMENTATION/BASELINE/PROVENANCE.json) records both paths. No sibling source or DOS donor was modified.

`ANALYSIS/7690KQPW/` was extracted from the supplied image using mtools. [media_kqpw.json](../ANALYSIS/media_kqpw.json) independently records root metadata, chains and payload hashes using the repository's read-only FAT12 parser. Preserve the original image: extracted files alone cannot replace sector/deleted/slack evidence.

### 3.2 Derived menu image

Retained file: [MEDIA/7690diag-pcdos320.img](../MEDIA/7690diag-pcdos320.img),737280 bytes.

```text
SHA256 d62da26560bcaab05f9d367dca6912db95b9c08b5b90111cb8bb58bb110981fd
Free bytes 555008
Default startup SERVICES
Default resident touch driver none
```

[The manifest](../MEDIA/7690diag-pcdos320.img.json) records the exact donor hash, each loose input, synthetic timestamp, root entries, chains, FAT-copy agreement and image hash. Two separately named menu rebuilds matched the retained image **byte for byte**. Independent `mcopy` extraction matched every one of the21 loose payloads and all three preserved DOS payloads against their sources. The builder also compares the DOS root entries/chains and complete source clusters including slack.

Rebuild to an **unused output name**:

```sh
python3 TOOLS/build_diagnostic_disk.py \
  --donor /Users/josh/src/JoshRodd/IBM5140_REF/DOS/PCDOS32.IMG \
  --output /tmp/7690-rebuilt-menu.img
python3 TOOLS/inspect_media.py /tmp/7690-rebuilt-menu.img
```

The donor must hash to `87b5cc84562cdf90b367c5c575680f3d37de92cc2f684033b15299015a568915`. The tool refuses existing output/manifest paths; remove only your own disposable previous outputs or choose fresh names. It does not overwrite originals, invoke FORMAT, touch a raw device, mix MS-DOS5 system files into PC DOS3.20, or patch SERVICES.

[MEDIA-PROOF.json](../ANALYSIS/MEDIA-PROOF.json) records two deterministic rebuilds and four refusal scenarios. The refusal fixtures used temporary sentinel/corrupted-copy files, not attempts to overwrite a real source. Temporary absolute filenames in the report are historical observations, not files required to remain installed.

## 4. Driver disassembly and execution

### 4.1 Byte-accounted listings

| Version | Original bytes | Reached instructions | Reached instruction bytes | Whole-file accounting |
|---|---:|---:|---:|---|
|3.02|8111|2006|5227|All8111 bytes retained exactly once|
|2.4|7021|1715|4321|All7021 bytes retained exactly once|

The remaining bytes are retained as unclassified, not discarded or asserted to be permanently unreachable. Listings: [3.02](../ANALYSIS/LEDTOUCH-3.02.lst), [2.4](../ANALYSIS/LEDTOUCH-2.4.lst). The disassembler checks input identities, known dispatch roots, overlapping instruction claims and byte reconstruction. Raw linear `ndisasm` listings are supplementary search aids; decoding a string as x86 does not prove execution.

### 4.2 Optical/BIOS fixture boundary

`touch_trace.py` loads the **unchanged original SYS bytes** at2000:0000, supplies a controlled stack and return boundary, and executes original near/far/IRET entries. Guest writes to its own dispatch/data/IVT are allowed; no success branch or algorithm instruction is patched.

The circuit fixture has separate selection-data, receiver, emitter and control latches; six-bit dark/lit results; conversion completion and result-consumption/re-arm state. Normal clear optical paths use dark63/lit0. Unmatched or blocked selections remain dark. Exact analog voltage, noise, conversion latency, physical strobe edge and8086 bus cycles are not measured. F301 keyboard/scanner inputs are not a simulated keyboard/barcode controller.

INT10 supplies declared mode, teletype, cursor no-render and custom-LCD responses. The raw-coordinate profile leaves the custom extension unsupported; separate scenarios report explicit top/active/physical dimensions. INT15 pointing-device initialization succeeds only as a stated fallback fixture; the captured callback is invoked with explicit packet data. DOS hooks are intercepted for vector/message support; that portion is **not DOS installation proof**. A return address/callback sentinel is research scaffolding outside the original binary, not an IBM BIOS implementation.

### 4.3 Executed cases

- Both init-only optical self-tests reach their actual `Test complete - OK` result under the clear fixture. The3.02 settling output is003, a produced loop parameter, not a factory timing constant.
- All40 single X beams and24 single Y beams, in both versions, produce the documented reduction sequence; adjacent pairs, disjoint masks, missing axes and no-touch are recorded.
- Both versions reject X18/Y8..15 because the middle usable Y byte isFF. A global-centroid substitute would report a contact incorrectly.
- A synthetic changing optical path first succeeds with neighboring receiver21h/emitter22h, then fails; subsequent calibration retains receiver21h and succeeds with emitter21h. This exercises the receiver-survival nuance across passes.
- Obstruction during calibration removes usable bits. Clear input plus INT33 reset does not restore them; the report records the resulting masks.
- A recognized top40/active400/physical480 response exercises crop/rescale. A recognized active height100 is ignored by3.02 but transformed by2.4.
- POINT corner/center/no-touch records and actual DOS strategy/interrupt partial reads are executed. Requests2,3,8 return2,3,5 bytes which concatenate to `1,037,012\r`; the packet status is0200.
- Normalized Y9137 with rows-minus-one29 emits row028 because remainder4999 rounds upward. This distinguishes the integer code from mathematical half-up.
- Mouse reset, position/bounds, button following/release, counters/current-position reporting, keyboard modifier mapping, equal-X-bound anomaly and selected private settings are exercised. The full set of documented functions is disassembled; **not every graphics cursor and mode combination was executed**.
- Callback delivery occurs through actual timer-handler instructions every second eligible tick in the fixture, with a real far-return client boundary; foreground polling and old-handler chaining remain distinct.
- ADC completion failure and missing post-read re-arm produce original failure behavior, not a forced pass. Runtime bounded polling is not treated as an exception invented by the host.
- The absent-interface3.02 path performs its original IBM-mouse initialization sequence and processes an explicit relative packet.
- Both initialization packet paths are executed with a request at7000:0000 and an INT10 fixture that preserves BX. The displaced status store at segment:0204 is recorded; actual DOS evidence below establishes a different, broader boundary.
- Light-pen function58 reports row25 in2.4 versus12 in3.02 for the same settled contact. With no contact, function4 setting Y=0 followed by58 raises divide-error INT00 in2.4; the fixture records the exception, not execution of a DOS error handler.

Results are retained in [TOUCH-TRACE.json](../ANALYSIS/TOUCH-TRACE.json). The legacy-named `extended_3_02` section also contains explicitly version-tagged comparisons. [TOUCH.md](TOUCH.md) and [DRIVER_ABI.md](DRIVER_ABI.md) distinguish the hardware, driver-private and public-ABI consequences.

## 5. Video and CPU diagnostic experiments

### 5.1 COLORFIX and font staging

[video_trace.py](../TOOLS/video_trace.py) runs the real COLORFIX installer/hook. Its DOS interrupts are intercepted and the hook stops on entry to the saved old INT10; no display is rendered. All256 AH09 attribute inputs match the decoded transformation: **112 change,144 remain unchanged**. Other sampled AH functions preserve BX. The installer changes BDA40:96 fromFF toEF while40:89 remainsFF.

The same tool executes the retained107-byte Model25 font-staging window at F000:23A0–240A with three glyphs at heights14/16 and block2. Every output row is checked, including duplicated last rows in the14-high case. This is staging only, not the SRAM transfer engine or7690 BIOS.

The retained window was independently checked against the full identified Model25 type1 ROM. To repeat that optional provenance check:

```sh
uv run --with unicorn==2.1.4 python TOOLS/video_trace.py \
  --model25-rom /Users/josh/src/bios8530/goldens/8525/type1/linear.bin \
  --output /tmp/7690-video-with-baseline-check.json
```

Without that option, the self-contained byte window and its original-ROM hash remain explicit in the report. No complete target ROM is synthesized.

### 5.2 LCD diagnostic RAM routines

Both supplied IBM7690.DGS revisions execute their real fill, constant-verify, address-fill and address-verify routines. The literal fixture has full-byte index/row/column latches and separate upper/lower RAM dictionaries. Fill counts are128 row writes and8192 writes each to column/upper/lower data. Intact patterns return carry clear; a corrupted upper constant byte and lower address byte return carry set.

A deliberately six-bit-masked column fixture fails after the verifier disturbs column0 and then reads column40h. This rejects that **simple decoder plus literal-write model**; it does not establish the real physical address width or eliminate pipeline/strobe interpretations. The experiment does not execute the RAM orchestrator, LCD sync/reset/readback tests, adapter BIOS or a full diagnostic suite. [VIDEO-TRACE.json](../ANALYSIS/VIDEO-TRACE.json) records the original-instruction results; [video_evidence.json](../ANALYSIS/video_evidence.json) retains primary tables and the broader static analysis.

### 5.3 CPU0 ROM and clock prerequisites

[platform_trace.py](../TOOLS/platform_trace.py) enters CPU0 at0159h and stops on the original failure branch0133h or successful boundary01AEh, before NMI. It exercises:

- all-zero and all-FF synthetic ROMs: fail AL05 despite zero whole-image sums;
- opposing errors in different8-KiB blocks: fail despite zero whole-image sum;
- a changed second read of the same byte: fail stability check;
- a synthetic00/FF checkerboard: pass this narrow gate, proving it is not authentication;
- both identified complete Model25 ROM images: reach01AEh, not a target POST or full CPU0 pass.

Separate direct entries at025Bh supply absent date or time BIOS services. Both take the real AL3Dh common error path, not a skip. No RTC chip, alarm delivery, NMI, PIT/PIC/DMA or full-module execution is simulated by this tool.

The self-contained command runs synthetic cases. Optional baseline comparisons used for the retained [PLATFORM-TRACE.json](../ANALYSIS/PLATFORM-TRACE.json):

```sh
uv run --with unicorn==2.1.4 python TOOLS/platform_trace.py \
  --model25-rom /Users/josh/src/bios8530/goldens/8525/type1/linear.bin \
  --model25-rom /Users/josh/src/bios8530/disasm/m25/type2/src/m25_seg.bin \
  --output /tmp/7690-platform-with-baselines.json
```

Those full ROM paths are external comparison inputs. The ordinary handbook and synthetic experiment do not require them.

## 6. Actual DOS boot and driver/client proof

### 6.1 Runtime setup

A supervised QEMU11.0.3 process ran a generic `pc` with16MiB RAM, one **read-only floppy**, no hard disk, no display window, a monitor and QMP socket. Readiness was observed. Input was delivered through emulated keyboard events. QMP `screendump` produced the PNGs; physicalB8000 text memory produced the paired80×25 CP437 text captures. The process was stopped after the scenarios.

Equivalent interactive launch for a prompt variant:

```sh
python3 TOOLS/build_diagnostic_disk.py \
  --donor /Users/josh/src/JoshRodd/IBM5140_REF/DOS/PCDOS32.IMG \
  --output /tmp/7690-prompt.img --startup prompt
qemu-system-i386 -machine pc -m 16M \
  -drive file=/tmp/7690-prompt.img,format=raw,if=floppy,readonly=on \
  -boot a
```

For write/format testing use a disposable copy or snapshot overlay, not the retained original or a host device. The **16MiB setting is solely for contemporary SeaBIOS**: an earlier640-KiB generic run stalled before video. It is not the target's documented640-KiB configuration and cannot establish8086 behavior.

### 6.2 Observed screens and commands

| Scenario | Actual observation | Captured surface |
|---|---|---|
| Corrected prompt derivative | Derived banner and A> prompt, no Bad command error |[PNG](../ANALYSIS/dos320-boot.png), [text](../ANALYSIS/dos320-boot.txt)|
| `VER` |IBM Personal Computer DOS Version3.20|[PNG](../ANALYSIS/dos320-ver.png), [text](../ANALYSIS/dos320-ver.txt)|
| `DIR /W` |Diagnostic files/marker,23 visible files,555008 free bytes|[PNG](../ANALYSIS/dos320-dir.png), [text](../ANALYSIS/dos320-dir.txt)|
| `TYPE AUTOEXEC.BAT` |Correct generated ECHO OFF/banner/instructions|[PNG](../ANALYSIS/dos320-autoexec.png), [text](../ANALYSIS/dos320-autoexec.txt)|
| Manual `SERVICES` |INCORRECT DIAGNOSTIC DISKETTE / IBM MODEL7690 refusal|[PNG](../ANALYSIS/dos320-services-gate.png), [text](../ANALYSIS/dos320-services-gate.txt)|
| Retained default menu image |Automatically reaches the same expected firmware refusal|[PNG](../ANALYSIS/dos320-menu-firmware-gate.png), [text](../ANALYSIS/dos320-menu-firmware-gate.txt)|
| CONFIG loads3.02 |Real DOS driver banner; touch absent, using IBM mouse; prompt|[PNG](../ANALYSIS/dos320-driver-load.png), [text](../ANALYSIS/dos320-driver-load.txt)|
| Actual DOS POINT client |Open/read succeeds; bytes30 0D, returned count2; exits to DOS|[PNG](../ANALYSIS/dos320-point-consumer.png), [text](../ANALYSIS/dos320-point-consumer.txt)|
| Original mixed disk |Date/time prompts with no AUTOEXEC|[PNG](../ANALYSIS/msdos500-original-startup.png), [text](../ANALYSIS/msdos500-original-startup.txt)|
| Mixed disk `VER` |MS-DOS Version5.00|[PNG](../ANALYSIS/msdos500-original-ver.png), [text](../ANALYSIS/msdos500-original-ver.txt)|

The two hidden DOS system files explain why the25 root files yield23 visible DIR entries in the no-CONFIG image. The DOS client was assembled by NASM, copied only to a disposable driver-enabled derivative and run as `POINTCHK`. It opens `POINT` with INT21/3D, reads up to10 bytes with3F, closes with3E, prints through DOS and exits through4C. Its full source, bytes and hash are retained inside [DOS-BOOT-TRACE.json](../ANALYSIS/DOS-BOOT-TRACE.json), not as an unexplained permanent executable. Its single-digit count display is sufficient for this **two-byte idle case**, not a general active-record viewer.

To reproduce the driver-loading scenario, add `--touch-driver --startup prompt` to the builder. To reconstruct the disposable consumer, extract `source_asm` from the probe object in DOS-BOOT-TRACE.json, assemble with `nasm -f bin`, and use `mcopy` to place it on a **fresh copy** of that derivative. Do not modify a mounted/retained source image. The record proves actual DOS character-device access in IBM-mouse fallback; it does not prove the optical hardware or an active mouse packet through a real7690 interrupt path.

### 6.3 A defect actually found during the smoke

The first generated AUTOEXEC used `@ECHO OFF`. PC DOS3.20 printed `Bad command or file name`; the preserved interpreter does not support that newer batch prefix. The generator was corrected to **`ECHO OFF`**, fresh variants were rebuilt and the shown screens no longer contain the error. The original archived `LEDINST.BAT` also begins with `@echo off`; it was **not edited** to make an original artifact look cleaner.

Expected SERVICES refusal was not suppressed or patched. The program compares F000:FFFE againstFA and exactly25 copyright bytes at F000:000C. SeaBIOS is not compatible target firmware. Reaching this refusal proves DOS boot and program execution, not a successful firmware gate or diagnostic menu.

## 7. Review and final audit discipline

Independent read-only reviews checked the hardware/diagnostic chapters against primary images and original instruction bytes. Material corrections were integrated: set2 break-continuation timing, version-specific LCD crop guard, broad-Y-mask rejection, retained receiver substitution, odd-divisor POINT rounding and CPU0's mandatory clock dependency. Executable cases now cover the touch-algorithm corrections; primary image/byte checks cover the timing and hardware statements. Review conclusions are not substituted for runtime or physical evidence.

The retained evidence is designed to be audited without trusting chapter prose: compare original hashes, parse all JSON, check local links, inspect page locators and verify declared code windows against their identified inputs. [AUDIT.json](../ANALYSIS/AUDIT.json) records the final structural/source/evidence checks on the delivered tree. Such checks do not validate every English sentence or establish physical behavior.

No project-wide test suite, emulator implementation, placeholder ROM, patched diagnostic, documentation-only test asserting wording, or permanent disposable POINT executable was added. The small retained tools are **reproduction tools for real source/byte/behavior evidence**, not a mock7690 presented as complete.

## 8. Explicitly unverified

- Authentic7690 reset/POST and C000 initialization, exact target ROM revision/checksums/descriptors, and a full SERVICES/DGS diagnostic run.
- Physical8086/bus/DMA/refresh timing, undocumented gate-array aliases/reset defaults, actual clock chip and alarm routing.
- Analog optical transfer, conversion/settling timing, environmental noise, physical selector wiring/edge polarity and the actual effect of DGS's F306 write.
- LCD scanout and physical presentation: active-area dimensions/aspect, calibrated foreground/background, luminance, response, LP phase, buffer routing, any FRC, and real per-mode adapter-BIOS values.
- Real keyboard/barcode-controller firmware, all electrical serial/parallel handshakes, wrap plugs, and user judgment of diagnostic display/barcode tests.
- Driver graphics cursor rendering in every mode, every possible private-API parameter combination, concurrent direct diagnostic/driver ownership, and active optical input through actual DOS.
- Physical mains loss, battery aging/exhaustion, rail transition timing and off-state clock persistence.
- Running KQPW, its communications host, or reconstructing the missing original1.10 master disk from loose files.

These are evidence boundaries for future implementers, not claims silently filled by synthetic responses.
