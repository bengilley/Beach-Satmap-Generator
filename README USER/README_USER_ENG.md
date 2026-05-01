# Beach Satmap Generator — User README

Simplified documentation for using the satmap generator with the graphical launcher.

This README is intended for end users. It keeps only what is needed to install, launch, configure, and retrieve the generated files.

---

## 1. What does this tool do?

Beach Satmap Generator creates a cleaner DayZ satmap, especially around beaches, water, and coastlines.

From four source files, it generates:

- a corrected final satmap;
- a beach mask;
- a versioned output folder so previous results are not overwritten.

It is designed for large maps, for example `10240 x 10240 px`.

---

## 2. Required files

Place the following files in the same folder:

```text
satmap_gui_launcher.pyw
satmap_generator_optimized_presets.py
input/
  heightmap.asc
  mask.png
  satmap.png
  layers.cfg
```

### File roles

| File | Purpose |
|---|---|
| `heightmap.asc` | Used to detect altitude, water, slopes, and coastal areas. |
| `mask.png` | Used to recognize textures through the colors defined in `layers.cfg`. |
| `satmap.png` | Source satellite image that will be corrected. |
| `layers.cfg` | Connects mask colors to DayZ texture/layer names. |

Accepted image formats: `PNG`, `JPG`, `JPEG`, `BMP`, `TIFF`.

For the `mask`, the recommended formats are `PNG`, `BMP`, or `TIFF`. Avoid `JPG`, because it may alter mask colors.

---

## 3. Installation

### Simple method from the launcher

1. Run `satmap_gui_launcher.pyw`.
2. Open the **Files** tab.
3. Click **Install dependencies** if the dependencies are not installed yet.

### Manual method

Open a terminal in the script folder and run:

```bash
py -m pip install numpy pillow scipy
```

---

## 4. Start the program

You can start the interface in two ways:

```bash
py satmap_gui_launcher.pyw
```

or by double-clicking:

```text
satmap_gui_launcher.pyw
```

The interface contains four tabs:

1. **Files**
2. **Profiles**
3. **Technical**
4. **Run**

---

## 5. Files tab

This tab is used to select the files used by the generator.

Check especially:

- the generator script path;
- the heightmap path;
- the mask path;
- the satmap path;
- the `layers.cfg` path.

### DayZ textures to recognize

You must enter the textures the script should use to recognize beach, sand, and optionally inland terrain.

| Field | Usage |
|---|---|
| Already beach texture | Texture already considered as beach or coastline. |
| Sand texture to expand | Source texture that the script should extend around the shore. |
| Land texture to blend | Optional. Limits the sand → land blend to a specific texture. |

Example:

```text
Already beach texture: hp_beach
Sand texture to expand: hp_sand
Land texture to blend: cp_grass
```

If you use a custom texture, type its name exactly as it appears in `layers.cfg`.

---

## 6. Profiles tab

This is the main tab for rendering settings.

### Recommended starting settings

| Setting | Recommended value |
|---|---|
| Beach: size and slope | `4 - Wide beach` or `3 - Balanced` |
| Water: altitude levels | `1 - Normal water` |
| Sand → land blend | `4 - Strong blend` or `3 - Natural blend` |
| Sand type | `belle_ile` or `atlantic_light` |
| Water type | `atlantic_belle_ile` |
| Sand texture | Optional |
| Water texture | Optional |

### Beach: size and slope

These settings control where sand can be generated.

| Parameter | Effect |
|---|---|
| Max beach width | Higher value lets the beach extend farther from the shore. |
| Allowed slope | Lower value makes the script avoid cliffs and embankments more strictly. |
| Max beach height | Maximum altitude where sand can be created. |

Tip: start with `4 - Wide beach`, then adjust if the sand goes too far or not far enough.

### Water: altitude levels

These settings define which areas are considered water or land according to the heightmap.

In most cases, keep:

```text
1 - Normal water
```

Use a lower or higher profile only if your water level does not match your heightmap correctly.

### Sand → land blend

This setting improves the transition between beach and inland terrain.

| Profile | Result |
|---|---|
| Disabled | No inland transition. |
| Light blend | Short and subtle transition. |
| Natural blend | Good compromise. |
| Strong blend | More visible and cleaner transition. |
| Dune effect | Stronger short dune effect. |

---

## 7. Colors and textures

### Sand colors

Useful examples:

| Preset | Usage |
|---|---|
| `belle_ile` | Natural light sand, good default choice. |
| `atlantic_light` | Light Atlantic coast. |
| `golden` | More golden sand. |
| `pale_white` | Very light sand. |
| `grey_shell` | Grey/shell sand. |
| `dark_volcanic` | Dark sand. |
| `red_ochre` | Red/ochre sand. |

### Water colors

Useful examples:

| Preset | Usage |
|---|---|
| `atlantic_belle_ile` | Good default for an Atlantic coast. |
| `atlantic_open_ocean` | Deeper blue ocean. |
| `tropical_lagoon` | Clear turquoise water. |
| `mediterranean_blue` | Mediterranean blue. |
| `fjord_dark` | Dark water. |
| `muddy_water` | Murky or silty water. |

### Optional textures

Sand and water textures add visual detail. They do not change the generated area.

| Texture | Recommended strength | Recommended scale |
|---|---:|---:|
| Sand | `0.30` to `0.60` | `1.0` |
| Water | `0.15` to `0.35` | `1.0` |

---

## 8. Technical tab

### Final resolution

For a DayZ 10K map, use:

```text
10240
```

### Memory / speed

This setting controls the number of rows processed per chunk.

| Value | Usage |
|---:|---|
| `512` / `1024` | Very safe, but slower. |
| `2048` | Good compromise. |
| `4096` | Recommended if you have 32 or 64 GB RAM. |
| `8192` | Faster, but uses more RAM. |

Start with `2048`.

### Mask color tolerance

Usually keep:

```text
0
```

Use a higher value only if your mask was compressed or modified and the colors no longer match `layers.cfg` exactly.

### Diagnostic images

Enable **Create diagnostic images** only if you need to understand a generation problem.

---

## 9. Generate the satmap

In the **Run** tab:

1. Click **Check files**.
2. Fix any errors if needed.
3. Click **Start generation**.
4. Wait until the process finishes.
5. Get the files from the `outputs` folder.

---

## 10. Generated files

Outputs are created in a folder like:

```text
outputs/output_V1/
outputs/output_V2/
outputs/output_V3/
```

Each generation creates a new version to avoid overwriting previous results.

Main files:

| File | Purpose |
|---|---|
| `satmap_final_10240.png` | Final satmap to use in your project. |
| `beach_mask_10240.png` | Generated beach/water mask. |

Additional files:

| File | Purpose |
|---|---|
| `generation_settings.json` | Saved settings used for the generation. |
| `COMPLETE_GENERATION_REPORT.md` | Readable generation report. |
| `debug_masks/` | Diagnostic images, only if enabled. |

---

## 11. Common problems

### The script cannot find my textures

Make sure the names you entered match exactly the names in `layers.cfg`.

Example:

```text
hp_sand
```

is not the same as:

```text
hp sand
```

### The mask does not match layers.cfg

Prefer a mask in `PNG`, `BMP`, or `TIFF`.

If your mask is a `JPG`, colors may be altered. In that case, use a lossless format or slightly increase the color tolerance.

### Sand goes too far inland

Decrease:

- Max beach width;
- Max beach height;
- Allowed slope;
- Land blend strength.

### There is not enough sand

Increase gradually:

- Max beach width;
- Max beach height;
- Allowed slope.

### Generation is slow

This is normal with a 10K satmap.

To improve speed:

- close heavy software;
- use `chunk rows = 4096` if your PC is stable;
- keep a resolution suitable for your project.

### The program runs out of RAM

Reduce:

```text
Memory / speed
```

Try `1024` or `2048`.

---

## 12. Command line usage

The graphical launcher is still the recommended way to use the tool.

Simple command:

```bash
py satmap_generator_optimized_presets.py
```

Example with a 10K map:

```bash
py satmap_generator_optimized_presets.py --target-size 10240 --chunk-rows 2048 --sand-preset 4
```

---

## 13. Recommended first test

```text
Beach: 4 - Wide beach
Water: 1 - Normal water
Sand → land blend: 4 - Strong blend
Sand type: belle_ile
Water type: atlantic_belle_ile
Final resolution: 10240
Memory / speed: 2048
Mask color tolerance: 0
Debug masks: disabled
```

---

## 14. Important advice

Always run a first generation with the recommended settings before customizing colors, textures, or advanced values.

This lets you confirm that the source files, mask, and `layers.cfg` are correctly recognized.
