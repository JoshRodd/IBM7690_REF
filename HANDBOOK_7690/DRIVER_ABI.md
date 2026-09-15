# LEDTOUCH software interfaces and executable behavior

The driver presents two interfaces over the same optical scanner: DOS character device **`POINT`** and a Microsoft-mouse-compatible **INT33h** entry. Compatibility is partial and version-specific. Neither interface is a replacement specification for the F300h–F303h hardware in [TOUCH.md](TOUCH.md).

**Primary contract:** TR printed5-4–5-17, physical PDF101–107. **Binary authority:** loose disk driver's Version3.02, SHA-256 `bfb95e3a5d1a9ef87742b33b19d33fee2fbcb0718f04995f770b0a3c37d6d2df`; image driver's Version2.4, SHA-256 `1c3dc5a2c4a9c6d422f03f92db6b3bcc2b314939603a117594e9573eb7ee2613`. All code/data offsets here are hexadecimal **file-relative SYS offsets**. See [source inventory](SOURCES.md) and [instruction experiments](../ANALYSIS/TOUCH-TRACE.json).

Statements marked **DOCUMENTED** describe the book, **BINARY** describe these files, **EXECUTED** describe synthetic-input instruction runs. Discrepancies are retained instead of making an ABI substitute look cleaner than the original.

## Loading, device header and residency

The documented installation is:

```dos
DEVICE=LEDTOUCH.SYS
```

in the boot disk's CONFIG.SYS, with the driver file accessible at that path. `LEDINST.BAT` invokes `NSTALL.EXE`, supplying `TXT.OK` and the driver; the installer is not the driver and its version/status values are separate. [DIAGNOSTICS.md](DIAGNOSTICS.md) covers boot media and installation choices.

Both files start with this 18-byte DOS device header:

| Offset | Size | Value / role |
|---|---:|---|
| 0000 | 4 | FFFFFFFFh, end of device chain before DOS links it |
| 0004 | 2 | 8000h, character-device attribute word |
| 0006 | 2 | 030Bh, strategy entry |
| 0008 | 2 | 0316h, request-interrupt entry |
| 000A | 8 | ASCII `POINT` followed by three spaces |

The strategy entry stores ES:BX as a request-packet pointer in private words02E5h (segment) and02E7h (offset), then `RETF`s. The request-interrupt entry saves caller state, switches to a private stack in the driver segment with SP=027Ah, dispatches on request command byte+2, restores the original stack, and `RETF`s. It is not an IRET entry and must not be invoked as a hardware interrupt.

The header advertises only8000h, not IOCTL or enhanced open/close capabilities. There are open/close-related handlers in the dispatch table, but their existence does not establish that every DOS version sends those requests to this attribute combination.

### Actual resident boundaries

| Version | File bytes | Init returns end address | Bytes before returned end | Rounded paragraphs |
|---|---:|---|---:|---:|
| 2.4 | 7021 | driver segment:1560h | 5472 | 342 |
| 3.02 | 8111 | driver segment:1906h | 6406 | 401, if allocator rounds upward |

The init-only self-test and messages beyond that boundary may be discarded by DOS. The TR's “requires4Kb RAM, occupies7.5Kb disk” is not an exact residency description for either preserved version. Do not keep calling an init-only routine after DOS has reclaimed that memory.

Both initialization routines replace the command0 dispatch slot with the unsupported-command handler, select reversed LCD presentation using INT10 AX=11BAh/BX=0201h, print the banner, install INT33 through DOS AH=25h, and run optical self-test. Version3.02 also reinstalls INT33 from the request-interrupt path while its scanner-initialized byte is zero.

**Installation status caveat, BINARY/EXECUTED:** init stores its resident end through the original ES:BX, then loads BX=0201h for the video call. It subsequently writes0100h to ES:[BX+3] without reloading the request pointer (3.02 0554h–0561h;2.4 052Fh–053Ch). With the analysis BIOS fixture preserving BX, this writes at request-segment:0204h, leaving a request at offset0's status unchanged. No supplied adapter ROM establishes a special BX restoration convention. This is a real control-flow observation, not permission to patch the driver; actual DOS/adapter-ROM installation should be checked separately. The analysis tool's successful init-only self-test is not a claim of DOS installation success.

**Separate actual-DOS observation:** PC DOS3.20 under generic QEMU/SeaBIOS loaded unpatched3.02 from CONFIG.SYS, selected its IBM-mouse fallback on absent optical hardware, and a DOS client successfully opened `POINT` and read `30 0D`. See [DOS-BOOT-TRACE.json](../ANALYSIS/DOS-BOOT-TRACE.json) and [the captured consumer screen](../ANALYSIS/dos320-point-consumer.png). This proves that installation/read path in that environment despite the low-level packet caveat; it does not establish actual7690 adapter-ROM installation or optical input under DOS.

## DOS `POINT` stream

### Documented output

`POINT` is input-only. A read produces one ASCII record:

```text
0\r                   no active touch
1,HHH,VVV\r           active touch, three decimal digits per coordinate
```

The manual's BASIC example uses `OPEN "POINT" FOR INPUT` and `LINE INPUT`, so the language/DOS cooked-input layer removes the carriage return. At the **driver request** boundary, the CR byte is present. An emulator or DOS-device shim must declare which layer it exposes.

HHH is a **1-based horizontal character position**; the book gives001–080. VVV is a1-based character line, with maximum determined by the video mode (up to030). These are not the INT33 logical coordinates and not the79×47 optical half-step grid.

### Binary scaling

The record generator is3.02 043Dh–0540h;2.4 0429h–051Bh. After scanning, any negative normalized coordinate yields `0\r`. Otherwise:

```text
qx, rx = divmod(normalized_x × 10, 1266)
column = min(80, qx + (rx >= 633) + 1)
qy, ry = divmod(normalized_y × BDA[0040:0084], 9999)
row = qy + (ry >= 4999) + 1
```

The vertical BDA value is **rows-minus-one**; the code loads a word then clears BH, using its low byte. Horizontal formatting remains an80-column scale; it is not multiplied by the current BDA text-column count. Thus the manual's80-column examples are not a generic promise of native40-column `LOCATE` positions.

The code shifts the integer divisor right one, then increments the quotient when the remainder is at least that value. For the odd divisor9999 this is **not exact mathematical half-up rounding**: remainder4999 already rounds upward. EXECUTED with normalized Y=9137 and rows-minus-one29, `264973=26×9999+4999` produces row028 rather than027. Output contains a literal leading zero for each coordinate's hundreds digit; this is not a general arbitrary-height formatter.

There is a stability counter for candidate character positions. The3.02 optical path requests three repeated candidate observations while IBM-mouse fallback uses one. First active data is published immediately when no previous character coordinate has been accepted; subsequent changes can wait. The record may therefore report the prior accepted cell while the beam result has already moved. A no-touch sample clears that accepted position.

### Partial reads and buffered state

The buffered record has its own remaining count at027Dh, current offset at027Fh and data beginning0281h. The command4 handler:

1. reads requested count from packet+12h;
2. for a nonzero request, generates a record **only if its private remaining count is zero**;
3. copies at most the remaining bytes to the far buffer at packet+0Eh/+10h;
4. updates both private offset/count and packet's returned count;
5. does **not** append a second newly scanned record to satisfy a larger remaining request.

EXECUTED on3.02, after synthetic beam X18/Y11:

| Requested bytes | Returned bytes | Data |
|---:|---:|---|
| 2 | 2 | `1,` |
| 3 | 3 | `037` |
| 8 | 5 | `,012\r` |

The three reads concatenate to `1,037,012\r`. A host shim that rescans for every byte, loses the remainder, or reads indefinitely until the requested size is full is observably different. A zero-length request does not initiate a scan.

### DOS request commands actually dispatched

Table at02E9h,17 words. Commands at or above10h are clamped to the last unsupported slot.

| Command | Meaning / implementation | 3.02 handler | Status word written |
|---:|---|---|---|
| 00 | Initialize once | 0541 | See initialization caveat |
| 01–03 | Unsupported, including input IOCTL03 | 0429 | 8103h |
| 04 | Read buffered data | 037B | **0200h** |
| 05 | Nondestructive read of current buffered byte; does not generate a fresh record | 03CE | 0200h if buffered,0100h if empty |
| 06 | Input status | 03F0 | 0200h |
| 07 | Input flush: zero remaining count | 03F8 | 0200h |
| 08–09 | Set a private flag, no character-output implementation | 0406 | 0100h |
| 0A–0C | Unsupported | 0429 | 8103h |
| 0D | Set private flag | 0411 | 0100h |
| 0E | Clear private flag | 041C | 0100h |
| 0F–10 and above | Unsupported | 0429 | 8103h |

The read/status handlers really write0200h. In the usual DOS request status layout,0100h is DONE and0200h is BUSY; do not silently rewrite these outputs to0100h/0300h in a binary-behavior description. The instruction harness directly observes0200h for all three partial-read requests. How a particular DOS release consumes these unusual status combinations is a separate runtime question.

The unsupported status8103h is the error/done result with unknown-command code03h. Direct IOCTL support is not advertised or implemented. Do not invent a calibration IOCTL just because the device has private INT33 functions.

## INT33 entry, register preservation and scheduling

| Version | Entry | Function0..19 dispatch table | Periodic entry |
|---|---|---|---|
| 2.4 | 0C99 | 0C3D | 0C65 |
| 3.02 | 0F3E | 0EE2 | 0F0A |

The handler returns with **IRET**. It preserves caller DS, ES, SI, DI and BP on ordinary paths, but documented outputs and many otherwise unspecified AX/BX/CX/DX values are not blanket-preserved. Function4Dh intentionally returns ES:DI. Treat only documented/decoded result registers as outputs; do not make client code depend on incidental AX values seen after a scan.

On entry, the handler snapshots BDA0040:0017 and uses INT10/AH0Fh to inspect current video mode. It establishes a640×200 logical extent on every entry. Text/graphics flags and width selection affect cursor rendering; they do not turn the driver into a native640×480 mouse API.

Normal API polling invokes the optical scan synchronously. Simply loading the driver does not install a continuously sampling touch IRQ. Callback registration can install a timer hook; see below. As a result, event counts describe **observed polls**, not all physical edges that occurred between widely spaced calls.

## Complete documented function table

Decimal names in the book correspond to hexadecimal AX values below. Version3.02 handler offsets are provided for debugger use; equivalent2.4 handlers are in its dispatch table.

| AX | Function | Inputs | Documented outputs / contract | 3.02 handler |
|---|---|---|---|---|
| 0000 | Reset | none | AX=FFFF installed,0 absent; resets driver variables | 1402 |
| 0001 | Show cursor | none | AX=current cursor level; visible at level0 | 1491 |
| 0002 | Hide cursor | none | AX=current cursor level; decrements nesting level | 14A3 |
| 0003 | Position/buttons | none | BX=button mask,CX=X,DX=Y | 153A |
| 0004 | Set cursor position | CX=X,DX=Y | none | 154A |
| 0005 | Press information | BX=button0 left,1 right,2 middle | AX=current buttons,BX=count,CX/DX=position | 1583 |
| 0006 | Release information | BX=button index | AX=current buttons,BX=count,CX/DX=position | 15BD |
| 0007 | Horizontal bounds | CX=min,DX=max | swaps reversed inputs | 15F7 |
| 0008 | Vertical bounds | CX=min,DX=max | swaps reversed inputs | 1606 |
| 0009 | Graphics cursor | BX=X hotspot,CX=Y hotspot,ES:DX=64-byte masks | copies16 screen-mask words then16 cursor-data words | 1615 |
| 000A | Text cursor | BX=0 software/1 hardware;CX/DX=masks or start/end scanlines | none | 1633 |
| 000B | Motion counters | none | CX=horizontal,DX=vertical signed relative counts | 1663 |
| 000C | User callback | CX=event mask,ES:DX=far routine | installs/updates callback | 16E9 |
| 000D | No operation | ignored | no defined new result | 1753 |
| 000E | No operation | ignored | no defined new result | 1753 |
| 000F | Mickey/pixel ratios | CX=horizontal,DX=vertical | sets relative-motion scaling | 1754 |
| 0010 | No operation | ignored | no defined new result | 1753 |
| 0011 | No operation | ignored | no defined new result | 1753 |
| 0012 | Large graphics cursor unsupported | ignored | AX=0 | 176F |
| 0013 | No operation | ignored | no defined new result | 1753 |
| 0058 | Light-pen-style position | none | AH=active,BX=pel column,CX=raster line,DH=character line,DL=character column | dispatcher1030 onward |
| 0059 | Button following | BX=release mask,CX=tracking mask | masks persist across reset | dispatcher10E3 |

Unknown extended functions return without a universal “unsupported” error code. The dispatcher first checks full AX<=0013h; extended comparisons then examine **AL**, so nonzero AH does not prevent an extended AL match. Use canonical AX values in applications. Do not advertise all modern Microsoft mouse-driver functions merely because INT33 exists.

### Reset: documented versus preserved defaults

TR5-7 says hidden level−1, arrow graphic cursor, hotspot−1/−1, inverting text box, mickey ratios8/16 and bounds0..639,0..199. The binaries do not implement every one of those prose defaults literally:

- Reset returns **AX=FFFFh,BX=3,CX=0,DX=0**; installation recognition is not a fresh hardware-presence test.
- Published mouse position becomes320,100, not the returned CX/DX zeros from the reset call.
- Horizontal and vertical lower-bound words are set to**1**, maximum639/199.
- Internal motion multipliers reset to1 horizontally and2 vertically. See the actual motion arithmetic rather than equating these private fields with the book's8/16 values.
- Cursor mode byte is set to1, which the renderer treats as hardware text cursor; its scanline end is7. A software-cursor data word0F18h is also stored. The book's “inverting box” is not an exact full reset-state listing.
- The graphics mask array is copied from the embedded default. Hotspot words initially containFFFFh; function0 does not explicitly rewrite them, so a custom hotspot can survive a reset even though the default mask is restored.
- Function59h masks survive reset as the book explicitly says.
- In3.02, reset clears the scan-initialized flag and recent mouse relative state, but not the usable optical mask. Version2.4 reset does not perform the same3.02 scanner reinitialization store.

These differences matter to an ABI replacement; a full emulator naturally executes them. Neither version's reset result is evidence that the interface adapter or touch panel is physically installed.

### Position reporting and bounds

The3.02 scan-to-mouse conversion uses `floor(normalized_x×640/9999)` and `floor(normalized_y×200/9999)`, then bounds and stability handling. On no touch it keeps the previously published CX/DX while clearing active state. Function3 has no dedicated documented “touch active” result; use58h or59h following when contact state is needed.

With raw geometry isolated from custom LCD cropping, both versions produce these executable observations:

| Beam contact | INT33 CX,DX | `POINT` example |
|---|---|---|
| X0/Y0 | 2,1 | `1,001,001` |
| X39/Y23 | 634,199 | lower-right record determined by80-column/rows-minus-one scaling |
| X18/Y11 | 292,95 | `1,037,012` |
| Release after X18/Y11 | keeps292,95 | `0` |

**Horizontal lower-bound asymmetry:** code3.02 17A1h–17B3h first clamps to maximum, then if value<=minimum substitutes `minimum+1`. Vertical code uses `<minimum` and substitutes `minimum`. Equal horizontal bounds10/10 can therefore report**11**, outside that requested range. This was executed. It is a driver defect/quirk, not a license to move the guest's actual X register to make the handbook's nominal0..639 promise true.

Function4 stores the requested coordinates directly and resets relative-motion origins; it does not itself clamp them. Future physical polling can replace the requested position. Do not confuse cursor positioning with recalibration of the infrared panel.

## Buttons are keyboard and touch policy

Button-status bits are0 left,1 right,2 middle. TR5-7 names left Ctrl, left Alt, and left Shift respectively. The actual3.02 code uses the ordinary keyboard-status byte:

| BDA0040:0017 flag | Button while touch active |
|---|---|
| bit2 Ctrl | bit0 left |
| bit3 Alt | bit1 right |
| bit1 left Shift | bit2 middle |

Ctrl/Alt bits are aggregate flags, **not side-specific** tests. The manual's “left” wording is not enforced by checking enhanced side-state bytes. Right Shift bit0 is the display-gesture modifier described in [TOUCH.md](TOUCH.md), not the middle mouse button.

The keyboard button is introduced while touch is active. On no touch, prior state can remain held while its modifier remains down; clearing the modifier releases it. This is not a literal three-button mouse protocol.

### Function59h following

BL selects buttons to pulse when an active touch is removed; CL selects buttons held throughout active contact. Only low bytes are stored. No new independent timer is created.

An executed example with release mask2 and tracking mask1:

1. Active touch: BX button mask1.
2. First no-touch poll: BX mask2, the synthetic right-button release-triggered press.
3. Next no-touch poll: BX mask0.
4. Function5 for right button returns count1, then0 on the next query.

Thus “release button” means a **button activation caused by touch removal**, not directly setting the mouse driver's release-event bit. Ordinary edge logic turns the pulse into press/release events. Without polling, the pulse cannot be delivered as though hardware had independently interrupted the CPU.

### Press/release counters and position discrepancy

The manual describes0..32767 counts and the coordinates of the last transition. The code uses ordinary16-bit increments without a32767 cap, and functions5/6 return the **currently published coordinates**, not per-button historical coordinate records. BX0 selects left,BX1 right,and any value above1 selects middle in the decoded handlers; applications should still pass documented0..2.

EXECUTED: press left at292,95, move to325,104 while still held, then call function5. It returns count1 with**325,104**, not the original press position. The count is then cleared. Preserve this distinction when diagnosing an application that assumes generic mouse-driver behavior.

## Cursor rendering

### Show/hide nesting

Show increments a negative level toward zero; a show at zero is ignored. Hide decrements the level; the0→−1 transition removes/restores the visible cursor, while additional hides nest. A matching number of shows is needed to return to zero. Each caller that hides should balance its own hide rather than unconditionally force visible.

The graphics cursor is a16×16 mask pair:

```text
new_pixel = (old_pixel AND screen_mask) XOR cursor_data
```

For a mask/data bit:00 clears,01 sets,10 preserves,11 inverts. Function9 copies64 bytes from the caller's **ES:DX**, despite the manual's table mentioning only DX; BX/CX specify signed hotspot offsets. Hotspot need not lie inside the bitmap.

The driver saves background bytes in its resident memory and restores them before moving/hiding. It suppresses repeated graphics redraw at an unchanged position. Applications must hide before modifying the saved-under region or risk restoring stale pixels. An emulator should expose the video memory behavior, not draw an unrelated host cursor over the framebuffer and call it the guest's cursor.

The text cursor has distinct paths:

- software mode combines the existing character/attribute word with screen/data masks;
- hardware mode uses BIOS cursor shape and position;
- the driver uses page0 in its BIOS rendering calls, not an arbitrary active video page abstraction.

The driver has inherited mode tests broader than the machine's actual LCD modes. Presence of code paths for modes0Bh/0Ch/0Dh does not establish that the7690 firmware exposes those modes. Follow [VIDEO.md](VIDEO.md) for valid machine modes, memory mapping and MCGA/LCD differences.

**OPEN / compatibility risk:** cursor code includes mode-specific address and mask handling, not a generic clipped raster compositor. Do not infer safe clipping for arbitrary out-of-range hotspots or every VGA mode from the Microsoft-compatible entry names. The shipped bitmaps and ordinary native modes are the primary implementation targets; unmodified instructions, rather than host redraw shortcuts, determine unusual inputs.

## Motion counters and callbacks

### Relative motion

Function0Bh calls the scanner, returns relative counts, and establishes a new origin. When contact is absent it reports zero and clears the origin. For optical input, the current logical-position delta is multiplied by internal ratios; the horizontal product is arithmetic-shifted right one, while the vertical product uses its stored multiplier directly. The3.02 IBM-mouse fallback has a separate raw-delta accumulator path.

Function0Fh clamps signed ratios below1 to1, stores horizontal CX, and stores **twice** vertical DX. This storage transformation is why copying the TR's ratio defaults straight into private words is not a faithful implementation. Keep the signed16-bit arithmetic, including multiplication/truncation, if implementing a binary-compatible software substitute.

### Event mask and far-call payload

| CX bit | Event |
|---:|---|
| 0 | position changed |
| 1 | left pressed |
| 2 | left released |
| 3 | right pressed |
| 4 | right released |
| 5 | middle pressed |
| 6 | middle released |
| 15–7 | unused by documented interface |

Function0Ch stores the mask and ES:DX callback, with a do-nothing far-return target if the supplied segment is zero. The callback receives:

```text
AX = event ID bits
BX = current button mask
CX = current logical X
DX = current logical Y
SI = horizontal relative counts
DI = vertical relative counts
```

The user routine must **RETF**, not IRET or near RET. Events can be accumulated before callback dispatch; setting a new mask can immediately expose an already pending event when the current INT33 call reaches its common exit. Do not assume the first callback must come from a future physical transition.

### Actual timer ownership

First function0Ch registration saves **INT08h** at physical0020h and installs its own timer entry. It is not an INT1Ch hook and does not remap the PIC. The timer entry:

1. skips polling if event mask is zero or driver is already inside its INT33 handler;
2. decrements a two-tick countdown;
3. on expiry synthesizes a return frame and enters its own function3 handler;
4. restores registers and far-jumps to the previous INT08h handler.

Every INT33 entry resets that countdown to2. Repeated foreground calls can defer background polls. With the ordinary18.2Hz system tick and no foreground calls, the callback polling cadence is approximately9.1Hz; it is **not** an optical hardware sample-rate specification. The old timer handler remains responsible for the normal BIOS timer work and IRQ acknowledgement.

EXECUTED with an actual guest `RETF` callback fixture: the first timer entry performs no optical I/O; the second scans and dispatches a movement event with CX=292. The trace includes callback registers and installed vector bytes. No real PIC or IBM BIOS timer handler was executed by that experiment.

Reset clears callback-mask state, but the installed timer chain is not unlinked. A zero mask makes it dormant. Save-state or unload logic must preserve the old vector and handler-lifetime relationship; loading/unloading arbitrary replacement drivers without repairing the chain can leave a dangling timer entry.

## Light-pen-style function58h

The documented interface reports AH active, BX/CX pel/raster coordinates, and DH/DL1-based character line/column. It is an **INT33 function**, distinct from BIOS INT10/AH04h light-pen support.

Version3.02 first scans, then uses its own smoothing state for this function: if active optical positions remain within24 logical units of the remembered anchor, it accumulates half of successive movement; larger movement or IBM mouse mode replaces the smoothed position. It derives character row by `floor(24*y/199)+1` and column by `floor(79*x/639)+1`. These are a fixed25×80 interpretation rather than a general current-text-height query.

**Version2.4 defect, BINARY/EXECUTED:** at0D84h it loads Y into CX, multiplies24×CX, loads199 into **BX**, but executes **`DIV CX` at0D90h**, not DIV BX. For nonzero Y the character-row intermediate becomes24, hence row25. With X18/Y11 after clear calibration, the real2.4 routine reports row25, while3.02 reports row12. Clear the contact, call function4 with Y=0, then function58:2.4 raises CPU divide-error INT00 in the fixture. The absence of a new physical contact matters because polling can otherwise replace function4's stored position. Version3.02 loads the intended CX=199 divisor at10ADh. See `lightpen_version_comparison` in [TOUCH-TRACE.json](../ANALYSIS/TOUCH-TRACE.json); no DOS divide-error handler execution is claimed.

The raw BX/CX outputs and touch-active AH are separate from this character-row defect. A downstream emulator should let the driver execute its real divide instruction, not intercept58h to return corrected generic mouse results.

## Additional binary-only functions

These are recovered implementation details, **not documented stable IBM application APIs**. They are useful for preserving software that actually uses them and for debugging this exact driver.

| AL on extended path | 2.4 | 3.02 |
|---|---|---|
| 4D | Return ES:DI pointer to compatibility identity string, toggling its encoded storage as needed | Same role, different storage range and encoding scope |
| 5A | BX=active-scan count; clear count | BX=count then clear; CH=mouse-fallback selector,CL=coordinate stability parameter |
| 5B | No decoded implementation | Store CL stability parameter,CH fallback selector,clear initialized flag |
| 5C | No decoded implementation | Store BX missing-touch retention count,CX signed X adjustment,DX signed Y adjustment |

3.02 offsets10F2h–1131h establish5Ah–5Ch. The fallback selector is software policy, not a hardware model byte or auto-detected ROM identity. The coordinate offsets are applied only on the recognized extended LCD-transform branch in [TOUCH.md](TOUCH.md).

Function4Dh returns compatibility text with a Microsoft-style identity inside an IBM-owned module. Both files carry explicit surrounding IBM text explaining that the compatibility notice is functional interface data, not ownership attribution. Do not infer a Microsoft driver binary or its full API from that string. Version3.02 keeps a larger region XOR-encoded and toggles it around legacy-function calls; arbitrary linear disassembly of those bytes is not real instructions.

## Version3.02 IBM pointing-device fallback

A failed selection wrap can set063Ch to1 and print `Touch panel not installed - using IBM mouse`. The next scanner call then enters0AFDh rather than accessing the optical circuit. This is an intentional driver fallback, not an emulator feature invented to hide missing hardware.

The initialization sequence uses BIOS INT15:

1. AX=C200h,BH=0: disable pointing device;
2. AX=C201h: reset;
3. AX=C207h,ES:BX=driver:0C0Bh: install packet callback;
4. AX=C200h,BH=1: enable.

Carry failure prints `Error interfacing mouse (xxxx)` and clears initialization for a later attempt. The analysis fixture explicitly supplies successful BIOS responses; it is not the7690 system BIOS.

The packet callback is a far routine consuming BIOS-passed stack words. It reads status atBP+0Ch, X delta atBP+0Ah, Y delta atBP+08h after establishing its frame. X/Y sign bits come from status10h/20h; Y is subtracted to make downward logical movement positive. Button bits0/1 are used; simultaneous left+right maps to middle. The code does not establish support for wheel/five-button packets.

Relative deltas update a normalized virtual position beginning5000,5000 at24 normalized units per delta and clamp to1..9999. A startup/quiet countdown can suppress active reports; held button state selects another delay. Raw motion counters are retained separately from optical position differences.

EXECUTED with absent-port fixture and a supplied BIOS callback packet `status=0,dx=4,dy=2`: after the quiet countdown the mouse API reports326,99. This proves execution of the recovered fallback code under the named fixtures, **not** a physical IBM mouse port test or successful7690 boot.

Version2.4 has no corresponding fallback block. Emulating only IBM-mouse fallback cannot pass optical self-tests or make a2.4 driver usable on a missing panel.

## Implementation acceptance and reproduction

A whole-machine implementation should execute the original driver and demonstrate:

- successful DOS loading, correct residency and linked device entry under a declared DOS version;
- partial `POINT` records and CR handling at the chosen DOS API layer;
- observable coordinate differences between raw optical, character stream, mouse logical and light-pen interfaces;
- all three keyboard button mappings, polling transitions, function59 pulse and reset persistence;
- balanced cursor show/hide, background restoration and real video-memory writes;
- callback entry/RETF, every-second-tick scheduling, foreground deferral and old timer chaining;
- no host-invented interrupts, event counts, historical press coordinates or corrected2.4 division;
- isolated3.02 fallback and failure paths without weakening the optical model.

Current executable evidence can be regenerated from repository root:

```sh
uv run --with unicorn==2.1.4 python TOOLS/touch_trace.py --output ANALYSIS/TOUCH-TRACE.json
```

The permanent tool is a research reproducer, not a conformance test suite for an emulator. Its BIOS cursor operations are deliberately not rendered. The listed cursor/real-DOS/real-PIC gates therefore remain downstream requirements unless separately documented as exercised in [VERIFICATION.md](VERIFICATION.md).
