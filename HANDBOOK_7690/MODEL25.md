# IBM 7690: what can be inherited from the 8086 Model 25

## Scope: architectural parent, not firmware identity

**DOCUMENTED:** the 7690 Technical Reference describes a workstation “based on the IBM Personal System/2 Model 25 architecture” (TR PDF 10 / printed 1-3). This is the correct starting point. It is not a statement that every Model 25 register, ROM byte, display path, drive limit, or firmware identification byte is identical.

The useful ancestor is the **8086 IBM 8525**, not the 8525-286 or any MCA machine. The 8086 Model 30 is a valuable sibling for understanding shared gate-array logic, but its RTC, fixed-disk configuration, display connection, and firmware revisions are not default 7690 features. A model byte of `FA` is insufficient to select a machine implementation.

This chapter provides a reuse matrix, a traceable comparative firmware identity, concrete ROM-derived integration facts, and limits on moving knowledge across machines. [BOOT.md](BOOT.md) owns target CPU/memory/PIC/DMA/PIT/reset; [STORAGE.md](STORAGE.md) owns target diskette. Device-specific chapters retain their own state ownership.

Evidence labels throughout:

- **DOCUMENTED — target:** a 7690 IBM publication explicitly says it.
- **DOCUMENTED — baseline:** a Model 25/30 IBM publication says it about that model.
- **BINARY — baseline:** bytes from a specifically identified Model 25 image establish an observation.
- **BINARY — target software:** a supplied 7690 disk utility or diagnostic executes the cited operation; this is not physical-board measurement.
- **INFERENCE:** the proposed inheritance or emulator design consequence.
- **OPEN:** information needed before claiming a complete target implementation.

## 1. Source chain and provenance

### Target authority

| Source | Use |
|---|---|
| [7690 Technical Reference](../IBM_7690_Clinical_Workstation_Technical_Reference.pdf) | Target hardware and BIOS statements, especially PDF 10–23 / printed 1-3–1-29, PDF 49–62 / 1-80–1-107, and section 6 |
| [7690 Guide to Operations](../IBM_7690_Clinical_Workstation_Guide_to_Operations.pdf) | Actual advertised configuration, user-visible boot and faults, HD media rules, ride-through limitations |
| [Supplied diagnostic directory](../7690diag/) and [extracted disk contents](../ANALYSIS/7690KQPW/) | Executable software evidence, version distinctions in DIAGNOSTICS.md |
| [Platform evidence ledger](../ANALYSIS/platform-evidence.json) | Exact hashes, page-image checks, raw byte windows, decoded instructions, and supplied image BPB |

### Comparative corpus

The comparative source repository is **`/Users/josh/src/bios8530`**; it was not modified. Selected unchanged PDFs and research JSON are retained locally under [DOCUMENTATION/BASELINE](../DOCUMENTATION/BASELINE/), with original paths, lengths and hashes in [PROVENANCE.json](../DOCUMENTATION/BASELINE/PROVENANCE.json). Other entries below remain external research references. Reading the handbook and its retained instruction evidence does not require the sibling checkout; re-running full comparative-ROM analysis does.

| Original upstream path | What it contributes | What it does not prove |
|---|---|---|
| [PS2_Model_25_Technical_Reference_Jun87.pdf](../DOCUMENTATION/BASELINE/PS2_Model_25_Technical_Reference_Jun87.pdf) | Primary IBM Model 25 CPU/bus/gate-array, controller tables, BIOS contracts | 7690 adapter behavior or ROM identity |
| `PS2_Model_30_Technical_Reference_Jan87.pdf` | Primary IBM sibling comparisons, particularly RTC and planar differences | A license to install a Model 30 RTC in the 7690 |
| [PS2_and_PC_BIOS_Interface_Technical_Reference_Apr87.pdf](../DOCUMENTATION/BASELINE/PS2_and_PC_BIOS_Interface_Technical_Reference_Apr87.pdf) | BIOS interface context | Actual 7690 extension code |
| [reference/hardware_spec.json](../DOCUMENTATION/BASELINE/hardware_spec.json) | Prior synthesis with source citations and explicit primary/secondary distinctions | Every field is not independently authoritative; some summaries are incomplete or oversimplified |
| [reference/model_differences.json](../DOCUMENTATION/BASELINE/model_differences.json) | Concrete Model 25 versus Model 30 decisions | A ready-made 7690 profile |
| [reference/rom_analysis.json](../DOCUMENTATION/BASELINE/rom_analysis.json) | Even/odd ROM pair identity, candidate descriptors, differences and hashes | A candidate byte pattern is not automatically the active descriptor |
| `disasm/m25/type1/src/BIOS.INC` and `type2/src/BIOS.INC` | Byte-preserving representation of the Model 25 ROMs | Names in generated/disassembled source are not IBM 7690 source labels |
| `disasm/m25/type1/src/m25_seg.bin`, `type2/src/m25_seg.bin` | Combined 64-KiB comparative ROM images used for the observations below | Neither is a captured 7690 ROM |
| `goldens/8525`, `roms/8525` | Original comparative chip/pair evidence | No target provenance merely because a board revision may have been reused |
| `reference/diagnostic_analysis.json`, `disks/adv25dia.img`, `disks/adv30dig.img` | Baseline diagnostic identities and behavior differences | Passing them is not a 7690 acceptance test |
| `vogons_M30_planar_registers.html` | Archived secondary reverse engineering, especially custom keyboard/PIC extensions | Not an IBM specification; uncertain bit explanations remain uncertain |
| `8530_fdc_findings.md` | Prior emulator investigation of concrete FDC diagnostic failures | Not a physical 7690 measurement or a current emulator pass report |

The platform ledger records hashes of the specific baseline ROM and reference files consumed in this research and contains the exact instruction windows used here. This preserves a portable **evidence extract**, not a redistributed full ROM. To reproduce broader analysis, obtain the named baseline corpus or independently hash the corresponding original ROM pair.

### How to use a synthesized baseline safely

1. Find the baseline claim and its source reference.
2. Check the target publication for an explicit change, reservation, or absence.
3. For ambiguous numbers, inspect the page image. Do not promote an OCR character into a hardware port.
4. For a firmware behavior, identify the actual combined image and the executed code path, not just a string or byte pattern somewhere in ROM.
5. Retain the confidence boundary when applying the behavior to 7690.
6. Treat a prior emulator experiment as an experiment on its identified software/model. It can disprove a proposed emulator wiring for that run, but is not evidence from an unmeasured 7690 motherboard.

This process exposed several important corrections: 7690 RAM control is `6B`, not OCR `68`; the DMA page aperture is `80–8F`, not OCR `80–BF`; the 7690 command tables contain real printed opcode errors; and the Model 25 ROM has a runtime choice between RTC/no-RTC descriptors.

## 2. Reuse matrix

The “decision” column is an implementation recommendation, not a claim of a completed emulator.

| Area | Baseline 8086 Model 25 | 7690 evidence / difference | Reuse decision |
|---|---|---|---|
| CPU | 8086-2, 8 MHz, 20-bit addressing | Same explicit target CPU and clock, TR PDF 11 / 1-5 | Reuse 8086 execution core, not 286 semantics |
| Local bus | 16-bit RAM/ROM; byte I/O/DMA with waits | Same explicit target cycle descriptions | Reuse bus-conversion mechanism; preserve target wait/readiness timing |
| System support | Bus master for refresh/DMA, parity/memory control | Same functional organization, TR PDF 12 / 1-6–1-7 | Reuse architecture, do not assume unpublished electrical aliases |
| Memory size | Original 512 KiB standard, optional low 128 KiB | Target 640 KiB standard, socketed low 128 KiB, TR PDF 10/20 | Configure target as 640 KiB, retaining failure/remap behavior |
| RAM control | `6B`, low-memory remap and six high 64-KiB enables | Same bitfield, target image verified | Reuse bit allocation; complete remap permutation remains to be established |
| Parity | Planar RAM parity, port `62` status | Same, but target `62.2` reserved | Reuse parity logic without importing fixed-disk-presence bit |
| Chip selects | `65` selects serial, diskette, video, parallel, fixed disk | Target `65.0` reserved, all other published bits match | Reuse routing core with target mask; remove built-in fixed-disk select |
| PIC | One custom eight-level controller | Same target, IRQ1 entry `71` | Reuse custom PIC extension, not generic XT IRQ1-only logic |
| PIC diagnostics | Proprietary extensions in baseline research | Supplied CPU0 directly uses `63`, `69.6/.7`, IRR/ISR and stimulus writes | Target software is stronger evidence for exercised sequences; see BOOT.md |
| PIT0/PIT2 | 8253-compatible system tick and sound | Same documented target functions | Reuse standard counter core and actual gates |
| PIT1 | Baseline hardware has diagnostic `-RAS_SIP` input | Target explicitly says diagnostic clock from support-array RAS; OUT unused | Do not inherit a shorthand “PIT1 drives refresh” implementation |
| DMA page map | `81`=ch2, `82`=ch3, `83`=ch1, `87`=ch0 | Target print says shifted `80/81/82/87`; CPU0 uses baseline addresses | Provisional baseline map, explicit contradiction; independent channel test needed |
| NMI | Planar parity, channel check, coprocessor; `A0` enable | Same target documented source/control group; diagnostic `69` layer also exercised | Reuse ownership/gating, not AT CMOS NMI logic |
| Keyboard transport | Custom gate-array serial interfaces, not 8042 | Target keyboard/bar-code data passes through the interface adapter to planar keyboard input | Reuse transport only through KEYBOARD.md's target integration contract |
| Pointing device | Shared IRQ1 and BIOS pointing interface | Target retains BIOS pointing data and services, while touch uses separate hardware/driver | Do not wire touch IRQ/protocol directly as a PS/2 mouse merely for convenience |
| Base video | MCGA with 64-KiB framebuffer and loadable fonts | Target still contains MCGA, but adds LCD transformation/controller and ROM | Reuse MCGA storage/register core, implement adapter path separately |
| Monitor identity | Integrated analog display, color/mono variants | Planar sees no ordinary monitor; 7690 adapter POST initializes LCD conversion | Never force a Model 25 monitor sense value to bypass missing C000 firmware |
| Expansion | Two Model 25 62-pin slots | Target four sockets on expansion bus, one occupied by integral adapter, three available; TR PDF 11 / 1-4 | Reuse byte-wide channel electrical model with target slot topology |
| Floppy | Original 720-KiB configuration | Target Operations explicitly specifies 1.44-MB drive and HD/DD media | Reuse 765-class core, add target-supported density behavior; don't cap at 720 KiB |
| Floppy command opcodes | Primary Model 25 tables give canonical encodings | Several 7690 tables print contradictory opcodes | Reuse canonical core after documenting the errors; STORAGE.md provides side-by-side evidence |
| Floppy RAS/DIR | IBM gate-array status, including active-low disk-change view | Same target named ports, but complete latch clearing/electrical semantics not published | Reuse only proven meanings; model index and mechanical state, not canned status |
| Fixed disk | Baseline BIOS and later options can support integrated XTA-style disk | No built-in target fixed-disk map, `65.0`/`62.2` reserved, IRQ5/DRQ3 unused | Do not instantiate baseline fixed disk by default |
| RTC | No native clock in original Model 25; firmware contains optional-clock probe | Target TR says no RTC; Operations says continuously battery-powered clock; supplied CPU0 requires BIOS clock and `B0/E0`-region RTC/RAM/alarm behavior | Preserve substantive conflict; a complete diagnostic experiment needs the demonstrated clock interfaces, not a no-RTC skip |
| ROM identification | Model `FA`, submodel `01`, revision `00` in supplied pair | Target TR printed 6-68 says model `FA`, submodel `00` | Do not relabel Model 25 ROM as target or edit one ID byte to make it “7690” |
| Adapter ROM | Optional early/late feature-ROM discovery | Mandatory 16-KiB target interface ROM at `C0000–C3FFF` | Reuse ROM scanner, supply actual target code before authentic boot claims |
| Power | Model 25 enclosure/power arrangements | Target ride-through battery leaves CPU running but disables LCD and drive | Add target power states; not AT standby, not a portable suspend/resume BIOS |
| Diagnostic disk | Model-specific starter/advanced disks | Target customer diagnostics and feature tests | Use target software as target evidence; baseline passes are only baseline passes |

Numerical baseline references: Model 25 TR physical PDF 16–27 / printed 1-3–1-14 (CPU, memory standard, PIC/timers/DMA), PDF 35–40 / 1-22–1-27 (RAM/bus/ports), PDF 91–117 / 1-78–1-104 (diskette); target references are listed in BOOT.md and STORAGE.md. Baseline model differences are cross-indexed by the external `reference/model_differences.json`.

## 3. Comparative Model 25 firmware: exact identities

**BINARY — baseline only.** Two combined images were read directly, hashed, and decoded without modifying them. File offset equals `F000:offset`; physical address equals `0xF0000 + offset`.

| Property | Model 25 Type 1 | Model 25 Type 2 |
|---|---|---|
| Original pair identified by baseline corpus | Even `00F2092.BIN`, odd `00F2093.BIN` | Even `00F2122.BIN`, odd `00F2123.BIN` |
| Combined size | 65,536 bytes | 65,536 bytes |
| SHA-256 | `cfbdc2cd67c95c15b06be14e2e5f4bbd6991f3506428af64038b6381a1120166` | `ed11efb8184ccf7055956ef34a6f81a496ac38e066d117f17df3fa2c79d9d2ee` |
| ASCII date at `FFF5` | `06/26/87` | `06/26/87` |
| Model byte at `FFFE` | `FA` | `FA` |
| Final byte at `FFFF` | `AF` | `C3` |
| Byte sum over whole image, modulo 256 | `00` | `00` |
| Reset bytes at `FFF0–FFF4` | `EA 5B E0 00 F0` | Same |

The baseline corpus builds the combined image as `combined[2*i]=even[i]`, `combined[2*i+1]=odd[i]`. This is lane interleaving, not concatenation. Its exact chip/pair attribution remains **Model 25**. The target's two system-ROM sockets and 16-bit local bus make the same layout plausible, but until actual 7690 chips are captured their identity/order is OPEN.

The Type 1 reset tail, all 16 bytes:

```text
F000:FFF0  EA 5B E0 00 F0 30 36 2F 32 36 2F 38 37 FF FA AF
```

Type 2 differs only in the last byte of this tail, `C3`.

### Ten byte differences, not a new firmware algorithm

The directly compared combined images differ at ten byte positions in five runs:

| F000 offset(s) | Type 1 | Type 2 | Interpretation |
|---|---|---|---|
| `0004–0005` | `30 39` | `31 32` | Part-number digits in front matter |
| `004C–004F` | `30 30 39 39` | `31 31 32 32` | Repeated/interleaved front-matter part-number digits |
| `5FFE` | `0C` | `10` | Unexplained identity/marker byte; following `5FFF` remains `00` |
| `E004–E005` | `30 39` | `31 32` | Part-number digits in high-region copyright text |
| `FFFF` | `AF` | `C3` | Checksum-balancing byte |

The marker's meaning is **INFERENCE**, not an IBM-defined register. The nearby source essay `disasm/m25/TYPE_DIFF.md` proposes a planar/build identifier and discusses Type 2 use in the 7690, but that association does not authenticate the ROM pair as a 7690 capture. The observed image comparison establishes that these two files' executable regions are otherwise identical; it does not establish that the 7690 shipped either file unchanged.

Avoid importing arithmetic or prose from a secondary comparison when the bytes can settle it. The directly computed whole-image checksums above are the evidence; checksum adjustment narratives are not needed to run the machine.

## 4. ROM-derived platform observations worth carrying forward

These are concrete observations in **both supplied Model 25 combined images**, because the differing locations do not intersect the following instruction paths. They constrain a useful baseline implementation. They are not an invented 7690 disassembly.

### 4.1 Real reset and the no-RAM phase

`F000:FFF0` far-jumps to `F000:E05B`; the instruction at `E05B`, `E9 2F 20`, is a near jump whose 16-bit IP wraps to `008D`. A disassembler using a flat, unbounded address may print `1008D`; the 8086 does not switch to a different physical segment on this near jump.

At `008D` the ROM executes CLI and writes `00` to checkpoint port `90` and parallel data `378`. `0096–00C2` tests flag behavior with SAHF/LAHF, conditional branches, shifts, and overflow. `00C7–00EE` walks a value through DS, ES, SS, SP, BP, SI, DI and checks the result. These are meaningful CPU-core probes: an emulator which preloads a safe RAM stack or enters after them can conceal broken reset/flag/segment handling.

At `00F0–00F2`, the baseline writes `82` to `65`, enabling parallel select/output for checkpointing while leaving other integrated selects off. This is an observed **firmware write**, not the hardware power-up value. It later uses ROM as its stack: `0100–010D` establishes SS from CS and SP=`0256`; `0111` jumps into checksum code, which returns through a ROM word. ROM must remain read-only even when addressed through SS.

### 4.2 Whole-ROM checksum and why BASIC bytes matter

`F000:12AA–12B5` sets CX=0, clears AL, adds the byte at DS:BX, increments BX, and LOOPs. In 16-bit LOOP semantics, initial CX=0 performs 65,536 iterations. On entry from `0107–0111`, DS=`F000`, BX=0: the loop sums the **entire combined 64-KiB image**. It ORs AL with itself to return zero/nonzero flags, then RETs.

**INFERENCE:** a baseline image assembled from only the visible BIOS/POST code, with the ROM BASIC region replaced by zeros, is not equivalent to the original ROM. In the original image the BASIC text begins in the `6000` region; the runtime BASIC content and high BIOS share the image whose integrity is tested. Neither an accepted partial ROM nor a checksum patch should be described as executing an unmodified ROM.

For the7690, the publication says system ROM contains a bootstrap and refers to ROM BASIC on boot errors, but the actual **target POST's** precise checksum algorithm and content partition are OPEN until the system ROM is available.

**BINARY — target diagnostic, a separate gate:** supplied CPU0 file0159h–01ACh checks the ROM before its NMI test. It sets DS=F000h, BX=6000h, CX=2000h and calls0954h four times, covering6000h–DFFFh in four8-KiB blocks. That routine reads each byte three times for stability, accumulates an8-bit sum, ANDs all bytes and ORs all bytes; successful exit requires sum00h, AND00h and ORFFh. The caller repeats each block's checksum in reverse via0979h, then repeats forward/reverse checks over all65536 bytes with CX=0. Failure loads AL=05h and branches through0133h to the common error path08ECh. A zero-filled block is rejected even when its sum is zero.

**EXECUTED:** [platform_trace.py](../TOOLS/platform_trace.py) enters this unchanged diagnostic gate directly. [PLATFORM-TRACE.json](../ANALYSIS/PLATFORM-TRACE.json) records both identified Model25 images reaching01AEh, stopping before NMI; synthetic all-zero/all-FF images, an unstable repeated read, and opposing errors in different8-KiB blocks fail at0133h with AL05h. The opposing errors preserve the whole-ROM sum, demonstrating why a single checksum is insufficient. A synthetic00/FF checkerboard passes this narrow gate, demonstrating the converse: these checks do **not authenticate firmware**. The same tool executes absent-date/absent-time BIOS fixtures through CPU0's real AL3Dh error path. None is a normal full-module or target POST pass.

### 4.3 DMA readback tests are not just “support channel 2”

`F000:011E–0154` master-clears DMA through `0D`, then writes and reads both bytes at ports `00–07`, with patterns `FFFF`, `5555`, and `AAAA`. This requires a shared 8237 byte-pointer implementation and actual address/count state even on unused channels. Returning zero from all “unused” DMA registers fails a real firmware contract.

`0156–018F` writes and reads page ports `81`, `82`, `83`, `87`, testing their low nibbles with changing values. It ORs `F0` into reads before comparing, showing that this particular test does not depend on the upper readback nibble. It does not justify arbitrary upper bits elsewhere.

For actual diskette DMA, `4B18–4B75` clears the byte pointer with `OUT 0C`, sets the mode at `0B`, writes channel-2 address low/high through `04`, masks the page to `0F`, writes it to **`81` at `4B4B`**, writes count minus one through `05`, and unmasks channel 2 at `0A`. The destination computation includes ES and the buffer offset, not merely a flat offset in the first 64 KiB. The code records BIOS boundary error `09` at BDA `41` if address-plus-count carries.

This is strong evidence against using the shifted DMA-page map for a Model 25. For the 7690, supplied CPU0 uses the same page addresses but does not independently prove DRQ-to-page assignment; the target TR's conflicting figure remains recorded in BOOT.md.

### 4.4 PIC initialization and the `63` normal-base read

`F000:0195–01A9` writes PIC sequence `13` to `20`, `08` to `21`, `09` to `21`, then mask `FF` to `21`. This is a single-controller initialization; a generic AT implementation waiting for a cascade ICW3 will parse it incorrectly.

The keyboard dispatch at `F000:E68C–E6A6` is the decisive base-read observation:

```text
E68C  E6 60       OUT 60,AL
E68F  33 C0       XOR AX,AX
E691  8E C0       MOV ES,AX
E693  E4 63       IN  AL,63
E695  24 F8       AND AL,F8
E697  40          INC AX
E698  D1 E0       SHL AX,1
E69A  D1 E0       SHL AX,1
E69C  8B D8       MOV BX,AX
E69E  26 8B 47 02 MOV AX,ES:[BX+2]
E6A2  50          PUSH AX
E6A3  26 8B 07    MOV AX,ES:[BX]
E6A6  50          PUSH AX
```

The byte is placed in `60`; the firmware computes IVT index `(normal_base + 1) * 4`. This explains how the documented proprietary hardware entry **INT 71h** coexists with software expecting the normal keyboard vector. The secondary archived discussion claims that IRQ1 always selects `71` independently of normal PIC base; the target hardware chapter also explicitly names `71`. The baseline instruction window directly proves only the software side of the demultiplexing, not every custom PIC INTA timing detail.

### 4.5 Actual diskette command readiness

`F000:4D5E–4D81` polls `3F4`, masks `C0`, and waits for `80` before writing the command/parameter byte to `3F5`. If readiness never arrives, it sets BIOS timeout bit `80`. Thus `(RQM=1,DIO=0)` is a live transfer condition, not a constant “FDC present” value. A device that accepts every OUT regardless of its current command/result phase may boot a simple image yet fail when an earlier result is unread.

The command state machine belongs in the hardware model. INT 13h firmware waits and handles errors; it must not receive successful results from a host-sector API while the emulated DMA/FDC/PIC state stays idle.

### 4.6 The active-low disk-change view

`F000:4E81–4E8A` reads `3F7` and tests bit `80`. Its caller at `4AC0–4AFC` immediately takes the no-change path when the bit is set; with the bit clear it attempts the change-clearing seek sequence and reports media-change/timeout status. This is comparative executable evidence for the active-low interpretation of the target TR's `-Diskette Change` label. Importing an AT-style DIR bit with the opposite meaning changes the BIOS's behavior on every media insertion.

The physical target signal remains active until a disk is present and a step pulse occurs, per TR PDF 61 / printed 1-105. STORAGE.md keeps the drive's change latch separate from controller reset and image insertion.

### 4.7 Bootstrap is not a `55 AA` check

The `F000:E6F2` INT 19h stub jumps to `4EE8`. That routine clears 512 bytes at `0000:7C00`, resets and reads drive 0 through INT 13h, and can try `DL=80` after failures. The observed source sequence includes two reset/read attempts and a timeout-specific branch; it should be traced as code rather than summarized as “always retry three times.”

At `4FA8–4FCB`, a successful sector read is tested by loading its first word, rejecting zero, then comparing that word to the next ten words using REPNE SCASW. Finding a matching word rejects the sector; not finding one allows a far jump at `4FC6` to `0000:7C00`. There is no boot-tail signature test in this path.

This detail is useful because it disproves an easy generic-PC assumption for the **identified baseline firmware**. It does not supply the unknown target boot algorithm. The 7690 TR promises the `0000:7C00` handoff and DL, but not this heuristic, fixed-disk fallback, retry UI, or register state beyond that promise.

## 5. A subtle firmware identity trap: two descriptors

A raw search finds the following two plausible INT 15h/C0h descriptors in the Model 25 combined ROM:

| F000 offset | Ten descriptor bytes | Feature-byte-1 implication |
|---|---|---|
| `5876` | `08 00 FA 01 00 94 00 00 00 00` | Bit 5 clear: no RTC |
| `E6F5` | `08 00 FA 01 00 B4 00 00 00 00` | Bit 5 set: RTC present |

**BINARY:** the selection code at `5857–5874` calls `02B5`; on a nonzero comparison it returns BX=`5876`, on the equal path BX=`E6F5`. The probe at `02B5–02E7` saves bytes from `EA`, `EB`, `EC`; writes ASCII `R`, `T`, `C` (`52`, `54`, `43`) to those ports; reads/compares them; then restores the original bytes. It tests whether the ports behave as storage. These addresses are in the Model 30 RTC counter/RAM region, not AT CMOS.

**INFERENCE:** a baseline implementation that gives every unused I/O address an automatic write/read latch can falsely pass this probe and report an RTC on a Model 25. That is an observable consequence of wrong open-bus modeling, not merely a cosmetic feature bit. Conversely, “ROM contains B4” is not proof that the normal Model 25 has a real-time clock. The active path must be identified.

For the target 7690, TR printed 6-49 explicitly says no RTC while Operations printed 1-11 says a battery keeps the internal clock running continuously. **BINARY — target software adds stronger contrary evidence:** CPU0's normal path calls INT 1Ah/AH=04 and AH=02 at file `025B–0285`; CF failures go to `04BE` (AL=`3D`) and `08EC`, not an optional-clock skip. Its success path tests RTC/RAM/alarm interfaces at `B0–B5` and `E0–EF` through `057D`, before PIT/PIC/DMA. A no-RTC BIOS cannot pass this path. The Model 25 code shows a possible inherited detection mechanism, **not proof of the target chip or descriptor**. BOOT.md gives the target diagnostic's exact call/interrupt prerequisites. Do not settle the target's contradiction by selecting the easiest descriptor, stubbing clock success, or skipping tests.

Similarly, the target's published model/submodel `FA/00` does not make it an 8086 Model 30. A descriptor reports a software compatibility identity; hardware ownership still comes from the target board/adapter contract. Modifying a Model 25 `01` to `00` does not add the missing LCD ROM, HD handling, power integration, or clinical keyboard/bar-code behavior.

## 6. Supplied 7690 software as a bridge, and its limits

The [CPU0.DGS](../7690diag/CPU0.DGS) module has **2,942 bytes**, SHA-256 `8d8943a0fb9bdd6cbd7bb8733387796f3057e1a608a51766927faaf105cabac1`; [DSKT1.DGS](../7690diag/DSKT1.DGS) has **4,800 bytes**, SHA-256 `4d188e243a57882f8ec36e5539fb8054a36a88a3dfc2d5f10db571d70f03409c`. The corresponding extracted files in `ANALYSIS/7690KQPW/` have the same content hashes for these modules. This is a per-file observation, not a statement that every supplied directory/image file is identical.

DGS offsets here are **zero-based file offsets**. The module is not assumed to be a DOS COM image loaded at offset `0100`. Its entry header and far-return interfaces are diagnostic-loader contracts; see DIAGNOSTICS.md. A raw `CD 13` byte search alone would not establish code; the ledger retains contiguous decoded instruction windows.

### Direct target-software observations

- CPU0 file `00DC–012F` tests 8086 flags and register/segment operations, resembling the baseline POST's early CPU checks. A diagnostic may execute privileged state changes under its own saved stack; a protected-mode-only harness is not an adequate execution context.
- CPU0 file `0760–07A9` reads PIC initialization/base state through `63` while manipulating `69.6`.
- CPU0 file `07D8–080A` enables diagnostic request injection with `69.7`, walks request masks through `63`, and records ISR/IRR through actual interrupts. BOOT.md gives the full transaction sequence and its boundary conditions.
- CPU0 file `01AE–0245` generates an NMI with the diagnostic controls and restores the prior vector/state; it is not merely checking an NMI-present flag.
- CPU0 file `025B–057D` requires working BIOS date/time and RTC/RAM/alarm behavior before the later timer/PIC/DMA routines are reachable. RTC RAM is tested at `036A–03A8`; INT 70h is hooked at `03AA–03C6`; `B1=02` is written/polled at `03D0–03E0`; INT 4Ah is hooked at `041A–0431`; BIOS alarm AH=06 is called at `044F–0451`. Failure enters the module's error path, not a no-clock branch.
- CPU0 file `0AE8–0B23` verifies low-nibble read/write state at page ports `87/83/81/82`. Same-value writes make it insufficient to prove that no aliases exist.
- DSKT1 file `06D3–06F3` uses INT 13h/AH=08 to discover installed drives, then resets through AH=00.
- DSKT1 file `0940–099B` reads track 10 sector 1, tolerates a media-change retry path, then tries sector **18** and records either **18 or 9 sectors/track** depending on the returned status. This is meaningful target-software support for HD/DD media, stronger than a generic Model 25 assumption that all drives are 720 KiB.
- DSKT1 file `0C77–0CD4` calls INT 13h/AH=18, installs the returned parameter pointer, prepares CHRN format descriptors, and formats a track through AH=05. It must be run only with disposable writable media when exercising destructive tests.

These diagnostics expect BIOS and hardware to cooperate. They do not independently reveal the target system ROM's part number, C000 code, IRQ edge timing, all FDC raw command behavior, or full page alias decode. Diagnostic pass/fail is one observation, not a replacement hardware specification.

### Why a baseline diagnostic pass is not transferable

The adjacent `8530_fdc_findings.md` records an emulator investigation in which Model 30 diskette diagnostics exposed errors **630** and **645**, while the Model 25 diagnostics tolerated some of the same controller behavior. The recorded issues were incorrect seek/recalibrate handling when already at the destination or with the motor stopped, and an index bit hard-coded to zero at RAS port `3F0.2`.

The general lesson is sound: software differences can expose a real gap in the shared device model. The recorded passes, line numbers, and development status belong to that prior environment. This handbook does not claim those tests were rerun, that the cited emulator still has those bugs, or that a physical 7690 was involved. STORAGE.md turns the documented index signal and command transitions into explicit future acceptance scenarios without importing a particular emulator's patches.

## 7. Model 30 noninheritance

The **8086** Model 30 is not an AT either. Nevertheless, several Model 30 features must be deliberately excluded from a 7690 profile unless independently established:

### RTC and alarm

The Model 30 has an MM58167-family clock with counter/RAM registers at `E0–EF` and command/status registers at `B0–BF`, a 32.768-kHz crystal, and battery support; its alarm participates in proprietary IRQ1 demultiplexing. These details are established for the Model 30 by its primary technical reference and schematic, indexed in the external `hardware_spec.json` and `model_differences.json`.

The 7690 hardware map does not list these decodes, its TR descriptor says no RTC, and the operator text conflicts. Neither the common `FA` model byte nor target submodel `00` establishes the Model 30's clock hardware. **However, CPU0 does more than preserve possibly unused state:** its normal path exercises `B0–B5`/`E0–EF`, hooks INT 70h and INT 4Ah, and requires BIOS date/time/alarm functions to succeed before later platform tests. This is independent target-software evidence for a compatible clock interface, although not a chip identification or physical measurement. A research configuration intended to pass the complete diagnostic needs that behavior. Full alarm-mask/routing semantics and actual target population remain OPEN; do not infer every Model 30 register bit merely from an `A1` save/restore.

### Integrated fixed disk

The Model 30 launch configurations included a 20-MB fixed-disk option using the IBM planar interface, IRQ5 and DMA3. The Model 25 baseline ROM also contains compatible fixed-disk support and the external corpus discusses later Model 25 disk options. The 7690's explicit target map reserves `65.0`, reserves `62.2`, names IRQ5 unused and DRQ3 unused, and omits the fixed-disk I/O range.

Thus the model-reuse layer should not claim an onboard target hard disk, map `320–32F` by default, or route every IRQ5 as fixed-disk completion. A separately configured expansion adapter is a separate device with its own ROM and resource ownership. The target descriptor's “BIOS uses DMA channel 3” statement remains a documented inconsistency/capability clue, not an instruction to populate a disk to satisfy it.

### Display and enclosure

The Model 30 uses an external analog monitor connection; the Model 25 uses an integrated analog display. The 7690 has neither as its final display path. Its interface adapter transforms MCGA output for its LCD and adds touch/bar-code/keyboard integration. A shared MCGA frame buffer does not eliminate the LCD's register/clock/ROM layer. Model 30 monitor-sense assumptions cannot substitute for target adapter initialization.

### ROM revisions and POST addresses

Model 30 revision 0/1/2/4 images have different code placement and identity history in the baseline corpus. An offset quoted for one of them must not be used to patch or interpret the Model 25 images, let alone the 7690. Even the two nearly identical Model 25 Type 1/2 images require explicit identification in an evidence report. “IBM PS/2 BIOS” is not adequate provenance.

### No AT/MCA inheritance by naming

Do not import:

- a 286 protected-mode reset/shutdown path;
- a second PIC or IRQ9/IRQ12 interpretation for `71`/pointing input;
- AT CMOS index/data or NMI control at `70/71`;
- a 16-bit ISA DMA channel-5 floppy shortcut;
- MCA POS configuration or MCA bus arbitration;
- VGA plane/chain/read-map behavior merely because a display is called PS/2;
- an AT 8042 keyboard command/data model.

All of these would replace a target-specific interface with a familiar but different machine. Sharing common low-level CPU/765/8253/8237 algorithms remains appropriate where the board's wiring and decode are kept explicit.

## 8. Contradiction register and implementation policy

| Conflict | Best available evidence | Required treatment |
|---|---|---|
| `68` versus `6B` RAM control | Target page image clearly prints `6B` | Correct OCR interpretation; this one is resolved |
| `80–BF` versus `80–8F` DMA aperture | Target page image clearly prints `0080–008F` | Correct OCR interpretation; do not map RTC space as DMA |
| Shifted DMA page channels | Target image prints shifted map; target CPU0 expects baseline addresses; baseline ROM demonstrably writes ch2 page to `81` | Provisional inherited map with OPEN target channel-attribution check |
| “PIT1 refresh” shorthand | Target and baseline full hardware description use diagnostic RAS input | Follow actual clock direction, not summary wording |
| 720-KiB-only BIOS drive table versus HD drive | Target Operations explicitly 1.44 MB; target DSKT1 probes 18 sectors/track | Do not shrink hardware to 720 KiB; document missing exact ROM overrides |
| Floppy opcode table collisions | Target images contain incorrect values; primary baseline images and ROM sequences give canonical ones | Correct the operational model with explicit errata table in STORAGE.md |
| No RTC versus continuous battery clock and mandatory diagnostic clock test | Two target manuals disagree; CPU0 requires BIOS date/time, RTC RAM and alarm before PIT/PIC/DMA; no target ROM/RTC capture | Keep physical identity OPEN, preserve the demonstrated software requirement, and never call a no-RTC skip a complete diagnostic pass |
| Target submodel 00 versus baseline 01 | Both statements/bytes are clear | Keep distinct identities; no target ROM hash claim |
| Target DRQ3 unused versus C0 feature bit 7 | Same target book makes both statements | Distinguish BIOS capability from populated hardware; keep conflict visible |
| Port `62.2`/`65.0` fixed-disk bits | Target marks reserved; baseline implements disk-related functions | Use target reservations, not parent-class defaults |
| Descriptor pattern at `E6F5` | Baseline code dynamically selects `5876` or `E6F5` | Trace active path; a pattern candidate alone is insufficient |
| Baseline Type 2 board associated with 7690 | Secondary service/planar history, no target ROM dump | Useful acquisition lead, never firmware authentication |

A compatibility experiment may choose a provisional interpretation to obtain traces. Record that configuration and its evidence label. Do not patch ROM bytes, suppress errors, or combine mutually exclusive decodes and then call the result an authentic machine. A hardware abstraction should reflect actual ownership boundaries; it need not introduce separate classes for every byte when the same state machine can implement a proven shared behavior.

## 9. Implementation boundaries and future proof

A practical reuse boundary has three layers:

1. **Shared chip algorithms:** 8086 execution, 8237 transfer machinery, 8253 counters, 765 command phases, UART, and MCGA core. These must still expose the board's clocks, gates, bus width, and interrupt interfaces.
2. **8086 PS/2 planar integration:** custom PIC/keyboard extensions, chip-select routing, RAM parity/remap, DMA pages, refresh diagnostic wiring. This layer is the main reusable Model 25 contribution, subject to the explicit target reservations and unresolved decode details.
3. **7690 interface and configuration:** C000 ROM, LCD path, touch/bar-code/keyboard bridge, power ride-through, 640-KiB configuration, HD drive and target identity. These cannot be supplied by relabeling a baseline BIOS image.

Meaningful future acceptance work should include:

- Running the unmodified **identified baseline ROM** first as a baseline-only experiment and recording its reset/POST behavior separately from the target.
- Capturing both target system ROM lanes and the full interface-adapter ROM, hashing originals before deriving combined images, and comparing code/data identity instead of assuming Type 2 equality.
- Recording the target's actual INT 15h/C0h descriptor and INT 1Ah function behavior under normal power, ride-through, and power-off restart.
- Giving DMA page registers distinct values and checking physical destinations, including independently tested read/write aliases; same-value register readback cannot prove channel attribution.
- Exercising CPU0's PIC diagnostics without writing its answer variables from the emulator.
- Testing target HD/DD diagnostics with 18/9-sector media and a real change latch, not just accepting a 720-KiB boot sector.
- Demonstrating early C000 initialization and the final LCD path rather than forcing analog monitor presence.
- Keeping baseline-only emulator pass reports, target software experiments, and actual hardware measurements as separate evidence classes.

**Completion boundary of this research:** the platform chapters and ledgers provide a grounded target/baseline contract, not authentic7690 POST or a full-machine diagnostic pass. Page-image checks and real binary decoding are supplemented by the isolated CPU0 ROM/clock experiments described above. Generic DOS boot/driver execution is separately recorded in [VERIFICATION.md](VERIFICATION.md); it does not verify the7690 planar. Exact target firmware identity, gate-array electrical/alias semantics and physical clock implementation remain acquisition/research prerequisites.
