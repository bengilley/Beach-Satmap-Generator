#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
satmap_generator_optimized.py

Version optimisée/vectorisée du générateur de satmap.

Entrées par défaut :
  - heightmap.asc
  - mask.png
  - satmap.png
  - layers.cfg

Sorties par défaut :
  - satmap_final_10240.png
  - beach_mask_10240.png

Dépendances :
  pip install numpy pillow scipy

Exemple :
  python satmap_generator_optimized.py

Exemple avec chemins personnalisés :
  python satmap_generator_optimized.py \
    --heightmap heightmap.asc \
    --mask mask.png \
    --satmap satmap.png \
    --layers layers.cfg \
    --target-size 10240 \
    --chunk-rows 512
"""

import argparse
import gc
import json
import re
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

# Autorise les grandes satmaps DayZ/terrain sans warning Pillow de sécurité.
Image.MAX_IMAGE_PIXELS = 300_000_000

try:
    from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter
except ImportError as exc:
    raise SystemExit(
        "Erreur : scipy est requis pour cette version optimisée.\n"
        "Installe-le avec : pip install scipy\n"
    ) from exc


# =========================================================
# CONFIG PAR DÉFAUT
# =========================================================
GENERATOR_VERSION = "1.3.5"

DEFAULT_HEIGHTMAP_PATH = "input/heightmap.asc"
DEFAULT_MASK_PATH = "input/mask.png"
DEFAULT_SATMAP_PATH = "input/satmap.png"
DEFAULT_LAYERS_CFG_PATH = "input/layers.cfg"

SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")
LOSSLESS_MASK_EXTENSIONS = (".png", ".bmp", ".tif", ".tiff")
LOSSY_MASK_EXTENSIONS = (".jpg", ".jpeg")
REPORT_FILE_NAME = "RAPPORT_GENERATION_COMPLET.md"
SETTINGS_JSON_NAME = "generation_settings.json"

DEFAULT_OUTPUT_SATMAP = "satmap_final_10240.png"
DEFAULT_OUTPUT_BEACH_MASK = "beach_mask_10240.png"

DEFAULT_TARGET_SIZE = 10240
DEFAULT_CHUNK_ROWS = 512

# ---------------------------------------------------------
# LOGIQUE TERRAIN
# ---------------------------------------------------------
CLEAN_CUTOFF_METERS = 0.0
SEA_LEVEL_METERS = 1.0

HP_SAND_MAX_METERS = 4.8
HP_SAND_DISTANCE = 42
SAND_SLOPE_MAX = 0.16

# ---------------------------------------------------------
# PRESETS SAND
# ---------------------------------------------------------
# Tableau lisible/modifiable facilement dans Visual Studio / VS Code.
# Tu peux ajouter tes propres lignes en respectant les mêmes clés.
SAND_PRESETS = [
    {
        "id": "1",
        "name": "tres_propre",
        "distance": 45.0,
        "slope_max": 0.16,
        "max_height": 4.8,
        "description": "Plage fine, tres controlee",
    },
    {
        "id": "2",
        "name": "propre_marge",
        "distance": 55.0,
        "slope_max": 0.18,
        "max_height": 5.2,
        "description": "Un peu plus de sable sans trop deborder",
    },
    {
        "id": "3",
        "name": "equilibre",
        "distance": 60.0,
        "slope_max": 0.20,
        "max_height": 5.5,
        "description": "Bon reglage de base",
    },
    {
        "id": "4",
        "name": "large",
        "distance": 70.0,
        "slope_max": 0.22,
        "max_height": 6.0,
        "description": "Plages plus visibles, bonne marge",
    },
    {
        "id": "5",
        "name": "tres_large",
        "distance": 85.0,
        "slope_max": 0.25,
        "max_height": 7.0,
        "description": "Sable plus loin dans les terres",
    },
    {
        "id": "6",
        "name": "agressif",
        "distance": 100.0,
        "slope_max": 0.28,
        "max_height": 8.0,
        "description": "Peut commencer a manger les talus",
    },
    {
        "id": "7",
        "name": "tres_agressif",
        "distance": 120.0,
        "slope_max": 0.32,
        "max_height": 10.0,
        "description": "Fort risque de sable trop haut / trop loin",
    },
    {
        "id": "8",
        "name": "custom",
        "distance": 70.0,
        "slope_max": 0.22,
        "max_height": 6.0,
        "description": "Valeurs personnalisées via le menu",
    },
]

# ---------------------------------------------------------
# TEXTURES / LAYERS.CFG PERSONNALISABLES
# ---------------------------------------------------------
# Noms de layers reconnus par défaut dans layers.cfg.
# Plusieurs noms peuvent être passés en ligne de commande avec une liste séparée par des virgules.
DEFAULT_BEACH_LAYER_NAMES = ""
DEFAULT_SAND_SOURCE_LAYER_NAMES = ""
DEFAULT_LAND_SIDE_LAYER_NAMES = ""

SEABED_WATER_BLEND = 0.86
MASK_BLUR_RADIUS = 1
GLOBAL_CONTRAST = 1.03

# sable naturel
WET_SAND_DISTANCE = 10
DRY_SAND_BRIGHTNESS = 6.0
WET_SAND_DARKEN = 20.0
SEABED_NOISE_STRENGTH = 0.18
SAND_NOISE_STRENGTH = 0.32
FULL_SAND_THRESHOLD = 0.55

# irrégularité du bord côté terre
EDGE_BREAKUP_STRENGTH = 0.22
EDGE_BREAKUP_SCALE = 0.9
EDGE_INNER_PRESERVE = 0.62

# deuxième passe côté terre : dégradé sable sec -> dune -> terre/herbe
LAND_PASS_DISTANCE_DEFAULT = 18.0
LAND_PASS_STRENGTH_DEFAULT = 0.72
LAND_PASS_SOURCE_THRESHOLD = 0.08
LAND_PASS_EDGE_LIMIT = 0.42
LAND_PASS_DISTANCE_MAX = 160.0
LAND_PASS_STRENGTH_MAX = 1.0

SEED = 42


# =========================================================
# PALETTES
# =========================================================
HP_BEACH_RGB = np.array([160, 120, 90], dtype=np.float32)

# Sable plus naturel : base moins rose, plus minérale
SAND_WET_RGB = np.array([190, 168, 145], dtype=np.float32)
SAND_DRY_RGB = np.array([222, 204, 178], dtype=np.float32)
SAND_SHELL_RGB = np.array([208, 196, 182], dtype=np.float32)

# Presets couleur sable : permettent d'adapter le rendu satmap à différents types de sable.
# Les valeurs sont RGB, volontairement éditables.
SAND_COLOR_PRESETS = {
    "belle_ile": {
        "label": "Belle-Île / sable clair naturel",
        "dry": [222, 204, 178],
        "wet": [190, 168, 145],
        "shell": [208, 196, 182],
        "wet_beach": [181, 156, 128],
        "seabed": [160, 120, 90],
    },
    "atlantic_light": {
        "label": "Atlantique clair",
        "dry": [230, 214, 184],
        "wet": [196, 176, 150],
        "shell": [220, 210, 196],
        "wet_beach": [188, 164, 134],
        "seabed": [170, 132, 98],
    },
    "golden": {
        "label": "Sable doré",
        "dry": [226, 190, 126],
        "wet": [176, 140, 95],
        "shell": [218, 200, 164],
        "wet_beach": [166, 132, 92],
        "seabed": [152, 112, 72],
    },
    "pale_white": {
        "label": "Sable blanc / très clair",
        "dry": [238, 230, 204],
        "wet": [205, 194, 170],
        "shell": [236, 230, 218],
        "wet_beach": [196, 184, 160],
        "seabed": [176, 160, 130],
    },
    "grey_shell": {
        "label": "Sable gris / coquillier",
        "dry": [200, 196, 184],
        "wet": [158, 154, 145],
        "shell": [220, 218, 210],
        "wet_beach": [150, 145, 132],
        "seabed": [128, 120, 108],
    },
    "dark_volcanic": {
        "label": "Sable sombre / volcanique",
        "dry": [112, 105, 96],
        "wet": [70, 68, 66],
        "shell": [150, 145, 135],
        "wet_beach": [82, 76, 70],
        "seabed": [74, 68, 62],
    },
    "red_ochre": {
        "label": "Sable ocre / rouge",
        "dry": [196, 128, 82],
        "wet": [132, 82, 58],
        "shell": [205, 176, 150],
        "wet_beach": [144, 92, 62],
        "seabed": [122, 76, 52],
    },
}

# Eau / contouring : plusieurs teintes pour un dégradé mer -> plage plus naturel.
WATER_DEEP_RGB = np.array([58, 88, 122], dtype=np.float32)
WATER_MID_RGB = np.array([70, 112, 142], dtype=np.float32)
WATER_SHALLOW_RGB = np.array([93, 149, 156], dtype=np.float32)
WATER_LAGOON_RGB = np.array([118, 181, 174], dtype=np.float32)
WATER_SURF_RGB = np.array([156, 202, 190], dtype=np.float32)
WET_BEACH_RGB = np.array([181, 156, 128], dtype=np.float32)

# Presets couleur eau : permettent d'adapter le dégradé mer -> plage à différents biomes.
# Les valeurs sont RGB, volontairement éditables.
WATER_COLOR_PRESETS = {
    "atlantic_belle_ile": {
        "label": "Atlantique / Belle-Île",
        "deep": [58, 88, 122],
        "mid": [70, 112, 142],
        "shallow": [93, 149, 156],
        "lagoon": [118, 181, 174],
        "surf": [156, 202, 190],
        "seabed": [160, 120, 90],
    },
    "atlantic_open_ocean": {
        "label": "Atlantique ouvert / bleu profond",
        "deep": [28, 72, 112],
        "mid": [45, 100, 135],
        "shallow": [76, 135, 150],
        "lagoon": [105, 165, 160],
        "surf": [165, 205, 195],
        "seabed": [135, 115, 90],
    },
    "atlantic_grey_coast": {
        "label": "Côte atlantique grise / Manche",
        "deep": [48, 70, 88],
        "mid": [72, 96, 108],
        "shallow": [105, 130, 125],
        "lagoon": [132, 154, 145],
        "surf": [178, 190, 178],
        "seabed": [125, 115, 100],
    },
    "tropical_lagoon": {
        "label": "Lagon tropical",
        "deep": [20, 95, 145],
        "mid": [35, 165, 185],
        "shallow": [95, 220, 210],
        "lagoon": [130, 235, 220],
        "surf": [220, 245, 230],
        "seabed": [210, 190, 130],
    },
    "caribbean_turquoise": {
        "label": "Caraïbes / turquoise clair",
        "deep": [0, 87, 143],
        "mid": [18, 156, 188],
        "shallow": [72, 218, 220],
        "lagoon": [125, 238, 225],
        "surf": [230, 248, 238],
        "seabed": [218, 202, 145],
    },
    "maldives_atoll": {
        "label": "Maldives / atoll sable blanc",
        "deep": [5, 76, 132],
        "mid": [25, 150, 190],
        "shallow": [85, 225, 220],
        "lagoon": [155, 242, 225],
        "surf": [235, 250, 238],
        "seabed": [225, 207, 150],
    },
    "coral_reef_shallow": {
        "label": "Récif corallien / haut-fond",
        "deep": [16, 80, 138],
        "mid": [30, 145, 170],
        "shallow": [95, 205, 190],
        "lagoon": [150, 225, 205],
        "surf": [225, 245, 225],
        "seabed": [190, 165, 120],
    },
    "mediterranean_blue": {
        "label": "Méditerranée / bleu minéral",
        "deep": [25, 75, 138],
        "mid": [42, 110, 165],
        "shallow": [70, 155, 185],
        "lagoon": [105, 190, 195],
        "surf": [180, 220, 215],
        "seabed": [150, 130, 95],
    },
    "aegean_clear": {
        "label": "Mer Égée / bleu clair",
        "deep": [18, 80, 150],
        "mid": [35, 125, 180],
        "shallow": [75, 175, 205],
        "lagoon": [110, 205, 210],
        "surf": [195, 230, 225],
        "seabed": [165, 145, 105],
    },
    "adriatic_clear": {
        "label": "Adriatique / bleu vert clair",
        "deep": [35, 85, 120],
        "mid": [55, 125, 150],
        "shallow": [90, 170, 175],
        "lagoon": [130, 200, 190],
        "surf": [200, 225, 210],
        "seabed": [155, 140, 110],
    },
    "red_sea_clear": {
        "label": "Mer Rouge / eau très claire",
        "deep": [15, 72, 132],
        "mid": [28, 130, 170],
        "shallow": [78, 190, 195],
        "lagoon": [120, 220, 205],
        "surf": [220, 240, 220],
        "seabed": [190, 165, 115],
    },
    "pacific_deep": {
        "label": "Pacifique profond",
        "deep": [12, 48, 95],
        "mid": [30, 80, 130],
        "shallow": [62, 125, 155],
        "lagoon": [90, 160, 165],
        "surf": [160, 210, 200],
        "seabed": [105, 95, 85],
    },
    "indian_ocean": {
        "label": "Océan Indien",
        "deep": [10, 70, 125],
        "mid": [28, 125, 160],
        "shallow": [70, 185, 190],
        "lagoon": [115, 215, 200],
        "surf": [220, 240, 225],
        "seabed": [190, 175, 125],
    },
    "cold_ocean": {
        "label": "Océan froid",
        "deep": [35, 65, 85],
        "mid": [55, 95, 115],
        "shallow": [90, 135, 140],
        "lagoon": [105, 155, 155],
        "surf": [180, 205, 205],
        "seabed": [120, 115, 105],
    },
    "north_sea_grey": {
        "label": "Mer du Nord / gris vert",
        "deep": [45, 65, 78],
        "mid": [65, 88, 95],
        "shallow": [92, 118, 112],
        "lagoon": [120, 140, 130],
        "surf": [170, 185, 175],
        "seabed": [115, 105, 88],
    },
    "baltic_green": {
        "label": "Baltique / vert froid",
        "deep": [36, 70, 72],
        "mid": [58, 100, 88],
        "shallow": [90, 130, 100],
        "lagoon": [125, 155, 115],
        "surf": [178, 195, 165],
        "seabed": [115, 105, 75],
    },
    "arctic_glacial": {
        "label": "Arctique / eau glaciale",
        "deep": [25, 70, 95],
        "mid": [55, 115, 135],
        "shallow": [100, 165, 170],
        "lagoon": [145, 205, 200],
        "surf": [220, 238, 230],
        "seabed": [130, 130, 120],
    },
    "fjord_dark": {
        "label": "Fjord / eau sombre",
        "deep": [15, 42, 58],
        "mid": [28, 65, 78],
        "shallow": [55, 95, 100],
        "lagoon": [85, 125, 120],
        "surf": [150, 175, 165],
        "seabed": [78, 74, 68],
    },
    "deep_ocean": {
        "label": "Océan profond",
        "deep": [18, 50, 82],
        "mid": [35, 82, 116],
        "shallow": [70, 130, 150],
        "lagoon": [95, 165, 165],
        "surf": [150, 205, 195],
        "seabed": [115, 105, 88],
    },
    "black_sea_deep": {
        "label": "Mer Noire / bleu sombre",
        "deep": [18, 43, 70],
        "mid": [32, 70, 90],
        "shallow": [62, 105, 112],
        "lagoon": [88, 130, 125],
        "surf": [150, 175, 165],
        "seabed": [90, 85, 72],
    },
    "muddy_water": {
        "label": "Eau vaseuse / trouble",
        "deep": [70, 85, 75],
        "mid": [100, 110, 85],
        "shallow": [135, 130, 95],
        "lagoon": [155, 145, 105],
        "surf": [190, 185, 150],
        "seabed": [125, 105, 70],
    },
    "river_delta_silty": {
        "label": "Delta / eau chargée en limon",
        "deep": [78, 88, 70],
        "mid": [112, 112, 78],
        "shallow": [148, 136, 90],
        "lagoon": [170, 150, 102],
        "surf": [200, 190, 145],
        "seabed": [135, 110, 70],
    },
    "mangrove_lagoon": {
        "label": "Mangrove / lagune verte",
        "deep": [38, 72, 58],
        "mid": [70, 105, 72],
        "shallow": [105, 132, 82],
        "lagoon": [135, 155, 95],
        "surf": [180, 190, 145],
        "seabed": [105, 85, 55],
    },
    "amazon_brown": {
        "label": "Fleuve tropical / brun organique",
        "deep": [80, 62, 42],
        "mid": [120, 88, 55],
        "shallow": [155, 112, 70],
        "lagoon": [180, 135, 90],
        "surf": [210, 185, 145],
        "seabed": [110, 82, 52],
    },
    "great_lakes_fresh": {
        "label": "Grands lacs / eau douce",
        "deep": [32, 75, 98],
        "mid": [55, 110, 125],
        "shallow": [90, 150, 145],
        "lagoon": [125, 175, 160],
        "surf": [185, 210, 195],
        "seabed": [120, 115, 95],
    },
    "alpine_lake": {
        "label": "Lac alpin / bleu vert clair",
        "deep": [22, 76, 110],
        "mid": [48, 125, 145],
        "shallow": [95, 175, 170],
        "lagoon": [135, 205, 190],
        "surf": [210, 235, 220],
        "seabed": [120, 125, 110],
    },
    "glacial_lake_milky": {
        "label": "Lac glaciaire / turquoise laiteux",
        "deep": [55, 98, 120],
        "mid": [85, 135, 150],
        "shallow": [130, 180, 180],
        "lagoon": [170, 210, 200],
        "surf": [225, 240, 230],
        "seabed": [150, 150, 135],
    },
    "green_algae_lake": {
        "label": "Lac végétal / algues vertes",
        "deep": [35, 70, 45],
        "mid": [65, 105, 55],
        "shallow": [105, 140, 65],
        "lagoon": [140, 165, 80],
        "surf": [185, 195, 135],
        "seabed": [90, 85, 55],
    },
    "volcanic_crater_lake": {
        "label": "Lac volcanique / bleu sombre vert",
        "deep": [12, 55, 72],
        "mid": [25, 92, 95],
        "shallow": [65, 135, 115],
        "lagoon": [95, 170, 135],
        "surf": [165, 210, 180],
        "seabed": [60, 58, 55],
    },
    "salt_lake_pale": {
        "label": "Lac salé / eau très pâle",
        "deep": [88, 130, 140],
        "mid": [125, 170, 165],
        "shallow": [170, 210, 190],
        "lagoon": [205, 230, 205],
        "surf": [240, 245, 225],
        "seabed": [220, 205, 165],
    },
    "dark_stormy": {
        "label": "Mer sombre / tempête",
        "deep": [25, 45, 60],
        "mid": [40, 70, 85],
        "shallow": [65, 95, 100],
        "lagoon": [80, 115, 112],
        "surf": [145, 165, 160],
        "seabed": [85, 80, 70],
    },
}

WATER_SEABED_RGB = HP_BEACH_RGB.copy()

FIELD_PALETTE = [
    np.array([150, 130, 95], dtype=np.float32),
    np.array([125, 110, 80], dtype=np.float32),
    np.array([110, 125, 75], dtype=np.float32),
    np.array([135, 120, 70], dtype=np.float32),
    np.array([165, 145, 105], dtype=np.float32),
    np.array([95, 120, 70], dtype=np.float32),
]

BASE_COLOR_BY_CATEGORY = {
    "field":  np.array([135, 120, 85], dtype=np.float32),
    "grass":  np.array([95, 128, 78], dtype=np.float32),
    "forest": np.array([72, 96, 58], dtype=np.float32),
    "earth":  np.array([140, 105, 70], dtype=np.float32),
    "rock":   np.array([122, 120, 114], dtype=np.float32),
    "sand":   np.array([210, 196, 168], dtype=np.float32),
    "beach":  np.array([182, 150, 118], dtype=np.float32),
    "gravel": np.array([122, 116, 104], dtype=np.float32),
    "road":   np.array([70, 70, 70], dtype=np.float32),
    "water":  np.array([58, 92, 130], dtype=np.float32),
    "other":  np.array([120, 120, 120], dtype=np.float32),
}

BLEND_BY_CATEGORY = {
    "field": 0.16,
    "grass": 0.10,
    "forest": 0.08,
    "earth": 0.12,
    "rock": 0.08,
    "sand": 0.08,
    "beach": 0.10,
    "gravel": 0.08,
    "road": 0.06,
    "water": 0.05,
    "other": 0.08,
}

CAT = {
    "field": 0,
    "grass": 1,
    "forest": 2,
    "earth": 3,
    "rock": 4,
    "sand": 5,
    "beach": 6,
    "gravel": 7,
    "road": 8,
    "water": 9,
    "other": 10,
}

BASE_COLOR_ARRAY = np.zeros((len(CAT), 3), dtype=np.float32)
BLEND_ARRAY = np.zeros((len(CAT),), dtype=np.float32)

for cat_name, cat_id in CAT.items():
    BASE_COLOR_ARRAY[cat_id] = BASE_COLOR_BY_CATEGORY.get(
        cat_name,
        BASE_COLOR_BY_CATEGORY["other"]
    )
    BLEND_ARRAY[cat_id] = BLEND_BY_CATEGORY.get(cat_name, 0.08)

FIELD_PALETTE_ARRAY = np.stack(FIELD_PALETTE).astype(np.float32)


# =========================================================
# ASC / NORMALISATION
# =========================================================
def load_asc_with_header(path: str):
    header = {}

    with open(path, "r", encoding="utf-8") as f:
        for _ in range(6):
            line = f.readline()
            if not line:
                raise ValueError("Header ASC incomplet.")
            parts = line.strip().split()
            if len(parts) >= 2:
                header[parts[0].lower()] = float(parts[1])

    # Plus rapide qu'une boucle Python ligne par ligne.
    elev = np.loadtxt(path, skiprows=6, dtype=np.float32)

    nodata = header.get("nodata_value", None)
    if nodata is not None:
        elev = np.where(elev == np.float32(nodata), np.nan, elev).astype(np.float32)

    return header, elev


def normalize_nan_safe(arr: np.ndarray) -> np.ndarray:
    out = arr.astype(np.float32, copy=True)
    valid = np.isfinite(out)

    if not np.any(valid):
        return np.zeros_like(out, dtype=np.float32)

    amin = np.nanmin(out)
    amax = np.nanmax(out)

    if amax - amin <= 1e-8:
        out.fill(0.0)
        return out

    out = (out - amin) / (amax - amin)
    out[~valid] = 0.0
    return out.astype(np.float32, copy=False)


# =========================================================
# LAYERS.CFG
# =========================================================
def parse_layers_cfg_legend(path: str):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    matches = re.findall(
        r"(\w+)\[\]\s*=\s*\{\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\}\}\s*;",
        content,
        flags=re.MULTILINE
    )

    color_to_layer = {}
    layer_to_color = {}

    for name, r, g, b in matches:
        rgb = (int(r), int(g), int(b))
        color_to_layer[rgb] = name
        layer_to_color[name] = rgb

    return color_to_layer, layer_to_color


def parse_layer_name_list(raw: str | None) -> set[str]:
    """Convertit une liste "nom1, nom2" en set normalisé."""
    if raw is None:
        return set()
    return {part.strip().lower() for part in raw.split(",") if part.strip()}


def layer_name_matches(layer_name: str, names: set[str]) -> bool:
    """Match exact insensible à la casse pour les noms de layers.cfg."""
    return layer_name.strip().lower() in names


def classify_layer(layer_name: str, beach_layer_names: set[str] | None = None, sand_source_layer_names: set[str] | None = None, land_side_layer_names: set[str] | None = None) -> str:
    name = layer_name.lower()
    beach_layer_names = beach_layer_names or set()
    sand_source_layer_names = sand_source_layer_names or set()
    land_side_layer_names = land_side_layer_names or set()

    if "water" in name or "ice_lake" in name or "ice_sea" in name:
        return "water"
    if layer_name_matches(layer_name, beach_layer_names):
        return "beach"
    if layer_name_matches(layer_name, sand_source_layer_names):
        return "sand"
    if layer_name_matches(layer_name, land_side_layer_names):
        return "earth"
    if "sand" in name:
        return "sand"
    if "beach" in name or "plage" in name:
        return "beach"
    if "tarmac" in name or "concrete" in name:
        return "road"
    if "gravel" in name:
        return "gravel"
    if "rock" in name or "stones" in name or "volcanic" in name:
        return "rock"
    if "forest" in name or "broadleaf" in name or "conifer" in name or "spruce" in name or "birch" in name:
        return "forest"
    if "grass" in name or "flowers" in name or "moss" in name or "stubble" in name or "snow_forest" in name:
        return "grass"
    if "soil" in name or "dirt" in name or "ground" in name:
        return "earth"

    return "field"


# =========================================================
# UTILS VECTORISÉS
# =========================================================
def rgb_to_key_arr(rgb_arr: np.ndarray) -> np.ndarray:
    return (
        (rgb_arr[..., 0].astype(np.uint32) << 16)
        | (rgb_arr[..., 1].astype(np.uint32) << 8)
        | rgb_arr[..., 2].astype(np.uint32)
    )


def rgb_to_key(rgb) -> int:
    r, g, b = rgb
    return (int(r) << 16) | (int(g) << 8) | int(b)


def resize_float_array(arr: np.ndarray, size: int) -> np.ndarray:
    img = Image.fromarray(arr.astype(np.float32)).resize(
        (size, size),
        Image.Resampling.BILINEAR
    )
    return np.asarray(img, dtype=np.float32)


def _single_noise(width: int, height: int, cell: int, amplitude: float) -> np.ndarray:
    small_h = height // cell + 1
    small_w = width // cell + 1

    arr = np.random.normal(0, 1, (small_h, small_w)).astype(np.float32)
    amin = arr.min()
    amax = arr.max()
    arr = (arr - amin) / (amax - amin + 1e-8)

    img = Image.fromarray((arr * 255).astype(np.uint8)).resize(
        (width, height),
        Image.Resampling.BILINEAR
    )
    out = np.asarray(img, dtype=np.float32) / 255.0
    return ((out - 0.5) * amplitude).astype(np.float32)


def build_multiscale_noise(width: int, height: int):
    noise_large = _single_noise(width, height, cell=96, amplitude=22.0)
    noise_medium = _single_noise(width, height, cell=40, amplitude=12.0)
    noise_fine = _single_noise(width, height, cell=12, amplitude=5.0)
    return noise_large, noise_medium, noise_fine


def blur_mask(mask_u8: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return mask_u8.astype(np.float32) / 255.0
    return (gaussian_filter(mask_u8.astype(np.float32), sigma=radius) / 255.0).astype(np.float32)


def dilate_mask(mask_bool: np.ndarray, radius: int = 6) -> np.ndarray:
    if radius <= 0:
        return mask_bool.astype(bool)
    return binary_dilation(mask_bool, iterations=radius)


def build_hard_soft_sand_mask(hp_sand_mask: np.ndarray, blur_radius: int = 1):
    soft = blur_mask(hp_sand_mask, blur_radius)
    sand_core = np.clip(
        (soft - FULL_SAND_THRESHOLD) / max(1.0 - FULL_SAND_THRESHOLD, 1e-6),
        0.0,
        1.0
    ).astype(np.float32)
    sand_edge = np.clip(soft, 0.0, 1.0).astype(np.float32)
    return sand_core, sand_edge


def apply_edge_breakup(sand_edge: np.ndarray, noise_medium: np.ndarray, noise_fine: np.ndarray) -> np.ndarray:
    """Casse le bord côté terre sans trouer le coeur de plage."""
    breakup = (
        (noise_medium / 12.0) * 0.75
        + (noise_fine / 5.0) * 0.25
    ) * EDGE_BREAKUP_SCALE

    edge_zone = (
        np.clip((sand_edge - 0.10) / 0.55, 0.0, 1.0)
        * (1.0 - np.clip((sand_edge - EDGE_INNER_PRESERVE) / 0.30, 0.0, 1.0))
    )

    mod = sand_edge - breakup * EDGE_BREAKUP_STRENGTH * edge_zone
    return np.clip(mod, 0.0, 1.0).astype(np.float32)


def get_natural_sand_color_vec(
    wetness: np.ndarray,
    dryness: np.ndarray,
    slope_val: np.ndarray,
    n_large: np.ndarray,
    n_medium: np.ndarray,
    n_fine: np.ndarray
) -> np.ndarray:
    """Version vectorisée de get_natural_sand_color()."""
    wetness = np.clip(wetness, 0.0, 1.0).astype(np.float32)[:, None]
    dryness = np.clip(dryness, 0.0, 1.0).astype(np.float32)[:, None]

    slope_val = slope_val.astype(np.float32)[:, None]
    n_large = n_large.astype(np.float32)[:, None]
    n_medium = n_medium.astype(np.float32)[:, None]
    n_fine = n_fine.astype(np.float32)[:, None]

    sand_col = SAND_WET_RGB * wetness + SAND_DRY_RGB * (1.0 - wetness)
    sand_col = sand_col * (1.0 - dryness * 0.35) + SAND_DRY_RGB * (dryness * 0.35)

    shell_factor = np.clip((n_fine / 5.0 + 0.5), 0.0, 1.0) * 0.20
    sand_col = sand_col * (1.0 - shell_factor) + SAND_SHELL_RGB * shell_factor

    sand_col += n_large * 0.10
    sand_col += n_medium * SAND_NOISE_STRENGTH
    sand_col += n_fine * 0.28

    sand_col -= WET_SAND_DARKEN * wetness
    sand_col += DRY_SAND_BRIGHTNESS * dryness
    sand_col -= slope_val * 10.0

    sand_col += np.array([2.0, 1.5, -1.5], dtype=np.float32) * (n_fine / 5.0)

    return np.clip(sand_col, 0, 255).astype(np.float32)


# =========================================================
# TRAITEMENTS PRINCIPAUX
# =========================================================
def build_category_map(mask: np.ndarray, color_to_layer: dict, beach_layer_names: set[str], sand_source_layer_names: set[str], land_side_layer_names: set[str] | None = None, mask_color_tolerance: float = 0.0):
    h, w, _ = mask.shape

    print("Construction vectorisée des catégories depuis layers.cfg...")

    category_id = np.full((h, w), CAT["field"], dtype=np.uint8)
    hp_sand_exact_mask = np.zeros((h, w), dtype=bool)
    land_side_exact_mask = np.zeros((h, w), dtype=bool)
    land_side_layer_names = land_side_layer_names or set()
    tolerance = float(mask_color_tolerance or 0.0)

    if tolerance <= 0.0:
        mask_key = rgb_to_key_arr(mask)
        for rgb, layer_name in color_to_layer.items():
            pixels = mask_key == rgb_to_key(rgb)
            cat_name = classify_layer(layer_name, beach_layer_names, sand_source_layer_names, land_side_layer_names)
            category_id[pixels] = CAT.get(cat_name, CAT["field"])

            if layer_name_matches(layer_name, sand_source_layer_names):
                hp_sand_exact_mask |= pixels
            if land_side_layer_names and layer_name_matches(layer_name, land_side_layer_names):
                land_side_exact_mask |= pixels

        del mask_key
        gc.collect()
        return category_id, hp_sand_exact_mask, land_side_exact_mask

    print(f"Tolérance RGB mask activée : ±{tolerance}")
    items = list(color_to_layer.items())
    tol2 = int(round(tolerance * tolerance * 3.0))
    chunk_rows = 512

    for y0 in range(0, h, chunk_rows):
        y1 = min(y0 + chunk_rows, h)
        chunk = mask[y0:y1].astype(np.int16, copy=False)
        best_dist = np.full((y1 - y0, w), tol2 + 1, dtype=np.int32)
        best_idx = np.full((y1 - y0, w), -1, dtype=np.int16)

        for idx, (rgb, _layer_name) in enumerate(items):
            r, g, b = rgb
            dr = chunk[..., 0].astype(np.int32) - int(r)
            dg = chunk[..., 1].astype(np.int32) - int(g)
            db = chunk[..., 2].astype(np.int32) - int(b)
            dist = dr * dr + dg * dg + db * db
            update = dist < best_dist
            best_dist[update] = dist[update]
            best_idx[update] = idx

        for idx, (_rgb, layer_name) in enumerate(items):
            pixels = best_idx == idx
            if not np.any(pixels):
                continue
            cat_name = classify_layer(layer_name, beach_layer_names, sand_source_layer_names, land_side_layer_names)
            category_id[y0:y1][pixels] = CAT.get(cat_name, CAT["field"])
            if layer_name_matches(layer_name, sand_source_layer_names):
                hp_sand_exact_mask[y0:y1] |= pixels
            if land_side_layer_names and layer_name_matches(layer_name, land_side_layer_names):
                land_side_exact_mask[y0:y1] |= pixels

    gc.collect()
    return category_id, hp_sand_exact_mask, land_side_exact_mask


def apply_base_satmap_correction(
    output: np.ndarray,
    category_id: np.ndarray,
    height_norm: np.ndarray,
    slope: np.ndarray,
    water_mask: np.ndarray,
    noise_large: np.ndarray,
    noise_medium: np.ndarray,
    noise_fine: np.ndarray,
    block_size: int,
    chunk_rows: int,
):
    print("Correction vectorisée de la satmap...")

    h, w = category_id.shape
    nb_y = (h + block_size - 1) // block_size
    nb_x = (w + block_size - 1) // block_size

    block_y = np.minimum(np.arange(nb_y) * block_size, h - 1)
    block_x = np.minimum(np.arange(nb_x) * block_size, w - 1)
    block_cat = category_id[np.ix_(block_y, block_x)]

    base_blocks = BASE_COLOR_ARRAY[block_cat].astype(np.float32, copy=True)

    field_blocks = block_cat == CAT["field"]
    if np.any(field_blocks):
        field_choices = np.random.randint(
            0,
            len(FIELD_PALETTE_ARRAY),
            size=int(field_blocks.sum())
        )
        base_blocks[field_blocks] = FIELD_PALETTE_ARRAY[field_choices]

    random_variation = np.random.randint(
        -6,
        7,
        size=(nb_y, nb_x, 3)
    ).astype(np.float32)
    base_blocks += random_variation

    blend_blocks = BLEND_ARRAY[block_cat].astype(np.float32)

    x_block_indices = np.arange(w) // block_size

    for y0 in range(0, h, chunk_rows):
        y1 = min(y0 + chunk_rows, h)
        y_block_indices = np.arange(y0, y1) // block_size

        parcel_base = base_blocks[y_block_indices[:, None], x_block_indices[None, :]]
        blend = blend_blocks[y_block_indices[:, None], x_block_indices[None, :]][..., None]

        cat_chunk = category_id[y0:y1]
        slope_chunk = slope[y0:y1]
        water_chunk = water_mask[y0:y1]

        noise_chunk = (
            noise_large[y0:y1] * 0.55
            + noise_medium[y0:y1] * 0.35
            + noise_fine[y0:y1] * 0.10
        )

        corr = parcel_base.astype(np.float32, copy=True)
        corr += (height_norm[y0:y1, :, None] - 0.5) * 12.0
        corr -= slope_chunk[:, :, None] * 10.0
        corr += noise_chunk[:, :, None]

        forest_mask = cat_chunk == CAT["forest"]
        if np.any(forest_mask):
            corr[forest_mask] -= 6.0

        rock_mask = cat_chunk == CAT["rock"]
        if np.any(rock_mask):
            corr[rock_mask] -= slope_chunk[rock_mask, None] * 8.0

        if np.any(water_chunk):
            corr[water_chunk] = BASE_COLOR_BY_CATEGORY["water"]

        np.clip(corr, 0, 255, out=corr)

        output_chunk = output[y0:y1]
        output_chunk *= (1.0 - blend)
        output_chunk += corr * blend
        np.clip(output_chunk, 0, 255, out=output_chunk)

    del base_blocks, blend_blocks
    gc.collect()


def smoothstep01(x: np.ndarray) -> np.ndarray:
    """Interpolation douce 0..1, utile pour éviter les bandes trop dures."""
    x = np.clip(x.astype(np.float32), 0.0, 1.0)
    return (x * x * (3.0 - 2.0 * x)).astype(np.float32)


def make_contour_weight(values: np.ndarray, center: float, width: float) -> np.ndarray:
    """Crée une bande douce autour d'une distance donnée pour le contouring."""
    return np.clip(1.0 - np.abs(values.astype(np.float32) - center) / max(width, 1e-6), 0.0, 1.0).astype(np.float32)


def apply_water_and_beach(
    output: np.ndarray,
    elev_m: np.ndarray,
    slope: np.ndarray,
    water_mask: np.ndarray,
    below_zero_mask: np.ndarray,
    dist_to_water: np.ndarray,
    sand_core: np.ndarray,
    sand_edge: np.ndarray,
    noise_large: np.ndarray,
    noise_medium: np.ndarray,
    noise_fine: np.ndarray,
    chunk_rows: int,
    sand_distance: float,
    sand_texture_settings: dict | None = None,
    water_texture_settings: dict | None = None,
    contour_settings: dict | None = None,
):
    """
    Application eau / fond marin / plage avec contouring.

    La version précédente mélangeait surtout une seule couleur d'eau avec le fond marin.
    Cette version ajoute une distance côté mer vers le rivage, puis construit plusieurs
    bandes douces : eau profonde, eau moyenne, eau turquoise peu profonde, liseré de
    ressac, sable humide et sable sec. Le résultat est un dégradé plus progressif de
    l'eau vers la plage.
    """
    print("Application vectorisée eau / fond marin / plage avec contouring...")

    h, _ = elev_m.shape

    # Distance côté mer : pour les pixels d'eau, distance jusqu'à la terre.
    print("Contouring eau -> plage...")
    dist_to_land = distance_transform_edt(water_mask).astype(np.float32)

    # Distances exprimées en pixels. Elles restent internes au rendu et ne changent
    # pas les masques d'altitude.
    contour_settings = contour_settings or {}
    surf_width = max(1.0, float(contour_settings.get("surf_width", 8.0)))
    shallow_factor = max(0.01, float(contour_settings.get("shallow_width_factor", 0.42)))
    mid_factor = max(0.01, float(contour_settings.get("mid_width_factor", 0.95)))
    deep_factor = max(0.01, float(contour_settings.get("deep_width_factor", 1.70)))
    foam_strength = max(0.0, float(contour_settings.get("foam_strength", 1.0)))
    wet_sand_width = max(1.0, float(contour_settings.get("wet_sand_width", WET_SAND_DISTANCE)))
    shallow_width = max(18.0, min(42.0, float(sand_distance) * shallow_factor))
    mid_width = max(38.0, min(96.0, float(sand_distance) * mid_factor))
    deep_width = max(80.0, min(180.0, float(sand_distance) * deep_factor))

    water_deep = WATER_DEEP_RGB.astype(np.float32)
    water_mid = WATER_MID_RGB.astype(np.float32)
    water_shallow = WATER_SHALLOW_RGB.astype(np.float32)
    water_lagoon = WATER_LAGOON_RGB.astype(np.float32)
    water_surf = WATER_SURF_RGB.astype(np.float32)
    wet_beach = WET_BEACH_RGB.astype(np.float32)

    for y0 in range(0, h, chunk_rows):
        y1 = min(y0 + chunk_rows, h)
        output_chunk = output[y0:y1]

        elev_chunk = elev_m[y0:y1]
        slope_chunk = slope[y0:y1]
        water_chunk = water_mask[y0:y1]
        below_zero_chunk = below_zero_mask[y0:y1]
        dist_land_chunk = dist_to_land[y0:y1]
        dist_beach_chunk = dist_to_water[y0:y1]

        nl = noise_large[y0:y1]
        nm = noise_medium[y0:y1]
        nf = noise_fine[y0:y1]

        # ---------------------------------------------------------
        # EAU : dégradé par contouring depuis le rivage vers le large.
        # ---------------------------------------------------------
        if np.any(water_chunk):
            water_yy, water_xx = np.where(water_chunk)
            d_land = dist_land_chunk[water_chunk]
            elev_vals = elev_chunk[water_chunk]
            slope_vals = slope_chunk[water_chunk]

            # Facteur de distance : 0 près de la plage, 1 vers le large.
            near_t = smoothstep01(d_land / max(surf_width, 1.0))
            shallow_t = smoothstep01(d_land / max(shallow_width, 1.0))
            mid_t = smoothstep01(d_land / max(mid_width, 1.0))
            deep_t = smoothstep01(d_land / max(deep_width, 1.0))

            # Facteur d'altitude/profondeur : stabilise le rendu si la heightmap
            # place l'eau très basse ou très proche du niveau zéro.
            depth = np.clip((SEA_LEVEL_METERS - elev_vals) / max(SEA_LEVEL_METERS - CLEAN_CUTOFF_METERS, 0.25), 0.0, 3.0)
            depth_t = smoothstep01(depth / 2.2)

            # Fond marin visible près du rivage.
            seabed = WATER_SEABED_RGB.copy()
            seabed = seabed + nl[water_chunk, None] * 0.10
            seabed = seabed + nm[water_chunk, None] * 0.08
            seabed = seabed + nf[water_chunk, None] * 0.03
            seabed = seabed - slope_vals[:, None] * 5.0

            # Construction en plusieurs rampes : lagon -> shallow -> mid -> deep.
            color = water_lagoon * (1.0 - shallow_t[:, None]) + water_shallow * shallow_t[:, None]
            color = color * (1.0 - mid_t[:, None]) + water_mid * mid_t[:, None]
            color = color * (1.0 - deep_t[:, None]) + water_deep * deep_t[:, None]

            # Teinte plus profonde si l'altitude est nettement sous le niveau de mer.
            color = color * (1.0 - depth_t[:, None] * 0.42) + water_deep * (depth_t[:, None] * 0.42)

            # Liserés doux de contouring, pour rappeler les bandes visibles sur une photo satellite.
            contour_1 = make_contour_weight(d_land, surf_width * 0.85, surf_width * 0.75)
            contour_2 = make_contour_weight(d_land, shallow_width * 0.52, shallow_width * 0.28)
            contour_3 = make_contour_weight(d_land, mid_width * 0.70, mid_width * 0.22)
            contour = np.clip((contour_1 * 0.22 + contour_2 * 0.14 + contour_3 * 0.08) * foam_strength, 0.0, 0.68)

            contour_color = water_surf * 0.62 + water_lagoon * 0.38
            color = color * (1.0 - contour[:, None]) + contour_color * contour[:, None]

            # Bruit très léger pour éviter un aplat uniforme.
            water_noise = nl[water_chunk, None] * 0.025 + nm[water_chunk, None] * 0.035 + nf[water_chunk, None] * 0.020
            color = color + water_noise

            # Fond marin volontairement plus discret qu'avant : on garde un peu de relief
            # au bord, mais on évite que la texture satellite d'origine transparaisse trop.
            seabed_alpha = np.clip(0.16 * (1.0 - shallow_t) * (1.0 - depth_t * 0.55), 0.0, 0.16)
            color = color * (1.0 - seabed_alpha[:, None]) + seabed * seabed_alpha[:, None]

            if water_texture_settings is not None:
                tex_gray, tex_rgb = sample_tiled_texture_points(water_texture_settings, water_yy + y0, water_xx)
                # Texture moins forte au large pour garder un dégradé propre, plus visible près du rivage.
                texture_shore_boost = np.clip(1.0 - shallow_t * 0.45, 0.55, 1.0).astype(np.float32)
                color = apply_water_texture_variation_to_colors(
                    color,
                    tex_gray,
                    tex_rgb,
                    float(water_texture_settings["strength"]),
                ) * texture_shore_boost[:, None] + color * (1.0 - texture_shore_boost[:, None])

            # Mélange final plus opaque pour tous les profils.
            # Objectif : bien recouvrir la texture d'origine tout en conservant le contouring.
            shore_boost = np.clip(1.0 - shallow_t, 0.0, 1.0)
            water_alpha = np.clip(0.90 + deep_t * 0.05 + depth_t * 0.04 + shore_boost * 0.03, 0.90, 0.985)
            final = output_chunk[water_chunk] * (1.0 - water_alpha[:, None]) + color * water_alpha[:, None]
            output_chunk[water_chunk] = np.clip(final, 0, 255)

        # ---------------------------------------------------------
        # PLAGE ÉMERGÉE : sable humide près de l'eau -> sable sec.
        # ---------------------------------------------------------
        sand_core_chunk = sand_core[y0:y1]
        sand_edge_chunk = sand_edge[y0:y1]

        sand_visible_mask = (
            (sand_edge_chunk > 0.01)
            & (~water_chunk)
            & (~below_zero_chunk)
        )

        if np.any(sand_visible_mask):
            d = dist_beach_chunk[sand_visible_mask]
            sand_yy, sand_xx = np.where(sand_visible_mask)

            wetness = 1.0 - smoothstep01(d / max(wet_sand_width * 1.25, 1.0))
            dryness = smoothstep01(d / max(float(sand_distance), 1.0))

            sand_col = get_natural_sand_color_vec(
                wetness=wetness,
                dryness=dryness,
                slope_val=slope_chunk[sand_visible_mask],
                n_large=nl[sand_visible_mask],
                n_medium=nm[sand_visible_mask],
                n_fine=nf[sand_visible_mask],
            )

            # Contouring léger sur la zone humide : crée un passage plus joli entre eau et sable.
            wet_band = make_contour_weight(d.astype(np.float32), wet_sand_width * 0.65, wet_sand_width * 0.70)
            wet_target = wet_beach + nl[sand_visible_mask, None] * 0.035 + nm[sand_visible_mask, None] * 0.045
            sand_col = sand_col * (1.0 - wet_band[:, None] * 0.32) + wet_target * (wet_band[:, None] * 0.32)

            # Très fine bordure de ressac sur le premier contact eau/sable.
            surf_band = np.clip(1.0 - d / max(3.5, 1.0), 0.0, 1.0).astype(np.float32)
            surf_col = water_surf * 0.38 + wet_beach * 0.62
            sand_col = sand_col * (1.0 - surf_band[:, None] * 0.24) + surf_col * (surf_band[:, None] * 0.24)

            if sand_texture_settings is not None:
                tex_gray, tex_rgb = sample_tiled_texture_points(sand_texture_settings, sand_yy + y0, sand_xx)
                sand_col = apply_texture_variation_to_colors(sand_col, tex_gray, tex_rgb, float(sand_texture_settings["strength"]))

            core_values = sand_core_chunk[sand_visible_mask]
            edge_values = sand_edge_chunk[sand_visible_mask]

            current = output_chunk[sand_visible_mask]
            result = current.copy()

            core_pixels = core_values > 0.01
            if np.any(core_pixels):
                alpha_core = np.minimum(1.0, 0.88 + core_values[core_pixels] * 0.12)[:, None]
                result[core_pixels] = (
                    current[core_pixels] * (1.0 - alpha_core)
                    + sand_col[core_pixels] * alpha_core
                )

            edge_pixels = ~core_pixels
            if np.any(edge_pixels):
                alpha_edge = np.clip(0.18 + 0.58 * edge_values[edge_pixels], 0.18, 0.76)[:, None]
                result[edge_pixels] = (
                    current[edge_pixels] * (1.0 - alpha_edge)
                    + sand_col[edge_pixels] * alpha_edge
                )

            output_chunk[sand_visible_mask] = np.clip(result, 0, 255)

    del dist_to_land
    gc.collect()

def apply_land_side_sand_second_pass(
    output: np.ndarray,
    elev_m: np.ndarray,
    slope: np.ndarray,
    water_mask: np.ndarray,
    below_zero_mask: np.ndarray,
    dist_to_water: np.ndarray,
    sand_edge: np.ndarray,
    noise_large: np.ndarray,
    noise_medium: np.ndarray,
    noise_fine: np.ndarray,
    chunk_rows: int,
    sand_distance: float,
    land_pass_distance: float,
    land_pass_strength: float,
    land_side_mask: np.ndarray | None = None,
    sand_texture_settings: dict | None = None,
):
    """
    Deuxième passe côté terre du sable - version plus courte et plus opaque.

    Objectif : éviter le gros halo sableux trop diffus.
    On applique une transition plus courte, plus dense près du bord,
    puis on casse légèrement le bord intérieur du sable côté terre.

    Si land_side_mask est fourni, la passe extérieure côté terre est limitée
    uniquement à cette troisième texture. Si aucun nom n’est fourni, le script
    conserve exactement le comportement précédent.
    """
    if land_pass_distance <= 0.0 or land_pass_strength <= 0.0:
        print("Deuxième passe côté terre du sable désactivée.")
        return

    if land_side_mask is not None and np.any(land_side_mask):
        print("Deuxième passe côté terre du sable (V2 adaptative, limitée à la texture côté terre)...")
    else:
        print("Deuxième passe côté terre du sable (V2 adaptative, tous profils)...")

    sand_source = sand_edge > LAND_PASS_SOURCE_THRESHOLD
    dist_outside_to_sand = distance_transform_edt(~sand_source).astype(np.float32)
    dist_inside_to_land = distance_transform_edt(sand_source).astype(np.float32)

    h, _ = elev_m.shape
    max_dist = max(float(land_pass_distance), 1.0)
    inner_dist = max(5.0, min(max_dist * 0.32, 16.0))
    max_sand_dist = max(float(sand_distance), 1.0)

    sand_dry = SAND_DRY_RGB.astype(np.float32)
    sand_shell = SAND_SHELL_RGB.astype(np.float32)
    earth_base = BASE_COLOR_BY_CATEGORY["earth"].astype(np.float32)
    grass_base = BASE_COLOR_BY_CATEGORY["grass"].astype(np.float32)

    for y0 in range(0, h, chunk_rows):
        y1 = min(y0 + chunk_rows, h)

        output_chunk = output[y0:y1]
        water_chunk = water_mask[y0:y1]
        below_chunk = below_zero_mask[y0:y1]
        slope_chunk = slope[y0:y1]
        dist_water_chunk = dist_to_water[y0:y1]
        sand_source_chunk = sand_source[y0:y1]
        dist_out_chunk = dist_outside_to_sand[y0:y1]
        dist_in_chunk = dist_inside_to_land[y0:y1]
        land_side_chunk = None if land_side_mask is None else land_side_mask[y0:y1]

        nl = noise_large[y0:y1]
        nm = noise_medium[y0:y1]
        nf = noise_fine[y0:y1]

        # PASSE A : bande extérieure sur la terre, volontairement courte.
        outer_mask = (
            (~sand_source_chunk)
            & (dist_out_chunk > 0.0)
            & (dist_out_chunk <= max_dist)
            & (~water_chunk)
            & (~below_chunk)
        )
        if land_side_chunk is not None:
            outer_mask &= land_side_chunk

        if np.any(outer_mask):
            d = dist_out_chunk[outer_mask]
            outer_yy, outer_xx = np.where(outer_mask)
            t = np.clip(d / max_dist, 0.0, 1.0).astype(np.float32)

            # Dégradé resserré : on coupe plus vite pour éviter le halo lointain.
            edge = np.clip(1.0 - (t / 0.78), 0.0, 1.0).astype(np.float32)
            edge_smooth = edge * edge * (3.0 - 2.0 * edge)
            mid = np.clip(1.0 - np.abs(t - 0.28) / 0.24, 0.0, 1.0).astype(np.float32)
            falloff = np.clip(1.0 - t * 0.92, 0.06, 1.0).astype(np.float32)

            current = output_chunk[outer_mask]
            green_bias = np.clip(
                (current[:, 1] - np.maximum(current[:, 0], current[:, 2])) / 70.0,
                0.0,
                1.0,
            )[:, None].astype(np.float32)

            current_luma = np.mean(current, axis=1, keepdims=True).astype(np.float32)
            warm_bias = np.clip((current[:, 0:1] - current[:, 2:3]) / 80.0, 0.0, 1.0).astype(np.float32)

            # Adaptation automatique pour tous les profils :
            # - profils courts / légers -> raccord discret, très proche de la couleur du terrain
            # - profils forts / larges  -> transition plus lisible mais toujours harmonisée
            profile_strength = np.clip(float(land_pass_strength), 0.0, 1.25)
            profile_distance = np.clip(max_dist / 24.0, 0.35, 1.85)
            match_bias = np.clip(0.60 + profile_distance * 0.16 - profile_strength * 0.06, 0.56, 0.88)
            sand_bias = np.clip(0.30 + profile_strength * 0.10, 0.24, 0.42)
            grass_bias = np.clip(0.10 + green_bias * 0.16, 0.10, 0.26)

            # Bord immédiat : sable encore présent, mais déjà accordé au terrain.
            near_sand = current * (0.14 + match_bias * 0.12) + sand_dry * 0.54 + earth_base * 0.22 + grass_base * 0.10
            near_sand = near_sand + nl[outer_mask, None] * 0.05 + nm[outer_mask, None] * 0.07 + nf[outer_mask, None] * 0.02
            near_sand = near_sand * (1.0 - green_bias * 0.10) + grass_base * (green_bias * 0.10)

            # Zone médiane : mélange adaptatif avec forte reprise de la teinte réelle du terrain.
            dusty = current * match_bias + sand_dry * sand_bias + earth_base * (0.22 - (match_bias - 0.60) * 0.10) + grass_base * (0.12 + green_bias * 0.10)
            dusty = dusty + nl[outer_mask, None] * 0.025 + nm[outer_mask, None] * 0.04 + nf[outer_mask, None] * 0.015
            dusty = dusty * (1.0 - green_bias * 0.10) + grass_base * (green_bias * 0.10)

            # Zone éloignée : presque entièrement raccordée au terrain pour supprimer l'effet sale.
            land_matched = current * (0.78 + (match_bias - 0.60) * 0.10) + earth_base * 0.12 + grass_base * grass_bias
            land_matched = land_matched + nm[outer_mask, None] * 0.015 + nf[outer_mask, None] * 0.008
            land_matched = land_matched * (1.0 - green_bias * 0.06) + grass_base * (green_bias * 0.06)
            land_matched = land_matched + (current_luma - 128.0) * 0.035 + warm_bias * 1.8

            w_near = (0.66 + 0.46 * edge_smooth + profile_strength * 0.04).astype(np.float32)
            w_mid = (0.26 + 0.82 * mid * (1.0 - t * 0.16)).astype(np.float32)
            w_far = np.clip((t - 0.14) / 0.86, 0.0, 1.0).astype(np.float32) * (0.74 + (profile_distance - 1.0) * 0.08)
            wt = np.maximum(w_near + w_mid + w_far, 1e-6)

            target = (
                near_sand * (w_near / wt)[:, None]
                + dusty * (w_mid / wt)[:, None]
                + land_matched * (w_far / wt)[:, None]
            )

            if sand_texture_settings is not None:
                tex_gray, tex_rgb = sample_tiled_texture_points(sand_texture_settings, outer_yy + y0, outer_xx)
                target = apply_texture_variation_to_colors(target, tex_gray, tex_rgb, float(sand_texture_settings["strength"]) * 0.65)

            breakup = np.clip(0.98 + nm[outer_mask] * 0.018 + nf[outer_mask] * 0.010, 0.76, 1.06).astype(np.float32)
            slope_factor = np.clip(1.0 - slope_chunk[outer_mask] * 0.32, 0.64, 1.0).astype(np.float32)
            water_guard = np.clip((dist_water_chunk[outer_mask] / max(max_sand_dist, 1.0)), 0.66, 1.0).astype(np.float32)

            alpha = (
                (0.14 + 0.56 * edge_smooth + 0.10 * mid + profile_strength * 0.04)
                * falloff
                * breakup
                * slope_factor
                * water_guard
                * float(land_pass_strength)
            ).astype(np.float32)
            alpha = np.clip(alpha, 0.04, 0.82)[:, None]

            result = current * (1.0 - alpha) + target * alpha
            output_chunk[outer_mask] = np.clip(result, 0, 255)

        # PASSE B : retouche du bord intérieur du sable côté terre.
        inner_mask = (
            sand_source_chunk
            & (dist_in_chunk > 0.0)
            & (dist_in_chunk <= inner_dist)
            & (dist_water_chunk > max(8.0, max_sand_dist * 0.36))
            & (~water_chunk)
            & (~below_chunk)
        )

        if np.any(inner_mask):
            d = dist_in_chunk[inner_mask]
            inner_yy, inner_xx = np.where(inner_mask)
            t = np.clip(d / inner_dist, 0.0, 1.0).astype(np.float32)
            edge = (1.0 - t).astype(np.float32)
            edge_smooth = edge * edge * (3.0 - 2.0 * edge)

            current = output_chunk[inner_mask]

            inner_green_bias = np.clip(
                (current[:, 1] - np.maximum(current[:, 0], current[:, 2])) / 70.0,
                0.0,
                1.0,
            )[:, None].astype(np.float32)
            inner_match = np.clip(0.42 + float(land_pass_strength) * 0.14 + max_dist / 80.0, 0.42, 0.68)

            dune_inside = current * (inner_match * 0.18) + sand_dry * 0.42 + earth_base * 0.26 + grass_base * 0.14
            dune_inside = dune_inside + nl[inner_mask, None] * 0.035 + nm[inner_mask, None] * 0.05 + nf[inner_mask, None] * 0.015
            dune_inside = dune_inside * (1.0 - inner_green_bias * 0.07) + grass_base * (inner_green_bias * 0.07)

            dry_inside = current * inner_match + sand_shell * 0.12 + sand_dry * 0.20 + earth_base * 0.12 + grass_base * 0.06
            dry_inside = dry_inside + nm[inner_mask, None] * 0.03 + nf[inner_mask, None] * 0.01

            target = dune_inside * edge_smooth[:, None] + dry_inside * (1.0 - edge_smooth)[:, None]

            if sand_texture_settings is not None:
                tex_gray, tex_rgb = sample_tiled_texture_points(sand_texture_settings, inner_yy + y0, inner_xx)
                target = apply_texture_variation_to_colors(target, tex_gray, tex_rgb, float(sand_texture_settings["strength"]) * 0.70)

            alpha = np.clip((0.18 + 0.36 * edge_smooth + float(land_pass_strength) * 0.06), 0.06, 0.74)[:, None]
            result = current * (1.0 - alpha) + target * alpha
            output_chunk[inner_mask] = np.clip(result, 0, 255)

    del sand_source, dist_outside_to_sand, dist_inside_to_land
    gc.collect()

def save_output_chunked(output: np.ndarray, output_satmap: str, chunk_rows: int):
    print("Contraste global léger + conversion uint8...")

    h, w, c = output.shape
    out_u8 = np.empty((h, w, c), dtype=np.uint8)

    for y0 in range(0, h, chunk_rows):
        y1 = min(y0 + chunk_rows, h)
        chunk = (output[y0:y1] - 128.0) * GLOBAL_CONTRAST + 128.0
        out_u8[y0:y1] = np.clip(chunk, 0, 255).astype(np.uint8)

    print(f"Sauvegarde satmap : {output_satmap}")
    Image.fromarray(out_u8).save(output_satmap)



def print_sand_presets_table():
    print("")
    print("TABLEAU DES PRESETS SAND")
    print("-" * 112)
    print(f"{'ID':<4} {'Nom':<16} {'Distance':>10} {'Pente max':>10} {'Hauteur max':>12}  Description")
    print("-" * 112)

    for preset in SAND_PRESETS:
        print(
            f"{preset['id']:<4} "
            f"{preset['name']:<16} "
            f"{preset['distance']:>10.0f} "
            f"{preset['slope_max']:>10.2f} "
            f"{preset['max_height']:>12.1f}  "
            f"{preset['description']}"
        )

    print("-" * 112)
    print("")
    print("Exemples :")
    print("  py satmap_generator_optimized_presets.py --target-size 10240 --chunk-rows 2048 --sand-preset 4")
    print("  py satmap_generator_optimized_presets.py --target-size 10240 --chunk-rows 2048 --sand-preset large")
    print("  py satmap_generator_optimized_presets.py --target-size 10240 --chunk-rows 2048 --sand-preset large --sand-distance 80")
    print("")


def resolve_sand_preset(value: str):
    if value is None:
        return None

    wanted = str(value).strip().lower()

    for preset in SAND_PRESETS:
        if wanted == preset["id"].lower() or wanted == preset["name"].lower():
            return preset

    valid = ", ".join([f"{p['id']}={p['name']}" for p in SAND_PRESETS])
    raise ValueError(f"Preset sand inconnu : {value}. Presets disponibles : {valid}")


def create_versioned_output_dir(output_root: Path) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    version = 1
    while True:
        candidate = output_root / f"output_V{version}"
        if not candidate.exists():
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        version += 1


def resolve_versioned_output_path(path_str: str) -> str:
    """
    Genere automatiquement un nom versionne du type _V1, _V2, _V3, etc.
    Exemple : satmap_final_10240.png -> satmap_final_10240_V1.png
    Si des versions existent deja, prend la suivante.
    """
    path = Path(path_str)
    parent = path.parent if str(path.parent) not in {"", "."} else Path(".")
    parent.mkdir(parents=True, exist_ok=True)

    ext = path.suffix
    stem = path.stem

    match = re.match(r"^(.*?)(?:_V(\d+))?$", stem, flags=re.IGNORECASE)
    base_stem = match.group(1) if match else stem

    version_pattern = re.compile(
        rf"^{re.escape(base_stem)}_V(\d+){re.escape(ext)}$",
        flags=re.IGNORECASE
    )

    max_version = 0

    for candidate in parent.iterdir():
        if not candidate.is_file():
            continue

        m = version_pattern.match(candidate.name)
        if m:
            max_version = max(max_version, int(m.group(1)))

    return str(parent / f"{base_stem}_V{max_version + 1}{ext}")


def parse_rgb_triplet(raw: str | None, option_name: str) -> np.ndarray | None:
    """Parse une couleur RGB au format 'R,G,B' ou '#RRGGBB'."""
    if raw is None:
        return None
    value = str(raw).strip()
    if not value:
        return None

    if value.startswith("#"):
        value = value[1:]
        if len(value) != 6:
            raise ValueError(f"{option_name} doit être au format #RRGGBB ou R,G,B.")
        try:
            parts = [int(value[i:i+2], 16) for i in (0, 2, 4)]
        except ValueError as exc:
            raise ValueError(f"{option_name} contient une couleur hexadécimale invalide.") from exc
    else:
        raw_parts = [p.strip() for p in value.split(",")]
        if len(raw_parts) != 3:
            raise ValueError(f"{option_name} doit contenir 3 valeurs RGB séparées par des virgules.")
        try:
            parts = [int(float(p)) for p in raw_parts]
        except ValueError as exc:
            raise ValueError(f"{option_name} contient une valeur RGB invalide.") from exc

    if any(p < 0 or p > 255 for p in parts):
        raise ValueError(f"{option_name} doit rester entre 0 et 255 pour chaque canal RGB.")

    return np.array(parts, dtype=np.float32)


def rgb_array_to_text(arr: np.ndarray) -> str:
    vals = np.clip(arr.astype(np.int32), 0, 255).tolist()
    return f"{vals[0]},{vals[1]},{vals[2]}"


def apply_sand_color_settings(args) -> dict:
    """Applique le preset ou les RGB custom au rendu sable/eau proche plage."""
    global HP_BEACH_RGB, SAND_WET_RGB, SAND_DRY_RGB, SAND_SHELL_RGB, WET_BEACH_RGB
    global BASE_COLOR_BY_CATEGORY, BASE_COLOR_ARRAY

    preset_key = str(getattr(args, "sand_color_preset", "belle_ile") or "belle_ile").strip().lower()
    if preset_key in {"default", "classic", "natural"}:
        preset_key = "belle_ile"
    if preset_key == "custom":
        base = SAND_COLOR_PRESETS["belle_ile"].copy()
    else:
        if preset_key not in SAND_COLOR_PRESETS:
            valid = ", ".join(sorted(list(SAND_COLOR_PRESETS.keys()) + ["custom"]))
            raise ValueError(f"Preset couleur sable inconnu : {preset_key}. Presets disponibles : {valid}")
        base = SAND_COLOR_PRESETS[preset_key].copy()

    dry_custom = parse_rgb_triplet(getattr(args, "sand_dry_rgb", None), "--sand-dry-rgb")
    wet_custom = parse_rgb_triplet(getattr(args, "sand_wet_rgb", None), "--sand-wet-rgb")
    shell_custom = parse_rgb_triplet(getattr(args, "sand_shell_rgb", None), "--sand-shell-rgb")
    wet_beach_custom = parse_rgb_triplet(getattr(args, "wet_beach_rgb", None), "--wet-beach-rgb")
    seabed_custom = parse_rgb_triplet(getattr(args, "seabed_rgb", None), "--seabed-rgb")

    # Ne jamais utiliser "array_a or array_b" avec numpy :
    # un tableau numpy n'a pas de vérité booléenne unique.
    dry = dry_custom if dry_custom is not None else np.array(base["dry"], dtype=np.float32)
    wet = wet_custom if wet_custom is not None else np.array(base["wet"], dtype=np.float32)
    shell = shell_custom if shell_custom is not None else np.array(base["shell"], dtype=np.float32)
    wet_beach = wet_beach_custom if wet_beach_custom is not None else np.array(base["wet_beach"], dtype=np.float32)
    seabed = seabed_custom if seabed_custom is not None else np.array(base["seabed"], dtype=np.float32)

    strength = float(getattr(args, "sand_color_strength", 1.0))
    if strength < 0.0 or strength > 1.5:
        raise ValueError("--sand-color-strength doit être entre 0.0 et 1.5.")

    # strength = 1.0 applique le preset exactement. <1 garde une partie de la palette d'origine.
    def mix(original: np.ndarray, target: np.ndarray) -> np.ndarray:
        return np.clip(original * (1.0 - min(strength, 1.0)) + target * min(strength, 1.0), 0, 255).astype(np.float32)

    SAND_DRY_RGB = mix(SAND_DRY_RGB, dry)
    SAND_WET_RGB = mix(SAND_WET_RGB, wet)
    SAND_SHELL_RGB = mix(SAND_SHELL_RGB, shell)
    WET_BEACH_RGB = mix(WET_BEACH_RGB, wet_beach)
    HP_BEACH_RGB = mix(HP_BEACH_RGB, seabed)

    # Catégories de base utilisées par la correction globale avant la passe plage.
    BASE_COLOR_BY_CATEGORY["sand"] = SAND_DRY_RGB.copy()
    BASE_COLOR_BY_CATEGORY["beach"] = WET_BEACH_RGB.copy()
    BASE_COLOR_ARRAY[CAT["sand"]] = BASE_COLOR_BY_CATEGORY["sand"]
    BASE_COLOR_ARRAY[CAT["beach"]] = BASE_COLOR_BY_CATEGORY["beach"]

    return {
        "preset": preset_key,
        "label": "Custom RGB" if preset_key == "custom" else SAND_COLOR_PRESETS[preset_key]["label"],
        "dry": rgb_array_to_text(SAND_DRY_RGB),
        "wet": rgb_array_to_text(SAND_WET_RGB),
        "shell": rgb_array_to_text(SAND_SHELL_RGB),
        "wet_beach": rgb_array_to_text(WET_BEACH_RGB),
        "seabed": rgb_array_to_text(HP_BEACH_RGB),
        "strength": strength,
    }



def apply_water_color_settings(args) -> dict:
    """Applique le preset ou les RGB custom au dégradé eau/fond marin proche plage."""
    global WATER_DEEP_RGB, WATER_MID_RGB, WATER_SHALLOW_RGB, WATER_LAGOON_RGB, WATER_SURF_RGB, WATER_SEABED_RGB
    global BASE_COLOR_BY_CATEGORY, BASE_COLOR_ARRAY

    preset_key = str(getattr(args, "water_color_preset", "atlantic_belle_ile") or "atlantic_belle_ile").strip().lower()
    if preset_key in {"default", "classic", "atlantic"}:
        preset_key = "atlantic_belle_ile"
    if preset_key == "custom":
        base = WATER_COLOR_PRESETS["atlantic_belle_ile"].copy()
    else:
        if preset_key not in WATER_COLOR_PRESETS:
            valid = ", ".join(sorted(list(WATER_COLOR_PRESETS.keys()) + ["custom"]))
            raise ValueError(f"Preset couleur eau inconnu : {preset_key}. Presets disponibles : {valid}")
        base = WATER_COLOR_PRESETS[preset_key].copy()

    deep_custom = parse_rgb_triplet(getattr(args, "water_deep_rgb", None), "--water-deep-rgb")
    mid_custom = parse_rgb_triplet(getattr(args, "water_mid_rgb", None), "--water-mid-rgb")
    shallow_custom = parse_rgb_triplet(getattr(args, "water_shallow_rgb", None), "--water-shallow-rgb")
    lagoon_custom = parse_rgb_triplet(getattr(args, "water_lagoon_rgb", None), "--water-lagoon-rgb")
    surf_custom = parse_rgb_triplet(getattr(args, "water_surf_rgb", None), "--water-surf-rgb")
    seabed_custom = parse_rgb_triplet(getattr(args, "water_seabed_rgb", None), "--water-seabed-rgb")

    deep = deep_custom if deep_custom is not None else np.array(base["deep"], dtype=np.float32)
    mid = mid_custom if mid_custom is not None else np.array(base["mid"], dtype=np.float32)
    shallow = shallow_custom if shallow_custom is not None else np.array(base["shallow"], dtype=np.float32)
    lagoon = lagoon_custom if lagoon_custom is not None else np.array(base["lagoon"], dtype=np.float32)
    surf = surf_custom if surf_custom is not None else np.array(base["surf"], dtype=np.float32)
    seabed = seabed_custom if seabed_custom is not None else np.array(base["seabed"], dtype=np.float32)

    strength = float(getattr(args, "water_color_strength", 1.0))
    if strength < 0.0 or strength > 1.5:
        raise ValueError("--water-color-strength doit être entre 0.0 et 1.5.")

    def mix(original: np.ndarray, target: np.ndarray) -> np.ndarray:
        s = min(strength, 1.0)
        return np.clip(original * (1.0 - s) + target * s, 0, 255).astype(np.float32)

    WATER_DEEP_RGB = mix(WATER_DEEP_RGB, deep)
    WATER_MID_RGB = mix(WATER_MID_RGB, mid)
    WATER_SHALLOW_RGB = mix(WATER_SHALLOW_RGB, shallow)
    WATER_LAGOON_RGB = mix(WATER_LAGOON_RGB, lagoon)
    WATER_SURF_RGB = mix(WATER_SURF_RGB, surf)
    WATER_SEABED_RGB = mix(WATER_SEABED_RGB, seabed)

    BASE_COLOR_BY_CATEGORY["water"] = WATER_DEEP_RGB.copy()
    BASE_COLOR_ARRAY[CAT["water"]] = BASE_COLOR_BY_CATEGORY["water"]

    return {
        "preset": preset_key,
        "label": "Custom RGB" if preset_key == "custom" else WATER_COLOR_PRESETS[preset_key]["label"],
        "deep": rgb_array_to_text(WATER_DEEP_RGB),
        "mid": rgb_array_to_text(WATER_MID_RGB),
        "shallow": rgb_array_to_text(WATER_SHALLOW_RGB),
        "lagoon": rgb_array_to_text(WATER_LAGOON_RGB),
        "surf": rgb_array_to_text(WATER_SURF_RGB),
        "seabed": rgb_array_to_text(WATER_SEABED_RGB),
        "strength": strength,
    }



def prepare_sand_texture_settings(args) -> dict | None:
    """Charge une texture optionnelle pour enrichir la matière du sable sur la satmap."""
    texture_path = str(getattr(args, "sand_texture_image", "") or "").strip()
    if not texture_path:
        return None
    path = Path(texture_path)
    if not path.exists():
        raise FileNotFoundError(f"Texture sable introuvable : {texture_path}")

    strength = float(getattr(args, "sand_texture_strength", 0.45))
    scale = float(getattr(args, "sand_texture_scale", 1.0))
    if strength < 0.0 or strength > 1.0:
        raise ValueError("--sand-texture-strength doit être entre 0.0 et 1.0.")
    if scale < 0.1 or scale > 8.0:
        raise ValueError("--sand-texture-scale doit être entre 0.1 et 8.0.")

    img = Image.open(path).convert("RGB")
    src_w, src_h = img.size
    tile_w = int(np.clip(round(src_w * scale), 32, 2048))
    tile_h = int(np.clip(round(src_h * scale), 32, 2048))
    if (tile_w, tile_h) != (src_w, src_h):
        img = img.resize((tile_w, tile_h), Image.Resampling.LANCZOS)

    rgb = np.asarray(img, dtype=np.float32) / 255.0
    gray = np.dot(rgb[..., :3], np.array([0.299, 0.587, 0.114], dtype=np.float32))
    gray_mean = float(np.mean(gray))
    gray = np.clip((gray - gray_mean) * 1.25 + 0.5, 0.0, 1.0).astype(np.float32)
    return {
        "path": str(path),
        "name": path.name,
        "strength": strength,
        "scale": scale,
        "rgb": rgb.astype(np.float32),
        "gray": gray,
        "tile_h": int(gray.shape[0]),
        "tile_w": int(gray.shape[1]),
    }





def prepare_water_texture_settings(args) -> dict | None:
    """Charge une texture optionnelle pour enrichir la surface de l'eau sur la satmap.

    Contrairement au sable, l'eau révèle très vite les répétitions carrées.
    La texture eau est donc préparée avec :
    - une tuile plus grande autorisée,
    - un léger lissage optionnel,
    - une répétition miroir,
    - une déformation de coordonnées stable sur toute la carte.

    Le traitement reste ensuite fait par chunks : seule la lecture de la texture
    utilise des coordonnées globales, ce qui évite les raccords visibles.
    """
    texture_path = str(getattr(args, "water_texture_image", "") or "").strip()
    if not texture_path:
        return None
    path = Path(texture_path)
    if not path.exists():
        raise FileNotFoundError(f"Texture eau introuvable : {texture_path}")

    strength = float(getattr(args, "water_texture_strength", 0.25))
    scale = float(getattr(args, "water_texture_scale", 1.0))
    smoothing = float(getattr(args, "water_texture_smoothing", 12.0))
    warp = float(getattr(args, "water_texture_warp", 18.0))
    if strength < 0.0 or strength > 1.0:
        raise ValueError("--water-texture-strength doit être entre 0.0 et 1.0.")
    if scale < 0.1 or scale > 8.0:
        raise ValueError("--water-texture-scale doit être entre 0.1 et 8.0.")
    if smoothing < 0.0 or smoothing > 64.0:
        raise ValueError("--water-texture-smoothing doit être entre 0.0 et 64.0.")
    if warp < 0.0 or warp > 96.0:
        raise ValueError("--water-texture-warp doit être entre 0.0 et 96.0.")

    img = Image.open(path).convert("RGB")
    src_w, src_h = img.size

    # 4096 limite la répétition visible sur une satmap 10240 sans exploser la RAM.
    tile_w = int(np.clip(round(src_w * scale), 32, 4096))
    tile_h = int(np.clip(round(src_h * scale), 32, 4096))
    if (tile_w, tile_h) != (src_w, src_h):
        img = img.resize((tile_w, tile_h), Image.Resampling.LANCZOS)

    rgb = np.asarray(img, dtype=np.float32) / 255.0

    # Lissage local de la matière eau. Il ne floute pas toute la satmap,
    # seulement la texture source, donc la génération par chunks reste inchangée.
    if smoothing > 0.0:
        rgb = gaussian_filter(rgb, sigma=(smoothing, smoothing, 0.0)).astype(np.float32)
        rgb = np.clip(rgb, 0.0, 1.0)

    gray = np.dot(rgb[..., :3], np.array([0.299, 0.587, 0.114], dtype=np.float32))
    gray_mean = float(np.mean(gray))
    gray = np.clip((gray - gray_mean) * 1.15 + 0.5, 0.0, 1.0).astype(np.float32)
    return {
        "path": str(path),
        "name": path.name,
        "strength": strength,
        "scale": scale,
        "smoothing": smoothing,
        "warp": warp,
        "wrap_mode": "mirror",
        "rgb": rgb.astype(np.float32),
        "gray": gray,
        "tile_h": int(gray.shape[0]),
        "tile_w": int(gray.shape[1]),
    }


def apply_water_texture_variation_to_colors(colors: np.ndarray, tex_gray: np.ndarray | None, tex_rgb: np.ndarray | None, strength: float) -> np.ndarray:
    """Texture eau volontairement douce : nuance la couleur sans créer de carrés visibles."""
    if tex_gray is None or tex_rgb is None or colors.size == 0 or strength <= 0.0:
        return colors
    detail = ((tex_gray.astype(np.float32) - 0.5) * 2.0)[:, None]

    # Eau = variation très basse fréquence : moins de contraste que le sable.
    brightness = np.clip(1.0 + detail * (0.10 * strength), 0.82, 1.16)
    chroma = np.clip(0.94 + tex_rgb.astype(np.float32) * 0.12, 0.88, 1.08)
    textured = colors.astype(np.float32) * brightness
    textured = textured * (1.0 - 0.08 * strength) + (colors.astype(np.float32) * chroma) * (0.08 * strength)
    luma = np.mean(tex_rgb.astype(np.float32), axis=1, keepdims=True)
    textured = textured + (luma - 0.5) * (4.0 * strength)
    return np.clip(textured, 0, 255).astype(np.float32)


def _wrap_texture_indices(values: np.ndarray, size: int, mode: str) -> np.ndarray:
    """Retourne des indices de texture répétables sans couture dure."""
    size = max(1, int(size))
    values_i = np.floor(values).astype(np.int64)
    if size == 1:
        return np.zeros_like(values_i, dtype=np.int64)

    if mode == "mirror":
        period = size * 2
        mod = np.mod(values_i, period)
        return np.where(mod < size, mod, period - mod - 1).astype(np.int64)

    return np.mod(values_i, size).astype(np.int64)


def _warp_texture_coordinates(texture_settings: dict, ys: np.ndarray, xs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Déforme très légèrement les coordonnées pour casser la lecture en grille.

    La formule est déterministe et basée sur les coordonnées globales, donc elle
    reste parfaitement stable entre deux chunks.
    """
    y = ys.astype(np.float32)
    x = xs.astype(np.float32)
    warp = float(texture_settings.get("warp", 0.0) or 0.0)
    if warp <= 0.0:
        return y, x

    warp_y = (
        np.sin(x * 0.0061 + y * 0.0027) * 0.55
        + np.sin(x * 0.0019 - y * 0.0073) * 0.45
    ) * warp
    warp_x = (
        np.sin(x * 0.0047 - y * 0.0059) * 0.60
        + np.sin(x * 0.0083 + y * 0.0017) * 0.40
    ) * warp
    return y + warp_y.astype(np.float32), x + warp_x.astype(np.float32)


def sample_tiled_texture_points(texture_settings: dict | None, ys: np.ndarray, xs: np.ndarray):
    if texture_settings is None or ys.size == 0:
        return None, None

    mode = str(texture_settings.get("wrap_mode", "repeat") or "repeat").lower()
    tile_h = int(texture_settings["tile_h"])
    tile_w = int(texture_settings["tile_w"])

    y_f, x_f = _warp_texture_coordinates(texture_settings, ys, xs)
    y0 = np.floor(y_f).astype(np.float32)
    x0 = np.floor(x_f).astype(np.float32)
    wy = (y_f - y0).astype(np.float32)
    wx = (x_f - x0).astype(np.float32)

    yi0 = _wrap_texture_indices(y0, tile_h, mode)
    xi0 = _wrap_texture_indices(x0, tile_w, mode)
    yi1 = _wrap_texture_indices(y0 + 1.0, tile_h, mode)
    xi1 = _wrap_texture_indices(x0 + 1.0, tile_w, mode)

    gray_tex = texture_settings["gray"]
    rgb_tex = texture_settings["rgb"]

    # Bilinear sampling : évite les ruptures pixelisées dans les grandes zones d'eau.
    g00 = gray_tex[yi0, xi0]
    g10 = gray_tex[yi0, xi1]
    g01 = gray_tex[yi1, xi0]
    g11 = gray_tex[yi1, xi1]
    gray = (
        g00 * (1.0 - wx) * (1.0 - wy)
        + g10 * wx * (1.0 - wy)
        + g01 * (1.0 - wx) * wy
        + g11 * wx * wy
    )

    wx3 = wx[:, None]
    wy3 = wy[:, None]
    c00 = rgb_tex[yi0, xi0]
    c10 = rgb_tex[yi0, xi1]
    c01 = rgb_tex[yi1, xi0]
    c11 = rgb_tex[yi1, xi1]
    rgb = (
        c00 * (1.0 - wx3) * (1.0 - wy3)
        + c10 * wx3 * (1.0 - wy3)
        + c01 * (1.0 - wx3) * wy3
        + c11 * wx3 * wy3
    )

    return gray.astype(np.float32), rgb.astype(np.float32)


def apply_texture_variation_to_colors(colors: np.ndarray, tex_gray: np.ndarray | None, tex_rgb: np.ndarray | None, strength: float) -> np.ndarray:
    if tex_gray is None or tex_rgb is None or colors.size == 0 or strength <= 0.0:
        return colors
    detail = ((tex_gray.astype(np.float32) - 0.5) * 2.0)[:, None]
    brightness = np.clip(1.0 + detail * (0.34 * strength), 0.58, 1.42)
    chroma = np.clip(0.78 + tex_rgb.astype(np.float32) * 0.44, 0.64, 1.28)
    textured = colors.astype(np.float32) * brightness
    textured = textured * (1.0 - 0.22 * strength) + (colors.astype(np.float32) * chroma) * (0.22 * strength)
    luma = np.mean(tex_rgb.astype(np.float32), axis=1, keepdims=True)
    textured = textured + (luma - 0.5) * (16.0 * strength)
    return np.clip(textured, 0, 255).astype(np.float32)


def print_sand_color_presets_table():
    print("")
    print("TABLEAU DES PRESETS COULEUR SABLE")
    print("-" * 110)
    print(f"{'ID':<16} {'Dry RGB':<14} {'Wet RGB':<14} {'Seabed RGB':<14} Description")
    print("-" * 110)
    for key, data in SAND_COLOR_PRESETS.items():
        print(
            f"{key:<16} "
            f"{','.join(map(str, data['dry'])):<14} "
            f"{','.join(map(str, data['wet'])):<14} "
            f"{','.join(map(str, data['seabed'])):<14} "
            f"{data['label']}"
        )
    print("custom           utilise --sand-dry-rgb / --sand-wet-rgb / --sand-shell-rgb / --wet-beach-rgb / --seabed-rgb")
    print("-" * 110)
    print("")


def print_water_color_presets_table():
    print("")
    print("TABLEAU DES PRESETS COULEUR EAU")
    print("-" * 132)
    print(f"{'ID':<24} {'Deep RGB':<13} {'Mid RGB':<13} {'Shallow RGB':<13} {'Lagoon RGB':<13} Description")
    print("-" * 132)
    for key, data in WATER_COLOR_PRESETS.items():
        print(
            f"{key:<24} "
            f"{','.join(map(str, data['deep'])):<13} "
            f"{','.join(map(str, data['mid'])):<13} "
            f"{','.join(map(str, data['shallow'])):<13} "
            f"{','.join(map(str, data['lagoon'])):<13} "
            f"{data['label']}"
        )
    print("custom                   utilise --water-deep-rgb / --water-mid-rgb / --water-shallow-rgb / --water-lagoon-rgb / --water-surf-rgb / --water-seabed-rgb")
    print("-" * 132)
    print("")



def print_progress(percent: int | float, message: str) -> None:
    """Ligne stable lue par le launcher : PROGRESS|pct|message."""
    pct = int(max(0, min(100, round(float(percent)))))
    print(f"PROGRESS|{pct}|{message}", flush=True)


def validate_image_input(path_str: str, option_name: str) -> None:
    path = Path(path_str)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"{option_name} introuvable : {path_str}")
    ext = path.suffix.lower()
    if ext not in SUPPORTED_IMAGE_EXTENSIONS:
        allowed = ", ".join(SUPPORTED_IMAGE_EXTENSIONS)
        raise ValueError(f"{option_name} doit être une image supportée ({allowed}) : {path_str}")


def validate_mask_format(path_str: str, tolerance: int | float) -> None:
    """Bloque les masks JPG par défaut, sauf si une tolérance RGB est explicitement utilisée."""
    ext = Path(path_str).suffix.lower()
    if ext in LOSSY_MASK_EXTENSIONS and float(tolerance) <= 0.0:
        allowed = ", ".join(LOSSLESS_MASK_EXTENSIONS)
        raise ValueError(
            "Le mask ne doit pas être en JPG/JPEG avec une tolérance RGB à 0. "
            f"Utilise un format sans perte ({allowed}) ou active --mask-color-tolerance."
        )


def verify_image_can_open(path_str: str, option_name: str) -> tuple[int, int]:
    validate_image_input(path_str, option_name)
    with Image.open(path_str) as img:
        img.verify()
    with Image.open(path_str) as img:
        return img.size


def read_asc_header_only(path_str: str) -> dict:
    header = {}
    with open(path_str, "r", encoding="utf-8") as f:
        for _ in range(6):
            line = f.readline()
            if not line:
                raise ValueError("Header ASC incomplet.")
            parts = line.strip().split()
            if len(parts) >= 2:
                header[parts[0].lower()] = float(parts[1])
    return header


def save_debug_bool(path: Path, arr: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((arr.astype(np.uint8) * 255)).save(path)


def save_debug_float(path: Path, arr: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = arr.astype(np.float32)
    finite = np.isfinite(data)
    if np.any(finite):
        amin = float(np.nanmin(data[finite]))
        amax = float(np.nanmax(data[finite]))
        if amax - amin > 1e-8:
            out = ((data - amin) / (amax - amin) * 255.0)
        else:
            out = np.zeros_like(data, dtype=np.float32)
    else:
        out = np.zeros_like(data, dtype=np.float32)
    out[~finite] = 0.0
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(path)


def save_debug_category_map(path: Path, category_id: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    colors = np.array([
        [135, 120, 85],   # field
        [95, 128, 78],    # grass
        [72, 96, 58],     # forest
        [140, 105, 70],   # earth
        [122, 120, 114],  # rock
        [210, 196, 168],  # sand
        [182, 150, 118],  # beach
        [122, 116, 104],  # gravel
        [70, 70, 70],     # road
        [58, 92, 130],    # water
        [120, 120, 120],  # other
    ], dtype=np.uint8)
    Image.fromarray(colors[np.clip(category_id, 0, len(colors) - 1)]).save(path)


def write_generation_report(args, started_at: datetime, finished_at: datetime, extra: dict) -> None:
    output_dir = Path(args.output_satmap).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    duration = max(0.0, (finished_at - started_at).total_seconds())
    arg_data = vars(args).copy()
    data = {
        "generator_version": GENERATOR_VERSION,
        "started_at": started_at.isoformat(timespec="seconds"),
        "finished_at": finished_at.isoformat(timespec="seconds"),
        "duration_seconds": round(duration, 3),
        "outputs": {
            "satmap": str(args.output_satmap),
            "beach_mask": str(args.output_beach_mask),
            "report": str(output_dir / REPORT_FILE_NAME),
            "settings_json": str(output_dir / SETTINGS_JSON_NAME),
        },
        "arguments": arg_data,
        "summary": extra,
    }
    (output_dir / SETTINGS_JSON_NAME).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Rapport complet de génération Satmap",
        "",
        f"Date de génération : `{finished_at.strftime('%Y-%m-%d %H:%M:%S')}`",
        f"Durée totale : `{duration:.1f} sec`",
        f"Version générateur : `{GENERATOR_VERSION}`",
        f"Dossier de sortie : `{output_dir}`",
        "",
        "## Fichiers source",
        "",
        f"- Heightmap ASC : `{args.heightmap}`",
        f"- Mask image : `{args.mask}`",
        f"- Satmap image : `{args.satmap}`",
        f"- Layers CFG : `{args.layers}`",
        "",
        "## Sorties",
        "",
        f"- Satmap : `{args.output_satmap}`",
        f"- Beach mask : `{args.output_beach_mask}`",
        f"- Réglages JSON : `{SETTINGS_JSON_NAME}`",
        "",
        "## Réglages principaux",
        "",
    ]
    for key, value in extra.items():
        lines.append(f"- {key} : `{value}`")
    lines += ["", "## Commande / arguments", "", "```json", json.dumps(arg_data, ensure_ascii=False, indent=2), "```", ""]
    (output_dir / REPORT_FILE_NAME).write_text("\n".join(lines), encoding="utf-8")
    print(f"Rapport complet créé : {output_dir / REPORT_FILE_NAME}")
    print(f"Réglages JSON créés : {output_dir / SETTINGS_JSON_NAME}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Générateur de satmap optimisé/vectorisé pour DayZ."
    )
    parser.add_argument("--heightmap", default=DEFAULT_HEIGHTMAP_PATH, help="Chemin vers heightmap.asc")
    parser.add_argument("--mask", default=DEFAULT_MASK_PATH, help="Chemin vers mask image (.png, .jpg, .jpeg, .bmp, .tif, .tiff)")
    parser.add_argument("--satmap", default=DEFAULT_SATMAP_PATH, help="Chemin vers satmap image (.png, .jpg, .jpeg, .bmp, .tif, .tiff)")
    parser.add_argument("--layers", default=DEFAULT_LAYERS_CFG_PATH, help="Chemin vers layers.cfg")
    parser.add_argument("--output-satmap", default=DEFAULT_OUTPUT_SATMAP, help="Image satmap finale")
    parser.add_argument("--output-beach-mask", default=DEFAULT_OUTPUT_BEACH_MASK, help="Masque plage/eau final")
    parser.add_argument("--target-size", type=int, default=DEFAULT_TARGET_SIZE, help="Taille cible carrée, ex: 10240")
    parser.add_argument("--chunk-rows", type=int, default=DEFAULT_CHUNK_ROWS, help="Nombre de lignes traitées par chunk")
    parser.add_argument("--block-size", type=int, default=32, help="Taille des blocs de correction couleur")

    parser.add_argument("--validate-only", action="store_true", help="Diagnostic complet sans génération de fichiers")
    parser.add_argument("--debug-masks", action="store_true", help="Génère des images de debug dans output_Vx/debug_masks")
    parser.add_argument("--no-report", action="store_true", help="Désactive le rapport Markdown/JSON écrit par le générateur")
    parser.add_argument("--mask-color-tolerance", type=float, default=0.0, help="Tolérance RGB pour associer un mask compressé aux couleurs de layers.cfg. 0 = exact, JPG bloqué")

    # Utilisation simple via tableau de presets.
    parser.add_argument(
        "--list-sand-presets",
        action="store_true",
        help="Affiche le tableau des presets sand puis quitte"
    )
    parser.add_argument(
        "--list-sand-color-presets",
        action="store_true",
        help="Affiche le tableau des presets couleur sable puis quitte"
    )
    parser.add_argument(
        "--list-water-color-presets",
        action="store_true",
        help="Affiche le tableau des presets couleur eau puis quitte"
    )
    parser.add_argument(
        "--sand-preset",
        default=None,
        help="Preset sand à utiliser : numéro 1-7 ou nom, ex: 4 ou large"
    )

    # Ces arguments remplacent la valeur du preset si tu veux ajuster finement.
    parser.add_argument("--sand-distance", type=float, default=None, help="Distance max au rivage en pixels pour générer du sable")
    parser.add_argument("--sand-slope-max", type=float, default=None, help="Pente max normalisée autorisée pour générer du sable")
    parser.add_argument("--sand-max-height", type=float, default=None, help="Altitude max en mètres pour générer du sable")

    parser.add_argument("--water-start-level", type=float, default=CLEAN_CUTOFF_METERS, help="Sous ce niveau : eau forte / fond marin")
    parser.add_argument("--water-end-level", type=float, default=SEA_LEVEL_METERS, help="Jusqu'à ce niveau : eau")
    parser.add_argument("--land-start-level", type=float, default=SEA_LEVEL_METERS, help="Au-dessus de ce niveau : terre / plage")
    parser.add_argument("--land-pass-distance", type=float, default=LAND_PASS_DISTANCE_DEFAULT, help="Distance en pixels de la 2e passe côté terre")
    parser.add_argument("--land-pass-strength", type=float, default=LAND_PASS_STRENGTH_DEFAULT, help="Force de la 2e passe côté terre, 0 à 1")
    parser.add_argument("--beach-layer-names", default=DEFAULT_BEACH_LAYER_NAMES, help="Noms des textures/layers considérés comme plage, séparés par virgules")
    parser.add_argument("--sand-layer-names", default=DEFAULT_SAND_SOURCE_LAYER_NAMES, help="Noms des textures/layers utilisés comme zone source du sable, séparés par virgules")
    parser.add_argument("--land-layer-names", default=DEFAULT_LAND_SIDE_LAYER_NAMES, help="Optionnel : noms des textures/layers limitant la transition côté terre, séparés par virgules. Vide = comportement précédent")

    parser.add_argument("--sand-color-preset", default="belle_ile", help="Preset couleur sable : belle_ile, atlantic_light, golden, pale_white, grey_shell, dark_volcanic, red_ochre ou custom")
    parser.add_argument("--sand-color-strength", type=float, default=1.0, help="Force d'application de la palette sable, 0.0 à 1.5. Défaut : 1.0")
    parser.add_argument("--sand-dry-rgb", default=None, help="Couleur sable sec custom au format R,G,B ou #RRGGBB")
    parser.add_argument("--sand-wet-rgb", default=None, help="Couleur sable humide custom au format R,G,B ou #RRGGBB")
    parser.add_argument("--sand-shell-rgb", default=None, help="Couleur coquillage/variation claire custom au format R,G,B ou #RRGGBB")
    parser.add_argument("--wet-beach-rgb", default=None, help="Couleur bord humide / wet beach custom au format R,G,B ou #RRGGBB")
    parser.add_argument("--seabed-rgb", default=None, help="Couleur fond marin visible près de la plage au format R,G,B ou #RRGGBB")
    parser.add_argument("--sand-texture-image", default="", help="Image de texture optionnelle pour enrichir visuellement le sable sur la satmap")
    parser.add_argument("--sand-texture-strength", type=float, default=0.45, help="Force de la texture sable, 0.0 à 1.0. Défaut : 0.45")
    parser.add_argument("--sand-texture-scale", type=float, default=1.0, help="Échelle de répétition de la texture sable. 1.0 = taille d'origine")

    parser.add_argument("--water-texture-image", default="", help="Image de texture optionnelle pour enrichir visuellement l'eau sur la satmap")
    parser.add_argument("--water-texture-strength", type=float, default=0.25, help="Force de la texture eau, 0.0 à 1.0. Défaut : 0.25")
    parser.add_argument("--water-texture-scale", type=float, default=1.0, help="Échelle de répétition de la texture eau. 1.0 = taille d'origine")
    parser.add_argument("--water-texture-smoothing", type=float, default=12.0, help="Lissage de la texture eau avant application, 0.0 à 64.0. Défaut : 12.0")
    parser.add_argument("--water-texture-warp", type=float, default=18.0, help="Déformation douce des coordonnées de texture eau, 0.0 à 96.0. Défaut : 18.0")

    parser.add_argument("--surf-width", type=float, default=8.0, help="Largeur du liseré de ressac en pixels")
    parser.add_argument("--shallow-width-factor", type=float, default=0.42, help="Facteur de largeur de l'eau peu profonde basé sur sand-distance")
    parser.add_argument("--mid-width-factor", type=float, default=0.95, help="Facteur de largeur de l'eau moyenne basé sur sand-distance")
    parser.add_argument("--deep-width-factor", type=float, default=1.70, help="Facteur de largeur de l'eau profonde basé sur sand-distance")
    parser.add_argument("--foam-strength", type=float, default=1.0, help="Force visuelle du ressac/contouring, 0.0 à 2.0")
    parser.add_argument("--wet-sand-width", type=float, default=float(WET_SAND_DISTANCE), help="Largeur du sable humide en pixels")

    parser.add_argument("--water-color-preset", default="atlantic_belle_ile", help="Preset couleur eau. Utilise --list-water-color-presets pour voir tous les choix, ou custom")
    parser.add_argument("--water-color-strength", type=float, default=1.0, help="Force d'application de la palette eau, 0.0 à 1.5. Défaut : 1.0")
    parser.add_argument("--water-deep-rgb", default=None, help="Couleur eau profonde custom au format R,G,B ou #RRGGBB")
    parser.add_argument("--water-mid-rgb", default=None, help="Couleur eau moyenne custom au format R,G,B ou #RRGGBB")
    parser.add_argument("--water-shallow-rgb", default=None, help="Couleur eau peu profonde custom au format R,G,B ou #RRGGBB")
    parser.add_argument("--water-lagoon-rgb", default=None, help="Couleur lagon / bord clair custom au format R,G,B ou #RRGGBB")
    parser.add_argument("--water-surf-rgb", default=None, help="Couleur ressac / écume custom au format R,G,B ou #RRGGBB")
    parser.add_argument("--water-seabed-rgb", default=None, help="Teinte fond marin sous l'eau au format R,G,B ou #RRGGBB")

    return parser.parse_args()


def main():
    global CLEAN_CUTOFF_METERS, SEA_LEVEL_METERS
    started_at = datetime.now()
    args = parse_args()
    print(f"Générateur Satmap v{GENERATOR_VERSION}")
    print_progress(1, "Démarrage")

    if args.list_sand_presets:
        print_sand_presets_table()
        return

    if args.list_sand_color_presets:
        print_sand_color_presets_table()
        return

    if args.list_water_color_presets:
        print_water_color_presets_table()
        return

    sand_color_settings = apply_sand_color_settings(args)
    water_color_settings = apply_water_color_settings(args)
    sand_texture_settings = prepare_sand_texture_settings(args)
    water_texture_settings = prepare_water_texture_settings(args)

    selected_preset = resolve_sand_preset(args.sand_preset)
    if selected_preset is None:
        selected_preset = {
            "id": "0",
            "name": "manuel_defaut",
            "distance": float(HP_SAND_DISTANCE),
            "slope_max": float(SAND_SLOPE_MAX),
            "max_height": float(HP_SAND_MAX_METERS),
            "description": "Réglage par défaut du script",
        }

    sand_distance = float(args.sand_distance if args.sand_distance is not None else selected_preset["distance"])
    sand_slope_max = float(args.sand_slope_max if args.sand_slope_max is not None else selected_preset["slope_max"])
    sand_max_height = float(args.sand_max_height if args.sand_max_height is not None else selected_preset["max_height"])

    CLEAN_CUTOFF_METERS = float(args.water_start_level)
    SEA_LEVEL_METERS = float(args.water_end_level)
    land_start_level = float(args.land_start_level)
    land_pass_distance = float(args.land_pass_distance)
    land_pass_strength = float(args.land_pass_strength)
    mask_color_tolerance = float(args.mask_color_tolerance)
    beach_layer_names = parse_layer_name_list(args.beach_layer_names)
    sand_source_layer_names = parse_layer_name_list(args.sand_layer_names)
    land_side_layer_names = parse_layer_name_list(args.land_layer_names)

    target_size = int(args.target_size)
    chunk_rows = int(args.chunk_rows)

    if not beach_layer_names:
        raise ValueError("--beach-layer-names doit contenir au moins un nom de layer.")
    if not sand_source_layer_names:
        raise ValueError("--sand-layer-names doit contenir au moins un nom de layer source pour le sable.")

    for p in [args.heightmap, args.mask, args.satmap, args.layers]:
        if not Path(p).exists():
            raise FileNotFoundError(f"Fichier introuvable : {p}")

    validate_image_input(args.mask, "--mask")
    validate_image_input(args.satmap, "--satmap")
    validate_mask_format(args.mask, mask_color_tolerance)

    if target_size < 512 or target_size > 30000:
        raise ValueError("--target-size doit être entre 512 et 30000.")
    if chunk_rows <= 0:
        raise ValueError("--chunk-rows doit être supérieur à 0.")
    if args.block_size < 4 or args.block_size > 512:
        raise ValueError("--block-size doit être entre 4 et 512.")
    if sand_distance <= 0:
        raise ValueError("--sand-distance doit être supérieur à 0.")
    if sand_slope_max <= 0:
        raise ValueError("--sand-slope-max doit être supérieur à 0.")
    if CLEAN_CUTOFF_METERS >= SEA_LEVEL_METERS:
        raise ValueError("--water-start-level doit être inférieur à --water-end-level.")
    if land_start_level < SEA_LEVEL_METERS:
        raise ValueError("--land-start-level doit être supérieur ou égal à --water-end-level.")
    if sand_max_height <= land_start_level:
        raise ValueError("--sand-max-height doit être supérieur à --land-start-level.")
    if land_pass_distance < 0 or land_pass_distance > LAND_PASS_DISTANCE_MAX:
        raise ValueError(f"--land-pass-distance doit être entre 0 et {LAND_PASS_DISTANCE_MAX}.")
    if land_pass_strength < 0 or land_pass_strength > LAND_PASS_STRENGTH_MAX:
        raise ValueError(f"--land-pass-strength doit être entre 0 et {LAND_PASS_STRENGTH_MAX}.")
    if mask_color_tolerance < 0 or mask_color_tolerance > 64:
        raise ValueError("--mask-color-tolerance doit être entre 0 et 64.")
    if args.surf_width < 1 or args.surf_width > 128:
        raise ValueError("--surf-width doit être entre 1 et 128.")
    if args.shallow_width_factor <= 0 or args.mid_width_factor <= 0 or args.deep_width_factor <= 0:
        raise ValueError("Les facteurs de contouring doivent être supérieurs à 0.")
    if args.foam_strength < 0 or args.foam_strength > 2:
        raise ValueError("--foam-strength doit être entre 0 et 2.")
    if args.wet_sand_width < 1 or args.wet_sand_width > 128:
        raise ValueError("--wet-sand-width doit être entre 1 et 128.")

    print_progress(3, "Validation")
    print("Lecture layers.cfg...")
    color_to_layer, _ = parse_layers_cfg_legend(args.layers)
    available_layers = set(color_to_layer.values())
    missing_beach = sorted([n for n in beach_layer_names if n not in {x.lower() for x in available_layers}])
    missing_sand = sorted([n for n in sand_source_layer_names if n not in {x.lower() for x in available_layers}])
    if missing_beach:
        print(f"ATTENTION : layers plage non trouvés dans layers.cfg : {', '.join(missing_beach)}")
    if missing_sand:
        print(f"ATTENTION : layers source sable non trouvés dans layers.cfg : {', '.join(missing_sand)}")

    if args.validate_only:
        print_progress(10, "Diagnostic fichiers")
        header = read_asc_header_only(args.heightmap)
        mask_size = verify_image_can_open(args.mask, "--mask")
        satmap_size = verify_image_can_open(args.satmap, "--satmap")
        estimated_output_gb = (target_size * target_size * 3 * 4) / (1024 ** 3)
        estimated_u8_gb = (target_size * target_size * 3) / (1024 ** 3)
        print("DIAGNOSTIC COMPLET")
        print(f"  heightmap header    : {header}")
        print(f"  mask size           : {mask_size}")
        print(f"  satmap size         : {satmap_size}")
        print(f"  layers détectés     : {len(available_layers)}")
        print(f"  mask tolerance RGB  : {mask_color_tolerance}")
        print(f"  estimation output   : {estimated_output_gb:.2f} Go float32 + {estimated_u8_gb:.2f} Go uint8")
        print_progress(100, "Diagnostic terminé")
        print("Diagnostic terminé : configuration valide.")
        return

    if args.output_satmap == DEFAULT_OUTPUT_SATMAP and args.output_beach_mask == DEFAULT_OUTPUT_BEACH_MASK:
        output_dir = create_versioned_output_dir(Path("outputs"))
        args.output_satmap = str(output_dir / DEFAULT_OUTPUT_SATMAP)
        args.output_beach_mask = str(output_dir / DEFAULT_OUTPUT_BEACH_MASK)
    else:
        args.output_satmap = resolve_versioned_output_path(args.output_satmap)
        args.output_beach_mask = resolve_versioned_output_path(args.output_beach_mask)
        output_dir = Path(args.output_satmap).parent

    random.seed(SEED)
    np.random.seed(SEED)

    contour_settings = {
        "surf_width": float(args.surf_width),
        "shallow_width_factor": float(args.shallow_width_factor),
        "mid_width_factor": float(args.mid_width_factor),
        "deep_width_factor": float(args.deep_width_factor),
        "foam_strength": float(args.foam_strength),
        "wet_sand_width": float(args.wet_sand_width),
    }

    print("Preset sand :")
    print(f"  preset             : {selected_preset['id']} - {selected_preset['name']}")
    print(f"  distance au rivage : {sand_distance} px")
    print(f"  pente max          : {sand_slope_max}")
    print(f"  hauteur max        : {sand_max_height} m")
    print("Réglages eau / terre :")
    print(f"  eau forte sous     : < {CLEAN_CUTOFF_METERS} m")
    print(f"  eau jusqu'à        : <= {SEA_LEVEL_METERS} m")
    print(f"  terre/plage dès    : > {land_start_level} m")
    print("Deuxième passe terre :")
    print(f"  distance transition: {land_pass_distance} px")
    print(f"  force transition   : {land_pass_strength}")
    print("Contouring eau / plage :")
    for k, v in contour_settings.items():
        print(f"  {k:22}: {v}")
    print("Couleur sable satmap :")
    print(f"  preset couleur     : {sand_color_settings['preset']} - {sand_color_settings['label']}")
    print(f"  force couleur      : {sand_color_settings['strength']}")
    print(f"  sable sec RGB      : {sand_color_settings['dry']}")
    print(f"  sable humide RGB   : {sand_color_settings['wet']}")
    print(f"  bord humide RGB    : {sand_color_settings['wet_beach']}")
    print(f"  fond marin RGB     : {sand_color_settings['seabed']}")
    if sand_texture_settings is not None:
        print("Texture sable satmap :")
        print(f"  image texture      : {sand_texture_settings['name']}")
        print(f"  force texture      : {sand_texture_settings['strength']}")
        print(f"  échelle texture    : {sand_texture_settings['scale']}")
    else:
        print("Texture sable satmap : désactivée")
    print("Couleur eau satmap :")
    print(f"  preset eau         : {water_color_settings['preset']} - {water_color_settings['label']}")
    print(f"  force eau          : {water_color_settings['strength']}")
    print(f"  eau profonde RGB   : {water_color_settings['deep']}")
    print(f"  eau moyenne RGB    : {water_color_settings['mid']}")
    print(f"  eau peu profonde RGB: {water_color_settings['shallow']}")
    print(f"  lagon RGB          : {water_color_settings['lagoon']}")
    print(f"  ressac RGB         : {water_color_settings['surf']}")
    print(f"  fond marin eau RGB : {water_color_settings['seabed']}")
    if water_texture_settings is not None:
        print("Texture eau satmap :")
        print(f"  image texture eau : {water_texture_settings['name']}")
        print(f"  force texture eau : {water_texture_settings['strength']}")
        print(f"  échelle texture eau: {water_texture_settings['scale']}")
        print(f"  lissage texture eau: {water_texture_settings['smoothing']}")
        print(f"  déformation texture: {water_texture_settings['warp']}")
    else:
        print("Texture eau satmap : désactivée")
    print("Textures / layers.cfg :")
    print(f"  layers plage       : {', '.join(sorted(beach_layer_names))}")
    print(f"  layers source sable: {', '.join(sorted(sand_source_layer_names))}")
    if land_side_layer_names:
        print(f"  layers côté terre : {', '.join(sorted(land_side_layer_names))}")
    else:
        print("  layers côté terre : non utilisé (comportement précédent)")
    print("Sorties :")
    print(f"  satmap             : {args.output_satmap}")
    print(f"  beach mask         : {args.output_beach_mask}")

    print_progress(10, "Chargement heightmap")
    print("Chargement heightmap ASC...")
    header, elev_raw = load_asc_with_header(args.heightmap)

    print_progress(16, "Redimensionnement heightmap")
    print("Resize heightmap en mètres...")
    valid_mask = np.isfinite(elev_raw)
    fill_value = float(np.nanmin(elev_raw[valid_mask])) if np.any(valid_mask) else 0.0
    elev_fill = np.where(valid_mask, elev_raw, fill_value).astype(np.float32)
    elev_m = resize_float_array(elev_fill, target_size)
    height_norm = normalize_nan_safe(elev_m)

    print_progress(24, "Chargement mask")
    print("Chargement mask...")
    mask = np.asarray(
        Image.open(args.mask).convert("RGB").resize(
            (target_size, target_size),
            Image.Resampling.NEAREST
        ),
        dtype=np.uint8
    )

    print_progress(32, "Chargement satmap")
    print("Chargement satmap...")
    output = np.asarray(
        Image.open(args.satmap).convert("RGB").resize(
            (target_size, target_size),
            Image.Resampling.LANCZOS
        ),
        dtype=np.float32
    )

    h, w = elev_m.shape

    print_progress(40, "Calcul pente")
    print("Calcul pente...")
    cellsize = header.get("cellsize", 1.0)
    scale_x = (elev_raw.shape[1] / target_size) * cellsize
    scale_y = (elev_raw.shape[0] / target_size) * cellsize

    gy, gx = np.gradient(elev_m, scale_y, scale_x)
    slope = np.sqrt(gx**2 + gy**2).astype(np.float32)
    slope = normalize_nan_safe(slope)
    del gy, gx
    gc.collect()

    print_progress(46, "Construction des catégories")
    category_id, hp_sand_exact_mask, land_side_exact_mask = build_category_map(mask, color_to_layer, beach_layer_names, sand_source_layer_names, land_side_layer_names, mask_color_tolerance=mask_color_tolerance)
    if not np.any(hp_sand_exact_mask):
        available_layers_text = ", ".join(sorted(set(color_to_layer.values())))
        raise ValueError(
            "Aucune texture source sable trouvée dans le mask/layers.cfg. "
            f"Vérifie --sand-layer-names. Layers disponibles : {available_layers_text}"
        )
    if land_side_layer_names and not np.any(land_side_exact_mask):
        available_layers_text = ", ".join(sorted(set(color_to_layer.values())))
        print(
            "ATTENTION : aucune texture côté terre trouvée dans le mask/layers.cfg. "
            "La deuxième passe côté terre fonctionnera comme précédemment. "
            f"Vérifie --land-layer-names si besoin. Layers disponibles : {available_layers_text}"
        )
        land_side_exact_mask = None
    elif not land_side_layer_names:
        land_side_exact_mask = None

    debug_dir = Path(args.output_satmap).parent / "debug_masks"
    if args.debug_masks:
        print("Debug masks : sauvegarde category_map...")
        save_debug_category_map(debug_dir / "debug_category_map.png", category_id)

    del mask
    gc.collect()

    print_progress(52, "Extension zone sable")
    print("Extension locale de la zone source sable autorisée...")
    hp_sand_allowed_mask = dilate_mask(hp_sand_exact_mask, radius=8)
    del hp_sand_exact_mask
    gc.collect()

    print_progress(58, "Détection niveaux eau")
    print(f"Détection eau / terre : eau forte < {CLEAN_CUTOFF_METERS}m, eau <= {SEA_LEVEL_METERS}m, terre > {land_start_level}m...")
    finite_elev = np.isfinite(elev_m)
    below_zero_mask = finite_elev & (elev_m < CLEAN_CUTOFF_METERS)
    water_mask = finite_elev & (elev_m <= SEA_LEVEL_METERS)

    print_progress(62, "Calcul distance au rivage")
    print("Distance au rivage optimisée...")
    dist_to_water = distance_transform_edt(~water_mask).astype(np.float32)

    print_progress(68, "Création du bruit")
    print("Création bruit multi-échelle...")
    noise_large, noise_medium, noise_fine = build_multiscale_noise(w, h)

    print_progress(74, "Correction satmap")
    apply_base_satmap_correction(
        output=output,
        category_id=category_id,
        height_norm=height_norm,
        slope=slope,
        water_mask=water_mask,
        noise_large=noise_large,
        noise_medium=noise_medium,
        noise_fine=noise_fine,
        block_size=args.block_size,
        chunk_rows=chunk_rows,
    )

    print_progress(78, "Génération rivage")
    print("Génération textures plage + sable vectorisée...")
    allowed_for_sand_ids = np.array([
        CAT["sand"],
        CAT["beach"],
        CAT["earth"],
        CAT["grass"],
        CAT["field"],
        CAT["gravel"],
    ], dtype=np.uint8)

    allowed_for_sand = np.isin(category_id, allowed_for_sand_ids)
    if args.debug_masks:
        save_debug_bool(debug_dir / "debug_allowed_for_sand.png", allowed_for_sand)
    del category_id
    gc.collect()

    hp_sand_bool = (
        (~water_mask)
        & hp_sand_allowed_mask
        & allowed_for_sand
        & (elev_m > land_start_level)
        & (elev_m <= sand_max_height)
        & (slope <= sand_slope_max)
        & (dist_to_water <= sand_distance)
    )

    del hp_sand_allowed_mask, allowed_for_sand
    gc.collect()

    hp_sand_mask = (hp_sand_bool.astype(np.uint8) * 255)
    if args.debug_masks:
        save_debug_bool(debug_dir / "debug_hp_sand_bool.png", hp_sand_bool)
    del hp_sand_bool
    gc.collect()

    sand_core, sand_edge = build_hard_soft_sand_mask(hp_sand_mask, MASK_BLUR_RADIUS)
    del hp_sand_mask
    gc.collect()

    sand_core[water_mask] = 0.0
    sand_core[below_zero_mask] = 0.0

    sand_edge[water_mask] = 0.0
    sand_edge[below_zero_mask] = 0.0

    sand_edge = apply_edge_breakup(sand_edge, noise_medium, noise_fine)
    sand_core = np.minimum(sand_core, sand_edge + 0.35).astype(np.float32)
    np.clip(sand_core, 0.0, 1.0, out=sand_core)

    if args.debug_masks:
        print("Debug masks : sauvegarde masques principaux...")
        save_debug_bool(debug_dir / "debug_water_mask.png", water_mask)
        save_debug_bool(debug_dir / "debug_below_zero_mask.png", below_zero_mask)
        save_debug_float(debug_dir / "debug_slope.png", slope)
        save_debug_float(debug_dir / "debug_dist_to_water.png", dist_to_water)
        save_debug_float(debug_dir / "debug_sand_core.png", sand_core)
        save_debug_float(debug_dir / "debug_sand_edge.png", sand_edge)
        if land_side_exact_mask is not None:
            save_debug_bool(debug_dir / "debug_land_side_mask.png", land_side_exact_mask)

    print_progress(82, "Application eau / plage")
    apply_water_and_beach(
        output=output,
        elev_m=elev_m,
        slope=slope,
        water_mask=water_mask,
        below_zero_mask=below_zero_mask,
        dist_to_water=dist_to_water,
        sand_core=sand_core,
        sand_edge=sand_edge,
        noise_large=noise_large,
        noise_medium=noise_medium,
        noise_fine=noise_fine,
        chunk_rows=chunk_rows,
        sand_distance=sand_distance,
        sand_texture_settings=sand_texture_settings,
        water_texture_settings=water_texture_settings,
        contour_settings=contour_settings,
    )

    print_progress(88, "Application côté terre")
    apply_land_side_sand_second_pass(
        output=output,
        elev_m=elev_m,
        slope=slope,
        water_mask=water_mask,
        below_zero_mask=below_zero_mask,
        dist_to_water=dist_to_water,
        sand_edge=sand_edge,
        noise_large=noise_large,
        noise_medium=noise_medium,
        noise_fine=noise_fine,
        chunk_rows=chunk_rows,
        sand_distance=sand_distance,
        land_pass_distance=land_pass_distance,
        land_pass_strength=land_pass_strength,
        land_side_mask=land_side_exact_mask,
        sand_texture_settings=sand_texture_settings,
    )

    print_progress(94, "Création beach mask")
    print("Création beach mask...")
    beach_mask_out = np.zeros((h, w), dtype=np.uint8)
    beach_mask_out[water_mask] = 128
    beach_mask_out[sand_edge > 0.05] = 255
    beach_mask_out[below_zero_mask] = 128

    print_progress(96, "Sauvegarde beach mask")
    print(f"Sauvegarde beach mask : {args.output_beach_mask}")
    Image.fromarray(beach_mask_out).save(args.output_beach_mask)

    del beach_mask_out, water_mask, below_zero_mask, sand_core, sand_edge
    del elev_m, slope, height_norm, dist_to_water
    if land_side_exact_mask is not None:
        del land_side_exact_mask
    del noise_large, noise_medium, noise_fine
    gc.collect()

    print_progress(98, "Sauvegarde satmap")
    save_output_chunked(output, args.output_satmap, chunk_rows)

    report_extra = {
        "preset_sand": f"{selected_preset['id']} - {selected_preset['name']}",
        "sand_distance": sand_distance,
        "sand_slope_max": sand_slope_max,
        "sand_max_height": sand_max_height,
        "water_start_level": CLEAN_CUTOFF_METERS,
        "water_end_level": SEA_LEVEL_METERS,
        "land_start_level": land_start_level,
        "land_pass_distance": land_pass_distance,
        "land_pass_strength": land_pass_strength,
        "mask_color_tolerance": mask_color_tolerance,
        "debug_masks": bool(args.debug_masks),
        **contour_settings,
    }
    if not args.no_report:
        write_generation_report(args, started_at, datetime.now(), report_extra)

    print_progress(100, "Terminé")
    print("Terminé.")
    print(f"Satmap : {args.output_satmap}")
    print(f"Beach mask : {args.output_beach_mask}")


if __name__ == "__main__":
    main()
