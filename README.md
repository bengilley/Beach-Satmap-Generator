# Beach Satmap Generator

**Beach Satmap Generator** is a Python / Tkinter tool designed to help generate and correct DayZ satellite maps around beaches, shorelines, sand transitions, water thresholds, and inland blending.

Created by **Bengilley & SleepingWolf**.

---

## Documentation

This repository contains two documentation folders:

### User documentation

For installation, basic usage, required files, recommended settings, generation steps, outputs, and common errors:

[Open README USER](README%20USER/)

This is the documentation recommended for normal users.

### Developer documentation

For advanced information, technical behavior, internal logic, CLI options, presets, diagnostics, and development notes:

[Open README DEV](README%20DEV/)

This documentation is intended for advanced users, modders, maintainers, and contributors.

---

## Quick start

1. Install Python 3.11 or newer.
2. Install dependencies:

```bash
py -m pip install -r requirements.txt
```

3. Place or select your required files:

```text
heightmap.asc
mask.png
satmap.png
layers.cfg
```

4. Launch the graphical interface:

```bash
py satmap_gui_launcher.pyw
```

Or double-click:

```text
satmap_gui_launcher.pyw
```

5. Follow the user documentation for the full workflow.

---

## Required files

The generator needs the following user-provided files:

```text
heightmap.asc
mask.png
satmap.png
layers.cfg
```

These files should be placed in the `input/` folder or selected manually from the launcher.

---

## Output folder

Generated files are written to:

```text
outputs/output_V1/
outputs/output_V2/
outputs/output_V3/
...
```

Typical generated files include:

```text
satmap_final_10240.png
beach_mask_10240.png
generation report
```

---

## Dependencies

Dependencies are listed in:

```text
requirements.txt
```

Main Python packages:

```text
numpy
pillow
scipy
```

---

## Repository structure

```text
Beach-Satmap-Generator/
├─ .github/
├─ input/
├─ outputs/
├─ README DEV/
├─ README USER/
├─ .gitignore
├─ LICENSE
├─ NOTICE.txt
├─ README.md
├─ requirements.txt
├─ satmap_generator_optimized_presets.py
└─ satmap_gui_launcher.pyw
```

---

## Notes for public release

This repository should not include personal or generated files such as:

```text
input/heightmap.asc
input/mask.png
input/satmap.png
input/layers.cfg
outputs/output_V*/
custom_profiles.json
launcher_settings.json
```

Keep `input/` and `outputs/` only as empty folders or with placeholder files such as `.gitkeep`.

---

## License

This project is licensed under the MIT License.

See:

[LICENSE](LICENSE)

---

## Credits

Created by **Bengilley & SleepingWolf**.

See also:

[NOTICE.txt](NOTICE.txt)
