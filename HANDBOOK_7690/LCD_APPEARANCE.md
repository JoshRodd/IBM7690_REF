# IBM 7690 LCD appearance and temporal response

Research date: 2026-09-15. Based on the eight supplied photographs in
[colours](../colours/) and the existing [video hardware chapter](VIDEO.md).
These are estimated sRGB presentation presets, not calibrated panel measurements.
The response model is deliberately borrowed from the IBM 5140 PC Convertible,
as requested; no 7690 optical timing was measured.

## Recommended starting values

| Appearance preset | Pixel 0 / background | Pixel 1 / foreground |
|---|---|---|
| Warm yellow, dark marks | **`#E8DB9B` — RGB (232, 219, 155)** | **`#554B4A` — RGB (85, 75, 74)** |
| Dark, pale marks | **`#292E47` — RGB (41, 46, 71)** | **`#B5C8C4` — RGB (181, 200, 196)** |

The yellow preset has a warm cream-to-yellow background and a muted brown-grey
foreground. The dark preset has a very dark blue-grey background and a pale,
slightly green/cyan-grey foreground. Neither pure black nor pure white reproduces
the supplied dark-profile photographs particularly well.

These bit labels follow the requested presentation convention. Apply the actual
LCD conversion and active/border reverse controls before selecting a displayed
endpoint; they do not necessarily describe a raw MCGA video-memory bit. See
[VIDEO.md](VIDEO.md) for the hardware mapping and independent inverse domains.
Keep the colour preset separate from the guest's reverse-video setting.

## What the pictures support

The five small `7690-*` photographs show a bright warm display with dark marks.
The three 768×512 photographs show pale marks on a much darker display.
This supports **two appearance profiles**, but does not establish two manufactured
LCD variants, different backlight technologies, or the reason for the difference.
Brightness/contrast settings, software inversion, viewing angle, illumination,
photographic white balance and panel ageing are unresolved variables.

| Supplied image | Observation and use |
|---|---|
| [7690-1_th.jpg](../colours/7690-1_th.jpg) | Oblique view, pinkish cream/yellow luminous field. Strong viewing-angle/lighting variation; weak endpoint evidence. |
| [7690-2_th.jpg](../colours/7690-2_th.jpg) | Frontal view with the strongest yellow field. Text is very faint at this resolution. Best reference for the saturated yellow end of the warm preset. |
| [7690-3_th2.jpg](../colours/7690-3_th2.jpg) | Dark text on a paler cream/grey field with substantial reflections. Shows that one fixed saturated yellow cannot represent every photographed condition. |
| [7690-4_th2.jpg](../colours/7690-4_th2.jpg) | Large dark filled graphic on a warm light field. Better dark-endpoint evidence than tiny blurred letters, although reflections and possible graphic patterns remain. |
| [7690-5_th2.jpg](../colours/7690-5_th2.jpg) | Yellow/cream display with broad dark horizontal and vertical marks. Supports the warm preset; hand and room reflections affect it. |
| [BASIC screen](../colours/IBM-7690-booting-straight-to-BASIC-768x512.jpg) | Pale green-grey text over a dark blue-grey field. Bright lower-screen reflection is not a different LCD background colour. |
| [Boot screen](../colours/IBM-7690-boot-screen-no-external-keyboard-768x512.jpg) | Dark blue-grey field, pale characters and reverse-text rectangles. Useful dark-field sample; photographer/room reflections remain visible. |
| [External-keyboard screen](../colours/IBM-7690-second-screen-when-external-keyboard-plugged-in-768x512.jpg) | Pale green-grey filled graphic and outlines against a dark field. Large graphic supplies a light-endpoint estimate with less text-edge blending; its fine pattern means it is not proven to be a uniform all-ones patch. |

No supplied photograph positively establishes the fully unpowered appearance.
Do not treat pixel 0, disabled backlight and electrically unpowered glass as the
same state. Existing hardware documentation describes separate driver/backlight
controls and physical brightness/contrast sliders; the photos do not measure
those controls' optical transfer functions.

## Photo sampling and choice of presets

Images were inspected individually. The following are per-channel median RGB
values from rectangular crops of the decoded JPEGs, without white-balance or
exposure correction. Coordinates are `(left, top, right, bottom)` in original
image pixels, with right/bottom exclusive. No upscaling was used for sampling.
These are **photographic samples**, not instrument readings of the panel.

| Image | Region | Median RGB / hex |
|---|---|---|
| `7690-2_th.jpg` | Yellow field `(145,55,179,78)` | (232,217,133), `#E8D985` |
| `7690-3_th2.jpg` | Cream field `(85,55,140,88)` | (205,195,173), `#CDC3AD` |
| `7690-4_th2.jpg` | Dark graphic `(106,41,131,60)` | (85,75,74), `#554B4A` |
| `7690-5_th2.jpg` | Yellow field `(65,42,106,61)` | (237,221,173), `#EDDDAD` |
| BASIC screen | Dark field `(280,190,410,290)` | (47,52,78), `#2F344E` |
| Boot screen | Dark field `(330,220,440,320)` | (36,41,64), `#242940` |
| External-keyboard screen | Light graphic `(280,111,398,192)` | (176,193,187), `#B0C1BB` |
| Boot screen | Reverse-text field `(149,125,267,132)` | (185,207,205), `#B9CFCD` |

The proposed yellow `#E8DB9B` is a hand-selected compromise between the stronger
yellow and warmer cream samples. The dark mark colour uses the large graphic's
median directly. The two dark-profile endpoints are rounded compromises between
the corresponding samples. These choices intentionally describe a representative
appearance rather than claim one photograph's exposure is authoritative.

Confidence is higher in the broad colour families and relative polarity than
in exact RGB channels. In particular, the warm images are only 196–280 pixels
wide, so individual LCD pels and text strokes are not resolved reliably.
JPEG compression, resampling, fine patterns, reflections and local illumination
mix optical states. Even the dark graphic crop ranges from approximately
(68,61,61) to (116,106,104) between its per-channel 10th and 90th percentiles.
That spread is not a confidence interval for the true foreground colour.

For emulator controls, allow the yellow field to shift toward cream and allow
both presets' contrast and brightness to vary. Keep reflections out of the base
palette; a reflection overlay, if desired, belongs to a separate presentation
layer. There is no evidence here for a calibrated set of intermediate grey levels.

## Proposed response time: inherited approximation

Use **100 ms exponential time constants in both directions**, matching the
proposed Convertible model. For either palette, store a normalized per-pixel
optical state `x`, where 0 selects the pixel-0 endpoint and 1 selects pixel 1:

```text
q = final binary LCD target after conversion and reverse controls
x_next = q + (x - q) * exp(-dt / 0.100)   # dt in seconds
linear_RGB = mix(sRGB_decode(pixel_0), sRGB_decode(pixel_1), x_next)
output_RGB = sRGB_encode(linear_RGB)
```

This gives approximately **220 ms for a 10–90% transition**, **300 ms to 95%**,
and **400 ms to 98%** after an ideal step from a settled endpoint. The earlier
5140 video estimate was about **233 ms for 10–90% darkening** and roughly
**0.3–0.5 seconds to near-settling**. Those observations were of the Convertible,
not the 7690. Equal reverse-direction timing is also an assumption, not a
measurement. Use the same timing for both 7690 appearance presets because
these still photographs cannot justify different values.

If the emulator advances the optical model at **50 Hz**, its 20 ms step is:

```text
x_next = x + 0.181269247 * (q - x)
```

That update can be represented by two precomputed transition tables indexed by
current quantized optical state, one for each target bit. Preserve the state
across target changes so interrupted transitions and software PWM work. Ensure
quantization does not leave values stuck short of the endpoints.

**50 Hz here is an optional emulation update cadence, not a measured or documented
7690 panel refresh rate.** Borrow the optical time constant without replacing the
7690's MCGA/conversion-controller timing with the Convertible controller's timing.
For another update interval, recompute `1 - exp(-dt / 0.100)`. The existing
[video timing discussion](VIDEO.md) keeps the buffered LCD output distinct from
the incoming MCGA timing.

## Remaining uncertainties

The supplied images cannot establish absolute chromaticity/luminance, native
pixel contrast, exact hardware revision, response asymmetry, PWM transfer,
backlight-off appearance or the cause of the two colour profiles. A known
binary test pattern, fixed camera exposure/white balance and recorded control
settings would be needed to improve the endpoints. No such new measurement or
video investigation is claimed here.

## Aspect ratio

The device has square pixels with an aspect of ratio of 4:3, with the pixels
being fixed at 640x480. The top and bottom are letterboxed with 40 pixels
each in 400-line modes, such as the default 80x25 text mode, or the doubled
320x200 graphics modes.
