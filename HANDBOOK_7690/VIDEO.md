# Video: MCGA scanout, digital conversion, and the clinical LCD

## Scope and evidence

The Type 7690 does **not** have a VGA LCD adapter, a PC Convertible display controller, or a monochrome analog monitor connected to an ordinary PS/2. It has the **8086 Model 25's MCGA architecture on the system board**, followed by a separate, programmable LCD conversion controller on the clinical interface adapter. The built-in display takes **digital video before the DAC**. Its documented physical raster is **640×480, black and white**. A correct emulator must preserve both devices and the intervening signal boundary.

Evidence labels in this chapter:

- **DOCUMENTED:** the supplied [7690 Technical Reference](../IBM_7690_Clinical_Workstation_Technical_Reference.pdf), abbreviated **TR**; [searchable extraction](../DOCUMENTATION/OCR/TECHREF.txt). `PDF 42 (1-66–1-67)` means one physical, one-based PDF page containing two printed pages. Physical pages **27–48** contain printed **1-36–1-79**. Mode numbers and register values below are hexadecimal unless explicitly described as decimal.
- **BINARY, 7690 software:** instructions in [`7690diag/COLORFIX.COM`](../7690diag/COLORFIX.COM) and [`7690diag/IBM7690.DGS`](../7690diag/IBM7690.DGS), with file offsets. A `.COM` loaded at offset `0100h` has execution offsets `0100h` greater than its file offsets. The diagnostic has a file-origin-zero entry, not a COM origin. The image's [`IBM7690.DGS`](../ANALYSIS/7690KQPW/IBM7690.DGS) is a different binary; its corresponding LCD block is identified separately below.
- **BINARY, Model 25 baseline:** `/Users/josh/src/bios8530/goldens/8525/type1/linear.bin`, 65,536 bytes, SHA-256 `cfbdc2cd67c95c15b06be14e2e5f4bbd6991f3506428af64038b6381a1120166`. Offsets are `F000:xxxx` in that baseline ROM. This is **not an authentic 7690 firmware dump**. The baseline is useful for the inherited MCGA memory/font interface, not for inventing the clinical adapter's POST or INT 10h extensions.
- **INFERENCE:** an implementation deduction, explicitly bounded by the evidence producing it.
- **OPEN:** information not established by the supplied manuals, binaries, or experiments. A register name alone is not its timing specification or bit truth table.

Critical primary diagrams and tables were visually checked on TR PDF **27, 29–38, 40–44, 46, 114, 118–119, 139–140, 143**. Physical brightness/contrast controls were checked on Operations PDF **14**. The Model 25 initialization table was checked on its Technical Reference PDF **75**; unchecked numeric OCR is not used to overrule these images. The [machine-readable evidence](../ANALYSIS/video_evidence.json) preserves tables, hashes, conflicting statements and the isolated instruction-execution observations.

No complete 7690 was booted and no physical display was measured for this chapter. Actual instructions from COLORFIX, the diagnostic RAM-write routine, and the **Model 25** font-staging routine were executed in isolated Unicorn sessions with controlled inputs; that establishes those software transactions, **not passing hardware tests**. Downstream acceptance scenarios are requirements, not claimed results.

## 1. The machine boundary: what to inherit and what to replace

| Retain from an MCGA implementation | Clinical-machine change |
|---|---|
| 64 KiB multiport video DRAM; 8 KiB character-generator SRAM | Add the interface adapter's **two separate 32 KiB static LCD image buffers**. They are not extra CPU framebuffer pages. |
| MCGA memory controller at `03D4h/03D5h`, formatter at `03D8h–03DFh` | Add independent LCD index/data ports `F304h/F305h`. |
| Character/attribute text, CGA graphics interleave, linear modes `11h/13h` | Convert the **digital stream**, including timing and blanking, to the LCD's split-panel organization. |
| 256×18-bit color palette/DAC programming and readback | The LCD **bypasses** that DAC. Palette RAM is not LCD mapping RAM and its RGB components are not physical LCD gray levels. |
| RAM-loaded fonts with an explicit staging-to-generator transfer | Retain that unusual MCGA transfer. Do not introduce EGA/VGA plane-2 font writes. |
| MCGA monitor sense and video interrupt circuitry | The planar POST sees **no monitor** with the clinical LCD attached. Adapter-ROM POST must initialize video, LCD support, and the Display Combination Code. |
| BIOS mode and character services | Adapter ROM remaps color modes and supplies `INT 10h AX=11BAh`; resident software also consumes and hooks INT 10h. |

DOCUMENTED: TR PDF 27–28 (1-36–1-39), Figure 1-21, extraction lines 1348–1472. Figure 1-21 shows the DAC output as **“No Connection”**, and labels the LCD input **digital video R, G, B, I**. Color monitors cannot be connected to this machine as described. The 16 KiB interface-adapter ROM is real documented hardware, but its executable contents have not been supplied.

Conceptual ownership:

```text
CPU video accesses ──────────────> MCGA 64 KiB DRAM
                                     │
CPU font staging ──> explicit load ──> 8 KiB character-generator SRAM
                                     │
MCGA memory controller + formatter ───┼─> digital video + sync ─> LCD controller
                                     │                           │
                                     └─> palette/DAC             ├─> 2 × 32 KiB image SRAM
                                         no attached CRT         └─> split-panel 640×480 LCD
```

**Implementation contract:** video-memory contents, character-generator contents, the MCGA raster, LCD capture/readout state, and host presentation are distinct. A BIOS call is a guest software operation over that hardware, not permission to replace the renderer with host text drawing. Touchscreen conversion and LCD-position queries must refer to the same active image rectangle; see [TOUCH.md](TOUCH.md) and [DRIVER_ABI.md](DRIVER_ABI.md).

The inherited integrated-video chip-select belongs to the planar decoder described in [MODEL25.md](MODEL25.md)/[BOOT.md](BOOT.md), not an extra LCD-enable boolean. Similarly, `F302h` belongs to the touch-controller latch. **Do not allocate a second copy of that latch in video, and do not put LCD power bits there.** The documented software-accessible LCD driver/backlight bits are at **LCD index `0Dh` through `F305h`**.

### The Model 25 inheritance boundary

The sibling corpus contains IBM's `PS2_Model_25_Technical_Reference_Jun87.pdf`, SHA-256 `b4d3df94571cfa6299f45290d75374322c03d68ddba4370cce8e41ab7dd4f899`; its searchable records have source ID `model25_techref` in `reference/corpus.sqlite3`. Physical pages **50–84** cover the corresponding MCGA diagram, registers, initialization, fonts, and programming advice. Particularly useful correspondences:

| 7690 TR | Model 25 TR | Common subject |
|---|---|---|
| PDF 31–36, printed 1-45–1-55 | PDF 57–66, printed 1-44–1-53 | Memory-controller/formatter registers and font-transfer interface |
| PDF 43, printed 1-69 | PDF 75, printed 1-62 | Memory-controller initialization bytes |
| PDF 44, printed 1-70 | PDF 76, printed 1-63 | Formatter and DAC initialization |
| PDF 44–48, printed 1-71–1-78 | PDF 77–84, printed 1-64–1-71 | Staged fonts, block selection, auxiliary font descriptors |

The image-checked initialization tables agree. This is evidence for sharing the **MCGA core**, not for sharing the output device or clinical ROM. The sibling `reference/hardware_spec.json` summarizes 64 KiB DRAM, 8 KiB SRAM, MCGA rather than VGA, and the integrated-select boundary. The secondary `MCGA.html` discusses a Model 25 gate-array multi-font erratum; it is a research lead for identifying the actual clinical planar chip revision, **not justification for enabling that defect by default**.

## 2. Modes, image placement, and geometry

### 2.1 MCGA storage mode versus LCD image

DOCUMENTED: TR PDF 28–30 (1-38–1-43), Figures 1-22–1-28. The LCD column below transcribes **Figure 1-23**, not the generic MCGA monitor dimensions.

| Requested MCGA mode | Guest organization | CPU display base | Visible payload, decimal bytes | Documented active LCD image |
|---|---|---:|---:|---|
| `00h/01h` | 40×25 character/attribute text, 8×16 font | `B8000h` | 2,000 | 640×400; 2 colors |
| `02h/03h` | 80×25 character/attribute text, 8×16 font | `B8000h` | 4,000 | 640×400; 2 colors |
| `04h/05h` | 320×200, 2 bits/logical pel | `B8000h` | 16,000, in two banks | 640×400; 2 colors |
| `06h` | 640×200, 1 bit/logical pel | `B8000h` | 16,000, in two banks | 640×400; 2 colors, double-scanned |
| `11h` | 640×480, 1 bit/pel | `A0000h` | 38,400 | 640×480; 2 colors |
| `13h` | 320×200, 1 byte/logical pel | `A0000h` | 64,000 | **320×400** as printed; 2 colors, double-scanned |

Do not quietly change the mode-13 entry to 640×400 to make it match a VGA renderer. The manual explicitly discourages mode `13h` because of the LCD's color limitations, but implements it. Its horizontal placement/doubling and the exact byte-to-digital-output interpretation need further evidence. **Unsupported on the physical LCD is not synonymous with unimplemented in MCGA or BIOS.** Likewise, the presence of general display-state table bits for EGA modes does not add mode `10h`, mode `12h`, or an external CRT to the 7690.

The 400-line images are documented as **centered vertically**, leaving blank regions above and below. The arithmetic consequence for a 480-line panel is 40 lines above and 40 below at the centered position; that is a derived placement, **not a recovered LCD-register initialization byte**. The user can change vertical position through the custom BIOS service. Never force the image back to center on every host redraw.

For 40-column text, Figure 1-23 simultaneously reports an 8×16 character box and a 640-pel LCD image from a 320-pel MCGA image. Horizontal expansion is required to reconcile the image widths; simple twofold pel repetition is a reasonable **INFERENCE** for a provisional renderer, not a measured wiring diagram. Preserve this distinction when investigating LCD index `02h` bit 7 and index `0Eh` bit 4.

### 2.2 BIOS mode remapping is adapter firmware

| Requested | Figure 1-24, PDF 29 (1-41) | Figure 7-1, PDF 143 (7-2) |
|---|---:|---:|
| `00h` | `00h` | `00h` |
| `01h` | `00h` | `00h` |
| `02h` | `02h` | `02h` |
| `03h` | `02h` | `02h` |
| `04h` | `04h` | `04h` |
| `05h` | **`05h`** | **`04h`** |
| `06h` | `06h` | `06h` |
| `11h` | `11h` | `11h` |
| `13h` | `13h` | `13h` |

Both conflicting mode-5 entries were visually checked. Do not claim to have resolved that conflict by selecting the more familiar table. A ROM dump or a real `AH=00h`/`AH=0Fh` trace is needed. The supplied diagnostic **does** establish the expectation `03h → 02h`: loose `IBM7690.DGS` file `13AEh–13C0h` sets `AX=0003h`, reads state with `AX=0F00h`, and fails unless AL is `02h`; image counterpart `180Eh–1820h`.

The generic BIOS chapter calls the power-on default mode 3, immediately reminding the reader that adapter ROM remaps modes (PDF 114, 6-12). Do not interpret that generic default as evidence that a fully initialized clinical machine must report AL=3. Conversely, do not rewrite all direct MCGA register accesses based on a remembered BIOS mode number: a program can change live hardware without invoking INT 10h.

### 2.3 Aspect ratio and physical appearance

**DOCUMENTED:** 640×480 addressable LCD pels, binary black/white capability, centered shorter modes, physical brightness and contrast sliders. **OPEN:** actual active-area dimensions, physical pixel aspect, calibrated foreground/background tint, rise/fall response, optical persistence, viewing-angle behavior, and backlight luminance.

A 640×480 array has a 4:3 **sample-count ratio**. That alone is not a measurement of the active glass or proof of square physical pels. The 5140 handbook's user-established square-pixel LCD geometry does **not** transfer to the 7690. Keep three coordinate systems: guest logical coordinates, LCD physical-pel coordinates, and host pixels. A square-pixel 640×480 host surface is an explicitly uncalibrated presentation choice until panel measurements establish the physical aspect. Do not apply an assumed CRT stretch to the 400-line active area so that it fills all 480 lines.

The Operations guide PDF 14 (1-8–1-9), extraction lines 544–562, shows **two physical sliders**, brightness and contrast, behind a cover. Those controls are not evidence for an I/O contrast DAC. The custom BIOS “normal/reverse” function changes polarity, **not analog contrast**.

## 3. CPU memory organization and pixel fetches

### 3.1 One MCGA store, not VGA planes

DOCUMENTED: TR PDF 27 (1-36), PDF 30–31 (1-43–1-44), PDF 44 (1-71). There are 64 KiB of MCGA DRAM, with the following mode-dependent uses:

| Mode family | CPU view | Ownership |
|---|---|---|
| Text | `A0000h–A7FFFh` | Four 8 KiB **font-staging blocks** inside video DRAM |
| Text | `B8000h–BFFFFh` | Character/attribute region; active image/page selects a subset |
| Modes `04h–06h` | `B8000h`, with odd-line bank at `BA000h` | CGA-compatible regeneration organization |
| Modes `11h/13h` | `A0000h–AFFFFh` | Linear video DRAM aperture |

The diagrams also mark intervening ranges “not used” or “reserved.” They do **not** establish every alias or open-bus response in the full `A0000h–BFFFFh` address range. Back all supported views with one MCGA DRAM allocation; establish exact unused-aperture decoding from the inherited implementation/planar evidence rather than allocating 128 KiB merely because the address range is that wide.

The separate 8 KiB character SRAM is loaded by the MCGA controller; it is not the same bytes as the staging aperture. The separate LCD SRAM is behind the LCD controller's diagnostic interface and scanout machinery; it is not another CPU window at `A0000h`.

### 3.2 Normal graphics packing

For modes `04h–06h`, relative to the normal displayed CGA region:

```text
row_base(y) = (y & 1) * 2000h + (y >> 1) * 80
mode 04h/05h:
    byte_offset = row_base(y) + (x >> 2)
    pixel_pair  = (vram[byte_offset] >> (6 - 2*(x & 3))) & 3
mode 06h:
    byte_offset = row_base(y) + (x >> 3)
    pixel_bit   = (vram[byte_offset] >> (7 - (x & 7))) & 1
```

Here 80 is **decimal bytes**. The line-bank stride is `2000h`, not 8,000 bytes. The displayed portions of the banks are 8,000 bytes each; gaps at the ends are still memory, not extra visible pixels.

For the linear modes:

```text
mode 11h: byte_offset = y * 80 + (x >> 3)
          pixel_bit  = (vram[byte_offset] >> (7 - (x & 7))) & 1
mode 13h: byte_offset = y * 320 + x
          pixel_code = vram[byte_offset]
```

These expressions describe the ordinary page-zero layout. Respect the controller's live display-start state rather than permanently hardwiring offset zero. Exact nonstandard start-address wrapping in every graphics mode is not fully described by the cited register prose. Linear mode `11h` is **one bit per pel**, not VGA four-plane mode `12h`; mode `13h` is **one byte per pel**, not an invitation to expose VGA sequencer/chain-4 registers.

DOCUMENTED packing: Figures 1-27–1-31, PDF 30–31; formulas are the direct arithmetic expression of those bank/packing diagrams.

### 3.3 Text, active pages, cursor and blink

Ordinary text fetch:

```text
cell = display_start_byte + 2 * (row * columns + column)
character = video_dram[cell]
attribute = video_dram[cell + 1]
foreground_code = attribute & 0Fh
background_code = (attribute >> 4) & (blink_enabled ? 07h : 0Fh)
```

Character/attribute memory is guest-visible storage. The LCD does not get to rewrite it merely because foreground and background have the same monochrome result. A BIOS or resident color-mapping hook may alter the value **before the BIOS writes it**; that is a different operation (§10).

`03D8h` bit 5 selects blink. With blink enabled, attribute bit 7 requests blinking and only three background-color bits are active. With blink disabled, all four high attribute bits select background. Hardware text blink and cursor blink must advance in guest display time, not once per host repaint. Their exact divider periods have not been measured here.

The hardware cursor exists in text modes only. MCGA cursor scanline programming is CGA-like even with 16-row fonts. TR PDF 114 (6-13) gives the 400-line transformation explicitly:

```text
displayed cursor start = CH * 2
displayed cursor end   = CL * 2 - 1
```

Thus a BIOS cursor `CH=06h, CL=07h` selects physical rows 12–13 of the 16-row box; do not silently use a VGA inclusive-end formula. Index `0Ah` bit 5 blanks the cursor. The register chapter asks for start below end, with an end maximum of 7; behavior of out-of-range/split cursors remains a measurement case.

The BIOS has saved cursor positions for eight pages and only one cursor type. `AH=05h` explicitly accepts pages 0–7 for 40-column text and 0–3 for 80-column text (PDF 114, 6-13). The adjacent mode table says eight pages for both text widths: that disagreement is real, not OCR. Do not implement eight usable 80-column pages based only on the generic table.

**BINARY, inherited:** Model 25 `F000:1A77h–1AA2h` multiplies page by BDA page length, stores the byte offset at `0040:004Eh`, then divides by two for the CRTC start in CGA/text modes. `F000:1A1Dh–1A5Bh` similarly converts row/column to a byte address and divides by two for cursor location. These observations establish word-addressed text start/cursor use for that baseline. Guest BIOS page lengths, not visible payload lengths, determine page stride; keep `0040:004Ch`, start-address registers and active-page state separate.

## 4. Fonts: the MCGA transfer is not a VGA font plane

### 4.1 Four DRAM blocks and two live SRAM pages

DOCUMENTED: TR PDF 44–47 (1-71–1-77), Figures 1-59–1-62, and PDF 117–118 (6-18–6-21).

| DRAM block | CPU base | Size | Can hardware display directly from this staging block? |
|---|---:|---:|---|
| 0 | `A0000h` | `2000h` | No: transfer to character SRAM first |
| 1 | `A2000h` | `2000h` | No |
| 2 | `A4000h` | `2000h` | No |
| 3 | `A6000h` | `2000h` | No |

The character generator has **two pages of 256 character definitions**. At most two staging blocks can be active there at once. Merely loading a staging block does not change the displayed font. `INT 10h AX=1103h`, the block-specifier service, transfers/activates the selected definitions.

`BL[1:0]` selects the block for generator page 0; `BL[3:2]` selects the block for generator page 1. If the two pairs are equal, only page 0 is needed and the display has 256 characters. If they differ, 512-character selection is enabled: attribute bit 3 selects page 0/1 for the same eight-bit character code. Example `BL=0Ch` means block 0 in page 0 and block 3 in page 1. This is not a BIOS character code wider than AL.

When 512-character selection is active, foreground intensity and font selection compete for attribute bit 3. The manual recommends `AX=1000h, BX=0712h` and reloading the first eight DAC colors for consistent analog color. The former call is the limited MCGA implementation of the otherwise generic palette-register service; it is **not evidence for a VGA attribute-controller register file**. On the clinical LCD the analog palette caveat does not create extra shades. Keep character `20h` blank: BIOS uses it to fill blank screen areas.

### 4.2 Exact staging representation from baseline instructions

The TR describes the staging area as containing **character code and pel data**, but its font-pointer prose is insufficient to derive the entire byte layout safely. The Model 25 baseline supplies that missing detail:

```text
address = A0000h + block * 2000h + scanline * 0200h + character_code * 2
video_dram[address]     = character_code
video_dram[address + 1] = glyph_scanline_byte
```

**BINARY, Model 25 only:** `F000:23A0h–240Ah` converts a glyph-major `ES:BP` input font into this **scanline-major, character/pel-pair** staging layout. For each character it writes DL as the character byte, the source glyph row as the next byte, advances the destination by `0200h` for the next row, then advances the starting character offset by two. The block selector adds `0200h` to the destination segment per block, i.e. `2000h` physical bytes. Source height `0Eh` repeats the last source row twice, producing 16 rows, matching the 7690 BIOS description at 6-18.

This is an important distinction from both `glyph*16+row` contiguous RAM fonts and VGA's 32-byte glyph slots. A 256-character, 16-row source file has 4,096 bitmap bytes; its MCGA staging representation occupies 8,192 bytes because every bitmap byte travels with a character code.

An isolated run of the real baseline routine loaded three synthetic characters starting at `41h` into block 2. For height 16, destination `A4082h` contained `41 40 42 50 43 60`, and row 15 at `A5E82h` contained `41 4F 42 5F 43 6F`. For height 14, destination rows 13, 14 and 15 contained identical final-row values. Full setup/results are in [video_evidence.json](../ANALYSIS/video_evidence.json). This experiment proves the baseline instructions; final clinical inheritance still needs a 7690 ROM comparison.

### 4.3 Transfer state, completion and race ownership

Memory-controller indices `12h/13h/14h` control the transfer (§5). A compatible state machine must distinguish:

1. DRAM staging bytes, independently writable by the CPU.
2. The requested source block and destination SRAM page.
3. Whether a transfer is armed/in progress.
4. How many characters may be loaded during a vertical blank.
5. The active font-page selection and 256/512-character mode.
6. The **completed SRAM bytes** used by text scanout.

`12h` bit 7 must first be cleared, then set to start loading; completion reads as zero. Bit 6 permits loading during normal display time when set, versus vertical-blank-only loading when clear. Bit 5 selects the page used/loaded. Do not clear bit 7 solely because software read it, or make all staging writes instantly visible in the live generator.

**BINARY, inherited:** Model 25 `F000:240Bh–2482h` clears the load bit, writes source index `13h` as `00h/10h/20h/30h`, writes `14h=FFh`, forms the destination-page/transfer control with bits 7 and 6 set, and polls bit 7 until clear or its loop exhausts. The precise per-character bus timing and the meaning of every partial-load count are still **OPEN**; `FFh` in a full-font routine is not sufficient evidence to invent an unconditional `value+1` rule for every register value.

### 4.4 BIOS fonts and software graphics fonts are different consumers

Important services, DOCUMENTED in TR PDF 117–118:

| `AH=11h`, AL | Operation |
|---:|---|
| `00h` | Load user alphanumeric definitions: `ES:BP` source, BH bytes/character (normally `10h`), BL block, CX count, DX character offset |
| `02h` | Load ROM 8×8 double-dot font into the requested block |
| `03h` | Set block specifier/activate the staged block(s) |
| `04h` | Load ROM 8×16 font |
| `20h` | Set INT 1Fh pointer for upper-half 8×8 graphics characters in modes 4–6 |
| `21h` | Set INT 43h user graphics-font pointer for modes 11/13, with points and row specification |
| `23h/24h` | Set INT 43h to ROM 8×8 double-dot / 8×16 font |
| `30h` | Return font information/pointer according to BH |

Reserved aliases are documented: `AL=01h→04h`, `10h→00h`, `11h→04h`, `12h→02h`, `14h→04h`, `22h→24h`. These are guest BIOS behaviors, not additional hardware fonts. `AL=30h` supports current INT 1Fh/43h pointers, ROM 8×8 lower/upper pointers, and BH=06h for ROM 8×16; the generic “alternate” label does not establish a second alternate 8×16 ROM font.

BIOS graphics character rendering writes pixels into the framebuffer; it does not cause LCD scanout to consult an INT-vector font for every pel. Changing INT 1Fh or INT 43h affects subsequent software drawing, not existing graphics pixels or loaded character SRAM. Conversely, changing the live SRAM font affects hardware text already in memory without repainting it through BIOS.

`0040:00A8h` points to `SAVE_TBL`, seven doubleword entries. Entry 1 is the BIOS video-parameter-table pointer, entry 2 reserved zero, entry 3 optional alphanumeric-font descriptor, entry 4 optional graphics-font descriptor, entries 5–7 reserved zero. The alpha descriptor contains byte height, byte block, word count, word starting character, far font pointer, byte displayable rows, then a list of mode bytes terminated by `FFh`. The graphics descriptor has byte rows, word height, far font pointer, then the terminated mode list. Zero auxiliary pointers select BIOS fonts. See PDF 47–48 (1-77–1-78), PDF 123 (6-30); these descriptors belong to guest RAM and must remain usable by software replacing the pointers.

## 5. MCGA memory-controller registers: 03D4h/03D5h

### 5.1 Indexed access and full register inventory

DOCUMENTED: TR PDF 31–36 (1-45–1-55). `03D4h` is a readable/writable index latch; bits **5:0** are the index, bits 7:6 reserved. `03D5h` accesses the selected register. There is no VGA attribute-controller address/data phase at `03C0h`, and a read of `03DAh` is not an LCD-index reset.

The manual describes 22 data-register entries: `00h–14h`, including reserved `08h`, plus reserved `20h`. Do not reinterpret “22 registers” as sequential implemented indices `00h–15h`.

| Index | Fields | Meaning and implementation obligation |
|---:|---|---|
| `00h` | full byte | Horizontal total, including displayed and nondisplayed character periods; controls horizontal frequency. Compatibility calculations matter; not a literal VGA CRTC total. |
| `01h` | full byte | Horizontal displayed. BIOS writes **`27h` in every listed mode**, and hardware calculates the correct displayed width for the selected mode. |
| `02h` | full byte | Character-position count at start of horizontal sync. |
| `03h` | bits 7:4 vertical-sync width; 3:0 horizontal-sync width | Vertical units are HSYNC periods; horizontal units are character clocks. |
| `04h` | low 8 bits of vertical total | Ninth comparison bit is **inverse of writable mode-control bit 6**. Together with vertical adjust controls vertical period. |
| `05h` | bits 5:0 adjust; 7:6 reserved | Vertical-total adjustment; documented minimum `02h`. |
| `06h` | low 8 bits of vertical displayed | Ninth comparison bit is inverse of mode-control bit 6. Despite the legacy “characters” name, prose describes displayed scan lines. |
| `07h` | low 8 bits of start vertical sync | Ninth comparison bit is inverse of mode-control bit 6. |
| `08h` | reserved | Do not install generic interlace/skew behavior solely because a 6845 has it here. |
| `09h` | bits 3:0 row size; 7:4 reserved | Table writes text `07h`, modes 4–6 `01h`, modes 11/13 `00h`; hardware derives the actual row/double-scan organization. |
| `0Ah` | bits 3:0 cursor start; bit 5 cursor blank; bits 7:6,4 reserved | Text cursor start; bit 5=1 hides cursor. |
| `0Bh` | bits 3:0 cursor end; 7:4 reserved | Text cursor end; documented ordinary maximum 7. |
| `0Ch` | all 8 bits | Display-start high byte; with `0Dh`, 16-bit start state. |
| `0Dh` | all 8 bits | Display-start low byte. |
| `0Eh` | bits 3:0 cursor position bits 11:8; 7:4 reserved | Hardware cursor location high part. |
| `0Fh` | all 8 bits | Hardware cursor location low part. |
| `10h` | **different read and write formats**, below | Mode control and timing-write inhibition. |
| `11h` | output tri-state, IRQ controls/status | Also selects which meaning is read from index `12h`. |
| `12h` | character-transfer/sync control **or display sense on read** | Do not collapse these into a single last-write readback byte. |
| `13h` | valid ordinary values `00h,10h,20h,30h` | Character font source block pointer. |
| `14h` | byte count-control value | Number of characters transferred in a vertical interval; text modes only. Exact nondefault count encoding remains open. |
| `20h` | reserved | No documented LCD extension here. |

### 5.2 Index 10h is asymmetric

**Write format**, TR PDF 34 (1-51), Figure 1-39:

| Bit | Meaning |
|---:|---|
| 7 | Inhibit writes to horizontal/vertical timing registers. BIOS sets it after mode set to protect against direct CGA software. |
| 6 | Must be 0; its inverse supplies the ninth bit to vertical comparisons. |
| 5 | Reserved |
| 4 | Clock select; documented required value 1 |
| 3 | Compatibility calculations, including proper horizontal values for 80×25; documented required value 1 in all modes |
| 2 | Reserved |
| 1 | Select mode `11h` |
| 0 | Select 256-color mode `13h`; requires `03DDh` bit 2 also set |

**Read format**, TR PDF 35 (1-52), Figure 1-40:

| Bit | Returned meaning |
|---:|---|
| 7 | 80-column selection, reflecting `03D8h` bit 0; **not the write-inhibit latch** |
| 6 | Reserved |
| 5 | Dot clock undivided/640-pel width when 1; divided-by-two/320-pel width when 0 |
| 4 | 25.175 MHz dot clock selected when 1 |
| 3 | Alphanumeric/text mode when 1 |
| 2 | Double-scanned when 1 |
| 1 | Mode `11h` selected |
| 0 | Mode `13h` selected |

A raw register-array readback fails this contract. Keep the timing-write gate separately from the value synthesized on reads. Also do not treat `09h=07h` as proof of an 8-row text image: the live MCGA mode and font state produce the documented 16-row text.

The manual names horizontal/vertical registers as inhibited, rather than providing an exhaustive per-index write-gate table. Timing indices `00h–07h` are the clear target; effects on other nonstandard writes should be traced rather than using a catch-all “all CRTC writes disabled” flag. Start and cursor movements must continue working after the BIOS protects timing. The Model 25 mode routine clears inhibition before programming and sets it afterwards at `F000:18B4h–18C3h` and `19D9h–19E5h`.

### 5.3 Index 11h: retrace interrupt and sense selection

DOCUMENTED: TR PDF 35 (1-53), Figure 1-41; PDF 48 (1-78).

| Bit | Meaning |
|---:|---|
| 7 | 1 tri-states video output drivers and selects **display-sense** readback at index `12h`; 0 reads normal character-generator/sync control |
| 6 | Read-only IRQ2 status: the video interrupt latch is asserting an interrupt |
| 5 | **Active-low enable:** 0 enables IRQ2; 1 disables it |
| 4 | **Active-low clear:** 0 holds the interrupt latch clear; 1 lets it latch |
| 3:0 | Reserved, should be zero |

Enable sequence: clear bit 4, clear bit 5, then set bit 4. A latched interrupt is not synonymous with “currently in vertical retrace.” Current retrace is read from `03DAh` bit 3. Return IRQ status until the documented clear action, even after the beam leaves retrace. Route this to the machine's **IRQ2**, not an AT cascaded IRQ9 invention. The manual says this video interrupt does not support interrupt sharing; integrate that with the planar interrupt controller, not with a generic ISA edge-toggle shortcut.

### 5.4 Index 12h: font load, syncs, and monitor sense

With index `11h` bit 7 clear, read/write fields are:

| Bit | Meaning |
|---:|---|
| 7 | Load character generator; write clear then set to initiate, reads zero on completion |
| 6 | Load full set during normal display time when 1; restrict loading to vertical blank when 0 |
| 5 | Select generator font page 1 when 1, page 0 when 0, for use/load |
| 4 | Enable 512 displayable character definitions, using attribute bit 3 as page select; 0 uses 256 definitions and bit 5 selects active page |
| 3 | Reserved, must be zero |
| 2 | Enable HSYNC and VSYNC outputs |
| 1 | Positive VSYNC polarity when 1 |
| 0 | Positive HSYNC polarity when 1 |

TR PDF 36 (1-54) has loose wording that the character generator “loads the display memory”; the diagram and font chapter establish **DRAM staging → character SRAM** as the relevant operation. Do not reverse the transfer and overwrite the framebuffer merely by setting bit 7.

With index `11h` bit 7 set, index `12h` **reads monitor-sense levels**. Figure 1-43, PDF 36 (1-54), gives bits 1:0:

| Sense value | Printed interpretation |
|---:|---|
| `00b` | Reserved |
| `01b` | Analog monochrome display |
| `10b` | Analog color display |
| `11b` | LCD attached |

The planar POST nevertheless interprets the clinical attachment as **no analog monitor** (PDF 27, 1-37). These are compatible statements at different firmware layers: do not fabricate an analog-monochrome sense value to get an unmodified baseline POST to initialize the LCD. The upper sense bits and any read behavior while outputs are changing need hardware evidence.

## 6. MCGA formatter and DAC ports

### 6.1 Formatter control/status

DOCUMENTED: TR PDF 36–38 (1-55–1-59), Figures 1-44–1-48.

| Port | Fields and effect |
|---:|---|
| `03D8h` | bit 5 blink enable; bit 4 640×200 monochrome/mode 6; bit 3 video/image enable; bit 2 B&W selection; bit 1 320×200 graphics/modes 4–5; bit 0 80-column text; bits 7:6 reserved |
| `03D9h` | bit 5 mode-4/5 color set; bit 4 alternate intensity; bits 3:0 background/foreground palette-code selection; bits 7:6 reserved |
| `03DAh` | read-only status: bit 3 vertical sync; bit 0 **negative display enable**; all other bits reserved |
| `03DBh/03DCh` | Reserved here; not an implemented CGA light-pen interface merely because those ports exist on older adapters |
| `03DDh` | bit 7 **negative readable-DAC indication**: 0 readable DAC, 1 non-readable type; bit 2 enables 256 colors; bit 0 reserved zero; other bits reserved |
| `03DEh/03DFh` | Reserved; no PCjr/JX page register |

For modes 6/11, `03D8h` bit 2=1 selects formatter color codes 0 and 7; bit 2=0 selects background code 0 and foreground code from `03D9h[3:0]`. The clinical LCD does not subsequently interpret those codes through programmable RGB palette RAM. For modes 4/5, `03D9h` chooses the compatibility color codes below:

| Pixel pair | Set 0, normal | Set 1, normal | Set 0, intensified | Set 1, intensified |
|---:|---:|---:|---:|---:|
| `00b` | selected background | selected background | selected background | selected background |
| `01b` | `02h` | `03h` | `0Ah` | `0Bh` |
| `10b` | `04h` | `05h` | `0Ch` | `0Dh` |
| `11b` | `06h` | `07h` | `0Eh` | `0Fh` |

This table describes the inherited **formatter/DAC-facing color codes**. The LCD's documented rule for modes 4/5 is instead that **C1 is significant** (§9). A renderer that first converts every pair to an RGB value and thresholds brightness can give a superficially plausible but wrong clinical image.

`03DAh` must be time-derived. Bit 0 is negative display-enable, not the 5140's read-toggle status and not a JX positive-display-enable count. Reading the same address twice without advancing enough emulated time need not change either status bit. Polling cannot be implemented as “alternate 0 and 9 until BIOS is happy.”

### 6.2 Palette RAM remains real even though the LCD bypasses it

There are **256 color entries**, each with red, green and blue components of **6 bits** each. Preserve this programmable/readable state for BIOS and programs even though changing it is not the documented path to change the LCD image.

| Port | Required operation |
|---:|---|
| `03C6h` | PEL mask, ordinary initialization `FFh`. The 7690 manual says mask operations are unsupported and this value should not be changed. Preserve compatibility state; do not use mask writes as an invented LCD grayscale palette. |
| `03C7h` write | Select palette read address and begin the red/green/blue read sequence |
| `03C7h` read | Low bits 1:0 report last palette command: `00b` write cycle, `11b` read cycle; `01b/10b` reserved. It is **not a read of the selected palette address**. |
| `03C8h` | Palette write address, eight-bit index |
| `03C9h` | One 6-bit component at a time: red, then green, then blue; bits 7:6 unused |

A complete access state machine includes address, component phase and read/write command state. Burst operations progress through entries after complete RGB triplets; exact behavior of malformed mixed read/write sequences and end-of-table wrapping should follow the identified DAC, not a host palette API. The book recommends disabling interrupts around a component sequence because a nested caller can disturb it. That warning would be meaningless if every `03C9h` write were treated as a whole RGB entry.

DOCUMENTED: TR PDF 38–40 (1-59–1-62), Figures 1-49–1-50. `AH=10h` subfunctions `10h/12h/15h/17h` set one/set block/read one/read block; component registers for a single entry are DH=red, CH=green, CL=blue, and blocks use packed RGB triples at `ES:DX`.

`AX=101Bh` converts palette entries to gray using a documented weighted sum of **30% red, 59% green, 11% blue** and writes the result to all three components. Original RGB values are lost unless the caller saved them. `AH=12h, BL=33h` enables/disables automatic summing during palette loading. These are **analog palette services**, not documented temporal gray generation in the LCD. Exact rounding belongs to firmware; the percentage statement alone does not prove a byte-exact rounding rule for a replacement BIOS.

## 7. The documented initialization tables

These are **DOCUMENTED BIOS parameter values**, not an observed clinical adapter-ROM trace, not reset defaults, and not the LCD-register initialization sequence. Sources: TR PDF 43–44 (1-69–1-70), Figures 1-56–1-58; image-checked against Model 25 TR PDF 75–76. `XX` means unspecified/not relevant in the table; it is not a zero write.

### 7.1 Memory controller

| Index | `00/01` | `02/03` | `04/05` | `06` | `11` | `13` |
|---:|---:|---:|---:|---:|---:|---:|
| `00` | 30 | 30 | 30 | 30 | 30 | 30 |
| `01` | 27 | 27 | 27 | 27 | 27 | 27 |
| `02` | 2A | 2A | 2A | 2A | 2A | 2A |
| `03` | 26 | 26 | 26 | 26 | 26 | 26 |
| `04` | B0 | B0 | B0 | B0 | FF | B0 |
| `05` | 0D | 0D | 0D | 0D | 0A | 0D |
| `06` | 8F | 8F | 8F | 8F | DF | 8F |
| `07` | 9B | 9B | 9B | 9B | E9 | 9B |
| `08` | XX | XX | XX | XX | XX | XX |
| `09` | 07 | 07 | 01 | 01 | 00 | 00 |
| `0A` | 06 | 06 | XX | XX | XX | XX |
| `0B` | 07 | 07 | XX | XX | XX | XX |
| `0C` | 00 | 00 | 00 | 00 | 00 | 00 |
| `0D` | 00 | 00 | 00 | 00 | 00 | 00 |
| `0E` | 00 | 00 | XX | XX | XX | XX |
| `0F` | 00 | 00 | XX | XX | XX | XX |
| `10` | 18 | 18 | 18 | 18 | 1A | 19 |
| `11` | 30 | 30 | 30 | 30 | 30 | 30 |
| `12` | 46 | 46 | 46 | 46 | 04 | 46 |
| `13` | 00 | 00 | XX | XX | XX | XX |
| `14` | FF | FF | XX | XX | XX | XX |

The `10h` values shown are the programming values **before** final timing-write inhibition. The register prose says BIOS subsequently sets bit 7. Also note the ninth vertical bit: `8Fh` with the implicit high bit is `18Fh`, consistent with a 400-line count representation, and `DFh` becomes `1DFh`, consistent with 480. This is a useful constraint, not license to derive all CRTC off-by-one rules from one table.

### 7.2 Formatter

| Port | `00/01` | `02/03` | `04/05` | `06` | `11` | `13` |
|---:|---:|---:|---:|---:|---:|---:|
| `03C6` | FF | FF | FF | FF | FF | FF |
| `03D8` | 28 | 29 | 0A | 18 | 18 | 08 |
| `03D9` | 30 | 30 | 30 | 3F | 3F | 30 |
| `03DD` | 00 | 00 | 00 | 00 | 00 | 04 |

`03DAh` and reserved ports are not mode-setting data. The grouped values do not resolve the adapter's remapped color/B&W variants or the mode-5 discrepancy. Do not force a clinical mode change to be exactly this four-port sequence without the missing ROM.

### 7.3 Default 16-entry DAC palette, not an LCD gray map

Figure 1-58 explicitly says the following information is **not applicable to the LCD**:

```text
index: R  G  B       index: R  G  B
 00:  00 00 00        08:  15 15 15
 01:  00 00 2A        09:  15 15 3F
 02:  00 2A 00        0A:  15 3F 15
 03:  00 2A 2A        0B:  15 3F 3F
 04:  2A 00 00        0C:  3F 15 15
 05:  2A 00 2A        0D:  3F 15 3F
 06:  2A 15 00        0E:  3F 3F 15
 07:  2A 2A 2A        0F:  3F 3F 3F
```

`AH=12h, BL=31h` controls whether default palette loading occurs on mode set; AL=0 enables, AL=1 disables. TR PDF 119 (6-23) says mode `13h` normally loads the first **248** entries, other modes the first 16. The full 248-entry sequence is not reproduced here because no authentic clinical ROM table was supplied. Preserve entries not written by the guest rather than fabricating a complete VGA default table.

## 8. LCD controller: F304h/F305h

### 8.1 One index/data interface; normal/base labels are not a proved bank switch

DOCUMENTED: TR PDF 41–42 (1-64–1-67), Figures 1-51–1-55.

```text
OUT F304h, index       select an eight-bit LCD register index
OUT F305h, value       write selected register
IN  value, F305h       read selected register where supported
IN  value, F304h       read index latch
```

Both ports are listed read/write. All **eight** index bits are register select; `FFh` is the reset command register, and `10h–FEh` are reserved. Figure 1-52's rasterized address labels are `F304h/F305h`; the OCR's `F384h/F385h` is wrong.

The book splits register descriptions into **Normal Mode** (`00h–03h`) and **Base Mode** (`0Dh–0Fh`, `FFh`). The address list is one space, the index ranges do not overlap, and **no separate bank-select transaction is documented**. Do not invent `F304h` bit 7 as a bank bit, duplicate sixteen registers into two banks, or equate “Base Mode” with a VGA unlock sequence. Index `0Eh` has real normal/test and read-clock controls, but neither the book nor the observed diagnostic turns them into a documented alternate bank of identically indexed registers. Preserve mode-dependent behavior where evidenced; leave any additional access-gating mechanism open.

### 8.2 Complete published register inventory

| Index | Published name / fields | Access and boundary |
|---:|---|---|
| `00h` | Start Address Pointer H: table says bits **4:0**, 7:5 reserved | R/W. Prose says bits **5:0**; binary comparison mask is `1Fh`. Conflict detailed below. |
| `01h` | Start Address Pointer V, bits 7:0 | R/W |
| `02h` | bit 0 `+ Reverse video`; bit 7 labelled **`320(H) +Mode45 / +Mode13`**; bits 1–6 reserved | All eight bit rows are marked R/W. The mode-selection label is not a complete truth table. |
| `03h` | low nibble reserved R/W; high nibble reserved | No documented rendering function; diagnostics compare the low nibble. |
| `04h` | Reserved in published index list | **BINARY:** used as a RAM address selector, not safe to ignore. |
| `05h` | RAM row address | Named but no full bitfield/address formula in the TR; binary transactions below. |
| `06h` | Upper RAM data | Named data path; diagnostic byte reads/writes observed. |
| `07h` | Lower RAM data | Named data path; diagnostic byte reads/writes observed. |
| `08h/09h/0Ah` | Reserved | No documented functional fields |
| `0Bh` | Reserved | **BINARY:** timing/status and test-mode readback behavior are required. |
| `0Ch` | Reserved | Exempt from zero-on-reset rule; **BINARY:** a write-zero/read-bit-7 check exists. |
| `0Dh` | bit 0 `-YDIS (+LCD enable)`; bit 1 `+BLOFF (-LCD backlight enable)`; bits 7:2 reserved | R/W; two power domains, not a color register |
| `0Eh` | bit 0 `+Normal / -Test Mode`; bit 1 `+Rd nml / -Rd tst Clock mode`; bit 2 reserved; bit 3 `+Color(P2) emulation reverse`; bit 4 `+320 / -640 (H) mode`; bits 5–6 reserved; bit 7 `+Border Reverse` | R/W on defined fields; binary test compares more bits than the prose assigns functions to |
| `0Fh` | LP period, bits 7:0 | R/W. Clock/divisor/phase formula not supplied. |
| `10h–FEh` | Reserved | Do not alias these onto low-nibble registers. |
| `FFh` | Master LCDA reset | Write-only command. Selecting an index is not the same transaction as writing its data. |

The reset note on printed 1-67 states that system reset or master reset clears all registers **except `00h,01h,0Ch,FFh`**. It does not specify the exceptions' reset values and does not state that image SRAM is cleared. Do not claim a complete reset image, or erase all video memory whenever the reset index is touched. The diagnostic uses the ordinary write helper to write `FFh`, without relying on a documented data value; treat command data-value restrictions as unestablished rather than demanding an invented magic byte.

### 8.3 Image position: a genuine source conflict

The image-checked Figure 1-54 gives H pointer bits **4:0**. The adjacent prose gives **5:0**. The diagnostic's mask for register `00h` is `1Fh`, independently supporting a **five-bit tested readback field**; it does not prove bit 5 has no physical effect.

More seriously, printed 1-67 says:

- Start Address Pointer **H defines the top border**.
- Start Address Pointer **V defines the left border**.
- Horizontal delay is in dot clocks, with maximum **±8 pels**.
- Vertical delay is in HSYNC rows, with maximum **±128 lines**.

These statements cannot be silently combined into the conventional assumption “H is horizontal, V is vertical, both are unsigned origin offsets.” There is no supplied encoding formula, signed-bias rule, wrap rule, or cold-start pair. Keep raw register values and a clearly identified provisional transform if rendering before hardware measurements. The **BIOS-level** vertical offset ABI is much clearer (§11); it must not be filled with a guessed raw-register number just because the same word “offset” appears in both places.

### 8.4 Active image reverse versus porch reverse

DOCUMENTED: `02h` bit 0 reverses the video **only over the screen area used by the current mode**. `0Eh` bit 7 reverses the **top and bottom porch/border regions**. They are independent. Four combinations are meaningful:

| Active reverse | Border reverse | Required distinction |
|---:|---:|---|
| 0 | 0 | Neither domain inverted |
| 1 | 0 | Active picture inverted; top/bottom borders unchanged |
| 0 | 1 | Picture unchanged; top/bottom borders inverted |
| 1 | 1 | Both domains inverted |

Do not invert the entire host window for `02h` bit 0. Host letterboxing outside the physical LCD is not a guest-controlled LCD porch. Also keep `0Eh` bit 3, **Color(P2) emulation reverse**, as distinct state: its name is not permission to collapse it onto the ordinary active-image reverse bit. Its precise digital-input truth table is **OPEN**.

### 8.5 LP period, normal/test clocks, and frame-rate control

The LCD is a split-panel device: both halves must be drawn at once, whereas the MCGA produces their data at different times. The interface's two 32 KiB buffers store image data for that conversion (PDF 40, 1-63). A renderer must not confuse these conversion buffers with two selectable DOS pages.

`0Fh` is named **LP period**, and `0Eh` bits 0/1 select normal versus test operation/read clock. This is real timing/control state. However, the source gives no LP-period unit, prescaler, terminal-count equation, reset value, documented mode table, or specific frame-rate-control gray algorithm. **There is no documented multi-level LCD gray/FRC register bank in this material.** The words “64 shades of gray” in MCGA tables describe the analog monochrome palette output, not this binary LCD.

A faithful implementation should separate capture timing from panel-readout timing and keep progress stable across a save/restore. It must not invent temporal dithering to reproduce analog DAC luminance. If a provisional renderer skips cycle-accurate split-panel buffering, state that limitation explicitly: matching a static image is not proof of the diagnostic RAM or LP clock paths. Physical panel scan frequency, relative phase, buffer ownership switches, and any undocumented FRC behavior remain measurement work.

## 9. Digital-to-LCD mapping is not RGB luminance conversion

DOCUMENTED ordinary behavior:

1. **Text color codes:** odd-numbered colors appear white; even-numbered colors appear black. Foreground/background parity matters, not the DAC's RGB contents. TR PDF 29 (1-41), PDF 143 (7-3).
2. **Modes `04h/05h`:** the high bit **C1** of each two-bit pel is significant; `00b/01b` are black and `10b/11b` are white. TR PDF 30 (1-42), explicit boxed note. This differs from applying text-style parity to the raw two-bit pel.
3. **Modes `06h/11h`:** one bit defines each pel, most-significant bit first. The documented default black/white operation must remain binary; programmed formatter foreground-code effects and LCD emulation reverse controls should be retained rather than bypassed by a permanent “all set bits white” shortcut for arbitrary register configurations.
4. **Mode `13h`:** byte-per-pel MCGA memory organization is documented, as is two-color LCD output. The manuals do not provide a complete eight-bit input-to-LCD truth table. Do not threshold the DAC, invent 256 LCD gray levels, or present a claimed authentic mapping based solely on the generic odd/even text-color advice.

An implementation can structure ordinary rendering as:

```text
fetch text or graphics data
    -> MCGA character/pel interpretation, cursor/blink, formatter mode
    -> digital signal selected for the clinical conversion mode
    -> LCD active-area/border placement and their separate inverse controls
    -> LCD driver/backlight/power availability
    -> uncalibrated or measured optical presentation
```

For supported default text/mode-4/5 rendering the first two ordinary mapping rules above are concrete acceptance criteria. The generalized digital truth table for nondefault formatter selections, `02h[7]`, `0Eh[3:4]`, and mode `13h` is not yet complete. Preserving these control states and identifying an open truth table is better than hiding them behind a generic luminance calculation.

## 10. Three different “color maps”: hardware, BIOS, COLORFIX

### 10.1 BIOS attribute repair

TR PDF 143 (7-2–7-3) documents a BIOS Color Map function, enabled by default, for **`INT 10h AH=09h` text written with different foreground/background combinations**. If both colors have the same odd/even parity, the foreground is changed to opposite parity so the text is visible. Example white-on-blue (`17h`) becomes brown-on-blue (`16h`), black on white at the LCD.

This is a **software write policy**. Programs writing `B8000h` directly bypass it. A renderer that automatically repairs all stored attributes would destroy the distinction and make diagnostic/direct-VRAM images wrong. The manual does not establish that every BIOS text service, scroll fill, or string function receives this repair; do not spread an AH=09h hook to all writes without firmware evidence.

The BDA flag is **`0040:0089h` bit 2**: 0 color monitor/disable Color Map, 1 monochrome/enable Color Map. The same byte's bit 5 is LCD reverse, bit 4 selects 8×16 rather than 8×8 text font, bit 3=0 enables default palette loading, bit 1 enables summing; bits 7:6 and 0 reserved. Source: image-checked TR PDF 139 (6-63), extraction lines 7185–7199. These are firmware-maintained state bytes, not an extra set of hardware I/O registers.

### 10.2 COLORFIX.COM, actual installed hook

BINARY: loose `COLORFIX.COM`, **267 bytes**, SHA-256 **`21f47f663254e2a08dde514d4741a291605f2eefa31fea6fda26c1c8ee912028`**. Its banner identifies “LCD Color Attribute Mapper,” Don D. Williams, IBM 1989, Version 0.0. It is absent from the supplied image directory; do not silently treat it as installed on every boot.

The installer at file `0058h–0093h` / COM `0158h–0193h`:

1. Sets DS to CS and prints its DOS `$`-terminated banner through `INT 21h AH=09h`.
2. Reads the existing INT 10h vector from physical `00040h/00042h` and stores it at its own COM offsets `0120h/0122h`.
3. Reads **`0040:0096h`**, ANDs it with `EFh`, and writes it back, clearing bit 4.
4. Installs its handler at COM `0124h` with `INT 21h AX=2510h`.
5. Terminates resident with `INT 27h`, DX=`0157h`.

**The `0040:0096h` write is not the `0040:0089h` Color Map flag.** The TR labels `40:96` bit 4 “101/102-key keyboard installed” (PDF 140, 6-64). The purpose of that installer side effect is unexplained by this routine. Preserve it if running the program; do not repair the disassembly into the address one expected to see.

The resident path is file `0024h–0055h` / COM `0124h–0155h`. Its observable transformation is:

```text
if AH == 09h:
    foreground_nibble = BL & 0Fh
    background_nibble = BL >> 4
    if foreground_nibble != background_nibble:
        if bit0(BL) == bit4(BL):
            BL = BL XOR 01h
far-jump to saved INT 10h vector
```

The hook saves/restores BX around its comparison; the eventual deliberate change is to BL only. It does **not** inspect current video mode, read the BDA Color Map enable flag, access F304/F305, access the DAC, or change the framebuffer itself. Consequently its AH=09h interception is not conditional on alpha mode, even though text visibility is the utility's purpose. Do not add an emulator-side text-mode guard that the actual code lacks.

The initial equality test compares raw nibbles, not blink-decoded colors. Identical foreground/background nibbles remain identical; it does not turn deliberately invisible equal-color cells into visible text. Examples from executing the actual handler:

| BL input | BL forwarded | Reason |
|---:|---:|---|
| `00h` | `00h` | Equal raw nibbles |
| `06h` | `07h` | Different even colors; toggle foreground parity |
| `07h` | `07h` | Already opposite parity |
| `11h` | `11h` | Equal raw nibbles |
| `17h` | `16h` | Different odd colors |
| `77h` | `77h` | Equal raw nibbles |
| `80h` | `81h` | Raw nibbles differ and parity matches; hook is not blink-aware |
| `88h` | `88h` | Equal raw nibbles |
| `F7h` | `F6h` | Different raw nibbles, same parity |

Isolated instruction execution covered all 256 BL inputs for AH=09h: **112 changed, 144 unchanged**. AH values `00h,0Ah,0Eh,10h,11h,13h,FFh` forwarded sample BX=`0217h` unchanged. Installer execution with controlled DOS services captured vector installation and resident size; it changed seeded `40:96=FFh` to `EFh`, while seeded `40:89=FFh` remained `FFh`. These are actual instruction observations with a synthetic old-vector endpoint, not a run under DOS or proof of the missing underlying clinical BIOS.

### 10.3 Keep the layers independent

- **DAC palette:** 256 RGB entries, programmable/readable, not LCD grayscale.
- **Hardware digital mapping:** ordinary parity/C1 rules and LCD control state, applies to direct VRAM and BIOS-written data alike.
- **BIOS/TSR attribute repair:** occurs on selected software calls before a character/attribute write; bypassed by direct VRAM stores.

Changing one must not secretly mutate the others. In particular, COLORFIX is ordinary guest software: preserve interrupt chaining and resident memory, rather than detecting its filename and enabling a host “readability” feature.

## 11. Custom clinical INT 10h ABI and touchscreen consumers

DOCUMENTED: TR PDF 118–119 (6-21–6-22). Every call below uses **AX=`11BAh`**. The function selector is **BH**. The support result is **AH=`BAh`**, not AL=`BAh`, not AX=`11BAh`, and not a documented carry-flag status.

| BH | Inputs | Documented outputs/effect |
|---:|---|---|
| `00h` | Get LCD size | AH=`BAh`; **BX=offset from scanline 0**, **CX=active scanlines**, **DX=“Model 30 video hardware status byte”**, **DI=total physical scanlines** |
| `01h` | BL=offset from scanline 0 | Set LCD vertical position; AH=`BAh` if supported |
| `02h` | BL=0 normal, BL=1 reverse | Normal = white on black; reverse = black on white; AH=`BAh` |
| `03h` | BL=0 backlight off, BL=1 on | Backlight control; AH=`BAh` |
| `04h` | BL=0 low power, BL=1 normal | Power control; AH=`BAh` |
| `05h` | ES:DI string, CX length | Send string to keyboard controller; AH=`BAh`; keyboard/barcode semantics belong in [KEYBOARD.md](KEYBOARD.md)/[PERIPHERALS.md](PERIPHERALS.md) |

The returned DX description is the **book's wording**. It does not make the machine an AT-class Model 30-286 and does not supply a bitfield for every returned status bit. BX is a **word result** even though set-position takes BL as a byte. Out-of-range set-position behavior, clamping/wrapping, return preservation for unused registers, and the exact unsupported-function result are not specified; recover them from adapter ROM or traces rather than inventing a CF error convention.

The supplied touch driver consumes this interface, not merely the framebuffer dimensions. [DRIVER_ABI.md](DRIVER_ABI.md) owns its version-specific hashes/offsets and [TOUCH.md](TOUCH.md) owns coordinate mathematics and hot-key behavior. Integration requirements:

- Query results must describe the **current active LCD image and vertical placement**, including the 400-line area inside the 480-line panel.
- Changing vertical position must update the single authoritative placement used by both LCD rendering and touch conversion. Do not duplicate unrelated “display top” and “touch top” variables.
- The driver's normal/reverse command is an image-polarity operation; it is not the physical contrast slider.
- The driver calls the query while processing input. A constant “640×480 mode” return can leave video apparently correct while producing wrong touches in the 400-line modes.
- Right-shift touch gestures and backlight hooks must run through the same firmware state transitions as application-issued calls; they do not own a second hardware latch.

### Standard INT 10h behavior that matters to the LCD

Retain guest execution of ordinary BIOS functions rather than reimplementing a partial host API:

- `AH=00h`: AL bit 7 inhibits regeneration-buffer clearing, **not all hardware programming**. A font load or LCD reset must not accidentally erase that preserved buffer. Source PDF 114 (6-12).
- `AH=01h–03h/05h`: cursor type, per-page positions, active page; hardware cursor not supported in graphics. Source PDF 114 (6-13).
- `AH=06h/07h`: scroll/clear window using guest attributes and active-page memory. `AL=0` blanks the whole specified window. Source PDF 115 (6-14).
- `AH=08h/09h/0Ah`: read character/attribute, write character+attribute, write character only; do not equate “character only” with overwriting the stored attribute. Source PDF 115 (6-14–6-15).
- `AH=0Ch/0Dh`: graphics pixel write/read. Bit 7 of the write color requests XOR in the supported non-13h graphics modes; mode 13h uses all eight color bits, so bit 7 is not XOR there. Source PDF 115–116 (6-15–6-16).
- `AH=0Eh/0Fh`: teletype and current state; `0Fh` returns AH=columns, AL=current mode, BH=page. Source PDF 116 (6-16).
- `AH=13h`: strings, optional embedded attributes and optional cursor update; CR/LF/backspace/bell are controls rather than glyphs. Source PDF 120 (6-25).
- `AH=12h, BL=32h`: enable/disable **video port and regeneration-buffer address decode**. This is not backlight blanking. AL=0 enables, AL=1 disables, supported return AL=`12h`. Source PDF 119 (6-23).
- `AH=1Ah`: display-combination code read/write; the table lists `00h` no display, `0Bh` analog monochrome, `0Ch` analog color. Actual clinical POST's final code is an adapter-ROM dependency, not a number to infer solely from its two-color LCD. Source PDF 121 (6-26).
- `AH=1Bh`: 64-byte functionality/state result for implementation type BX=0, including a pointer to a 16-byte static capabilities table. Return actual supported modes and current guest state; generic bits for unsupported video modes are not permission to advertise them. Source PDF 121–122 (6-26–6-29).

The BDA includes current mode `40:49`, columns `40:4A`, page length `40:4C`, byte start offset `40:4E`, eight cursor words `40:50–5F`, cursor type `40:60`, active page `40:62`, controller port `40:63`, formatter-mode/color mirrors `40:65/66`, rows `40:84`, character height `40:85`, options `40:87`, display-control flags `40:89`, DCC `40:8A`, and the `SAVE_TBL` pointer `40:A8`. These are **software-visible RAM**, not a substitute for actual register state. Direct hardware writes can diverge from BIOS's remembered state.

## 12. Blanking, backlight, driver power and primary-power loss

### 12.1 Do not collapse independent mechanisms

DOCUMENTED: TR PDF 42–43 (1-66–1-68), PDF 119 (6-22–6-23), PDF 144–145 (7-4–7-6).

| Mechanism | What it controls | What it must not automatically do |
|---|---|---|
| MCGA `03D8h` bit 3 | Image/video enable | Erase VRAM or reset font SRAM |
| MCGA `12h` bit 2 | H/V sync outputs | Become the LCD backlight control |
| MCGA `11h` bit 7 | Output tri-state and sense-read selection | Rewrite the attached-display configuration |
| Planar integrated-video decode | Guest CPU access to video resources | Be confused with an optically dark but running display |
| LCD `0Dh` bit 0 | **1 enables −22.3 V LCD driver supply**, 0 disables it | Clear picture memory just because driver voltage goes away |
| LCD `0Dh` bit 1 | **0 enables backlight**, 1 turns it off | Change pel polarity or DAC palette |
| LCD `0Eh` bits 0/1 | Normal/test and read-clock operation | Be silently forced back to normal on every redraw |
| Loss of primary power | LCD and diskette unavailable under battery operation | Pretend the battery powers a normal visible display |

For lowest consumption the manual recommends disabling driver voltage and backlight and entering test mode. The bit labels make **zero** the test selections for `0Eh` bits 0 and 1; the prose phrase “turn on Test mode” does not mean setting those bits. Preserve polarity explicitly.

The power-control BIOS call is not specified as a byte-for-byte register sequence. Its observable normal/low-power transition is documented; exact sequencing/delays and restoration of prior controller state require adapter firmware. Hardware voltage rise/fall and safe physical power sequencing are also not measured here. A host renderer may show an unavailable panel as dark, but must keep that optical result distinct from binary image data and from system CPU suspension.

### 12.2 Inactivity blanking and keyboard indication are firmware behavior

The book directs applications to turn off the backlight after **five minutes of inactivity**, using `AX=11BAh, BH=03h, BL=0`; BL=1 turns it back on. This is application/firmware policy, **not an autonomous five-minute timeout inherent in the F305h register**.

When the BIOS backlight-off service is used, firmware ensures a visible power-on reminder through keyboard indicators:

- If any indicator is already on, leave existing indicator states alone.
- If all are off, light Scroll Lock.
- Restore original indicator states when backlight is restored.

Directly writing the LCD power register is not documented as itself issuing keyboard commands. Model the indicator preservation in the BIOS/driver interaction, not in the hardware port handler. Keyboard LEDs and backlight state must be restored consistently; [KEYBOARD.md](KEYBOARD.md) owns keyboard command semantics. Primary-power detection and battery behavior are in [PERIPHERALS.md](PERIPHERALS.md).

## 13. Timing and diagnostics: evidence beyond the register book

### 13.1 Two timing domains, one emulated clock

The MCGA register readback documents a **25.175 MHz** dot clock; Model 25 display support describes its analog 31.5 kHz-class scan. The 7690 conversion buffers decouple serial MCGA arrival from split-panel output. Do not derive panel timing from host vsync, equate the LP period with the MCGA vertical total without evidence, or make port status depend on read count.

The initialization tables and diagnostic polling constrain correct behavior but do not give every MCGA compatibility-counter formula. In particular, the constant `01h=27h` across 40/80-column and graphics modes proves that a plain unmodified 6845 counter equation is insufficient. A cycle-accurate implementation needs the inherited MCGA timing model plus measured clinical conversion timing. A static renderer can be useful earlier, but must not claim timing-complete diagnostic compatibility.

### 13.2 Exact diagnostic provenance

| Binary | Bytes | SHA-256 |
|---|---:|---|
| loose `7690diag/IBM7690.DGS` | 10,474 | `e44671fa1565793365a748743e364b4be4027c12f012b9b687c8047b2459fa57` |
| supplied image `ANALYSIS/7690KQPW/IBM7690.DGS` | 11,333 | `be20cd798aef2f63d4c094bf71ebf02376b53fc31011e80a0d8595fa5a3fe4f4` |

The loose listing is [`ANALYSIS/diagnostic_IBM7690_DGS_disassembly.txt`](../ANALYSIS/diagnostic_IBM7690_DGS_disassembly.txt). It is a linear decode containing embedded strings/tables, so addresses are not automatically executable instructions. The cited subroutines have actual callsites and decoded boundaries. The corresponding image LCD block is **`0460h` later** for the routines listed below; this is not a universal relocation for the entire diagnostic.

### 13.3 Reserved LCD index 0Bh has real observable behavior

Loose routine **`12F1h–139Ah`**, image **`1751h–17FAh`**, selects index `0Bh` at `F304h` and polls `F305h`:

- It waits for bit **1** to clear then set, synchronizing twice.
- It waits for `(value & 82h)==0`.
- It counts low/high phase activity using bit **7**, while testing bit 1 for the terminating vertical phase.
- It requires the count to be in **`0186h–019Ah` inclusive**, decimal **390–410**.
- It reads a PIT channel-0 count and requires **`B6C3h–C413h` inclusive**.
- Timeout/count/timing failures return carry set.

This closely parallels the planar `03DAh` routine at loose **`124Bh–12F0h`**, which uses status bit 3 for vertical phase and bit 0 for line/display phase. **INFERENCE:** LCD `0Bh` bit 1 supplies a vertical-phase indication and bit 7 a line/display-phase indication. Exact edge polarity, signal names and phase relation to panel output need measurement. A constant reserved-register zero cannot pass this polling sequence; neither can a generic “return last value written” implementation in normal mode.

Do not turn the PIT range into a claimed measured whole-frame refresh rate. It is the counter value observed at the routine's specific start/stop points, with its own synchronization and timer programming. The machine's PIT must run while the display advances; changing its frequency to compensate for a wrong raster is not an acceptable fix.

The dispatcher distinguishes planar-sync and interface-adapter-sync failures: loose callsites `11E5h/11F8h` store failure selectors `21h/22h`; strings at `0438h/044Bh` identify those paths. Full diagnostic UI/error reporting belongs in [DIAGNOSTICS.md](DIAGNOSTICS.md).

### 13.4 LCD RAM access through indices 04h–07h

The book names `05h` row, `06h` upper RAM data, `07h` lower RAM data, but calls `04h` reserved. The actual diagnostic uses all four:

```text
select 05h; write row
select 04h; write column/address selector
select 06h; write/read upper-byte data
select 07h; write/read lower-byte data
```

Loose routines:

| File range | Behavior | Image start |
|---|---|---:|
| `1407h–145Fh` | Master reset; address-dependent RAM test; constant patterns `00h,FFh,55h,AAh`; return carry on mismatch | `1867h` |
| `1460h–14A0h` | Fill selected upper/lower RAM locations with SI/DI low bytes | `18C0h` |
| `14A1h–14E1h` | Fill upper bytes with column selector and lower bytes with row selector | `1901h` |
| `14E2h–1551h` | Read/compare address-dependent patterns | `1942h` |
| `1552h–15C5h` | Read/compare constant patterns | `19B2h` |

Rows descend **`80h` through `01h`**, columns descend **`40h` through `01h`**. Before reading each tested column, the verification routines select column **zero** and write zero to both data ports, then select the target column and compare. Consequently column zero must not alias every nonzero column; in particular blindly masking `40h` to zero can invalidate the first comparison. This deliberate disturbance helps expose address-decoding faults that a single-value echo would miss.

An isolated execution of the actual `1460h` fill routine, with OUT logging and controlled IN results, captured **128 row writes**, **8,192 column writes**, **8,192 upper-data writes** and **8,192 lower-data writes**. First data transactions were `05←80,04←40,06←55,07←AA`; final tested column was `01h` in row `01h`. The evidence file records the actual trace endpoints/counts. No LCD hardware model was supplied to make this experiment “pass.”

**Reproducible extension:** [video_trace.py](../TOOLS/video_trace.py) and [VIDEO-TRACE.json](../ANALYSIS/VIDEO-TRACE.json) execute those fill routines **and both verification routines in both supplied DGS revisions**. The explicit fixture retains full-byte row/column selectors and separate upper/lower RAM dictionaries. Intact constant/address patterns return carry clear; a corrupted upper constant byte or lower address byte returns carry set. A second fixture deliberately masks the column to six bits and fails the address test because column40h aliases the verifier's zero-column disturbance. This rejects that simple decoder/write model; it does not resolve possible physical pipeline/strobe semantics or prove an eight-bit real RAM address bus.

The same tool reproduces all256 COLORFIX attribute cases and both14/16-row font-staging cases. Its107-byte retained font window is unchanged **Model25** code, independently matched to the identified full comparative ROM when run with `--model25-rom`; it is not a7690 firmware substitute.

**OPEN:** how these selectors map to the full physical 32 KiB chips, additional address bits/banks, scanout organization, auto-increment behavior, and the relationship to normal/test read clocks. The tested 8,192 selector combinations per data port do **not** prove that each physical chip is only 8 KiB, nor that a 64 KiB framebuffer should be addressed by this simple two-dimensional formula. Keep the documented capacity and the observed diagnostic address subset separate.

### 13.5 Readback masks are observations, not writable-bit definitions

Loose `15C6h–162Bh` performs master reset, sets index `0Eh` to zero, then conducts two XOR-pattern write/read sweeps over indices `00h–0Eh`, comparing under the table at **`162Ch–163Ah`**. The image has the same bytes at **`1A8Ch–1A9Ah`**:

```text
index: 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E
mask:  1F FF FF 0F 00 00 00 0F 00 00 00 83 00 03 FB
```

Each sweep evolves BL with XOR `55h` or `AAh` and masks it after the comparison; it is not simply a constant byte written to every register. The setup puts the controller into **test/alternate-read-clock state**, so do not impose normal timing-status semantics on every test-mode `0Bh` read.

Important consequences:

- `00h` is compared under `1Fh`, supporting the table's five-bit H readback field.
- All of `02h` and the low nibble of `03h` are tested for retention even though the manual labels many fields reserved.
- `0Bh` is compared under `83h` in this test configuration, although it supplies changing timing bits during the normal timing check.
- `0Dh` low two power bits are compared.
- `0Eh` is compared under `FBh`, excluding only bit 2; this includes bits 5 and 6 that the manual calls reserved. Preserve observable readback without assigning invented image effects to those bits.
- A zero mask means **the diagnostic does not compare that register here**, not that hardware reads zero or ignores writes. Index `04h` is the immediate counterexample.

Loose **`139Bh–13ADh`**, image **`17FBh–180Dh`**, separately writes zero to `0Ch`, reads it, and fails if bit 7 remains set. The manual exempts `0Ch` from reset-to-zero but provides no register function. Record this minimal observed requirement without renaming it an interrupt/status/reset latch whose full behavior has not been recovered.

## 14. State ownership and save/restore contract

A useful emulator representation separates at least:

| State owner | Persistent guest-visible state |
|---|---|
| Planar decoder | Integrated video enable/address-decoding state |
| MCGA memory controller | Index latch; programmed timing; write-inhibit latch; mode controls; start/cursor addresses; IRQ enable/clear/latch; sync/font control; display-sense input configuration |
| MCGA formatter | Mode, border/color selection, extended mode, timing-derived status inputs |
| MCGA memory | 64 KiB DRAM and independent 8 KiB character SRAM; in-progress font transfer and source/destination selection |
| DAC | 256 RGB entries, PEL mask state, read/write command/address/component phase |
| LCD controller | Full index latch; raw defined/tested register values; active and border polarity; mode/test clocks; LP-period state; RAM selectors; capture/readout positions |
| LCD storage | Both 32 KiB SRAMs and any evidenced capture/readout selection state |
| Power/optics | Driver voltage enabled, backlight enabled, primary-power availability; separately measured or uncalibrated optical response |
| Guest RAM/firmware | BDA video state, INT vectors, auxiliary font tables, touch-driver variables, COLORFIX resident code and old vector, indicator-save state |

A save state must not reconstruct everything from the last INT 10h mode or currently visible pixels. That loses offscreen pages, staged versus active fonts, DAC phase, incomplete transfer state, the IRQ latch, diagnostic memory and the LCD index latch. Host image caches can be regenerated; guest memory and device state cannot.

Read-modify-write operations must preserve unrelated state where the device supports it, but an asymmetric register such as MCGA index `10h` needs special care: its read format is not its write image. Do not expose a host-side register accessor that assumes every port is a symmetric byte latch. Raw register fields whose functional interpretation remains open should remain distinguishable in traces/save states, not be silently discarded.

## 15. Practical rendering and failure scenarios

These are acceptance scenarios for a downstream implementation. They have **not** been run against a complete emulator here.

### Modes and storage

1. **CGA line-bank boundary:** write distinct patterns to `B8000h` and `BA000h`; modes 4–6 alternate even/odd logical rows correctly and double-scan as appropriate, without using a contiguous 16,000-byte raster.
2. **Mode 11h packing:** place bits at `(0,0)`, `(639,0)`, `(0,479)`, `(639,479)`; exactly those physical pels are selected before polarity, using 80 bytes/row and no VGA planes.
3. **Page ownership:** prepare two text pages with different contents/cursor positions, switch active page, and change the inactive one. Only display-start changes select the new visible page; changing an offscreen page does not select it.
4. **No-clear mode set:** set bit 7 in AL and inspect preservation of actual VRAM, not just the host screenshot. Font/LCD reinitialization must not erase the preserved store as a side effect.
5. **Mode remapping:** request `03h`, query `0Fh`, require `02h` as the diagnostic does. Record real mode-5 behavior separately to resolve the document conflict; do not bake either disputed result into an unlabelled acceptance oracle.

### Text, fonts and color

6. **Direct versus BIOS attribute writes:** write `17h` directly to text VRAM and through AH=09h with Color Map enabled/disabled. Direct memory retains equal-parity visibility behavior; only the documented software path repairs it.
7. **Four mode-4 pel values:** display `00,01,10,11` side by side. The ordinary LCD result is black, black, white, white, independent of analog RGB palette edits; not text-style even/odd alternation.
8. **DAC isolation:** write/read a nondefault RGB triplet, interrupt/restart a triplet sequence, and verify component/address state. Those writes must not turn the physical LCD into color or calibrated grayscale.
9. **Staged versus active font:** load a visibly different font into unused block 2 while displaying block 0. Text must not change until block activation/transfer. Then activate block 2 and confirm the change without rewriting text cells.
10. **512-character font select:** use two different glyphs for the same character code on pages 0/1 and toggle attribute bit 3. Verify glyph selection independently of analog intensity and ordinary LCD reverse.
11. **Cursor end semantics:** use CH=6, CL=7 in 400-line text and observe rows 12–13; hide with bit 5; ensure no hardware cursor appears in graphics. Compare odd/out-of-range shapes with hardware before asserting their results.
12. **COLORFIX semantics:** run the actual utility and inspect chained AH=09h attributes. Equal raw nibbles stay equal, `17h→16h`, other AH values bypass, and BDA `40:96` bit 4 is actually cleared. Do not replace this with a filename-triggered readability option.

### LCD state, power and input integration

13. **Independent inverse domains:** in a 400-line mode, toggle active reverse and border reverse in all four combinations. The 40-line top/bottom regions and the image must be independently distinguishable; host margins outside the LCD are unchanged.
14. **Vertical positioning and touch:** query size/position, move the image with BH=01h, query again, and touch the same physical locations. Rendering and driver conversion consume one updated origin. The return support signature is AH=BAh.
15. **Backlight versus data:** disable only the backlight. VRAM, fonts, LCD buffers and active mode remain intact; restoring light reveals the appropriate retained/current picture rather than reinitializing DOS video.
16. **Power/indicator restoration:** with all LEDs off, invoke the BIOS blanking call and observe its Scroll Lock reminder; with a preexisting LED on, preserve it; restore saved indicator states on backlight-on. Direct F305h writes must not spuriously synthesize BIOS keyboard operations.
17. **Primary-power loss:** keep the CPU/keyboard/battery model consistent with [PERIPHERALS.md](PERIPHERALS.md), while the LCD is unavailable. Do not recover visibility merely because the backlight register remains logically enabled.

### Polling, readback and errors

18. **MCGA asymmetric readback:** write timing inhibition in index 10h, then read 10h in 40/80-column modes. The returned bit 7 tracks 80-column selection, not the inhibition latch; timing writes remain protected while cursor/page operations work.
19. **Interrupt latch versus current retrace:** enable IRQ2 with the documented sequence, cross retrace, leave retrace and read both status interfaces. The interrupt remains latched until cleared while `03DAh` returns the current beam state.
20. **LCD sync diagnostic:** execute the real `0Bh` polling routine with modeled PIT/display time. Let wrong scan counts and timing genuinely fail. Never force carry clear or fabricate success status because the display looks correct.
21. **LCD RAM decoder:** execute the address-pattern test, including destructive writes to column zero, against persistent independent upper/lower RAM. Deliberately alias a column or swap the two data paths and require a real mismatch.
22. **Readback in test mode:** execute the two register sweeps with the documented binary masks. Reserved-but-tested bits must round-trip as required without invented display effects; switching out of test mode restores timing-dependent reads rather than a permanent echo.
23. **Reserved/unsupported programming:** log nonstandard accesses and preserve specified state; avoid host exceptions. Reserved indices must not alias reset or power registers due to overaggressive low-nibble masking. No particular unknown read value is an authentic oracle until measured.

## 16. Remaining evidence needed for full fidelity

The following gaps have concrete consequences; they are not permission to substitute generic VGA:

1. **Authentic clinical planar and 16 KiB adapter ROM dumps.** Needed for POST sequencing, final DCC/BDA initialization, mode remapping (especially mode 5), the `11BAh` implementation, LCD initialization values, clock/power transitions and BIOS attribute repair. Baseline Model 25 ROM is not this firmware.
2. **LCD-controller register traces at reset and each BIOS mode set.** Capture F304/F305 and MCGA writes with timestamps, both ordinary and no-clear sets; determine any access gating behind “Normal”/“Base,” rather than assuming a bank mechanism.
3. **Horizontal/vertical pointer encoding.** Resolve 5/6-bit H width, the contradictory axis prose, offsets, signed bias, rollover and clipping; correlate raw registers with BH=00h/01h results and photographed pixel position.
4. **Complete RAM addressing/capture/readout map.** Identify index 04h width, all row/bank bits, whether 06h/07h have increments/latches, test-clock behavior, and how diagnostic accesses relate to both physical 32 KiB chips and split-panel scanout.
5. **LP and timing signals.** Measure LP period, panel frame/line phases, index 0Bh waveform, index 0Ch behavior and reset exceptions. Use the diagnostic's count/PIT limits as software constraints, not replacement measurements.
6. **Digital conversion truth table.** Test text all attributes, every mode-4/5 pair, mode-6/11 foreground selections, all 256 mode-13 codes, both inverse controls, Color(P2) emulation reverse, and both 320-mode controls. Do not conflate DAC colors with digital bit selection.
7. **Panel geometry and optics.** Measure active-area width/height and pixel pitch; capture brightness/contrast extremes, response/persistence, backlight-off appearance and power recovery. No calibrated RGB or physical-pixel aspect claim is currently justified.
8. **MCGA nondefault timing/font edges.** Determine exact compatibility-counter formulas, partial font-transfer count and timing, mid-transfer writes, invalid cursor shapes, and unused CPU aperture mirrors. The inherited baseline sharply narrows the investigation but does not measure the modified clinical board.

The immediately implementable core is substantial: MCGA memory/formatter semantics, explicit staged fonts, the published LCD index/power/inverse fields, the custom BIOS consumer contract, and the concrete diagnostic access sequences. What remains open is specifically the missing firmware and unmeasured controller/optical behavior—not a reason to erase the distinction between MCGA, DAC, digital conversion, and LCD.
