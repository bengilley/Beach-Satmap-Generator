# Quick guide EN

## Installation

Install Python, then dependencies:

```bash
py -m pip install -r requirements.txt
```

## Required files

The launcher needs:

```text
heightmap.asc
mask.png
satmap.png
layers.cfg
```

File paths are empty by default. Select files manually from the `1. Files` tab.

## Textures

You can select a vanilla DayZ texture from the dropdown and/or type custom texture names manually.

Example:

```text
Existing beach / coastline : hp_beach
Source sand to extend      : hp_sand
Target inland texture      : empty or optional texture
```

Use:

```text
Check layers.cfg textures
```

to verify that texture names exist in `layers.cfg`.

## Generation

Generation starts only from:

```text
4. Run
```

Results are created in:

```text
outputs/output_V...
```
