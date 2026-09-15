# Peripherals: barcode gateway, communications, sound, and power

## Scope and evidence

This chapter specifies the 7690's barcode wand/card reader, integrated serial and parallel ports, beeper/earphone path, ride-through power, and the operational dependencies between them. The CPU and interrupt-controller foundation belongs to [MODEL25.md](MODEL25.md); keyboard scan generation to [KEYBOARD.md](KEYBOARD.md); diskette mechanics to [STORAGE.md](STORAGE.md); LCD control to [VIDEO.md](VIDEO.md); shared interface-adapter latches to [TOUCH.md](TOUCH.md).

The machine is an **8086 Model-25-derived workstation**, not an AT or Micro Channel machine. An internal serial link in the barcode electronics does **not** make the barcode reader COM1. Serial COM1, the keyboard serial interface, and the barcode-controller-to-keyboard serial link are three separate channels.

### Evidence index

Unless explicitly qualified, contracts below are **DOCUMENTED** in the supplied [Technical Reference](../IBM_7690_Clinical_Workstation_Technical_Reference.pdf). The [searchable text](../DOCUMENTATION/OCR/TECHREF.txt) helps locate passages but is not numeric authority.

| Subject | Printed pages | Physical PDF pages | Text locator |
|---|---|---|---|
| Planar enables, PIT, system ports, IRQ assignments | 1-8–1-15 | 13–16 | lines 528–750 |
| Serial port | 1-107–1-121 | 62–69 | lines 3164–3585 |
| Parallel port | 1-122–1-125 | 70–71 | lines 3586–3723 |
| Beeper and earphone | 1-126 | 72 | lines 3724–3776 |
| Power supply | 2-2–2-5 | 75–76 | lines 3864–3946 |
| Barcode hardware and full programming interface | 4-2–4-16 | 92–99 | lines 4798–5211 |
| Adapter sense ports | 5-2–5-3 | 100 | lines 5226–5280 |
| AC-loss sense, blanking, indicator restoration | 7-4–7-6 | 144–145 | section heading locators near end of text |

**Image checked for this chapter:** PDF 13–15, 63–73, 75–76, 92–98, 100, and 144. These are two-page spreads: PDF 98 contains printed 4-14 and 4-15, for example. Barcode header/trailer lengths, masks, status nibbles, the `11BAh` extension, UART/parallel bits, rail polarity, and significant contradictory printed values were checked against rendered pages rather than OCR.

**BINARY:** no barcode-controller or system BIOS ROM execution is claimed here. **INFERENCE** marks a design deduction or Model 25/8250 baseline assumption. **OPEN** marks details for which the supplied evidence does not define exact behavior. The actual binary investigation of supplied diagnostics and touch drivers is in [DIAGNOSTICS.md](DIAGNOSTICS.md) and [DRIVER_ABI.md](DRIVER_ABI.md); their observations must not be promoted into an authentic 7690 ROM dump.

## 1. Barcode feature: the complete route

The optional feature is **Feature 0001, IBM part 49F6178** (Operations printed 2-13 and 4-13). It comprises a wand and its holder, which doubles as a card-reader slot. It is not a magnetic-stripe reader or independent card-reader protocol: the card's **barcode faces down**, and the operator passes it through the holder in one continuous motion. Removing the wand permits scanning ordinary labels. The tip touches the medium, preferably at a slight angle; ordinary supported labels can be scanned in either direction. See [Operations text](../DOCUMENTATION/OCR/OPERATIONS.txt), printed 4-13–4-14 / PDF 35–36, lines 1566–1628.

The electronics route is:

1. The wand produces TTL bar/light transitions.
2. A **40-pin barcode-controller IC plus 1K×8 RAM** measures widths and decodes the symbology to ASCII.
3. Its full-duplex internal serial link sends ASCII to the keyboard microcontroller.
4. That microcontroller creates US enhanced-keyboard make/break sequences and merges them with human keyboard input.
5. The external keyboard jumper cable carries the combined stream to the system-board keyboard controller.
6. The system's shared IRQ1/INT `71h` path leads to ordinary keyboard services and applications.

A default successful read is barcode data followed by **one carriage return `0Dh`**. Applications distinguish a scan from human typing by configuring a unique header and/or trailer, not by polling a separate UART receive register. Do not bypass scan translation by depositing text directly in DOS or the BIOS character buffer.

### Optical/electrical input

TR 4-2–4-4 / PDF 92–93:

- One TTL input bit: **1 is a dark bar, 0 a light bar**.
- Narrowest bar pulse must be **greater than 150 µs**; widest bar pulse must be **less than 70 ms**. These are strict inequalities as printed, not a complete decoder tolerance model.
- Minimum contrast ratio **45%**; tilt between vertical and **45°**.
- Internal barcode-to-keyboard serial link: **2400 baud, odd parity, one stop bit**. The status encoding explicitly depicts bit 7 as parity and seven ASCII data bits. Do not conflate that internal ASCII representation with the keyboard's 8-data-bit/odd-parity mode-2 frame. The link's general word-length configuration is not separately stated in its three-item parameter list.

Wand connector assignments (Figure 4-1):

| Pin | Signal |
|---:|---|
| 1 | Scanner synchronization |
| 2 | Barcode data |
| 3 | +LED Read OK |
| 4 | Scanner-type sense; wand = floating |
| 5 | Scanner trigger |
| 6 | 5-V scanner enable |
| 7 | +5 V |
| 8 | Ground |

The controller pinout exposes `-CTS` pin 4, `-RTS` pin 5, `-Laser Scan Enable` pin 6, `-Laser/+Wand Input` pin 7, `-Laser Trigger` pin 8, reset pin 9, RxD from keyboard pin 10, TxD to keyboard pin 11, scanner-data input pin 12, laser-sync pin 13, LED output pin 14, and beeper output pin 15. Figure 4-2 does not supply a CPU port for those pins. Nor does the presence of a beeper-output pin override the explicit application-owned successful-read sound described below. The diagram prints both terminator-select pins 25 and 26 as `TR0`; do not infer their missing second designation or strap values.

POST performs a barcode-controller presence test. The feature can be absent while the keyboard works normally. A connected wand does not prove a functioning controller; an installed controller does not prove a clean readable label. Preserve these distinctions in configuration and diagnostics.

### Supported labels

The controller automatically recognizes:

- Code 39, citing ANSI MH10.8M-1983 and MIL-STD-1189;
- Interleaved 2 of 5, citing ANSI MH10.8M-1983;
- UPC/EAN/JAN;
- Standard Codabar (NM7);
- Code 128.

All five families are enabled initially. Code 39 full-ASCII conversion and optional check-character verification are initially disabled. UPC/EAN/JAN supplemental codes are initially disabled.

Two- and five-digit supplements are supported for **UPC-A, UPC-E, EAN/JAN-13, EAN/JAN-8**. With supplements, the scan must be forward and the supplemental digits must be scanned **last**. Reverse reading of ordinary symbols does not imply reverse reading of supplemental symbols.

A label-level emulator input should therefore contain at least symbology, encoded payload, scan direction, optional supplement, and a way to represent a failed/invalid read. Passing only an arbitrary string cannot exercise symbology-disable masks, check characters, length rules, or direction constraints. This is an **INFERENCE for host API design**, not a historical firmware API. A separate waveform input mode can exercise raw bar widths; do not claim optical decoding fidelity if only predecoded labels are supported.

## 2. Barcode programming ABI and gateway grammar

**DOCUMENTED, image checked:** TR 4-5–4-7 / PDF 93–94.

Issue:

```asm
mov ax,11BAh
mov bh,05h
; ES:DI -> complete binary command string
; CX    -> byte length, including gateway markers
int 10h
; AH=BAh means this extension is supported
```

The string is length-delimited, **not NUL-terminated**; its closing marker contains a zero byte. The BIOS passes instructions through the keyboard controller to the barcode controller. `AH=BAh` documents recognition/support of the BIOS function, **not** a decoded-label success, controller checksum result, or a specified command-error code. No carry-flag success/error contract is given here. An emulator running real ROM should implement the underlying hardware rather than trap this INT solely to make sample programs appear to work.

Ordinary programming string:

```text
F0 04  1B 2D 79  <ASCII decimal n><operator> ... <ASCII decimal n><FINAL OPERATOR>  F0 00
```

- `F0 04`: begin-command marker; opens the keyboard-to-barcode gateway.
- `1B`: ESC.
- `2D 79`: literal ASCII `-y`.
- Operand n: one or two **decimal ASCII digits**, not an immediate binary mask and not a hexadecimal string.
- Each ordinary command is `<n><letter>`.
- Intermediate letters are lowercase; **the last operator is uppercase**.
- One `ESC - y` prefix suffices for a concatenated sequence.
- No spaces in the command syntax. Counted header/trailer payload is an explicit exception and can contain spaces.
- `F0 00`: end marker; closes the gateway.

The printed manual calls `-` both `2Dh` and decimal 47. ASCII `2Dh` is decimal **45**; the glyph, hexadecimal value, and sample sequences agree. Use byte `2D`, not decimal 47 (`/`). This is a visible source typo, not an emulator alias.

Example from TR 4-6–4-7: enable only Code 39 and enable its check verification:

```text
F0 04 1B 2D 79 31 66 31 47 F0 00
                 1  f  1  G
```

This is eleven bytes. The `F` operand is an **enable selection**, despite the heading “Disabling Support”; `1F` selects Code 39 and excludes the other families. Do not invert it into a disable mask.

### Parser/state ownership

A useful implementation separates the keyboard gateway state from the barcode escape parser:

- Keyboard owns `normal`, `F0-option-pending`, and `barcode-gateway-open` contexts, plus ordinary scan-set commands.
- Barcode controller owns escape prefix recognition, decimal operand accumulation, operator dispatch, counted text consumption, decoder options, header/trailer storage, pacing permission, pending decoded output, status, and reset interval.
- The BIOS owns iteration over ES:DI/CX and its own interrupt/command-handshake strategy.

`F0 00` is a scan-set query in ordinary keyboard-command context but gateway close in the barcode transaction. `F0 04` is a 7690 extension, not ordinary scan set 4. Preserve context before dispatching generic enhanced-keyboard commands.

**OPEN:** the manual does not specify ACK cadence for every gateway byte, malformed escape recovery, how command fragments span separate BIOS calls, a timeout for an unterminated gateway, nor rollback/commit behavior when a concatenated command fails partway through. Do not invent an AT ACK after each ASCII byte or silently make the command atomic. The documented valid grammar and effects below are the implementation contract; malformed-stream behavior needs keyboard/controller firmware or capture.

## 3. Complete barcode command catalog

All masks and operands in this section are **decimal values encoded as ASCII digits**. Every ordinary command has `F0 04 ESC - y` before it and `F0 00` after it unless concatenated as described above.

### F — complete family selection

`<n>F`, TR 4-7 / PDF 94:

| Decimal weight | Family enabled when selected |
|---:|---|
| 1 | Code 39 |
| 2 | Interleaved 2 of 5 |
| 4 | UPC/EAN |
| 8 | Codabar |
| 16 | Code 128 |

Sum enabled families; omitted families are disabled. The initial selection enables all five (equivalent mask **31**, a deduction from the explicit all-enabled default and table). `0F` selects none. This command's Interleaved-2-of-5 bit is **2**, unlike command C's bit **4**.

### C — industrial selection plus extended Code 39

`<n>C`, TR 4-7–4-8 / PDF 94–95:

| Decimal weight | Selection |
|---:|---|
| 1 | Code 39 |
| 2 | Code 39 full-ASCII conversion modifier |
| 4 | Interleaved 2 of 5 |
| 8 | Codabar |
| 16 | Code 128 |

The explicit supported-selection table is `0,1,3,4,5,7,8,9,11,12,13,15,16,17,19,20,21,23,24,25,27,28,29,31`. This is all combinations with **weight 2 (bit 1)** used only together with weight 1: extended Code 39 is **3**, not standalone **2**. The bit is a conversion option, not a sixth barcode family. Other listed family weights combine naturally. Initial industrial selection enables all industrial families without full ASCII (equivalent **29**).

### U — UPC/EAN/JAN selection and supplements

`<n>U`, TR 4-9 / PDF 95:

| Weight | Meaning |
|---:|---|
| 1 | UPC/EAN/JAN enabled, no supplements |
| 2 | UPC-only option, no supplements |
| 4 | Two-digit supplement option |
| 8 | Five-digit supplement option |

The manual's complete realized-options table:

| n | Result |
|---:|---|
| 1 | UPC/EAN/JAN, no supplements; default |
| 2 | UPC only, no supplements |
| 5 | UPC/EAN/JAN plus two digits |
| 7 | UPC only plus two digits |
| 9 | UPC/EAN/JAN plus five digits |
| 11 | UPC only plus five digits |
| 13 | UPC/EAN/JAN plus either two or five digits |
| 15 | UPC only plus either two or five digits |

Notice the source's special **2** no-supplement UPC-only row, whereas supplemented UPC-only rows include weight 1 as well (7/11/15). Do not “correct” 7 to 6 or assume every unlisted mask is equivalent. Exact behavior for unlisted n values remains OPEN. Direction constraints still apply after supplements are enabled.

### G — check-character verification/transmission

`<n>G`, TR 4-10 / PDF 96:

| Weight | Meaning |
|---:|---|
| 1 | Verify Code 39 check character |
| 2 | Verify Interleaved 2 of 5 check character |
| 8 | Transmit check character |

Verification disabled is the documented default. When verification is enabled, **only labels containing valid check characters can be read**. Check-character transmission is independently selectable; do not always strip it or always append it. No weight 4 is defined. The chapter names barcode standards but does not reproduce every checksum algorithm or define whether a status “valid” bit is updated by a rejected scan; those are distinct acquisition requirements for a full optical decoder.

### H — decoding-option selection

`<n>H`, TR 4-10 / PDF 96:

| Weight | Meaning |
|---:|---|
| 1 | Code 39 full ASCII conversion |
| 2 | Suppress Codabar start/stop characters |
| 4 | UPC-only restriction |
| 8 | UPC/EAN two-digit supplements |
| 16 | UPC/EAN five-digit supplements |

All these options are disabled initially. C/H and U/H are overlapping ways to program the same conceptual options, not evidence for two independent decoders with contradictory state. **INFERENCE:** store one canonical full-ASCII flag, UPC restriction, and supplement selection, with commands updating the appropriate fields in command order. **OPEN:** which unrelated fields are preserved by each overlapping command and what a subsequent F selection resets are not fully defined by the prose. Do not advertise a measured last-writer policy for an untested combination.

### M — Interleaved-2-of-5 label length

`<n>M`, TR 4-11 / PDF 96. OCR loses the operator in the surrounding text; the image explicitly prints **M**.

| n | Accepted label length |
|---:|---|
| 0 | Any even length from **4 through 32 inclusive**; default |
| 3–32 | Exactly n digits, rounding an odd requested n upward to the next even integer |
| 33 | Either **6 or 14 digits** |

Examples: `3M` and `4M` both request length 4; `31M` requests 32; `33M` is not a request for 34. Operands 1, 2, and above 33 have no defined effect here. The chapter does not unambiguously say whether a verified-but-suppressed check digit contributes to the requested length; capture that interaction before claiming complete conformance.

### N and O — counted header and trailer

`<n>N<text>` sets header; `<n>O<text>` sets trailer. TR 4-12 / PDF 97.

- n is **0–10 characters**.
- Consume exactly n ASCII payload bytes after the operator. Their interpretation is data, not command syntax.
- Payload may contain **blank, ESC, XON, XOFF**. Therefore an ESC in a counted field does not automatically start a new escape sequence.
- Header default: absent.
- Trailer default: **one CR, `0Dh`**.
- The manual says a carriage return **must always be the last character in the trailer text**.

The allowed count 0 and the requirement for a final CR are not reconciled in the manual for `0O`. Keep that case OPEN; do not infer that it disables the mandatory record terminator. For defined nonempty trailers include CR in the count. A ten-character trailer has space for at most nine other bytes before its final CR.

Example header `BC:`:

```text
F0 04 1B 2D 79 33 4E 42 43 3A F0 00
```

Example trailer `!` followed by CR:

```text
F0 04 1B 2D 79 32 4F 21 0D F0 00
```

Do not parse either string as NUL-terminated. Do not append a second default CR after a complete configured trailer. A status response is separately specified below; the manual does not state that configured read-message headers/trailers wrap status reports.

### J and K — single-read pacing

`0J` disables single-read mode; `1J` enables it. Default is disabled. **Enabling immediately closes permission for the first read**: a subsequent Next Read command is required even before the first label.

`0K` and `1K` both allow the next barcode read. They are identical in the printed contract; 0 is not a revoke command.

A minimal **INFERENCE state model** consistent with TR 4-13–4-14 / PDF 97–98 is:

| State/event | Transition |
|---|---|
| Continuous + `1J` | Single-read, disarmed |
| Single-read + `0K` or `1K` | Single-read, armed |
| Armed + accepted label | Emit one read message; disarm |
| Disarmed + attempted label | No read message |
| Any pacing state + `0J` | Continuous |
| Reset | Initial continuous state |

“Next read” is permission, not a documented accumulating credit counter. Repeated K commands before a label must not be claimed to queue unlimited scan credits. Whether an invalid attempted label consumes permission, and whether a scan attempted while disarmed is ignored or internally retained, are OPEN; the contract guarantees no extra transmission before permission, not the optical sampling implementation.

### S — request status

`1S` requests status. No other operand is documented. The controller returns a **seven-character** message:

```text
ESC  backslash  Vhigh  Vlow  LastFamily  OtherStatus  CR
1B      5C       ...    ...     ...         ...     0D
```

For the four status-bearing characters, bits 6–4 are `011`, bits 3–0 carry the nibble, and the internal serial diagram shows bit 7 as parity. Thus after removing parity, each is in **`30h`–`3Fh`**, with nibble values A–F represented by punctuation `: ; < = > ?`, **not ASCII A–F**. An application decodes with `character & 0Fh`, not a decimal-only parser.

| Character position (1-based) | Data |
|---:|---|
| 1 | ESC `1B` |
| 2 | Backslash `5C` |
| 3 | Software-version upper nibble in low nibble |
| 4 | Software-version lower nibble in low nibble |
| 5 | Low bit 0 Code 39 last read; bit 1 Interleaved 2 of 5; bit 2 UPC/EAN/JAN; bit 3 Codabar |
| 6 | Low bit 0 Code 128 last read; bit 1 unused; bit 2 last check character valid; bit 3 scanner type, **0 moving beam / 1 fixed beam** |
| 7 | CR `0D` |

The actual controller software-version byte and pre-first-read last-family/check state are **OPEN**; do not invent a version such as 1.00 because the diagnostics disk has a version label. F301 bit 3's wand/scanner sense is related physical evidence but is a separate register and must not be confused with character 6 bit 3's status encoding.

The return travels through the keyboard data stream, not an ES:DI output buffer or a COM1 receive FIFO. Observe application-visible ESC/backslash/status/CR after keyboard synthesis. No extra ASCII ACK or success string is specified.

### E — controller reset, outside the `-y` grammar

Reset string is exactly:

```text
F0 04 1B 45 F0 00
```

That is `begin ESC E end`, **not `ESC-y0E`**. It restores initial power-up conditions, clears buffers, and performs self-test. The reader is inoperative for **approximately one second**. Keyboard Reset `FFh` also resets this microcontroller (TR 3-8), whereas the barcode-reset command is not documented to reset the whole keyboard or machine.

Do not automatically send a successful read beep on reset completion. Failed-controller self-test response bytes are not specified by this chapter.

## 4. Barcode errors, operator feedback, and executable boundaries

TR 4-16 explicitly makes positive operator feedback **the application's responsibility**: configure unique framing, watch the keyboard stream, then sound a tone when a complete read is recognized. An emulator-wide unconditional host beep when a label is supplied would mask broken framing, a disabled code family, or lost keyboard bytes.

Operations printed 3-7 / PDF 27 distinguishes:

- **9021 — Bar Code Feature:** controller/logic kit appears absent; newly installed feature requires correct installation.
- **9022 — Bar Code Read Error:** check cable, clean wand tip, inspect barcode quality.

These are diagnostic/application messages, **not** wire bytes `21h`/`22h` or invented UART error flags. A rejected checksum/length/type should not become ordinary valid text merely because the host UI passed in a string. Exactly what diagnostic issues each visible error is owned by [DIAGNOSTICS.md](DIAGNOSTICS.md).

A complete implementation separates:

1. **Documented programming compatibility:** valid BIOS strings update controller state, pacing, framing, and status.
2. **Keyboard-stream fidelity:** ASCII becomes modifier-safe raw scans, respecting buffering and handshakes; see [KEYBOARD.md](KEYBOARD.md).
3. **Optical-decoder fidelity:** widths, quiet zones, direction, contrast, code/check rules and rejected scans. A predecoded-label facility does not prove this layer.

The manual does not expose the controller RAM map, identify its exact firmware version, publish all recognition thresholds, or define every invalid command. Those are bounded evidence gaps; a framework that accepts all labels and ignores programming masks is not an implementation of the documented feature.

## 5. Integrated serial port: COM1, not the barcode link

**DOCUMENTED, image checked:** TR 1-107–1-121 / PDF 62–69. COM1 decodes **`3F8h`–`3FFh`** and uses **IRQ4**. The serial chip select is enabled by **port `65h` bit 4**. The 7690 system board's `65h` bit 0 is reserved, unlike fixed-disk assumptions inherited from other machines.

The UART has an 8250-style register contract with double buffering (holding/buffer register plus shift register), not a 16550 FIFO. IIR bits 7–3 are zero; no FIFO-enable/control register is documented at `3FAh`. It adds/removes start, parity and stop bits; data is LSB first. TR introduction describes programmable operation from 50 to 9600 baud; the divisor hardware has a broader mathematical range, not a promise that every external connection supports it.

### Register map and aliases

| Port | DLAB | Read | Write |
|---|---:|---|---|
| `3F8` | 0 | RBR, received byte | THR, next transmitted byte |
| `3F8` | 1 | DLL, divisor low | DLL |
| `3F9` | 0 | IER | IER |
| `3F9` | 1 | DLM, divisor high | DLM |
| `3FA` | either | IIR | No ordinary write register documented |
| `3FB` | either | LCR | LCR |
| `3FC` | either | MCR | MCR |
| `3FD` | either | LSR | Diagnostic status injection described below |
| `3FE` | either | MSR | Diagnostic status injection described below |
| `3FF` | either | Scratch byte | Scratch byte |

DLAB is LCR bit 7. Changing it alters only the aliases at offsets 0/1. A DLL write is not transmitted data, and an RBR read while DLAB=1 must not consume a pending character.

### IER and IIR: two levels of interrupt acknowledgement

IER bits 7–4 reserved zero; bit 3 modem status enable, bit 2 receiver-line-status enable, bit 1 THR-empty enable, bit 0 received-data-available enable. Clearing all four suppresses UART interrupts **without disabling receive/transmit or status accumulation**.

IIR bit 0 is **1 when no interrupt is pending**. With bit 0 zero, bits 2–1 identify highest pending priority; bits 7–3 are zero:

| IIR value | Priority | Cause | UART-side clearing action |
|---|---:|---|---|
| `06` | Highest | Receiver overrun/parity/framing/break | Read LSR |
| `04` | 2 | RBR contains data | Read RBR |
| `02` | 3 | THR empty | Read IIR for this cause, or write THR |
| `00` | Lowest | Modem input change/delta | Read MSR |
| `01` | None | No enabled cause | No source to clear |

Reading IIR is **not** universal acknowledgement: it does not consume RBR or clear modem deltas. PIC EOI is also not UART acknowledgement. Preserve pending causes while IRQ4 is masked, and present the next eligible cause after the current one is serviced. The source prose says IIR freezes identification of the highest pending interrupt during selection/service; do not let unrelated host-thread updates produce a torn cause/status observation.

MCR bit 3 controls **OUT2, the system interrupt gate** (TR 1-120). Thus UART cause, IER enable, OUT2 gate, and PIC IRQ4 mask are separate state. A shortcut `if IER != 0: raise_irq4()` cannot represent these combinations. The exact gate-array edge capture is part of the central interrupt model, not a reason to synthesize INT `0Ch` directly.

### LCR: character format

| Bit(s) | Function |
|---|---|
| 7 | DLAB |
| 6 | Set break: force serial output to spacing/break independent of ordinary transmitted data until cleared |
| 5 | Stick parity, when parity enabled: parity is 0 for even selection, 1 for odd selection |
| 4 | Even parity when 1; odd when 0 |
| 3 | Parity enable |
| 2 | Stop selection: 0=one stop bit; 1=two for word lengths 6–8, **1.5 for five-bit words** |
| 1–0 | `00`=5 data bits, `01`=6, `10`=7, `11`=8 |

Set-break prose uses “inactive” for the forced level; the receive/break definition and EIA table establish continuous spacing as the relevant condition. Do not equate the UART's logic polarity with the external RS-232 voltage sign without the line driver.

### MCR, modem inputs, and loopback

MCR bits 7–5 zero; bit 4 loopback; bit 3 OUT2; bit 2 OUT1; bit 1 RTS; bit 0 DTR. Setting output bits asserts the corresponding active-low chip output. DTR/RTS/OUT1/OUT2 are inactive after master reset.

Loopback (`MCR & 10h`): disconnect external SIN and modem inputs, connect transmit shift output to receive shift input, and use modem outputs as modem inputs. External SOUT is held in its documented active state rather than driving transmitted loopback characters onto the cable. Transmitter, receiver and modem-status interrupts remain operational and IER-controlled.

| MSR bit | Normal input | Loopback source |
|---:|---|---|
| 7 | DCD / RLSD asserted | OUT2, MCR bit 3 |
| 6 | RI asserted | OUT1, MCR bit 2 |
| 5 | DSR asserted | DTR, MCR bit 0 |
| 4 | CTS asserted | RTS, MCR bit 1 |
| 3 | Delta DCD | DCD state change |
| 2 | Trailing-edge RI | RI active→inactive |
| 1 | Delta DSR | DSR state change |
| 0 | Delta CTS | CTS state change |

Reading MSR clears its four delta bits, not the current input levels. A pulse may leave a delta set even if the input returned to its earlier state. TR 1-120 additionally says RI bit 6 changing 0→1 generates an interrupt, which conflicts with the explicitly trailing-edge status definition. Record that as an **OPEN source conflict**, not a justification to discard either edge in a claimed faithful model.

TR 1-116 explicitly allows diagnostic writes to **LSR low six bits** and **MSR low four bits** to exercise interrupts; setting a relevant bit generates its enabled cause. Resetting these synthetic causes uses ordinary acknowledgement rules. Reprogram normal registers before clearing loopback to resume normal operation. A generic UART core that ignores all LSR/MSR writes cannot exercise this documented diagnostic facility.

### LSR and timed data movement

| Bit | Meaning |
|---:|---|
| 7 | Reserved zero |
| 6 | Transmitter empty: **both THR and transmit shift register empty** |
| 5 | THR empty: can accept another character; rises when THR moves into shift register, clears on THR write |
| 4 | Break: receive held spacing longer than a complete configured frame |
| 3 | Framing error: invalid low stop bit |
| 2 | Parity error; clear on LSR read |
| 1 | Overrun error; clear on LSR read |
| 0 | Complete received byte in RBR |

Error bits 1–4 generate receiver-line-status cause when enabled. RBR reading clears received-data availability; LSR reading acknowledges receiver error status. THRE and transmitter-empty must differ while the final character is shifting. Use emulated frame time, not a fixed delay per host socket read.

**Source conflict:** TR 1-117 says an overrun occurs when a new byte enters an unread RBR, “thereby destroying the previous character.” Many generic 8250 models preserve the old RBR and lose the new byte instead. This chapter records the 7690 manual's overwrite description, not a measured silicon result. A claimed exact UART core must settle this with the actual part/diagnostic trace rather than conceal it under “8250-compatible.”

No FIFO depth beyond the documented holding/buffer plus shift registers is established. A host terminal/socket buffer can exist outside the emulated wire, but bytes must enter the receiver at programmed baud/frame timing so guest overrun remains possible.

### Divisor and BIOS boundary

The generator clock is described as **1.84 MHz** and is divided by a 16-bit divisor, then 16 for baud. Loading either divisor byte reloads the baud counter immediately. The prose says divisors 1–65,535; its parenthesized power-of-two expression contains an obvious arithmetic typo. Divisor zero behavior is not specified here.

A standard **BASELINE** clock of 1.8432 MHz yields `baud = 115200/divisor`: 9600→12, 4800→24, 2400→48, 1200→96. This precision is a baseline clock choice, not a 7690 oscillator measurement; TR rounds to 1.84 MHz. Keep both byte latches meaningful and do not quantize all writes to eight BIOS baud values.

TR 6-41–6-45 provides INT `14h`. Standard initialize AH=00 uses DX=zero-based port, AL bits 7–5 baud selector 110/150/300/600/1200/2400/4800/9600, bits 4–3 parity (`x0` none, `01` odd, `11` even), bit 2 stop selection, bits 1–0 word length (documented standard choices 7 and 8). AH returns line status with **bit 7 timeout**, unlike hardware LSR bit 7 which is reserved zero; AL returns modem status. Do not place BIOS timeout in hardware LSR. TR 1-119's example AL=`8Bh`, AH=00 initializes 1200, eight data bits, odd parity, one stop. DX must designate the intended port even though that abbreviated example does not load it.

### External serial connector and voltage states

Figure 1-109 / PDF 69 uses a **25-pin D-shell**, not a modern DE-9:

| Pin | Signal |
|---:|---|
| 2 | Transmit data, output |
| 3 | Receive data, input |
| 4 | RTS, output |
| 5 | CTS, input |
| 6 | DSR, input |
| 7 | Signal ground |
| 8 | RLSD / carrier detect, input |
| 11 | Tied to pin 20 |
| 20 | DTR, output |
| 22 | Ring indicate, input |
| All others | Not connected |

RS-232 spacing/binary 0 is **positive** voltage, +3 to +15 V; marking/binary 1 is **negative**, −3 to −15 V. The −3 to +3 V region and magnitudes beyond 15 V are invalid in the printed table. The +12/−12 rails power EIA line drivers; losing primary rails can make the **external link** inoperative even if some digital logic remains powered. The exact UART-core state during battery operation is not stated; do not infer clean reception from retained RAM alone.

## 6. Integrated parallel port: real data direction and handshakes

**DOCUMENTED, image checked:** TR 1-122–1-125 / PDF 70–71. Parallel port 1 uses `378h` data, `379h` status, `37Ah` control, with IRQ7 available. System-board **`65h` bit 1** enables its chip select; **`65h` bit 7** enables its output drivers. To receive external data, clear `65h` bit 7. Do not replace this with an AT/PS2-style direction bit 5 at `37Ah`, which is reserved here.

| Port | Contract |
|---|---|
| `378` write | Latch eight output data bits. This is **not** automatically a printed character. |
| `378` read | Read data-buffer path; block diagram includes connector wrap/input path. When outputs are disabled, external devices can supply data. Preserve distinction between output latch and sampled external pins. |
| `379` read | Current printer/connector input status, with Busy inversion below. |
| `37A` read/write | Control outputs and their readable state; no FIFO/ECP/EPP register set is documented. |

### Control bits and polarity

| `37Ah` bit | Meaning |
|---:|---|
| 7–5 | Reserved |
| 4 | Enable IRQ7 on `-ACK` transition **active→inactive** (low→high at pin 10) |
| 3 | Select input: 1 selects attached device; connector signal is `-Slct In` |
| 2 | `-Initialize`: 0 asserts device reset; low pulse minimum **50 µs** |
| 1 | Auto linefeed: 1 requests linefeed after printing a line; connector `-Auto FD XT` |
| 0 | Strobe: active pulse clocks data into attached device; connector `-Strobe` |

Control outputs are open collector, pulled up to +5 V by **4.7 kΩ**; sink capability 16 mA at 0.4 V. The conventional connector-level relation is active-low strobe/autofeed/select for set control bits and direct initialize polarity. Distinguish logical asserted state from pin voltage and readback inversion. Actual external overrides on open-collector control pins need resolved-line sampling, not simply echoing the last write if implementing connector-level devices.

Data outputs source **2.6 mA at 2.4 V**, sink **24 mA at 0.5 V**, with **39 Ω** series resistors. These electrical facts justify tri-state/input handling; they do not require an analog circuit simulator for a logical port model.

Strobe active duration is at least **0.5 µs**; data setup and hold are each at least **0.5 µs** before/after it. An attached printer consumes a byte on a valid handshake, not every OUT instruction and not every read of status. A host print sink should buffer accepted bytes after emulated strobe recognition.

### Status bits

| `379h` bit | Interpretation |
|---:|---|
| 7 | `-Busy`: **0 when printer busy**, 1 ready. Busy applies during entry, offline, or error conditions. |
| 6 | `-ACK`: 0 during acknowledgement; current pin state, not a latched “byte printed” flag. |
| 5 | PE: 1 paper end. |
| 4 | Selected: 1 selected. |
| 3 | `-Error`: 0 error. |
| 2–0 | Reserved. |

The sample timing shows an ACK of approximately **5 µs** and separate Busy/data/strobe timing. An ACK rising edge with IRQ enabled requests IRQ7; reading `379h` merely observes current status. PIC EOI clears controller service state, not the external ACK waveform. BIOS does not use IRQ7 for its normal printer service (TR 1-14); direct-I/O software and diagnostics can.

Figure 1-115 connector pins: 1 `-Strobe`; 2–9 D0–D7 bidirectional; 10 `-ACK`; 11 Busy; 12 PE; 13 Selected; 14 `-Auto FD XT`; 15 `-Error`; 16 `-Init`; 17 `-Slct In`; 18–25 ground. A missing printer, an offline printer, paper-end, and a held Busy line are different input states. Do not hardwire all status bits to “ready” to pass a print call.

A deterministic attached-device model can implement busy duration, ACK pulse, selected/paper/error state, init reset, and optional data input. **INFERENCE:** choose printer-specific delays in the attached printer model; they are not universal 7690 timing constants beyond the printed interface minima. Writes while planar chip select is disabled belong to the expansion-channel routing, not to a hidden always-present LPT.

## 7. Beeper, PIT channel 2, and earphone insertion

**DOCUMENTED:** TR 1-9–1-12 and 1-126 / PDF 13–15, 72. The beeper and its approximately **half-watt** driver are on the system board. Sound is controlled through PIT channel 2 plus system-port bits; there is no documented digital audio FIFO or volume register.

| Endpoint | Meaning |
|---|---|
| `42h` | PIT channel-2 count data; channel programming/latching controlled through `43h`. |
| `61h` bit 0 | PIT2 gate; 0 halts channel-2 operation according to system-port description. |
| `61h` bit 1 | Beeper data gate; 1 enables timer output into sound path; 0 forces output zero. |
| `62h` bit 5 | Live PIT2 output status; useful even when beeper sound is gated off. |

TR lists three composable techniques: toggle a direct program-control bit for a pulse train; modulate timer clocking/gating through software; program PIT2 waveform output. Keep output transition timing in emulated time. A host `beep()` API on each port write is not equivalent, and suppressing all sound when bit 0 is zero loses direct program-driven behavior in timer modes whose OUT remains high. Use the actual PIT gate/mode/OUT state and final data gate rather than treating `(port61 & 3)==3` as the entire sound circuit.

**Visible source conflict:** Figure 1-116 on PDF 72 prints channel-2 clock **1.9318 MHz** and Gate 2 controlled by I/O port **bit 1**. The earlier dedicated timer/register descriptions repeatedly specify about **1.19 MHz** and gate **bit 0**, with bit 1 separately gating the beeper data. Use those explicit register definitions; flag the Figure 1-116 row as contradictory. A Model 25 baseline PIT frequency of 1.19318 MHz is an inheritance choice, not a measurement of a 1.9318-MHz 7690 clock. Do not implement both conflicting gate assignments simultaneously.

Bits 4/5 at `61h` control active-low-enable NMI masks, not speaker volume. Preserve them during sound writes. Bits 7–6 and 3–2 are reserved; no XT keyboard-clear bit belongs in this sound port.

The rear earphone jack accepts a **¼-inch audio plug**. Inserting any plug disconnects the internal beeper and routes its output to earphones; the timer continues. Recommended monophonic impedance **15–35 Ω**; some up to **100 Ω** can be acceptable. Drive level is fixed, so sensitivity affects loudness. An emulated jack-insertion event should change routing/muting only; no CPU-visible insertion status is documented. A modern host volume slider is host policy, not guest hardware.

Barcode successful-read tones come from the **application** recognizing received framing. POST error tones come from firmware/diagnostics; neither should be manufactured by the host input facility independently of the guest's PIT/port activity.

## 8. Power: ride-through is not suspend and not an RTC specification

### Supply and rail dependencies

**DOCUMENTED, image checked:** TR 2-2–2-5 / PDF 75–76.

The internal supply is described as single-phase, **60 W**, five-voltage-level. Nominal AC input is **115 V**, range **90–137 V**, maximum **2.0 A**. Its introductory prose gives +5 V at 7.0 A, +12 V at 1.6 A, −12 V at 300 mA, and −22.3 V at 70 mA. The adjacent output table differs:

| Rail | Table min/max load | Regulation tolerance | Ripple |
|---|---|---|---|
| +5 V | 1.5 / 7.0 A | +5% / −3% | 100 mV peak-to-peak |
| +12 V | 0.12 / **1.7 A** | +5% / −3% | 120 mV peak-to-peak |
| −12 V | 0.015 / **0.25 A** | +10% / −8% | 120 mV peak-to-peak |

The differing +12/−12 maximum currents are printed source differences; retain both provenance rather than silently selecting a spurious precise limit. They do not define an emulator brownout algorithm under virtual adapter loading.

System board/storage consume approximately 4 A of +5 V, leaving approximately 3 A for expansion. +12 V powers diskette drive and, with −12 V, the EIA serial drivers. +5/+12/−12 are distributed across expansion slots. −22.3 V supports the LCD supply path.

Undervoltage sense values (Figure 2-3) are +5→**+4.5 V**, +12→**+10.8 V**, −12→**−10.2 V**, −22.3→**−21.6 V**. Overcurrent/undervoltage shuts the supply down until corrected; AC input has an external fuse. Do not convert these four values into unrelated guest-readable ADC registers.

### Power-good and LCD rail enable

Power-good resets system logic, indicates proper supply operation, and provides advance warning during turn-off. Normal high is **2.4–5.25 V**; inactive low **0–0.4 V**. It is inactive during under-voltage, power-on and power-off sequences. Turn-on delay is **100–500 ms**; line can sink **2 mA** or source **100 µA**.

The separate **−22.3-V enable** is TTL: **high enables −22.3 V; low causes that output to go to +5 V**, not zero volts. This is essential to LCD dependency modeling. The adapter latch owning the control is specified in [TOUCH.md](TOUCH.md)/[VIDEO.md](VIDEO.md); do not create a second independent `F302h` power register or equate every display blank with loss of this rail.

Power connector assignments:

| Connector | Destination | Pins |
|---|---|---|
| P1, 12 pins | System board J7 | 1 power-good; 2 ground; 3 +12; 4 −12; 5–8 ground; 9 open; 10–12 +5 |
| P2, 4 pins | Interface adapter J5 | 1 −22.3; 2 −22.3 enable; 3 polarizing; 4 ground |
| P3, 2 pins | Battery pack | 1 battery positive; 2 ground |

### Battery ride-through

The battery pack is **seven Ni-Cad cells, 2.2 Ah**, charged at a constant **100 mA**. A properly charged pack supplies **three minutes** of backup for **keyboard and memory**. When primary AC disappears **while the power switch remains on**, the pack automatically becomes active. **LCD, touch panel and diskette drive are inoperative on battery**. The application remains able to act on AC-loss sense and keyboard events; this is not a firmware suspend-to-RAM command that stops all guest progress.

Operations printed 3-9 / PDF 28, lines 1198–1239 provides the practical test: leave plugged in and switched on **at least 24 hours**, illuminate Caps Lock, unplug without switching off, confirm the light stays on for **three minutes**, then reconnect. Replace pack if it fails; routine replacement interval **two years**. Replacement part is **49F6137** (Operations 5-4 / PDF 39). These are service procedures, not an exact discharge curve or proof of an emulator cutoff at exactly 180.000 seconds.

Turning the workstation off before unplugging avoids draining the pack. Operations calls it a bridge until the facility's emergency supply starts and recommends an emergency-power outlet. Model distinct **AC present**, **power switch**, **battery available/charged**, and rail-good conditions; one `powered` boolean cannot represent the required behavior.

A defensible logical power model can expose an explicitly configured “backup available” condition and scheduled exhaustion scenario. **OPEN:** detailed switchover waveform, undervoltage hysteresis, battery current under load, partial-charge duration, state retention after pack exhaustion, UART digital-core operation on backup, and restoration reset thresholds. Do not derive them solely from 2.2 Ah/100 mA or promise lossless disk writes during ride-through.

### Application-visible power sense

TR 7-4 / PDF 144 gives the exact polling sequence:

```asm
mov dx,0F301h
in  al,dx
test al,1
jnz primary_power_on
jz  primary_power_off
```

`F301h` bit 0 is **+12 V OK**, annotated `-Battery Power/Fuse Open`; **1 good**, **0 battery or fuse-open condition**. The bit is therefore not a unique battery-presence or state-of-charge indicator. Bit 1 is LCD power OK (−22 V). Bit 3 senses scanner type (1 wand, 0 scanner); other touch/keyboard senses belong to [TOUCH.md](TOUCH.md). Do not fabricate a power-loss interrupt: the supplied programming advice is polling.

TR 7-4 advises applications to inhibit normal keyboard input during primary-power loss because the user cannot see the display, with a possible hot-key logoff exception. This is **software policy**, not a hardware rule to stop the keyboard. It also recommends unlimited diskette retries while primary power is lost. Hardware emulation must preserve the failed/incomplete I/O and resume capability rather than report every operation successful. The storage chapter owns the exact FDC effects.

### LCD blanking and indicator side effect

TR 7-5–7-6 / PDF 144–145 requires applications to turn the LCD backlight off after **five minutes of inactivity**, to extend assembly life. It supplies:

```asm
mov ax,11BAh
mov bh,03h
mov bl,0            ; off; BL=1 turns it on
int 10h
```

This is a BIOS extension with **application-owned timing**, not an automatic hardware five-minute counter. Keep backlight blanking separate from video generation, touch-driver gestures, complete LCD rail failure, and AC loss.

When this backlight-control call turns light off, already illuminated keyboard indicators are not altered. If **all were off**, Scroll Lock's indicator is turned on as an on-reminder. Original indicators are restored on unblanking. This is an observable software/controller interaction, not permission to change host Scroll Lock or a guaranteed change in the BIOS logical Scroll Lock flag. Applications may offer an earlier blanking hotkey, but the manual does not assign a universal chord. Supplied touch-driver gesture behavior is binary-specific and owned by [DRIVER_ABI.md](DRIVER_ABI.md), not a new electrical power switch.

### Clock-battery statement: preserve the contradiction boundary

The operations guide printed 1-11–1-12 / PDF 15–16 says its Set Time and Date service is usually needed only when a **clock battery** is replaced or local time changes. Its error table also includes **161 — System Date and Time**, with service advice if the error recurs (printed 3-6 / PDF 27). Those are genuine 7690 user-documentation claims and must not be erased merely because the system board resembles Model 25.

They do **not** identify RTC silicon, an I/O address map, battery wiring, alarm interrupt, CMOS bytes, or BIOS register contracts. In particular, do not instantiate the Model 30 MM58167 banks/IRQ1 alarm, an AT CMOS RTC at `70h/71h`, or an emulator wall-clock service on this basis. The ride-through pack is separately described and not proof that it is the clock battery. Until actual 7690 firmware/board evidence resolves this, clock implementation remains an explicit acquisition question in [MODEL25.md](MODEL25.md)/[BOOT.md](BOOT.md).

## 9. Downstream acceptance scenarios

These are implementation acceptance paths, **not claimed runs of an emulator**. Research for this chapter was source/image inspection; no build, formatter, linter or test suite was run.

### Barcode

1. Boot with feature absent and present; keyboard works in both, presence diagnostic differs. A missing wand does not masquerade as a missing controller.
2. Through INT `10h`, send the eleven-byte `1f1G` example; valid Code 39 with correct check is accepted, another symbology is not, wrong check does not reach DOS as valid text.
3. Compare F's Interleaved bit 2 with C's bit 4; verify they select the same family through different command encodings, not two unrelated flags.
4. Configure 2-digit supplements, scan forward then reverse, and verify the documented forward-only supplemented path. Plain reverse labels remain supported.
5. Apply `31M`: accept 32-digit Interleaved label, reject 30; apply `33M`: permit 6/14, not 34. Check the unresolved checksum-length interaction separately rather than guessing.
6. Install header containing a space and ESC and a trailer containing CR; counted bytes survive parsing, no premature command restart or C-string truncation, exactly one configured record terminator.
7. Enable `1J`: no first read before K. `0K` and `1K` each grant one read; no second transmission without another permission. Test invalid-read credit semantics only after obtaining authoritative behavior.
8. Request `1S`; decode punctuation-valued nibbles correctly, receive seven logical characters through keyboard services rather than through COM1. Do not invent the controller version.
9. Reset with `ESC E`; clear configuration/buffers, honor approximate unavailable interval, return defaults. Keyboard reset additionally resets barcode; barcode reset does not reset CPU.
10. Scan mixed-case/punctuation with Num/Caps and held Shift; application receives intended label and subsequent human keys retain their state. Read-success tone occurs only when guest code recognizes the complete frame.

### Serial and parallel

11. Program divisor with DLAB set while RBR is pending; divisor reads do not consume it, DLL writes do not transmit. Change word/stop/parity and observe actual frame timing.
12. Exercise loopback with RTS/DTR/OUT1/OUT2 one at a time; observe the specified MSR mapping/deltas and IIR priorities. Clear causes by their proper reads, not by PIC EOI alone.
13. Keep THR empty while the final character shifts: LSR bit 5 is 1 and bit 6 is 0. Introduce receive overrun/parity/framing/break separately; settle the documented overwrite conflict against physical/part evidence.
14. Clear OUT2 with IER causes pending; UART status remains meaningful but system IRQ output is gated. Clear planar serial select and verify integrated decode no longer consumes channel I/O.
15. Write LPT data repeatedly without strobe: nothing is printed. Valid strobe with setup/hold accepts a byte; ACK low→high requests IRQ7 only when enabled. Paper-end, offline and error states remain distinct.
16. Clear `65h` bit 7 and drive external data pins; read input without enabling undocumented `37Ah` direction bits. Disable parallel chip select separately from its output drivers.

### Sound and power

17. Program PIT2, gate its audible output, and poll `62h` bit 5: muting sound does not necessarily stop timer output. Inserting an earphone plug mutes the built-in speaker without resetting PIT or changing a fictional status bit.
18. With backup available and switch on, remove primary power: `F301h` bit 0 clears; display/touch/diskette cease normal function; keyboard/retained memory remain useful; no manufactured RTC or power-loss IRQ.
19. Simulate a fuse-open +12 fault: bit 0 clears just as on battery, proving it is not a charge gauge. Independently disable the −22.3-V enable and model its +5-V disabled level/LCD sense dependency through the shared latch owner.
20. Invoke backlight off with all three indicators off, then with Caps already on; observe the documented on-reminder and restoration. Let guest application implement five-minute/hotkey timing. Do not erase video RAM or stop the CPU because the panel is dark.
21. Restore primary power during ride-through and exercise an application's disk retry and input-reenable path. Exhaustion and cold-restart outcomes require the explicitly chosen, evidence-limited power profile rather than an invented exact chemical model.

## 10. What must remain explicitly unresolved

The primary material establishes extensive programming contracts, but not a license to fabricate peripheral firmware. Highest-value acquisitions are: barcode MCU and keyboard MCU ROMs; exact gate-array serial/ACK captures; actual barcode software-version/status defaults; malformed gateway/overlapping-option behavior; raw control-character synthesis; barcode check/length boundary interaction; UART part identity and overrun/RI-edge behavior; physical PIT clock confirmation against the beeper-table typo; real power switchover/exhaustion traces; and actual 7690 RTC hardware/firmware identification. Keep each implementation's DOCUMENTED, BINARY, INFERENCE and OPEN boundaries local to the affected behavior.
