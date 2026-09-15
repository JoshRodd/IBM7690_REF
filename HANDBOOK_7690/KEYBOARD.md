# Keyboard: compact keys, serial protocol, and the shared IRQ1 path

## Scope and evidence

The 7690 has a **78-key, US-layout, integral keyboard with its own microcontroller**. Its shape resembles the PC Convertible keyboard; its electrical and software interfaces do not. It emits enhanced type-`P` scan sets 1 and 2 over the Model 25/30 **mode-2 bidirectional serial protocol**. Barcode characters enter this same microcontroller and emerge as keyboard scan sequences. Do not implement a Convertible NMI/matrix interface, an XT unidirectional keyboard, or an AT 8042.

Evidence notation in this chapter:

- **DOCUMENTED** means the supplied [7690 Technical Reference](../IBM_7690_Clinical_Workstation_Technical_Reference.pdf), principally printed 3-2–3-27, physical PDF 78–90. The searchable [TECHREF text](../DOCUMENTATION/OCR/TECHREF.txt), lines 3979–4777, is a locator, not authority for numeric transcription.
- **DOCUMENTED, image checked:** physical PDF 81–82 (commands and problematic timing), 84–90 (all physical-key/scan tables and barcode translation); PDF 14–15 (system ports and shared IRQ1). A PDF page contains two printed pages. For this section, PDF 84 contains printed 3-14 and 3-15, not printed page 84.
- **BASELINE / INFERENCE** identifies inherited Model 25 implementation evidence, not a 7690 ROM observation. The sibling research corpus `/Users/josh/src/bios8530/reference/hardware_spec.json`, `planar_registers` and `interrupts.irq1_dispatch_contract`, records primary Model 25 documentation and explicitly secondary reverse engineering of undocumented keyboard ports. See [MODEL25.md](MODEL25.md) for the inheritance boundary.
- **OPEN** marks missing firmware/hardware evidence or an actual source contradiction. No 7690 keyboard-microcontroller ROM or 7690 system BIOS dump was supplied. No claim in this chapter is a measured 7690 firmware execution result.

Hexadecimal bytes and ports use `h` or code formatting; key numbers are decimal IBM diagram positions. Timing and rates are decimal.

## 1. Ownership: do not conflate three keyboard interfaces

The physical route is:

`physical switches → keyboard microcontroller → interface-adapter connector → external keyboard jumper cable → system-board keyboard port → shared IRQ1 → BIOS INT 71h demultiplexer → conventional keyboard handler → INT 16h/DOS`

The integral keyboard still requires the external cable. The operations guide's 301-error advice explicitly checks that cable and a held key. A disconnected cable is not the same failure as a nonexistent internal keyboard, nor is a missing barcode feature a broken keyboard.

| Owner | State and responsibilities |
|---|---|
| Keyboard microcontroller | Physical key states, Fn, real/artificial Shift bookkeeping, internal Num state, scan-set selection, typematic timer, 17-byte scan FIFO, response stream, command/parameter parser, indicator outputs, barcode-to-scan conversion. |
| System-board gate array | Serial framing/parity, per-port data and status, clock inhibition/transmit controls, source request to the interrupt controller. |
| Interrupt controller | IRQ1 mask/pending/in-service and special INT `71h` routing; conventional EOI handling. |
| BIOS | System initialization to scan set 1, shared-source dispatch, port-`60h` compatibility latch, standard scan interpretation, BDA flags and character ring, INT `16h` services. |
| Application | Meaning of function keys, barcode framing recognition, successful-read sound, inactivity/backlight policy, input inhibition during AC loss. |

**DOCUMENTED:** TR 1-9 says the system-board controller receives serial data and checks parity, and describes presentation at `60h`. TR 1-11 is more specific that output port `60h` is used by BIOS to store keystrokes. TR 1-13 explicitly says level 1 is shared by keyboard and pointing device and handled through INT `71h`. These facts support the Model 25 layered route, not an invented direct host-to-INT-09 shortcut.

### Planar register boundary

| Port | Contract and certainty |
|---|---|
| `60h` | **DOCUMENTED:** BIOS keystroke storage latch. **BASELINE:** BIOS copies a selected serial-port byte here before dispatching the normal keyboard handler. Not an 8042 data/command endpoint. |
| `61h` | **DOCUMENTED:** bits 7–6 and 3–2 reserved; bit 5 masks channel-check NMI when 1; bit 4 masks RAM-parity NMI when 1; bit 1 beeper data gate; bit 0 PIT channel-2 gate. **There is no documented bit-7 XT keyboard-clear handshake here.** |
| `62h` | **DOCUMENTED:** bit 7 parity error; bit 6 channel check; bit 5 PIT2 output; bits 4–2 reserved; bit 1 coprocessor installed; bit 0 reserved. Not an AT keyboard status register. |
| `66h` | **BASELINE, secondary:** bits 0/1 port-1/port-2 error (parity interpretation provisional); bit 2 keyboard-lock status; bit 3 software port-role selection; bits 4/5 port-1 clock pulse/release and active-low force; bits 6/7 corresponding port-2 controls. Precise edge/electrical semantics require ROM tracing. |
| `67h`, `68h` | **BASELINE:** port-1 and port-2 bidirectional serial data buffers. Do not assume both represent populated 7690 connectors. |
| `69h` | **BASELINE, secondary:** bit 3 pulse starts port-1 transmission; bit 4 starts port-2 transmission; bit 2 probable NMI allowance. Other bits are not established here. |
| `6Ah` | **BASELINE, secondary:** bit 2 port-1 byte available, bit 5 port-2 byte available. Do not treat this as the AT `64h` status bit layout. |
| `A0h` read | **BASELINE, secondary:** bits 2/3 indicate keyboard serial-port IRQ1 sources. Writes control global NMI, not an 8042 command byte. |

A Model 25 implementation can supply the provisional gate-array behavior above. Its normal IRQ1 vector is specially routed to `71h`, independently of the programmed ordinary PIC base. The baseline BIOS then invokes PIC-base+1 for keyboard or INT `73h` for pointing after writing the compatibility latch. **Do not add the Model 30 RTC source** merely because it shares the same research corpus. Source acknowledgement, rearming, and PIC EOI are distinct operations: an `IN 60h`, arbitrary `OUT 61h`, or software INT `09h` is not a substitute for servicing the selected serial source. Exact 7690 gate-array transaction traces remain OPEN; preserve this boundary in any implementation claiming only documented fidelity.

## 2. Serial wire and power-on state machine

**DOCUMENTED:** TR 3-2, 3-5–3-7 / PDF 78–80.

- Mode 2 supports commands in both directions and parity. The data frame is **start 0, data bits D0 through D7, odd parity, stop 1**: 11 bits, LSB first. Scan set and serial mode are different settings.
- Clock and data use open-collector signaling: either side can force a line low. Low/inactive is 0.0–0.7 V; high/active is 2.4–5.5 V. The keyboard generates transfer clocks.
- Clock low inhibits keyboard transmission. Clock high with data low is the system request-to-send condition. Both lines high permit keyboard transmission.
- If clock is forced low **before the parity bit is sent**, retain the byte for retransmission and release the lines. If parity has already been sent, finish that transfer. Do not consume a FIFO byte simply because its start bit was emitted.
- During BAT the keyboard ignores incoming line activity and releases both lines high.
- The text also says idle data is held inactive while idle clock is active, then calls that same condition a system request to send. This is an internal prose inconsistency, not evidence for overriding the transfer decision table. An exact idle waveform is OPEN.

Power application initiates POR; the printed POR interval is **150 ms–2.0 s**. BAT tests processor, ROM checksum, and RAM, and takes **300–500 ms**, stated as additional to POR. Successful BAT sends `AAh` and begins scanning. Failed BAT sends `FCh`, disables scanning, and waits for command/reset. The text gives completion timing as **600 ms–2.5 s after POR**, and **300–500 ms after acknowledgement of Reset**. These overlapping descriptions do not define one uniquely exact power-up schedule. Select deterministic emulated times within a declared profile; do not call them measured delays.

Following successful POR the **system sets scan set 1**. The manual does not establish that every intermediate keyboard state before that host command is already set 1. Indicators are off after power-on/reset. The `FFh` reset command also resets the barcode microcontroller; [PERIPHERALS.md](PERIPHERALS.md) describes the latter's approximately one-second reset interval.

The six-pin system-board keyboard connector is J1: pin 1 data, 2 not connected, 3 ground, 4 +5 V, 5 clock, 6 not connected (TR 1-128 / PDF 73). Do not derive keyboard matrix rows or switch ghosting topology from these pins.

## 3. Buffering, repeat, and command arbitration

### Scan FIFO

**DOCUMENTED:** TR 3-3–3-5 / PDF 78–79.

The keyboard has a **17-byte FIFO**, but normal queued scan data may occupy only the first **16** positions without overrun. On overflow, the 17th position is the `FFh` overrun marker. Further keystrokes while full are lost. The marker is delivered when it reaches the head, not as an immediate out-of-band exception. Command response codes **do not occupy scan-FIFO positions**.

A multiple-byte make/break sequence must fit **in its entirety** into available space; otherwise overrun occurs. Never queue only `E0h` or `F0h` and drop the corresponding code. Track a sequence's prospective byte count before committing it. Do not make the physical controller lossless by attaching an unbounded host FIFO.

Pressed keys are reported in press order. Release emits break except for the documented Pause/Break combinations. The keyboard retains events while serial transmission is inhibited; a held key under inhibition stores only its first make, not endlessly repeated copies.

### Typematic

Default delay is **500 ms ±20%**, followed by **10.9 characters/s ±20%**. Only the most recently pressed held key repeats. Releasing it stops repeat even when older keys remain down. The manual excludes Ctrl+Pause, Ctrl+Break, Num Lock, Scroll Lock, and Caps Lock from typematic; do not silently import a broader no-repeat modifier list from another keyboard model.

Repeat only the unique base sequence for a shift-dependent key, not its artificial Shift setup/teardown. The current typematic make sequence is not immediately changed when a host indicator command changes Num state. Make/break processing samples the overlay state at the subsequent event; this can produce different make/break mappings if Fn/Num changes while a key is held. Do not replace that documented behavior with an unconditional make-time key-identity snapshot.

### Command table

**DOCUMENTED, image checked:** TR 3-8–3-13 / PDF 81–83. Here arrows list response bytes in transmission order; responses remain subject to the serial handshake.

| Host command | Required action and response |
|---|---|
| `FF` Reset | `FA`, wait for acknowledgement acceptance/reset-line procedure, reset and BAT; `AA` on success or `FC` failure. Also reset barcode controller. The printed text says the system pulses clock/data with a **500-ms active pulse** before reset proceeds, or another command ends reset waiting. This surprising value is visibly printed, not an OCR microsecond conversion; do not silently claim a verified 500-µs replacement. |
| `FE` Resend | Retransmit previous output; if previous output was `FE`, resend the last byte before it. No additional `FA`. |
| `F6` Set Default | `FA`; restore default key types/rate/delay, resume only if previously scanning. |
| `F5` Default Disable | As default, but stop scanning and await further instructions. |
| `F4` Enable | `FA`; erase output buffer, clear last typematic key, start scanning. |
| `F3 p` Set Rate/Delay | `FA`; suspend scanning awaiting parameter; `FA` for parameter; install rate/delay and resume only if previously enabled. Another valid command interrupts the parameter transaction without changing the old rate/delay; process that command. The special recovery prose retains the previous scanning eligibility for a subsequent complete `F3 p`. |
| `F2` Read ID | `FA AB 84`; suspend scanning during response, then commence scanning. These are bytes `AB` then `84`, regardless of the prose's confusing low/high-byte terminology. |
| `F0 p` Select/Query Set | On `F0`, `FA`, stop scanning, clear FIFO and typematic key. `p=01` set 1; `02` set 2; `00` query. A valid parameter receives `FA`, then a byte indicating the current set according to the printed prose; resume only if previously enabled. A new valid command cancels pending selection without changing the old set, but **does not undo the earlier FIFO/repeat clear**. See ambiguity below. |
| `EE` Echo | `EE`, no `FA`; continue scanning. |
| `ED p` Set Indicators | `FA`; stop scanning until parameter; `FA`; set lights and internal Num state; resume only if previously enabled. New command cancels pending indicator update without modifying previous lights. |
| Set Key Types / Set All Key Types | Acknowledged but not supported. The 7690 chapter names these command families without printing their opcodes or parameter-consumption details; do not claim a measured implementation of set-3 type controls. |

`ED` parameter bits: bit 0 Scroll Lock, bit 1 Num Lock, bit 2 Caps Lock, bits 7–3 must be zero. A 1 lights the corresponding indicator. Bit 1 additionally synchronizes the keyboard's internal Num state. The system must resend the entire desired indicator byte, not a bit-change command.

Invalid input or incorrect host-to-keyboard parity produces `FE`. Valid commands except Echo/Resend receive `FA`. If a new command interrupts output of an ACK, abort that ACK and process the new command. Device-side detection of an unidentifiable switch closure produces `FF`, as does FIFO overrun; the byte alone does not distinguish these causes.

**OPEN, scan query:** the `F0` prose says the current-set byte follows the ACK without explicitly restricting that statement to option 00. It does not print the actual returned set-identification encodings. A generic enhanced-keyboard implementation may return an identifier only for query and may use encoded IDs; those behaviors are not established by this 7690 passage. Do not turn the prose into a fabricated binary trace. Ordinary BIOS set-1 initialization and barcode gateway `F0 04` must both be accounted for when this is resolved.

`F0` also introduces the barcode gateway extension: `F0 04` opens it, `F0 00` closes it. **Parser context matters**: `F0 00` in normal keyboard-command context queries scan set; inside the barcode transaction it ends that transaction. Do not reject `04` as an ordinary invalid scan set before allowing the 7690 extension.

### Exact rate parameter, including a printed discrepancy

Delay is `250 ms × (1 + ((p >> 5) & 3))`; bit 7 must be zero. Bits 4–0 select rate. The complete printed rates are:

| Low five bits (hex) | CPS | Low five bits | CPS | Low five bits | CPS | Low five bits | CPS |
|---|---:|---|---:|---|---:|---|---:|
| 00 | 30.0 | 08 | 15.0 | 10 | 7.5 | 18 | 3.7 |
| 01 | 30.0 | 09 | 13.3 | 11 | 6.7 | 19 | 3.3 |
| 02 | 24.0 | 0A | 12.0 | 12 | 6.0 | 1A | 3.0 |
| 03 | 24.0 | 0B | 10.9 | 13 | 5.5 | 1B | 2.7 |
| 04 | 20.0 | 0C | 10.0 | 14 | 5.0 | 1C | 2.5 |
| 05 | 20.0 | 0D | 9.2 | 15 | 4.6 | 1D | 2.3 |
| 06 | 17.1 | 0E | 8.6 | 16 | 4.3 | 1E | 2.1 |
| 07 | 17.1 | 0F | 8.0 | 17 | 4.0 | 1F | 2.0 |

PDF 81 visibly prints `Period = ((8+A) × 2 × B)/2 × 0.00834 seconds`, with A bits 2–0 and B bits 4–3. Taken literally it produces zero for B=0, contradicting its own table. The familiar enhanced-keyboard formula `((8+A) × 2^B) × 0.00417 seconds` is a **BASELINE candidate**, not an image-confirmed correction; the duplicated low-rate selector pairs in the first column are also visibly printed. A documentation-driven profile can implement the explicit table. A cycle-accurate claim needs a keyboard-controller ROM or measured repeat trace. Keep this discrepancy visible rather than copying OCR as arithmetic.

## 4. Physical key map and base raw scan codes

**DOCUMENTED, image checked:** Figures 3-3–3-5 / PDF 84–85. Codes below are **already enhanced-keyboard device scans**, not Convertible internal scans. Ordinary set-1 break is `make OR 80h`; ordinary set-2 break is `F0 make`. For an extended `E0 make`, break is `E0 (make OR 80h)` in set 1 or `E0 F0 make` in set 2. Special combinations below replace these rules.

**Set-2 break continuation timing:** TR3-13 / physical PDF83 says transmission of the second byte begins typically within **2 ms after the interface is enabled following the F0 prefix**. Subsequent key transmissions before that interface enable can delay it to **10 ms worst case**. Measure this interval from interface re-enable, not from prefix emission; it is not a blanket delay bound for every unrelated response or multibyte sequence.

The missing diagram numbers 29, 42, and 45 are not missing emulator keys; they are absent from this US 78-key layout. `Fn` is number 59; no standalone transmitted scan is assigned to it.

| Key # | Host physical position / legend | Base set 1 | Base set 2 |
|---:|---|---|---|
| 1 | Backquote | 29 | 0E |
| 2 | Digit1 | 02 | 16 |
| 3 | Digit2 | 03 | 1E |
| 4 | Digit3 | 04 | 26 |
| 5 | Digit4 | 05 | 25 |
| 6 | Digit5 | 06 | 2E |
| 7 | Digit6 | 07 | 36 |
| 8 | Digit7 | 08 | 3D |
| 9 | Digit8 | 09 | 3E |
| 10 | Digit9 | 0A | 46 |
| 11 | Digit0 | 0B | 45 |
| 12 | Minus | 0C | 4E |
| 13 | Equal | 0D | 55 |
| 14 | Backslash | 2B | 5D |
| 15 | Backspace | 0E | 66 |
| 16 | Tab | 0F | 0D |
| 17 | Q | 10 | 15 |
| 18 | W | 11 | 1D |
| 19 | E | 12 | 24 |
| 20 | R | 13 | 2D |
| 21 | T | 14 | 2C |
| 22 | Y | 15 | 35 |
| 23 | U | 16 | 3C |
| 24 | I | 17 | 43 |
| 25 | O | 18 | 44 |
| 26 | P | 19 | 4D |
| 27 | BracketLeft | 1A | 54 |
| 28 | BracketRight | 1B | 5B |
| 30 | CapsLock | 3A | 58 |
| 31 | A | 1E | 1C |
| 32 | S | 1F | 1B |
| 33 | D | 20 | 23 |
| 34 | F | 21 | 2B |
| 35 | G | 22 | 34 |
| 36 | H | 23 | 33 |
| 37 | J | 24 | 3B |
| 38 | K | 25 | 42 |
| 39 | L | 26 | 4B |
| 40 | Semicolon | 27 | 4C |
| 41 | Quote | 28 | 52 |
| 43 | Enter | 1C | 5A |
| 44 | ShiftLeft | 2A | 12 |
| 46 | Z | 2C | 1A |
| 47 | X | 2D | 22 |
| 48 | C | 2E | 21 |
| 49 | V | 2F | 2A |
| 50 | B | 30 | 32 |
| 51 | N | 31 | 31 |
| 52 | M | 32 | 3A |
| 53 | Comma | 33 | 41 |
| 54 | Period | 34 | 49 |
| 55 | Slash | 35 | 4A |
| 56 | ShiftRight | 36 | 59 |
| 57 | Asterisk / PrtSc | 37 | 7C |
| 58 | Ctrl | 1D | 14 |
| 59 | Fn | local modifier; no assigned scan | local modifier; no assigned scan |
| 60 | AltLeft | 38 | 11 |
| 61 | Space | 39 | 29 |
| 62 | AltRight | E0 38 | E0 11 |
| 63 | ArrowLeft | E0 4B | E0 6B |
| 64 | ArrowUp | E0 48 | E0 75 |
| 65 | ArrowDown | E0 50 | E0 72 |
| 66 | ArrowRight | E0 4D | E0 74 |
| 67 | Escape | 01 | 76 |
| 68 | F1 | 3B | 05 |
| 69 | F2 | 3C | 06 |
| 70 | F3 | 3D | 04 |
| 71 | F4 | 3E | 0C |
| 72 | F5 | 3F | 03 |
| 73 | F6 | 40 | 0B |
| 74 | F7 | 41 | 83 |
| 75 | F8 | 42 | 0A |
| 76 | F9 | 43 | 01 |
| 77 | F10 | 44 | 09 |
| 78 | Num | table prints 00; effective Num function requires Fn | table prints 00; effective Num function requires Fn |
| 79 | ScrollLock | 46 | 7E |
| 80 | Insert | E0 52 | E0 70 |
| 81 | Delete | E0 53 | E0 71 |

Key 78's `00` base-case entry is not accompanied by prose deciding whether an unmodified Num physically transmits a zero or means no useful function. Keep that ambiguity separate from known `FF` error behavior. Do not use `00` as a universal empty-latch return.

### Fn and control combinations

| Physical combination | Function | Set 1 make / break | Set 2 make / break |
|---|---|---|---|
| Fn+Ctrl | Right Ctrl | `E0 1D / E0 9D` | `E0 14 / E0 F0 14` |
| Fn+Esc | SysReq | `54 / D4` | `84 / F0 84` |
| Fn+F1 | F11 | `57 / D7` | `78 / F0 78` |
| Fn+F2 | F12 | `58 / D8` | `07 / F0 07` |
| Fn+Num | Num Lock | `45 / C5` | `77 / F0 77` |
| Ctrl+Num | Pause | `E1 1D 45 E1 9D C5`, no separate break | `E1 14 77 E1 F0 14 F0 77`, no separate break |
| Fn+Enter, Num off | Keypad Enter | `E0 1C / E0 9C` | `E0 5A / E0 F0 5A` |
| Fn+Left | Home | base `E0 47 / E0 C7`, plus shift envelope below | base `E0 6C / E0 F0 6C`, plus envelope |
| Fn+Up | PgUp | `E0 49 / E0 C9`, plus envelope | `E0 7D / E0 F0 7D`, plus envelope |
| Fn+Down | PgDn | `E0 51 / E0 D1`, plus envelope | `E0 7A / E0 F0 7A`, plus envelope |
| Fn+Right | End | `E0 4F / E0 CF`, plus envelope | `E0 69 / E0 F0 69`, plus envelope |

Ctrl+Scroll Lock produces Break (TR 3-26; Operations 4-7). The scan tables do not actually print its special sequence despite stating this exception to ordinary make/break. Enhanced-keyboard `E0 46 E0 C6` / `E0 7E E0 F0 7E` is a **BASELINE candidate**, not a measured 7690 sequence. Ctrl+Alt+Del is a BIOS/OS reset combination, not a physical reset pin generated by the emulator. Operations 4-6 says Shift+PrtSc prints the screen; preserve that distinction from unshifted asterisk.

## 5. Embedded keypad and artificial Shift

**DOCUMENTED, image checked:** TR 3-4–3-5 and Figures 3-9–3-14, 3-18–3-19 / PDF 79, 86–88, 90.

Internal Num toggles on each Fn+Num function and synchronizes to `ED` bit 1 only when that command arrives. The keyboard tracks real left/right Shift and artificial left/right Shift; update a real Shift status only when its real scan has actually entered the FIFO. BIOS BDA flags are not this local state.

### Numeric overlay base codes

| Position | Keypad output | Set 1 | Set 2 |
|---|---:|---|---|
| 52 M | 0 | 52 | 70 |
| 37 J | 1 | 4F | 69 |
| 38 K | 2 | 50 | 72 |
| 39 L | 3 | 51 | 7A |
| 23 U | 4 | 4B | 6B |
| 24 I | 5 | 4C | 73 |
| 25 O | 6 | 4D | 74 |
| 8 Digit7 | 7 | 47 | 6C |
| 9 Digit8 | 8 | 48 | 75 |
| 10 Digit9 | 9 | 49 | 7D |
| 54 Period | decimal | 53 | 71 |
| 12 Minus | minus | 4A | 7B |
| 13 Equal | plus | 4E | **69 as printed in Fig. 3-10; OPEN** |
| 55 Slash | divide | E0 35 | E0 4A |
| 57 Asterisk | multiply | 37 | 7C |

Figure 3-10 prints `69` for keypad plus, which duplicates keypad 1. The enhanced-keyboard baseline value is `79`. Figure 3-9 also prints `37/B7` as key 13's ordinary equals scan where Figure 3-4 and barcode Figure 3-15 print `0D/8D`. Figure 3-9 prints `4B` instead of `47` for key 8 in two wrapped modes. These are **visible source conflicts**, not OCR cleanup opportunities. The base table uses the corroborated `0D`; keypad 7 uses the corroborated unwrapped `47`; exact controller behavior for those conflicting cells needs binary/physical evidence. Never silently describe a repaired table as a direct transcription.

For the numeric digit/decimal rows, the table's four cases can be represented without duplicating every sequence:

| Case | Set-1 make / break using keypad code K | Set-2 make / break |
|---|---|---|
| Num off, Fn off | ordinary physical-key scans | ordinary physical-key scans |
| Num off, Fn on, no Shift | `2A K AA / 2A (K OR 80h) AA` | `12 K F0 12 / 12 F0 K F0 12` |
| Num on, Shift on | `AA K 2A / AA (K OR 80h) 2A` | `F0 12 K 12 / F0 12 F0 K 12` |
| Num on without Shift, or Fn+Shift as tabulated | `K / (K OR 80h)` | `K / F0 K` |

These keypad wrappers are **not `E0`-prefixed**. Do not reuse the cursor wrapper verbatim. The source's keypad table uses left-Shift envelopes; its explicit right/both-Shift substitution footnote belongs to the cursor tables. Applying that footnote wholesale to keypad combinations is an inference requiring confirmation.

Minus and plus use keypad codes in all overlay columns without the digit wrappers. Enter is extended only in the Fn column; Num+Shift and the Num-mode/Fn+Shift column show ordinary Enter. Slash uses extended divide for Fn and the Num-mode column; its Num+Shift make is `E0 AA E0 35`, break `E0 2A E0 B5` in set 1, and `E0 F0 12 E0 4A / E0 F0 4A E0 12` in set 2. Preserve the differing order actually printed rather than normalizing the two tables silently. Asterisk's Num+Shift column is `E0 37 / E0 B7` or `E0 7C / E0 F0 7C`; other shown columns retain ordinary multiply.

### Dedicated cursor/page keys

Let `Cmake/Cbreak` be the full extended base sequence from the physical/Fn table. These rules apply to Left/Up/Down/Right/Home/PgUp/PgDn/End and Insert/Delete:

| Num | Physical Shift | Make | Break |
|---:|---:|---|---|
| 0 | 0 | `Cmake` | `Cbreak` |
| 1 | 1 | `Cmake` | `Cbreak` |
| 0 | 1 | artificial extended Shift break(s), then `Cmake` | `Cbreak`, then artificial extended Shift make(s) restoring real state |
| 1 | 0 | artificial extended left-Shift make, then `Cmake` | `Cbreak`, then artificial extended left-Shift break |

Extended Shift forms: set 1 left=`E0 2A`/`E0 AA`, right=`E0 36`/`E0 B6`; set 2 left=`E0 12`/`E0 F0 12`, right=`E0 59`/`E0 F0 59`. If both real Shifts are down, both sets envelop the cursor scans; the exact relative order of the two envelopes is not specified. Fn chooses the page/home/end base before applying these rules. It does not turn the dedicated arrows into unprefixed numeric-keypad events.

Example with Num on, no real Shift: Left make=`E0 2A E0 4B`, release=`E0 CB E0 AA`. With Num off and left Shift held: Left make=`E0 AA E0 4B`, release=`E0 CB E0 2A`. Repeats send only `E0 4B`. If another key arrives while an artificial Shift is in force, reconcile the transmitted state before that key; if real Shift is released while a dependent key repeats, send the real break and establish the artificial Shift needed by the repeating key. A stateless table lookup per host event cannot satisfy this rollover contract.

## 6. Barcode characters are synthesized keyboard input

**DOCUMENTED, image checked:** TR 3-24–3-25 / PDF 89. Barcode programming belongs to [PERIPHERALS.md](PERIPHERALS.md); this section owns the final ASCII-to-keyboard boundary.

Use the US base positions above, **not the Num-overlaid meaning of those physical positions**. Barcode `7` means ordinary digit-7 scans, not a keypad Home event because Num changed. Printable punctuation pairs are:

| Base character | Shifted character | Physical position |
|---|---|---|
| grave | tilde | 1 |
| `1 2 3 4 5 6 7 8 9 0` | `! @ # $ % ^ & * ( )` | 2–11 |
| minus, equals | underscore, plus | 12, 13 |
| backslash | vertical bar | 14 |
| left bracket, right bracket | left brace, right brace | 27, 28 |
| semicolon, apostrophe | colon, double quote | 40, 41 |
| comma, period, slash | less-than, greater-than, question mark | 53, 54, 55 |

Space is key 61. Letters use their alphabetic positions. Each character gets a complete make/break pair; shifted punctuation additionally gets an ordinary Shift envelope. The manual's explicit set-1 example is barcode `!` → **`2A 02 82 AA`**. In set 2 the corresponding documented construction yields `12 16 F0 16 F0 12`.

The controller compensates when Caps Lock or a held Shift would change a lower-case barcode character. Consequently host-held modifiers must not corrupt scanned patient/record identifiers. Keep barcode-generated Shift changes separate from host-owned switches and restore the preexisting state. The table prints uppercase letter legends as position names; it is not authority for turning all alphabetic scan data uppercase.

**OPEN:** the tables omit raw mappings for many ASCII controls and do not specify Ctrl/Alt compensation, simultaneous human/barcode arbitration, exact synthetic-modifier coalescing, or character pacing across the 17-byte keyboard FIFO. Header/trailer commands explicitly permit ESC, XON, and XOFF and default trailer CR, so the actual controller necessarily has more behavior than the printable map. Implementing arbitrary ASCII by injecting DOS characters would conceal this missing hardware behavior; obtain controller firmware or capture before claiming full raw fidelity. At the application interface, the documented CR must end a default successful barcode message.

## 7. Host mapping, indicators, and downstream acceptance

Use physical host codes, not host Unicode text. Expose a configurable dedicated 7690 Fn binding; host Right Alt must remain key 62 rather than silently becoming Fn. Optional convenience bindings for F11/F12/Home/End/Pause should schedule the documented physical chords, including releases, not bypass the microcontroller. Distinguish left/right Shift. Ignore host-generated autorepeat and use emulated time. On focus loss, release host-owned keys through the same physical state machine; do not clear guest BDA flags directly.

Only US keycaps are documented. Host text-paste requires deliberate US-key synthesis and must accept the FIFO/backpressure limits. A debug raw-byte injection facility, if provided, should be visibly separate from physical-key input and must still exercise planar receive/IRQ handling.

Keyboard lights are controller outputs, not a UI mirror of host lock lights. Screen blanking adds another layer: TR 7-5 / PDF 144 says the backlight-control BIOS call preserves lit indicators; if all were off it turns Scroll Lock's indicator on, then restores original indicators when unblanking. That does not justify changing host Scroll Lock or changing the application's logical Scroll Lock state. The real BIOS should own its command sequence; see [VIDEO.md](VIDEO.md) and [PERIPHERALS.md](PERIPHERALS.md).

The supplied touch driver adds keyboard-dependent gestures and mouse-button mappings above this hardware path. See [DRIVER_ABI.md](DRIVER_ABI.md) and [TOUCH.md](TOUCH.md) for version-specific binary evidence: the driver uses aggregate BIOS Ctrl/Alt state for its mouse mappings despite left-side wording in the manual, while right Shift participates in LCD gestures. Do not implement those mappings inside the physical keyboard controller or reinterpret host modifiers before the BIOS sees them.

The [Operations text](../DOCUMENTATION/OCR/OPERATIONS.txt) printed 4-4–4-9 / PDF 31–33 supplies user semantics: Fn+Num toggles blue keypad overlay; Ctrl+Num pauses, Ctrl+Scroll breaks, Ctrl+Alt+Del restarts; Fn+Ctrl is right Control. Function-key actions belong to applications. TR 7-6 recommends an application-defined blanking hotkey but assigns **no universal hardware chord**.

These are future acceptance paths, not claimed emulator test results:

1. **Cold keyboard enumeration:** serial BAT `AA`, host scan-set setup, Read ID `FA AB 84`; no 8042 accesses or second PIC needed. Missing external cable fails independently of internal keyboard presence.
2. **Raw versus BIOS path:** press/release A; observe set-1 `1E 9E` in the selected serial source, INT `71h`, compatibility latch, then the ordinary handler and INT `16h` result. Mask IRQ1, verify pending data does not become a direct BIOS character.
3. **Set switching:** select set 2 and observe A `1C F0 1C`; return set 1 without a hidden controller translation. Interruption of a pending `F0` command leaves the old set but discards already-cleared queued input.
4. **FIFO boundary:** with transmission inhibited, queue 16 bytes, then another event; receive the existing bytes followed by `FF`, not a partial extended sequence. A held repeated key under inhibition contributes only its first make.
5. **Repeat transition:** hold one key, then another; only the newer repeats. Releasing newer does not resume older. LED Num synchronization does not rewrite the current repeat sequence prematurely.
6. **Modifier restoration:** hold left, right, and both Shift variants through arrow/Fn-page combinations with Num both off and on; type an alphabetic key while the arrow repeats, then release Shift. No stuck artificial shift or misplaced `E0` prefixes.
7. **Overlay versus barcode:** enable Num, type physical J (keypad 1), scan barcode containing J (letter), verify separate paths; scan lower-case text under Caps and held Shift, and preserve physical state afterward.
8. **Command error:** bad host parity requests `FE`; RESEND resends the previous non-RESEND output; a new command aborting an ACK does not replay that obsolete ACK later.
9. **Power/backlight:** unplug primary power with switch on and backup available; keyboard remains operational while LCD and touch/diskette stop. BIOS blanking maintains an on-indicator without inventing a hardware inactivity timer.

### Remaining acquisition targets

The manual is rich enough for a documented-behavior keyboard model, but not an exact reproduction of every controller edge. Obtain the keyboard MCU ROM or a logic-analyzer trace to resolve: scan-set query return encoding/order; reset pulse timing; typematic table/formula discrepancies; keypad-plus and other conflicting scan cells; Ctrl+Break bytes; unmodified Num behavior; unsupported key-type parameter handling; control-character barcode synthesis; overlapping scan/response/gateway arbitration; and serial acknowledgement/rearm edges on the actual 7690 planar. These are bounded evidence gaps, not invitations to substitute AT or Convertible state.
