# Touch panel: optical circuit, scan algorithm, and calibration

The IBM 7690 has an **infrared beam-interruption panel**, not a resistive tablet, serial mouse, or controller that directly returns X/Y packets. Its driver selects optical devices, samples a six-bit ADC twice per beam, determines which beams are obscured, and derives a position in software. Implement that circuit boundary to run the supplied diagnostics and unmodified driver; injecting INT 33h coordinates bypasses most of the machine-specific work.

This chapter owns **F300h–F303h**. [VIDEO.md](VIDEO.md) owns the separate LCD index/data pair F304h/F305h and adapter BIOS video extensions. [DRIVER_ABI.md](DRIVER_ABI.md) owns DOS `POINT`, INT 33h, cursor drawing, button emulation and callbacks. [DIAGNOSTICS.md](DIAGNOSTICS.md) covers independent diagnostic-module tests, including transactions that differ from the driver.

## Evidence boundary

- **DOCUMENTED:** technical reference (TR), printed 5-2–5-3, physical PDF page 100; driver interfaces at 5-4–5-17, PDF101–107. [Primary PDF](../IBM_7690_Clinical_Workstation_Technical_Reference.pdf#page=100); [searchable extraction](../DOCUMENTATION/OCR/TECHREF.txt). The register drawing on PDF100 was visually checked; its odd direction markings are genuinely printed, not silently corrected OCR.
- **BINARY:** actual driver offsets below are hexadecimal, relative to byte zero of `LEDTOUCH.SYS`. A DOS SYS file does **not** have the COM program's 0100h origin. Directory version and driver version are different identifiers.
- **EXECUTED:** [TOUCH-TRACE.json](../ANALYSIS/TOUCH-TRACE.json) comes from real preserved x86 instructions run by [touch_trace.py](../TOOLS/touch_trace.py), with explicitly synthetic optical values and BIOS responses. This verifies the decoded algorithms, not the electrical circuit, IBM BIOS execution, DOS installation, CPU cycles, or physical calibration.
- **INFERENCE / OPEN:** latch edges, analog transfer curves, precise conversion delay and actual power-up voltages remain unmeasured. The supplied books name interfaces but do not include a full optical schematic or controller firmware listing.

### Preserved driver identities

| Distribution | Driver banner | Bytes | SHA-256 |
|---|---|---:|---|
| Loose `7690diag/`, diskette version 1.10 | `Version 3.02`, copyright 1987, 1990 | 8111 | `bfb95e3a5d1a9ef87742b33b19d33fee2fbcb0718f04995f770b0a3c37d6d2df` |
| `7690KQPW.IMA`, extracted `ANALYSIS/7690KQPW/` | `Version 2.4`, copyright 1987, 1989 | 7021 | `1c3dc5a2c4a9c6d422f03f92db6b3bcc2b314939603a117594e9573eb7ee2613` |

Both are analyzed. Do not call the driver “1.10”, assume the two files are byte-identical, or use filesystem timestamps as their build dates. The diskette photograph's label explicitly says diagnostic version 1.10 and copyright 1981, 1990, even though the loose files carry 1989 timestamps.

## Physical and logical resolution

TR 5-2 describes LEDs and receivers behind the black translucent bezel, facing one another across the display. Interrupting beams in both axes produces a touch. It specifies maximum **79 horizontal and 47 vertical distinct positions** and a smallest detectable object's dimension of 0.792 cm / 0.312 in horizontally, 0.927 cm / 0.365 in vertically. These are detection-size statements, not pixel pitch or a calibrated host-window coordinate transform.

The binaries scan **64 selections: 40 horizontal-position beams and 24 vertical-position beams**. A single interrupted beam identifies one beam center; a pair of neighboring interrupted beams identifies a midpoint. Thus `2×40−1=79` and `2×24−1=47` explain the documented distinct-position counts without inventing 79+47 emitter channels.

There is no pressure measurement. There is no evidence of independently resolved multiple touches. Separate fingers can produce ambiguous combinations of interrupted beams; the software reduction is not a multitouch matching algorithm. Model the bezel's occlusion before software coordinate reduction. A host contact footprint should obscure an appropriate set of beams, not feed the guest a 640×480 precision tablet value.

## Register map

All addresses are full 16-bit I/O addresses. Do not truncate them to ten ISA address bits or alias them to 0300h–0303h.

### F300h — shared optical selection data, write

| Bit | Primary label |
|---:|---|
| 7 | Driver/Receiver Y-8 |
| 6 | Driver/Receiver Y-4 |
| 5 | Driver/Receiver Y-2 |
| 4 | Driver/Receiver Y-1 |
| 3 | Driver/Receiver X-8 |
| 2 | Driver/Receiver X-4 |
| 1 | Driver/Receiver X-2 |
| 0 | Driver/Receiver X-1 |

The labels refer to device-selection wiring. **They are not a touch coordinate readback format.** The driver writes the desired selector to F300h, then pulses either the receiver-select or LED-select control. The two selected devices must be retained independently: a subsequent F300h write does not make the previous receiver selection disappear.

Maintain a separate eight-bit selection-data latch for the diagnostic all-high comparator. The driver exhaustively distinguishes `FFh` from every other byte even though normal scan selectors only use a subset of the possible values.

The book labels all F300h bits `O`; it does not establish useful F300h readback. The executed driver reads the comparator in F301h, not the selection byte from F300h.

### F301h — diagnostic inputs, read

| Bit | Meaning | Required distinction |
|---:|---|---|
| 7 | Touch Panel Not Installed | 1 means panel absent; not identical to missing interface adapter |
| 6 | `-Sel Data All High` | 0 for F300h=`FFh`; 1 for each `00h`–`FEh`, as required by both self-tests |
| 5 | Keyboard Not Installed | Independent keyboard presence input |
| 4 | Reserved | No invented function |
| 3 | Scanner Type | 1=wand, 0=scanner, according to primary drawing |
| 2 | ADC Check | Input over one-half scale; analog diagnostic input, not touch-valid |
| 1 | LCD Power OK | Negative LCD supply, labeled −22 V |
| 0 | +12 V OK | 0 corresponds to battery-power condition or open fuse; see [PERIPHERALS.md](PERIPHERALS.md) |

Bits 7/5/3 describe distinct connected peripherals. Do not return one “everything present” value for all configurations. The driver checks the selection comparator before panel-presence and analog checks; an absent-adapter response and an installed adapter with disconnected panel take different paths.

The waveform harness uses bit1=1 and bit0=1 except explicit fault scenarios. It does not measure or implement the scanner and keyboard electrical inputs. Real emulation should route them from the owning device/power state.

### F302h — optical controls and ADC status, read/write

| Bit | Write meaning | Read meaning |
|---:|---|---|
| 7–4 | Reserved | Not given an independent function; self-test preserves upper nibble when wrapping low controls |
| 3 | `+Start ADC` | `+ADC Convert Busy` in the manual; see the read-consumption behavior below |
| 2 | `+Receiver Select` | Control readback |
| 1 | `+Driver Enable` | Control readback |
| 0 | `+LED Select` | Control readback |

Receiver and emitter **selection strobes** are not the same as emitter **enable**. Ordinary polling writes `04h,00h` to select a receiver and `01h,00h,02h` to select and then illuminate an emitter. Clearing the controls does not erase the selected channel; otherwise this sequence could not work.

Bits 0–2 must read back coherently. The self-test writes low values 7 down to 1 and then 0 and compares readback with bit3 masked away. One module must own the control latch, selection strobes and ADC state. A second “diagnostic port” implementation returning independent constants will contradict the runtime scanner.

**No dedicated touch interrupt is used by either preserved LEDTOUCH driver.** Software polling executes the scan. An optional INT 08h hook supplies periodic polls for mouse callbacks; that is PIT/IRQ0 software scheduling, not a touch-controller IRQ line.

### F303h — ADC result, read

| Bit | Printed voltage weight |
|---:|---:|
| 5 | 2.500 V |
| 4 | 1.250 V |
| 3 | 0.625 V |
| 2 | 0.313 V |
| 1 | 0.156 V |
| 0 | 0.078 V |
| 7–6 | Reserved |

The driver executes `AND AX,003Fh` after reading this port. Treat it as a six-bit conversion result, not an eight-bit coordinate. The weights are consistent with `5 V/64` steps (nominal 0.078125 V); that arithmetic is an inference from the printed weights, not a measured transfer curve or calibration voltage.

The table's `I/O` column oddly marks bits7–2 `O` and bits1–0 `I/O`, despite the heading “ADC Output.” Actual CPU-side code performs `IN AL,DX` at F303h. The observable CPU read, not that inconsistent direction column, determines the emulator interface. No preserved driver write to F303h establishes a DAC or programmable ADC register.

## ADC transaction and the misleading “busy” simplification

Both versions use this instruction sequence:

```text
DX = F302h
AL = IN(DX)
OUT(DX, AL | 08h)
OUT(DX, AL & F7h)
repeat at most 50 status reads:
    if (IN(F302h) & 08h) == 0: stop polling
AX = IN(F303h) & 003Fh
```

Runtime helper offsets: **3.02 0A9Bh–0AB6h**, **2.4 09CBh–09E6h**. In 3.02 the separate initialization helper at 1CBEh–1CD9h has the same transaction. `LOOPNE` exits on clear bit3 or exhausted CX. **The ordinary runtime helper reads the result even after exhausting the 50 polls; it does not return a separate timeout status.** Do not invent a driver error that its instructions never return.

The initialization test imposes an additional observable contract:

1. Read F303h.
2. Read F302h; expect **bit3 set**.
3. Pulse start high then low.
4. Poll F302h until **bit3 clear**, within 50 reads.
5. Read F303h.
6. Read F302h; expect **bit3 set again**.

Offsets: 3.02 1E36h–1E80h; 2.4 1A52h–1A93h. The independent `IBM7690.DGS` test uses the same consumed-result observation. Consequently, “busy is zero whenever no conversion is running” is insufficient: it fails immediately after a result read.

A useful **emulator-state inference** is:

| State | F302h bit3 | F303h behavior |
|---|---:|---|
| No unread result / consumed | 1 | Returns result latch; remains or becomes consumed |
| Conversion underway | 1 | Preserve defined result latch; timing not established here |
| Unread conversion result ready | 0 | Returns result, transitions to consumed and bit3=1 |

The driver proves these boundary observations, **not** the ADC part number, exact start edge, whether bit3 physically represents a complemented end-of-conversion latch, or a specified number of microseconds. The harness completes on the pulse's falling edge and does not insert analog delay. A real machine model should schedule completion in emulated time and preserve this read side effect. Never make status depend on the guest's CS:IP or test name.

Negative instruction experiments deliberately disable result-read rearming or conversion completion. Both preserved initialization routines reach `Touch Panel Needs Service`; the report records the actual error-message pointer selected before the keyboard acknowledgement fixture returns. These are failure-path checks, not real hardware measurements.

## One beam transaction

For scan index `i`, the driver uses independently mutable tables `receiver[i]` and `emitter[i]`:

```text
OUT F302h,00h                 ; emitter disabled
OUT F300h,receiver[i]
OUT F302h,04h
OUT F302h,00h                 ; receiver latched
wait optical settling loop
D = ADC_read()                ; emitter-off / ambient reading
threshold = max(D - 8, 0)

OUT F300h,emitter[i]
OUT F302h,01h
OUT F302h,00h                 ; emitter latched
OUT F302h,02h                 ; enable selected emitter
wait optical settling loop
L = ADC_read()                ; illuminated reading
OUT F302h,00h                 ; disable emitter

blocked[i] = (L >= threshold)
```

This ADC polarity matters: a working unobstructed beam produces an illuminated result **lower** than the dark reading. With the explicit fixture `D=63,L=0`, an unobstructed beam is clear; a blocked beam with `L=63` is blocked. Returning a larger ADC number for stronger received light would reverse the driver's interpretation.

The comparison is unsigned and **equality counts as blocked**. The subtraction is signed-tested only to clamp the six-bit dark result minus eight at zero. Ambient conditions too close to zero leave no useful discrimination, even if the mouse API appears otherwise functional.

The init-only optical service scan uses a stronger difference threshold: 3.02 1C20h–1C7Ah subtracts **16** rather than 8. The independent v1.10 diagnostic module uses **20**. Preserve those as software-policy differences over one circuit; do not bake a single “touch threshold” into the hardware port implementation.

## Selector ordering and retained tables

Canonical selector generation is:

```python
selector = ((index // 8) << 4) | (index % 8)   # index 0..63
```

Sequence: `00..07,10..17,20..27,30..37,40..47,50..57,60..67,70..77`.

| Scan indices | Bitmap bytes | Position axis |
|---|---|---|
| 0–39 | first five bytes | horizontal position |
| 40–63 | final three bytes | vertical position |

Within each byte, lower scan indices occupy higher bits: index0 is bit7, index7 is bit0. Bitmaps are not little-endian coordinate words.

### Useful 3.02 internal offsets

These are **driver-private RAM**, not machine registers or ABI promises. They are useful debugger/watchpoint locations when executing this exact hash.

| Offset | Width / role |
|---|---|
| 0620 | word, optical settling loop count currently used |
| 0622 | word, tracked successful settling count |
| 0624 | word, additional ambient-settling allowance |
| 0626–062D | eight-byte detected/intersected blocked-beam bitmap |
| 062E–0631 | zero-initialized padding following bitmap; relevant to scan reduction |
| 0632–0639 | eight-byte usable-beam mask, initially all FF |
| 063A | byte, remaining calibration passes |
| 063B | byte, scan/pointing-device initialized flag |
| 063C | byte, IBM mouse fallback selector, zero=optical panel |
| 063D | byte, optical substitution attempt |
| 063E–067D | 64 emitter selector bytes |
| 067E–06BD | 64 receiver selector bytes |
| 06BE | leading canonical-table boundary byte, initially 00 |
| 06BF–06FE | 64 canonical selector bytes |
| 06FF | trailing canonical-table boundary byte, initially 77 |
| 0700 | current dark-minus-eight threshold |
| 0701 / 0703 | normalized horizontal / vertical words, FFFF=no touch |
| 0705 | one-shot LCD inversion gesture latch |
| 0706 | prior vertical gesture position, FFFF=none |
| 0708 | counted active scans / IBM mouse packets for private query |
| 070A / 070C | configured missing-touch retention / remaining polls |
| 070E / 0710 | signed coordinate adjustments used in extended LCD transform |

2.4 equivalents: bitmap05F0, usable05FC, calibration0604, initialized0605, attempt0606, emitter0607, receiver0647, canonical0688, threshold06C9, coordinates06CA/06CC, inversion06CE, previous gesture06CF, count06D1. There is no 3.02 IBM mouse fallback block in 2.4.

## Calibration is software, not coordinate calibration UI

The supplied code does not ask a user to touch targets to fit a geometric matrix. Its calibration chooses usable optical paths and settling delays. A host emulator should not replace it with an invented four-corner touchscreen setup.

### Common optical substitution algorithm

Initial table construction gives each emitter and receiver its canonical selector. During calibration, a beam failing the difference test tries adjacent optical paths in this order:

1. current retained receiver, previous canonical emitter;
2. current retained receiver, next canonical emitter;
3. previous canonical receiver, canonical emitter;
4. next canonical receiver, canonical emitter.

The surrounding canonical bytes make the endpoints addressable, but do not prove that every adjacent code corresponds to a physically adjacent receiver across an axis boundary. The actual stored tables and selected values, rather than a host assumption about an electrical matrix, determine the subsequent transactions.

The receiver in the first two retries is canonical only until a receiver substitution has occurred. Those retries write only the emitter-table entry; a neighboring receiver retained from a previous successful calibration pass remains selected. Tables are not rebuilt between passes.

A failing beam sets the temporary blocked bitmap. It is intersected with the usable mask; the usable mask is then ANDed with the complement of the failures during calibration. Those unusable bits are software state. Later ordinary scans cannot report them as touches.

**Important:** setting the initialization flag back to zero rebuilds selector tables but does not refill the usable mask with FF. INT33 reset does not overwrite that mask either. Do not claim that Ctrl+right Shift necessarily restores a beam already masked out; fresh driver loading starts from the original all-ones mask. Emulators must preserve the actual guest memory, not perform an extra host-side reset.

**EXECUTED changing-path fixture:** selector22h's canonical pair is dark; receiver21h/emitter22h is illuminated once, then fades. In both versions, calibration first retains neighboring receiver21h and later succeeds with **receiver21h/emitter21h**, leaving all usable bits set. This directly exercises retained receiver state across passes rather than only the all-clear case. A separate obstruction-at-calibration fixture masks X18/Y11; clearing the input and calling INT33 reset does **not** restore those usable bits. Results are in `calibration_receiver_retention_and_mask_survival` in [TOUCH-TRACE.json](../ANALYSIS/TOUCH-TRACE.json). The synthetic fade is a controlled algorithm input, not a measured optical aging/timing curve.

### Version 2.4

The runtime scanner starts at 06D3h. Each receiver/emitter settling loop uses a literal `DX=0090h` and `DEC DX / JNZ`. The initialized data has eight calibration passes. When a difference test fails during those passes, selector substitution occurs; after calibration the same event becomes an ordinary blocked beam. Treat the loop as guest instructions at the selected CPU/bus timing, not a host sleep of “144 microseconds.”

### Version 3.02

At 0712h, a nonzero fallback selector branches to the IBM pointing-device code. Otherwise first initialization sets eight passes and initializes settling counts to two. For a failing beam during calibration:

- while current settling count is at most 00FFh, add ten and retry the same selection;
- after that threshold, restore the tracked successful count and advance the optical substitution attempt;
- a successful test can raise the tracked count;
- after the eighth pass, choose `tracked + floor(tracked/2) + additional` for normal scanning.

The initial self-test at 1DB4h does more than the lazy runtime initializer: it invokes scanner initialization repeatedly, performs a separate service scan, and checks each stored dark reading against 30. If an ambient sample is too low, it increases the additional/current allowance in steps of ten, up to its 0100h comparison, then reports excessive room light if still unsuccessful. A nonzero extra allowance gets a further one-eighth margin. It prints the final decimal settling-loop count.

The synthetic all-clear fixture prints **`Optical devices settle time 003`** and **`Test complete - OK`**. Three is an instruction-loop parameter produced by that fixture, not a measured factory constant. Slow analog settling, weak emitters, obstruction during calibration and ambient light need separate circuit scenarios.

## From blocked beams to normalized coordinates

After calibration the usable blocked map must contain activity in both axes. No valid two-axis touch yields `FFFFh,FFFFh`. Version3.02 can retain a previous valid result for a programmable number of missing scans, configured by private INT33 function5Ch; the default is no such retention. This is a software debounce count, not elapsed milliseconds.

Both versions also reject any usable Y bitmap whose **middle byte is FFh**, meaning all vertical beams8–15 are obscured, even if X is a valid single beam and the whole Y obstruction is contiguous. The code loads the first two Y bytes into AX, ORs their combined activity and the third byte into AL, rejects zero AL, then rejects zero after `INC AX` (3.02 08B2h–08BEh;2.4 082Ch–0838h). Because AH is the middle byte, AH=FFh forces AL=FFh and the increment wraps to zero. X18/Y8..15 therefore yields FFFF/FFFF with default retention, not a centroid. This is a software broad-occlusion guard, not a separately documented hardware limit.

For a **single contiguous blocked run that passes those guards**, with first and last beam indices `a,b` within an axis:

```text
normalized_x = 127 × (a + b)         ; horizontal indices 0..39
normalized_y = 217 × (a + b)         ; vertical indices 0..23
```

A single beam has `a=b`. Neighbor pairs produce the odd half-step values. This explains the 79/47 distinct positions. It does **not** exactly fill 0..9999: the final single beams yield 9906 and 9982. Later software scales against 9999 and may clamp, round, or translate the values differently.

BINARY: 3.02 X reduction08F5h–094Ah, Y094Bh–0983h; 2.4 X0855h–08A2h, Y08A3h onward. Executed single-beam sweeps cover all 40 horizontal and all 24 vertical positions in both versions.

| Interrupted X beams | Interrupted Y beams | Normalized result, both versions |
|---|---|---|
| 0 | 0 | 0,0 |
| 39 | 23 | 9906,9982 |
| 18 | 11 | 4572,4774 |
| 18,19 | 11,12 | 4699,4991 |
| 0,1 | 0,1 | 127,217 |
| 38,39 | 22,23 | 9779,9765 |
| 18 | none | FFFF,FFFF |
| none | 11 | FFFF,FFFF |

### Do not replace sparse-mask behavior with a global centroid

The actual reduction walks bytes and uses byte/word lookahead, not a sum of all active beams. Disjoint obstructions can be bridged within a lookahead region or ignored past a gap. For example, with unmodified3.02:

- X `{2,5}`, Y `{3,6}` gives **889,1953**, matching the outer indices in those local spans;
- X `{2,18}`, Y `{3,20}` gives **508,4991**: the separated horizontal contact is not handled the same way as the vertical gap.

These are executed algorithm observations under artificial beam masks, not a promised multitouch UI. Let the original driver make that reduction when emulating hardware. An ABI replacement must declare which driver version and awkward edge behavior it reproduces.

## LCD active-area coordinate transform

After raw reduction, both drivers call **INT10 AX=11BAh, BH=00h**. A recognized adapter response has `AH=BAh`; the code uses BX=top offset, CX=active scanlines and DI=total panel scanlines. Both skip an unrecognized response. **3.02 additionally skips signed CX<=199** (0992h–0996h); **2.4 skips only CX=0** (08EAh–08ECh). Thus a recognized nonzero height below200 is transformed by2.4, but not3.02.

For a recognized larger active area,3.02 applies, with integer truncation:

```text
if top != 0:
    y = max(y - floor(9999 × top / panel_height), 0)
active_span = floor(9999 × active_height / panel_height)
y = min(y, active_span)
y = floor(9999 × y / active_span)
y = clamp(y + adjustment_y, 0, 9999)
x = clamp(x + adjustment_x, 0, 9999)
```

Offsets 0984h–09FDh; private signed adjustment words070Eh/0710h are set by INT33/5Ch. This is why rendering a centered LCD image while mapping touch over an unrelated full host window produces misaligned input. The hardware, adapter BIOS active-area report and driver must agree.

**OPEN:** no authentic C000 adapter ROM is supplied, so the actual per-mode BX/CX/DI values and its response to direct controller changes are not executable here. [VIDEO.md](VIDEO.md) transcribes the documented interface. The trace report separately exercises a synthetic top40/active400/total480 response; do not advertise it as an observed factory mode.

## LCD gestures during polling

The scan routine reads keyboard flags at0040:0017. Right Shift (bit0) converts touches into display-control gestures rather than application input:

- **Right Shift + Ctrl flag:** clear initialized state, request eight calibration passes, suppress coordinates.
- **Right Shift, left half (`x<5000`):** toggle a one-shot software inversion state through INT10/11BAh BH02h. Repeated scans of the same held gesture do not repeatedly invert.
- **Right Shift, right half:** compare successive vertical normalized values. Use BIOS BH00h to obtain active-area limits, then BH01h to move the vertical offset by four scanlines when legal. Reset the remembered position after issuing a move.
- Return FFFF coordinates while the gesture is consumed. A later no-touch path resets the inversion latch and prior vertical value.

This is **foreground/background reversal**, not a measured analog contrast adjustment. The driver does not directly modify F304h/F305h for these gestures. A firmware runner must execute the adapter BIOS path; an ABI-only layer should not claim to have tested those hardware registers by responding to this call in the host.

## Initialization failures and version differences

| Check | 3.02 code / consequence | 2.4 difference |
|---|---|---|
| All-high selection wrap | 1DB7–1DEE; failure selects IBM mouse fallback and prints its banner | 19DB–1A0F; reports select-line wrap failure, no mouse fallback |
| Low three control-bit wrap | 1DEF–1E35; failure selects fallback after service prompt | 1A10–1A51; service prompt only |
| ADC consumed/start/ready sequence | 1E36–1E80; selected error3 or0B, fallback enabled on these errors | 1A52–1A93; same observed status expectations without fallback block |
| Panel-not-installed bit | 1E82–1E96; service prompt for panel disconnected | 1A94–1AA8 |
| Ambient light / settling | repeated calibration and adjustable delay | fixed runtime settling loop; service scan checks ambient values |
| Weak/no light | service scan uses dark-minus16 threshold | same service role; separate code and messages |
| Primary +12 V input | F301 bit0 clear selects error91h | same primary-supply check |

Not every embedded message has a live caller in every driver. The strings `ADC Conversion Error`, `Touch Panel Receiver Error`, and `LED Output Weak` are not proof of three independently implemented runtime state machines. Follow reachable branches, not a `strings` inventory.

The default service-prompt fixture acknowledges Enter to let an error return. It does not simulate a patient-facing UI or prove the real keyboard's diagnostic handling.

## Implementation ownership and save-state contract

**Hardware-owned:** F300 selection latch; independent receiver/emitter selection; emitter-enable state; F302 control readback; ADC conversion/result/consumed phase; scheduled completion; analog inputs for selected path; presence, comparator and power inputs.

**Guest software-owned:** all selector tables, masks, calibration passes/delays, normalized coordinates, smoothing counters, mouse events, callback vectors and LCD gesture state. Do not duplicate or silently reset these in a host device model. A whole-machine save state already retains them as guest RAM.

**Host input adapter:** contact position/footprint mapped onto beam occlusion, without knowledge of driver CS:IP or callback state. Explicitly decide how a single mouse click or hover corresponds to contact; the panel does not report hover in free space.

**Power owner:** actual +12 V / LCD rail and battery transition. Loss of optical power must affect sampled behavior and F301 input state coherently. It is not enough to make the picture dark while continuing perfect touch data on battery.

## Downstream implementation gates

These are future emulator requirements, not already-passed hardware claims:

1. Boot a configured authentic ROM pair/adapter ROM when obtained; load the original driver through DOS without patching its header, branches or result values.
2. Pass select wrap, control wrap and ADC consumption/start/ready checks through one consistent device model.
3. Calibrate an unobstructed grid; record actual selectors, per-beam dark/light readings and chosen delay. Obstruction during calibration must have a reproducible effect.
4. Exercise first/last beam, neighboring pair, one-axis-only occlusion, separated masks and release. Observe original `POINT` and INT33 outputs; do not substitute precomputed coordinates.
5. Vary optical settle time, ambient intensity, receiver/emitter pairing and weak paths; fail genuinely when the software's thresholds require it.
6. Exercise recognized LCD centering reports and right-Shift gestures without inconsistent video/touch coordinate spaces.
7. Load2.4 and3.02 independently and preserve their calibration, failure and fallback differences.
8. Snapshot during selection, pending conversion, unread result, partial DOS record, callback countdown and button release pulse; resume to the same observable results.

## Reproducing the instruction evidence

From repository root, after extracting the supplied image as described in [DIAGNOSTICS.md](DIAGNOSTICS.md):

```sh
uv run --with unicorn==2.1.4 python TOOLS/touch_trace.py --output ANALYSIS/TOUCH-TRACE.json
```

The tool verifies both input hashes before execution. It exercises initialization, all single-beam positions, adjacent/disjoint masks, no-touch, DOS-record generation, mouse coordinates, callback polling, button following, selected failures and IBM mouse fallback. Inputs and deliberate BIOS substitutions are recorded in the JSON. Neither a successful synthetic self-test nor its instruction count establishes a real 8086 timing model.
