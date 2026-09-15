# IBM 7690 emulator writer's handbook

Audience: whole-machine emulator, hardware-interface, and virtual-device-driver authors working with the **IBM 7690 Clinical Workstation**. The architectural parent is the **8086 IBM PS/2 Model 25**, not the 286 Model 25, an MCA machine, a PC Convertible, or an AT with a touchscreen attached.

The implementation target is coherent machine state that lets **unchanged target firmware and software** execute: planar POST, the clinical interface-adapter BIOS, LCD initialization, keyboard/barcode traffic, disk boot, optical calibration, touch polling, and power-failure behavior. This handbook supplies the documented interfaces, comparative firmware evidence, disassembled target software, executable research fixtures, and acceptance boundaries. It does **not** supply or claim to have executed an authentic 7690 system ROM or interface-adapter ROM; neither was among the supplied artifacts.

The two target books, original loose diagnostics, original mixed disk image and photograph remain unchanged. Selected Model 25 references are retained locally with provenance; the broader `bios8530` corpus remains a comparative research source, not a required checkout merely to read this handbook. See [SOURCES.md](SOURCES.md).

## Read order

1. [BOOT.md](BOOT.md) — CPU and bus timing, physical memory, complete published I/O allocation, planar control, parity/remapping, custom PIC/IRQ1/NMI, DMA, PIT/refresh, reset/POST, ROM discovery, BIOS data, and the clock contradiction.
2. [MODEL25.md](MODEL25.md) — exact inheritance/rejection matrix, two comparative ROM identities, executed-path versus candidate-descriptor distinctions, reset and interrupt integration, and where Model 30 evidence helps without becoming target fact.
3. [VIDEO.md](VIDEO.md) — MCGA framebuffer packing, fonts and staging, complete memory-controller and LCD-index contracts, mode/attribute conversion, LCD geometry and rails, BIOS extensions, and executable diagnostic transactions.
4. [KEYBOARD.md](KEYBOARD.md) — physical 78-key mapping, set-1/set-2 byte sequences, Fn/Num Lock rules, commands and responses, electrical/serial timing, buffering, repeat, custom planar transport, and BIOS interaction.
5. [TOUCH.md](TOUCH.md) — optical selectors, ADC handshake, dark/lit measurements, calibration and substitutions, usable masks, coordinate reduction, active-area transforms, failure behavior, and a circuit-level emulator contract.
6. [DRIVER_ABI.md](DRIVER_ABI.md) — both original LEDTOUCH versions: DOS installation and `POINT` records, exact INT33 dispatch and private extensions, button/counter/cursor behavior, timer callbacks, version defects, and IBM-mouse fallback.
7. [STORAGE.md](STORAGE.md) — diskette gate array, FDC command/execution/result state, DMA/IRQ/TC ownership, mechanics and disk change, HD/DD support, BIOS/EBDA state, diagnostic probes, destructive operations, and genuine printed opcode errors.
8. [PERIPHERALS.md](PERIPHERALS.md) — barcode wand/card-holder path and full command grammar, serial/parallel interfaces, sound/earphone, mains and ride-through battery, LCD/floppy power consequences, and connector/electrical boundaries.
9. [DIAGNOSTICS.md](DIAGNOSTICS.md) — original versus mixed versus derived media, FAT12 and boot chains, reproducible bootable disk construction, SERVICES private environment, DGS loading and test entrypoints, error interpretation, and safe execution.
10. [VERIFICATION.md](VERIFICATION.md) — exactly what was run, original-instruction trace scenarios, real DOS boot/driver/consumer screenshots, reproduction commands, source audits, and what remains unexercised.
11. [SOURCES.md](SOURCES.md) — authority hierarchy, full source identities, physical-PDF/printed-page navigation, comparative provenance, binary offset conventions, and a cross-chapter discrepancy register.
12. [MACHINE-CONTRACT.json](MACHINE-CONTRACT.json) — concise machine-readable integration facts and evidence links. It is intentionally **not** named a ROM contract: target ROM identities are unknown.

## What is established, and at what boundary?

| Evidence / implementation boundary | What it can establish | What it cannot establish |
|---|---|---|
| DOCUMENTED, target primary page | IBM's published register, protocol, timing, connector or BIOS contract | That contradictory text matches a particular board or ROM revision |
| BINARY, target software | Exact operations of preserved diagnostic/driver bytes, with file/version/offset identified | Physical decode, analog timing, undocumented silicon, or all possible software behavior |
| BINARY, comparative ROM | Actual Model 25 instructions and data, tied to an exact image hash | Authentic 7690 ROM identity, C000 extension behavior, or unchanged peripherals |
| EXECUTED, isolated fixture | Original instructions produced recorded results under explicit synthetic ports/BIOS/input state | Full ROM POST, DOS installation unless DOS was actually running, or physical calibration |
| EXECUTED, generic DOS machine | Preserved boot chain, DOS command execution, real SYS loading, real DOS client behavior | An 8086/7690 CPU, LCD, planar, ROM, or complete diagnostic pass |
| Whole-machine emulator | Observable state transitions generated by the unchanged target ROM and real software | Electrical safety, physical pixel aspect, measured color or analog performance |
| Electrical clone | Measured levels, timing, loading, polarity, power and connectors against original hardware | Software completeness merely because the circuit does not fail electrically |
| ABI replacement | The explicitly declared DOS/INT33/BIOS boundary, including errors and awkward version behavior | That the underlying optical circuit or target firmware was exercised |

**INFERENCE** marks a reasoned implementation consequence. **OPEN** marks missing evidence. Do not turn either into a reset value, port alias, ROM byte, or success response because it is convenient for an emulator.

## Minimal target configuration, without phantom hardware

The documented built-in configuration is an 8086-2 at **8 MHz**, **640 KiB parity RAM**, **64 KiB MCGA display memory**, a **640×480 binary LCD**, the clinical interface adapter, infrared touch panel, US 78-key keyboard, serial and parallel ports, and a 3.5-inch drive. Operations explicitly specifies a **1.44-MB-capable drive accepting HD and DD media**; the diagnostic product and supplied image are **720 KiB**. Do not confuse disk-image geometry with installed drive capability.

A first integration configuration can use one drive A with a disposable DD diagnostic image, mains power healthy, keyboard/touch present, no barcode feature, no external expansion cards, and no built-in fixed disk. These are explicit configuration choices; they are not a claim that all installations had the same options. Three expansion slots are available after the integral interface adapter occupies one of the four sockets.

Two firmware regions are required for an authentic machine run:

| Physical region | Documented role | Current evidence |
|---|---|---|
| F0000–FFFFF | 64-KiB planar POST/BIOS/fonts/bootstrap | Target mapping documented; actual 7690 bytes, chip identities, date and hash absent |
| C0000–C3FFF | 16-KiB clinical interface-adapter POST and BIOS | Target mapping and services documented; actual image absent |

The two comparative Model 25 images are not substitutes that become target ROMs after changing a model byte. Target TR identifies model **FA**, submodel **00**; the preserved Model 25 images identify submodel **01**. SERVICES' FA/copyright check is necessary but far weaker than actual compatibility.

**Clock profile must be explicit.** The TR says no RTC, Operations promises a continuously battery-backed clock, and supplied CPU0 requires successful date/time BIOS calls plus RTC/RAM/alarm behavior before PIT/PIC/DMA tests. This is a material three-way conflict, not a reason to add AT CMOS at70/71 or force a successful return. A full-diagnostic research configuration needs a coherent compatible clock path; physical 7690 chip population and exact firmware handling remain OPEN.

## Changes a generic-PC base class must not hide

| Familiar assumption | 7690 consequence |
|---|---|
| PS/2 means 286, VGA, MCA or 8042 | Original 8086 Model 25 architecture; MCGA; custom planar keyboard/PIC extensions; byte-wide expansion channel |
| IRQ1 always dispatches ordinary INT09 | Custom hardware entry **INT71**, software demultiplexing and downstream keyboard/mouse/clock consumers |
| PIT1 output drives refresh | Documented PIT1 clock comes from support-array RAS activity for diagnostics; its output is unused; refresh is independently generated |
| RAM control is port68 | Image-confirmed port **6B**;68 belongs to a different planar interface function |
| A0/A1 are the AT slave PIC | A0 is the documented NMI-enable path; do not install a second PIC |
| Touch returns X/Y packets | Software selects64 optical paths and compares six-bit dark/lit ADC samples |
| Touch and LCD share one control register | F300–F303 are optical/power-sense interface; LCD is F304 index/F305 data; LCD power/backlight is **index0D**, not F302 |
| Standard VGA planes/font RAM | MCGA's one64-KiB store, code/data font staging, two live font SRAM pages and transfer state |
| LCD palette equals MCGA DAC output | Built-in LCD taps digital video **before DAC**; analog palette and binary LCD conversion are separate |
|640×480 proves square pixels and calibrated gray | Raster is documented; physical pixel aspect, tint, luminance and response are not measured |
| A 720-KiB image means a720-KiB-only drive | Target Operations and DSKT1's sector18 probe require the HD/DD distinction |
| Battery means suspend/resume | Short ride-through keeps CPU/keyboard/memory alive while LCD/touch/floppy become unavailable; not a Convertible-style suspend BIOS |
| Card reader means magnetic stripe | Optional barcode card-holder/wand feeds the keyboard gateway |
| DOS driver reset restores every private field | Original versions preserve some masks, following/button settings and other state; follow the actual dispatch paths |
| A diagnostic banner means a full pass | Loader identity checks, module ROM/clock prerequisites, direct-I/O tests and user interaction are distinct gates |

## Board-state ownership

Keep one owner for every physical latch and shared resource. Rendering, POST support, device diagnostics and BIOS substitution must not maintain contradictory copies.

| Owner | State it owns | Required interaction |
|---|---|---|
| CPU/bus/system support |20-bit address wrap, instruction execution, bus waits, arbitration, RAM/parity/remap, chip-select routing | DMA/refresh receive real bus service; device clocks advance in emulated time |
| Interrupt controller/planar | Request, mask, in-service and extension/injection state; NMI causes and masks | Keyboard/pointing/clock share the actual entry route; EOI and source acknowledgement are different actions |
| Power | Mains, ride-through capacity, rail validity, reset threshold and retained-state boundaries | Drives F301 sense bits and LCD/floppy availability; source loss alone need not reset CPU |
| MCGA | Video RAM, index/register latches, font SRAM/staging, scan timing, CRT/DAC state | Produces digital scanout consumed by LCD controller; no duplicate host-side text buffer as authority |
| LCD interface | F304 index, F305 selected register, conversion/position/inversion/power/backlight and diagnostic state | Implements the same state seen by C000 BIOS, direct diagnostics and rendering |
| Optical interface | F300 selection data, separate emitter/receiver selections, enable/strobes, ADC conversion/result/read-consumption state, presence/comparator inputs | Does not compute host mouse coordinates; guest software owns calibration/masks/reduction |
| Keyboard gateway | Serial transaction, inhibition, buffering, command parser, scan-set/Fn state and barcode insertion | Shares physical transport with application input; BIOS hooks operate on bytes delivered by that path |
| Diskette | FDC phases, status/result FIFO, drive/head/motor/media state, density/change latch, DMA request/terminal count and IRQ | CPU-visible status follows actual transfer/mechanical state; no magic sector-read callback bypass |
| Guest software | IVT hooks, BDA/EBDA, DOS request packets, POINT buffer, INT33 state, DGS environment | Preserve guest memory normally; don't secretly repair defects or synthesize resident services |

A host pointer is an **input source**, not a second authoritative mouse implementation. Map its footprint into obscured beams, then let the original scan code calibrate and reduce them. When exposing an ABI-only path instead, state that boundary and selected driver version. Do not deliver both an injected INT33 position and a hardware touch for the same event.

## Timing and ordering

- Run busy loops as guest instructions at the modeled CPU/bus timing. Driver settling values are loop counts, not microseconds.
- Advance UART bits, keyboard transmission, PIT edges, FDC mechanics, LCD scanout and ADC conversion from device events. Do not use host sleeps to satisfy a polling loop.
- Preserve explicit read/write side effects. ADC result consumption must be distinguishable from conversion-ready; a forever-low “not busy” response fails preserved self-tests.
- Keep diagnostic injection paths in the same interrupt controller and register state as normal traffic. A separate canned “test succeeded” path hides incorrect acknowledgement and priority.
- Preserve the order of a foreground touch poll, mouse callback countdown, old IRQ0 chaining, and application callback. A host-frame-rate callback is not equivalent.
- Device power loss, device reset, CPU reset, warm POST, driver reset and recalibration are different transitions. Specify which state survives each; unknown hardware reset values stay unknown.

## Staged whole-machine acceptance

These are **downstream gates**, not claims that this repository already implements an emulator.

### A. Firmware and reset

Acquire and hash actual planar and C000 ROMs with board/chip provenance; verify lane reconstruction without discarding original chip dumps. Fetch reset from physical FFFF0 and let POST establish stack, memory configuration, vectors and BDA. Preserve ROM checksum failures, parity faults and missing-device results. Do not inject a successful memory count or patch a target-identity byte.

### B. Planar diagnostics and shared interrupts

Implement control/readback, masks, in-service/request state, diagnostic stimulus at63/69, NMI source acknowledgement, DMA pages, PIT/RAS clocking and reset/retention coherently. Supplied CPU0 first checks ROM content/checksums, then NMI and a mandatory clock/RAM/alarm path before later PIT/PIC/DMA tests. An isolated routine fixture can investigate a later test but must not be reported as a normal full-module pass.

### C. Video and keyboard before disk boot

Let the real adapter ROM initialize MCGA and LCD through their registers. Verify text, loadable fonts, logical graphics storage versus LCD placement, inversion, blanking, cursor, short-mode positioning, and rail controls. Deliver keyboard make/break/extended sequences, commands, buffering and Fn transitions through the custom transport; confirm BIOS-visible input without bypassing it with a host INT16 handler.

### D. Disk and DOS

Boot a disposable copy of the supplied or derived media through actual INT13/FDC/DMA/IRQ state. Verify both densities, disk changes, write protection, seek/read errors, terminal count and destructive operations on throwaway media. Reach the real SERVICES menu only after its unchanged gate accepts authentic firmware; then preserve its private services and DGS load origin.

### E. Optical and ABI behavior

Run both original self-tests without success interception, all64 single-beam positions, accepted neighboring runs, rejected broad vertical occlusion, disjoint masks, missing axes, weak/blocked calibration paths and ADC timeout/re-arm failures. Verify LCD-active-area conversion separately for2.4/3.02. Under actual DOS, load the SYS driver, read partial POINT records, exercise INT33 bounds/buttons/counters/callbacks and preserve version quirks. Test absence/fallback as a different configuration, not as evidence that optical hardware works.

### F. Power and optional devices

Remove mains with ride-through available: maintain the documented running/retained state while affected peripherals become unavailable; recover on restoration without inventing suspend/resume. Exhaust ride-through and exercise actual reset behavior. Add barcode feature only when present; verify programming grammar, single-read permission, framing and status through the keyboard path. Test serial/parallel errors and handshakes through their owning devices.

## Proof currently delivered

- Primary numerical tables and challenged contradictions were checked against rendered page images, not accepted solely from OCR.
- Both original touch drivers were disassembled with exact byte accounting and executed in bounded Unicorn fixtures; their real self-tests,64-position sweeps, records, selected APIs and failure cases have retained machine-readable results.
- Selected original video/diagnostic routines were executed with explicitly synthetic memory/I/O; these are algorithm/protocol observations, not a working LCD emulator.
- A reproducible PC DOS3.20 diagnostic research image was built without changing donor/originals; its DOS chain and automatic SERVICES refusal were observed in QEMU. Driver3.02 also loaded through actual DOS and a real POINT client returned the idle record. The supplied mixed disk booted MS-DOS5.00.
- Authentic 7690 ROM execution, complete diagnostic passes, physical timing, calibrated panel appearance and clock-chip identification remain unverified. [VERIFICATION.md](VERIFICATION.md) gives exact evidence rather than a blanket “tested” claim.
