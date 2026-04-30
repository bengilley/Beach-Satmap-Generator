# Beach Satmap Generator

Beach Satmap Generator is a Python/Tkinter tool for generating and correcting DayZ satmaps around beaches, shorelines, sand transitions, water/land thresholds, and inland texture blending.

The launcher is designed for public distribution:
- file paths are empty by default;
- user paths are hidden in logs and command previews;
- required files are validated before generation;
- duplicate file selections are blocked;
- `layers.cfg` texture names can be checked before running;
- the interface supports French, English, and Russian.

## Requirements

- Windows recommended
- Python 3.11 or newer
- Dependencies listed in `requirements.txt`

Install dependencies manually:

```bash
py -m pip install -r requirements.txt
```

Or use the launcher button:

```text
Installer dépendances / Install dependencies
```

## Files required from the user

Place or select these files:

```text
heightmap.asc
mask.png
satmap.png
layers.cfg
```

The launcher starts with empty paths on purpose. Select each file manually in the `1. Fichiers / 1. Files` tab.

## Launch

Double-click:

```text
satmap_gui_launcher.pyw
```

Or run from a terminal:

```bash
py satmap_gui_launcher.pyw
```

## Basic workflow

1. Open `satmap_gui_launcher.pyw`.
2. Select the language in the top-right menu.
3. Select:
   - generator script;
   - heightmap ASC;
   - mask PNG;
   - satmap PNG;
   - layers CFG.
4. Select or type texture names:
   - existing beach / coastline;
   - source sand to extend;
   - optional inland target texture.
5. Click `Vérifier les fichiers / Check files`.
6. Click `Vérifier textures layers.cfg / Check layers.cfg textures`.
7. Configure profiles and technical settings.
8. Launch the generation from the `4. Lancement / 4. Run` tab.

## Output

Generated files are written to:

```text
outputs/output_V1/
outputs/output_V2/
outputs/output_V3/
...
```

Each output folder can contain:
- final satmap PNG;
- beach mask PNG;
- a complete generation report in the selected language.

## Privacy / public release notes

This public pack does not include:
- personal Windows paths;
- generated outputs;
- private project files;
- user-specific launcher settings;
- custom saved profiles.

The `.gitignore` file is configured to avoid committing large/private source and output files.

## License

This project is licensed under the MIT License.

Created by Bengilley & SleepingWolf.
