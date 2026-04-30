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
import re
import random
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
GENERATOR_VERSION = "1.1.0"

DEFAULT_HEIGHTMAP_PATH = "input/heightmap.asc"
DEFAULT_MASK_PATH = "input/mask.png"
DEFAULT_SATMAP_PATH = "input/satmap.png"
DEFAULT_LAYERS_CFG_PATH = "input/layers.cfg"

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

# Eau / contouring : plusieurs teintes pour un dégradé mer -> plage plus naturel.
WATER_DEEP_RGB = np.array([58, 88, 122], dtype=np.float32)
WATER_MID_RGB = np.array([70, 112, 142], dtype=np.float32)
WATER_SHALLOW_RGB = np.array([93, 149, 156], dtype=np.float32)
WATER_LAGOON_RGB = np.array([118, 181, 174], dtype=np.float32)
WATER_SURF_RGB = np.array([156, 202, 190], dtype=np.float32)
WET_BEACH_RGB = np.array([181, 156, 128], dtype=np.float32)

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
def build_category_map(mask: np.ndarray, color_to_layer: dict, beach_layer_names: set[str], sand_source_layer_names: set[str], land_side_layer_names: set[str] | None = None):
    h, w, _ = mask.shape

    print("Construction vectorisée des catégories depuis layers.cfg...")
    mask_key = rgb_to_key_arr(mask)

    category_id = np.full((h, w), CAT["field"], dtype=np.uint8)
    hp_sand_exact_mask = np.zeros((h, w), dtype=bool)
    land_side_exact_mask = np.zeros((h, w), dtype=bool)
    land_side_layer_names = land_side_layer_names or set()

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
    surf_width = 8.0
    shallow_width = max(18.0, min(42.0, float(sand_distance) * 0.42))
    mid_width = max(38.0, min(96.0, float(sand_distance) * 0.95))
    deep_width = max(80.0, min(180.0, float(sand_distance) * 1.70))

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
            seabed = HP_BEACH_RGB.copy()
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
            contour = np.clip(contour_1 * 0.22 + contour_2 * 0.14 + contour_3 * 0.08, 0.0, 0.34)

            contour_color = water_surf * 0.62 + water_lagoon * 0.38
            color = color * (1.0 - contour[:, None]) + contour_color * contour[:, None]

            # Bruit très léger pour éviter un aplat uniforme.
            water_noise = nl[water_chunk, None] * 0.025 + nm[water_chunk, None] * 0.035 + nf[water_chunk, None] * 0.020
            color = color + water_noise

            # Fond marin volontairement plus discret qu'avant : on garde un peu de relief
            # au bord, mais on évite que la texture satellite d'origine transparaisse trop.
            seabed_alpha = np.clip(0.16 * (1.0 - shallow_t) * (1.0 - depth_t * 0.55), 0.0, 0.16)
            color = color * (1.0 - seabed_alpha[:, None]) + seabed * seabed_alpha[:, None]

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

            wetness = 1.0 - smoothstep01(d / max(WET_SAND_DISTANCE * 1.25, 1.0))
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
            wet_band = make_contour_weight(d.astype(np.float32), WET_SAND_DISTANCE * 0.65, WET_SAND_DISTANCE * 0.70)
            wet_target = wet_beach + nl[sand_visible_mask, None] * 0.035 + nm[sand_visible_mask, None] * 0.045
            sand_col = sand_col * (1.0 - wet_band[:, None] * 0.32) + wet_target * (wet_band[:, None] * 0.32)

            # Très fine bordure de ressac sur le premier contact eau/sable.
            surf_band = np.clip(1.0 - d / max(3.5, 1.0), 0.0, 1.0).astype(np.float32)
            surf_col = water_surf * 0.38 + wet_beach * 0.62
            sand_col = sand_col * (1.0 - surf_band[:, None] * 0.24) + surf_col * (surf_band[:, None] * 0.24)

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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Générateur de satmap optimisé/vectorisé pour DayZ."
    )
    parser.add_argument("--heightmap", default=DEFAULT_HEIGHTMAP_PATH, help="Chemin vers heightmap.asc")
    parser.add_argument("--mask", default=DEFAULT_MASK_PATH, help="Chemin vers mask.png")
    parser.add_argument("--satmap", default=DEFAULT_SATMAP_PATH, help="Chemin vers satmap.png")
    parser.add_argument("--layers", default=DEFAULT_LAYERS_CFG_PATH, help="Chemin vers layers.cfg")
    parser.add_argument("--output-satmap", default=DEFAULT_OUTPUT_SATMAP, help="Image satmap finale")
    parser.add_argument("--output-beach-mask", default=DEFAULT_OUTPUT_BEACH_MASK, help="Masque plage/eau final")
    parser.add_argument("--target-size", type=int, default=DEFAULT_TARGET_SIZE, help="Taille cible carrée, ex: 10240")
    parser.add_argument("--chunk-rows", type=int, default=DEFAULT_CHUNK_ROWS, help="Nombre de lignes traitées par chunk")
    parser.add_argument("--block-size", type=int, default=32, help="Taille des blocs de correction couleur")

    # Utilisation simple via tableau de presets.
    parser.add_argument(
        "--list-sand-presets",
        action="store_true",
        help="Affiche le tableau des presets sand puis quitte"
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

    return parser.parse_args()


def main():
    global CLEAN_CUTOFF_METERS, SEA_LEVEL_METERS
    args = parse_args()
    print(f"Générateur Satmap v{GENERATOR_VERSION}")

    if args.list_sand_presets:
        print_sand_presets_table()
        return

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
    beach_layer_names = parse_layer_name_list(args.beach_layer_names)
    sand_source_layer_names = parse_layer_name_list(args.sand_layer_names)
    land_side_layer_names = parse_layer_name_list(args.land_layer_names)

    if not beach_layer_names:
        raise ValueError("--beach-layer-names doit contenir au moins un nom de layer.")
    if not sand_source_layer_names:
        raise ValueError("--sand-layer-names doit contenir au moins un nom de layer source pour le sable.")

    if args.output_satmap == DEFAULT_OUTPUT_SATMAP and args.output_beach_mask == DEFAULT_OUTPUT_BEACH_MASK:
        output_dir = create_versioned_output_dir(Path("outputs"))
        args.output_satmap = str(output_dir / DEFAULT_OUTPUT_SATMAP)
        args.output_beach_mask = str(output_dir / DEFAULT_OUTPUT_BEACH_MASK)
    else:
        args.output_satmap = resolve_versioned_output_path(args.output_satmap)
        args.output_beach_mask = resolve_versioned_output_path(args.output_beach_mask)

    random.seed(SEED)
    np.random.seed(SEED)

    for p in [args.heightmap, args.mask, args.satmap, args.layers]:
        if not Path(p).exists():
            raise FileNotFoundError(f"Fichier introuvable : {p}")

    target_size = int(args.target_size)
    chunk_rows = int(args.chunk_rows)

    if chunk_rows <= 0:
        raise ValueError("--chunk-rows doit être supérieur à 0.")
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
    print("Textures / layers.cfg :")
    print(f"  layers plage       : {', '.join(sorted(beach_layer_names))}")
    print(f"  layers source sable: {', '.join(sorted(sand_source_layer_names))}")
    if land_side_layer_names:
        print(f"  layers côté terre : {", ".join(sorted(land_side_layer_names))}")
    else:
        print("  layers côté terre : non utilisé (comportement précédent)")
    print("Sorties :")
    print(f"  satmap             : {args.output_satmap}")
    print(f"  beach mask         : {args.output_beach_mask}")

    print("Lecture layers.cfg...")
    color_to_layer, _ = parse_layers_cfg_legend(args.layers)

    print("Chargement heightmap ASC...")
    header, elev_raw = load_asc_with_header(args.heightmap)

    print("Resize heightmap en mètres...")
    valid_mask = np.isfinite(elev_raw)
    fill_value = float(np.nanmin(elev_raw[valid_mask])) if np.any(valid_mask) else 0.0
    elev_fill = np.where(valid_mask, elev_raw, fill_value).astype(np.float32)
    elev_m = resize_float_array(elev_fill, target_size)
    height_norm = normalize_nan_safe(elev_m)

    print("Chargement mask...")
    mask = np.asarray(
        Image.open(args.mask).convert("RGB").resize(
            (target_size, target_size),
            Image.Resampling.NEAREST
        ),
        dtype=np.uint8
    )

    print("Chargement satmap...")
    output = np.asarray(
        Image.open(args.satmap).convert("RGB").resize(
            (target_size, target_size),
            Image.Resampling.LANCZOS
        ),
        dtype=np.float32
    )

    h, w = elev_m.shape

    # =========================================================
    # SLOPE
    # =========================================================
    print("Calcul pente...")
    cellsize = header.get("cellsize", 1.0)
    scale_x = (elev_raw.shape[1] / target_size) * cellsize
    scale_y = (elev_raw.shape[0] / target_size) * cellsize

    gy, gx = np.gradient(elev_m, scale_y, scale_x)
    slope = np.sqrt(gx**2 + gy**2).astype(np.float32)
    slope = normalize_nan_safe(slope)
    del gy, gx
    gc.collect()

    # =========================================================
    # MASK -> CATEGORIES
    # =========================================================
    category_id, hp_sand_exact_mask, land_side_exact_mask = build_category_map(mask, color_to_layer, beach_layer_names, sand_source_layer_names, land_side_layer_names)
    if not np.any(hp_sand_exact_mask):
        available_layers = ", ".join(sorted(set(color_to_layer.values())))
        raise ValueError(
            "Aucune texture source sable trouvée dans le mask/layers.cfg. "
            f"Vérifie --sand-layer-names. Layers disponibles : {available_layers}"
        )
    if land_side_layer_names and not np.any(land_side_exact_mask):
        available_layers = ", ".join(sorted(set(color_to_layer.values())))
        print(
            "ATTENTION : aucune texture côté terre trouvée dans le mask/layers.cfg. "
            "La deuxième passe côté terre fonctionnera comme précédemment. "
            f"Vérifie --land-layer-names si besoin. Layers disponibles : {available_layers}"
        )
        land_side_exact_mask = None
    elif not land_side_layer_names:
        land_side_exact_mask = None

    del mask
    gc.collect()

    print("Extension locale de la zone source sable autorisée...")
    hp_sand_allowed_mask = dilate_mask(hp_sand_exact_mask, radius=8)
    del hp_sand_exact_mask
    gc.collect()

    # =========================================================
    # WATER / CLEAN CUT
    # =========================================================
    print(f"Détection eau / terre : eau forte < {CLEAN_CUTOFF_METERS}m, eau <= {SEA_LEVEL_METERS}m, terre > {land_start_level}m...")
    finite_elev = np.isfinite(elev_m)
    below_zero_mask = finite_elev & (elev_m < CLEAN_CUTOFF_METERS)
    water_mask = finite_elev & (elev_m <= SEA_LEVEL_METERS)

    print("Distance au rivage optimisée...")
    dist_to_water = distance_transform_edt(~water_mask).astype(np.float32)

    print("Création bruit multi-échelle...")
    noise_large, noise_medium, noise_fine = build_multiscale_noise(w, h)

    # =========================================================
    # SATMAP BASE CORRECTION
    # =========================================================
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

    # =========================================================
    # HP_SAND VECTORISÉ
    # =========================================================
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

    # =========================================================
    # APPLICATION VISUELLE
    # =========================================================
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
    )

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
    )

    # =========================================================
    # FINAL MASK OUTPUT
    # =========================================================
    print("Création beach mask...")
    beach_mask_out = np.zeros((h, w), dtype=np.uint8)
    beach_mask_out[water_mask] = 128
    beach_mask_out[sand_edge > 0.05] = 255
    beach_mask_out[below_zero_mask] = 128

    print(f"Sauvegarde beach mask : {args.output_beach_mask}")
    Image.fromarray(beach_mask_out).save(args.output_beach_mask)

    del beach_mask_out, water_mask, below_zero_mask, sand_core, sand_edge
    del elev_m, slope, height_norm, dist_to_water
    if land_side_exact_mask is not None:
        del land_side_exact_mask
    del noise_large, noise_medium, noise_fine
    gc.collect()

    # =========================================================
    # FINALIZE
    # =========================================================
    save_output_chunked(output, args.output_satmap, chunk_rows)

    print("Terminé.")
    print(f"Satmap : {args.output_satmap}")
    print(f"Beach mask : {args.output_beach_mask}")


if __name__ == "__main__":
    main()
