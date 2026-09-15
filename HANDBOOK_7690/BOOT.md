# IBM 7690: processor, planar, reset, POST, and the BIOS boundary

## Scope and evidence discipline

This is the platform contract for an **8086-based IBM 7690 Clinical Workstation**, not an AT, an MCA PS/2, or a generic Model 25 with a different screen bitmap. It specifies the hardware which must exist before the system ROM and the interface-adapter ROM can initialize the machine. Floppy mechanics and INT 13h are in [STORAGE.md](STORAGE.md); the inheritance limits are in [MODEL25.md](MODEL25.md). [VIDEO.md](VIDEO.md), [KEYBOARD.md](KEYBOARD.md), [TOUCH.md](TOUCH.md), and [PERIPHERALS.md](PERIPHERALS.md) own their detailed device protocols.

**DOCUMENTED** identifies a statement in an IBM publication. **BINARY** identifies an observation in supplied software, with the particular artifact named. **INFERENCE** identifies an implementation consequence or comparative hypothesis. **OPEN** means an interface detail is not established; it is not permission to manufacture a successful POST response.

There is **no supplied, authenticated 7690 system-ROM or interface-adapter-ROM dump**. The Model 25 binaries discussed below are comparative evidence, never target firmware. A diagnostic diskette is neither ROM. Addresses `F000:xxxx` are segment:offset; `0xFFFF0` is physical. Port numbers and masks are hexadecimal. Sizes in KiB are powers of 1024. PDF page numbers below are one-based **physical pages of the supplied file**; the scans contain two printed pages per PDF page.

| Source | Relevant evidence |
|---|---|
| [7690 Technical Reference](../IBM_7690_Clinical_Workstation_Technical_Reference.pdf), abbreviated TR | PDF 10–16 / printed 1-2–1-15: machine, CPU, timers, DMA, interrupts; PDF 20–23 / 1-22–1-29: memory, I/O, bus; PDF 109–113 / 6-2–6-11: ROM scanning and BIOS; PDF 132 / 6-48–6-49: descriptor; PDF 137–142 / 6-58–6-68: bootstrap, time, BDA, ROM tables |
| [Guide to Operations](../IBM_7690_Clinical_Workstation_Guide_to_Operations.pdf), abbreviated Operations | PDF 15 / printed 1-10–1-11: memory count, approximately 45-second POST, diagnostic boot; PDF 25 / 3-2–3-3: error/beep behavior; PDF 27 / 3-6–3-7: fault classes |
| [Searchable TR](../DOCUMENTATION/OCR/TECHREF.txt) | Lines 405–707, 942–1097, 5688–5918, 7040–7324; **locator only where numbers disagree with images** |
| [CPU0.DGS](../7690diag/CPU0.DGS) | Actual diagnostic instructions, zero-based file offsets; SHA-256 `8d8943a0fb9bdd6cbd7bb8733387796f3057e1a608a51766927faaf105cabac1` |
| [Platform evidence ledger](../ANALYSIS/platform-evidence.json) | Source hashes, exact byte windows and disassembly for the observations in this chapter; Model 25 source chain and identity are explained in MODEL25.md |

The TR memory, DMA, `61`, `62`, `65`, `6B`, I/O, and descriptor tables were read from rendered page images. Two consequential OCR errors are **`68` for `6B`** on printed 1-22 and **`0080–00BF` for `0080–008F`** on printed 1-24. Neither is a hardware alternate decode.

## 1. Architecture and clocks

**DOCUMENTED — TR PDF 10–12, printed 1-3–1-7.** The CPU is an Intel **8086-2 at 8 MHz**, with a 16-bit external data bus and 20-bit address space. Five planar gate arrays provide two CPU-support functions, two video-support functions, and one diskette-support function. The system-support array is a bus master for DMA and refresh, requesting the CPU's bus through its request/grant line. The I/O-support array contains the integrated interrupt controller and keyboard-related logic; substituting an AT 8042 plus a cascaded pair of 8259s is wrong.

| Transaction or clock | Target contract |
|---|---|
| Local system RAM/ROM | 16-bit transfers, four 125-ns CPU clocks, nominal 500 ns, no wait states |
| Normal I/O | 8-bit transfers, eight 125-ns CPU clocks including four waits, nominal 1 microsecond |
| CPU word I/O | Converted to successive byte transactions; do not treat a word OUT as one indivisible 16-bit device write |
| DMA | 8-bit only, 4-MHz controller, six 250-ns DMA clocks, nominal 1.5 microseconds per transfer |
| Additional waits | `I/O CH RDY` can extend transactions; the channel description permits one added wait for each clock held not ready and says not to hold it inactive longer than 17 clocks |
| Refresh | Generated in the system-support array, not by programming PIT channel 1 as an XT refresh generator; memory requires refresh within 4 ms, and a refresh bus operation takes nine 125-ns clocks |
| CPU clock source | 48 MHz divided to 8 MHz, 33% duty cycle; the same generator provides a nominal 1.84-MHz serial clock |
| Channel `OSC` | 14.31818 MHz, 70-ns period, 50% duty cycle, distinct from the 8-MHz CPU/channel `CLK` |
| PIT channels 0 and 2 | Hardware section rounds to 1.19 MHz; BIOS timer definition gives 1,193,180 Hz |

Timing sources: TR PDF 11–12 / 1-5–1-7, PDF 15 / 1-13, PDF 20–22 / 1-23–1-27, PDF 113 / 6-10. The 4-ms requirement is a **row-retention requirement**, not an instruction to stall the CPU once every 4 ms. The manual does not establish a complete refresh-row schedule; a cycle-accurate implementation needs that schedule rather than a guessed periodic burst.

**INFERENCE — emulator execution model.** Use an 8086 CPU core, including the real-mode 20-bit physical-address wrap and pre-286 instruction/flag behavior. Start from architectural reset at physical `0xFFFF0`; do not start at INT 19h or construct a BDA in place of executing POST. DMA, PIT, serial clocks, and the drive's rotation must progress on machine time, not according to host UI frame count. I/O-ready waits and bus ownership matter during polling loops. A guest word write across an I/O boundary must reach both byte-addressed devices in the proper order.

The gate array's request/grant protocol matters to a physical in-circuit emulator: TR PDF 112 / printed 6-8 explicitly warns that loss of synchronization can damage the array. This is an electrical warning, not evidence that software emulation needs a host thread per bus master.

## 2. Physical memory and ROM mapping

**DOCUMENTED — TR Figure 1-2, PDF 11 / printed 1-5; memory construction PDF 20 / printed 1-22.**

| Physical addresses | Owner and restrictions |
|---|---|
| `00000–9FFFF` | 640 KiB installed planar read/write memory, parity checked |
| `A0000–BFFFF` | Video aperture; this does not mean 128 KiB independent video RAM. The planar has 64 KiB video memory; see VIDEO.md |
| `C0000–C3FFF` | 16-KiB **7690 interface-adapter POST and BIOS** ROM |
| `C4000–EFFFF` | Not assigned a built-in device by Figure 1-2; part of the adapter-ROM search space, not additional conventional RAM |
| `F0000–FFFFF` | 64-KiB system ROM containing POST, BIOS, graphics character patterns, and bootstrap |

The first 128 KiB is socketed, using four 64K-by-4 data devices and two 64K-by-1 parity devices. The upper 512 KiB is two banks of 256K-by-9 SIPs. The **7690 is documented with 640 KiB standard**, unlike the original 512-KiB Model 25 configuration. A machine-config selector which accidentally defaults to 512 KiB because the base class is called “Model25” is not faithful to the stated 7690 configuration.

The system ROM uses two 32K-by-8 devices in 28-pin sockets. The 16-bit local bus and Model 25 binary source chain support even/odd-lane construction; the 7690 manual's statement “64K by 8-bits” is an aggregate capacity description, not proof of a different chip ordering. **OPEN:** actual 7690 chip part numbers, lane labels, ROM dates, hashes, and firmware revisions. Do not rename Model 25 chip files as 7690 ROMs. An eventual capture must retain both original chips and the derivation of the combined image.

Absent memory must not become a writable backing array merely because the emulator allocated a 1-MiB host buffer. Reserved apertures must not alias RAM unless hardware evidence requires it. **OPEN:** undriven-bus values and partial-decode mirrors are not specified by these tables.

### `6B`: planar RAM control/status

The address is **`006B`**, image-confirmed in the prose on TR PDF 20 / printed 1-22, Figure 1-11. It is not `68`; `68` belongs to the proprietary keyboard/pointing interface in the comparative Model 25 evidence.

| Bit | Meaning |
|---:|---|
| 7 | Parity-check pointer: `1` lower 128-KiB bank failed; `0` upper 512-KiB bank failed |
| 6 | Active-low enable for `90000–9FFFF` |
| 5 | Active-low enable for `80000–8FFFF` |
| 4 | Active-low enable for `70000–7FFFF` |
| 3 | Active-low enable for `60000–6FFFF` |
| 2 | Active-low enable for `50000–5FFFF` |
| 1 | Active-low enable for `40000–4FFFF` |
| 0 | Remap low memory |

POST uses this facility to resolve contention with channel memory and to work around a failed first 128 KiB. Bit 7 is **status ownership**, not another RAM-enable latch. Keep parity-source/bank state separate from the writable mapping controls. **OPEN:** the TR names the remap action but does not give the exact address permutation, all readback semantics, or power-up values. In particular, do not turn bit 0 into an arbitrary “subtract 128 KiB from every address” rule without tracing the actual memory tests and bank decode.

**BINARY — comparative Model 25:** reset code clears `6B` at `F000:01D7`; its failure path reads `6B`, ORs bit 0, and writes it at `0201–0205` before retrying low-memory tests. This corroborates the control's existence but does not prove the 7690's complete remap wiring. See MODEL25.md for the ROM identity.

## 3. Complete published I/O allocation

**DOCUMENTED — TR Figure 1-12, PDF 21 / printed 1-24.** This table distinguishes an allocated aperture from individually proven aliases.

| I/O address range | Device |
|---|---|
| `0000–001F` | 8237A-5 DMA controller |
| `0020–003F` | Interrupt controller in the I/O-support gate array |
| `0040–005F` | System timer; normal counter/control addresses `40–43` |
| `0060–0062` | Planar I/O ports |
| `0063–006F` | Planar control/status extensions |
| `0080–008F` | DMA page-register aperture |
| `00A0–00AF` | Interrupt-controller extension, including NMI enable at `A0` |
| `0378–037F` | Parallel port |
| `03C0–03DF` | MCGA video subsystem |
| `03F0–03F7` | Diskette gate array and controller |
| `03F8–03FF` | Serial port |
| `F300–F303` | Interface-adapter touch/power registers; see TOUCH.md |
| `F304–F305` | Interface-adapter LCD controller; see VIDEO.md |

`0000–00FF` is reserved for planar I/O. Other addresses are available to channel adapters except for assigned functions. All **16 I/O address bits** should be decoded by an adapter (TR PDF 22 / printed 1-26); aliasing `F300` to `0300` loses the 7690 hardware.

**Not part of this target map:** AT CMOS at `70/71`, AT second PIC at `A0/A1`, AT DMA controllers at `C0–DE`, MCA POS registers, or a built-in fixed-disk register group at `320–32F`. In particular, `A0` is not the second PIC's command register. A port outside the table can still be present on an optional adapter; “not built in” is not “forbidden for all configurations.”

### `65`: on-planar chip-select routing

**DOCUMENTED — TR PDF 13 / printed 1-8, Figure 1-3; read/write.**

| Bit | Meaning at `65` |
|---:|---|
| 7 | Parallel output-driver enable |
| 6–5 | Reserved, zero |
| 4 | Serial chip select |
| 3 | Diskette chip select |
| 2 | Video chip select |
| 1 | Parallel chip select |
| 0 | Reserved, zero — **not** the baseline Model 25 fixed-disk chip select |

For a function bit set to one, the planar consumes that function's I/O cycles and blocks the channel read/write strobes. With the bit clear, the planar no longer selects the device and those transactions reach the channel. **INFERENCE:** implement this as routing/selection, not as merely a remembered byte. A disabled built-in UART must not continue answering while a channel UART also answers. Keep bit 7's output-driver effect distinct from bit 1's register-select effect. The TR does not publish a reset value; firmware initialization and externally supplied power/reset state must not be confused.

### `60`, `61`, `62`: data latch, controls, and inputs

**DOCUMENTED — TR PDF 13–15 / printed 1-9–1-12, Figures 1-5/1-6.** `60` is the interface's BIOS keystroke byte location; the comparative ROM explicitly writes received bytes there before invoking the standard handler. It is not sufficient to instantiate an AT data/status pair at `60/64`.

| Bit | `61`, read/write control | `62`, read-only input/status |
|---:|---|---|
| 7 | Reserved zero | RAM parity error occurred |
| 6 | Reserved zero | I/O-channel check active |
| 5 | `1` disables I/O-channel-check NMI; `0` enables | Actual PIT channel-2 OUT |
| 4 | `1` disables planar RAM-parity NMI; `0` enables | Reserved |
| 3–2 | Reserved zero | Reserved — bit 2 is **not** a fixed-disk presence input in the 7690 table |
| 1 | Speaker/beeper data gate: `1` passes timer 2, `0` forces output zero | Math coprocessor installed |
| 0 | PIT channel-2 gate | Reserved |

The port `62` value is derived from input state; it is not a mirror of `61`. Muting audio through `61.1` does not freeze the timer output reported at `62.5`. Changing an NMI gate must not erase unrelated error evidence. **BINARY — CPU0.DGS:** file `01AE–01B6` and `0215–021D` set then clear `61` bits `30` around NMI tests. This establishes the pulse sequence expected by supplied software; the publication alone does not fully specify the parity/check latch-clear circuit.

### `63–6A`: extend the planar, not the AT keyboard controller

The primary TR's detailed register map is incomplete here. Preserve the following distinction between direct target software observations and comparative interpretation:

| Port | Established use and limit |
|---|---|
| `63`, read | CPU0 tests PIC state, including normal vector base in bits 7–3; Model 25 BIOS reads `63 & F8` and adds one before dispatching the keyboard vector |
| `63`, write | Diagnostic stimulus under `69` control: NMI and IRQ request injection demonstrated by CPU0; not a generic storage latch |
| `64` | Inside reserved planar-control aperture. No complete target decode established. **Do not assign AT keyboard status/command semantics** |
| `66` | Proprietary keyboard/pointing control/status, detailed in KEYBOARD.md with comparative provenance |
| `67`, `68` | Proprietary serial-interface byte buffers in comparative evidence; not RAM control |
| `69` | Target CPU0 uses bits 2, 6, 7 as additional NMI/diagnostic controls; keyboard transmit-related bits are separately owned by KEYBOARD.md |
| `6A` | Proprietary interface status in comparative evidence; density-related interpretation is not a complete documented 7690 bitfield |

**BINARY — exact CPU0 diagnostic protocol, not a guessed reset table:**

**Reachability prerequisite:** the PIC/DMA routines below are not the diagnostic's first tests. CPU0's normal path first passes ROM/NMI and then the clock tests at file `025B–057D`. Carry-set returns from INT 1Ah/AH=04 or AH=02 go to the common error path, not a no-RTC skip. A no-RTC BIOS cannot run the normal module through to the later PIT/PIC/DMA tests. Section 10 gives the direct clock evidence; a targeted harness entering a later routine would be a separate experiment, not a complete CPU0 pass.

1. File `0763–0791`: write `13` to `20`; set `69.6`; read `63` and require bit `08` clear; write `08` to `21`; clear `69.6`; read `63 & F8`, require `08`.
2. File `0795–07A9`: write `01` to `21`; set `69.6`; read `63 & 04`, require zero. This is a diagnostic view of initialization state, not evidence that normal port-63 reads always return a fixed `08`.
3. File `07AE–07E0`: reinitialize the PIC, install handlers for vectors `08–0F`, mask bits `03` at `21`, set `69.7`, and clear `63`.
4. File `07E6–07FB`: write request masks `80`, `40`, `20`, `10`, `08`, `04` to `63`, allowing interrupts and checking the recorded in-service bit. IRQ0 and IRQ1 are masked in this test; it does **not** prove that a synthetic IRQ1 bypasses or uses the normal proprietary `71` dispatch.
5. Handler at file `0B24–0B49` reads ISR using `OUT 20,0B` then `IN 20`, reads IRR using `OUT 20,0A` then `IN 20`, stores both, clears `63`, and writes nonspecific EOI `20` to `20`.
6. Cleanup at `0800–0830` clears `63`, clears `69` bits `C0`, restores the vector table, PIC state, and saved `A1` byte.
7. The separate NMI test, file `01AE–01F7`, pulses `61.5/.4`, sets `69 |= 84`, replaces vector `02`, then writes `01` to `63` and waits for the NMI handler's marker. It later clears `63` and `69` bits `84`.

**INFERENCE:** these observations support a diagnostic-stimulus register and alternate diagnostic read view, not seven independent arbitrary “pass test” values. Store one coherent PIC request/in-service model and derive the observed views from it. **OPEN:** exact silicon behavior of every bit, diagnostic stimulus priority for simultaneous writes, all initialization-state readback bits, and reserved-bit read values. Implementing only the exercised sequences can be a research model, but must not be described as a complete gate-array reconstruction.

## 4. Interrupt controller, vector 71, and NMI

### Maskable interrupts

**DOCUMENTED — TR PDF 15–16 / printed 1-13–1-14.** One eight-level interrupt controller is integrated into the gate array; IRQ0 is highest priority. The assigned sources are:

| IRQ | Planar owner | Channel availability |
|---:|---|---|
| 0 | PIT channel 0 | Not available |
| 1 | Keyboard and pointing device, proprietary entry vector `71` | Not available |
| 2 | Video | Available when its planar function does not own it |
| 3 | Not used | Available |
| 4 | Serial port | Available subject to planar selection |
| 5 | Not used | Available — not automatically a fixed disk |
| 6 | Diskette | Available subject to planar selection |
| 7 | Parallel | Available subject to planar selection |

BIOS does not use video IRQ2 or parallel IRQ7 in its ordinary routines. This is different from deleting those lines. Expansion devices may use them.

**BINARY — initialization compatibility.** CPU0 file `073E–0748` writes `13` to `20`, then `08` and `01` to `21`, corresponding to a single-controller initialization with a normal vector base of `08`. The comparative Model 25 POST at `F000:0195–01A3` instead writes `13`, `08`, `09`; both are observable inputs an implementation may encounter. Do not require a cascade ICW3 and consume the next mask byte as configuration. The target diagnostic proves mask reads/writes, IRR/ISR selection with `0A/0B`, and EOI `20`; it does not fully specify every 8259 operational mode or every address alias in `20–3F`.

The TR's BIOS introduction, PDF 109 / printed 6-3, gives the conventional “IRQ1 corresponds to vector 9” rule. The hardware chapter explicitly gives **INT 71h**. These are not two physical IRQ1 sources: the Model 25 firmware explains the layering. **BINARY — comparative Model 25 `F000:E68C–E6A6`:** write the received byte to `60`, read the programmed base from `63`, mask with `F8`, add one, multiply by four, and fetch a far vector from the IVT. The gate-array hardware entry is `71`; the normal keyboard handler remains the programmed base plus one. Pointing input is dispatched separately; see KEYBOARD.md.

**INFERENCE:** normal IRQ0 and IRQ2–7 should follow the programmed PIC base, while the integrated IRQ1 entry requires the proprietary dispatch mechanism. Revectoring `09` alone must not silently break the actual `71` entry. Save/restore must retain masks, pending requests, ISR state, priority configuration, normal base, proprietary source state, and diagnostic view controls. A mouse byte must not be delivered as a scan code merely because both use IRQ1.

### External interrupt sharing

**DOCUMENTED — TR PDF 16–19 / printed 1-14–1-21.** Integrated adapters do not use IBM's optional external shared-IRQ protocol. Shared adapters let a line float high and pulse it low; the leading edge arms the controller and the trailing edge causes the interrupt. Other adapters on that level disarm until Global Rearm. A handler checks its device, services it, disables interrupts, writes `02Fx` for IRQ level `x=2..7`, sends EOI, and returns. A still-active adapter must reissue after rearm, preventing simultaneous sources from being lost.

The software chain starts with a short jump around a fixed structure holding a far forward pointer and signature; last linked is first called. The manual's example uses signature word `424B`, while some extracted prose appears as `4248`; do not copy OCR into executable chain recognition. Chaining details belong to the adapter actually being emulated. Do not rearm all integrated sources on every generic PIC EOI simply because the manual describes this optional bus protocol. For an unsupported external sharing card, state the missing hardware explicitly.

### NMI is not AT CMOS bit 7

**DOCUMENTED — TR PDF 16 / printed 1-14 and PDF 21 / printed 1-24.** Sources are planar parity, I/O-channel check, and coprocessor interrupt. `OUT A0,80` enables NMI; `OUT A0,00` disables it. `61.4` and `61.5` separately mask parity and channel-check sources. `62.7/.6` report error state; `6B.7` identifies the parity bank. CPU0's use of `69.2` and the diagnostic injector is described above; it is an additional implementation prerequisite, not a reason to ignore `A0`.

**INFERENCE:** NMI arbitration must consider source state and gates. Re-enabling NMI is not equivalent to directly calling INT 02h on every write. The actual edge/latch treatment when an error remains asserted is **OPEN** without silicon/ROM tracing. CPU0's `63` stimulus must enter the same architectural NMI path as a real source, including flags/stack/return semantics; do not set the diagnostic's result byte from the emulator.

The BIOS INT 02h description, TR PDF 113 / printed 6-9, searches for bad parity and displays its segment, or four question marks if it cannot locate it. Operations lists `Parity Check 1`, `Parity Check 2`, and `ROM Error` as service failures. A blanket “read-only memory never fails” implementation cannot exercise the error-path contract.

## 5. DMA: byte transfers, page registers, and alias limits

**DOCUMENTED — TR PDF 15 / printed 1-13.** Four 20-bit DMA channels, 8-bit data, 4-MHz 8237-compatible controller. Channel 0 is unavailable externally; channel 2 is diskette; channels 1 and 3 have no built-in assignment. Refresh is independently generated by the support array, so an XT rule consuming DMA channel 0 for periodic PIT-1 refresh is not the documented wiring.

The ordinary 8237 programming surface used by supplied CPU0 and comparative ROM includes address/count pairs `00/01`, `02/03`, `04/05`, `06/07`; command at write `08`; mask control at `0A`; mode at `0B`; byte-pointer clear at `0C`; master clear at `0D`. CPU0 file `0847–087F` clears the controller and checks low/high byte readback at all eight address/count registers with changing patterns; file `0885–0895` restores command/mode state. The Model 25 diskette path at `F000:4B18–4B75` clears the shared byte pointer, writes mode, programs channel-2 address and count low byte then high byte, and unmasks channel 2.

**INFERENCE — compatible 8237 state ownership.** Keep base/current address and count, transfer direction and mode, channel masks/requests, the shared first/last-byte flip-flop, terminal-count state, and four high-address page latches. A count written as `n-1` transfers `n` bytes; the comparative ROM decrements the computed transfer length at `4B62` before writing `05`. DMA writes memory through the current mapping and parity-generation path; it must not bypass the board's RAM enables. Terminal count is an event seen by the FDC, not just a way to stop a host `memcpy`.

### The printed shifted page map is a real contradiction

| Channel | 7690 TR Figure 1-8, image-confirmed | Model 25 TR PDF 26 / printed 1-13 and comparative ROM |
|---:|---:|---:|
| 2 | `80` | `81` |
| 3 | `81` | `82` |
| 1 | `82` | `83` |
| 0 | `87` | `87` |

**BINARY — target diagnostic:** CPU0 file `0AE8–0B23` writes/reads `87`, `83`, `81`, `82` and checks the **low nibble**. This is direct evidence that supplied software expects those addresses to be readable and writable. However, it writes the same value to all four before reading: it does **not** by itself prove that they are independent or which DRQ consumes each latch. The comparative Model 25 diskette code at `F000:4B49–4B4B` masks the page to four bits and writes **`81` for channel 2**. A machine which uses the printed shifted map cannot execute that path correctly with a buffer above the first 64 KiB.

**INFERENCE, recommended research configuration:** use the Model 25 `81/82/83/87` map provisionally, label it inherited, and retain the 7690 documentation discrepancy. Do not implement `80` and `81` as simultaneous channel-2 aliases merely to make both tables appear true: `81` has incompatible channel assignments in the two alternatives. Do not call an emulator-only Model 25 DMA probe a physical 7690 measurement.

**OPEN — read/write aliases:** the published apertures `00–1F` and `80–8F` are not complete alias truth tables. The sources here do not establish whether every `10–1F` access mirrors `00–0F`, which unused page addresses are storage latches, or whether read and write aliases differ. Port `80` is particularly unsafe to treat as a harmless POST delay/checkpoint sink. Preserve direction-specific dispatch and investigate unassigned addresses with independently tagged channel transfers when real target firmware/hardware becomes available. This handbook does not invent an alias mask.

For a 20-bit channel, the compatible address is `(page_low_nibble << 16) | current_address`; the 16-bit address counter does not carry into an external page latch. The BIOS reports boundary violations as `09`; the comparative ROM tests address-plus-count carry at `4B6F–4B77`. Hardware must still model the counter wrap if software programs a crossing transfer directly; do not silently make DMA linear across the page. Detailed diskette transactions are in STORAGE.md.

## 6. PIT and refresh diagnostic timing

**DOCUMENTED — TR PDF 13–15 / printed 1-9–1-12.** The system timer is an 8253 or equivalent. `40`, `41`, `42` select counters 0–2 and `43` programs the mode. Counter latching is supported without stopping counting. IBM recommends a second read where a count is critical.

| Channel | GATE | CLOCK | OUT |
|---|---|---|---|
| 0 | Tied high | 1.19-MHz oscillator | IRQ0 |
| 1 | Tied high | **`-RAS_SIP` from the system-support gate array** | Not connected |
| 2 | `61.0` | 1.19-MHz oscillator | Beeper path, observable through `62.5` |

Channel 1 is explicitly for **internal diagnostic tests**. The common shorthand “PIT1 refresh” reverses causality here: refresh/RAM strobes feed the counter, rather than PIT1 OUT initiating refresh. A freely running 1.193-MHz channel 1 is not a harmless approximation for a diagnostic which counts RAM activity. **OPEN:** the exact set of reads, writes, refresh cycles, and bank strobes contributing `-RAS_SIP` edges requires fuller electrical evidence.

The standard 8253 counter core can be reused for mode behavior and low/high-byte sequencing; the board supplies the different clocks and gates. Do not add 8254-only read-back commands merely because a generic PIT core has them. Keep latched count snapshots and byte-read position distinct from the live counter. `61.1` gates output to the beeper after timer generation; it is not PIT GATE2. Mode-specific gate behavior belongs to the timer core even though the TR summarizes clearing GATE2 as halting the timer.

**DOCUMENTED — TR PDF 113 / printed 6-10.** BIOS programs a 65,536 divisor against 1,193,180 Hz, giving approximately 18.2 ticks/s. INT 08h increments BDA `40:6C`, manages overflow and the day counter, decrements `40:40`, turns off diskette motors when that counter expires, and invokes INT 1Ch. The time-of-day implementation is therefore also a floppy motor-control dependency. A PIC mask preventing IRQ0 must stop BIOS tick advancement, even though the PIT itself keeps counting.

## 7. Reset and POST: established phases versus missing code

**DOCUMENTED — TR PDF 12 / printed 1-7:** the clock generator produces reset after sensing power good. The channel RESET DRV signal also initializes logic on power-up or low line voltage and is synchronized to CLK's falling edge (PDF 23 / printed 1-28). A short AC failure supported by the ride-through battery is not automatically a CPU reset; see PERIPHERALS.md.

Operations PDF 15 / printed 1-10 describes a visible memory count at the upper-left of the LCD, approximately **45 seconds** of POST, then **one beep**. This is operator guidance, not a published cycle-count trace. After POST, the diagnostic diskette loads and displays its logo/menu; a menu drawn by the disk must not be mistaken for ROM output.

Operations PDF 25 / printed 3-2 distinguishes:

- Successful POST: one beep.
- Detected faults: two or three beeps plus the failing test number.
- Noncritical fault: `RESUME = "F1" KEY`, allowing reduced operation.
- Critical fault: error display and halt.
- Three beeps specifically warn of a critical display or keyboard error requiring service.

Operations PDF 27 / printed 3-6–3-7 gives `1XX` system-board, `2XX` memory, `3XX` keyboard, `5XX` display, `6XX` diskette, and `90XX` interface-adapter fault families. `205` can allow reduced-memory continuation with F1; `199` concerns the installed-device list. These are user-visible contracts, not a complete mapping from every low-level failed bit to a numeric code. Do not suppress the fault or inject F1 automatically to obtain a boot screen.

### Reset flags and low-memory ownership

**DOCUMENTED — TR PDF 113 / printed 6-11 and PDF 139 / 6-63.** Ctrl-Alt-Delete stores `1234` at BDA word `40:72` and jumps to POST, which skips the memory retest. It does not authorize skipping all controller initialization or the interface-adapter path. Memory `00300–003FF` is used as a stack during power-on initialization and bootstrap (TR PDF 111 / printed 6-6). These are firmware-owned locations, not an emulator's permission to preinitialize them before reset.

**BINARY — comparative Model 25:** its reset tail is `EA 5B E0 00 F0`, a far jump to `F000:E05B`, whose near jump wraps within the segment to `008D`. Early instructions perform CPU flag/register tests before establishing a normal RAM stack. At `0100–0111`, SS points to ROM and SP points at a ROM return word; checksum code at `12AA–12B5` traverses 65,536 bytes through 16-bit wrap and returns flags. DMA and PIC tests follow before low-memory remapping. These are useful CPU-core failure probes, but their offsets, exact checkpoints at `90/378`, error order, and reset constants must not be presented as authentic 7690 POST behavior.

**OPEN:** actual 7690 reset vector, early stack strategy, system-ROM checksums, POST dispatch/order, manufacturing codes, controller reset defaults, delay-loop timing, and the division of responsibility between planar and interface-adapter POST. Acquiring both ROM regions is the missing prerequisite for a faithful cold-boot trace, not a reason to emulate only DOS calls.

## 8. Adapter ROM installation and the C000 boundary

**DOCUMENTED — TR PDF 112–113 / printed 6-8–6-9:** after default BIOS vectors are established, POST scans for adapter ROMs in **2-KiB increments**. `C0000–C7FFF` is scanned **before video initialization**; `C8000–EFFFF` near the end of POST. A recognized module has:

| Relative byte | Meaning |
|---:|---|
| 0 | `55` |
| 1 | `AA` |
| 2 | Length in 512-byte units |
| 3 | Executable initialization entry, called with a far CALL |

Sum every byte in the declared length modulo 256; zero is required. Initialization installs/intercepts vectors and must return with RETF. The documented 7690 interface-adapter ROM occupies `C0000–C3FFF`, so it is on the **early** search path. A 16-KiB module covering the whole region would encode length `20`; that is an arithmetic implication, **not an observed target header**.

**INFERENCE:** install the actual adapter ROM as a ROM bus device and execute its entry; do not implement its functionality by modifying an unrelated VGA BIOS. The ROM handles LCD, touch, and bar-code feature POST/BIOS (TR PDF 20 / 1-22). The system-board video logic senses no normal monitor, and the adapter's POST supplies correct initialization (TR printed 1-37). Consequently a Model 25 ROM with an empty C000 window is not a convincing 7690 cold-boot test, even if a synthetic framebuffer displays text.

**OPEN:** the actual adapter header, whether its entire 16 KiB participates in the header checksum, revision information, vector hooks, exact boot-time callbacks, and any density/identity overrides. “Probably implemented in the adapter ROM” is a research hypothesis for the documented differences, not an established implementation fact.

## 9. BIOS data and service contracts

**DOCUMENTED — TR PDF 138–141 / printed 6-60–6-67.** BIOS uses `00400–004FF`; POST carves the highest possible **1 KiB below 640 KiB** for the EBDA, stores its segment at `40:0E`, and writes its size in KiB at EBDA offset zero. INT 12h returns contiguous usable KiB **excluding the EBDA**: an all-good 640-KiB machine reports **639**, not 640 (TR PDF 124 / printed 6-32).

| BDA offset in segment `0040` | Size | Owner / consumer |
|---|---:|---|
| `00,02,04,06` | Word each | COM1–COM4 addresses found by POST |
| `08,0A,0C` | Word each | LPT1–LPT3 addresses |
| `0E` | Word | EBDA segment, also returned by INT 15h/AH=C1h |
| `10` | Word | Equipment flags / INT 11h |
| `13` | Word | Contiguous usable memory in KiB / INT 12h |
| `16` | Byte | BIOS control flags; no complete target bitfield published here |
| `17–3D` | Mixed | Keyboard flags, ring-buffer pointers/data; KEYBOARD.md |
| `3E` | Byte | Disk recalibration state and working IRQ-completion bit |
| `3F` | Byte | Diskette motor/write state |
| `40` | Byte | Motor-off tick counter |
| `41` | Byte | Last diskette BIOS status |
| `42–48` | Seven bytes | FDC result packet |
| `49–66` | Mixed | Video mode, dimensions, page/cursor, ports/palette; VIDEO.md |
| `6C` | Dword | System tick count, low word first |
| `70` | Byte | Timer overflow indication |
| `71` | Byte | Ctrl-Break flag, bit 7 |
| `72` | Word | Warm reset/memory-test-complete flag (`1234`) |
| `78–7A` | Byte each | Printer timeout values |
| `7C–7F` | Byte each | Serial timeout values |
| `80,82` | Word each | Keyboard buffer start/end offsets |
| `84–8A` | Mixed | Extended display information, including 7690 LCD reverse-video bit at `89.5` |
| `8B` | Byte | Last diskette data/step-rate selection |
| `90,91` | Byte each | Drive media state |
| `94,95` | Byte each | Drive current seek-track cache |
| `96,97` | Byte each | Extended keyboard type/LED flags |
| `98` | Dword | User wait-flag pointer |
| `9C` | Dword | User timeout in microseconds |
| `A8` | Dword | Alternate video parameter table pointer |
| `CE` | Word | Day counter |
| `F0–FF` | 16 bytes | Reserved for user/inter-application use |

Do not infer that an emulator should maintain these fields independently of executing ROM. They are **guest RAM maintained by firmware**; device state and BDA cache can temporarily disagree while an interrupt is pending. On a documented all-good machine the EBDA segment is arithmetically `9FC0`, but program code should use `40:0E`, not hard-code it. Lower usable memory moves the EBDA.

The EBDA has pointing-interface state at offsets `22–2F`: far callback at `22/24`, flags at `26/27`, and reserved data thereafter. The remainder is not free heap. Preserve unknown bytes on save/restore and do not overwrite the EBDA with a touch driver's private allocation.

The equipment word uses bits 15–14 for printer count, 11–9 for serial-port count, 7–6 for diskette-drive count minus one **when bit 0 is set**, 5–4 for initial video mode, bit 2 for pointing-device presence, bit 1 for coprocessor, and bit 0 for IPL diskette installed. Bits 13–12, 8, and 3 are reserved (TR PDF 123 / printed 6-31). Enumerating a disk image is not enough to set this correctly: POST sees drive/controller behavior.

### Vectors and preservation

The usual IVT formula is `4 * vector`, with an offset word followed by a segment word. BIOS entry points include INT `10` video, `11` equipment, `12` memory, `13` diskette, `14` serial, `15` system services, `16` keyboard, `17` printer, `18` ROM BASIC, `19` bootstrap, and `1A` time. Special data/callback vectors include `1B` Ctrl-Break, `1C` timer tick, `1D` legacy video parameters, `1E` diskette parameters, `1F` extended graphics characters, `40` saved/revectored diskette interface, and `43` graphics-character table (TR PDF 110–111 / printed 6-4–6-7).

At power-on, `1B` and `1C` point to IRET routines; `1F` is initialized to `0000:0000`. Never treat every IVT entry as an executable ISR: `1E` points to data. BIOS generally preserves registers other than AX and flags unless a function returns a value in another register; honor the individual function contract. Reserved functions often return carry set rather than an invented success value.

## 10. Clock contradiction: no-RTC publication versus software prerequisites

**DOCUMENTED — TR PDF 132 / printed 6-49, image checked.** INT 15h/AH=C0h returns ES:BX pointing at a ROM descriptor, carry clear and AH=0. The descriptor starts with a length word (minimum eight bytes), then model, submodel, BIOS revision, and feature bytes. Listed feature-byte-1 bits are:

- bit 7 = 1: BIOS uses DMA channel 3;
- bit 6 = 0: one interrupt controller;
- bit 5 = 0: **no real-time clock**;
- bit 4 = 1: INT 15h keyboard escape hook;
- bit 2 = 1: EBDA allocated.

The DMA3 statement does not match the hardware chapter's “DRQ3 not used” assignment; it may describe inherited BIOS capability rather than a populated target fixed disk. The publication does not define all feature bits, so do not fabricate a full descriptor by filling unspecified bits with assumptions. TR PDF 142 / printed 6-68 explicitly states **model FA and submodel 00**, unlike the supplied Model 25's submodel 01. The 7690's actual descriptor bytes and revision remain OPEN.

**DOCUMENTED — TR PDF 137 / printed 6-59.** INT 1Ah/AH=00 reads the tick counter into CX:DX and reports/clears the overflow flag in AL; AH=01 sets CX:DX and clears overflow. AH=0A reads the day counter into CX (days since 1980-01-01); AH=0B sets it. AH=0C–FF are reserved, carry set. The page does **not** document AT-style hardware-clock read/set/alarm functions `02–09`; do not create an AT CMOS clock to fill the gap. BDA `40:CE` and the PIT tick are software-maintained date/time, not evidence for a battery RTC.

**Contradiction retained:** Operations PDF 15 / printed 1-11 says a battery keeps the internal clock running continuously; PDF 16 / printed 1-12 continues the set-time/date guidance; PDF 27 / printed 3-6 says a recurring `161` date/time error merits service. The system's ride-through battery does keep the running processor alive temporarily, but that does not by itself explain persistent clock operation while switched off. The supplied publications do not locate an RTC device or its register decode on the 7690. A no-RTC planar is documented; an always-running clock is also asserted in the operator guide.

**BINARY — substantive target-software evidence:** the supplied CPU0 normal path at file `025B–0285` calls INT 1Ah/AH=04 (date) and AH=02 (time), and carry-set failures branch to `04BE`, which loads AL=`3D` then jumps from `04C0` to common error path `08EC`. This is **not an optional-clock skip**. The success path tests RTC/RAM and alarm behavior before reaching PIT at `0580`: RAM ports `E8–EF` are exercised at `036A–03A8`; INT 70h is hooked at `03AA–03C6`; `B1=02` is written and polled at `03D0–03E0`; INT 4Ah is hooked at `041A–0431`; BIOS alarm AH=06 is invoked at `044F–0451`; a private wait at `0453–0460` expects its completion marker. Missing events lead through cleanup back to `04BE`. Successful cleanup/restoration runs from `04C3` through `057D`. The full block manipulates `B0–B5` and `E0–EF`, not AT CMOS `70/71`.

**INFERENCE / OPEN:** this directly establishes a clock-service and register-level requirement of the supplied diagnostic, stronger than a mere save/restore of an unused register. It conflicts with the TR's no-RTC descriptor and omitted AH=02–09 interfaces. To exercise the complete diagnostic normally, a research configuration needs working compatible clock/RAM/alarm behavior; returning CF for an absent clock cannot lead to a full pass. Do not fake successful INT 1Ah returns or jump past the test. The actual target chip/population, alarm routing, firmware descriptor, and source of the contradictory TR text still require authentic ROM/board evidence. Model 30 clock behavior is a justified comparative implementation lead here, **not silent inheritance based only on the model name**.

The comparative Model 25 ROM even contains *two* descriptors selected after probing `EA/EB/EC`; one reports no RTC and one RTC-present. MODEL25.md explains why a raw ROM byte-pattern search is not enough to identify the active descriptor. This makes the clock question more important, not less.

## 11. Bootstrap handoff

**DOCUMENTED — TR PDF 137 / printed 6-58.** INT 19h reads track 0, sector 1 to **`0000:7C00`** and transfers control with `CS=0000`, `IP=7C00`, and `DL` identifying the boot drive. A hardware error transfers to ROM BASIC. The page does not promise DS, ES, SS, SP, IF, or the contents of other general registers; callers must not depend on invented values. INT 19h is a bootstrap service, not a hardware reset.

**OPEN:** target drive-selection/retry order, exact boot-sector admissibility check, non-system-disk UI, and whether the adapter ROM modifies the path. Do not impose a `55 AA` boot-sector signature requirement merely because this is common in later BIOSes.

**BINARY — comparative Model 25:** its `E6F2` stub reaches `4EE8`; the routine clears 512 bytes at `7C00`, resets/reads drive 0, and can try `DL=80` after failure. At `4FA8–4FBC` it reads the first word of the sector, rejects zero, then uses `REPNE SCASW` to reject a match among the following ten words; it does **not** test the final `55 AA`. Success at `4FC6` far-jumps to `0000:7C00`. This is a peculiar ROM-derived heuristic, not a general definition of bootability or an authenticated 7690 rule. STORAGE.md records the supplied disk's actual signature and geometry independently.

## 12. Downstream acceptance scenarios

These are **future emulator acceptance scenarios**, not claims that this repository has booted an emulator.

1. **Authentic cold entry:** with independently captured target system and adapter ROMs, record the first reset fetch, early C000 initialization call, memory count, BDA/EBDA creation, one POST beep, and actual disk bootstrap. A synthetic logo is not this proof.
2. **Warm entry:** let guest Ctrl-Alt-Delete establish `40:72=1234`; observe the changed memory-test path while controllers and the adapter still initialize coherently. Directly jumping to a DOS boot sector is not equivalent.
3. **Chip-select cutover:** disable `65.3`, address `3F4`, and confirm the built-in FDC no longer supplies status; enabling it restores decode without secretly modifying a channel adapter's state.
4. **IRQ layering:** program a nondefault normal PIC base, produce keyboard input, and observe hardware entry `71` followed by the selected base-plus-one vector. Simultaneous pointing input must remain distinguishable.
5. **PIC diagnostics:** after satisfying CPU0's preceding ROM/NMI/clock prerequisites, run its synthetic IRQ paths against actual PIC request/ISR state. Request injection must not bypass interrupt masks, EOI, or CPU stack entry; alternate port-63 views must not become constant-success values. Entering a later routine directly is a scoped harness test, not a full CPU0 run.
6. **DMA page attribution:** independently program each page latch with a distinct value and transfer known diskette bytes above 64 KiB, without crossing a boundary. This distinguishes the printed map, inherited map, and accidental aliases. The supplied CPU0 same-value readback test alone cannot.
7. **DMA wrap:** direct controller programming which crosses a 64-KiB page must exercise hardware address wrap, while BIOS INT 13h reports the documented boundary error. The two surfaces are not interchangeable.
8. **PIT1 activity:** count channel-1 edges during known RAM/refresh activity; compare to independent elapsed PIT0 time. A generic timer with the wrong source should fail rather than be patched with diagnostic-specific counts.
9. **Failure visibility:** corrupt a ROM checksum or induce parity in a selected bank and preserve the visible error/beep/halt or reduced-memory continuation. Do not force successful POST after the fault.
10. **Clock boundary:** record the actual target descriptor, supported INT 1Ah functions, power-off persistence, and CPU0's RTC/RAM/alarm outcome once firmware/hardware is available. The no-RTC table, Operations prose, and diagnostic requirement must all remain visible; no one source alone settles the physical implementation.
11. **Battery ride-through:** remove primary power during a disk transfer without resetting the CPU if ride-through remains available; the drive becomes unavailable and later software retries can recover. Keep that separate from actual low-voltage reset.

No formatter, build, linter, test suite, or emulator boot was run for this research chapter. Evidence consists of page-image examination and actual binary extraction/disassembly recorded in the linked ledger. The outstanding ROM and electrical prerequisites above are explicit boundaries, not omitted emulator features hidden behind successful return codes.
