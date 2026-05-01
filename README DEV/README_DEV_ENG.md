# Complete documentation — Beach Satmap Generator

Documented versions: generator `1.3.5` / launcher `1.7.7`.

This document explains how `satmap_generator_optimized_presets.py` and `satmap_gui_launcher.pyw` work, including input files, processing logic, settings, profiles, output files, diagnostics and troubleshooting.

---

## 1. Purpose

The project generates an enhanced DayZ satellite map around coastlines: beaches, sea gradients, seabed tint, surf/foam, wet sand, sand-to-land transitions and terrain-based color correction.

Main inputs:

```text
input/heightmap.asc
input/mask.png
input/satmap.png
input/layers.cfg
```

Main outputs:

```text
outputs/output_Vx/satmap_final_10240.png
outputs/output_Vx/beach_mask_10240.png
outputs/output_Vx/generation_settings.json
outputs/output_Vx/RAPPORT_GENERATION_COMPLET.md
```

---

## 2. Project files

| File | Purpose |
|---|---|
| `satmap_generator_optimized_presets.py` | Generation engine. Can be run from the command line or from the launcher. |
| `satmap_gui_launcher.pyw` | Tkinter GUI used to configure and run the generator without a `.bat` file. |
| `info.png` | Icon used by the GUI help tooltips. |
| `custom_profiles.json` | Created by the launcher to store user profiles. |
| `launcher_settings.json` | Created by the launcher to remember paths and last settings. |

---

## 3. Installation

### Requirements

- Windows recommended.
- Python 3.10+ recommended.
- Python dependencies:

```bash
py -m pip install numpy pillow scipy
```

Tkinter is normally included with Python on Windows.

### Recommended structure

```text
BeachSatmapGenerator/
├─ satmap_generator_optimized_presets.py
├─ satmap_gui_launcher.pyw
├─ info.png
├─ input/
│  ├─ heightmap.asc
│  ├─ mask.png
│  ├─ satmap.png
│  └─ layers.cfg
└─ outputs/
```

The launcher can auto-detect standard files inside `input/`.

---

## 4. Quick start

### GUI mode

Double-click:

```text
satmap_gui_launcher.pyw
```

Then:

1. **1. Files**: check the generator, heightmap, mask, satmap and layers.cfg paths.
2. **2. Profiles**: choose beach width/slope/height, water levels, inland blend, colors and textures.
3. **3. Technical**: configure final resolution, memory/speed and diagnostics.
4. **4. Run**: review the generated command, validate, then launch generation.

### CLI mode

```bash
py satmap_generator_optimized_presets.py ^
  --heightmap input/heightmap.asc ^
  --mask input/mask.png ^
  --satmap input/satmap.png ^
  --layers input/layers.cfg ^
  --beach-layer-names hp_beach ^
  --sand-layer-names hp_sand ^
  --target-size 10240 ^
  --chunk-rows 2048 ^
  --sand-preset 4
```

---

## 5. Required inputs

### `heightmap.asc`

ASC heightmap used to determine water/land, calculate slope, limit sand by maximum altitude and compute shoreline distance.

### `mask.png`

Terrain mask image. Each RGB color must match a layer color defined in `layers.cfg`.

Supported formats: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tif`, `.tiff`.

PNG/BMP/TIFF are strongly recommended. JPG/JPEG is rejected when `--mask-color-tolerance` is `0`, because compression can alter RGB colors.

### `satmap.png`

Base satellite texture. The generator resizes and visually corrects it by terrain category.

### `layers.cfg`

Maps mask RGB colors to DayZ layer names. The generator expects entries like:

```cpp
texture_name[] = {{ R, G, B }};
```

The names used in beach, sand source and inland texture fields must exist in this file.

---

## 6. Internal processing pipeline

1. Read `layers.cfg` and build an RGB → layer legend.
2. Load the ASC heightmap.
3. Resize heightmap, mask and satmap to `target-size`.
4. Calculate normalized slope from the heightmap.
5. Classify mask pixels into terrain categories.
6. Detect the sand source layer from `--sand-layer-names`.
7. Locally dilate the sand source area.
8. Detect water and emerged land from altitude thresholds.
9. Compute distance to shoreline.
10. Build multi-scale noise to avoid flat colors.
11. Apply base satmap color correction by terrain category.
12. Build the sand mask using distance, altitude, slope, source layer and allowed categories.
13. Render water/beach contouring: deep water → shallow water → surf → wet sand → dry sand.
14. Apply the second inland sand-to-land pass.
15. Save `beach_mask_10240.png`.
16. Save the final satmap.
17. Write generation reports unless disabled.

---

## 7. GUI sections

### `1. Files`

Configure generator path, heightmap, mask, satmap, layers.cfg and DayZ textures to recognize.

Vanilla texture list:

```text
cp_grass, cp_dirt, cp_rock, cp_concrete1, cp_concrete2, cp_broadleaf_dense1, cp_broadleaf_dense2, cp_broadleaf_sparse1, cp_broadleaf_sparse2, cp_conifer_common1, cp_conifer_common2, cp_conifer_moss1, cp_conifer_moss2, cp_grass_tall, cp_gravel, en_flowers1, en_flowers2, en_flowers3, en_forest_con, en_forest_dec, en_grass1, en_grass2, en_soil, en_stones, en_stubble, en_tarmac_old, sa_forest_spruce, sa_grass_brown, sa_concrete, sa_beach, sa_forest_birch, sa_gravel, sa_snow, sa_snow_forest, sa_volcanic_red, sa_volcanic_yellow, sa_grass_green
```

### `2. Profiles`

Contains beach profile, water altitude profile, inland blend, sand colors, sand texture, water colors, water texture and seaside finishing.

### `3. Technical`

Contains final size, chunk rows, color block size, mask color tolerance and debug mask creation.

### `4. Run`

Shows the generated command, validation tools, generation actions, log output and progress.

---

## 8. Beach profiles

### Engine presets

| ID | Name | Distance px | Max slope | Max height m | Description |
| --- | --- | --- | --- | --- | --- |
| 1 | tres_propre | 45.0 | 0.16 | 4.8 | Thin, tightly controlled beach |
| 2 | propre_marge | 55.0 | 0.18 | 5.2 | Slightly wider sand without excessive spillover |
| 3 | equilibre | 60.0 | 0.2 | 5.5 | Good baseline setting |
| 4 | large | 70.0 | 0.22 | 6.0 | More visible beaches with safe margin |
| 5 | tres_large | 85.0 | 0.25 | 7.0 | Sand extends farther inland |
| 6 | agressif | 100.0 | 0.28 | 8.0 | May start climbing onto embankments |
| 7 | tres_agressif | 120.0 | 0.32 | 10.0 | High risk of sand too high or too far inland |
| 8 | custom | 70.0 | 0.22 | 6.0 | Custom values from the menu |

### GUI profiles

| GUI profile | CLI preset | Beach width px | Slope | Height m | Use |
| --- | --- | --- | --- | --- | --- |
| 1 - Bord net | 1 | 45.0 | 0.16 | 4.8 | Fine, low-impact beach |
| 2 - Bord naturel | 2 | 55.0 | 0.18 | 5.2 | Moderate margin |
| 3 - Équilibré | 3 | 60.0 | 0.2 | 5.5 | Versatile setting |
| 4 - Plage large | 4 | 70.0 | 0.22 | 6.0 | Versatile wide beach |
| 5 - Grande plage | 5 | 85.0 | 0.25 | 7.0 | More visible sand |
| 6 - Extension forte | 6 | 100.0 | 0.28 | 8.0 | May climb onto embankments |
| 7 - Extension max | 7 | 120.0 | 0.32 | 10.0 | Test only |
| 8 - Personnalisé | 8 | 70.0 | 0.22 | 6.0 | Free values |

Use profile `3` for a balanced baseline and `4` for a wider visible coastline. Profiles `6` and `7` are aggressive and can climb onto slopes.

---

## 9. Water profiles

| GUI profile | Deep water below m | Water up to m | Land from m | Use |
| --- | --- | --- | --- | --- |
| 1 - Standard | 0.0 | 1.0 | 1.0 | Water <= 1.0 m |
| 2 - Littoral bas | 0.0 | 0.8 | 0.8 | Low coastal level |
| 3 - Eau plus large | 0.0 | 1.3 | 1.3 | More visible water |
| 4 - Personnalisé | 0.0 | 1.0 | 1.0 | Free levels |

Rule:

```text
water-start-level < water-end-level <= land-start-level < sand-max-height
```

---

## 10. Inland sand-to-land blend

| GUI profile | Distance px | Strength | Use |
| --- | --- | --- | --- |
| 1 - Désactivé | 0.0 | 0.0 | No inland retouch |
| 2 - Net léger | 12.0 | 0.6 | Halo almost removed |
| 3 - Net naturel | 18.0 | 0.78 | Balanced retouch |
| 4 - Net marqué | 24.0 | 0.92 | More visible transition |
| 5 - Dune courte | 32.0 | 1.0 | Marked short dune |
| 6 - Personnalisé | 18.0 | 0.78 | Free values |

Distance or strength at `0` disables the inland pass. Higher values create a stronger transition but may dirty inland terrain if overused.

---

## 11. Complete CLI reference

| Option | Default | Values | Purpose |
| --- | --- | --- | --- |
| --heightmap | input/heightmap.asc | ASC | Source ASC heightmap used for elevations, water, slopes and coastline detection. |
| --mask | input/mask.png | PNG/JPG/BMP/TIF | Terrain mask image. Its colors must match layers.cfg. |
| --satmap | input/satmap.png | PNG/JPG/BMP/TIF | Base satmap image corrected and enriched by the generator. |
| --layers | input/layers.cfg | CFG | Mapping file between mask RGB colors and DayZ layer names. |
| --output-satmap | outputs/output_Vx/satmap_final_10240.png | PNG | Final satmap image. With the default name, the script creates output_V1, output_V2, etc. |
| --output-beach-mask | outputs/output_Vx/beach_mask_10240.png | PNG | Final beach/water mask. |
| --target-size | 10240 | 512 to 30000 | Final square resolution. DayZ 10K usually uses 10240. |
| --chunk-rows | 512 CLI / 2048 GUI | 64 to 8192 | Rows processed per chunk. Higher is faster but uses more RAM. |
| --block-size | 32 | 4 to 512 | Size of terrain color correction blocks. |
| --sand-preset | manual/default or GUI profile | 1-8 or name | Beach preset used as a base before manual overrides. |
| --sand-distance | preset | 1 to 300 px | Maximum distance from shore where sand can be generated. |
| --sand-slope-max | preset | 0.01 to 1.00 | Maximum allowed normalized slope. Lower values avoid cliffs and embankments. |
| --sand-max-height | preset | 0.1 to 50 m | Maximum elevation where sand may appear. |
| --water-start-level | 0.0 | -100 to 100 m | Below this threshold, water is treated as deeper/darker. |
| --water-end-level | 1.0 | -100 to 100 m | Upper elevation threshold treated as water. |
| --land-start-level | 1.0 | -100 to 100 m | Elevation from which terrain is considered emerged land/beach. |
| --land-pass-distance | 18 CLI / GUI profile | 0 to 160 px | Width of the second inland sand-to-land pass. |
| --land-pass-strength | 0.72 CLI / GUI profile | 0 to 1 | Strength of the inland transition. |
| --beach-layer-names | required, GUI: hp_beach | comma-separated list | Layers already considered beach/coastline. |
| --sand-layer-names | required, GUI: hp_sand | comma-separated list | Source layers authorizing sand expansion. |
| --land-layer-names | empty | optional | Optional inland layers used to limit the interior transition. Empty = general behavior. |
| --sand-color-preset | belle_ile | preset or custom | Sand color palette. |
| --sand-color-strength | 1.0 | 0.0 to 1.5 | Intensity of the selected sand palette. |
| --sand-dry-rgb | None | R,G,B or #RRGGBB | Custom dry sand override when using custom mode. |
| --sand-wet-rgb | None | R,G,B or #RRGGBB | Custom wet sand override. |
| --sand-shell-rgb | None | R,G,B or #RRGGBB | Custom light/shell variation override. |
| --wet-beach-rgb | None | R,G,B or #RRGGBB | Custom wet edge between water and beach. |
| --seabed-rgb | None | R,G,B or #RRGGBB | Custom sandy seabed visible near shore. |
| --sand-texture-image | empty | image | Optional texture adding grain to sand without changing generated areas. |
| --sand-texture-strength | 0.45 | 0.0 to 1.0 | Sand texture strength. |
| --sand-texture-scale | 1.0 | 0.1 to 8.0 | Sand texture repetition scale. |
| --water-color-preset | atlantic_belle_ile | preset or custom | Water gradient palette. |
| --water-color-strength | 1.0 | 0.0 to 1.5 | Intensity of the selected water palette. |
| --water-deep-rgb | None | R,G,B or #RRGGBB | Custom deep water color. |
| --water-mid-rgb | None | R,G,B or #RRGGBB | Custom mid water color. |
| --water-shallow-rgb | None | R,G,B or #RRGGBB | Custom shallow water color. |
| --water-lagoon-rgb | None | R,G,B or #RRGGBB | Custom lagoon / very clear water color. |
| --water-surf-rgb | None | R,G,B or #RRGGBB | Custom surf / foam color. |
| --water-seabed-rgb | None | R,G,B or #RRGGBB | Custom underwater seabed color. |
| --water-texture-image | empty | image | Optional texture for waves, noise, foam or reflections. |
| --water-texture-strength | 0.25 | 0.0 to 1.0 | Water texture strength. |
| --water-texture-scale | 1.0 | 0.1 to 8.0 | Water texture scale. |
| --water-texture-smoothing | 12.0 | 0.0 to 64.0 px | Smoothing applied to the water texture before tiling. |
| --water-texture-warp | 18.0 | 0.0 to 96.0 px | Coordinate warp used to reduce visible repetition. |
| --surf-width | 8.0 | 1 to 128 px | Thickness of the bright surf band. |
| --shallow-width-factor | 0.42 | 0.05 to 5.0 | Shallow-water width multiplier based on sand-distance. |
| --mid-width-factor | 0.95 | 0.05 to 5.0 | Mid-water width multiplier. |
| --deep-width-factor | 1.70 | 0.05 to 5.0 | Distance before deep/dark water. |
| --foam-strength | 1.0 | 0 to 2 | Visual strength of foam and contour bands. |
| --wet-sand-width | 10.0 | 1 to 128 px | Width of wet sand near water. |
| --mask-color-tolerance | 0 | 0 to 255 | RGB tolerance for matching mask to layers.cfg. 0 = exact, JPG rejected. |
| --debug-masks | false | flag | Creates diagnostic images in debug_masks. |
| --validate-only | false | flag | Checks files and settings without generating. |
| --no-report | false | flag | Disables generation_settings.json and RAPPORT_GENERATION_COMPLET.md. |
| --list-sand-presets | false | flag | Prints beach presets and exits. |
| --list-sand-color-presets | false | flag | Prints sand color presets and exits. |
| --list-water-color-presets | false | flag | Prints water color presets and exits. |

---

## 12. Sand color presets

| Preset | Label | Dry | Wet | Shell | Wet beach | Seabed |
| --- | --- | --- | --- | --- | --- | --- |
| belle_ile | Belle-Île / natural light sand | 222,204,178 | 190,168,145 | 208,196,182 | 181,156,128 | 160,120,90 |
| atlantic_light | Light Atlantic | 230,214,184 | 196,176,150 | 220,210,196 | 188,164,134 | 170,132,98 |
| golden | Golden sand | 226,190,126 | 176,140,95 | 218,200,164 | 166,132,92 | 152,112,72 |
| pale_white | White / very light sand | 238,230,204 | 205,194,170 | 236,230,218 | 196,184,160 | 176,160,130 |
| grey_shell | Grey / shell sand | 200,196,184 | 158,154,145 | 220,218,210 | 150,145,132 | 128,120,108 |
| dark_volcanic | Dark / volcanic sand | 112,105,96 | 70,68,66 | 150,145,135 | 82,76,70 | 74,68,62 |
| red_ochre | Ochre / red sand | 196,128,82 | 132,82,58 | 205,176,150 | 144,92,62 | 122,76,52 |
| custom | Manual RGB | --sand-dry-rgb | --sand-wet-rgb | --sand-shell-rgb | --wet-beach-rgb | --seabed-rgb |

Custom RGB format:

```text
R,G,B
#RRGGBB
```

---

## 13. Water color presets

| Preset | Label | Deep | Mid | Shallow | Lagoon | Surf | Seabed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| atlantic_belle_ile | Atlantic / Belle-Île | 58,88,122 | 70,112,142 | 93,149,156 | 118,181,174 | 156,202,190 | 160,120,90 |
| atlantic_open_ocean | Open Atlantic / deep blue | 28,72,112 | 45,100,135 | 76,135,150 | 105,165,160 | 165,205,195 | 135,115,90 |
| atlantic_grey_coast | Grey Atlantic coast / Channel | 48,70,88 | 72,96,108 | 105,130,125 | 132,154,145 | 178,190,178 | 125,115,100 |
| tropical_lagoon | Tropical lagoon | 20,95,145 | 35,165,185 | 95,220,210 | 130,235,220 | 220,245,230 | 210,190,130 |
| caribbean_turquoise | Caribbean / light turquoise | 0,87,143 | 18,156,188 | 72,218,220 | 125,238,225 | 230,248,238 | 218,202,145 |
| maldives_atoll | Maldives / white-sand atoll | 5,76,132 | 25,150,190 | 85,225,220 | 155,242,225 | 235,250,238 | 225,207,150 |
| coral_reef_shallow | Coral reef / shoal | 16,80,138 | 30,145,170 | 95,205,190 | 150,225,205 | 225,245,225 | 190,165,120 |
| mediterranean_blue | Mediterranean / mineral blue | 25,75,138 | 42,110,165 | 70,155,185 | 105,190,195 | 180,220,215 | 150,130,95 |
| aegean_clear | Aegean Sea / light blue | 18,80,150 | 35,125,180 | 75,175,205 | 110,205,210 | 195,230,225 | 165,145,105 |
| adriatic_clear | Adriatic / light blue-green | 35,85,120 | 55,125,150 | 90,170,175 | 130,200,190 | 200,225,210 | 155,140,110 |
| red_sea_clear | Red Sea / very clear water | 15,72,132 | 28,130,170 | 78,190,195 | 120,220,205 | 220,240,220 | 190,165,115 |
| pacific_deep | Deep Pacific | 12,48,95 | 30,80,130 | 62,125,155 | 90,160,165 | 160,210,200 | 105,95,85 |
| indian_ocean | Indian Ocean | 10,70,125 | 28,125,160 | 70,185,190 | 115,215,200 | 220,240,225 | 190,175,125 |
| cold_ocean | Cold ocean | 35,65,85 | 55,95,115 | 90,135,140 | 105,155,155 | 180,205,205 | 120,115,105 |
| north_sea_grey | North Sea / green grey | 45,65,78 | 65,88,95 | 92,118,112 | 120,140,130 | 170,185,175 | 115,105,88 |
| baltic_green | Baltic / cold green | 36,70,72 | 58,100,88 | 90,130,100 | 125,155,115 | 178,195,165 | 115,105,75 |
| arctic_glacial | Arctic / glacial water | 25,70,95 | 55,115,135 | 100,165,170 | 145,205,200 | 220,238,230 | 130,130,120 |
| fjord_dark | Fjord / dark water | 15,42,58 | 28,65,78 | 55,95,100 | 85,125,120 | 150,175,165 | 78,74,68 |
| deep_ocean | Deep ocean | 18,50,82 | 35,82,116 | 70,130,150 | 95,165,165 | 150,205,195 | 115,105,88 |
| black_sea_deep | Black Sea / dark blue | 18,43,70 | 32,70,90 | 62,105,112 | 88,130,125 | 150,175,165 | 90,85,72 |
| muddy_water | Muddy / turbid water | 70,85,75 | 100,110,85 | 135,130,95 | 155,145,105 | 190,185,150 | 125,105,70 |
| river_delta_silty | Delta / silty water | 78,88,70 | 112,112,78 | 148,136,90 | 170,150,102 | 200,190,145 | 135,110,70 |
| mangrove_lagoon | Mangrove / green lagoon | 38,72,58 | 70,105,72 | 105,132,82 | 135,155,95 | 180,190,145 | 105,85,55 |
| amazon_brown | Tropical river / organic brown | 80,62,42 | 120,88,55 | 155,112,70 | 180,135,90 | 210,185,145 | 110,82,52 |
| great_lakes_fresh | Great Lakes / freshwater | 32,75,98 | 55,110,125 | 90,150,145 | 125,175,160 | 185,210,195 | 120,115,95 |
| alpine_lake | Alpine lake / light blue-green | 22,76,110 | 48,125,145 | 95,175,170 | 135,205,190 | 210,235,220 | 120,125,110 |
| glacial_lake_milky | Glacial lake / milky turquoise | 55,98,120 | 85,135,150 | 130,180,180 | 170,210,200 | 225,240,230 | 150,150,135 |
| green_algae_lake | Vegetal lake / green algae | 35,70,45 | 65,105,55 | 105,140,65 | 140,165,80 | 185,195,135 | 90,85,55 |
| volcanic_crater_lake | Volcanic crater lake / dark blue-green | 12,55,72 | 25,92,95 | 65,135,115 | 95,170,135 | 165,210,180 | 60,58,55 |
| salt_lake_pale | Salt lake / very pale water | 88,130,140 | 125,170,165 | 170,210,190 | 205,230,205 | 240,245,225 | 220,205,165 |
| dark_stormy | Dark stormy sea | 25,45,60 | 40,70,85 | 65,95,100 | 80,115,112 | 145,165,160 | 85,80,70 |
| custom | Manual RGB | --water-deep-rgb | --water-mid-rgb | --water-shallow-rgb | --water-lagoon-rgb | --water-surf-rgb | --water-seabed-rgb |

`atlantic_belle_ile` is the default baseline. Tropical presets produce much brighter water. Muddy/delta/mangrove/river presets are intended for turbid or inland waters.

---

## 14. Sand and water textures

### Sand texture

```text
--sand-texture-image
--sand-texture-strength
--sand-texture-scale
```

Adds visual grain to sand only. It does not change generated sand areas.

Recommended:

```text
strength : 0.30 to 0.60
scale    : 1.0 to 3.0
```

### Water texture

```text
--water-texture-image
--water-texture-strength
--water-texture-scale
--water-texture-smoothing
--water-texture-warp
```

Adds waves, noise, reflections or foam without changing water areas. Mirror tiling and coordinate warp reduce visible repetition.

Recommended:

```text
strength  : 0.15 to 0.35
scale     : 1.0 to 4.0
smoothing : 8 to 16
warp      : 12 to 24
```

---

## 15. Seaside finishing

| Setting | Purpose | Recommended |
|---|---|---|
| `surf-width` | Foam/surf band thickness | 6 to 10 px |
| `foam-strength` | Bright surf and contour intensity | 0.6 to 1.1 |
| `wet-sand-width` | Wet sand width | 8 to 14 px |
| `shallow-width-factor` | Bright shallow-water width near shore | 0.30 to 0.50 |
| `mid-width-factor` | Shallow-to-mid water transition | 0.70 to 1.10 |
| `deep-width-factor` | Distance before deep/dark water | 1.25 to 1.70 |

These controls affect visual appearance only, not generated terrain zones.

---

## 16. Outputs

| Output | Description |
|---|---|
| `satmap_final_10240.png` | Final corrected satmap. |
| `beach_mask_10240.png` | Final water/beach mask: `0` land, `128` water, `255` generated beach/sand. |
| `generation_settings.json` | Full saved argument set and extra generation data. |
| `RAPPORT_GENERATION_COMPLET.md` | Human-readable report. |
| `debug_masks/` | Diagnostic masks created only with `--debug-masks`. |

---

## 17. Validation

```bash
py satmap_generator_optimized_presets.py --validate-only ^
  --heightmap input/heightmap.asc ^
  --mask input/mask.png ^
  --satmap input/satmap.png ^
  --layers input/layers.cfg ^
  --beach-layer-names hp_beach ^
  --sand-layer-names hp_sand
```

Validation checks file existence, formats, layer names, ASC dimensions, RAM estimate and key value ranges.

---

## 18. Recommended settings

Stable 10K profile:

```text
target-size       : 10240
chunk-rows        : 2048 or 4096
block-size        : 32
sand-preset       : 4 - Wide beach
water-profile     : 1 - Standard
inland-profile    : 4 - Strong blend
sand-color        : belle_ile
water-color       : atlantic_belle_ile
mask tolerance    : 0 for PNG/BMP/TIFF
debug masks       : enabled for tests, disabled for clean runs
```

---

## 19. Troubleshooting

| Issue | Likely cause | Fix |
|---|---|---|
| No beach layer name | Empty `--beach-layer-names`. | Provide `hp_beach` or a valid layers.cfg texture. |
| No sand source layer name | Empty `--sand-layer-names`. | Provide `hp_sand` or a valid sand source layer. |
| No source sand found | Name mismatch or mask does not use the layer color. | Check texture names against layers.cfg. |
| JPG rejected | Mask compression with tolerance 0. | Use PNG or set tolerance > 0. |
| Beach too wide | Distance/height/slope too permissive. | Lower sand distance, max height or slope. |
| No beach generated | Source layer missing or constraints too strict. | Check source layer and relax distance/height/slope. |
| Repeating water texture | Texture too small or weak smoothing/warp. | Increase texture scale, smoothing and warp. |
| High RAM usage | Large target size or chunk rows. | Lower chunk rows and close other software. |

---

## 20. Recommended workflow

1. Prepare input files.
2. Launch the GUI.
3. Verify paths and layer names.
4. Run validation.
5. Generate once with debug masks enabled.
6. Inspect debug masks.
7. Adjust beach/water/blend settings.
8. Generate final output without debug.
9. Keep the validated `output_Vx` folder.
