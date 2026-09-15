# IBM 7690: diskette hardware, media, DMA, and BIOS

## Scope and evidence

This chapter covers the workstation's **integrated diskette subsystem**, not an assumed AT floppy controller and not an inherited Model 25 fixed disk. It connects the IBM diskette gate array, 765-class controller command engine, drive/media state, DMA channel 2, IRQ6, INT 13h, BDA state, boot media, and supplied diagnostics. [BOOT.md](BOOT.md) owns CPU/bus timing, DMA page-map uncertainty, PIC/NMI, and reset/ROM scanning. [MODEL25.md](MODEL25.md) identifies the comparative ROMs and limits on inheritance.

Evidence labels are local: **DOCUMENTED** for IBM publications, **BINARY** for identified software bytes, **INFERENCE** for implementation consequences or comparative choices, and **OPEN** for unresolved details. No physical7690 controller trace, drive measurement, target system ROM, or target interface-adapter ROM was supplied. No target-controller execution or complete hardware diagnostic pass is claimed; [generic DOS boot evidence](VERIFICATION.md) is a separate boundary.

| Source | Location and use |
|---|---|
| [7690 Technical Reference](../IBM_7690_Clinical_Workstation_Technical_Reference.pdf), TR | PDF 49–62 / printed 1-80–1-107: diskette hardware, command/status tables, signal timing and connector; PDF 124–128 / 6-32–6-41: INT 13h; PDF 138–141 / 6-60–6-67: BDA/DPT; PDF 144 / 7-4–7-5: power loss |
| [7690 Operations](../IBM_7690_Clinical_Workstation_Guide_to_Operations.pdf) | PDF 15–16 / printed 1-10–1-13: diagnostic boot/copy/format; PDF 27–28 / 3-6–3-9: disk errors and battery; PDF 39 / A-2–A-3: HD/DD media and write protection |
| [TR searchable text](../DOCUMENTATION/OCR/TECHREF.txt) | Lines 2540–3194, 6422–6615, 7124–7165, 7209–7243, 7288–7313, 7387–7416 |
| [DSKT1.DGS](../7690diag/DSKT1.DGS) | 4,800 bytes, SHA-256 `4d188e243a57882f8ec36e5539fb8054a36a88a3dfc2d5f10db571d70f03409c`; exact file offsets below |
| [7690KQPW.IMA](../7690KQPW.IMA) | Supplied sector image; geometry and hashes below |
| [Platform evidence ledger](../ANALYSIS/platform-evidence.json) | Exact hashes, BPB fields, target diagnostic and comparative ROM instruction windows |
| External Model 25 primary reference | `/Users/josh/src/bios8530/PS2_Model_25_Technical_Reference_Jun87.pdf`, especially PDF 102–105 and 111 / printed 1-89–1-92 and 1-98: independent opcode-table evidence |

The target register/command/status tables were read from rendered page images. This is essential: **several target command opcodes are printed incorrectly in the original book**, rather than merely misrecognized by OCR. Section 5 keeps the erroneous printed value and the independently supported operational value separate.

## 1. Configuration: an HD-capable workstation with a DD diagnostic disk

**DOCUMENTED — Operations PDF 39 / printed A-2.** The workstation has a **3.5-inch 1.44-MB drive**, supporting 2.0-MB unformatted HD media and 1.0-MB unformatted media formatted to 720 KiB. The introduction also explicitly names the 1.44-MB drive. These are not capacities inferred from the Model 25 name.

The ordinary original Model 25 configuration used a 720-KiB drive. Reusing a Model 25 machine profile must therefore not cap the 7690 at 720 KiB. Conversely, the supplied diagnostic diskette is deliberately low density; its capacity does not identify the drive's maximum capacity.

**Documented contradiction — TR PDF 126–127 / printed 6-37–6-39:** INT 13h/AH=08 lists only drive type `03`, “720 K, 3.5 in, 80 track,” and AH=17 lists only `AL=04`, “720K diskette in a 720K diskette drive.” These tables do not describe the advertised HD configuration completely. The TR's rate fields do list 500/250 kbps, and actual target diagnostic software handles 18- versus 9-sector media. Thus the mismatch is not a reason to delete HD support.

**OPEN:** the actual target BIOS's AH=08 drive-type value, all returned HD parameter tables, exact density sensing, and whether any override is installed by the C000 interface-adapter ROM. Do not silently extend the table with a familiar AT return value and label it observed target behavior.

### Media rules versus image geometry

Operations PDF 39 says:

- Format HD media to 1.44 MB with a 1.44-MB drive.
- Do not format HD media as 720 KiB; IBM warns such media will be unreliable even if reformatted.
- Format low-density media to 720 KiB; DOS may otherwise select the drive's maximum 1.44-MB format.
- For interchange with a 720-KiB drive, use low-density media formatted to 720 KiB, not HD media.
- An uncovered write-protect window inhibits writes. The original Diagnostic Diskette is permanently write-protected.

**INFERENCE:** model **drive capability**, **inserted medium density**, **recorded track layout**, and **write protection** separately. A 737,280-byte host file is a sector layout, not an electrical density sensor. Mounting it in an HD-capable drive should not change the drive identity to a DD-only drive. Conversely, accepting an HD sector layout in a DD-only configured drive merely because the host file can be indexed is not physical emulation.

For conventional sector-image representation, the supplied image establishes `80 cylinders × 2 heads × 9 sectors × 512 bytes`; the analogous 1.44-MB representation is `80 × 2 × 18 × 512 = 1,474,560` bytes. The latter is an **INFERENCE from the conventional layout and target 18-sector diagnostic path**, not an independently captured HD disk supplied here. Neither formula can represent malformed sector IDs, deleted data, nonstandard sector lengths, CRC errors, or track gaps without extra metadata.

### Controller capacity versus connectors and installed drives

**DOCUMENTED — TR PDF 49 / printed 1-80:** a single **40-pin** internal connector carries the signals necessary for **two** diskette drives. The DOR nevertheless contains motor/select fields for units 0–3, while the main status register documents busy bits only for drives 0 and 1. Register field width does not prove that four physical drives can be attached. The advertised workstation has one internal drive; a second controller-level unit must not appear present simply because `US=1` is representable.

## 2. State ownership and bus integration

The diskette subsystem has distinct owners:

| Owner | State it must own |
|---|---|
| Planar select/router | `65.3`, whether I/O cycles select the onboard diskette logic or go to the expansion channel |
| Diskette support gate array | DOR, CCR/rate/precompensation controls, DMA/IRQ masking, signal-status views, latched RAS events, data-separator/PLL behavior |
| 765-class command engine | Command collection, execution phase, result packet, per-drive seek state, pending completion/sense state, byte-transfer requests, error status |
| Drive | Selected unit/head, cylinder/track-zero sensor, motor/spindle/rotation/index, ready and fault signals, change latch, power availability |
| Medium | Density, write-protect state, track/sector IDs, data/address marks, bytes and CRC/error metadata |
| 8237 DMA | Channel-2 address/count/mode/mask/page/current transfer and terminal-count event |
| PIC | IRQ6 request and in-service state, masking, EOI; not the FDC's result FIFO |
| BIOS in guest RAM/ROM | DPT selection, BDA media/recalibration/motor/status cache, retry policy, INT 13h error translation |

**DOCUMENTED — TR PDF 49 / printed 1-80:** the diskette gate array decodes registers, controls read/write clocks, write precompensation and transfer rate, masks interrupt and DMA request lines, and provides phase-error detection to a PLL. The phase detector/amplifier and VCO keep the read clock aligned with disk data.

**INFERENCE:** a sector-image implementation may abstract the PLL/flux path, but should state that fidelity boundary. It must still generate command progress, request/acknowledge/terminal-count transitions, rotational ID selection, meaningful errors, and drive status. A function which copies sectors directly on INT 13h does not implement these hardware interfaces.

The onboard controller uses **IRQ6 and DRQ2** (TR PDF 15–16 / printed 1-13–1-14). DMA transfers are byte-wide at the nominal 4-MHz controller timing described in BOOT.md. `65.3=0` removes the onboard select and routes its I/O cycles to the channel; it is not an alias for holding the 765 in reset. Likewise, DOR's interrupt/DMA enable is not the PIC mask and not the 8237 channel mask. Keep all three gates separate.

Power loss is another independent gate. **DOCUMENTED — TR PDF 144 / printed 7-4; Operations PDF 28 / 3-9:** during battery ride-through the CPU remains running but the diskette drive and LCD are not operational. A read cannot complete successfully from its host image simply because the guest CPU did not reset. Exact in-flight controller status after drive power disappears is OPEN; it must be determined from the selected controller/drive model and eventually checked against target hardware, not papered over with automatic success.

## 3. Register map and exact gate-array bitfields

**DOCUMENTED — TR PDF 49–51 / printed 1-81–1-85.**

| Port | Read | Write |
|---|---|---|
| `3F0` | RAS port A, signal status | No target write function documented |
| `3F1` | RAS port B, signal status | No target write function documented |
| `3F2` | No target readback function documented | Digital Output Register, DOR |
| `3F3` | No target function documented | No target function documented |
| `3F4` | Main Status Register, MSR | No target function documented |
| `3F5` | Execution data or result bytes according to phase | Command/parameter or execution data according to phase |
| `3F6` | No target function documented | No target function documented |
| `3F7` | Digital Input Register, DIR | Configuration Control Register, CCR |

Do not automatically add a later PC FDC's tape-drive register, data-rate-select register at write `3F4`, software-reset bit, enhanced FIFO configuration command, lock/version commands, or DOR readback. The allocated range is not permission to populate every hole. A generic controller core can support those for other machines, but the 7690's published surface does not establish them.

### `3F0`: RAS port A, read-only

| Bit | Target figure label | Owner / consequence |
|---:|---|---|
| 7 | IRQ6 | Interrupt request signal; must relate coherently to controller completion |
| 6 | DRQ2 | DMA request signal; must relate coherently to execution byte demand |
| 5 | Step, latched | A step event is observable beyond a fleeting combinational pulse |
| 4 | Track 0 | Track-zero state from selected drive |
| 3 | `-Head 1 Select` | Active-low head-select signal view |
| 2 | Index | Rotation/index state, not a permanent zero |
| 1 | Write Protect | Medium/drive write-protect indication |
| 0 | `-Direction` | Active-low step-direction signal view |

Source: TR Figure 1-63, PDF 49 / printed 1-81, image checked. The minus signs matter: a register exposing a signal level is not automatically a positive logical predicate with the same bit position. **OPEN:** which RAS IRQ/DRQ observations are before or after the DOR gate, exact latched-step clear conditions, and the full polarity transformations for every board revision. The figure names the surface; it does not define a universal read-clear latch behavior. Do not clear all RAS latches on every read without evidence.

### `3F1`: RAS port B, read-only

| Bit | Meaning |
|---:|---|
| 7 | Reserved |
| 6 | `-Drive Select 1` |
| 5 | `-Drive Select 0` |
| 4 | Write Data, latched |
| 3 | Read Data, latched |
| 2 | Write Enable, latched |
| 1 | `-Drive Select 3` |
| 0 | `-Drive Select 2` |

Source: TR Figure 1-64, PDF 49 / printed 1-81. This target table says **read-only**. A baseline summary saying that `3F1` may also be writable is not enough to add a target write function. Signal-history latches cannot be reproduced by returning a constant based only on whether an image is inserted. **OPEN:** the latch set/clear truth table and power-on values.

### `3F2`: Digital Output Register, write-only

| Bit | Meaning |
|---:|---|
| 7 | Motor enable 3 |
| 6 | Motor enable 2 |
| 5 | Motor enable 1 |
| 4 | Motor enable 0 |
| 3 | DMA and interrupt enable |
| 2 | `-Controller Reset`: clear asserts reset; set releases it |
| 1–0 | Select unit: `00` drive 0, `01` drive 1, `10` drive 2, `11` drive 3 |

Source: TR Figure 1-65, PDF 50 / printed 1-82. **All DOR bits are cleared by reset.** This establishes a reset value for this register; it does not establish reset values for every neighboring register. `1C` is the arithmetic combination selecting drive 0, releasing controller reset, enabling DMA/IRQ, and enabling motor 0; `0C` leaves the motor off. These are useful decoded combinations, not a claim that all target firmware always writes those exact bytes in that order.

**INFERENCE:** controller reset aborts/clears command-engine state according to the 765 reset protocol. It must not erase the medium, pretend the head has mechanically recalibrated, clear the physical disk-change latch without a step, or automatically unmask IRQ6/DMA2. Releasing reset and an eventual reset-completion interrupt are distinct events. The exact reset-completion sense queue and its timing on the target variant are OPEN until a controller/firmware trace is available; do not conflate every pending interrupt with one seven-byte read/write result.

### `3F7`, read: Digital Input Register

| Bit | Meaning |
|---:|---|
| 7 | **`-Diskette Change`** |
| 6–4 | Reserved |
| 3 | DMA enable |
| 2 | No write precompensation |
| 1 | 250-kbps rate select |
| 0 | Reserved |

Source: TR Figure 1-66, PDF 50 / printed 1-82. Read and write are **different registers** at the same address. Bits 3/2/1 provide control-state observations; bit 7 is drive/media state. Do not return the last CCR write as the full DIR value.

**BINARY — comparative Model 25:** `F000:4E81–4E8A` reads `3F7` and tests `80`; caller `4AC0–4AFC` treats a set bit as the no-change path and a clear bit as change requiring recovery. This supports the negative polarity in the target figure: **zero indicates asserted change** on that comparative path. A generic AT-style positive “changed” DIR bit is not safe to inherit.

The physical `-Diskette Change` signal is asserted at power-on and on disk removal, and remains asserted until **a disk is present and a step pulse is received** (TR PDF 61 / printed 1-105). Insertion alone is insufficient. Controller reset alone is insufficient. Reading DIR is not the documented clearing action. A seek command that generates no step must not accidentally clear the physical latch merely because the requested cylinder equals the current cylinder.

### `3F7`, write: Configuration Control Register

| Bit | Meaning |
|---:|---|
| 7–3 | Reserved zero |
| 2 | No write precompensation |
| 1 | 250-kbps rate select |
| 0 | Reserved zero |

Source: TR Figure 1-67, PDF 50 / printed 1-83. The BDA rate definitions on printed 6-64 identify the two supported rate encodings as `00=500 kbps` and `10=250 kbps` before/after the appropriate bit placement. Thus the published CCR selects **500 kbps with bit 1 clear** and **250 kbps with bit 1 set**. It is not a four-rate AT CCR: codes with bit 0 set are reserved in this target table, not documented 300-kbps or 1-Mbps modes.

**INFERENCE:** rate selection controls decoding timing; it does not rewrite the medium's format or update the BIOS's media-cache byte directly. A wrong-rate read should fail at the controller/sector-search layer, not return the right bytes because the host already knows an LBA. With bit 2 set, precompensation is disabled; that control can be retained even in a sector-level implementation which does not synthesize write flux.

### `3F4`: Main Status Register

| Bit | Meaning / software use |
|---:|---|
| 7 | Request for Master / data register ready for CPU transfer |
| 6 | Data direction: `1` controller to CPU, `0` CPU to controller |
| 5 | Non-DMA mode indication |
| 4 | Controller busy; target prose describes read/write execution |
| 3–2 | Reserved in the target table |
| 1 | Drive 1 seeking/busy |
| 0 | Drive 0 seeking/busy |

Source: TR Figure 1-68, PDF 51 / printed 1-84. MSR may be read at any time. Its RQM/DIO pair controls whether a transfer at `3F5` is currently legal. **BINARY — comparative Model 25 `F000:4D5E–4D81`:** BIOS waits for `(MSR & C0) == 80` before writing a command byte. A permanently ready response with no phase transition is not correct simply because one polling loop exits.

**INFERENCE — compatible core:** preserve command-busy state while collecting parameters and returning results, and preserve per-drive seek-busy state independently. The target's brief bit-4 prose does not give the full 765 phase truth table. Do not turn all busy bits into one “transfer active” boolean, and do not expose four seek-busy bits because a generic controller supports four units when the target explicitly reserves bits 3–2.

## 4. Command, execution, and result phases

**DOCUMENTED — TR PDF 51 / printed 1-85.** Commands are multibyte transfers with up to three phases:

1. **Command:** CPU writes opcode and parameters through `3F5` when MSR permits CPU-to-controller transfer.
2. **Execution:** controller performs seek, ID search, data transfer, comparison, or formatting. Some commands have no data execution phase; data commands may use DMA or programmed transfers according to the controller's Specify configuration.
3. **Result:** CPU reads the prescribed status/CHRN bytes through `3F5` when MSR permits controller-to-CPU transfer.

**INFERENCE — implementation invariant:** a result byte is consumed only by a valid result-phase read. The next command cannot silently overwrite an unread result packet. A status read at `3F4` must not dequeue a result, advance a sector, or acknowledge a seek completion. Data DMA acknowledge cycles are not ordinary command-port writes and must not append to the command buffer.

Use independent state for:

- the current command and number of collected parameters;
- execution cursor/sector/byte position;
- per-drive seek destination, present cylinder, and completion status;
- pending sense-interrupt completions;
- the result packet and next result byte;
- internal IRQ and DRQ assertions plus external gates;
- physical drive state and medium metadata.

A seek may finish while software is preparing another operation; “controller idle” and “all drives stopped seeking” need not be identical. Seek/Recalibrate have **no immediate result phase**, but completion is retrieved using Sense Interrupt Status. Specify has no result phase. Sense Drive Status returns only ST3. Invalid commands return a single ST0 status. Treating all commands as seven-byte result commands is a common emulation failure.

**OPEN:** exact non-DMA service deadline, per-byte ready latency, reset sense-queue cardinality, all command-abort corner cases, and unsupported-mode behavior on the exact fitted 7690 controller silicon. The published interface is clearly 765/8272-family, but a part marking or authentic ROM/controller trace is needed before claiming revision-specific electrical behavior. Do not add newer enhanced-controller facilities to compensate for missing details.

## 5. Command bytes and the printed opcode errata

### Independently supported operational command set

The table below uses the canonical 765-family encodings. Most target tables agree. Where they do not, **primary Model 25 page images** were used as independent evidence, explicitly listed in the errata table below. Modifier bits are `MT=80`, `MF=40`, `SK=20` only where shown. Unit/head parameter `U` normally packs head select in bit 2 and unit in bits 1–0; upper bits are don't-care in the printed command tables. Seek/Recalibrate tables show bit 2 as zero.

`C,H,R,N` are sector ID cylinder, head, record, and size code; `EOT` is final sector number; `GPL` is gap length; `DTL` is data length for N=0; `STP` is scan step; `D` is format fill byte.

| Operation | Base opcode | Allowed high modifiers | Bytes written including opcode | Result |
|---|---:|---|---|---|
| Read Data | `06` | MT, MF, SK | `op U C H R N EOT GPL DTL` (9) | `ST0 ST1 ST2 C H R N` |
| Read Deleted Data | `0C` | MT, MF, SK | Same 9-byte layout | Same 7-byte result |
| Read a Track | `02` | MF, SK in target table | Same 9-byte layout | Same 7-byte result |
| Read ID | `0A` | MF | `op U` (2) | Same 7-byte result, from encountered ID |
| Write Data | `05` | MT, MF | `op U C H R N EOT GPL DTL` (9) | Same 7-byte result |
| Write Deleted Data | `09` | MT, MF | Same 9-byte layout | Same 7-byte result |
| Format a Track | `0D` | MF | `op U N SC GPL D` (6), then execution CHRN stream | Same 7-byte result |
| Scan Equal | `11` | MT, MF, SK | `op U C H R N EOT GPL STP` (9) | Same 7-byte result |
| Scan Low or Equal | `19` | MT, MF, SK | Same 9-byte scan layout | Same 7-byte result |
| Scan High or Equal | `1D` | MT, MF, SK | Same 9-byte scan layout | Same 7-byte result |
| Recalibrate | `07` | None | `07 unit` (2) | None immediately; Sense Interrupt Status later |
| Sense Interrupt Status | `08` | None | `08` (1) | `ST0 PCN` for a pending completion |
| Specify | `03` | None | `03 SRT/HUT HLT/ND` (3) | None |
| Sense Drive Status | `04` | None | `04 U` (2) | `ST3` |
| Seek | `0F` | None | `0F unit NCN` (3) | None immediately; Sense Interrupt Status later |
| Invalid/unsupported command | Not a valid operation | — | Opcode causes invalid-command result | ST0 with invalid-command interrupt code |

Sources: TR PDF 53–59 / printed 1-88–1-100, Figures 1-69–1-96; independent baseline pages below. For a Sense Interrupt Status with no pending completion, the exact no-pending result behavior of the selected silicon must be modeled from its compatible core/revision evidence; the target book's fixed two-byte illustration does not settle every case.

### Image-confirmed target printing errors

| Command | Target printed value, ignoring high modifier bits | Operational value supported independently | Target location | Independent primary Model 25 location |
|---|---:|---:|---|---|
| Read ID | `06` (`0 MF 0 0 0 1 1 0`) | `0A` (`0 MF 0 0 1 0 1 0`) | TR PDF 54 / printed 1-91, Fig. 1-75 | PDF 102 / printed 1-89, same figure |
| Write Data | `06` | `05` | TR PDF 55 / printed 1-92, Fig. 1-77 | PDF 103 / printed 1-90 |
| Write Deleted Data | `0E` | `09` | TR PDF 55 / printed 1-93, Fig. 1-79 | PDF 104 / printed 1-91 |
| Format a Track | `0C` | `0D` | TR PDF 56 / printed 1-94, Fig. 1-81 | PDF 105 / printed 1-92 |
| Seek | `07` | `0F` | TR PDF 59 / printed 1-100, Fig. 1-95 | PDF 111 / printed 1-98 |

This is not a speculative “7690 custom command set.” Literal implementation would make Read ID and Write Data collide with Read Data, and Seek collide with Recalibrate, while requiring different parameter counts. The independently documented common controller and baseline code support ordinary commands; for example the Model 25 ROM contains `MOV AH,4D` at `F000:488E` for MFM format and `MOV AH,0F` at `4DC0` for seek.

**INFERENCE, operational policy:** implement the established 765 command set and retain this errata record. Do not accept both conflicting opcodes as aliases based on guessed intent or future parameter count: the controller must choose a command length at the opcode, and aliasing Read/Write would destroy deterministic semantics. A real target trace would provide the final direct hardware confirmation, but there is no evidence for a bespoke incompatible command decoder.

### Parameter semantics and lengths

**DOCUMENTED — TR PDF 52 / printed 1-86–1-87 and PDF 141 / 6-67:**

- `C`/`NCN`/`PCN` are different concepts: ID cylinder, requested mechanical destination, and controller's reported present cylinder. Do not set the physical head directly from every read command's `C`.
- `H` is the ID head address; `HD` is selected head. The target text expects them equal in normal command words. A richer medium can expose an ID mismatch rather than silently repairing it.
- `R` is the record/sector ID, conventionally starting at 1; it is not a zero-based array index.
- `N=0,1,2,3` denotes 128, 256, 512, 1024-byte sectors in the BIOS DPT table. The compatible `128 << N` relation is an implementation rule for the common controller, but do not assume every possible N is supported by target media/BIOS.
- For N=0, `DTL` supplies the requested data length. Do not always transfer 512 bytes because the supplied image uses N=2.
- `EOT` is the last sector number for progression, not a total byte count. DMA terminal count is a separate stop condition.
- `MT=1` selects multitrack operation using both heads; `MF=1` selects MFM where implemented; `SK` controls skipping deleted-data marks.
- `STP=01` compares adjacent sectors during scan, `02` alternate sectors. The target text does not fully specify every byte-level scan comparison/wildcard convention; retain that as a compatible-core/revision requirement, not an invented target extension.
- Specify's first parameter packs SRT in its upper four bits and HUT in the lower four. Its second packs HLT in bits 7–1 and ND in bit 0. The target prose calls ND “nondata,” while MSR explicitly identifies non-DMA mode; the operational role is the controller's DMA/non-DMA transfer selection, not disabling all data commands.
- The printed SRT examples `1111→1 ms`, `1110→2 ms`, `1101→3 ms`, HLT 2–256 ms in 2-ms increments, and HUT 0–240 ms in 16-ms increments are controller-clock-dependent timing descriptions. Do not apply them at both data rates without accounting for the selected compatible controller's clock scaling.

### Execution consequences

**INFERENCE:** Read ID returns the next encountered valid sector ID as rotation advances; it is not an alias for reading sector 1. Read Track must follow track-oriented controller semantics, not a host “read the entire image” operation. Deleted-data commands must preserve/address the mark distinction; a plain sector-image backend lacking mark metadata cannot claim complete support by treating them as normal data commands.

Format consumes CHRN descriptors during execution, one four-byte tuple per sector. The `D` parameter is the data fill byte, not a pointer to a ready-made sector buffer. The controller must produce the requested IDs/layout, update medium data only when writable and powered, and return real completion/error status. A successful BIOS format should not be synthesized while leaving the underlying medium unchanged.

## 6. Controller status and real error paths

**DOCUMENTED — TR PDF 59–60 / printed 1-101–1-103, image checked.** ST0–ST3 are returned status registers, not independently addressed I/O registers. ST0/ST1/ST2 plus CHRN form data-command results; ST3 is returned by Sense Drive Status.

### ST0

| Bits | Meaning |
|---|---|
| 7–6 | Interrupt code: `00` normal completion; `01` command began but terminated unsuccessfully; `10` invalid command, never started; `11` ready signal changed during execution |
| 5 | Seek End |
| 4 | Equipment Check: drive fault or no track-zero signal after 77 Recalibrate step pulses, as described by the target book |
| 3 | Not Ready when a read/write command is issued to a not-ready drive |
| 2 | Selected head at interrupt |
| 1–0 | Selected unit at interrupt |

The 77-step Recalibrate bound is explicitly printed even though ordinary media has 80 tracks. Software may need repeated recalibration attempts from a distant cylinder; do not silently turn the command into unlimited instant motion. Controller/drive revision behavior should be preserved rather than changed just to make every initial cylinder succeed.

### ST1

| Bit / mask | Meaning |
|---|---|
| 7 / `80` | End of Cylinder, attempted access beyond the final sector |
| 6 | Reserved |
| 5 / `20` | Data Error, CRC error in ID or data field |
| 4 / `10` | Overrun, controller not serviced within the transfer deadline |
| 3 | Reserved |
| 2 / `04` | No Data, requested sector/ID cannot be found or read as required |
| 1 / `02` | Not Writable, write-protect during Write/Write Deleted/Format |
| 0 / `01` | Missing Address Mark in ID; the target description says ST2 bit 0 is also set |

### ST2

| Bit / mask | Meaning |
|---|---|
| 7 | Reserved zero |
| 6 / `40` | Control Mark / deleted-data mark encountered during Read Data or Scan |
| 5 / `20` | CRC/data error in the data field |
| 4 / `10` | Wrong Cylinder, command C differs from recorded ID C |
| 3 / `08` | Scan Equal Hit |
| 2 / `04` | Scan Not Satisfied |
| 1 / `02` | Bad Cylinder, related to mismatched C / recorded `FF` according to the target prose |
| 0 / `01` | Missing data/deleted-data address mark |

The book's Bad Cylinder prose is less precise than a full controller datasheet; do not collapse every wrong-cylinder error into Bad Cylinder solely because both descriptions mention a mismatch. The compatible core should retain their distinct conditions, with exact revision semantics documented when established.

### ST3

| Bit / mask | Meaning |
|---|---|
| 7 / `80` | Fault |
| 6 / `40` | Write Protect |
| 5 / `20` | Ready |
| 4 / `10` | Track 0 |
| 3 / `08` | Two-sided |
| 2 / `04` | Head address |
| 1–0 | Unit selection |

**INFERENCE:** ST3 is a selected-drive status view. An absent unit must not report track zero, ready, two-sided, and a usable disk simply because the DOR selected it. Medium absent, drive absent, motor stopped, drive power absent, and a CRC-damaged sector are distinct physical conditions which may lead to different FDC status and BIOS timeout paths.

### Error precedence and observability

Keep raw FDC error state until the result packet is consumed; let the actual ROM perform BIOS status translation. Important distinct cases include:

- Wrong data rate or missing ID: sector search cannot find a matching recorded ID; it must not index a host sector anyway.
- Write protected: preserve medium bytes and produce Not Writable, not a host filesystem exception visible to DOS.
- DMA masked or not acknowledged in time: overrun/timeout must remain possible even though the host could instantly copy the bytes.
- Terminal count before normal progression completes: terminate according to controller semantics with coherent final CHRN and result bytes, not a blanket “all requested sectors transferred.”
- No step/track-zero response: recalibration equipment error differs from a successful no-motion recalibration already at track zero.
- Motor not yet up to speed: ID/data availability differs from a head positioning command. Do not impose a motor-on condition on every controller command.
- Power loss during write: prevent successful completion of bytes not physically writable; exact partial-write/error reporting needs a clearly stated fidelity level.

The target book does not specify a total ordering for every simultaneous error or exact final CHRN for all terminal-count boundaries. These are **OPEN silicon-level details**, not license to set every status flag at once or always return a generic controller failure.

## 7. DMA channel 2 and IRQ6 transaction lifecycle

**DOCUMENTED — target** assignment is DRQ2/IRQ6; **BINARY — comparative Model 25** shows the ordinary 8237 programming flow. BOOT.md documents the target TR's contradictory DMA page-address figure and direct target CPU0 evidence.

For the inherited working map, channel 2 has address `04`, count `05`, and high-address page `81`. A typical BIOS DMA setup clears the global first/last-byte flip-flop at `0C`, programs mode at `0B`, writes address low/high, writes page low nibble, writes `byte_count-1` low/high, and unmasks channel 2 through `0A`. These are not arbitrary “floppy DMA registers”: the byte pointer and DMA controller are shared with other channels.

**BINARY — comparative firmware anchor:** `F000:4B18–4B75`, SHA-256 of the Type 1 combined ROM `cfbdc2cd67c95c15b06be14e2e5f4bbd6991f3506428af64038b6381a1120166`; all relevant bytes are the same in Type 2. Page value is masked to `0F` at `4B49`, written to `81` at `4B4B`. The computed count is decremented at `4B62` and written at `4B64/4B6A`. The address-plus-count carry leads to BDA status `09` at `4B77`.

### Read transaction, algorithmic model

**INFERENCE from the documented interfaces:**

1. BIOS resolves media state, powers/selects the drive, waits for acceleration/head settling as required, programs rate/Specify/DMA, and issues the FDC command.
2. FDC collects the complete parameter packet using MSR/RQM/DIO. It does not begin a host-sector copy after the first opcode byte.
3. The selected physical head searches the rotating track for matching IDs under the selected rate/encoding; wrong cylinder/head/record/size can fail.
4. As data becomes available, the FDC asserts its internal DRQ. DOR bit 3 and DMA channel state determine whether the external request is serviced.
5. The 8237 owns bus cycles, transfers bytes through the board's memory map, updates current address/count, and produces terminal count. Its 16-bit address counter wraps without carrying into the external four-bit page latch.
6. Controller termination produces a result packet and IRQ6 according to its command state. The PIC sees the gated request; masking IRQ6 delays CPU service but does not rewind disk rotation or restore the transferred bytes.
7. BIOS's IRQ handler observes completion, marks its working BDA flag, sends PIC EOI, and invokes the documented completion hook. The INT 13h path retrieves result bytes and returns status/count.
8. Later PIT ticks decrement the motor-off counter; motor shutdown is not tied to the host call returning from a read.

Write reverses the DMA data direction; Format and Scan consume memory-to-controller bytes for different reasons. The data direction encoded in 8237 mode must agree with the controller command. BIOS Verify uses a compatible DMA verification path rather than requiring an ordinary caller data buffer; do not implement it by modifying the caller's RAM.

### Completion acknowledgements are different events

- **FDC result read** advances the controller's result state.
- **Sense Interrupt Status** obtains seek/recalibration/reset-related completion state.
- **PIC EOI** clears in-service priority state; it is not an FDC reset or FIFO drain.
- **DMA terminal count** tells the controller the programmed transfer is complete; it is not PIC EOI.
- **DOR DMA/IRQ enable** gates requests; it does not program PIC masks or DMA addresses.

Conflating these makes “second operation after an error” failures likely: the first operation appears complete, but the next command consumes stale status or never receives an interrupt.

## 8. Mechanical timing and connector evidence

**DOCUMENTED — TR PDF 61–62 / printed 1-104–1-106.**

| Signal | Published behavior/timing |
|---|---|
| `-Drive Select 0/1` | Active selects interface; inactive ignores control inputs and disables drive outputs; maximum select delay 500 ns |
| `-Motor Enable 0/1` | Active starts spindle; inactive lets it slow to a stop |
| `-Step` | One-track movement per active pulse; minimum pulse width 1 microsecond; direction sampled at trailing edge |
| `-Direction` | Active moves toward higher track number/spindle; inactive toward track zero; stable 1 microsecond before/after trailing step edge |
| `-Head 1 Select` | Active selects upper head 1; inactive lower head 0 |
| `-Write Enable` | Enables write-current circuits; active at least 8 microseconds before data |
| `-Write Data` | At 250 kbps: 250-ns pulses, 4/6/8-microsecond spacing; gate-array precompensation 125 ns |
| `-Index` | Active index pulse width 1 ms |
| `-Track 0` | Head at track zero; absence after recalibration is used to infer no drive |
| `-Write Protect` | Active with uncovered window, disables write-current circuits |
| `-Diskette Change` | Active at power-on/removal; clears only with disk present plus step |

These values are published interface limits, not a complete drive model. **OPEN:** exact fitted drive part number/revision, rotational speed tolerance and spin-up/down curves, track-position settle time beyond the programmable BIOS/controller parameters, how index is gated by selection/readiness, and latch reset behavior. Do not invent a measured RPM for this workstation from the existence of an index pin. A sector-level emulator can use a conventional drive model, but must label its mechanical assumptions and expose timed index pulses to RAS reads.

The 40-pin connector provides the familiar data/control signals plus power rather than a separate AT-style 34-pin cable with unrelated power plug. Signal pins in Figure 1-97 include `8` index, `10/16` motor enables 1/0, `12/14` drive selects 0/1, `18` direction, `20` step, `22` write data, `24` write enable, `26` track zero, `28` write protect, `30` read data, `32` head select, `34` disk change, `38` +5 V, and `40` +12 V; the interleaved odd pins are grounds and several early even pins are reserved/not connected. **The exact connector drawing must be consulted before physical rewiring.** The software fact is that ready/change/select/motor signals have separate ownership; an image mount is not a substitute for all of them.

**INFERENCE:** drive rotation/index must continue on emulated machine time while the CPU executes unrelated code. Returning index high every Nth port read couples spindle speed to polling frequency and can “pass” one diagnostic while being wrong. Use rotation phase and a pulse window instead. A short index pulse must remain observable when guest loops run at the documented CPU/I/O timing.

## 9. BIOS INT 13h: published API, not a host shortcut

**DOCUMENTED — TR PDF 124–128 / printed 6-33–6-40.** BIOS uses multitasking hooks:

- INT 15h `AX=90FD` before motor-acceleration wait;
- INT 15h `AX=9001` before waiting for diskette completion;
- INT 15h `AX=9101` on interrupt completion.

A replacement BIOS implementation would need to preserve this API, but when authentic ROM executes, the emulator should implement hardware and let ROM own these calls. BIOS recommends resetting then retrying a failed disk operation; the number of retries and recovery sequence belongs to the actual firmware/application, not a hidden host loop that always forces success.

### Function summary

| AH | Published operation and significant parameters/results |
|---:|---|
| `00` | Reset diskette system; DL bit 7 must be clear. Hard-reset controller and prepare it; recalibrate on next drive operation. AH/status and CF report outcome; BDA `41` updated |
| `01` | Read status of last operation; returns AH/status and CF |
| `02` | Read sectors to ES:BX; DL drive, DH head, CH/CL cylinder/sector, AL count; returns AL actually transferred, AH/status, CF |
| `03` | Write sectors from ES:BX; same CHS/count and return contract |
| `04` | Verify sectors; same CHS/count, returns AL verified and status; no ordinary caller data-buffer output is specified |
| `05` | Format track from CHRN tuples at ES:BX; DL drive, DH head, CH track, AL number of sectors; AH/status and CF |
| `06–07` | Reserved; CF set, AH=`01`, BDA status updated |
| `08` | Read drive parameters; returns ES:DI to 11-byte DPT for maximum media, maximum CHS, DL drive count, BH=0, BL type, AX=0; target printed table lists only type `03`/720 KiB |
| `09–14` | Reserved; CF set, AH=`01`, BDA status updated |
| `15` | Read DASD type: AH=`00` absent, `01` diskette without change line, `02` diskette with change line; `03` reserved |
| `16` | Disk-change-line status: AH=`00` inactive, `01` invalid drive, `06` active; CF set for nonzero AH |
| `17` | Set DASD type for format, compatibility operation; target lists AL=`04` for 720K in 720K drive; AH=18 preferred |
| `18` | Set media type for format; DL drive, CH/CL maximum cylinder and sectors; returns ES:DI to 11-byte DPT, CF/error if unsupported or invalid; must be repeated after media change |
| `19–FF` | Reserved; published error return applies |

For CHS operations, bits 7–6 of CL are the high two cylinder bits; CH is the low eight, and CL bits 5–0 are sector number. Track/head are zero-based and sector one-based. The manual says many DH/CH/CL/AL values are **not value checked**; that means errors may arise in controller execution, not that every out-of-range request succeeds.

AH=08 invalid-drive behavior is unusual and explicit: ES, AX, BX, CX, DH, DI are zero; DL is the number of installed drives; BDA status `41` is zero and CF is clear. An invalid drive query is not necessarily a generic carry-set disk error. Do not repurpose one error handler for all functions.

Before Format when multiple formats are available, call AH=18; otherwise the maximum drive capacity is the default. AH=18 checks disk change, tries to reset it, establishes the formatting data rate if it succeeds, and reports timeout `80` if the signal cannot be reset. On error the ES:DI pointer is unchanged. Returning a valid-looking table while leaving CF set or changing the pointer on failure violates the consumer contract.

### BIOS status is not raw ST0

| AH / BDA `40:41` | Published meaning |
|---:|---|
| `00` | No error |
| `01` | Invalid function/request |
| `02` | Bad address mark |
| `03` | Write protect |
| `04` | Sector not found |
| `06` | Media changed |
| `08` | **Conflict:** function-status table says reserved; BDA table says DMA failure |
| `09` | DMA boundary error |
| `0C` | Unsupported tracks/sectors-per-track combination |
| `10` | CRC error |
| `20` | General controller failure |
| `40` | Seek failure |
| `80` | Timeout |

Sources: TR PDF 125 / printed 6-34 and PDF 139 / printed 6-62. Preserve the `08` disagreement; do not assert one exact target translation until actual ROM behavior is traced. Likewise an FDC ST1 bit mask such as `02` is not a BIOS `AH=02`: ST1 `02` means write protection, whose BIOS code is `03`.

**INFERENCE:** a hardware emulator should not duplicate error translation in the controller if the BIOS already performs it. Preserve raw result bytes and let ROM return AH. A high-level BIOS substitute must document its source and test consumer-observable behavior separately from controller fidelity.

## 10. DPT, BDA, and asynchronous motor ownership

### Diskette Parameter Table

**DOCUMENTED — TR PDF 141 / printed 6-67.** INT 1Eh points to the active 11-byte diskette parameter table; AH=08 and AH=18 return table pointers as described above. The table contains:

| Offset | Meaning |
|---:|---|
| `00` | First Specify byte, SRT/HUT |
| `01` | Second Specify byte, HLT/ND |
| `02` | Timer ticks before turning motor off |
| `03` | Sector size code N: `00/01/02/03` for 128/256/512/1024 bytes |
| `04` | Sectors per track |
| `05` | Read/write gap length |
| `06` | Data length |
| `07` | Format gap length |
| `08` | Format fill byte |
| `09` | Head-settle time in milliseconds |
| `0A` | Motor-startup time in eighths of a second |

This is a byte structure in guest address space, not a hidden host configuration. Applications/diagnostics can install a different INT 1Eh table and restore it. Respect their active pointer rather than always using a compiled 720-KiB DPT. **OPEN:** exact target default bytes for DD and HD media; the manual gives field meanings but no authenticated target ROM table image here.

### BDA storage fields

**DOCUMENTED — TR PDF 138–140 / printed 6-61–6-65.** All offsets below are in segment `0040`.

| Offset | Size | Meaning |
|---|---:|---|
| `3E` | Byte | Bit 7 working interrupt flag (zero on return from diskette BIOS); bits 3–0 recalibration state for units 3–0 |
| `3F` | Byte | Bit 7 write operation versus read; bits 3–0 motors on |
| `40` | Byte | Motor-off count, decremented by timer IRQ; zero causes motors off |
| `41` | Byte | Last BIOS diskette status |
| `42–48` | Seven bytes | Controller result packet |
| `8B` | Byte | Last diskette rate bits 7–6: `00` 500 kbps, `10` 250 kbps, other encodings reserved; step-rate bits 5–4: `00` SRT=`0C`, `01` SRT=`0D`, `10` SRT=`0A`, `11` reserved |
| `90,91` | Byte each | Drive 0/1 media state: bits 7–6 rate as above, bit 4 clear means unestablished; bits 5/3 reserved; bits 2–0 reserved=`111` |
| `94,95` | Byte each | Track currently sought to for drive 0/1 |

These are **BIOS caches/workspace**, not direct drive sensors. A DMA-complete interrupt can change the working flag before an INT 13h call returns; a motor can run after the call; a medium can change while the BIOS cache still describes the old one. Do not have the host image-mount UI directly rewrite all these bytes as if firmware had already detected the change.

Timer IRQ0/INT 08h decrements the motor counter, turns off drive motors at zero, and clears running flags (TR PDF 113 / printed 6-10). Therefore a PIC/PIT failure can look like a floppy motor-control failure even when FDC reads work. Repeated reads before the timeout and a paused CPU should be distinguished from stopped machine time.

## 11. Supplied image and diagnostic-binary observations

### The supplied disk image is 720 KiB

**BINARY — [7690KQPW.IMA](../7690KQPW.IMA):**

- Length: **737,280 bytes**.
- SHA-256: **`6b89fe1a982eb7e480fb1757ca0285d9889e0154f18611a8e57cc4a8bb8997fe`**.
- OEM field at byte offsets `03–0A`: ASCII `MSDOS5.0`.
- Final boot-sector bytes at offsets `01FE–01FF`: `55 AA`.

| BPB file offset | Field | Observed value |
|---:|---|---:|
| `000B` | Bytes per sector | 512 |
| `000D` | Sectors per cluster | 2 |
| `000E` | Reserved sectors | 1 |
| `0010` | FAT count | 2 |
| `0011` | Root directory entries | 112 |
| `0013` | Total sectors | 1440 |
| `0015` | Media byte | `F9` |
| `0016` | Sectors per FAT | 3 |
| `0018` | Sectors per track | 9 |
| `001A` | Heads | 2 |

These values derive 80 cylinders and the usual sector-image layout. The signature is a fact about this image, not proof that target INT 19h requires it. The OEM string is not a proof that the installed diagnostic operating environment is retail MS-DOS 5.0; identify executable boot files separately, as in DIAGNOSTICS.md.

The image stores sectors, not raw flux/CRC/address-mark timing. Preserve it read-only as evidence and use a writable overlay or separate disposable copy for destructive diagnostics. Do not alter the original FAT/image to make an emulator boot.

### DSKT1 drive/media discovery

**BINARY — target module, zero-based file offsets:**

1. `06D9–06E8`: query INT 13h/AH=08 for drive 0, save returned drive count, then reset with AH=00. This is why AH=08 behavior matters even before read/write testing.
2. `0940–0959`: read one sector at **cylinder 10, head 0, sector 1** into the diagnostic buffer. Status `06` enters the media-change retry loop; `095C–0965` increments a counter and retries until its limit of three is reached.
3. `096D–097F`: read one sector at **cylinder 10, head 0, sector 18**.
4. `0981–099B`: timeout `80` takes an error path; status `02` or `04` selects **9 sectors/track**; otherwise it records **18 sectors/track**.

The last branch is important: this is **the diagnostic's classification algorithm**, not a universal way for an emulator to determine density. An unexpected status can lead software down the 18-sector path. A controller returning generic success or arbitrary errors for nonexistent sectors changes the diagnostic's inferred media geometry. The emulator should expose truthful operation results, not recognize this probe and return whichever value leads to a pass.

### Formatting and verification really mutate media

At file `0C77–0C95`, DSKT1 loads requested geometry and invokes AH=18, saves ES:DI, then uses the parameter pointer. At `0CAE–0CB8` it constructs CHRN tuples with cylinder `1F` (31), head `01`, supplied record IDs, and N=`02` (512 bytes). At `0CBA–0CD4` it makes up to three AH=05 format attempts. `0CDF–0CFC` verifies nine sectors through AH=04 at the selected record on cylinder 31/head 1.

**INFERENCE:** use scratch media for this path. A “read-only diagnostic image” protects the diagnostic program, but the media selected as the diagnostic test target may still be writable and intentionally reformatted. Keep source/program disk and test target distinct. A UI which silently writes through to the original supplied image is not acceptable evidence preservation.

The module header and service calls are not a stand-alone DOS COM contract. Run it through the proper diagnostic loader; file offsets must not be mislabeled `CS:0100+offset` without loader evidence.

### Diagnostic copy/format programs are not general DOS tools

Operations PDF 15 / printed 1-11 says the diagnostic Format Diskette service is **for diagnostic purposes only** and directs users to DOS FORMAT for working diskettes. Copy Diskette is only for low-density media. PDF 16 / printed 1-13 requires a blank/disposable 720-KiB target for copying the supplied diagnostic disk.

Observed binary identities:

| File | Length | SHA-256 |
|---|---:|---|
| [DFORMAT.COM](../7690diag/DFORMAT.COM) | 906 | `8d7ae244bb44ea48d85a460d2475bf9f0483e34d80d0bf32d18f7eded9f6eca7` |
| [DCOPY.COM](../7690diag/DCOPY.COM) | 2,172 | `f5c585544042d30fb8adaedcacad45fd51faf96f9142f995f92c7d26dce252c5` |

The corresponding files extracted from the supplied image have the same hashes. This chapter does not infer a full command-line interface from `.COM` filenames or claim either utility was executed.

## 12. Faults which a successful boot alone will not expose

### Index and drive speed

RAS A exposes index at `3F0.2`, and the target signal definition publishes a 1-ms index pulse. A normal BIOS sector read can succeed in a simplified controller with no exposed index state; a diagnostic polling index cannot. The adjacent baseline investigation `8530_fdc_findings.md` records a prior Model 30 emulator error `645 NO INDEX PULSE` caused by hard-coded zero. That is comparative warning evidence, not a current 7690 test result.

### Already at track zero or requested cylinder

A Recalibrate command when already on track zero should produce the compatible successful completion, not a manufactured seek failure because no motion is necessary. A Seek to the current cylinder similarly has no need to move but still has command/completion semantics. **INFERENCE from the compatible command/drive model:** do not require spindle motor power for head positioning simply because read/write data needs rotation. The baseline investigation records these as another way a controller could boot yet fail stricter diagnostics. Exact target drive power dependencies still require the actual fitted hardware specification.

### Change line and wrong polarity

If an inserted medium automatically clears change, the BIOS may never report AH=`06`. If change remains asserted forever, AH=18's reset attempt can time out. If bit-7 polarity is inherited from the wrong machine, the BIOS continually takes the wrong branch. Exercise removal, insertion without movement, actual step, and controller reset as separate transitions.

### Controller completion versus PIC state

A PIC EOI should not eat the FDC result. A result read should not blindly EOI IRQ6. A still-pending seek completion must be available to Sense Interrupt Status. An interrupt masked at `21` can remain pending while mechanical work completes. A model tested only by direct BIOS shortcuts will not establish any of these.

### Plain images hide richer media errors

The supplied image cannot encode deleted data or CRC errors. Those commands must either operate through an enriched medium representation or be explicitly outside the current implementation's medium fidelity. Returning success for an unsupported command/media representation is not faithful emulation. Error injection for research should create coherent raw controller status and media metadata, not just force a final BIOS AH value.

### Power ride-through

TR printed 7-4 advises applications to provide unlimited disk-I/O retries when primary power is lost, because the drive is unavailable until power returns. That instruction is for software recovery policy. It does not authorize the emulator to hold every disk request indefinitely or turn every transient error into eventual success. The guest may deliberately stop retrying, cancel work, or log out while CPU/RAM remain powered.

## 13. Future acceptance scenarios

These scenarios define observable interfaces worth exercising when an emulator exists. They were **not run** in this documentation task.

1. **Read/write register separation:** write CCR rate/precompensation, then read DIR with drive change asserted; verify only the appropriate control-state bits and physical change status appear. DOR write-only behavior must not become accidental generic echo.
2. **Select routing:** clear `65.3`; the onboard FDC stops responding at its I/O range while a configured channel adapter can own the cycles. DOR state and a controller reset remain distinct.
3. **Phase ordering:** issue a complete Read ID and consume exactly its result packet; leave one result unread, attempt another command, and observe the core's real phase behavior rather than silent FIFO replacement.
4. **Seek completion:** Seek/Recalibrate generate completion state retrieved by Sense Interrupt Status, without an unsolicited seven-byte data result. Include a command already at its destination, a distant recalibration, and an absent drive.
5. **Both densities:** read known sectors on conventional 9-sector DD and 18-sector HD media in the target-capable drive. Wrong-rate attempts must fail at the physical/controller layer. DSKT1's cylinder-10 sector-18 probe should infer geometry from actual returned status.
6. **DMA location and wrap:** transfer to buffers above 64 KiB with independently tagged page latches; then exercise a crossing transfer through BIOS and raw DMA separately. Record final bytes/address/count/TC, not just AH=0.
7. **DMA gating:** mask channel 2 or DOR's DMA/IRQ gate during execution. Confirm no phantom memory transfer and that error/completion state remains coherent when gates are restored.
8. **IRQ6 masking and EOI:** complete a command with IRQ6 masked, then unmask; service the actual pending source, read results, and perform PIC EOI separately. Repeating the command must not consume stale results.
9. **Index:** observe pulses over emulated time with different polling rates; period must not be a function of number of IN instructions. Confirm the documented pulse-width model and selected-drive gating chosen by the implementation.
10. **Change latch:** begin at power-on change, insert without stepping, step with media present, remove/reinsert, and reset only the controller. Check DIR polarity and BIOS AH=16/AH=18 outcomes for each transition.
11. **Write protection:** run Write/Format against protected scratch media; no data changes, raw Not Writable and correct BIOS write-protect status. Removing protection permits a real update, not a success-only stub.
12. **Format/DPT replacement:** let DSKT1 install its returned table, format cylinder 31/head 1 on scratch media, verify the recorded CHRN/data, and restore the previous pointer. A flat sector backend must account for its layout limitation explicitly.
13. **Read ID and error media:** return rotationally encountered IDs, distinguish deleted marks, missing marks, wrong-cylinder and CRC errors using a metadata-capable backend. Preserve result CHRN and error bits rather than only an error string.
14. **Motor timer:** consecutive reads refresh BIOS motor timeout; with no more activity, IRQ0 ticks turn motors off. Masking IRQ0 stops the BIOS decrement without freezing the independent FDC/drive clocks.
15. **Primary power loss:** make drive power unavailable during a pending request while CPU ride-through continues; no fabricated sector success, no unintended CPU reset, and subsequent guest retries can work after primary power returns.
16. **Evidence-safe diagnostics:** boot a read-only copy/overlay of the supplied image and provide separate disposable writable test media. Preserve original hashes and distinguish firmware POST, disk loader, DSKT1 tests, and user-visible service menu.

The remaining prerequisites are the actual 7690 ROM pair plus C000 adapter ROM, controller/drive part identification, complete RAS latch/reset and read/write alias semantics, exact HD BIOS tables, and electrical/timing traces for disputed boundaries. The chapter specifies the complete published interface and the known software expectations without replacing those missing facts with generic PC lore.
