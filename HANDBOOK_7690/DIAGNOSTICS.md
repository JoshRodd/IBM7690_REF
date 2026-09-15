# Diagnostic media, boot construction, and executable test oracles

This chapter keeps three things separate: the photographed IBM Version 1.10 diagnostic product, the supplied **loose files** associated with it, and the **later mixed MS-DOS/KQPW disk image**. A fourth object—the disk made by this repository's builder—is an explicitly derived research medium. None is a supplied dump of the workstation's system or interface-adapter ROM.

**Evidence labels:** **DOCUMENTED** means the IBM publication or photographed label says it; **BINARY** means supplied bytes establish it; **INFERENCE** identifies an interpretation; **OPEN** means the supplied evidence does not settle it. Successful DOS boot is not successful IBM 7690 emulation. A diagnostic menu is not successful execution of its hardware tests.

## 1. Sources and coordinate conventions

* [Guide to Operations](../IBM_7690_Clinical_Workstation_Guide_to_Operations.pdf), printed 1-6–1-14 and 3-1–3-10; [searchable extraction](../DOCUMENTATION/OCR/OPERATIONS.txt), particularly lines 514–695 and 960–1303. These are two-page spreads: **PDF page 15** contains printed 1-10/1-11, **PDF page 26** contains printed 3-4/3-5, and **PDF page 27** contains printed 3-6/3-7. The error numbers in §9 were checked visually against rendered PDF page 27, not accepted from OCR alone.
* [Technical Reference](../IBM_7690_Clinical_Workstation_Technical_Reference.pdf), touch-panel and interface-adapter descriptions; see [TOUCH.md](TOUCH.md), [VIDEO.md](VIDEO.md), and [PERIPHERALS.md](PERIPHERALS.md) for register ownership. This chapter describes what diagnostic code does, not a second, competing hardware specification.
* [Photographed disk](../7690diag.jpg), SHA-256 `8510a07d4599922e09c37630ae161c0744233219373aac4d2f98e4145299356a`.
* [Full image inventory](../ANALYSIS/media_kqpw.json), [DOS donor inventory](../ANALYSIS/media_pcdos32.json), [all loose/common-file hash comparisons](../ANALYSIS/media_comparison.json), [diagnostic string inventory](../ANALYSIS/diagnostic_strings.json), and [module descriptors](../ANALYSIS/diagnostic_modules.json).
* Disassemblies: [SERVICES.COM](../ANALYSIS/diagnostic_SERVICES_COM_disassembly.txt), [DIAGS.COM](../ANALYSIS/diagnostic_DIAGS_COM_disassembly.txt), [IBM7690.DGS restarted at known routine boundaries](../ANALYSIS/diagnostic_IBM7690_routines.txt), and [full linear DGS decode](../ANALYSIS/diagnostic_IBM7690_DGS_disassembly.txt). **The COM listings use origin 0100h: subtract 0100h to obtain file offsets. DGS listings use origin zero: displayed addresses are file offsets.** Text and tables are not instructions; the full linear listing can become misaligned across data. Use the restarted listing for the callable DGS routines.
* Boot listings: [PC DOS 3.20 donor](../ANALYSIS/diagnostic_boot_pcdos32.txt) and [KQPW/MS-DOS image](../ANALYSIS/diagnostic_boot_kqpw.txt). Their displayed address minus 7C00h is the image byte offset.

All hexadecimal offsets below are **file offsets** unless expressly called COM execution addresses. Full SHA-256 values in the JSON artifacts disambiguate every supplied revision.

## 2. What was actually supplied

### 2.1 Label and loose Version 1.10 files

**DOCUMENTED, photograph:** label `SA12-7007-00`, `IBM 7690 Clinical Workstation Customer-Level Diagnostic Diskette`, `Version 1.10`, copyright International Business Machines Corp `1981, 1990`, licensed material/program property of IBM. The shutter says `3.5 Diskette 1.0 MB capacity`: this is the unformatted-capacity terminology of the 720-KiB medium, not evidence of a one-megabyte sector image. Operations printed 1-11 and 1-13 explicitly specify low density, 1.0 Mb unformatted/720 Kb formatted.

**BINARY:** `7690diag/` contains 21 files, 94,448 logical bytes and 102 one-KiB clusters when allocated on this FAT geometry. `VERSION.110` is only `0D 0A 1A`; its **extension**, not its contents, carries the version. There is no boot sector, FAT, root directory, `IBMBIO.COM`, `IBMDOS.COM`, `COMMAND.COM`, `CONFIG.SYS`, or `AUTOEXEC.BAT` in the loose set. Filesystem modification times on extracted host files cannot reconstruct the original directory timestamps, deleted entries, boot code, DOS identity, or physical sector defects. The label establishes product identity; it does not prove every loose byte was read from that particular photographed disk.

### 2.2 The supplied image is not a pristine Version 1.10 diagnostic disk

**BINARY:** `7690KQPW.IMA` is exactly 737,280 bytes, SHA-256:

```
6b89fe1a982eb7e480fb1757ca0285d9889e0154f18611a8e57cc4a8bb8997fe
```

It contains bootable-form MS-DOS 5.00 system files, Version 1.00 diagnostic-marker naming, IBM diagnostics, and later application/utilities. `KQPW.TXT` lines 11–15 say `TIM_TERM SYSEM`, `(C) 1989,1994 KQPW`, and `INSERT CARD AND SLIDE TO LEFT`. Files include `TIM_TERM.EXE`, `SAYWHAT.COM`, `VIDPOP.COM`, `.SQZ` screens, `SQUEEZE.COM`, `SWINST.COM`, `IMPORT.COM`, and `POP.COM`. Their presence is not proof of an automatic startup path: **the active root directory has no AUTOEXEC.BAT**. Its 13-byte `CONFIG.SYS` is exactly `country=001\r\n`; it does not load LEDTOUCH.

The boot OEM field is `MSDOS5.0`, but the DOS identity is independently supported by strings:

| Image file | File offset | Embedded evidence |
|---|---:|---|
| `IO.SYS` | 7D02h | `MS DOS Version 5.00 ... 1981-1991 Microsoft ...` |
| `MSDOS.SYS` | 01FCh string run | `MS DOS Version 5.00 ...` follows an incidental leading `D` in the printable run |
| `COMMAND.COM` | 1EA0h | `Microsoft(R) MS-DOS(R) Version 5.00` |
| `IBMBIO.COM` | 7D1Ah | Also MS-DOS Version 5.00 text, despite the IBM-looking filename |
| `IBMDOS.COM` | 01FCh string run | Also MS-DOS Version 5.00 text |

`IO.SYS` is 33,430 bytes, `IBMBIO.COM` 33,462; `MSDOS.SYS` and `IBMDOS.COM` are both 37,394 bytes but **are not byte-identical**. Do not infer PC DOS from the `.COM` aliases. The boot sector searches **IO.SYS then MSDOS.SYS** in the first two root slots; the later `.COM` files are not that boot sector's system-file selection.

### 2.3 Complete cross-revision comparison

Nineteen names are common to loose files and image: fifteen are byte-identical, four differ. Image-only files and every root entry/hash/chain are enumerated in `media_kqpw.json`; all loose hashes are in `media_comparison.json`.

| Name | Loose bytes | Image bytes | Comparison |
|---|---:|---:|---|
| COLORFIX.COM | 267 | absent | Loose-only; not invoked automatically by the builder |
| CPU0.DGS | 2,942 | 2,942 | Identical |
| DCOPY.COM | 2,172 | 2,172 | Identical |
| DFORMAT.COM | 906 | 906 | Identical |
| DIAGS.COM | 3,338 | 3,338 | Identical |
| DISPLAY1.DGS | 5,557 | 5,557 | Different: 1,186 byte positions |
| DSKT1.DGS | 4,800 | 4,800 | Identical |
| DTMEDTE.COM | 1,395 | 1,395 | Identical |
| IBM7690.DGS | 10,474 | 11,333 | Different |
| LEDINST.BAT | 1,426 | 1,426 | Identical |
| LEDTOUCH.SYS | 8,111 | 7,021 | Different; see DRIVER_ABI/TOUCH |
| NSTALL.EXE | 9,918 | 9,918 | Identical |
| PAR1.DGS | 601 | 601 | Identical |
| RBT.EXE | 7,828 | 7,828 | Identical |
| SER0.DGS | 3,039 | 3,039 | Identical |
| SERVICES.COM | 21,696 | 21,696 | Different: 186 byte positions |
| STG0.DGS | 1,675 | 1,675 | Identical |
| TXT.OK | 602 | 602 | Identical |
| US0KMAIN.DGS | 1,602 | 1,602 | Identical |
| US0PCN.DGS | 6,096 | 6,096 | Identical |
| VERSION.110 | 3 | absent | Image instead has VERSION.100, same three payload bytes |

The four changed loose SHA-256 values are:

```
DISPLAY1.DGS f1dbe20f6a5f1b2624f8f461f7beb756b1f3d94c467d036b8e8d1e5d31717f61
IBM7690.DGS e44671fa1565793365a748743e364b4be4027c12f012b9b687c8047b2459fa57
LEDTOUCH.SYS bfb95e3a5d1a9ef87742b33b19d33fee2fbcb0718f04995f770b0a3c37d6d2df
SERVICES.COM b20e20228d14eb0587050e5c350e33b709b5240fc27d68d78d8ba964ec1a1028
```

The image counterparts are respectively:

```
3e9fbd1cba041d71c48088bf5bde7c4b10e300967ebb26d60fc794c0bc0defa7
be20cd798aef2f63d4c094bf71ebf02376b53fc31011e80a0d8595fa5a3fe4f4
1c3dc5a2c4a9c6d422f03f92db6b3bcc2b314939603a117594e9573eb7ee2613
adc59a24633e0172c1fcf332e242dde16b8250035694151c5f61878e6f9c577a
```

**BINARY:** SERVICES bytes before 16A2h are identical across revisions; the changes occur in the message-resource region, including copyright and gray-level descriptions. DISPLAY1 is not merely a copyright edit. IBM7690 and LEDTOUCH have substantive size/revision differences. **INFERENCE:** the image preserved older diagnostics alongside a later application/DOS installation. It is not evidence that IBM shipped this combined disk, MS-DOS 5, or KQPW in 1990.

## 3. Sector, FAT, root, and boot-chain contract

Both supplied image and DOS donor have the same basic FAT12 geometry:

| BPB field | Offset | Value |
|---|---:|---:|
| Bytes/sector | 0Bh, word | 512 |
| Sectors/cluster | 0Dh, byte | 2 |
| Reserved sectors | 0Eh, word | 1 |
| FAT copies | 10h, byte | 2 |
| Root entries | 11h, word | 112 |
| Total sectors | 13h, word | 1,440 |
| Media descriptor | 15h, byte | F9h |
| Sectors/FAT | 16h, word | 3 |
| Sectors/track | 18h, word | 9 |
| Heads | 1Ah, word | 2 |

Thus 80 cylinders × 2 heads × 9 sectors × 512 bytes = 737,280 bytes. LBA0 is boot, LBA1–3 FAT1, LBA4–6 FAT2, LBA7–13 fixed root directory, LBA14–1439 data. FAT offset is 0200h, second FAT 0800h, root 0E00h, data 1C00h. There are 713 data clusters, numbered 2–714. Each FAT entry is 12 bits: even cluster uses the low 12 bits of the word at `floor(3*c/2)`, odd the upper 12. Values FF8h–FFFh terminate a chain; 000h is free and FF7h bad. Do not treat FAT12 as FAT16 because there are 16-bit unaligned loads in a host implementation.

**BINARY:** both FAT copies match in both supplied images. The mixed image has 57 free clusters (58,368 bytes). Its BPB extended label is `NO NAME    ` while its root volume-label entry is `DISK      1` (see raw 11-byte field in JSON); these are distinct fields, not a reason to rewrite either. The inspector reports active root entries only; deleted records and unused sectors remain in the original image but are not presented as active files.

### 3.1 Mixed-image boot sequence

The boot sector SHA-256 is `cd0daf3e0810677b393d827efa9859a71dcecf4ea5eb7c3e3e7b1d8fdd5a6f36`; signature bytes at 1FEh are `55 AA`.

1. Short jump at zero enters 003Eh. It establishes a real-mode stack at 0000:7C00, copies/adjusts the diskette parameter table through INT 1Eh's vector at physical 0078h, and resets disk services via INT 13h.
2. It computes root and data LBAs from the BPB; reads the first root sector to 0000:0500.
3. At 00D7h–00EBh it compares the first two directory names to the 11-byte strings at 01E6h/01F1h: `IO      SYS`, `MSDOS   SYS`.
4. At 0105h it obtains the first file's starting cluster from the directory, translates it to data LBA, and reads **three consecutive sectors** to 0000:0700 using INT 13h. It does not perform a general FAT chain walk in these 512 bytes.
5. At 014Dh it far-jumps to 0070:0000. The loaded IO.SYS prefix continues the DOS bootstrap.
6. Read/name failures print `Non-System disk or disk error`, prompt to replace/press a key, restore the diskette parameter vector, and invoke INT 19h.

Root slot0 IO.SYS starts at cluster2 with attributes 27h; slot1 MSDOS.SYS starts at35, also27h. Slot3 COMMAND.COM starts at73 with attributes20h. Bits of 27h are read-only, hidden, system, archive. A file-copy tool that relocates the boot-critical prefix or reorders root entries can make superficially complete media unbootable.

### 3.2 PC DOS 3.20 donor sequence and why preservation matters

Donor: `IBM5140_REF/DOS/PCDOS32.IMG`, SHA-256 `87b5cc84562cdf90b367c5c575680f3d37de92cc2f684033b15299015a568915`; boot SHA-256 `c8c1da9c4b616dd730c32e279c43821b2d21157396e3f8e6eef6a88aed8bca10`.

This is inherited **DOS media**, not IBM 7690 firmware or an original clinical diagnostic master. `COMMAND.COM` at 11B4h says `The IBM Personal Computer DOS`; at 11D3h it says `Version 3.20 ... 1981, 1986`.

Its boot code starts at0036h, reads the first root sector to0500h, compares root slot0/slot1 to `IBMBIO  COM`/`IBMDOS  COM` at00A9h–00C0h, derives the first system file's sector count from its directory size at00DAh–00E5h, and loads sectors **consecutively from the beginning of the data area**, not from arbitrary FAT-linked clusters. It reads track-sized chunks and jumps at0124h to0070:0000. Preserving the first file's name alone is therefore insufficient.

| Preserved donor object | Root slot | Attributes | Clusters | Logical bytes | SHA-256 |
|---|---:|---:|---|---:|---|
| IBMBIO.COM | 0 | 27h | 2–17 | 16,369 | `841bf028620d0867293d7ba7613772f07e2681f36442182d2fa439133343fd8f` |
| IBMDOS.COM | 1 | 27h | 18–45 | 28,477 | `bbe0ad857e91f1f077af287d2f6748bd868983be9585a6cb0bba7c52dd42f789` |
| COMMAND.COM | 9 | 20h | 131–154 | 23,791 | `77402f36394f77fa8270f0563068f7f75949ce030dd28ec9fee7383f1e0b64db` |

The builder preserves the **complete original 32-byte directory entries, every chain link, all allocated cluster bytes including slack, and all 512 boot bytes** for these files. Keeping COMMAND at its original location is conservative and simplifies reproducibility; the documented first-stage requirement specifically concerns the system-file ordering and IBMBIO's consecutive placement.

## 4. Reproducible derived disk, without a destructive format

[TOOLS/build_diagnostic_disk.py](../TOOLS/build_diagnostic_disk.py) is a Python-standard-library FAT12 editor, not a shell script that assumes `COPY` makes a boot disk. [TOOLS/inspect_media.py](../TOOLS/inspect_media.py) provides its parser and a standalone read-only root/chain/hash report. Run from the repository root:

```sh
python3 TOOLS/build_diagnostic_disk.py \
  --donor /Users/josh/src/JoshRodd/IBM5140_REF/DOS/PCDOS32.IMG \
  --output ANALYSIS/7690diag-menu.img
```

For a generic-PC DOS boot smoke, avoid automatic model-check rejection/reboot:

```sh
python3 TOOLS/build_diagnostic_disk.py \
  --donor /Users/josh/src/JoshRodd/IBM5140_REF/DOS/PCDOS32.IMG \
  --output ANALYSIS/7690diag-prompt.img --startup prompt
python3 TOOLS/inspect_media.py ANALYSIS/7690diag-prompt.img
```

### 4.1 Deterministic construction rules

1. Read donor and loose sources only. Require the exact documented donor SHA-256 and exact 21-name loose-file set; record every loose input hash in the manifest. The builder does not certify modified loose payloads as original: compare its manifest with `media_comparison.json` for that purpose.
2. Work on a bytearray copy. Preserve the three files in §3.2. Reclaim all other donor file clusters, zero reclaimed/free data-cluster contents, and clear non-preserved root entries. This drops general DOS utilities, not boot-critical DOS files; the original donor is never modified.
3. Install all 21 loose files plus generated AUTOEXEC.BAT, in ASCII-sorted name order, using ascending free root slots and clusters while skipping preserved slots/clusters. Update both packed FAT12 copies. Free clusters start at46; preserved COMMAND clusters131–154 remain occupied, so a large allocation can legitimately be fragmented around them.
4. New entries get archive attribute20h and the fixed synthetic timestamp **1990-01-01 00:00:00**. This timestamp is reproducibility metadata, not a recovered IBM date. Source host timestamps are not used.
5. Internal construction invariants reparse the result, compare all installed payloads, check FAT-copy identity and boot/system-entry/chain/cluster preservation. These checks are not a CPU boot test.
6. Create output and manifest exclusively. Existing paths are refused, including the usual case of accidentally naming an original as output. No raw-device operations, host formatting, or modification of sibling media occurs. The default manifest is `OUTPUT.img.json`.

The preserved DOS files occupy68 clusters, loose files102, and AUTOEXEC one. With default no CONFIG, 171 clusters are occupied and **542 clusters/555,008 bytes remain free**. Loading the driver adds one CONFIG cluster, leaving541/553,984 bytes. No invented diagnostic master boot sector is needed.

### 4.2 Startup is an explicit research choice

Default AUTOEXEC contains an identifying `ECHO` banner then `SERVICES`. The prompt variant prints the same derived-media banner and instructs the operator to type SERVICES only on a compatible IBM firmware/hardware model. AUTOEXEC suppresses the interactive DOS startup date/time sequence; the diagnostics' own Set Time and Date remains a separate utility.

By default **no CONFIG.SYS is generated and LEDTOUCH.SYS is not resident**. IBM7690.DGS accesses the touch interface directly, and a background driver owning the same latches would complicate the oracle. The complete driver and installer remain on disk. `--touch-driver` deliberately adds `DEVICE=LEDTOUCH.SYS\r\n` for driver-oriented work; this is not the default diagnostic arrangement, nor a reconstruction of the absent original CONFIG.

The builder does not invoke COLORFIX, LEDINST, FORMAT, or DCOPY. It does not patch SERVICES' ROM checks. It does not modify the KQPW image or borrow its later MS-DOS system files. A manifest labels the result as **derived research disk, not original IBM diagnostic media**.

### 4.3 Boot-smoke protocol and limits

A generic x86 machine can establish that this preserved PC DOS boot chain works. Example launch, with snapshot writes and **no hard disk**:

```sh
qemu-system-i386 -machine pc -m 16M \
  -drive file=ANALYSIS/7690diag-prompt.img,format=raw,if=floppy \
  -boot a -snapshot
```

Observe the derived banner and DOS prompt, run `VER`, `DIR`, and `TYPE AUTOEXEC.BAT`; expect PC DOS Version3.20, the loose diagnostic files and VERSION.110, no unexplained application startup. This is a **generic PC DOS smoke**, not an 8086/Model25/7690 acceptance claim. An AT-like QEMU machine is inappropriate evidence for LCD, RTC, touch, keyboard, bus timing, or genuine 7690 ROM compatibility.

The generic smoke uses 16 MiB because the contemporary SeaBIOS/QEMU startup did not reach display initialization with `-m 640K`; that host test configuration is **not** the target's 640-KiB RAM specification. Generated AUTOEXEC uses `ECHO OFF`, not `@ECHO OFF`: the latter produced `Bad command or file name` on the preserved PC DOS3.20 command interpreter. The original `LEDINST.BAT` is preserved verbatim and also begins with `@echo off`; that original batch's first-line compatibility issue does not require modifying the archived file.

For determinism, build again to a distinct unused filename with identical options, then compare image SHA-256 values. Different output pathnames do not enter image bytes. Retain original and manifest hashes alongside any test result. Use snapshot/copy-on-write media for menus that can write or format; never point an emulator at a raw host device.

**EXECUTED:** this smoke was run with QEMU11.0.3 and SeaBIOS1.17, using read-only floppy media. The preserved [menu image](../MEDIA/7690diag-pcdos320.img) boots and automatically reaches SERVICES' expected **IBM MODEL7690 / INCORRECT DIAGNOSTIC DISKETTE** refusal on generic firmware. A prompt variant reports PC DOS3.20 and555,008 free bytes. A separate driver-enabled variant loads unmodified LEDTOUCH3.02, selects IBM-mouse fallback, and a real DOS handle-based client opens `POINT` and reads the two-byte idle record `30 0D`. The supplied mixed image independently boots MS-DOS5.00 to its date/time prompts. [DOS-BOOT-TRACE.json](../ANALYSIS/DOS-BOOT-TRACE.json) records exact variants, hashes, observations and the disposable client's bytes; [VERIFICATION.md](VERIFICATION.md) links actual screen captures. No successful identity gate, 7690 diagnostic menu, target ROM POST, or DOS optical-touch path was exercised.

## 5. SERVICES is a resident diagnostic environment, not just a menu

All offsets in this section concern loose SERVICES SHA `b20e2022…1a1028`. These mechanisms are also byte-identical in the image revision up to16A2h.

### 5.1 ROM gate: a necessary but very insufficient compatibility test

At file01C3h (COM02C3h), SERVICES loads DS from its word at file0080h (`00 F0`, segment F000h) and reads `[DS:FFFE]`. It compares AL toFAh. It then compares exactly25 bytes at **F000:000C** with its25-byte text at file0060h, `COPYRIGHT IBM CORPORATION`, as specified by `CX=0019h`. The comparisons occur at file01CCh and01F4h–0207h. Failure selects `INCORRECT DIAGNOSTIC DISKETTE`, explanatory IBM MODEL7690 text, and the restart path.

Do not satisfy these tests by blindly spoofing a model byte/copyright string and then label the emulator authentic. Model25-derived firmware is a separately sourced baseline; it is not an actual supplied 7690 ROM. Failing this gate on a generic ROM is expected and does not mean the constructed FAT disk failed to boot. Passing the gate proves two comparisons, not compatibility of interface-adapter ROM signatures/checksums, BIOS services, diagnostic timing, or ports.

### 5.2 Private interrupts and stack-segment state

At file04DEh onward, SERVICES initializes its resident environment. The loop at COM060Ah copies36 offset words from COM062Dh into IVT entries starting at physical0200h, attaching SERVICES' CS to each: **INT80h–INTA3h** become diagnostic services. It also writes INT1Bh and conditionally INT09h. It saves the old keyboard IRQ vector, installs INT22h/23h/24h handlers, and saves/restores INT1Eh around child operations. These are **software-owned hooks**, not IBM BIOS interrupts to implement in firmware.

Messages commonly use INT9Fh with a selector word at `SS:0070`, parameter byte at`SS:0072`, and BX pointing to message substitutions; the feature DGS also uses INT82h for its own length-prefixed/string resources. Shared diagnostic bookkeeping is frequently addressed through SS rather than DS: the child can change DS to its module while SS still refers to the resident control environment. A shortcut loader that launches DIAGS.COM as a completely independent normal DOS process does not recreate this state.

### 5.3 Child loading is not DOS EXEC

SERVICES file0414h–047Ch selects the utility, obtains a load segment from its resident allocation pointer, creates a PSP using INT21h/AH26h, sets DTA to the new segment's0100h (AH1Ah), opens a DOS FCB (AH0Fh), sets one-byte record size, and reads with AH27h/CXFFFFh. It then sets DS/ES to that segment and uses a constructed far return to enter offset0100h. The resident stack and private interrupt services survive. File0496h–04B8h covers the FCB open helper; file047Dh–04A5h covers loading failure and the reinsert-diagnostic-disk prompt.

Consequences for a DOS or emulator implementation:

* Implement FCB services, including DTA segment ownership, record size, returned count/status and search continuation. A handle-only INT21h implementation that happens to run COMMAND is not enough.
* Preserve real-mode segment arithmetic and DOS PSP behavior. Do not synthesize the diagnostic menu instead of executing this path.
* Keep callbacks and resident stack state valid across module loads and interactive tests.
* On absent/changed media, surface actual read/reinsert flow; do not replace failed reads with zero-filled fake modules.

## 6. DIAGS.COM module discovery and calling convention

DIAGS SHA-256 is `ba9a7d2974e568e0cd80def9541613c173c30b4e5e77368c9e4ce2303498ae14`; its3338 bytes are identical across supplied revisions. Its file0003h signature is `EDSYEDSDCP`, and file003Eh contains wildcard FCB name `????????DGS`.

### 6.1 Discovery

At file0225h (COM0325h), it reserves space after itself in paragraph units. At file0237h it clears a99-entry, six-byte internal device table (COM0BB8h). At file0248h–033Ch it copies the wildcard FCB, uses INT21h/AH1Ah to set the DTA, AH11h/AH12h for Find First/Next, AH0Fh/10h for FCB open/close, and AH27h for one-byte-record reads. Files load at offset zero in successive paragraph-aligned segments, not offset0100h. INT12h supplies the conventional-memory bound; a too-large module is not registered as successfully loaded.

### 6.2 Two descriptor layouts coexist

The comparison routine at file01F7h (COM02F7h) compares four bytes at module+3 against its own `EDSY`. It is a **binary-format discriminator**, not a general authenticity test.

* EDSY modules: descriptor table starts at0013h; fixed five-byte records consist of three executable entry bytes, a device byte, and a fifth metadata byte. A zero entry begins the terminator.
* Non-EDSY modules: descriptors begin at0000h; each has the same three entry bytes and device byte, then a name-length byte and that many name bytes. The next descriptor is at`current+5+length`. The executable entry is generally a jump over descriptors and messages.
* Device byte bit7 is split into an internal flag; the low7 bits select the device. Do not discard the high bit or mistake a variable name length for a fixed-format metadata byte.

| File | Format | Descriptor file offsets | Device IDs (decimal) |
|---|---|---|---|
| CPU0.DGS | EDSY | 0013h | 1 |
| STG0.DGS | EDSY | 0013h | 2 |
| US0KMAIN.DGS | Named | 0000h | 3, high bit set (`83h`) |
| DISPLAY1.DGS | EDSY | 0013h | 5 |
| DSKT1.DGS | EDSY | 0013h | 6 |
| PAR1.DGS | EDSY | 0013h,0018h | 9,10 |
| SER0.DGS | EDSY | 0013h,0018h | 11,12 |
| US0PCN.DGS | Named | 0000h,0017h | 30,31 |
| IBM7690.DGS | Named | 0000h | 90 (`5Ah`) |

The exact descriptors and per-module hashes are in `diagnostic_modules.json`. The IBM feature entry is `E9 E7 09 5A 11`: jump to09EAh, device90,17-byte name including NUL. There is also an **internal**, directly called touch component at1670h with its own data following; it is not a second root-level DIAGS-discovered module.

### 6.3 Probe and test entry

DIAGS file037Fh (COM047Fh) calls loaded entries with **AH=3**, setting DS and ES to the module segment, through a far pointer held in the control program. Returned AL determines whether it marks the device installed. Feature entry09EAh dispatches AH0, AH1, AH2 and the remaining probe path separately; AH1 reaches self-test chain0A69h, AH2 reaches interactive menu0AFBh. The touch wrapper1670h establishes DS/ES=CS and calls20A0h with a pushed CS so the touch entry's RETF is matched correctly.

Errors often return AX plus BX pointing to a message. Do not conflate all results with DOS ERRORLEVEL: they are returned to the diagnostic supervisor. In the touch entry, AH is set90h and AL is an internal decimal subcode; the display helper explicitly divides AL by10 to build `90xx`. For example subcode10 is AL0Ah and displays9010; the returned register word need not be packed BCD9010h.

## 7. Menus as an implementation oracle

The following strings are **BINARY**, located in loose SERVICES or IBM7690.DGS. A string alone proves a resource exists, not that the supplied device set makes every generic IBM service reachable.

### 7.1 Top-level and checkout

SERVICES file18D7h–1948h supplies the no-fixed-disk menu:

```
0 - SYSTEM CHECKOUT
1 - FORMAT DISKETTE
2 - COPY DISKETTE
4 - SET TIME AND DATE
9 - END SERVICES
```

The alternate resource1847h–18D6h adds `3 - PREPARE SYSTEM FOR MOVING`. The code probes fixed-disk INT13h/AH08h/DL80h before choosing the menu, and rejects option3 when that probe fails. A generic message resource is not evidence of an installed hard disk on this workstation.

System Checkout (1949h): `0 - RUN TESTS ONE TIME`, `1 - RUN TESTS MULTIPLE TIMES`, `2 - LOG UTILITIES`, `9 - EXIT`. It asks whether the installed-device list is correct, permits adding/deleting items, and accepts item numbers separated by blanks or commas. It asks which options to test or Enter for all; multiple mode asks a run count or Enter for continuous, then `WAIT EACH TIME AN ERROR OCCURS (Y/N)` (1B88h). DIAGS has `PASS COUNT = 00000` at00E2h.

Log Utilities (1BD5h): `0 - START ERROR LOG`, `1 - STOP ERROR LOG`, `3 - DISPLAY TIME OF DAY`, `9 - END LOG UTILITIES`. Logging selects diskette or printer and a drive ID. `UNABLE TO READ ERROR LOG`, `DISK FULL ERROR - UNABLE TO LOG`, and `PRINTER NOT WORKING` are genuine failure resources; an emulator must allow media-full/printer-not-ready states rather than silently declaring logging successful.

The Set Time and Date resources ask Enter to preserve the current value or a replacement date/time; time must be24-hour format. `INVALID DATE` and `INVALID TIME` occur at21C7h/21DCh. See [PERIPHERALS.md](PERIPHERALS.md) for clock hardware; the UI's DOS calls do not justify modeling an AT RTC merely because QEMU supplies one.

### 7.2 IBM 7690 feature menu

IBM7690.DGS file0078h–0192h says `IBM 7690 FEATURE TESTS`, copyright1987,1990, `Version 1.1`:

```
0 - INTERFACE ADAPTER SELF TEST
1 - LCD INTERFACE TEST
2 - TOUCH PANEL TESTS
3 - BAR CODE FEATURE TESTS
9 - EXIT TO MAIN MENU
PRESS "ENTER" TO RUN ALL TESTS
```

This internal `1.1` string and disk-level Version1.10 are distinct formatting conventions. The file's author string at0048h names John H. Barker and Don D. Williams.

Touch menu16B7h: `0 - SELF TEST`, `1 - TOUCH TRACKING`, `9 - EXIT TO MAIN MENU`. Operations printed3-4 (PDF26) directs the user to select Touch Panel Tests then Touch Tracking. Code2147h repeatedly scans and displays tracking until a BIOS keyboard key is available; it consumes that key and returns to the prompt flow. Do not equate tracking with a Windows-style mouse or a successful DOS LEDTOUCH read: this is direct-port diagnostic code.

The input dispatcher20F8h–211Eh also admits `?`, Ctrl-A(01h), Ctrl-Q(11h), and Ctrl-L(0Ch), each followed by Enter. Subsequent branches reach raw/stepped optical display, repeated self-test and detailed optical classification. Digit2/3/4 comparisons occur deeper in the dispatcher but the outer validator does **not** admit those digits normally. Do not publish them as ordinary advertised menu options. The `?` path formats the settling count from1F45h and emits `VERIFY LATEST EC LEVEL IS INSTALLED` if above15 (21EBh–21F6h); those counts are loop units, not milliseconds.

### 7.3 Display, diskette, serial, and network resources

SERVICES display menu2800h provides self-test, attributes, character set,80×25,40×25,320×200,640×200/640×480, screen paging, exit, and `10 - RUN ALL ABOVE TESTS`. It asks whether all8 pages displayed and whether the screen is correct. **Human visual responses are part of the oracle.** See [VIDEO.md](VIDEO.md) for the actual MCGA/LCD mapping; do not count a correctly drawn diagnostic menu as proof of individual pixel/page/palette behavior.

Diskette menu2CB4h provides `1 - SEEK TEST`, `2 - WRITE, READ, COMPARE TEST`, `3 - VERIFY DISKETTE TEST`, `4 - SPEED TEST`, `5 - DISKETTE CHANGE TEST`, `9 - RETURN TO CONTROL PROGRAM`. It explicitly asks for scratch disks and for write-protect transitions. The speed resource says `SHOULD BE 1970 TO 2030`; its units require the DSKT code/timing interpretation, so do not reinterpret that number as RPM. DFORMAT/DCOPY resources mention1440,720 and360KB; Operations nevertheless limits its documented Copy Diskette procedure to low-density720KB.

Serial and parallel resources ask for wrap plugs, and distinguish a serial adapter connector from the end of an IBM communications cable. A software-only loopback is not proof of the external connector/cable path. US0PCN contains local/remote network status, a5-second update banner, NCB/session counts, adapter configuration and node-inactive errors; no claim is made that a network adapter is installed or emulated merely because its optional module is present.

SERVICES also contains hard-disk low-level-format, game-control, SDLC, BSC, mouse, math-coprocessor and printer text. The supplied DGS inventory does not contain a corresponding executable module for every resource. Never derive installed hardware, support claims, or reachable menus solely from this shared message library.

## 8. IBM7690.DGS direct-hardware tests

This section is an executable oracle for **loose v1.10, SHA e44671fa…9fa57 only**. Main hardware contracts remain in TOUCH/VIDEO/KEYBOARD/PERIPHERALS. Every instruction here is guest software behavior; avoid turning diagnostic-specific constants into universal hardware defaults.

### 8.1 Interface-adapter common self-test

At0D70h:

1. WriteFFh toF300h; F301h bit6 must read clear. Then write00h throughFEh, checking bit6 set for each. Failure returns AX9001h, selection-wrap failure.
2. ReadF302h, retain its high nibble, iterate low-control values7 down to1, then0. Each readback is masked withF7h to exclude bit3, then compared with the value written. Failure returns9002h. This is a low-control latch readback test, not permission to ignore the upper state.
3. F301h bit0 must be set; otherwise return9003h and `12V Fuse Open`.
4. F301h bit5 must be clear; otherwise return9004h and `Internal Keyboard Cable Not Connected`.
5. Print `INTERFACE ADAPTER TEST OK` and return AX0.

These checks distinguish selection wrap, low-control readback, fuse indication and cable presence. A constantFFh/unmapped-port model fails for several different reasons; simply returning zero is no better.

### 8.2 LCD dependencies and error return surface

The module tests interface ROM/RAM/register/sync/voltage-related conditions, not just BIOS INT10h output. Representative F304 index accesses begin at12F1h,1466h,14A7h,14E8h,1558h,163Fh and164Dh. See VIDEO for the complete decoded implementation, indexed-register masks and RAM address patterns.

The manual fallback display at02C0h asks numeric keys to classify a nonworking display:

| Key | Displayed error class |
|---:|---|
| 1 | 9031,9035 or9036 — ROM,RAM,REGISTER |
| 2 | 9037 — LCD CABLE |
| 3 | 9033 or9034 — PLANAR/ADAPTER SYNC |
| 4 | 9032 — -22.3V/12V |

The prompt says F1 to continue. BIOS/ROM checksum tests need the actual expected interface-adapter firmware contents or an explicitly synthetic compatibility fixture. No such original ROM dump was supplied. Replacing a checksum result with “pass” would destroy the diagnostic's value.

### 8.3 Touch scan primitives: explicit state transitions

The routines distinguish selected receiver, selected emitter, emitter enable, conversion state, and sampled six-bit ADC data. They must share the same F302 state as the normal driver and LCD/power-related consumers.

| DGS file range | Operation |
|---|---|
| 2445h–2464h | Dark/receiver sample: F302←0; F300←selector; F302←04h then00h; wait via the16-bit count at1F45h; call ADC helper |
| 2465h–2487h | Lit/emitter sample: F300←selector; F302←01h then00h then02h; wait via1F45h; ADC helper; save sample while writingF302←0 |
| 2488h–24A3h | ReadF302; write bit3 set then toggled clear; pollF302 bit3 up to50 reads using LOOPNE; readF303; maskAX with003Fh |
| 2281h–22DBh | Complete64-position scan and blocked-beam bitmap construction |

The poll terminates when bit3 reads clear, or its count expires. The scan helper itself still reads ADC after timeout; **the separate self-test** identifies handshake failures. A host must not assume every acquisition helper propagates an explicit timeout error.

Scan2281h initializes eight bitmap bytes at1F48h and writes64 dark/lit byte pairs at1F52h. Selectors are00..07,10..17,…70..77—not0..63. Bit mask starts80h and rotates right; after eight detectors the bitmap pointer advances and selector advances to the next high-nibble bank. It obtains dark sample, computes `max(dark - 20, 0)`, then obtains lit sample. If `lit >= threshold`, it sets the corresponding blocked bit. This diagnostic threshold20 is **not the later LEDTOUCH driver's threshold**. The64 positions represent40 horizontal plus24 vertical beams according to the hardware/driver chapters; the bitmap/pair layout here must not be flattened into an arbitrary640×480 pointer coordinate.

A dark value63, lit0 yields no blocked bit; lit63 yields a blocked bit against threshold43. Those are **synthetic analog fixtures**, not measured physical ADC defaults. They are useful to exercise software state transitions but cannot establish conversion latency, optical response curves, ambient-light calibration or cable electrical behavior.

### 8.4 Touch self-test and consumed-conversion semantics

Self-test2655h sets provisional settle count0090h and clears error byte1F42h. It repeats selection wrap and low-control readback. At26EBh it readsF303 and expectsF302 bit3 set; it then pulses bit3 set→clear, expects bit3 to become clear within50 polls, readsF303 again and expects bit3 set again. Consequently a model where bit3 is only a permanently cleared “ADC idle” bit will fail even if every sample byte is plausible. The byte-level guest observation is:

```
read ADC data -> status bit3 set
start pulse 8 -> 0 -> eventually status bit3 clear
read ADC data -> status bit3 set again
```

The naming/polarity must follow TOUCH's documented register interpretation, but these transitions are an independent binary constraint. On failure the module displays subcode10 (`ADC Will Not Start`) or11 (`ADC Busy Will Not Reset`) according to its actual branch paths; the English text is not a substitute for analyzing the reads.

At273Fh F301h bit7 set means touch panel not connected, subcode12. At275Dh onward it selects zero, reads/masks F302, performs the anomalous write below, delays2000 decrement-loop iterations and checks F301h bit2 set; failure is subcode13, amplifier error.

**Preserve this anomaly:** bytes at2769h are `81 CA 04 00`, i.e. **OR DX,0004h**, not OR AL,04h. Since DX wasF302h, the OUT at276Dh targets **F306h**. This is a literal supplied-binary observation, not OCR. Do not quietly describe it as a receiver-control strobe atF302h, patch the binary, or invent a documentedF306 register to make it fit. Whether hardware address decoding aliases that address, whether it is harmless in this sequence, or whether this is a program defect remains **OPEN** without hardware/ROM evidence. Trace it explicitly in any emulator experiment.

### 8.5 Adaptive settling, ambient light, and optical classification

At2791h the settling count starts2. A full scan follows. The self-test examines the dark samples against44 (`2Ch`), collecting bad-receiver bits. If any fail, it adds5 and repeats until the count exceeds255. This is a software-loop calibration; mapping one count to a fixed number of microseconds independent of CPU speed would be unjustified.

On persistent failure it prints the room-light instructions: cover display, press a key, wait5 seconds and remove cover. It rescans. If the covered display removes the dark failures, it reports subcode15/high light; if not, subcode16/detector error. On successful settling, it increases the count by `floor(count/4)+1` for margin, rescans, and checks the eight blocked bitmap bytes. Any blocked bit reaches subcode17/I/R LED error; otherwise it prints TOUCH PANEL TEST OK unless in suppressed preliminary mode.

Detailed optical routine22DCh uses selector tables with sentinel neighbors, tests dark samples against44 and lit samples against19, then tries adjacent emitters and receivers to distinguish excessive receiver conductance, receiver faults and emitter faults. Error-list strings are at17BDh,18F7h and1A24h; per-device report slots contain axis/device labels. This is richer than a single boolean “touch present”. Optical self-tests should be exercised both with no obstruction and with physically plausible blocked/dim/cross-coupled fixtures; a host-injected ordinary touch can correctly be diagnosed as a beam fault during this test.

Touch-visible error mapping at2223h–227Ch:

| Decimal subcode / display | Message resource |
|---:|---|
| 1 /9001 | Select line wrap failure — replace interface adapter |
| 2 /9002 | Control line wrap failure — replace interface adapter |
| 10 /9010 | ADC will not start |
| 11 /9011 | ADC busy will not reset |
| 12 /9012 | Touch panel not connected/loose cable |
| 13 /9013 | Touch panel amplifier error |
| 14 /9014 | ADC conversion error |
| 15 /9015 | Room light level too high |
| 16 /9016 | Touch panel detector error |
| 17 /9017 | I/R LED error |
| 18 /9018 | I/R LED output weak — clean or replace touch panel |

**Scope caveat:** a return-message mapping is not proof every listed subcode is reachable in this revision's ordinary self-test. In particular resources for14/18 exist, while the traced main2655h path above directly identifies1,2,10,11,12,13,15,16,17. Retain this distinction when constructing fault-injection acceptance cases.

### 8.6 Bar-code interaction

Bar-code menu0721h offers `0 - SELF TEST`, `1 - SINGLE TEST`, `2 - MULTIPLE TESTS`, `9 - EXIT TO MAIN MENU`. It asks whether the feature is installed, asks the operator to scan, permits Esc if a bar code will not read or to end, displays a data field, and asks `IS BAR CODE DATA CORRECT? (Y/N)` (08B8h region).

Resources show `Version: ?.?`, Code39, Interleaved2of5, UPC/EAN/JAN, Codabar, Code128, fixed-beam and moving-beam scanner read (0933h–09BDh). These are diagnostic report fields, not proof that an arbitrary string arriving through the ordinary keyboard path satisfies the optional bar-code hardware protocol. Errors at07B5h,07F3h,082Ch,085Eh are9021 feature failure,9022 read error,9023 barcode error/check cable,9024 status error/check cable. See KEYBOARD/PERIPHERALS for protocol and presence ownership.

## 9. Documented operating and troubleshooting contract

**DOCUMENTED, Operations printed1-10/1-11:** POST tests memory, shows memory size, takes approximately45 seconds, and normally ends with one beep. The IBM logo then appears briefly, followed by Services. This is an operator expectation from the publication, not a cycle count derived from the diagnostic executable. POST errors and diagnostic program errors must be logged separately.

**DOCUMENTED, printed3-2/3-3:** two or three beeps indicate POST errors; a noncritical condition may allow F1 with reduced function; a critical error halts. Three beeps indicate a critical display/keyboard problem. Do not make all failures recoverable merely so the disk can start.

The visually checked troubleshooting spread, printed3-6/3-7 (PDF27), gives:

| Display/code | Documented action/meaning |
|---|---|
| 161 or clock symbol | F1, then Set Time and Date; recurrent/inability to set requires service |
| 199 installed-device list | Missing internal item: service; external item: follow its test instructions |
| 205 memory | Service; F1 may continue with reduced memory |
| 301 keyboard/computer | Check cable and held keys; power off, wait20 seconds, power on; service if persistent |
| 302 workstation | Service |
| 6XX or diagnostic program will not load | Correct customer diagnostic disk/insertion, retry; service if still failing |
| 9015 high light | Keep bright light away; service if persistent |
| 9018 weak LED | Clean bezel; service if persistent |
| 9021 bar code feature | Feature seems absent; check recently installed logic kit |
| 9022 bar code read | Check wand connection, clean tip and bar-code quality |
| 1XX/2XX/3XX/5XX/9XX/11XX | System board/memory address/keyboard/display/parallel/serial categories |
| 30XX/31XX/90XX | Network/network/interface-adapter categories |
| ROM Error, Parity Check1/2 | Service |

These are printed decimal display categories. `90XX` is not an I/O port range. The publication groups failures for operators; it does not specify every diagnostic internal return register or all extended error subcodes. A module's test-failure number also must not be confused with DOS's FCB read status or the installer batch's ERRORLEVEL.

## 10. Disk-writing and installation safety

Operations says diagnostic Format Diskette prepares media **for diagnostic purposes only**; use DOS FORMAT for working disks. Its Copy Diskette copies all information and formats a blank target as part of the copy. Backup procedure (printed1-13/1-14) explicitly swaps source and target, with more than640KB potentially requiring another source insertion. An emulator needs a real removable-media transition and should preserve an unambiguous source-versus-target identity in logs.

Diskette-specific failure strings include645 no index pulse,646 track0 detection failed,647 no transitions on read data,648 format test failed (SERVICES3090h–30F3h), write-protected disk, DMA boundary error, timeout, seek/controller/CRC errors, DMA overrun, record/address mark not found, invalid command and unknown error. These are meaningful negative cases; do not mask FDC failures by returning successful BIOS status.

Shared hard-disk strings explicitly warn all data will be destroyed and include conditional/unconditional format and surface analysis. There is no reason to attach a valuable host-backed hard disk to a diagnostic smoke. The derived image builder removes the donor's general FORMAT/FDISK utilities but intentionally retains IBM's diagnostic DFORMAT/DCOPY as supplied. That reduces clutter, not the need for snapshot media.

`LEDINST.BAT` runs `A:NSTALL A:TXT.OK A:LEDTOUCH.SYS`; on return codes1 or2 it invokes `A:RBT`. It tests ERRORLEVEL in descending order, correctly accounting for DOS `IF ERRORLEVEL n` meaning “at least n”. It is not a harmless read-only helper. Returned17 means insufficient disk space;16 invalid disk-space access;15 data-file write;14 data-file open-for-write;13 data write-access;12 CONFIG write;11 CONFIG rewind;10 CONFIG write-access;9 data read;8 data length;7 missing data;6 text read;5 missing text;4 missing command-line text/data;3 insufficient host memory. Zero or another unhandled failure reaches the failed path, not reboot. Exact batch text is [LEDINST.BAT](../7690diag/LEDINST.BAT). Do not use this installer to mutate original media; use the builder's explicit CONFIG option when its semantics are desired.

## 11. Acceptance ladder for emulator development

These are **future acceptance scenarios**, not claims that a complete IBM7690 emulator has passed them.

1. **Media parser:** independently recover the documented BPB/root layout and hashes; traverse files spanning the preserved COMMAND gap; reject cyclic/broken FAT chains. Distinguish no boot signature, wrong root-system name, and sector-read error.
2. **Derived DOS boot:** observe the unpatched donor boot sector and original system files reach PC DOS3.20 prompt; record image hash, option set, console and no-hard-disk configuration. This closes the disk-builder claim only.
3. **ROM rejection:** on a deliberately nonmatching generic BIOS, observe SERVICES' genuine incorrect-diskette path rather than a crash, silent pass or an emulator hardcoded menu. Do not “fix” the rejection by falsely identifying the machine.
4. **Compatible supervisor:** with a properly identified, explicitly sourced BIOS baseline, follow installation of INT80h–A3h, FCB module discovery, device descriptors and one-time checkout. Attribute remaining ROM-sensitive failures to actual missing prerequisites.
5. **Media faults:** remove/change disk during module load, write-protect scratch media, fill log disk, report printer not-ready. Verify menus and error paths remain live without fabricated successful I/O.
6. **Device presence:** test optional bar-code/network presence both ways. Presence detection must follow hardware responses, not merely which `.DGS` files exist on disk.
7. **Touch handshake:** inject separate failures for selection-wrap, control-readback, conversion consumed/not-ready transition, absent cable and amplifier status. Trace the literalF306 write. Compare expected branches rather than guessing from message wording.
8. **Optical behavior:** dark/lit synthetic fixtures, a single blocked beam on each axis, boundary selectors07→10 and67→70, ambient-light failure relieved by covering, persistent bad detector, dim/neighbor emitter classification. Keep normal-driver threshold and DGS threshold separate.
9. **Video and LCD:** actual visual confirmation of attributes, character set,40/80 columns, graphics modes and8-page prompts plus adapter RAM/indexed-register self-test. A VGA-looking screen cannot substitute for the documented LCD hardware.
10. **Repeated checkout:** exercise finite pass count, continuous run interrupted by user, stop-on-error versus continue, and log failure while tests continue according to guest code. Timing, memory and resident interrupt state must remain coherent across passes.

## 12. Explicit remaining prerequisites

* No original Version1.10 sector image: original DOS version, boot code, startup scripts, physical layout and deleted/slack provenance cannot be reconstructed from the loose files or label. The builder is a complete **derived** recipe, not an assertion about that missing master.
* No actual supplied7690 system/interface-adapter ROM dumps: Model25 material remains attributed baseline evidence. Checksums, exact ROM self-test acceptance and all7690-specific ROM differences require authentic bytes or a clearly marked synthetic fixture.
* No physical timing/analog capture: decrement counts and guest polling patterns constrain sequence, not calibrated microseconds, optical transfer functions or ADC noise.
* No demonstrated original-hardware interpretation of the DGS F306 anomaly. Preserve and log it; do not invent register documentation.
* No full hardware-backed clinical diagnostic run follows from static disassembly or a generic DOS boot. Human display/track/bar-code judgments and external wrap plugs remain genuine parts of the intended test workflow.

The useful end state is not “all diagnostics forced green.” It is an attributable executable chain whose successful and failing observations follow the modeled devices, with every unsupplied ROM or physical dependency visible rather than hidden.
