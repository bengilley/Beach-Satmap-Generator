#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
satmap_gui_launcher.py

Interface graphique Tkinter pour lancer le générateur de satmap sans .bat.

Version : boutons de génération uniquement dans l'onglet Lancement.

À placer dans le même dossier que :
  - satmap_generator_optimized_presets.py
  - input/heightmap.asc
  - input/mask.png
  - input/satmap.png
  - input/layers.cfg

Lancement :
  py satmap_gui_launcher.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from tkinter import END, BOTH, DISABLED, NORMAL, filedialog, messagebox, simpledialog
import tkinter as tk
from tkinter import Tk, StringVar, BooleanVar, Text, Canvas
from tkinter.ttk import Button, Checkbutton, Combobox, Entry, Frame, Label, LabelFrame, Notebook, Progressbar, Scrollbar, Separator, Spinbox, Style

APP_TITLE = "Beach Satmap Generator"
APP_VERSION = "1.7.7"
WINDOW_START_SIZE = "1200x850"
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 650
GENERATOR_EXPECTED_VERSION = "1.3.4"
CUSTOM_PRESETS_FILE = "custom_profiles.json"
LAUNCHER_SETTINGS_FILE = "launcher_settings.json"
GENERATOR_NAME = "satmap_generator_optimized_presets.py"
INFO_ICON_FILE = "info.png"

# Palette visuelle de l'interface. Logique et génération inchangées.
APP_BG = "#f4f7fb"
CARD_BG = "#ffffff"
HEADER_BG = "#eef4ff"
FOOTER_BG = "#ffffff"
TEXT_COLOR = "#1f2937"
MUTED_COLOR = "#667085"
BORDER_COLOR = "#d7dee9"
ACCENT_COLOR = "#2563eb"
ACCENT_DARK = "#1d4ed8"
DANGER_COLOR = "#b42318"
DANGER_DARK = "#912018"
SUCCESS_COLOR = "#027a48"

DEFAULT_INPUT_DIR = "input"
DEFAULT_OUTPUT_DIR = "outputs"

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")
LOSSLESS_MASK_EXTENSIONS = (".png", ".bmp", ".tif", ".tiff")
LOSSY_MASK_EXTENSIONS = (".jpg", ".jpeg")
IMAGE_FILETYPES = [
    ("Images", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
    ("PNG", "*.png"),
    ("JPEG", "*.jpg *.jpeg"),
    ("BMP", "*.bmp"),
    ("TIFF", "*.tif *.tiff"),
    ("Tous les fichiers", "*.*"),
]
SCRIPT_FILETYPES = [("Scripts Python", "*.py *.pyw"), ("Tous les fichiers", "*.*")]
ASC_FILETYPES = [("Heightmap ASC", "*.asc"), ("Tous les fichiers", "*.*")]
CFG_FILETYPES = [("Layers CFG", "*.cfg"), ("Tous les fichiers", "*.*")]

SAND_COLOR_PRESET_CHOICES = [
    "belle_ile",
    "atlantic_light",
    "golden",
    "pale_white",
    "grey_shell",
    "dark_volcanic",
    "red_ochre",
    "custom",
]

SAND_COLOR_PRESETS = {
    "belle_ile": {
        "dry": "222,204,178",
        "wet": "190,168,145",
        "shell": "208,196,182",
        "wet_beach": "181,156,128",
        "seabed": "160,120,90",
    },
    "atlantic_light": {
        "dry": "230,214,184",
        "wet": "196,176,150",
        "shell": "220,210,196",
        "wet_beach": "188,164,134",
        "seabed": "170,132,98",
    },
    "golden": {
        "dry": "226,190,126",
        "wet": "176,140,95",
        "shell": "218,200,164",
        "wet_beach": "166,132,92",
        "seabed": "152,112,72",
    },
    "pale_white": {
        "dry": "238,230,204",
        "wet": "205,194,170",
        "shell": "236,230,218",
        "wet_beach": "196,184,160",
        "seabed": "176,160,130",
    },
    "grey_shell": {
        "dry": "200,196,184",
        "wet": "158,154,145",
        "shell": "220,218,210",
        "wet_beach": "150,145,132",
        "seabed": "128,120,108",
    },
    "dark_volcanic": {
        "dry": "112,105,96",
        "wet": "70,68,66",
        "shell": "150,145,135",
        "wet_beach": "82,76,70",
        "seabed": "74,68,62",
    },
    "red_ochre": {
        "dry": "196,128,82",
        "wet": "132,82,58",
        "shell": "205,176,150",
        "wet_beach": "144,92,62",
        "seabed": "122,76,52",
    },
}



WATER_COLOR_PRESET_CHOICES = [
    "atlantic_belle_ile",
    "atlantic_open_ocean",
    "atlantic_grey_coast",
    "tropical_lagoon",
    "caribbean_turquoise",
    "maldives_atoll",
    "coral_reef_shallow",
    "mediterranean_blue",
    "aegean_clear",
    "adriatic_clear",
    "red_sea_clear",
    "pacific_deep",
    "indian_ocean",
    "cold_ocean",
    "north_sea_grey",
    "baltic_green",
    "arctic_glacial",
    "fjord_dark",
    "deep_ocean",
    "black_sea_deep",
    "muddy_water",
    "river_delta_silty",
    "mangrove_lagoon",
    "amazon_brown",
    "great_lakes_fresh",
    "alpine_lake",
    "glacial_lake_milky",
    "green_algae_lake",
    "volcanic_crater_lake",
    "salt_lake_pale",
    "dark_stormy",
    "custom",
]

WATER_COLOR_PRESETS = {
    "atlantic_belle_ile": {
        "deep": "58,88,122",
        "mid": "70,112,142",
        "shallow": "93,149,156",
        "lagoon": "118,181,174",
        "surf": "156,202,190",
        "seabed": "160,120,90",
    },
    "atlantic_open_ocean": {
        "deep": "28,72,112",
        "mid": "45,100,135",
        "shallow": "76,135,150",
        "lagoon": "105,165,160",
        "surf": "165,205,195",
        "seabed": "135,115,90",
    },
    "atlantic_grey_coast": {
        "deep": "48,70,88",
        "mid": "72,96,108",
        "shallow": "105,130,125",
        "lagoon": "132,154,145",
        "surf": "178,190,178",
        "seabed": "125,115,100",
    },
    "tropical_lagoon": {
        "deep": "20,95,145",
        "mid": "35,165,185",
        "shallow": "95,220,210",
        "lagoon": "130,235,220",
        "surf": "220,245,230",
        "seabed": "210,190,130",
    },
    "caribbean_turquoise": {
        "deep": "0,87,143",
        "mid": "18,156,188",
        "shallow": "72,218,220",
        "lagoon": "125,238,225",
        "surf": "230,248,238",
        "seabed": "218,202,145",
    },
    "maldives_atoll": {
        "deep": "5,76,132",
        "mid": "25,150,190",
        "shallow": "85,225,220",
        "lagoon": "155,242,225",
        "surf": "235,250,238",
        "seabed": "225,207,150",
    },
    "coral_reef_shallow": {
        "deep": "16,80,138",
        "mid": "30,145,170",
        "shallow": "95,205,190",
        "lagoon": "150,225,205",
        "surf": "225,245,225",
        "seabed": "190,165,120",
    },
    "mediterranean_blue": {
        "deep": "25,75,138",
        "mid": "42,110,165",
        "shallow": "70,155,185",
        "lagoon": "105,190,195",
        "surf": "180,220,215",
        "seabed": "150,130,95",
    },
    "aegean_clear": {
        "deep": "18,80,150",
        "mid": "35,125,180",
        "shallow": "75,175,205",
        "lagoon": "110,205,210",
        "surf": "195,230,225",
        "seabed": "165,145,105",
    },
    "adriatic_clear": {
        "deep": "35,85,120",
        "mid": "55,125,150",
        "shallow": "90,170,175",
        "lagoon": "130,200,190",
        "surf": "200,225,210",
        "seabed": "155,140,110",
    },
    "red_sea_clear": {
        "deep": "15,72,132",
        "mid": "28,130,170",
        "shallow": "78,190,195",
        "lagoon": "120,220,205",
        "surf": "220,240,220",
        "seabed": "190,165,115",
    },
    "pacific_deep": {
        "deep": "12,48,95",
        "mid": "30,80,130",
        "shallow": "62,125,155",
        "lagoon": "90,160,165",
        "surf": "160,210,200",
        "seabed": "105,95,85",
    },
    "indian_ocean": {
        "deep": "10,70,125",
        "mid": "28,125,160",
        "shallow": "70,185,190",
        "lagoon": "115,215,200",
        "surf": "220,240,225",
        "seabed": "190,175,125",
    },
    "cold_ocean": {
        "deep": "35,65,85",
        "mid": "55,95,115",
        "shallow": "90,135,140",
        "lagoon": "105,155,155",
        "surf": "180,205,205",
        "seabed": "120,115,105",
    },
    "north_sea_grey": {
        "deep": "45,65,78",
        "mid": "65,88,95",
        "shallow": "92,118,112",
        "lagoon": "120,140,130",
        "surf": "170,185,175",
        "seabed": "115,105,88",
    },
    "baltic_green": {
        "deep": "36,70,72",
        "mid": "58,100,88",
        "shallow": "90,130,100",
        "lagoon": "125,155,115",
        "surf": "178,195,165",
        "seabed": "115,105,75",
    },
    "arctic_glacial": {
        "deep": "25,70,95",
        "mid": "55,115,135",
        "shallow": "100,165,170",
        "lagoon": "145,205,200",
        "surf": "220,238,230",
        "seabed": "130,130,120",
    },
    "fjord_dark": {
        "deep": "15,42,58",
        "mid": "28,65,78",
        "shallow": "55,95,100",
        "lagoon": "85,125,120",
        "surf": "150,175,165",
        "seabed": "78,74,68",
    },
    "deep_ocean": {
        "deep": "18,50,82",
        "mid": "35,82,116",
        "shallow": "70,130,150",
        "lagoon": "95,165,165",
        "surf": "150,205,195",
        "seabed": "115,105,88",
    },
    "black_sea_deep": {
        "deep": "18,43,70",
        "mid": "32,70,90",
        "shallow": "62,105,112",
        "lagoon": "88,130,125",
        "surf": "150,175,165",
        "seabed": "90,85,72",
    },
    "muddy_water": {
        "deep": "70,85,75",
        "mid": "100,110,85",
        "shallow": "135,130,95",
        "lagoon": "155,145,105",
        "surf": "190,185,150",
        "seabed": "125,105,70",
    },
    "river_delta_silty": {
        "deep": "78,88,70",
        "mid": "112,112,78",
        "shallow": "148,136,90",
        "lagoon": "170,150,102",
        "surf": "200,190,145",
        "seabed": "135,110,70",
    },
    "mangrove_lagoon": {
        "deep": "38,72,58",
        "mid": "70,105,72",
        "shallow": "105,132,82",
        "lagoon": "135,155,95",
        "surf": "180,190,145",
        "seabed": "105,85,55",
    },
    "amazon_brown": {
        "deep": "80,62,42",
        "mid": "120,88,55",
        "shallow": "155,112,70",
        "lagoon": "180,135,90",
        "surf": "210,185,145",
        "seabed": "110,82,52",
    },
    "great_lakes_fresh": {
        "deep": "32,75,98",
        "mid": "55,110,125",
        "shallow": "90,150,145",
        "lagoon": "125,175,160",
        "surf": "185,210,195",
        "seabed": "120,115,95",
    },
    "alpine_lake": {
        "deep": "22,76,110",
        "mid": "48,125,145",
        "shallow": "95,175,170",
        "lagoon": "135,205,190",
        "surf": "210,235,220",
        "seabed": "120,125,110",
    },
    "glacial_lake_milky": {
        "deep": "55,98,120",
        "mid": "85,135,150",
        "shallow": "130,180,180",
        "lagoon": "170,210,200",
        "surf": "225,240,230",
        "seabed": "150,150,135",
    },
    "green_algae_lake": {
        "deep": "35,70,45",
        "mid": "65,105,55",
        "shallow": "105,140,65",
        "lagoon": "140,165,80",
        "surf": "185,195,135",
        "seabed": "90,85,55",
    },
    "volcanic_crater_lake": {
        "deep": "12,55,72",
        "mid": "25,92,95",
        "shallow": "65,135,115",
        "lagoon": "95,170,135",
        "surf": "165,210,180",
        "seabed": "60,58,55",
    },
    "salt_lake_pale": {
        "deep": "88,130,140",
        "mid": "125,170,165",
        "shallow": "170,210,190",
        "lagoon": "205,230,205",
        "surf": "240,245,225",
        "seabed": "220,205,165",
    },
    "dark_stormy": {
        "deep": "25,45,60",
        "mid": "40,70,85",
        "shallow": "65,95,100",
        "lagoon": "80,115,112",
        "surf": "145,165,160",
        "seabed": "85,80,70",
    },
}

LANGUAGE_OPTIONS = {
    "🇫🇷 Français": "fr",
    "🇬🇧 English": "en",
    "🇷🇺 Русский": "ru",
}
LANGUAGE_LABEL_BY_CODE = {code: label for label, code in LANGUAGE_OPTIONS.items()}

UI_TRANSLATIONS = {
    "fr": {},
    "en": {
        "Langue": "Language",
        "Beach Satmap Generator": "Beach Satmap Generator",
        "1. Fichiers": "1. Files",
        "2. Profils": "2. Profiles",
        "3. Technique": "3. Technical",
        "4. Lancement": "4. Run",
        "Fichiers utilisés par le script": "Files used by the script",
        "Script générateur": "Generator script",
        "Heightmap ASC": "Heightmap ASC",
        "Mask image": "Mask image",
        "Satmap image": "Satmap image",
        "Layers CFG": "Layers CFG",
        "Parcourir": "Browse",
        "Textures DayZ à reconnaître": "Textures used in layers.cfg",
        "Type": "Type",
        "Texture DayZ standard": "Vanilla DayZ texture",
        "Texture mod / custom": "Custom / mod texture",
        "Texture déjà plage": "Existing beach / coastline",
        "Texture sable à agrandir": "Source sand to extend",
        "Texture terre à mélanger": "Target inland texture",
        "ex vanilla : sa_beach | custom : hp_beach,my_beach": "ex vanilla: sa_beach | custom: hp_beach,my_beach",
        "ex vanilla : cp_gravel | custom : hp_sand,my_sand": "ex vanilla: cp_gravel | custom: hp_sand,my_sand",
        "optionnel | ex : cp_grass ou custom_grass": "optional | ex: cp_grass or custom_grass",
        "Choisis les textures que le script doit reconnaître dans layers.cfg. Les textures standard et custom sont combinées automatiquement. Plusieurs customs peuvent être séparées par des virgules.": "Choose a vanilla DayZ texture from the list, then add one or more custom textures manually if needed. Both are combined automatically. Custom names can be separated with commas. Empty inland texture = previous behavior.",
        "Actions rapides": "Quick actions",
        "Créer input / outputs": "Create input / outputs",
        "Installer dépendances": "Install dependencies",
        "Ouvrir dossier du script": "Open script folder",
        "Réinitialiser chemins": "Reset paths",
        "Fichiers attendus par défaut : input/heightmap.asc, input/mask.png, input/satmap.png, input/layers.cfg": "Default expected files: input/heightmap.asc, input/mask.png, input/satmap.png, input/layers.cfg. Supported image formats for mask, satmap and textures: PNG, JPG, JPEG, BMP, TIFF.",
        "Plage : taille et pente": "Coastal zone profile",
        "Eau : niveaux d'altitude": "Altitude thresholds profile",
        "Fusion sable → terre": "Inland transition profile",
        "Largeur plage max": "Sand distance px",
        "Pente autorisée": "Max slope",
        "Hauteur plage max": "Max height m",
        "Eau profonde sous": "Strong water below m",
        "Limite eau": "Water up to m",
        "Terre à partir de": "Land from m",
        "Largeur fusion terre": "Retouch distance px",
        "Force fusion terre": "Retouch strength",
        "Réglages rapides recommandés": "Recommended quick settings",
        "Recommandés": "Recommended",
        "Naturel équilibré": "Balanced natural",
        "Littoral bas": "Low coastline",
        "Grande plage propre": "Large clean beach",
        "Bord net léger": "Light sharp edge",
        "Plage large douce": "Soft large beach",
        "Extension forte": "Strong extension",
        "Profils personnalisés sauvegardés": "Saved custom profiles",
        "Charger": "Load",
        "Sauvegarder réglage actuel": "Save current settings",
        "Supprimer": "Delete",
        "Sauvegarde locale : custom_profiles.json": "Local save: custom_profiles.json",
        "Résumé des profils": "Full profile details",
        "Réglages moteur": "Technical settings",
        "Résolution finale": "Final size",
        "Mémoire / vitesse": "Chunk rows",
        "Taille variations couleur": "Color block size",
        "Ouvrir le dossier outputs à la fin": "Open outputs folder when finished",
        "Mémoire / vitesse - observations RAM": "Chunk rows - RAM observations",
        "Observation 10240 x 10240 : le script seul monte à environ 8.5 Go RAM au pic.": "Observation 10240 x 10240: the script alone peaks at about 8.5 GB RAM.",
        "Le chunk-rows change surtout la vitesse et la stabilité.": "Chunk rows mainly changes speed and stability.",
        "512 / 1024 : très sûr, utile pour petites configurations, mais plus lent.": "512 / 1024: very safe, useful for small configs, but slower.",
        "2048 : équilibré, stable sur la plupart des PC récents.": "2048: balanced, stable on most recent PCs.",
        "4096 : recommandé pour 32/64 Go RAM, bon compromis vitesse/stabilité.": "4096: recommended for 32/64 GB RAM, good speed/stability compromise.",
        "8192 : mode performance, à utiliser si le PC reste stable.": "8192: performance mode, use if the PC stays stable.",
        "Windows peut afficher plus haut à cause du cache système et des logiciels ouverts.": "Windows may show higher usage because of system cache and open software.",
        "Informations techniques": "Technical information",
        "Commande générée": "Generated command",
        "Actualiser la commande": "Refresh command",
        "Actions de génération": "Generation actions",
        "Lancer la génération": "Start generation",
        "Arrêter": "Stop",
        "Journal": "Log",
        "Prêt": "Ready",
        "Vérification": "Check",
        "Fichiers manquants": "Missing files",
        "Fichiers manquants ou chemins invalides :\n\n": "Missing files or invalid paths:\n\n",
        "Tous les fichiers obligatoires sont présents.": "All required files are present.",
        "ATTENTION : fichier obligatoire manquant ou invalide - ": "WARNING: required file missing or invalid - ",
        "Génération en cours...": "Generation running...",
        "Génération terminée.": "Generation finished.",
        "La génération a échoué.": "Generation failed.",
        "Démarrage": "Starting",
        "Sauvegarder profil": "Save profile",
        "Nom du profil personnalisé :": "Custom profile name:",
        "Remplacer": "Replace",
        "Le profil '{name}' existe déjà. Le remplacer ?": "Profile '{name}' already exists. Replace it?",
        "Profil": "Profile",
        "Aucun profil personnalisé sélectionné.": "No custom profile selected.",
        "Supprimer le profil personnalisé '{name}' ?": "Delete custom profile '{name}'?",
        "Profil personnalisé sauvegardé : {name}": "Custom profile saved: {name}",
        "Profil personnalisé chargé : {name}": "Custom profile loaded: {name}",
        "Profil personnalisé supprimé : {name}": "Custom profile deleted: {name}",
        "Commande invalide : {error}": "Invalid command: {error}",
        "Script introuvable : {path}": "Generator script not found: {path}",
        "Fichier obligatoire manquant ou invalide": "Required file missing or invalid",
        "Dossier output non détecté automatiquement": "Output folder not detected automatically",
        "non disponible": "not available",
        "non utilisé": "not used",
        "liste vanilla DayZ + champ custom manuel": "vanilla DayZ list + manual custom field",
        "Couleurs du sable": "Satmap sand color",
        "Type de sable": "Color preset",
        "Intensité sable": "Color strength",
        "Choisis un type de sable ou règle les couleurs à la main. Format accepté : R,G,B ou #RRGGBB.": "Use a preset to quickly match different sand types. In custom mode, enter RGB values as R,G,B or #RRGGBB.",
        "Sable sec": "Dry sand RGB",
        "Sable mouillé": "Wet sand RGB",
        "Sable clair / coquillages": "Shell variation RGB",
        "Bord mouillé": "Wet beach edge RGB",
        "Fond sableux": "Seabed RGB",
        "Texture sable": "Texture image",
        "Intensité texture": "Texture strength",
        "Taille texture": "Scale",
        "Optionnel : ajoute du grain visuel au sable sans modifier la zone générée.": "Optional: use a texture image (pebbles, fine sand, dark sand, etc.) to add visual detail to the sand color without changing the generator logic.",
        "Couleurs de l'eau": "Satmap water color",
        "Type d'eau": "Water preset",
        "Intensité eau": "Water strength",
        "Choisis un type d'eau ou règle le dégradé à la main : mer Atlantique, lagon, lac, eau sombre, etc.": "Use a preset to adapt the water gradient to real-world environments: Atlantic, Mediterranean, tropical lagoon, cold sea, fjord, alpine lake, glacial lake, muddy delta, mangrove, dark water, or custom.",
        "Eau profonde": "Deep water RGB",
        "Eau intermédiaire": "Mid water RGB",
        "Eau peu profonde": "Shallow water RGB",
        "Eau très claire": "Lagoon RGB",
        "Écume / ressac": "Surf / foam RGB",
        "Fond sous l'eau": "Water seabed RGB",
        "Texture de l'eau": "Satmap water texture",
        "Texture eau": "Water texture image",
        "Intensité texture eau": "Water texture strength",
        "Taille texture eau": "Water texture scale",
        "Optionnel : ajoute des vagues, du bruit ou des reflets sans changer les zones d'eau.": "Optional: use a water texture image (waves, noise, reflections, foam, etc.) to add visual detail to the water gradient.",
        "RAPPORT_GENERATION_COMPLET.md": "COMPLETE_GENERATION_REPORT.md",
    },
    "ru": {
        "Langue": "Язык",
        "Beach Satmap Generator": "Генератор Satmap пляжей",
        "1. Fichiers": "1. Файлы",
        "2. Profils": "2. Профили",
        "3. Technique": "3. Техника",
        "4. Lancement": "4. Запуск",
        "Fichiers utilisés par le script": "Файлы, используемые скриптом",
        "Script générateur": "Скрипт генератора",
        "Heightmap ASC": "Heightmap ASC",
        "Mask image": "Mask image",
        "Satmap image": "Satmap image",
        "Layers CFG": "Layers CFG",
        "Parcourir": "Обзор",
        "Textures DayZ à reconnaître": "Текстуры из layers.cfg",
        "Type": "Тип",
        "Texture DayZ standard": "Vanilla-текстура DayZ",
        "Texture mod / custom": "Custom / mod текстура",
        "Texture déjà plage": "Существующий пляж / берег",
        "Texture sable à agrandir": "Исходный песок для расширения",
        "Texture terre à mélanger": "Целевая земля внутри",
        "ex vanilla : sa_beach | custom : hp_beach,my_beach": "пример vanilla: sa_beach | custom: hp_beach,my_beach",
        "ex vanilla : cp_gravel | custom : hp_sand,my_sand": "пример vanilla: cp_gravel | custom: hp_sand,my_sand",
        "optionnel | ex : cp_grass ou custom_grass": "опционально | пример: cp_grass или custom_grass",
        "Choisis les textures que le script doit reconnaître dans layers.cfg. Les textures standard et custom sont combinées automatiquement. Plusieurs customs peuvent être séparées par des virgules.": "Выберите vanilla-текстуру DayZ из списка, затем при необходимости добавьте одну или несколько custom-текстур вручную. Они будут объединены автоматически. Custom-текстуры можно разделять запятыми. Пустая внутренняя земля = прежнее поведение.",
        "Actions rapides": "Быстрые действия",
        "Créer input / outputs": "Создать input / outputs",
        "Installer dépendances": "Установить зависимости",
        "Ouvrir dossier du script": "Открыть папку скрипта",
        "Réinitialiser chemins": "Сбросить пути",
        "Fichiers attendus par défaut : input/heightmap.asc, input/mask.png, input/satmap.png, input/layers.cfg": "Файлы по умолчанию: input/heightmap.asc, input/mask.png, input/satmap.png, input/layers.cfg. Поддерживаемые форматы изображений для mask, satmap и текстур: PNG, JPG, JPEG, BMP, TIFF.",
        "Plage : taille et pente": "Профиль береговой зоны",
        "Eau : niveaux d'altitude": "Профиль высотных порогов",
        "Fusion sable → terre": "Профиль перехода к суше",
        "Largeur plage max": "Дистанция песка px",
        "Pente autorisée": "Макс. уклон",
        "Hauteur plage max": "Макс. высота м",
        "Eau profonde sous": "Сильная вода ниже м",
        "Limite eau": "Вода до м",
        "Terre à partir de": "Суша от м",
        "Largeur fusion terre": "Дистанция ретуши px",
        "Force fusion terre": "Сила ретуши",
        "Réglages rapides recommandés": "Рекомендуемые быстрые настройки",
        "Recommandés": "Рекомендуемые",
        "Naturel équilibré": "Естественный баланс",
        "Littoral bas": "Низкий берег",
        "Grande plage propre": "Большой чистый пляж",
        "Bord net léger": "Лёгкий чёткий край",
        "Plage large douce": "Мягкий широкий пляж",
        "Extension forte": "Сильное расширение",
        "Profils personnalisés sauvegardés": "Сохранённые пользовательские профили",
        "Charger": "Загрузить",
        "Sauvegarder réglage actuel": "Сохранить текущие настройки",
        "Supprimer": "Удалить",
        "Sauvegarde locale : custom_profiles.json": "Локально: custom_profiles.json",
        "Résumé des profils": "Полное описание профилей",
        "Réglages moteur": "Технические параметры",
        "Résolution finale": "Финальный размер",
        "Mémoire / vitesse": "Строк на chunk",
        "Taille variations couleur": "Размер цветовых блоков",
        "Ouvrir le dossier outputs à la fin": "Открыть outputs после завершения",
        "Mémoire / vitesse - observations RAM": "Строки chunk — наблюдения RAM",
        "Observation 10240 x 10240 : le script seul monte à environ 8.5 Go RAM au pic.": "Наблюдение 10240 x 10240: сам скрипт достигает около 8.5 ГБ RAM на пике.",
        "Le chunk-rows change surtout la vitesse et la stabilité.": "Chunk-rows в основном влияет на скорость и стабильность.",
        "512 / 1024 : très sûr, utile pour petites configurations, mais plus lent.": "512 / 1024: очень безопасно для слабых ПК, но медленнее.",
        "2048 : équilibré, stable sur la plupart des PC récents.": "2048: сбалансировано и стабильно на большинстве современных ПК.",
        "4096 : recommandé pour 32/64 Go RAM, bon compromis vitesse/stabilité.": "4096: рекомендуется для 32/64 ГБ RAM, хороший компромисс скорость/стабильность.",
        "8192 : mode performance, à utiliser si le PC reste stable.": "8192: режим производительности, использовать если ПК стабилен.",
        "Windows peut afficher plus haut à cause du cache système et des logiciels ouverts.": "Windows может показывать больше из-за системного кэша и открытых программ.",
        "Informations techniques": "Техническая информация",
        "Commande générée": "Сгенерированная команда",
        "Actualiser la commande": "Обновить команду",
        "Actions de génération": "Действия генерации",
        "Lancer la génération": "Запустить генерацию",
        "Arrêter": "Остановить",
        "Journal": "Журнал",
        "Prêt": "Готово",
        "Vérification": "Проверка",
        "Fichiers manquants": "Отсутствующие файлы",
        "Fichiers manquants ou chemins invalides :\n\n": "Отсутствующие файлы или неверные пути:\n\n",
        "Tous les fichiers obligatoires sont présents.": "Все обязательные файлы присутствуют.",
        "ATTENTION : fichier obligatoire manquant ou invalide - ": "ВНИМАНИЕ: обязательный файл отсутствует или неверен - ",
        "Génération en cours...": "Генерация выполняется...",
        "Génération terminée.": "Генерация завершена.",
        "La génération a échoué.": "Генерация завершилась ошибкой.",
        "Démarrage": "Запуск",
        "Sauvegarder profil": "Сохранить профиль",
        "Nom du profil personnalisé :": "Имя пользовательского профиля:",
        "Remplacer": "Заменить",
        "Le profil '{name}' existe déjà. Le remplacer ?": "Профиль '{name}' уже существует. Заменить?",
        "Profil": "Профиль",
        "Aucun profil personnalisé sélectionné.": "Пользовательский профиль не выбран.",
        "Supprimer le profil personnalisé '{name}' ?": "Удалить пользовательский профиль '{name}'?",
        "Profil personnalisé sauvegardé : {name}": "Пользовательский профиль сохранён: {name}",
        "Profil personnalisé chargé : {name}": "Пользовательский профиль загружен: {name}",
        "Profil personnalisé supprimé : {name}": "Пользовательский профиль удалён: {name}",
        "Commande invalide : {error}": "Неверная команда: {error}",
        "Script introuvable : {path}": "Скрипт генератора не найден: {path}",
        "Fichier obligatoire manquant ou invalide": "Обязательный файл отсутствует или неверен",
        "Dossier output non détecté automatiquement": "Папка output не определена автоматически",
        "non disponible": "недоступно",
        "non utilisé": "не используется",
        "liste vanilla DayZ + champ custom manuel": "список vanilla DayZ + ручное custom-поле",
        "Couleurs du sable": "Цвет песка satmap",
        "Type de sable": "Пресет цвета",
        "Intensité sable": "Сила цвета",
        "Choisis un type de sable ou règle les couleurs à la main. Format accepté : R,G,B ou #RRGGBB.": "Используйте пресет для быстрого подбора типа песка. В режиме custom укажите RGB в формате R,G,B или #RRGGBB.",
        "Sable sec": "Сухой песок RGB",
        "Sable mouillé": "Влажный песок RGB",
        "Sable clair / coquillages": "Вариация ракушек RGB",
        "Bord mouillé": "Влажная кромка RGB",
        "Fond sableux": "Морское дно RGB",
        "Texture sable": "Изображение текстуры",
        "Intensité texture": "Сила текстуры",
        "Taille texture": "Масштаб",
        "Optionnel : ajoute du grain visuel au sable sans modifier la zone générée.": "Опционально: используйте изображение текстуры (галька, мелкий песок, тёмный песок и т.д.), чтобы добавить визуальные детали к цвету песка без изменения логики генератора.",
        "Couleurs de l'eau": "Цвет воды satmap",
        "Type d'eau": "Пресет воды",
        "Intensité eau": "Сила воды",
        "Choisis un type d'eau ou règle le dégradé à la main : mer Atlantique, lagon, lac, eau sombre, etc.": "Используйте пресет, чтобы адаптировать градиент воды под реальные среды: Атлантика, Средиземное море, тропическая лагуна, холодное море, фьорд, альпийское озеро, ледниковое озеро, мутная дельта, мангры, тёмная вода или custom.",
        "Eau profonde": "Глубокая вода RGB",
        "Eau intermédiaire": "Средняя вода RGB",
        "Eau peu profonde": "Мелководье RGB",
        "Eau très claire": "Лагуна RGB",
        "Écume / ressac": "Прибой / пена RGB",
        "Fond sous l'eau": "Дно под водой RGB",
        "Texture de l'eau": "Текстура воды satmap",
        "Texture eau": "Изображение текстуры воды",
        "Intensité texture eau": "Сила текстуры воды",
        "Taille texture eau": "Масштаб текстуры воды",
        "Optionnel : ajoute des vagues, du bruit ou des reflets sans changer les zones d'eau.": "Опционально: используйте изображение текстуры воды (волны, шум, отражения, пена и т.д.), чтобы добавить визуальные детали к градиенту воды.",
        "RAPPORT_GENERATION_COMPLET.md": "ПОЛНЫЙ_ОТЧЕТ_ГЕНЕРАЦИИ.md",
    },
}


# Compléments i18n utilisés par les textes dynamiques.
UI_TRANSLATIONS["en"].update({
    "Détail": "Detail",
    "Largeur plage max": "Sand distance",
    "Hauteur plage max": "Max height",
    "Eau profonde sous": "Strong water below",
    "Limite eau": "Water up to",
    "Terre / plage dès": "Land / beach from",
    "Distance retouche": "Retouch distance",
    "Force fusion terre": "Retouch strength",
})
UI_TRANSLATIONS["ru"].update({
    "Détail": "Детали",
    "Largeur plage max": "Дистанция песка",
    "Hauteur plage max": "Макс. высота",
    "Eau profonde sous": "Сильная вода ниже",
    "Limite eau": "Вода до",
    "Terre / plage dès": "Суша / пляж от",
    "Distance retouche": "Дистанция ретуши",
    "Force fusion terre": "Сила ретуши",
})
UI_TRANSLATIONS["en"].update({
    "PLAGE : TAILLE ET PENTE": "COASTAL ZONE PROFILE",
    "EAU : NIVEAUX D'ALTITUDE": "ALTITUDE THRESHOLD PROFILE",
    "FUSION SABLE → TERRE": "INLAND TRANSITION PROFILE",
    "distance": "distance",
    "pente": "slope",
    "hauteur": "height",
    "eau forte": "strong water",
    "eau": "water",
    "terre": "land",
    "force": "strength",
})
UI_TRANSLATIONS["ru"].update({
    "PLAGE : TAILLE ET PENTE": "ПРОФИЛЬ БЕРЕГОВОЙ ЗОНЫ",
    "EAU : NIVEAUX D'ALTITUDE": "ПРОФИЛЬ ВЫСОТНЫХ ПОРОГОВ",
    "FUSION SABLE → TERRE": "ПРОФИЛЬ ПЕРЕХОДА К СУШЕ",
    "distance": "дистанция",
    "pente": "уклон",
    "hauteur": "высота",
    "eau forte": "сильная вода",
    "eau": "вода",
    "terre": "суша",
    "force": "сила",
})

UI_TRANSLATIONS["en"].update({
    "Date de génération": "Generation date",
    "Durée totale": "Total duration",
    "Version launcher": "Launcher version",
    "Version générateur attendue": "Expected generator version",
    "Langue du rapport": "Report language",
    "Dossier de sortie": "Output folder",
    "Fichiers source": "Source files",
    "Mode textures": "Texture mode",
    "Profil": "Profile",
    "Description": "Description",
    "Réglages moteur": "Technical settings",
    "Commande utilisée": "Command used",
    "Fichiers générés attendus": "Expected generated files",
})
UI_TRANSLATIONS["ru"].update({
    "Date de génération": "Дата генерации",
    "Durée totale": "Общая длительность",
    "Version launcher": "Версия launcher",
    "Version générateur attendue": "Ожидаемая версия генератора",
    "Langue du rapport": "Язык отчёта",
    "Dossier de sortie": "Папка вывода",
    "Fichiers source": "Исходные файлы",
    "Mode textures": "Режим текстур",
    "Profil": "Профиль",
    "Description": "Описание",
    "Réglages moteur": "Технические параметры",
    "Commande utilisée": "Использованная команда",
    "Fichiers générés attendus": "Ожидаемые созданные файлы",
})

UI_TRANSLATIONS["en"].update({
    "Aucun dossier output_Vx détecté pour écrire le rapport complet.": "No output_Vx folder detected to write the complete report.",
    "Rapport complet créé": "Complete report created",
    "Déjà en cours": "Already running",
    "Une génération est déjà en cours.": "A generation is already running.",
})
UI_TRANSLATIONS["ru"].update({
    "Aucun dossier output_Vx détecté pour écrire le rapport complet.": "Папка output_Vx не найдена для записи полного отчёта.",
    "Rapport complet créé": "Полный отчёт создан",
    "Déjà en cours": "Уже выполняется",
    "Une génération est déjà en cours.": "Генерация уже выполняется.",
})

UI_TRANSLATIONS["en"].update({
    "Lecture des couches": "Reading layers",
    "Chargement heightmap": "Loading heightmap",
    "Redimensionnement heightmap": "Resizing heightmap",
    "Chargement masque": "Loading mask",
    "Chargement satmap": "Loading satmap",
    "Calcul de pente": "Calculating slope",
    "Extension zone sable": "Extending sand zone",
    "Détection niveaux eau": "Detecting water levels",
    "Calcul distance au rivage": "Calculating shore distance",
    "Création du bruit": "Creating noise",
    "Construction des catégories": "Building categories",
    "Correction satmap": "Satmap correction",
    "Application eau / plage": "Applying water / beach",
    "Application côté terre": "Applying inland side",
    "Génération rivage": "Generating shoreline",
    "Création beach mask": "Creating beach mask",
    "Sauvegarde beach mask": "Saving beach mask",
    "Sauvegarde satmap": "Saving satmap",
    "Terminé": "Done",
})
UI_TRANSLATIONS["ru"].update({
    "Lecture des couches": "Чтение слоёв",
    "Chargement heightmap": "Загрузка heightmap",
    "Redimensionnement heightmap": "Изменение размера heightmap",
    "Chargement masque": "Загрузка mask",
    "Chargement satmap": "Загрузка satmap",
    "Calcul de pente": "Расчёт уклона",
    "Extension zone sable": "Расширение зоны песка",
    "Détection niveaux eau": "Определение уровней воды",
    "Calcul distance au rivage": "Расчёт дистанции до берега",
    "Création du bruit": "Создание шума",
    "Construction des catégories": "Построение категорий",
    "Correction satmap": "Коррекция satmap",
    "Application eau / plage": "Применение воды / пляжа",
    "Application côté terre": "Применение со стороны суши",
    "Génération rivage": "Генерация берега",
    "Création beach mask": "Создание beach mask",
    "Sauvegarde beach mask": "Сохранение beach mask",
    "Sauvegarde satmap": "Сохранение satmap",
    "Terminé": "Готово",
})


UI_TRANSLATIONS["en"].update({
    "Vérifier textures layers.cfg": "Check layers.cfg textures",
    "Chemins réinitialisés : tous les chemins de fichiers sont maintenant vides.": "Paths reset: all file paths are now empty.",
    "Chemin layers.cfg vide. Sélectionne d'abord un fichier layers.cfg.": "layers.cfg path is empty. Select a layers.cfg file first.",
    "Vérification textures impossible : chemin layers.cfg vide.": "Texture check impossible: layers.cfg path is empty.",
    "Fichier layers.cfg introuvable ou invalide.": "layers.cfg file not found or invalid.",
    "Erreur lecture layers.cfg : {error}": "Error reading layers.cfg: {error}",
    "INFO : vide, option non utilisée.": "INFO: empty, option not used.",
    "vide, option non utilisée.": "empty, option not used.",
    "ERROR : aucune texture renseignée.": "ERROR: no texture entered.",
    "aucune texture renseignée.": "no texture entered.",
    "introuvable dans layers.cfg": "not found in layers.cfg",
    "Textures détectées dans layers.cfg : {count}": "Textures detected in layers.cfg: {count}",
    "... liste tronquée": "... list truncated",
})
UI_TRANSLATIONS["ru"].update({
    "Vérifier textures layers.cfg": "Проверить текстуры layers.cfg",
    "Chemins réinitialisés : tous les chemins de fichiers sont maintenant vides.": "Пути сброшены: все пути файлов теперь пустые.",
    "Chemin layers.cfg vide. Sélectionne d'abord un fichier layers.cfg.": "Путь к layers.cfg пустой. Сначала выберите файл layers.cfg.",
    "Vérification textures impossible : chemin layers.cfg vide.": "Проверка текстур невозможна: путь к layers.cfg пустой.",
    "Fichier layers.cfg introuvable ou invalide.": "Файл layers.cfg не найден или неверен.",
    "Erreur lecture layers.cfg : {error}": "Ошибка чтения layers.cfg: {error}",
    "INFO : vide, option non utilisée.": "INFO: пусто, опция не используется.",
    "vide, option non utilisée.": "пусто, опция не используется.",
    "ERROR : aucune texture renseignée.": "ERROR: текстура не указана.",
    "aucune texture renseignée.": "текстура не указана.",
    "introuvable dans layers.cfg": "не найдено в layers.cfg",
    "Textures détectées dans layers.cfg : {count}": "Текстур найдено в layers.cfg: {count}",
    "... liste tronquée": "... список обрезан",
})


UI_TRANSLATIONS["en"].update({
    "chemin vide": "empty path",
})
UI_TRANSLATIONS["ru"].update({
    "chemin vide": "пустой путь",
})


UI_TRANSLATIONS["en"].update({
    "ce n'est pas un fichier": "this is not a file",
    "extension invalide": "invalid extension",
    "aucune extension": "no extension",
    "attendu": "expected",
    "Fichier dupliqué : {a} et {b} utilisent le même fichier ({path})": "Duplicate file: {a} and {b} use the same file ({path})",
})
UI_TRANSLATIONS["ru"].update({
    "ce n'est pas un fichier": "это не файл",
    "extension invalide": "неверное расширение",
    "aucune extension": "нет расширения",
    "attendu": "ожидается",
    "Fichier dupliqué : {a} et {b} utilisent le même fichier ({path})": "Дублирующийся файл: {a} и {b} используют один и тот же файл ({path})",
})


UI_TRANSLATIONS["en"].update({
    "Ouvrir outputs": "Open outputs",
    "Vérifier les fichiers": "Check files",
})
UI_TRANSLATIONS["ru"].update({
    "Ouvrir outputs": "Открыть outputs",
    "Vérifier les fichiers": "Проверить файлы",
})


UI_TRANSLATIONS["en"].update({
    "— aucune —": "— none —",
})
UI_TRANSLATIONS["ru"].update({
    "— aucune —": "— нет —",
})


UI_TRANSLATIONS["en"].update({
    "Couleurs du sable": "Satmap sand color",
    "Type de sable": "Color preset",
    "Intensité sable": "Color strength",
    "Sable sec": "Dry sand RGB",
    "Sable mouillé": "Wet sand RGB",
    "Sable clair / coquillages": "Shell variation RGB",
    "Bord mouillé": "Wet beach edge RGB",
    "Fond sableux": "Seabed RGB",
    "Choisis un type de sable ou règle les couleurs à la main. Format accepté : R,G,B ou #RRGGBB.": "Use a preset to quickly match different sand types. In custom mode, enter RGB values as R,G,B or #RRGGBB.",
})
UI_TRANSLATIONS["ru"].update({
    "Couleurs du sable": "Цвет песка satmap",
    "Type de sable": "Цветовой пресет",
    "Intensité sable": "Сила цвета",
    "Sable sec": "Сухой песок RGB",
    "Sable mouillé": "Мокрый песок RGB",
    "Sable clair / coquillages": "Светлая вариация RGB",
    "Bord mouillé": "Влажная кромка RGB",
    "Fond sableux": "Морское дно RGB",
    "Choisis un type de sable ou règle les couleurs à la main. Format accepté : R,G,B ou #RRGGBB.": "Используйте пресет, чтобы быстро подобрать тип песка. В режиме custom введите RGB в формате R,G,B или #RRGGBB.",
})

UI_TRANSLATIONS["en"].update({
    "Texture sable": "Texture image",
    "Intensité texture": "Texture strength",
    "Taille texture": "Scale",
    "Optionnel : ajoute du grain visuel au sable sans modifier la zone générée.": "Optional: use a texture image (pebbles, fine sand, dark sand, etc.) to add visual detail to the sand color without changing the generator logic.",
    "Texture sable": "Sand texture image",
    "Intensité texture sable": "Sand texture strength",
    "Taille texture sable": "Sand texture scale",
    "désactivée": "disabled",
})
UI_TRANSLATIONS["en"].update({
    "Texture de l'eau": "Satmap water texture",
    "Texture eau": "Water texture image",
    "Intensité texture eau": "Water texture strength",
    "Taille texture eau": "Water texture scale",
    "Optionnel : ajoute des vagues, du bruit ou des reflets sans changer les zones d'eau.": "Optional: use a water texture image (waves, noise, reflections, foam, etc.) to add visual detail to the water gradient.",
})
UI_TRANSLATIONS["ru"].update({
    "Texture sable": "Изображение текстуры",
    "Intensité texture": "Сила текстуры",
    "Taille texture": "Масштаб",
    "Optionnel : ajoute du grain visuel au sable sans modifier la zone générée.": "Опционально: используйте изображение текстуры (галька, мелкий песок, тёмный песок и т. д.), чтобы добавить визуальные детали к цвету песка без изменения логики генератора.",
    "Texture sable": "Изображение текстуры песка",
    "Intensité texture sable": "Сила текстуры песка",
    "Taille texture sable": "Масштаб текстуры песка",
    "désactivée": "отключено",
})
UI_TRANSLATIONS["ru"].update({
    "Texture de l'eau": "Текстура воды satmap",
    "Texture eau": "Изображение текстуры воды",
    "Intensité texture eau": "Сила текстуры воды",
    "Taille texture eau": "Масштаб текстуры воды",
    "Optionnel : ajoute des vagues, du bruit ou des reflets sans changer les zones d'eau.": "Опционально: используйте изображение текстуры воды (волны, шум, отражения, пена и т. д.), чтобы добавить визуальные детали к градиенту воды.",
})


UI_TRANSLATIONS["en"].update({
    "Lissage eau": "Water texture smoothing",
    "Anti-répétition eau": "Water texture warp",
    "0 = désactivé | conseillé : lissage 12, anti-répétition 18": "0 = disabled | recommended: smoothing 12, warp 18",
})
UI_TRANSLATIONS["ru"].update({
    "Lissage eau": "Сглаживание текстуры воды",
    "Anti-répétition eau": "Искажение текстуры воды",
    "0 = désactivé | conseillé : lissage 12, anti-répétition 18": "0 = отключено | рекомендуется: сглаживание 12, искажение 18",
})

UI_TRANSLATIONS["en"].update({
    "Détecter inputs": "Detect inputs",
    "Chemins détectés automatiquement : {count}": "Automatically detected paths: {count}",
    "Aucun input détecté automatiquement.": "No input detected automatically.",
    "Chemins réinitialisés : détection automatique relancée.": "Paths reset: automatic detection restarted.",
    "Mask image": "Mask image",
    "Satmap image": "Satmap image",
})
UI_TRANSLATIONS["ru"].update({
    "Détecter inputs": "Найти inputs",
    "Chemins détectés automatiquement : {count}": "Автоматически найдено путей: {count}",
    "Aucun input détecté automatiquement.": "Автоматически inputs не найдены.",
    "Chemins réinitialisés : détection automatique relancée.": "Пути сброшены: автоматический поиск запущен снова.",
    "Mask image": "Изображение mask",
    "Satmap image": "Изображение satmap",
})

UI_TRANSLATIONS["en"].update({
    "Finition du bord de mer": "Coastal rendering / Water-beach contouring",
    "Ces réglages changent seulement l'apparence du bord de mer : écume, sable mouillé et dégradé d'eau. Ils ne changent pas la zone réellement générée.": "These settings are visual finishing controls: they do not replace the coastal zone, altitude, or transition profiles. Hover over the info icon to see each value's exact role.",
    "Épaisseur de l'écume": "Surf width px",
    "Intensité de l'écume": "Surf / foam strength",
    "Largeur sable mouillé": "Wet sand width px",
    "Zone eau claire": "Shallow water factor",
    "Zone eau intermédiaire": "Mid water factor",
    "Zone eau profonde": "Deep water factor",
    "Diagnostic et sécurité": "Validation / debug options",
    "Tolérance couleurs du mask": "Mask RGB color tolerance",
    "Créer images de diagnostic": "Generate debug masks",
    "Diagnostic complet": "Full diagnostic",
})
UI_TRANSLATIONS["ru"].update({
    "Finition du bord de mer": "Отрисовка побережья / контуры вода-пляж",
    "Ces réglages changent seulement l'apparence du bord de mer : écume, sable mouillé et dégradé d'eau. Ils ne changent pas la zone réellement générée.": "Эти настройки отвечают за визуальную доработку: они не заменяют профили береговой зоны, высот или перехода. Наведите курсор на значок информации, чтобы увидеть роль каждого параметра.",
    "Épaisseur de l'écume": "Ширина прибоя px",
    "Intensité de l'écume": "Сила прибоя / пены",
    "Largeur sable mouillé": "Ширина влажного песка px",
    "Zone eau claire": "Фактор мелководья",
    "Zone eau intermédiaire": "Фактор средней воды",
    "Zone eau profonde": "Фактор глубокой воды",
    "Diagnostic et sécurité": "Проверка / debug",
    "Tolérance couleurs du mask": "Допуск цветов mask RGB",
    "Créer images de diagnostic": "Создавать debug masks",
    "Diagnostic complet": "Полная диагностика",
})


# Libellés simplifiés v1.7.0 : vocabulaire plus clair pour l'interface.
UI_TRANSLATIONS["en"].update({
    "Textures DayZ à reconnaître": "DayZ textures to recognize",
    "Texture DayZ standard": "Standard DayZ texture",
    "Texture mod / custom": "Mod / custom texture",
    "Texture déjà plage": "Already beach texture",
    "Texture sable à agrandir": "Sand texture to expand",
    "Texture terre à mélanger": "Land texture to blend",
    "Choisis les textures que le script doit reconnaître dans layers.cfg. Les textures standard et custom sont combinées automatiquement. Plusieurs customs peuvent être séparées par des virgules.": "Choose the textures the script must recognize in layers.cfg. Standard and custom textures are combined automatically. Multiple custom names can be separated with commas.",

    "Plage : taille et pente": "Beach: size and slope",
    "Eau : niveaux d'altitude": "Water: altitude levels",
    "Fusion sable → terre": "Sand → land blend",
    "Largeur plage max": "Max beach width",
    "Pente autorisée": "Allowed slope",
    "Hauteur plage max": "Max beach height",
    "Eau profonde sous": "Deep water below",
    "Limite eau": "Water limit",
    "Terre à partir de": "Land starts at",
    "Largeur fusion terre": "Land blend width",
    "Force fusion terre": "Land blend strength",

    "Finition du bord de mer": "Seaside edge finishing",
    "Ces réglages changent seulement l'apparence du bord de mer : écume, sable mouillé et dégradé d'eau. Ils ne changent pas la zone réellement générée.": "These settings only change the look of the seaside edge: foam, wet sand, and water gradient. They do not change the generated area.",
    "Épaisseur de l'écume": "Foam thickness",
    "Intensité de l'écume": "Foam intensity",
    "Largeur sable mouillé": "Wet sand width",
    "Zone eau claire": "Clear water zone",
    "Zone eau intermédiaire": "Mid-water zone",
    "Zone eau profonde": "Deep water zone",

    "Couleurs du sable": "Sand colors",
    "Type de sable": "Sand type",
    "Intensité sable": "Sand intensity",
    "Sable sec": "Dry sand",
    "Sable mouillé": "Wet sand",
    "Sable clair / coquillages": "Light sand / shells",
    "Bord mouillé": "Wet edge",
    "Fond sableux": "Sandy seabed",
    "Choisis un type de sable ou règle les couleurs à la main. Format accepté : R,G,B ou #RRGGBB.": "Choose a sand type or edit the colors manually. Accepted format: R,G,B or #RRGGBB.",
    "Texture sable": "Sand texture",
    "Texture du sable": "Sand texture",
    "Intensité texture": "Texture intensity",
    "Taille texture": "Texture size",
    "Optionnel : ajoute du grain visuel au sable sans modifier la zone générée.": "Optional: adds visual grain to the sand without changing the generated area.",

    "Couleurs de l'eau": "Water colors",
    "Type d'eau": "Water type",
    "Intensité eau": "Water intensity",
    "Eau profonde": "Deep water",
    "Eau intermédiaire": "Mid water",
    "Eau peu profonde": "Shallow water",
    "Eau très claire": "Very clear water",
    "Écume / ressac": "Foam / surf",
    "Fond sous l'eau": "Underwater seabed",
    "Choisis un type d'eau ou règle le dégradé à la main : mer Atlantique, lagon, lac, eau sombre, etc.": "Choose a water type or edit the gradient manually: Atlantic sea, lagoon, lake, dark water, etc.",
    "Texture de l'eau": "Water texture",
    "Texture eau": "Water texture",
    "Intensité texture eau": "Water texture intensity",
    "Taille texture eau": "Water texture size",
    "Lissage eau": "Water smoothing",
    "Anti-répétition eau": "Water anti-tiling",
    "0 = désactivé | conseillé : lissage 12, anti-répétition 18": "0 = disabled | suggested: smoothing 12, anti-tiling 18",
    "Optionnel : ajoute des vagues, du bruit ou des reflets sans changer les zones d'eau.": "Optional: adds waves, noise, or reflections without changing water areas.",

    "Réglages moteur": "Engine settings",
    "Résolution finale": "Final resolution",
    "Mémoire / vitesse": "Memory / speed",
    "Taille variations couleur": "Color variation size",
    "Diagnostic et sécurité": "Diagnostics and safety",
    "Tolérance couleurs du mask": "Mask color tolerance",
    "Créer images de diagnostic": "Create diagnostic images",
    "Mémoire / vitesse - repères RAM": "Memory / speed - RAM guide",
    "Résumé des profils": "Profile summary",
})

UI_TRANSLATIONS["ru"].update({
    "Textures DayZ à reconnaître": "Текстуры DayZ для распознавания",
    "Texture DayZ standard": "Стандартная текстура DayZ",
    "Texture mod / custom": "Mod / custom текстура",
    "Texture déjà plage": "Текстура уже является пляжем",
    "Texture sable à agrandir": "Текстура песка для расширения",
    "Texture terre à mélanger": "Текстура земли для смешивания",
    "Choisis les textures que le script doit reconnaître dans layers.cfg. Les textures standard et custom sont combinées automatiquement. Plusieurs customs peuvent être séparées par des virgules.": "Выберите текстуры, которые скрипт должен распознавать в layers.cfg. Стандартные и custom-текстуры объединяются автоматически. Несколько custom-имён можно разделять запятыми.",

    "Plage : taille et pente": "Пляж: размер и уклон",
    "Eau : niveaux d'altitude": "Вода: уровни высоты",
    "Fusion sable → terre": "Смешивание песок → земля",
    "Largeur plage max": "Макс. ширина пляжа",
    "Pente autorisée": "Разрешённый уклон",
    "Hauteur plage max": "Макс. высота пляжа",
    "Eau profonde sous": "Глубокая вода ниже",
    "Limite eau": "Граница воды",
    "Terre à partir de": "Земля начинается от",
    "Largeur fusion terre": "Ширина смешивания земли",
    "Force fusion terre": "Сила смешивания земли",

    "Finition du bord de mer": "Финальная обработка берега",
    "Ces réglages changent seulement l'apparence du bord de mer : écume, sable mouillé et dégradé d'eau. Ils ne changent pas la zone réellement générée.": "Эти настройки меняют только внешний вид берега: пену, мокрый песок и градиент воды. Они не меняют фактически создаваемую зону.",
    "Épaisseur de l'écume": "Толщина пены",
    "Intensité de l'écume": "Интенсивность пены",
    "Largeur sable mouillé": "Ширина мокрого песка",
    "Zone eau claire": "Зона светлой воды",
    "Zone eau intermédiaire": "Зона средней воды",
    "Zone eau profonde": "Зона глубокой воды",

    "Couleurs du sable": "Цвета песка",
    "Type de sable": "Тип песка",
    "Intensité sable": "Интенсивность песка",
    "Sable sec": "Сухой песок",
    "Sable mouillé": "Мокрый песок",
    "Sable clair / coquillages": "Светлый песок / ракушки",
    "Bord mouillé": "Мокрая кромка",
    "Fond sableux": "Песчаное дно",
    "Choisis un type de sable ou règle les couleurs à la main. Format accepté : R,G,B ou #RRGGBB.": "Выберите тип песка или настройте цвета вручную. Формат: R,G,B или #RRGGBB.",
    "Texture sable": "Текстура песка",
    "Texture du sable": "Текстура песка",
    "Intensité texture": "Интенсивность текстуры",
    "Taille texture": "Размер текстуры",
    "Optionnel : ajoute du grain visuel au sable sans modifier la zone générée.": "Опционально: добавляет визуальную зернистость песка без изменения созданной зоны.",

    "Couleurs de l'eau": "Цвета воды",
    "Type d'eau": "Тип воды",
    "Intensité eau": "Интенсивность воды",
    "Eau profonde": "Глубокая вода",
    "Eau intermédiaire": "Средняя вода",
    "Eau peu profonde": "Мелкая вода",
    "Eau très claire": "Очень светлая вода",
    "Écume / ressac": "Пена / прибой",
    "Fond sous l'eau": "Дно под водой",
    "Choisis un type d'eau ou règle le dégradé à la main : mer Atlantique, lagon, lac, eau sombre, etc.": "Выберите тип воды или настройте градиент вручную: Атлантика, лагуна, озеро, тёмная вода и т.д.",
    "Texture de l'eau": "Текстура воды",
    "Texture eau": "Текстура воды",
    "Intensité texture eau": "Интенсивность текстуры воды",
    "Taille texture eau": "Размер текстуры воды",
    "Lissage eau": "Сглаживание воды",
    "Anti-répétition eau": "Анти-повтор воды",
    "0 = désactivé | conseillé : lissage 12, anti-répétition 18": "0 = отключено | совет: сглаживание 12, анти-повтор 18",
    "Optionnel : ajoute des vagues, du bruit ou des reflets sans changer les zones d'eau.": "Опционально: добавляет волны, шум или отражения без изменения зон воды.",

    "Réglages moteur": "Настройки движка",
    "Résolution finale": "Финальное разрешение",
    "Mémoire / vitesse": "Память / скорость",
    "Taille variations couleur": "Размер цветовых вариаций",
    "Diagnostic et sécurité": "Диагностика и безопасность",
    "Tolérance couleurs du mask": "Допуск цветов mask",
    "Créer images de diagnostic": "Создать диагностические изображения",
    "Mémoire / vitesse - repères RAM": "Память / скорость — ориентиры RAM",
    "Résumé des profils": "Сводка профилей",
})

UI_TRANSLATIONS["en"].update({
    "PLAGE : TAILLE ET PENTE": "BEACH: SIZE AND SLOPE",
    "EAU : NIVEAUX D'ALTITUDE": "WATER: ALTITUDE LEVELS",
    "FUSION SABLE → TERRE": "SAND → LAND BLEND",
})
UI_TRANSLATIONS["ru"].update({
    "PLAGE : TAILLE ET PENTE": "ПЛЯЖ: РАЗМЕР И УКЛОН",
    "EAU : NIVEAUX D'ALTITUDE": "ВОДА: УРОВНИ ВЫСОТЫ",
    "FUSION SABLE → TERRE": "СМЕШИВАНИЕ ПЕСОК → ЗЕМЛЯ",
})

PROFILE_LABELS = {
    "1 - Bord net": {"fr": "1 - Plage fine", "en": "1 - Thin beach", "ru": "1 - Тонкий пляж"},
    "2 - Bord naturel": {"fr": "2 - Plage naturelle", "en": "2 - Natural beach", "ru": "2 - Естественный пляж"},
    "3 - Équilibré": {"fr": "3 - Équilibré", "en": "3 - Balanced", "ru": "3 - Сбалансированный"},
    "4 - Plage large": {"fr": "4 - Plage large", "en": "4 - Wide beach", "ru": "4 - Широкий пляж"},
    "5 - Grande plage": {"fr": "5 - Très grande plage", "en": "5 - Very wide beach", "ru": "5 - Очень широкий пляж"},
    "6 - Extension forte": {"fr": "6 - Extension forte", "en": "6 - Strong expansion", "ru": "6 - Сильное расширение"},
    "7 - Extension max": {"fr": "7 - Test extrême", "en": "7 - Extreme test", "ru": "7 - Экстремальный тест"},
    "8 - Personnalisé": {"fr": "8 - Manuel", "en": "8 - Manual", "ru": "8 - Ручной"},

    "1 - Standard": {"fr": "1 - Eau normale", "en": "1 - Normal water", "ru": "1 - Обычная вода"},
    "2 - Littoral bas": {"fr": "2 - Eau basse", "en": "2 - Low water", "ru": "2 - Низкая вода"},
    "3 - Eau plus large": {"fr": "3 - Eau plus haute", "en": "3 - Higher water", "ru": "3 - Более высокая вода"},
    "4 - Personnalisé": {"fr": "4 - Manuel", "en": "4 - Manual", "ru": "4 - Ручной"},

    "1 - Désactivé": {"fr": "1 - Sans fusion", "en": "1 - No blend", "ru": "1 - Без смешивания"},
    "2 - Net léger": {"fr": "2 - Fusion légère", "en": "2 - Light blend", "ru": "2 - Лёгкое смешивание"},
    "3 - Net naturel": {"fr": "3 - Fusion naturelle", "en": "3 - Natural blend", "ru": "3 - Естественное смешивание"},
    "4 - Net marqué": {"fr": "4 - Fusion forte", "en": "4 - Strong blend", "ru": "4 - Сильное смешивание"},
    "5 - Dune courte": {"fr": "5 - Effet dune", "en": "5 - Dune effect", "ru": "5 - Эффект дюны"},
    "6 - Personnalisé": {"fr": "6 - Manuel", "en": "6 - Manual", "ru": "6 - Ручной"},
}

DESC_TRANSLATIONS = {
    "Plage fine et peu intrusive": {"en": "Fine, low-impact beach", "ru": "Тонкий и ненавязчивый пляж"},
    "Marge modérée": {"en": "Moderate margin", "ru": "Умеренный запас"},
    "Réglage polyvalent": {"en": "Versatile setting", "ru": "Универсальная настройка"},
    "Plage large polyvalente": {"en": "Versatile wide beach", "ru": "Универсальный широкий пляж"},
    "Sable plus présent": {"en": "More visible sand", "ru": "Более выраженный песок"},
    "Risque de remonter sur talus": {"en": "May climb onto embankments", "ru": "Может заходить на откосы"},
    "Test uniquement": {"en": "Test only", "ru": "Только для теста"},
    "Valeurs libres": {"en": "Free values", "ru": "Свободные значения"},
    "Eau <= 1.0 m": {"en": "Water <= 1.0 m", "ru": "Вода <= 1.0 м"},
    "Niveau côtier bas": {"en": "Low coastal level", "ru": "Низкий уровень берега"},
    "Eau plus présente": {"en": "More visible water", "ru": "Более выраженная вода"},
    "Niveaux libres": {"en": "Free levels", "ru": "Свободные уровни"},
    "Aucune retouche côté terre": {"en": "No inland retouch", "ru": "Без ретуши со стороны суши"},
    "Halo presque supprimé": {"en": "Halo almost removed", "ru": "Ореол почти удалён"},
    "Retouche équilibrée": {"en": "Balanced retouch", "ru": "Сбалансированная ретушь"},
    "Transition plus visible": {"en": "More visible transition", "ru": "Более заметный переход"},
    "Dune courte marquée": {"en": "Marked short dune", "ru": "Выраженная короткая дюна"},
}

GENERATOR_LOG_TRANSLATIONS = {
    "Générateur Satmap": {"en": "Satmap Generator", "ru": "Генератор Satmap"},
    "Preset sand :": {"en": "Sand preset:", "ru": "Пресет песка:"},
    "Réglages eau / terre :": {"en": "Water / land settings:", "ru": "Настройки воды / суши:"},
    "Deuxième passe terre :": {"en": "Second inland pass:", "ru": "Второй проход суши:"},
    "Couleurs du sable :": {"en": "Satmap sand color:", "ru": "Цвет песка satmap:"},
    "Texture sable satmap :": {"en": "Satmap sand texture:", "ru": "Текстура песка satmap:"},
    "Couleurs de l'eau :": {"en": "Satmap water color:", "ru": "Цвет воды satmap:"},
    "Texture de l'eau :": {"en": "Satmap water texture:", "ru": "Текстура воды satmap:"},
    "Textures / layers.cfg :": {"en": "Textures / layers.cfg:", "ru": "Текстуры / layers.cfg:"},
    "Sorties :": {"en": "Outputs:", "ru": "Выходные файлы:"},
    "Lecture layers.cfg...": {"en": "Reading layers.cfg...", "ru": "Чтение layers.cfg..."},
    "Chargement heightmap ASC...": {"en": "Loading heightmap ASC...", "ru": "Загрузка heightmap ASC..."},
    "Resize heightmap en mètres...": {"en": "Resizing heightmap in meters...", "ru": "Изменение размера heightmap в метрах..."},
    "Chargement mask...": {"en": "Loading mask...", "ru": "Загрузка mask..."},
    "Chargement satmap...": {"en": "Loading satmap...", "ru": "Загрузка satmap..."},
    "Calcul pente...": {"en": "Calculating slope...", "ru": "Расчёт уклона..."},
    "Construction vectorisée des catégories depuis layers.cfg...": {"en": "Building vectorized categories from layers.cfg...", "ru": "Построение векторных категорий из layers.cfg..."},
    "Extension locale de la zone source sable autorisée...": {"en": "Local extension of allowed sand source zone...", "ru": "Локальное расширение разрешённой зоны песка..."},
    "Distance au rivage optimisée...": {"en": "Optimized shoreline distance...", "ru": "Оптимизированная дистанция до берега..."},
    "Création bruit multi-échelle...": {"en": "Creating multi-scale noise...", "ru": "Создание многоуровневого шума..."},
    "Correction vectorisée de la satmap...": {"en": "Vectorized satmap correction...", "ru": "Векторная коррекция satmap..."},
    "Génération textures plage + sable vectorisée...": {"en": "Generating vectorized beach + sand textures...", "ru": "Векторная генерация пляжа + песка..."},
    "Application vectorisée eau / fond marin / plage avec contouring...": {"en": "Applying vectorized water / seabed / beach with contouring...", "ru": "Применение воды / морского дна / пляжа с контурами..."},
    "Contouring eau -> plage...": {"en": "Water -> beach contouring...", "ru": "Контуры вода -> пляж..."},
    "Deuxième passe côté terre du sable désactivée.": {"en": "Second inland sand pass disabled.", "ru": "Второй проход песка со стороны суши отключён."},
    "Deuxième passe côté terre du sable (V2 adaptative, limitée à la texture côté terre)...": {"en": "Second inland sand pass (adaptive V2, limited to inland texture)...", "ru": "Второй проход песка со стороны суши (адаптив V2, ограничен текстурой суши)..."},
    "Deuxième passe côté terre du sable (V2 adaptative, tous profils)...": {"en": "Second inland sand pass (adaptive V2, all profiles)...", "ru": "Второй проход песка со стороны суши (адаптив V2, все профили)..."},
    "Création beach mask...": {"en": "Creating beach mask...", "ru": "Создание beach mask..."},
    "Contraste global léger + conversion uint8...": {"en": "Light global contrast + uint8 conversion...", "ru": "Лёгкий общий контраст + конвертация uint8..."},
    "Terminé.": {"en": "Done.", "ru": "Готово."},
    "Satmap :": {"en": "Satmap:", "ru": "Satmap:"},
    "Beach mask :": {"en": "Beach mask:", "ru": "Beach mask:"},
}

SHORE_PROFILES = {
    "1 - Bord net":      {"key": "1", "distance": 45.0, "slope": 0.16, "height": 4.8, "desc": "Plage fine et peu intrusive"},
    "2 - Bord naturel":  {"key": "2", "distance": 55.0, "slope": 0.18, "height": 5.2, "desc": "Marge modérée"},
    "3 - Équilibré":     {"key": "3", "distance": 60.0, "slope": 0.20, "height": 5.5, "desc": "Réglage polyvalent"},
    "4 - Plage large":   {"key": "4", "distance": 70.0, "slope": 0.22, "height": 6.0, "desc": "Plage large polyvalente"},
    "5 - Grande plage":  {"key": "5", "distance": 85.0, "slope": 0.25, "height": 7.0, "desc": "Sable plus présent"},
    "6 - Extension forte": {"key": "6", "distance": 100.0, "slope": 0.28, "height": 8.0, "desc": "Risque de remonter sur talus"},
    "7 - Extension max": {"key": "7", "distance": 120.0, "slope": 0.32, "height": 10.0, "desc": "Test uniquement"},
    "8 - Personnalisé":  {"key": "8", "distance": 70.0, "slope": 0.22, "height": 6.0, "desc": "Valeurs libres"},
}

WATER_PROFILES = {
    "1 - Standard":       {"water_start": 0.0, "water_end": 1.0, "land_start": 1.0, "desc": "Eau <= 1.0 m"},
    "2 - Littoral bas":   {"water_start": 0.0, "water_end": 0.8, "land_start": 0.8, "desc": "Niveau côtier bas"},
    "3 - Eau plus large": {"water_start": 0.0, "water_end": 1.3, "land_start": 1.3, "desc": "Eau plus présente"},
    "4 - Personnalisé":   {"water_start": 0.0, "water_end": 1.0, "land_start": 1.0, "desc": "Niveaux libres"},
}

INLAND_PROFILES = {
    "1 - Désactivé":    {"distance": 0.0, "strength": 0.0, "desc": "Aucune retouche côté terre"},
    "2 - Net léger":    {"distance": 12.0, "strength": 0.60, "desc": "Halo presque supprimé"},
    "3 - Net naturel":  {"distance": 18.0, "strength": 0.78, "desc": "Retouche équilibrée"},
    "4 - Net marqué":   {"distance": 24.0, "strength": 0.92, "desc": "Transition plus visible"},
    "5 - Dune courte":  {"distance": 32.0, "strength": 1.00, "desc": "Dune courte marquée"},
    "6 - Personnalisé": {"distance": 18.0, "strength": 0.78, "desc": "Valeurs libres"},
}

TEXTURE_NONE = "— aucune —"
VANILLA_TEXTURES = [
    "cp_grass",
    "cp_dirt",
    "cp_rock",
    "cp_concrete1",
    "cp_concrete2",
    "cp_broadleaf_dense1",
    "cp_broadleaf_dense2",
    "cp_broadleaf_sparse1",
    "cp_broadleaf_sparse2",
    "cp_conifer_common1",
    "cp_conifer_common2",
    "cp_conifer_moss1",
    "cp_conifer_moss2",
    "cp_grass_tall",
    "cp_gravel",
    "en_flowers1",
    "en_flowers2",
    "en_flowers3",
    "en_forest_con",
    "en_forest_dec",
    "en_grass1",
    "en_grass2",
    "en_soil",
    "en_stones",
    "en_stubble",
    "en_tarmac_old",
    "sa_forest_spruce",
    "sa_grass_brown",
    "sa_concrete",
    "sa_beach",
    "sa_forest_birch",
    "sa_gravel",
    "sa_snow",
    "sa_snow_forest",
    "sa_volcanic_red",
    "sa_volcanic_yellow",
    "sa_grass_green",
]
VANILLA_TEXTURE_CHOICES = [TEXTURE_NONE] + VANILLA_TEXTURES

TOOLTIP_TEXTS = {
    "language": {"fr":"Langue de l'interface, des journaux traduits et des infobulles.","en":"Language used for the interface, translated logs, and tooltips.","ru":"Язык интерфейса, переведённых журналов и подсказок."},
    "generator_path": {"fr":"Chemin du script générateur satmap_generator_optimized_presets.py.","en":"Path to the generator script satmap_generator_optimized_presets.py.","ru":"Путь к скрипту генератора satmap_generator_optimized_presets.py."},
    "heightmap_path": {"fr":"Heightmap ASC source : altitudes utilisées pour l'eau, les pentes et le littoral.","en":"Source ASC heightmap: elevations used for water, slopes, and coastline detection.","ru":"Исходная heightmap ASC: высоты для определения воды, уклонов и берега."},
    "mask_path": {"fr":"Mask image : ses couleurs doivent correspondre au layers.cfg. PNG/BMP/TIFF recommandés.","en":"Mask image: its colors must match layers.cfg. PNG/BMP/TIFF are recommended.","ru":"Изображение mask: цвета должны совпадать с layers.cfg. Рекомендуются PNG/BMP/TIFF."},
    "satmap_path": {"fr":"Satmap source utilisée comme base visuelle à corriger.","en":"Source satmap used as the visual base to correct.","ru":"Исходная satmap, используемая как визуальная база для коррекции."},
    "layers_path": {"fr":"layers.cfg : correspondance entre couleurs du mask et noms de textures/layers.","en":"layers.cfg: mapping between mask colors and texture/layer names.","ru":"layers.cfg: соответствие цветов mask и имён textures/layers."},
    "beach_vanilla": {"fr":"Texture vanilla reconnue comme plage/littoral existant.","en":"Vanilla texture recognized as existing beach/coastline.","ru":"Vanilla-текстура, распознаваемая как существующий пляж/берег."},
    "beach_custom": {"fr":"Texture(s) custom de plage existante, séparées par virgules si besoin.","en":"Custom existing beach texture(s), comma-separated if needed.","ru":"Custom-текстуры существующего пляжа, через запятую при необходимости."},
    "sand_vanilla": {"fr":"Texture vanilla utilisée comme source de sable à étendre.","en":"Vanilla texture used as the sand source to extend.","ru":"Vanilla-текстура, используемая как источник песка для расширения."},
    "sand_custom": {"fr":"Texture(s) custom servant de source sable, ex. hp_sand.","en":"Custom texture(s) used as sand source, e.g. hp_sand.","ru":"Custom-текстуры как источник песка, например hp_sand."},
    "land_vanilla": {"fr":"Texture vanilla côté terre pour limiter la transition intérieure.","en":"Vanilla inland texture used to limit the inland transition.","ru":"Vanilla-текстура суши для ограничения внутреннего перехода."},
    "land_custom": {"fr":"Texture(s) custom côté terre. Vide = comportement général précédent.","en":"Custom inland texture(s). Empty = previous general behavior.","ru":"Custom-текстуры суши. Пусто = прежнее общее поведение."},
    "shore_profile": {'fr': 'Choisit un preset de plage.\nRéglages inclus : largeur max (px), pente autorisée (ratio), hauteur max (m).\nTu peux ensuite affiner chaque valeur juste dessous.', 'en': 'Selects a beach preset.\nIncluded settings: max width (px), allowed slope (ratio), max height (m).\nYou can fine-tune each value below.', 'ru': 'Выбирает пресет пляжа.\nПараметры: максимальная ширина (px), разрешённый уклон (коэффициент), максимальная высота (м).\nНиже можно настроить значения вручную.'},
    "water_profile": {'fr': 'Choisit un preset de niveau eau/terre.\nUnité des seuils : mètre (m).\nCes valeurs viennent de la heightmap ASC.', 'en': 'Selects a water/land level preset.\nThreshold unit: meter (m).\nThese values come from the ASC heightmap.', 'ru': 'Выбирает пресет уровней вода/суша.\nЕдиница порогов: метр (м).\nЗначения берутся из heightmap ASC.'},
    "inland_profile": {'fr': 'Choisit un preset de fusion sable → terre.\nRéglages inclus : largeur de fusion (px) et force (0 à 1).', 'en': 'Selects a sand-to-land blending preset.\nIncluded settings: blend width (px) and strength (0 to 1).', 'ru': 'Выбирает пресет смешивания песок → суша.\nПараметры: ширина смешивания (px) и сила (0–1).'},
    "sand_distance": {'fr': 'Largeur maximale où la plage peut être générée depuis le rivage.\nType : nombre décimal.\nUnité : px.\nMin : 1 | Max : 300.\nConseillé : 45 à 85 px.', 'en': 'Maximum width where beach can be generated from the shoreline.\nType: decimal number.\nUnit: px.\nMin: 1 | Max: 300.\nRecommended: 45 to 85 px.', 'ru': 'Максимальная ширина генерации пляжа от берега.\nТип: десятичное число.\nЕдиница: px.\nМин: 1 | Макс: 300.\nРекомендуется: 45–85 px.'},
    "sand_slope": {'fr': 'Pente maximale autorisée pour créer du sable.\nType : nombre décimal.\nUnité : ratio de pente, pas px/m.\nMin : 0.01 | Max : 1.00.\nBas = évite mieux les talus et falaises.', 'en': 'Maximum slope allowed for sand generation.\nType: decimal number.\nUnit: slope ratio, not px/m.\nMin: 0.01 | Max: 1.00.\nLower = avoids cliffs and embankments better.', 'ru': 'Максимальный уклон для генерации песка.\nТип: десятичное число.\nЕдиница: коэффициент уклона, не px/м.\nМин: 0.01 | Макс: 1.00.\nМеньше = лучше избегает склонов и скал.'},
    "sand_height": {'fr': 'Altitude maximale où la plage peut être créée.\nType : nombre décimal.\nUnité : m.\nMin : 0.1 | Max : 50.\nConseillé : 4.8 à 8 m.', 'en': 'Maximum altitude where beach can be created.\nType: decimal number.\nUnit: m.\nMin: 0.1 | Max: 50.\nRecommended: 4.8 to 8 m.', 'ru': 'Максимальная высота, где может создаваться пляж.\nТип: десятичное число.\nЕдиница: м.\nМин: 0.1 | Макс: 50.\nРекомендуется: 4.8–8 м.'},
    "water_start": {'fr': "Sous ce niveau, l'eau est traitée comme plus profonde/sombre.\nType : nombre décimal.\nUnité : m.\nMin : -100 | Max : 100.\nSouvent : 0.0 m.", 'en': 'Below this level, water is treated as deeper/darker.\nType: decimal number.\nUnit: m.\nMin: -100 | Max: 100.\nCommon value: 0.0 m.', 'ru': 'Ниже этого уровня вода считается более глубокой/тёмной.\nТип: десятичное число.\nЕдиница: м.\nМин: -100 | Макс: 100.\nОбычно: 0.0 м.'},
    "water_end": {'fr': 'Limite haute considérée comme eau.\nType : nombre décimal.\nUnité : m.\nMin : -100 | Max : 100.\nConseillé : 0.8 à 1.3 m.', 'en': 'Upper limit treated as water.\nType: decimal number.\nUnit: m.\nMin: -100 | Max: 100.\nRecommended: 0.8 to 1.3 m.', 'ru': 'Верхняя граница, считающаяся водой.\nТип: десятичное число.\nЕдиница: м.\nМин: -100 | Макс: 100.\nРекомендуется: 0.8–1.3 м.'},
    "land_start": {'fr': 'Niveau à partir duquel le terrain est considéré comme terre/plage émergée.\nType : nombre décimal.\nUnité : m.\nMin : -100 | Max : 100.\nEn général identique à Limite eau.', 'en': 'Level from which terrain is treated as emerged land/beach.\nType: decimal number.\nUnit: m.\nMin: -100 | Max: 100.\nUsually identical to Water limit.', 'ru': 'Уровень, с которого terrain считается сушей/надводным пляжем.\nТип: десятичное число.\nЕдиница: м.\nМин: -100 | Макс: 100.\nОбычно совпадает с границей воды.'},
    "inland_distance": {'fr': 'Largeur de fusion entre sable et terre côté intérieur.\nType : nombre décimal.\nUnité : px.\nMin : 0 | Max : 160.\n0 = désactivé. Conseillé : 12 à 32 px.', 'en': 'Blend width between sand and inland terrain.\nType: decimal number.\nUnit: px.\nMin: 0 | Max: 160.\n0 = disabled. Recommended: 12 to 32 px.', 'ru': 'Ширина смешивания между песком и внутренней сушей.\nТип: десятичное число.\nЕдиница: px.\nМин: 0 | Макс: 160.\n0 = отключено. Рекомендуется: 12–32 px.'},
    "inland_strength": {'fr': 'Intensité de la fusion sable → terre.\nType : nombre décimal.\nUnité : coefficient.\nMin : 0 | Max : 1.\n0 = aucune fusion, 1 = fusion forte.', 'en': 'Sand-to-land blend intensity.\nType: decimal number.\nUnit: coefficient.\nMin: 0 | Max: 1.\n0 = no blend, 1 = strong blend.', 'ru': 'Интенсивность смешивания песок → суша.\nТип: десятичное число.\nЕдиница: коэффициент.\nМин: 0 | Макс: 1.\n0 = нет смешивания, 1 = сильное смешивание.'},
    "surf_width": {'fr': "Épaisseur de la bande claire d'écume entre eau et sable.\nType : nombre décimal.\nUnité : px.\nMin : 1 | Max : 128.\nConseillé Atlantique : 6 à 10 px.", 'en': 'Thickness of the bright foam band between water and sand.\nType: decimal number.\nUnit: px.\nMin: 1 | Max: 128.\nRecommended Atlantic: 6 to 10 px.', 'ru': 'Толщина светлой полосы пены между водой и песком.\nТип: десятичное число.\nЕдиница: px.\nМин: 1 | Макс: 128.\nДля Атлантики: 6–10 px.'},
    "foam_strength": {'fr': "Intensité visuelle de l'écume et des bandes claires.\nType : nombre décimal.\nUnité : coefficient.\nMin : 0 | Max : 2.\nConseillé : 0.6 à 1.1.", 'en': 'Visual intensity of foam and bright bands.\nType: decimal number.\nUnit: coefficient.\nMin: 0 | Max: 2.\nRecommended: 0.6 to 1.1.', 'ru': 'Визуальная интенсивность пены и светлых полос.\nТип: десятичное число.\nЕдиница: коэффициент.\nМин: 0 | Макс: 2.\nРекомендуется: 0.6–1.1.'},
    "wet_sand_width": {'fr': "Largeur de la bande de sable humide près de l'eau.\nType : nombre décimal.\nUnité : px.\nMin : 1 | Max : 128.\nConseillé : 8 à 14 px.", 'en': 'Width of the wet sand band near water.\nType: decimal number.\nUnit: px.\nMin: 1 | Max: 128.\nRecommended: 8 to 14 px.', 'ru': 'Ширина полосы мокрого песка у воды.\nТип: десятичное число.\nЕдиница: px.\nМин: 1 | Макс: 128.\nРекомендуется: 8–14 px.'},
    "shallow_width_factor": {'fr': "Largeur de la zone d'eau claire près du rivage.\nType : nombre décimal.\nUnité : multiplicateur de Largeur plage max.\nMin : 0.05 | Max : 5.0.\nConseillé : 0.30 à 0.50.", 'en': 'Width of the bright shallow-water zone near shore.\nType: decimal number.\nUnit: multiplier of Max beach width.\nMin: 0.05 | Max: 5.0.\nRecommended: 0.30 to 0.50.', 'ru': 'Ширина зоны светлого мелководья у берега.\nТип: десятичное число.\nЕдиница: множитель максимальной ширины пляжа.\nМин: 0.05 | Макс: 5.0.\nРекомендуется: 0.30–0.50.'},
    "mid_width_factor": {'fr': 'Largeur de transition eau claire → eau intermédiaire.\nType : nombre décimal.\nUnité : multiplicateur de Largeur plage max.\nMin : 0.05 | Max : 5.0.\nConseillé : 0.70 à 1.10.', 'en': 'Transition width from clear water to mid water.\nType: decimal number.\nUnit: multiplier of Max beach width.\nMin: 0.05 | Max: 5.0.\nRecommended: 0.70 to 1.10.', 'ru': 'Ширина перехода светлая вода → средняя вода.\nТип: десятичное число.\nЕдиница: множитель максимальной ширины пляжа.\nМин: 0.05 | Макс: 5.0.\nРекомендуется: 0.70–1.10.'},
    "deep_width_factor": {'fr': "Distance avant que l'eau devienne profonde/sombre.\nType : nombre décimal.\nUnité : multiplicateur de Largeur plage max.\nMin : 0.05 | Max : 5.0.\nConseillé : 1.25 à 1.70.", 'en': 'Distance before water becomes deep/dark.\nType: decimal number.\nUnit: multiplier of Max beach width.\nMin: 0.05 | Max: 5.0.\nRecommended: 1.25 to 1.70.', 'ru': 'Дистанция до глубокой/тёмной воды.\nТип: десятичное число.\nЕдиница: множитель максимальной ширины пляжа.\nМин: 0.05 | Макс: 5.0.\nРекомендуется: 1.25–1.70.'},
    "sand_color_preset": {"fr":"Preset des couleurs sable : sec, humide, coquillier, bord et fond marin.","en":"Sand color preset: dry, wet, shell, edge, and seabed colors.","ru":"Пресет цветов песка: сухой, влажный, ракушечный, кромка и дно."},
    "sand_color_strength": {'fr': "Intensité d'application du type de sable choisi.\nType : nombre décimal.\nUnité : coefficient.\nMin : 0 | Max : 1.5.\n1 = couleur du preset complète.", 'en': 'Application intensity of the selected sand type.\nType: decimal number.\nUnit: coefficient.\nMin: 0 | Max: 1.5.\n1 = full preset color.', 'ru': 'Интенсивность применения выбранного типа песка.\nТип: десятичное число.\nЕдиница: коэффициент.\nМин: 0 | Макс: 1.5.\n1 = полный цвет пресета.'},
    "sand_dry_rgb": {"fr":"RGB du sable sec. Format R,G,B ou #RRGGBB.","en":"Dry sand RGB. Format R,G,B or #RRGGBB.","ru":"RGB сухого песка. Формат R,G,B или #RRGGBB."},
    "sand_wet_rgb": {"fr":"RGB du sable humide, visible près de l'eau.","en":"Wet sand RGB, visible near water.","ru":"RGB влажного песка, виден рядом с водой."},
    "sand_shell_rgb": {"fr":"RGB de variation claire/coquillière du sable.","en":"RGB for light/shell sand variation.","ru":"RGB светлой/ракушечной вариации песка."},
    "wet_beach_rgb": {"fr":"RGB du bord humide entre eau et plage.","en":"RGB of the wet edge between water and beach.","ru":"RGB влажной кромки между водой и пляжем."},
    "seabed_rgb": {"fr":"RGB du fond marin sableux visible près du rivage.","en":"RGB of the sandy seabed visible near shore.","ru":"RGB песчаного дна, видимого рядом с берегом."},
    "sand_texture_image": {"fr":"Texture optionnelle pour ajouter du grain au sable.","en":"Optional texture to add grain to sand.","ru":"Дополнительная текстура для зернистости песка."},
    "sand_texture_strength": {'fr': 'Intensité de la texture sable.\nType : nombre décimal.\nUnité : coefficient.\nMin : 0 | Max : 1.\nConseillé : 0.3 à 0.6.', 'en': 'Sand texture intensity.\nType: decimal number.\nUnit: coefficient.\nMin: 0 | Max: 1.\nRecommended: 0.3 to 0.6.', 'ru': 'Интенсивность текстуры песка.\nТип: десятичное число.\nЕдиница: коэффициент.\nМин: 0 | Макс: 1.\nРекомендуется: 0.3–0.6.'},
    "sand_texture_scale": {'fr': 'Échelle de la texture sable.\nType : nombre décimal.\nUnité : multiplicateur.\nMin : 0.1 | Max : 8.0.\nPlus haut = motif plus grand.', 'en': 'Sand texture scale.\nType: decimal number.\nUnit: multiplier.\nMin: 0.1 | Max: 8.0.\nHigher = larger pattern.', 'ru': 'Масштаб текстуры песка.\nТип: десятичное число.\nЕдиница: множитель.\nМин: 0.1 | Макс: 8.0.\nБольше = крупнее рисунок.'},
    "water_color_preset": {"fr":"Preset des couleurs eau : profonde, moyenne, peu profonde, lagon, ressac, fond.","en":"Water color preset: deep, mid, shallow, lagoon, surf, seabed.","ru":"Пресет цветов воды: глубокая, средняя, мелкая, лагуна, прибой, дно."},
    "water_color_strength": {'fr': "Intensité d'application du type d'eau choisi.\nType : nombre décimal.\nUnité : coefficient.\nMin : 0 | Max : 1.5.\n1 = couleur du preset complète.", 'en': 'Application intensity of the selected water type.\nType: decimal number.\nUnit: coefficient.\nMin: 0 | Max: 1.5.\n1 = full preset color.', 'ru': 'Интенсивность применения выбранного типа воды.\nТип: десятичное число.\nЕдиница: коэффициент.\nМин: 0 | Макс: 1.5.\n1 = полный цвет пресета.'},
    "water_deep_rgb": {"fr":"RGB de l'eau profonde/sombre.","en":"RGB for deep/dark water.","ru":"RGB глубокой/тёмной воды."},
    "water_mid_rgb": {"fr":"RGB de l'eau moyenne.","en":"RGB for mid water.","ru":"RGB средней воды."},
    "water_shallow_rgb": {"fr":"RGB de l'eau peu profonde près du rivage.","en":"RGB for shallow water near shore.","ru":"RGB мелководья рядом с берегом."},
    "water_lagoon_rgb": {"fr":"RGB de l'eau très claire/lagon.","en":"RGB for very clear/lagoon water.","ru":"RGB очень светлой воды/лагуны."},
    "water_surf_rgb": {"fr":"RGB du ressac/écume mélangé aux bandes claires.","en":"RGB for surf/foam blended into bright bands.","ru":"RGB прибоя/пены для светлых полос."},
    "water_seabed_rgb": {"fr":"RGB du fond marin sous l'eau.","en":"RGB for underwater seabed.","ru":"RGB дна под водой."},
    "water_texture_image": {"fr":"Texture optionnelle pour vagues, bruit ou reflets sur l'eau.","en":"Optional texture for waves, noise, or reflections on water.","ru":"Дополнительная текстура волн, шума или отражений на воде."},
    "water_texture_strength": {'fr': 'Intensité de la texture eau.\nType : nombre décimal.\nUnité : coefficient.\nMin : 0 | Max : 1.\nConseillé : 0.15 à 0.35.', 'en': 'Water texture intensity.\nType: decimal number.\nUnit: coefficient.\nMin: 0 | Max: 1.\nRecommended: 0.15 to 0.35.', 'ru': 'Интенсивность текстуры воды.\nТип: десятичное число.\nЕдиница: коэффициент.\nМин: 0 | Макс: 1.\nРекомендуется: 0.15–0.35.'},
    "water_texture_scale": {'fr': 'Échelle de la texture eau.\nType : nombre décimal.\nUnité : multiplicateur.\nMin : 0.1 | Max : 8.0.\nPlus haut = répétition moins visible.', 'en': 'Water texture scale.\nType: decimal number.\nUnit: multiplier.\nMin: 0.1 | Max: 8.0.\nHigher = less visible repetition.', 'ru': 'Масштаб текстуры воды.\nТип: десятичное число.\nЕдиница: множитель.\nМин: 0.1 | Макс: 8.0.\nБольше = меньше заметны повторы.'},
    "water_texture_smoothing": {'fr': 'Lissage appliqué à la texture eau avant répétition.\nType : nombre décimal.\nUnité : px, rayon de lissage.\nMin : 0 | Max : 64.\nConseillé : 8 à 16 px.', 'en': 'Smoothing applied to the water texture before tiling.\nType: decimal number.\nUnit: px, smoothing radius.\nMin: 0 | Max: 64.\nRecommended: 8 to 16 px.', 'ru': 'Сглаживание текстуры воды перед повторением.\nТип: десятичное число.\nЕдиница: px, радиус сглаживания.\nМин: 0 | Макс: 64.\nРекомендуется: 8–16 px.'},
    "water_texture_warp": {'fr': 'Déformation de coordonnées pour casser la répétition de la texture eau.\nType : nombre décimal.\nUnité : px.\nMin : 0 | Max : 96.\nConseillé : 12 à 24 px.', 'en': 'Coordinate warp used to break water texture repetition.\nType: decimal number.\nUnit: px.\nMin: 0 | Max: 96.\nRecommended: 12 to 24 px.', 'ru': 'Искажение координат для разрушения повторов текстуры воды.\nТип: десятичное число.\nЕдиница: px.\nМин: 0 | Макс: 96.\nРекомендуется: 12–24 px.'},
    "custom_preset": {"fr":"Profil personnalisé sauvegardé localement.","en":"Locally saved custom profile.","ru":"Локально сохранённый пользовательский профиль."},
    "target_size": {'fr': 'Résolution finale de la satmap et du beach mask.\nType : nombre entier.\nUnité : px.\nMin : 512 | Max : 30000.\nDayZ 10K : 10240 px.', 'en': 'Final resolution of the satmap and beach mask.\nType: integer.\nUnit: px.\nMin: 512 | Max: 30000.\nDayZ 10K: 10240 px.', 'ru': 'Финальное разрешение satmap и beach mask.\nТип: целое число.\nЕдиница: px.\nМин: 512 | Макс: 30000.\nDayZ 10K: 10240 px.'},
    "chunk_rows": {'fr': 'Nombre de lignes traitées par paquet.\nType : nombre entier.\nUnité : lignes/px.\nMin : 64 | Max : 8192.\nPlus haut = plus rapide mais plus de RAM.', 'en': 'Number of rows processed per chunk.\nType: integer.\nUnit: rows/px.\nMin: 64 | Max: 8192.\nHigher = faster but more RAM.', 'ru': 'Количество строк, обрабатываемых за chunk.\nТип: целое число.\nЕдиница: строки/px.\nМин: 64 | Макс: 8192.\nБольше = быстрее, но больше RAM.'},
    "block_size": {'fr': 'Taille des blocs de variation de couleur.\nType : nombre entier.\nUnité : px.\nMin : 4 | Max : 512.\nConseillé : 32 ou 64 px.', 'en': 'Size of color-variation blocks.\nType: integer.\nUnit: px.\nMin: 4 | Max: 512.\nRecommended: 32 or 64 px.', 'ru': 'Размер блоков вариации цвета.\nТип: целое число.\nЕдиница: px.\nМин: 4 | Макс: 512.\nРекомендуется: 32 или 64 px.'},
    "open_outputs": {"fr":"Ouvre outputs à la fin d'une génération réussie.","en":"Opens outputs after a successful generation.","ru":"Открывает outputs после успешной генерации."},
    "mask_color_tolerance": {'fr': 'Tolérance de correspondance des couleurs du mask.\nType : nombre entier.\nUnité : niveaux RGB.\nMin : 0 | Max : 255.\n0 = RGB exact et JPG refusé. >0 = accepte un mask compressé.', 'en': 'Color matching tolerance for the mask.\nType: integer.\nUnit: RGB levels.\nMin: 0 | Max: 255.\n0 = exact RGB and JPG rejected. >0 = accepts compressed masks.', 'ru': 'Допуск совпадения цветов mask.\nТип: целое число.\nЕдиница: уровни RGB.\nМин: 0 | Макс: 255.\n0 = точный RGB и JPG запрещён. >0 = допускает сжатый mask.'},
    "debug_masks": {'fr': 'Crée des images de diagnostic.\nType : case oui/non.\nUnité : aucune.\nMin/Max : désactivé ou activé.\nProduit : eau, pente, distance rivage, sable core/edge, category map.', 'en': 'Creates diagnostic images.\nType: yes/no checkbox.\nUnit: none.\nMin/Max: disabled or enabled.\nOutputs: water, slope, shore distance, sand core/edge, category map.', 'ru': 'Создаёт диагностические изображения.\nТип: флажок да/нет.\nЕдиница: нет.\nМин/Макс: выключено или включено.\nВывод: вода, уклон, дистанция до берега, sand core/edge, category map.'},
}

# Infobulles détaillées pour les paramètres de texture sable/eau.
TOOLTIP_TEXTS.update({
    "sand_texture_image": {"fr": "Image optionnelle utilisée pour ajouter du grain visuel au sable.\nFormats : PNG, JPG, JPEG, BMP, TIFF.\nValeur vide = texture désactivée.\nImpact : ne change pas la zone de sable générée, seulement le rendu couleur.", "en": "Optional image used to add visual grain to sand.\nFormats: PNG, JPG, JPEG, BMP, TIFF.\nEmpty value = texture disabled.\nImpact: does not change the generated sand area, only the color rendering.", "ru": "Дополнительное изображение для визуальной зернистости песка.\nФорматы: PNG, JPG, JPEG, BMP, TIFF.\nПустое значение = текстура отключена.\nВлияние: не меняет зону песка, только цветовой рендер."},
    "sand_texture_strength": {"fr": "Intensité de la texture sable.\nType : nombre décimal.\nUnité : coefficient.\nMin : 0 | Max : 1.\nDéfaut : 0.45.\nConseillé : 0.3 à 0.6.\n0 = aucun effet, 1 = texture très visible.", "en": "Sand texture intensity.\nType: decimal number.\nUnit: coefficient.\nMin: 0 | Max: 1.\nDefault: 0.45.\nRecommended: 0.3 to 0.6.\n0 = no effect, 1 = very visible texture.", "ru": "Интенсивность текстуры песка.\nТип: десятичное число.\nЕдиница: коэффициент.\nМин: 0 | Макс: 1.\nПо умолчанию: 0.45.\nРекомендуется: 0.3–0.6.\n0 = без эффекта, 1 = очень заметная текстура."},
    "sand_texture_scale": {"fr": "Échelle de la texture sable.\nType : nombre décimal.\nUnité : multiplicateur.\nMin : 0.1 | Max : 8.0.\nDéfaut : 1.0.\nPlus haut = motif plus grand, répétition moins serrée.", "en": "Sand texture scale.\nType: decimal number.\nUnit: multiplier.\nMin: 0.1 | Max: 8.0.\nDefault: 1.0.\nHigher = larger pattern, less tight repetition.", "ru": "Масштаб текстуры песка.\nТип: десятичное число.\nЕдиница: множитель.\nМин: 0.1 | Макс: 8.0.\nПо умолчанию: 1.0.\nБольше = крупнее рисунок, меньше плотность повтора."},
    "water_texture_image": {"fr": "Image optionnelle utilisée pour ajouter vagues, bruit, écume ou reflets sur l'eau.\nFormats : PNG, JPG, JPEG, BMP, TIFF.\nValeur vide = texture désactivée.\nImpact : ne change pas les zones d'eau, seulement le rendu visuel.", "en": "Optional image used to add waves, noise, foam, or reflections on water.\nFormats: PNG, JPG, JPEG, BMP, TIFF.\nEmpty value = texture disabled.\nImpact: does not change water areas, only the visual rendering.", "ru": "Дополнительное изображение для волн, шума, пены или отражений на воде.\nФорматы: PNG, JPG, JPEG, BMP, TIFF.\nПустое значение = текстура отключена.\nВлияние: не меняет зоны воды, только визуальный рендер."},
    "water_texture_strength": {"fr": "Intensité de la texture eau.\nType : nombre décimal.\nUnité : coefficient.\nMin : 0 | Max : 1.\nDéfaut : 0.25.\nConseillé : 0.15 à 0.35.\n0 = aucun effet, 1 = texture très visible.", "en": "Water texture intensity.\nType: decimal number.\nUnit: coefficient.\nMin: 0 | Max: 1.\nDefault: 0.25.\nRecommended: 0.15 to 0.35.\n0 = no effect, 1 = very visible texture.", "ru": "Интенсивность текстуры воды.\nТип: десятичное число.\nЕдиница: коэффициент.\nМин: 0 | Макс: 1.\nПо умолчанию: 0.25.\nРекомендуется: 0.15–0.35.\n0 = без эффекта, 1 = очень заметная текстура."},
    "water_texture_scale": {"fr": "Échelle de la texture eau.\nType : nombre décimal.\nUnité : multiplicateur.\nMin : 0.1 | Max : 8.0.\nDéfaut : 1.0.\nPlus haut = motif plus grand et répétition moins visible.", "en": "Water texture scale.\nType: decimal number.\nUnit: multiplier.\nMin: 0.1 | Max: 8.0.\nDefault: 1.0.\nHigher = larger pattern and less visible repetition.", "ru": "Масштаб текстуры воды.\nТип: десятичное число.\nЕдиница: множитель.\nМин: 0.1 | Макс: 8.0.\nПо умолчанию: 1.0.\nБольше = крупнее рисунок и менее заметные повторы."},
    "water_texture_smoothing": {"fr": "Lissage appliqué à la texture eau avant répétition.\nType : nombre décimal.\nUnité : px, rayon de lissage.\nMin : 0 | Max : 64.\nDéfaut : 12.0.\nConseillé : 8 à 16 px.\n0 = désactivé.", "en": "Smoothing applied to the water texture before tiling.\nType: decimal number.\nUnit: px, smoothing radius.\nMin: 0 | Max: 64.\nDefault: 12.0.\nRecommended: 8 to 16 px.\n0 = disabled.", "ru": "Сглаживание текстуры воды перед повторением.\nТип: десятичное число.\nЕдиница: px, радиус сглаживания.\nМин: 0 | Макс: 64.\nПо умолчанию: 12.0.\nРекомендуется: 8–16 px.\n0 = отключено."},
    "water_texture_warp": {"fr": "Déformation de coordonnées pour casser la répétition de la texture eau.\nType : nombre décimal.\nUnité : px.\nMin : 0 | Max : 96.\nDéfaut : 18.0.\nConseillé : 12 à 24 px.\n0 = désactivé.", "en": "Coordinate warp used to break water texture repetition.\nType: decimal number.\nUnit: px.\nMin: 0 | Max: 96.\nDefault: 18.0.\nRecommended: 12 to 24 px.\n0 = disabled.", "ru": "Искажение координат для разрушения повторов текстуры воды.\nТип: десятичное число.\nЕдиница: px.\nМин: 0 | Макс: 96.\nПо умолчанию: 18.0.\nРекомендуется: 12–24 px.\n0 = отключено."},
})

class HoverTooltip:
    """Infobulle simple au survol pour expliquer un paramètre."""

    def __init__(self, widget, text_getter, delay_ms: int = 350, wraplength: int = 560) -> None:
        self.widget = widget
        self.text_getter = text_getter
        self.delay_ms = delay_ms
        self.wraplength = wraplength
        self._after_id = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None) -> None:
        self._cancel()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self) -> None:
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self) -> None:
        self._cancel()
        if self._tip is not None:
            return
        text = self.text_getter() if callable(self.text_getter) else str(self.text_getter)
        text = str(text or "").strip()
        if not text:
            return
        try:
            x = self.widget.winfo_rootx() + 22
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        except Exception:
            x, y = 100, 100

        tip = tk.Toplevel(self.widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tip,
            text=text,
            justify="left",
            background="#ffffff",
            foreground=TEXT_COLOR,
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=6,
            wraplength=self.wraplength,
        )
        label.pack()
        self._tip = tip

    def _hide(self, _event=None) -> None:
        self._cancel()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


class SatmapGui(Tk):
    def __init__(self) -> None:
        super().__init__()
        self.root_dir = Path(__file__).resolve().parent
        self.process: subprocess.Popen[str] | None = None
        self.worker: threading.Thread | None = None
        self.last_command: list[str] | None = None
        self.last_start_time: datetime | None = None
        self._status_blink_job: str | None = None
        self._status_blink_on = False
        self._status_blink_mode = "idle"
        self._is_running = False
        self._run_mode = "generation"
        self._launcher_state_loaded = False
        self._profile_combo_bindings = []
        self._translatable_combo_values = []

        self.title(APP_TITLE)
        self.geometry(WINDOW_START_SIZE)
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self._build_vars()
        self._load_launcher_settings()
        self._build_ui()
        if not self._launcher_state_loaded:
            self._apply_reference_414_profile()
        self._sync_texture_layer_vars()
        self._refresh_status()
        self.protocol("WM_DELETE_WINDOW", self._on_close)


    def _auto_detect_file(self, names: list[str], extensions: tuple[str, ...] | list[str], include_input: bool = True) -> str:
        """Détecte automatiquement un fichier dans input/ puis dans le dossier du launcher.

        Priorité :
        1. nom exact complet, par exemple satmap_generator_optimized_presets.py ;
        2. stem exact, par exemple heightmap.asc ;
        3. stem contenant le mot-clé, par exemple my_satmap_final.png.
        """
        exts = tuple(e.lower() for e in extensions)
        wanted_full = {n.lower() for n in names if Path(n).suffix}
        wanted_stems = {Path(n).stem.lower() if Path(n).suffix else n.lower() for n in names}

        folders: list[Path] = []
        if include_input:
            folders.append(self.root_dir / DEFAULT_INPUT_DIR)
        folders.append(self.root_dir)

        candidates: list[Path] = []
        for folder in folders:
            if not folder.exists() or not folder.is_dir():
                continue
            try:
                files = [p for p in folder.iterdir() if p.is_file()]
            except OSError:
                continue

            for file_path in files:
                suffix = file_path.suffix.lower()
                full = file_path.name.lower()
                stem = file_path.stem.lower()
                if suffix not in exts:
                    continue
                if full in wanted_full:
                    return self._store_path_for_ui(file_path)
                if stem in wanted_stems:
                    candidates.insert(0, file_path)
                elif any(w in stem for w in wanted_stems):
                    candidates.append(file_path)

        if candidates:
            return self._store_path_for_ui(candidates[0])
        return ""

    def _detect_inputs_now(self) -> None:
        """Relance la détection automatique des chemins principaux."""
        detected = [
            (self.generator_var, self._auto_detect_file([GENERATOR_NAME, "satmap_generator_optimized_presets"], (".py", ".pyw"), include_input=False)),
            (self.heightmap_var, self._auto_detect_file(["heightmap"], (".asc",), include_input=True)),
            (self.mask_var, self._auto_detect_file(["mask"], IMAGE_EXTENSIONS, include_input=True)),
            (self.satmap_var, self._auto_detect_file(["satmap"], IMAGE_EXTENSIONS, include_input=True)),
            (self.layers_var, self._auto_detect_file(["layers"], (".cfg",), include_input=True)),
        ]
        count = 0
        for var, value in detected:
            if value:
                var.set(value)
                count += 1
        self._refresh_status()
        self._update_command_preview()
        if count:
            self._append_log(f"[OK] {self._tr('Chemins détectés automatiquement : {count}', count=count)}\n")
        else:
            self._append_log(f"[WARNING] {self._tr('Aucun input détecté automatiquement.')}\n")

    def _build_vars(self) -> None:
        self.language_var = StringVar(value="🇫🇷 Français")
        # Chemins vierges par défaut : l'utilisateur choisit explicitement ses fichiers.
        self.generator_var = StringVar(value=self._auto_detect_file([GENERATOR_NAME, "satmap_generator_optimized_presets"], (".py", ".pyw"), include_input=False))
        self.heightmap_var = StringVar(value=self._auto_detect_file(["heightmap"], (".asc",), include_input=True))
        self.mask_var = StringVar(value=self._auto_detect_file(["mask"], IMAGE_EXTENSIONS, include_input=True))
        self.satmap_var = StringVar(value=self._auto_detect_file(["satmap"], IMAGE_EXTENSIONS, include_input=True))
        self.layers_var = StringVar(value=self._auto_detect_file(["layers"], (".cfg",), include_input=True))
        self.beach_layers_var = StringVar(value="hp_beach")
        self.sand_layers_var = StringVar(value="hp_sand")
        self.land_layers_var = StringVar(value="")

        self.beach_vanilla_var = StringVar(value=TEXTURE_NONE)
        self.beach_custom_var = StringVar(value="hp_beach")
        self.sand_vanilla_var = StringVar(value=TEXTURE_NONE)
        self.sand_custom_var = StringVar(value="hp_sand")
        self.land_vanilla_var = StringVar(value=TEXTURE_NONE)
        self.land_custom_var = StringVar(value="")

        self.sand_color_preset_var = StringVar(value="belle_ile")
        self.sand_color_strength_var = StringVar(value="1.0")
        self.sand_dry_rgb_var = StringVar(value="222,204,178")
        self.sand_wet_rgb_var = StringVar(value="190,168,145")
        self.sand_shell_rgb_var = StringVar(value="208,196,182")
        self.wet_beach_rgb_var = StringVar(value="181,156,128")
        self.seabed_rgb_var = StringVar(value="160,120,90")
        self.sand_texture_image_var = StringVar(value="")
        self.sand_texture_strength_var = StringVar(value="0.45")
        self.sand_texture_scale_var = StringVar(value="1.0")

        self.water_color_preset_var = StringVar(value="atlantic_belle_ile")
        self.water_color_strength_var = StringVar(value="1.0")
        self.water_deep_rgb_var = StringVar(value="58,88,122")
        self.water_mid_rgb_var = StringVar(value="70,112,142")
        self.water_shallow_rgb_var = StringVar(value="93,149,156")
        self.water_lagoon_rgb_var = StringVar(value="118,181,174")
        self.water_surf_rgb_var = StringVar(value="156,202,190")
        self.water_seabed_rgb_var = StringVar(value="160,120,90")
        self.water_texture_image_var = StringVar(value="")
        self.water_texture_strength_var = StringVar(value="0.25")
        self.water_texture_scale_var = StringVar(value="1.0")
        self.water_texture_smoothing_var = StringVar(value="12.0")
        self.water_texture_warp_var = StringVar(value="18.0")

        self.mask_color_tolerance_var = StringVar(value="0")
        self.debug_masks_var = BooleanVar(value=False)
        self.surf_width_var = StringVar(value="8.0")
        self.shallow_width_factor_var = StringVar(value="0.42")
        self.mid_width_factor_var = StringVar(value="0.95")
        self.deep_width_factor_var = StringVar(value="1.70")
        self.foam_strength_var = StringVar(value="1.0")
        self.wet_sand_width_var = StringVar(value="10.0")

        self.shore_profile_var = StringVar(value="4 - Plage large")
        self.water_profile_var = StringVar(value="1 - Standard")
        self.inland_profile_var = StringVar(value="4 - Net marqué")

        self.shore_detail_var = StringVar(value="")
        self.water_detail_var = StringVar(value="")
        self.inland_detail_var = StringVar(value="")

        self.sand_distance_var = StringVar(value="70.0")
        self.sand_slope_var = StringVar(value="0.22")
        self.sand_height_var = StringVar(value="6.0")

        self.water_start_var = StringVar(value="0.0")
        self.water_end_var = StringVar(value="1.0")
        self.land_start_var = StringVar(value="1.0")

        self.inland_distance_var = StringVar(value="24.0")
        self.inland_strength_var = StringVar(value="0.92")

        self.target_size_var = StringVar(value="10240")
        self.chunk_rows_var = StringVar(value="2048")
        self.block_size_var = StringVar(value="32")
        self.open_outputs_var = BooleanVar(value=True)

        self.status_var = StringVar(value="Prêt")
        self.cmd_preview_var = StringVar(value="")
        self.progress_var = StringVar(value="0%")
        self.custom_preset_var = StringVar(value="")
        self._progress_value = 0

    def _configure_visual_theme(self) -> None:
        """Applique un thème ttk plus propre et homogène à toute l'interface."""
        self.configure(background=APP_BG)
        self.option_add("*Font", "{Segoe UI} 9")
        style = Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(".", font=("Segoe UI", 9))
        style.configure("TFrame", background=APP_BG)
        style.configure("Page.TFrame", background=APP_BG)
        style.configure("Header.TFrame", background=HEADER_BG)
        style.configure("Footer.TFrame", background=FOOTER_BG)

        style.configure("TLabel", background=APP_BG, foreground=TEXT_COLOR)
        style.configure("Header.TLabel", background=HEADER_BG, foreground=TEXT_COLOR)
        style.configure("Title.TLabel", background=HEADER_BG, foreground=TEXT_COLOR, font=("Segoe UI", 18, "bold"))
        style.configure("Subtitle.TLabel", background=HEADER_BG, foreground=MUTED_COLOR, font=("Segoe UI", 9))
        style.configure("Muted.TLabel", background=APP_BG, foreground=MUTED_COLOR)
        style.configure("Footer.TLabel", background=FOOTER_BG, foreground=MUTED_COLOR, font=("Segoe UI", 8))

        style.configure(
            "TLabelframe",
            background=APP_BG,
            bordercolor=BORDER_COLOR,
            relief="solid",
            padding=12,
        )
        style.configure(
            "TLabelframe.Label",
            background=APP_BG,
            foreground=TEXT_COLOR,
            font=("Segoe UI", 10, "bold"),
        )

        style.configure("TNotebook", background=APP_BG, borderwidth=0, tabmargins=(4, 6, 4, 0))
        style.configure("TNotebook.Tab", padding=(16, 8), font=("Segoe UI", 10, "bold"))
        style.map(
            "TNotebook.Tab",
            background=[("selected", CARD_BG), ("active", "#eaf1ff"), ("!selected", "#dde6f3")],
            foreground=[("selected", ACCENT_DARK), ("!selected", TEXT_COLOR)],
        )

        style.configure("TButton", padding=(10, 5), relief="flat")
        style.map("TButton", background=[("active", "#eaf1ff")])
        style.configure("Primary.TButton", background=ACCENT_COLOR, foreground="#ffffff", font=("Segoe UI", 9, "bold"), padding=(12, 6))
        style.map("Primary.TButton", background=[("active", ACCENT_DARK), ("disabled", "#9bb7f0")], foreground=[("disabled", "#eef4ff")])
        style.configure("Danger.TButton", background=DANGER_COLOR, foreground="#ffffff", font=("Segoe UI", 9, "bold"), padding=(12, 6))
        style.map("Danger.TButton", background=[("active", DANGER_DARK), ("disabled", "#e6aaa5")], foreground=[("disabled", "#fff5f5")])
        style.configure("Accent.TButton", background="#e8f0fe", foreground=ACCENT_DARK, padding=(12, 6))
        style.map("Accent.TButton", background=[("active", "#dbe8ff")])

        style.configure("TEntry", padding=(4, 4), fieldbackground="#ffffff", bordercolor=BORDER_COLOR, lightcolor=BORDER_COLOR, darkcolor=BORDER_COLOR)
        style.configure("TCombobox", padding=(4, 4), fieldbackground="#ffffff", bordercolor=BORDER_COLOR)
        style.configure("TCheckbutton", background=APP_BG, foreground=TEXT_COLOR)
        style.configure("Horizontal.TProgressbar", troughcolor="#e5eaf3", background=ACCENT_COLOR, bordercolor="#e5eaf3", lightcolor=ACCENT_COLOR, darkcolor=ACCENT_COLOR)
        self._style = style

    def _build_ui(self) -> None:
        self._configure_visual_theme()
        self._load_info_icon()

        # Structure principale en grille :
        #   ligne 0 = titre fixe
        #   ligne 1 = onglets qui prennent toute la place disponible
        #   ligne 2 = barre basse fixe, toujours visible même quand la fenêtre est réduite
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        top = Frame(self, padding=(14, 12), style="Header.TFrame")
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        title_block = Frame(top, style="Header.TFrame")
        title_block.pack(side="left", anchor="w")
        self.title_label = Label(title_block, text=f"Beach Satmap Generator v{APP_VERSION}", style="Title.TLabel")
        self.title_label.pack(anchor="w")
        self.subtitle_label = Label(title_block, text="Satmap, plage, eau et beach mask pour DayZ", style="Subtitle.TLabel")
        self.subtitle_label.pack(anchor="w", pady=(2, 0))

        self.language_label = Label(top, text="Langue", style="Header.TLabel")
        self.language_label.pack(side="right", padx=(8, 0))
        self.language_combo = Combobox(
            top,
            textvariable=self.language_var,
            values=list(LANGUAGE_OPTIONS.keys()),
            state="readonly",
            width=18,
        )
        self.language_combo.pack(side="right")
        self.language_combo.bind("<<ComboboxSelected>>", lambda _evt: self._apply_language(save=True))

        self.notebook = Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))

        self.tab_paths = Frame(self.notebook, padding=14, style="Page.TFrame")
        self.tab_profiles = Frame(self.notebook, padding=14, style="Page.TFrame")
        self.tab_advanced = Frame(self.notebook, padding=14, style="Page.TFrame")
        self.tab_output = Frame(self.notebook, padding=14, style="Page.TFrame")

        self.notebook.add(self.tab_paths, text="1. Fichiers")
        self.notebook.add(self.tab_profiles, text="2. Profils")
        self.notebook.add(self.tab_advanced, text="3. Technique")
        self.notebook.add(self.tab_output, text="4. Lancement")

        self._build_paths_tab()
        self._build_profiles_tab()
        self._build_advanced_tab()
        self._build_output_tab()

        bottom = Frame(self, padding=(12, 8), style="Footer.TFrame")
        bottom.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=0)

        self.status_label = Label(
            bottom,
            textvariable=self.status_var,
            anchor="w",
            justify="left",
            wraplength=620,
            style="Footer.TLabel",
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        # Signature créateurs / copyright affichée en bas à droite sur toutes les pages.
        self.signature_label = Label(
            bottom,
            text=f"2026 © Created by Bengilley & SleepingWolf · Launcher v{APP_VERSION}",
            style="Footer.TLabel",
            anchor="e",
        )
        self.signature_label.grid(row=0, column=1, sticky="e")

        def _resize_footer(event) -> None:
            # Garde le statut lisible sans pousser la signature hors de la fenêtre.
            reserved = 390
            self.status_label.configure(wraplength=max(220, event.width - reserved))

        bottom.bind("<Configure>", _resize_footer)

        self._setup_status_watchers()
        self._apply_language(save=False)

    def _build_paths_tab(self) -> None:
        # Conteneur unique de l'onglet : évite les blocs posés en surcouche directement sur l'onglet.
        content = Frame(self.tab_paths, style="Page.TFrame")
        content.pack(fill=BOTH, expand=True)

        box = LabelFrame(content, text="Fichiers utilisés par le script", padding=10)
        box.pack(fill="x")

        rows = [
            ("Script générateur", self.generator_var, "file"),
            ("Heightmap ASC", self.heightmap_var, "file"),
            ("Mask image", self.mask_var, "file"),
            ("Satmap image", self.satmap_var, "file"),
            ("Layers CFG", self.layers_var, "file"),
        ]
        for i, (label, var, kind) in enumerate(rows):
            Label(box, text=label).grid(row=i, column=0, sticky="w", pady=4)
            Entry(box, textvariable=var, width=95).grid(row=i, column=1, sticky="ew", padx=8, pady=4)
            Button(box, text="Parcourir", command=lambda v=var: self._browse_file(v)).grid(row=i, column=2, pady=4)
        box.columnconfigure(1, weight=1)

        texture_box = LabelFrame(content, text="Textures DayZ à reconnaître", padding=10)
        texture_box.pack(fill="x", pady=10)

        Label(texture_box, text="Type", width=24).grid(row=0, column=0, sticky="w", pady=(0, 6))
        Label(texture_box, text="Texture DayZ standard").grid(row=0, column=1, sticky="w", pady=(0, 6))
        Label(texture_box, text="Texture mod / custom").grid(row=0, column=2, sticky="w", padx=8, pady=(0, 6))

        Label(texture_box, text="Texture déjà plage", width=24).grid(row=1, column=0, sticky="w", pady=4)
        self.beach_vanilla_combo = Combobox(texture_box, textvariable=self.beach_vanilla_var, values=self._texture_choice_values(), state="readonly", width=28)
        self.beach_vanilla_combo.grid(row=1, column=1, sticky="ew", pady=4)
        Entry(texture_box, textvariable=self.beach_custom_var, width=50).grid(row=1, column=2, sticky="ew", padx=8, pady=4)
        Label(texture_box, text="ex vanilla : sa_beach | custom : hp_beach,my_beach").grid(row=1, column=3, sticky="w", pady=4)

        Label(texture_box, text="Texture sable à agrandir", width=24).grid(row=2, column=0, sticky="w", pady=4)
        self.sand_vanilla_combo = Combobox(texture_box, textvariable=self.sand_vanilla_var, values=self._texture_choice_values(), state="readonly", width=28)
        self.sand_vanilla_combo.grid(row=2, column=1, sticky="ew", pady=4)
        Entry(texture_box, textvariable=self.sand_custom_var, width=50).grid(row=2, column=2, sticky="ew", padx=8, pady=4)
        Label(texture_box, text="ex vanilla : cp_gravel | custom : hp_sand,my_sand").grid(row=2, column=3, sticky="w", pady=4)

        Label(texture_box, text="Texture terre à mélanger", width=24).grid(row=3, column=0, sticky="w", pady=4)
        self.land_vanilla_combo = Combobox(texture_box, textvariable=self.land_vanilla_var, values=self._texture_choice_values(), state="readonly", width=28)
        self.land_vanilla_combo.grid(row=3, column=1, sticky="ew", pady=4)
        Entry(texture_box, textvariable=self.land_custom_var, width=50).grid(row=3, column=2, sticky="ew", padx=8, pady=4)
        Label(texture_box, text="optionnel | ex : cp_grass ou custom_grass").grid(row=3, column=3, sticky="w", pady=4)

        texture_box.columnconfigure(1, weight=1)
        texture_box.columnconfigure(2, weight=1)

        Label(
            content,
            text="Choisis les textures que le script doit reconnaître dans layers.cfg. Les textures standard et custom sont combinées automatiquement. Plusieurs customs peuvent être séparées par des virgules.",
            style="Muted.TLabel",
            wraplength=930,
            justify="left",
        ).pack(anchor="w", pady=(0, 4))

        quick = LabelFrame(content, text="Actions rapides", padding=10)
        quick.pack(fill="x", pady=10)
        Button(quick, text="Créer input / outputs", command=self._create_folders).pack(side="left", padx=(0, 8))
        Button(quick, text="Installer dépendances", command=self._install_deps).pack(side="left", padx=(0, 8))
        Button(quick, text="Vérifier les fichiers", command=lambda: (self._refresh_status(), self._show_missing_files())).pack(side="left", padx=(0, 8))
        Button(quick, text="Vérifier textures layers.cfg", command=self._verify_layers_textures).pack(side="left", padx=(0, 8))
        Button(quick, text="Détecter inputs", command=self._detect_inputs_now).pack(side="left", padx=(0, 8))
        Button(quick, text="Réinitialiser chemins", command=self._reset_default_paths).pack(side="left")

        Label(content, text="Fichiers attendus par défaut : input/heightmap.asc, input/mask.png, input/satmap.png, input/layers.cfg. Formats image supportés pour mask, satmap et textures : PNG, JPG, JPEG, BMP, TIFF.").pack(anchor="w", pady=(8, 0))

    def _build_profiles_tab(self) -> None:
        # Onglet scrollable : garde toutes les options accessibles même en petite fenêtre.
        outer = Frame(self.tab_profiles, style="Page.TFrame")
        outer.pack(fill=BOTH, expand=True)

        canvas = Canvas(outer, highlightthickness=0, background=APP_BG, bd=0)
        vscroll = Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill=BOTH, expand=True)

        content = Frame(canvas, style="Page.TFrame")
        window_id = canvas.create_window((0, 0), window=content, anchor="nw")

        def _update_scrollregion(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _resize_content(event):
            canvas.itemconfigure(window_id, width=event.width)

        def _on_mousewheel(event):
            widget = self.focus_get()
            if widget is not None:
                widget_class = str(widget.winfo_class())
                if widget_class in {"TCombobox", "Combobox", "Entry", "TEntry", "Spinbox", "TSpinbox"}:
                    return "break"
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"

        def _bind_canvas_mousewheel(_event=None):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_canvas_mousewheel(_event=None):
            canvas.unbind_all("<MouseWheel>")

        content.bind("<Configure>", _update_scrollregion)
        canvas.bind("<Configure>", _resize_content)
        canvas.bind("<Enter>", _bind_canvas_mousewheel)
        canvas.bind("<Leave>", _unbind_canvas_mousewheel)

        presets = LabelFrame(content, text="Réglages rapides recommandés", padding=10)
        presets.pack(fill="x", pady=10)

        presets_row_1 = Frame(presets)
        presets_row_1.pack(fill="x", pady=(0, 6))
        Button(presets_row_1, text="Recommandés", command=self._apply_reference_414_profile).pack(side="left", padx=(0, 8))
        Button(presets_row_1, text="Naturel équilibré", command=self._apply_natural_balanced_profile).pack(side="left", padx=(0, 8))
        Button(presets_row_1, text="Littoral bas", command=self._apply_low_coast_profile).pack(side="left", padx=(0, 8))
        Button(presets_row_1, text="Grande plage propre", command=self._apply_wide_clean_profile).pack(side="left")

        presets_row_2 = Frame(presets)
        presets_row_2.pack(fill="x")
        Button(presets_row_2, text="Bord net léger", command=self._apply_clean_edge_profile).pack(side="left", padx=(0, 8))
        Button(presets_row_2, text="Plage large douce", command=self._apply_wide_soft_profile).pack(side="left", padx=(0, 8))
        Button(presets_row_2, text="Extension forte", command=self._apply_strong_extension_profile).pack(side="left")


        top_grid = Frame(content)
        top_grid.pack(fill="x")
        top_grid.columnconfigure(0, weight=1)
        top_grid.columnconfigure(1, weight=1)
        top_grid.columnconfigure(2, weight=1)

        shore = LabelFrame(top_grid, text="Plage : taille et pente", padding=10)
        water = LabelFrame(top_grid, text="Eau : niveaux d'altitude", padding=10)
        inland = LabelFrame(top_grid, text="Fusion sable → terre", padding=10)
        shore.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        water.grid(row=0, column=1, sticky="nsew", padx=6)
        inland.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        self._profile_box(shore, self.shore_profile_var, list(SHORE_PROFILES), self._on_shore_profile_change, "shore_profile")
        Label(shore, textvariable=self.shore_detail_var, justify="left", wraplength=270).pack(anchor="w", fill="x", pady=(0, 10))
        self._field(shore, "Largeur plage max", self.sand_distance_var, "sand_distance")
        self._field(shore, "Pente autorisée", self.sand_slope_var, "sand_slope")
        self._field(shore, "Hauteur plage max", self.sand_height_var, "sand_height")

        self._profile_box(water, self.water_profile_var, list(WATER_PROFILES), self._on_water_profile_change, "water_profile")
        Label(water, textvariable=self.water_detail_var, justify="left", wraplength=270).pack(anchor="w", fill="x", pady=(0, 10))
        self._field(water, "Eau profonde sous", self.water_start_var, "water_start")
        self._field(water, "Limite eau", self.water_end_var, "water_end")
        self._field(water, "Terre à partir de", self.land_start_var, "land_start")

        self._profile_box(inland, self.inland_profile_var, list(INLAND_PROFILES), self._on_inland_profile_change, "inland_profile")
        Label(inland, textvariable=self.inland_detail_var, justify="left", wraplength=270).pack(anchor="w", fill="x", pady=(0, 10))
        self._field(inland, "Largeur fusion terre", self.inland_distance_var, "inland_distance")
        self._field(inland, "Force fusion terre", self.inland_strength_var, "inland_strength")


        contour_box = LabelFrame(content, text="Finition du bord de mer", padding=10)
        contour_box.pack(fill="x", pady=(10, 10))
        Label(
            contour_box,
            text="Ces réglages changent seulement l'apparence du bord de mer : écume, sable mouillé et dégradé d'eau. Ils ne changent pas la zone réellement générée.",
            style="Muted.TLabel",
            wraplength=980,
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        contour_grid = Frame(contour_box)
        contour_grid.pack(fill="x")
        contour_fields = [
            (
                "Épaisseur de l'écume",
                self.surf_width_var,
                "surf_width",
            ),
            (
                "Intensité de l'écume",
                self.foam_strength_var,
                "foam_strength",
            ),
            (
                "Largeur sable mouillé",
                self.wet_sand_width_var,
                "wet_sand_width",
            ),
            (
                "Zone eau claire",
                self.shallow_width_factor_var,
                "shallow_width_factor",
            ),
            (
                "Zone eau intermédiaire",
                self.mid_width_factor_var,
                "mid_width_factor",
            ),
            (
                "Zone eau profonde",
                self.deep_width_factor_var,
                "deep_width_factor",
            ),
        ]
        for idx, (label, var, help_text) in enumerate(contour_fields):
            row = idx // 3
            col = idx % 3
            cell = Frame(contour_grid)
            cell.grid(row=row, column=col, sticky="ew", padx=(0, 14), pady=4)
            contour_grid.columnconfigure(col, weight=1)
            label_row = Frame(cell)
            label_row.pack(fill="x")
            Label(label_row, text=label).pack(side="left", anchor="w")
            self._help_icon(label_row, help_text).pack(side="left", padx=(5, 0))
            entry = Entry(cell, textvariable=var, width=8)
            entry.pack(anchor="w", pady=(2, 0))

        sand_color_box = LabelFrame(content, text="Couleurs du sable", padding=10)
        sand_color_box.pack(fill="x", pady=(10, 10))
        top_color = Frame(sand_color_box)
        top_color.pack(fill="x", pady=(0, 4))
        Label(top_color, text="Type de sable", width=18).pack(side="left")
        self.sand_color_combo = Combobox(top_color, textvariable=self.sand_color_preset_var, values=SAND_COLOR_PRESET_CHOICES, state="readonly", width=22)
        self.sand_color_combo.pack(side="left", padx=(0, 12))
        self.sand_color_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_sand_color_preset_change())
        Label(top_color, text="Intensité sable", width=14).pack(side="left")
        Entry(top_color, textvariable=self.sand_color_strength_var, width=8).pack(side="left", padx=(0, 12))
        Label(top_color, text="Choisis un type de sable ou règle les couleurs à la main. Format accepté : R,G,B ou #RRGGBB.").pack(side="left")

        rgb_grid = Frame(sand_color_box)
        rgb_grid.pack(fill="x")
        rgb_rows = [
            ("Sable sec", self.sand_dry_rgb_var),
            ("Sable mouillé", self.sand_wet_rgb_var),
            ("Sable clair / coquillages", self.sand_shell_rgb_var),
            ("Bord mouillé", self.wet_beach_rgb_var),
            ("Fond sableux", self.seabed_rgb_var),
        ]
        for i, (label, var) in enumerate(rgb_rows):
            row = i // 3
            col = (i % 3) * 3
            Label(rgb_grid, text=label, width=18).grid(row=row, column=col, sticky="w", pady=3, padx=(0, 4))
            Entry(rgb_grid, textvariable=var, width=16).grid(row=row, column=col + 1, sticky="w", pady=3, padx=(0, 6))
            preview = Canvas(rgb_grid, width=30, height=22, highlightthickness=1, highlightbackground=BORDER_COLOR, bd=0)
            preview.grid(row=row, column=col + 2, sticky="w", pady=3, padx=(0, 14))
            self._register_rgb_preview(var, preview)

        sand_texture_box = LabelFrame(sand_color_box, text="Texture du sable", padding=8)
        sand_texture_box.pack(anchor="w", pady=(8, 0))

        texture_row = Frame(sand_texture_box)
        texture_row.pack(anchor="w")
        texture_row.columnconfigure(1, weight=0)
        sand_texture_label_cell = Frame(texture_row)
        sand_texture_label_cell.grid(row=0, column=0, sticky="w")
        Label(sand_texture_label_cell, text="Texture sable", width=18).pack(side="left")
        self._help_icon(sand_texture_label_cell, "sand_texture_image").pack(side="left", padx=(3, 6))
        sand_texture_entry = Entry(texture_row, textvariable=self.sand_texture_image_var, width=32)
        sand_texture_entry.grid(row=0, column=1, sticky="w", padx=(0, 8))
        sand_texture_button = Button(texture_row, text="Parcourir", command=lambda: self._browse_file(self.sand_texture_image_var))
        sand_texture_button.grid(row=0, column=2, sticky="w")
        self._bind_tooltip_to_widget(sand_texture_entry, "sand_texture_image")
        self._bind_tooltip_to_widget(sand_texture_button, "sand_texture_image")

        texture_options_row = Frame(sand_texture_box)
        texture_options_row.pack(anchor="w", pady=(6, 0))
        sand_texture_strength_label_cell = Frame(texture_options_row)
        sand_texture_strength_label_cell.pack(side="left")
        Label(sand_texture_strength_label_cell, text="Intensité texture", width=18).pack(side="left")
        self._help_icon(sand_texture_strength_label_cell, "sand_texture_strength").pack(side="left", padx=(3, 6))
        sand_texture_strength_entry = Entry(texture_options_row, textvariable=self.sand_texture_strength_var, width=7)
        sand_texture_strength_entry.pack(side="left", padx=(0, 18))
        sand_texture_scale_label_cell = Frame(texture_options_row)
        sand_texture_scale_label_cell.pack(side="left")
        Label(sand_texture_scale_label_cell, text="Taille texture", width=18).pack(side="left")
        self._help_icon(sand_texture_scale_label_cell, "sand_texture_scale").pack(side="left", padx=(3, 6))
        sand_texture_scale_entry = Entry(texture_options_row, textvariable=self.sand_texture_scale_var, width=7)
        sand_texture_scale_entry.pack(side="left")
        self._bind_tooltip_to_widget(sand_texture_strength_entry, "sand_texture_strength")
        self._bind_tooltip_to_widget(sand_texture_scale_entry, "sand_texture_scale")

        sand_texture_note = Label(
            sand_texture_box,
            text="Optionnel : ajoute du grain visuel au sable sans modifier la zone générée.",
            wraplength=620,
            justify="left",
        )
        sand_texture_note.pack(anchor="w", pady=(6, 0))
        self._bind_tooltip_to_widget(sand_texture_note, "sand_texture_image")

        water_color_box = LabelFrame(content, text="Couleurs de l'eau", padding=10)
        water_color_box.pack(fill="x", pady=(0, 10))
        top_water = Frame(water_color_box)
        top_water.pack(fill="x", pady=(0, 4))
        Label(top_water, text="Type d'eau", width=18).pack(side="left")
        self.water_color_combo = Combobox(top_water, textvariable=self.water_color_preset_var, values=WATER_COLOR_PRESET_CHOICES, state="readonly", width=22)
        self.water_color_combo.pack(side="left", padx=(0, 12))
        self.water_color_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_water_color_preset_change())
        Label(top_water, text="Intensité eau", width=14).pack(side="left")
        Entry(top_water, textvariable=self.water_color_strength_var, width=8).pack(side="left", padx=(0, 12))
        Label(top_water, text="Choisis un type d'eau ou règle le dégradé à la main : mer Atlantique, lagon, lac, eau sombre, etc.", wraplength=520, justify="left").pack(side="left", fill="x", expand=True)

        water_rgb_grid = Frame(water_color_box)
        water_rgb_grid.pack(fill="x")
        water_rgb_rows = [
            ("Eau profonde", self.water_deep_rgb_var),
            ("Eau intermédiaire", self.water_mid_rgb_var),
            ("Eau peu profonde", self.water_shallow_rgb_var),
            ("Eau très claire", self.water_lagoon_rgb_var),
            ("Écume / ressac", self.water_surf_rgb_var),
            ("Fond sous l'eau", self.water_seabed_rgb_var),
        ]
        for i, (label, var) in enumerate(water_rgb_rows):
            row = i // 3
            col = (i % 3) * 3
            Label(water_rgb_grid, text=label, width=18).grid(row=row, column=col, sticky="w", pady=3, padx=(0, 4))
            Entry(water_rgb_grid, textvariable=var, width=16).grid(row=row, column=col + 1, sticky="w", pady=3, padx=(0, 6))
            preview = Canvas(water_rgb_grid, width=30, height=22, highlightthickness=1, highlightbackground=BORDER_COLOR, bd=0)
            preview.grid(row=row, column=col + 2, sticky="w", pady=3, padx=(0, 14))
            self._register_rgb_preview(var, preview)

        water_texture_box = LabelFrame(water_color_box, text="Texture de l'eau", padding=8)
        water_texture_box.pack(anchor="w", pady=(8, 0))
        water_texture_row = Frame(water_texture_box)
        water_texture_row.pack(anchor="w")
        water_texture_row.columnconfigure(1, weight=0)
        water_texture_label_cell = Frame(water_texture_row)
        water_texture_label_cell.grid(row=0, column=0, sticky="w")
        Label(water_texture_label_cell, text="Texture eau", width=18).pack(side="left")
        self._help_icon(water_texture_label_cell, "water_texture_image").pack(side="left", padx=(3, 6))
        water_texture_entry = Entry(water_texture_row, textvariable=self.water_texture_image_var, width=32)
        water_texture_entry.grid(row=0, column=1, sticky="w", padx=(0, 8))
        water_texture_button = Button(water_texture_row, text="Parcourir", command=lambda: self._browse_file(self.water_texture_image_var))
        water_texture_button.grid(row=0, column=2, sticky="w")
        self._bind_tooltip_to_widget(water_texture_entry, "water_texture_image")
        self._bind_tooltip_to_widget(water_texture_button, "water_texture_image")

        water_texture_basic_options_row = Frame(water_texture_box)
        water_texture_basic_options_row.pack(anchor="w", pady=(6, 0))
        water_texture_strength_label_cell = Frame(water_texture_basic_options_row)
        water_texture_strength_label_cell.pack(side="left")
        Label(water_texture_strength_label_cell, text="Intensité texture eau", width=18).pack(side="left")
        self._help_icon(water_texture_strength_label_cell, "water_texture_strength").pack(side="left", padx=(3, 6))
        water_texture_strength_entry = Entry(water_texture_basic_options_row, textvariable=self.water_texture_strength_var, width=7)
        water_texture_strength_entry.pack(side="left", padx=(0, 18))
        water_texture_scale_label_cell = Frame(water_texture_basic_options_row)
        water_texture_scale_label_cell.pack(side="left")
        Label(water_texture_scale_label_cell, text="Taille texture eau", width=18).pack(side="left")
        self._help_icon(water_texture_scale_label_cell, "water_texture_scale").pack(side="left", padx=(3, 6))
        water_texture_scale_entry = Entry(water_texture_basic_options_row, textvariable=self.water_texture_scale_var, width=7)
        water_texture_scale_entry.pack(side="left")
        self._bind_tooltip_to_widget(water_texture_strength_entry, "water_texture_strength")
        self._bind_tooltip_to_widget(water_texture_scale_entry, "water_texture_scale")

        water_texture_options_row = Frame(water_texture_box)
        water_texture_options_row.pack(anchor="w", pady=(6, 0))
        water_texture_smoothing_label_cell = Frame(water_texture_options_row)
        water_texture_smoothing_label_cell.pack(side="left")
        Label(water_texture_smoothing_label_cell, text="Lissage eau", width=18).pack(side="left")
        self._help_icon(water_texture_smoothing_label_cell, "water_texture_smoothing").pack(side="left", padx=(3, 6))
        water_texture_smoothing_entry = Entry(water_texture_options_row, textvariable=self.water_texture_smoothing_var, width=7)
        water_texture_smoothing_entry.pack(side="left", padx=(0, 10))
        water_texture_warp_label_cell = Frame(water_texture_options_row)
        water_texture_warp_label_cell.pack(side="left")
        Label(water_texture_warp_label_cell, text="Anti-répétition eau", width=22).pack(side="left")
        self._help_icon(water_texture_warp_label_cell, "water_texture_warp").pack(side="left", padx=(3, 6))
        water_texture_warp_entry = Entry(water_texture_options_row, textvariable=self.water_texture_warp_var, width=7)
        water_texture_warp_entry.pack(side="left", padx=(0, 10))
        water_texture_hint = Label(water_texture_options_row, text="0 = désactivé | conseillé : lissage 12, anti-répétition 18")
        water_texture_hint.pack(side="left")
        self._bind_tooltip_to_widget(water_texture_smoothing_entry, "water_texture_smoothing")
        self._bind_tooltip_to_widget(water_texture_warp_entry, "water_texture_warp")
        self._bind_tooltip_to_widget(water_texture_hint, "water_texture_smoothing")
        water_texture_note = Label(water_texture_box, text="Optionnel : ajoute des vagues, du bruit ou des reflets sans changer les zones d'eau.", wraplength=620, justify="left")
        water_texture_note.pack(anchor="w", pady=(6, 0))
        self._bind_tooltip_to_widget(water_texture_note, "water_texture_image")

        custom_box = LabelFrame(content, text="Profils personnalisés sauvegardés", padding=10)
        custom_box.pack(fill="x", pady=(0, 10))
        self.custom_preset_combo = Combobox(custom_box, textvariable=self.custom_preset_var, values=[], state="readonly", width=38)
        self.custom_preset_combo.pack(side="left", padx=(0, 8))
        Button(custom_box, text="Charger", command=self._load_selected_custom_preset).pack(side="left", padx=(0, 8))
        Button(custom_box, text="Sauvegarder réglage actuel", command=self._save_current_custom_preset).pack(side="left", padx=(0, 8))
        Button(custom_box, text="Supprimer", command=self._delete_selected_custom_preset).pack(side="left")
        Label(custom_box, text="Sauvegarde locale : custom_profiles.json", style="Muted.TLabel").pack(side="left", padx=(12, 0))
        self._refresh_custom_preset_combo()

        # Résumé des profils retiré volontairement : les infobulles et les profils
        # sélectionnés donnent maintenant l'information utile sans alourdir l'onglet.

    def _refresh_details_text(self) -> None:
        if not hasattr(self, "details_text"):
            return
        details_content = []
        details_content.append(self._tr("PLAGE : TAILLE ET PENTE") + "\n")
        for name, p in SHORE_PROFILES.items():
            details_content.append(f"- {self._profile_label(name)} : {self._tr_desc(p['desc'])} | {self._tr('distance')} {p['distance']} px | {self._tr('pente')} {p['slope']} | {self._tr('hauteur')} {p['height']} m\n")
        details_content.append("\n" + self._tr("EAU : NIVEAUX D'ALTITUDE") + "\n")
        for name, p in WATER_PROFILES.items():
            details_content.append(f"- {self._profile_label(name)} : {self._tr_desc(p['desc'])} | {self._tr('eau forte')} < {p['water_start']} m | {self._tr('eau')} <= {p['water_end']} m | {self._tr('terre')} > {p['land_start']} m\n")
        details_content.append("\n" + self._tr("FUSION SABLE → TERRE") + "\n")
        for name, p in INLAND_PROFILES.items():
            details_content.append(f"- {self._profile_label(name)} : {self._tr_desc(p['desc'])} | {self._tr('distance')} {p['distance']} px | {self._tr('force')} {p['strength']}\n")
        self.details_text.config(state=NORMAL)
        self.details_text.delete("1.0", END)
        self.details_text.insert("1.0", "".join(details_content))
        self.details_text.config(state=DISABLED)

    def _build_advanced_tab(self) -> None:
        # Conteneur unique de l'onglet : aucune section n'est posée en surcouche sur l'onglet.
        content = Frame(self.tab_advanced, style="Page.TFrame")
        content.pack(fill=BOTH, expand=True)

        box = LabelFrame(content, text="Réglages moteur", padding=10)
        box.pack(fill="x")
        self._field(box, "Résolution finale", self.target_size_var, "target_size")
        self._field(box, "Mémoire / vitesse", self.chunk_rows_var, "chunk_rows")
        self._field(box, "Taille variations couleur", self.block_size_var, "block_size")
        Checkbutton(box, text="Ouvrir le dossier outputs à la fin", variable=self.open_outputs_var).pack(anchor="w", pady=8)

        validate_box = LabelFrame(content, text="Diagnostic et sécurité", padding=10)
        validate_box.pack(fill="x", pady=(10, 0))
        mask_row = Frame(validate_box)
        mask_row.pack(fill="x", pady=4)
        Label(mask_row, text="Tolérance couleurs du mask", width=28).pack(side="left")
        mask_tol_entry = Entry(mask_row, textvariable=self.mask_color_tolerance_var, width=8)
        mask_tol_entry.pack(side="left")
        self._help_icon(mask_row, "mask_color_tolerance").pack(side="left", padx=(6, 0))
        debug_row = Frame(validate_box)
        debug_row.pack(fill="x", pady=4)
        debug_check = Checkbutton(debug_row, text="Créer images de diagnostic", variable=self.debug_masks_var)
        debug_check.pack(side="left")
        self._help_icon(debug_row, "debug_masks").pack(side="left", padx=(6, 0))

        help_box = LabelFrame(content, text="Mémoire / vitesse - observations RAM", padding=10)
        help_box.pack(fill="x", pady=10)
        Label(help_box, text="Observation 10240 x 10240 : le script seul monte à environ 8.5 Go RAM au pic.").pack(anchor="w")
        Label(help_box, text="Le chunk-rows change surtout la vitesse et la stabilité.").pack(anchor="w")
        Label(help_box, text="512 / 1024 : très sûr, utile pour petites configurations, mais plus lent.").pack(anchor="w")
        Label(help_box, text="2048 : équilibré, stable sur la plupart des PC récents.").pack(anchor="w")
        Label(help_box, text="4096 : recommandé pour 32/64 Go RAM, bon compromis vitesse/stabilité.").pack(anchor="w")
        Label(help_box, text="8192 : mode performance, à utiliser si le PC reste stable.").pack(anchor="w")
        Label(help_box, text="Windows peut afficher plus haut à cause du cache système et des logiciels ouverts.").pack(anchor="w")

        info_box = LabelFrame(content, text="Informations techniques", padding=10)
        info_box.pack(fill="x", pady=(0, 10))

        info_label = Label(info_box, text="", justify="left", wraplength=900)
        info_label._fr_text = "TECHNICAL_INFO_TEXT"
        info_label.pack(anchor="w")

    def _build_output_tab(self) -> None:
        # Conteneur unique de l'onglet lancement : commande, actions et journal sont imbriqués ensemble.
        content = Frame(self.tab_output, style="Page.TFrame")
        content.pack(fill=BOTH, expand=True)

        cmd_box = LabelFrame(content, text="Commande générée", padding=10)
        cmd_box.pack(fill="x")
        Entry(cmd_box, textvariable=self.cmd_preview_var, width=130).pack(fill="x")
        Button(cmd_box, text="Actualiser la commande", command=self._update_command_preview, style="Accent.TButton").pack(anchor="e", pady=(8, 0))

        actions_box = LabelFrame(content, text="Actions de génération", padding=10)
        actions_box.pack(fill="x", pady=(10, 0))
        self.run_button = Button(actions_box, text="Lancer la génération", command=self._start_generation, style="Primary.TButton")
        self.run_button.pack(side="left", padx=(0, 8))
        self.stop_button = Button(actions_box, text="Arrêter", command=self._stop_generation, state=DISABLED, style="Danger.TButton")
        self.stop_button.pack(side="left")
        self.diagnostic_button = Button(actions_box, text="Diagnostic complet", command=self._start_diagnostic, style="Accent.TButton")
        self.diagnostic_button.pack(side="left", padx=(8, 0))

        self.progress_bar = Progressbar(actions_box, mode="determinate", length=260, maximum=100)
        self.progress_bar.pack(side="left", padx=(18, 8), fill="x", expand=True)
        self.progress_label = Label(actions_box, textvariable=self.progress_var, width=8)
        self.progress_label.pack(side="left")

        log_box = LabelFrame(content, text="Journal", padding=10)
        log_box.pack(fill=BOTH, expand=True, pady=10)
        scrollbar = Scrollbar(log_box)
        scrollbar.pack(side="right", fill="y")
        self.log_text = Text(log_box, height=20, wrap="word", yscrollcommand=scrollbar.set, background="#0f172a", foreground="#e5e7eb", insertbackground="#ffffff", relief="solid", borderwidth=1, highlightthickness=0, padx=8, pady=8)
        self.log_text.pack(fill=BOTH, expand=True)
        self.log_text.tag_configure("info", foreground="#93c5fd")
        self.log_text.tag_configure("ok", foreground="#86efac")
        self.log_text.tag_configure("warning", foreground="#fde68a")
        self.log_text.tag_configure("error", foreground="#fca5a5")
        self.log_text.tag_configure("step", foreground="#c4b5fd")
        scrollbar.config(command=self.log_text.yview)

    def _rgb_text_to_hex(self, raw: str) -> str | None:
        """Convertit un texte RGB R,G,B ou #RRGGBB en couleur hex pour l'aperçu GUI."""
        value = str(raw or "").strip()
        if not value:
            return None
        try:
            if value.startswith("#"):
                hexa = value[1:].strip()
                if len(hexa) != 6 or not re.fullmatch(r"[0-9A-Fa-f]{6}", hexa):
                    return None
                return f"#{hexa.lower()}"

            parts = [part.strip() for part in value.split(",")]
            if len(parts) != 3:
                return None
            rgb = [int(float(part.replace(" ", ""))) for part in parts]
            if any(channel < 0 or channel > 255 for channel in rgb):
                return None
            return "#{:02x}{:02x}{:02x}".format(*rgb)
        except Exception:
            return None

    def _register_rgb_preview(self, var: StringVar, preview: Canvas) -> None:
        """Associe un carré d'aperçu à un champ RGB et le met à jour à chaque modification."""
        if not hasattr(self, "_rgb_preview_widgets"):
            self._rgb_preview_widgets = []
        self._rgb_preview_widgets.append((var, preview))

        def refresh(*_args) -> None:
            self._update_rgb_preview(var, preview)

        var.trace_add("write", refresh)
        self._update_rgb_preview(var, preview)

    def _update_rgb_preview(self, var: StringVar, preview: Canvas) -> None:
        color = self._rgb_text_to_hex(var.get())
        if color is None:
            preview.configure(background="#f2f4f7", highlightbackground=DANGER_COLOR)
        else:
            preview.configure(background=color, highlightbackground=BORDER_COLOR)

    def _refresh_rgb_previews(self) -> None:
        """Rafraîchit tous les carrés RGB, utile après chargement de profil/preset."""
        for var, preview in getattr(self, "_rgb_preview_widgets", []):
            self._update_rgb_preview(var, preview)

    def _profile_box(self, parent: Frame, variable: StringVar, values: list[str], callback, help_key: str | None = None) -> None:
        display_var = StringVar()
        header = Frame(parent)
        header.pack(fill="x", pady=(0, 4))
        if help_key:
            self._help_icon(header, help_key).pack(side="right")
        combo = Combobox(parent, textvariable=display_var, values=[], state="readonly")
        combo.pack(fill="x", pady=(0, 8))

        def on_select(_evt=None) -> None:
            reverse = {self._profile_label(v): v for v in values}
            selected = reverse.get(display_var.get(), display_var.get())
            variable.set(selected)
            callback()

        combo.bind("<<ComboboxSelected>>", on_select)
        self._profile_combo_bindings.append((combo, display_var, variable, list(values)))
        self._update_profile_combos()


    def _load_info_icon(self) -> None:
        self._info_icon_image = None
        self._info_icon_source = None
        path = self.root_dir / INFO_ICON_FILE
        if not path.exists():
            return
        try:
            source = tk.PhotoImage(file=str(path))
            max_dim = max(source.width(), source.height())
            factor = max(1, int((max_dim + 17) // 18))
            self._info_icon_source = source
            self._info_icon_image = source.subsample(factor, factor) if factor > 1 else source
        except Exception:
            self._info_icon_image = None
            self._info_icon_source = None

    def _tooltip_text(self, key: str) -> str:
        data = TOOLTIP_TEXTS.get(key)
        if isinstance(data, dict):
            lang = self._current_lang()
            return data.get(lang) or data.get("fr") or next(iter(data.values()))
        return self._tr(str(key))

    def _bind_tooltip_to_widget(self, widget, help_key: str) -> None:
        if getattr(widget, "_tooltip_installed", False):
            return
        widget._tooltip_key = help_key
        widget._tooltip_obj = HoverTooltip(widget, lambda key=help_key: self._tooltip_text(key))
        widget._tooltip_installed = True

    def _help_icon(self, parent: Frame, help_key: str):
        if getattr(self, "_info_icon_image", None) is not None:
            icon = tk.Label(parent, image=self._info_icon_image, cursor="question_arrow", borderwidth=0, highlightthickness=0)
        else:
            icon = tk.Label(parent, text="?", width=2, cursor="question_arrow", background="#e8f0fe", foreground=ACCENT_DARK, font=("Segoe UI", 8, "bold"))
        icon._is_help_icon = True
        self._bind_tooltip_to_widget(icon, help_key)
        return icon

    def _insert_help_icon_near(self, widget, help_key: str) -> None:
        if getattr(widget, "_help_icon_inserted", False):
            return
        parent = widget.master
        icon = self._help_icon(parent, help_key)
        manager = widget.winfo_manager()
        try:
            if manager == "pack":
                icon.pack(side="left", padx=(5, 0), before=widget)
            elif manager == "grid":
                info = widget.grid_info()
                row = int(info.get("row", 0))
                slaves = parent.grid_slaves(row=row)
                max_col = 0
                for child in slaves:
                    child_info = child.grid_info()
                    c = int(child_info.get("column", 0))
                    span = int(child_info.get("columnspan", 1))
                    max_col = max(max_col, c + span - 1)
                icon.grid(row=row, column=max_col + 1, sticky="w", padx=(4, 0))
            else:
                icon.pack(side="left", padx=(5, 0))
        except Exception:
            try:
                icon.pack(side="left", padx=(5, 0))
            except Exception:
                pass
        widget._help_icon_inserted = True

    def _field(self, parent: Frame, label: str, var: StringVar, help_key: str | None = None) -> None:
        row = Frame(parent)
        row.pack(fill="x", pady=4)
        label_widget = Label(row, text=label, width=20, anchor="w")
        label_widget.pack(side="left")
        if help_key:
            self._help_icon(row, help_key).pack(side="left", padx=(0, 6))
        # Champs numériques compacts : ces valeurs restent courtes (px, m, coefficient).
        entry = Entry(row, textvariable=var, width=10)
        entry.pack(side="left")

    def _install_parameter_tooltips(self) -> None:
        """Conservé pour compatibilité interne.

        Les infobulles sont ajoutées manuellement uniquement aux paramètres
        utiles pour éviter les doublons et la surcharge visuelle.
        """
        return

    def _current_lang(self) -> str:
        return LANGUAGE_OPTIONS.get(self.language_var.get(), "fr")

    def _tr(self, text: str, **kwargs) -> str:
        lang = self._current_lang()
        value = text if lang == "fr" else UI_TRANSLATIONS.get(lang, {}).get(text, text)
        if kwargs:
            try:
                value = value.format(**kwargs)
            except Exception:
                pass
        return value

    def _tr_desc(self, text: str) -> str:
        lang = self._current_lang()
        if lang == "fr":
            return text
        return DESC_TRANSLATIONS.get(text, {}).get(lang, text)

    def _profile_label(self, internal_name: str) -> str:
        lang = self._current_lang()
        return PROFILE_LABELS.get(internal_name, {}).get(lang, internal_name)

    def _profile_internal_from_display(self, display_name: str) -> str:
        for internal_name in list(SHORE_PROFILES) + list(WATER_PROFILES) + list(INLAND_PROFILES):
            if display_name == self._profile_label(internal_name):
                return internal_name
        return display_name

    def _texture_none_label(self) -> str:
        return self._tr(TEXTURE_NONE)

    def _texture_choice_values(self) -> list[str]:
        return [self._texture_none_label()] + VANILLA_TEXTURES

    def _texture_internal_value(self, value: str) -> str:
        value = (value or "").strip()
        if value in {TEXTURE_NONE, self._tr(TEXTURE_NONE), "— none —", "— нет —"}:
            return TEXTURE_NONE
        return value

    def _translate_generator_line(self, line: str) -> str:
        lang = self._current_lang()
        if lang == "fr":
            return line
        stripped = line.strip()
        suffix = "\n" if line.endswith("\n") else ""
        for fr, translations in GENERATOR_LOG_TRANSLATIONS.items():
            translated = translations.get(lang)
            if not translated:
                continue
            if stripped == fr:
                return translated + suffix
            if stripped.startswith(fr):
                return translated + stripped[len(fr):] + suffix
        # Traductions partielles des libellés les plus fréquents du générateur.
        replacements = {
            "preset": {"en": "preset", "ru": "пресет"},
            "distance au rivage": {"en": "shore distance", "ru": "дистанция до берега"},
            "pente max": {"en": "max slope", "ru": "макс. уклон"},
            "hauteur max": {"en": "max height", "ru": "макс. высота"},
            "eau forte sous": {"en": "strong water below", "ru": "сильная вода ниже"},
            "eau jusqu'à": {"en": "water up to", "ru": "вода до"},
            "terre/plage dès": {"en": "land/beach from", "ru": "суша/пляж от"},
            "distance transition": {"en": "transition distance", "ru": "дистанция перехода"},
            "force transition": {"en": "transition strength", "ru": "сила перехода"},
            "layers plage": {"en": "beach layers", "ru": "слои пляжа"},
            "layers source sable": {"en": "sand source layers", "ru": "слои источника песка"},
            "layers côté terre": {"en": "inland layers", "ru": "слои суши"},
            "non utilisé": {"en": "not used", "ru": "не используется"},
            "comportement précédent": {"en": "previous behavior", "ru": "прежнее поведение"},
            "preset couleur": {"en": "color preset", "ru": "пресет цвета"},
            "force couleur": {"en": "color strength", "ru": "сила цвета"},
            "sable sec RGB": {"en": "dry sand RGB", "ru": "сухой песок RGB"},
            "sable humide RGB": {"en": "wet sand RGB", "ru": "влажный песок RGB"},
            "bord humide RGB": {"en": "wet beach edge RGB", "ru": "влажная кромка RGB"},
            "fond marin RGB": {"en": "seabed RGB", "ru": "морское дно RGB"},
            "image texture": {"en": "texture image", "ru": "изображение текстуры"},
            "force texture": {"en": "texture strength", "ru": "сила текстуры"},
            "échelle texture": {"en": "texture scale", "ru": "масштаб текстуры"},
            "preset eau": {"en": "water preset", "ru": "пресет воды"},
            "force eau": {"en": "water strength", "ru": "сила воды"},
            "eau profonde RGB": {"en": "deep water RGB", "ru": "глубокая вода RGB"},
            "eau moyenne RGB": {"en": "mid water RGB", "ru": "средняя вода RGB"},
            "eau peu profonde RGB": {"en": "shallow water RGB", "ru": "мелководье RGB"},
            "lagon RGB": {"en": "lagoon RGB", "ru": "лагуна RGB"},
            "ressac RGB": {"en": "surf RGB", "ru": "прибой RGB"},
            "fond marin eau RGB": {"en": "water seabed RGB", "ru": "дно под водой RGB"},
            "image texture eau": {"en": "water texture image", "ru": "изображение текстуры воды"},
            "force texture eau": {"en": "water texture strength", "ru": "сила текстуры воды"},
            "échelle texture eau": {"en": "water texture scale", "ru": "масштаб текстуры воды"},
            "lissage texture eau": {"en": "water texture smoothing", "ru": "сглаживание текстуры воды"},
            "déformation texture": {"en": "texture warp", "ru": "искажение текстуры"},
            "satmap": {"en": "satmap", "ru": "satmap"},
            "beach mask": {"en": "beach mask", "ru": "beach mask"},
        }
        out = line
        for fr, trans in replacements.items():
            out = out.replace(fr, trans.get(lang, fr))
        return out

    def _technical_info_text(self) -> str:
        lang = self._current_lang()
        if lang == "en":
            return (
                "Final size: output resolution for the satmap and beach mask. "
                "10240 is recommended for a 10K map. Higher values improve precision, "
                "but increase generation time and RAM use. Interface limit: 512 to 30000.\n\n"
                "Chunk rows: number of rows processed in one pass. "
                "On a 10240 x 10240 output, current observation is about 8.5 GB RAM peak for the script alone. "
                "Chunk rows mainly affects speed and stability: 4096 is recommended, 8192 is performance mode if stable. "
                "Interface limit: 64 to 8192.\n\n"
                "Color block size: size of the zones used to break flat colors and add color variation. "
                "16 gives more detail but more noise, 32 is recommended, 64 is softer, "
                "128 or more may create visible large blocks. Interface limit: 4 to 512.\n\n"
                "General recommended setting: Final size 10240, Chunk rows 4096 recommended / 8192 performance, Color block size 32 or 64 depending on the desired result."
            )
        if lang == "ru":
            return (
                "Финальный размер: разрешение выходной satmap и beach mask. "
                "10240 рекомендуется для карты 10K. Чем выше значение, тем точнее результат, "
                "но тем больше время генерации и потребление RAM. Лимит интерфейса: 512–30000.\n\n"
                "Строк на chunk: количество строк, обрабатываемых за один проход. "
                "Для вывода 10240 x 10240 текущее наблюдение — около 8.5 ГБ RAM на пике только для скрипта. "
                "Chunk rows в основном влияет на скорость и стабильность: 4096 рекомендуется, 8192 — режим производительности, если ПК стабилен. "
                "Лимит интерфейса: 64–8192.\n\n"
                "Размер цветовых блоков: размер зон, используемых для разбивки однотонных участков и добавления вариаций цвета. "
                "16 даёт больше деталей, но больше шума; 32 рекомендуется; 64 мягче; "
                "128 и выше может создавать видимые крупные блоки. Лимит интерфейса: 4–512.\n\n"
                "Общая рекомендация: финальный размер 10240, Chunk rows 4096 рекомендуется / 8192 производительность, размер цветовых блоков 32 или 64 по желаемому результату."
            )
        return (
            "Résolution finale : résolution de sortie de la satmap et du beach mask. "
            "10240 est recommandé pour une carte 10K. Plus la valeur est haute, plus le rendu est précis, "
            "mais plus la génération consomme de RAM et de temps. Limite acceptée par l'interface : 512 à 30000.\n\n"
            "Mémoire / vitesse : nombre de lignes traitées en une seule passe. "
            "Sur une sortie 10240 x 10240, l'observation actuelle donne environ 8.5 Go RAM au pic pour le script seul. "
            "Le chunk-rows influence surtout la vitesse et la stabilité : 4096 est recommandé, 8192 est le mode performance si stable. "
            "Limite acceptée par l'interface : 64 à 8192.\n\n"
            "Taille variations couleur : taille des zones utilisées pour casser les aplats et ajouter des variations de couleur. "
            "16 donne un rendu plus détaillé mais plus bruité, 32 est recommandé, 64 donne un rendu plus doux, "
            "128 ou plus peut créer de gros blocs visibles. Limite acceptée par l'interface : 4 à 512.\n\n"
            "Réglage conseillé général : Résolution finale 10240, Mémoire / vitesse 4096 recommandé / 8192 performance, Taille variations couleur 32 ou 64 selon le rendu souhaité."
        )

    def _translate_widget_tree(self, widget) -> None:
        try:
            current_text = widget.cget("text")
        except Exception:
            current_text = None
        if current_text is not None and isinstance(current_text, str):
            if not hasattr(widget, "_fr_text"):
                widget._fr_text = current_text
            widget.configure(text=self._technical_info_text() if widget._fr_text == "TECHNICAL_INFO_TEXT" else self._tr(widget._fr_text))
        for child in widget.winfo_children():
            if isinstance(child, Combobox):
                continue
            self._translate_widget_tree(child)

    def _update_profile_combos(self) -> None:
        if not hasattr(self, "_profile_combo_bindings"):
            return
        for combo, display_var, variable, values in self._profile_combo_bindings:
            combo["values"] = [self._profile_label(v) for v in values]
            display_var.set(self._profile_label(variable.get()))


    def _state_variables(self) -> dict[str, StringVar | BooleanVar]:
        return {
            "generator": self.generator_var,
            "heightmap": self.heightmap_var,
            "mask": self.mask_var,
            "satmap": self.satmap_var,
            "layers": self.layers_var,
            "beach_vanilla": self.beach_vanilla_var,
            "beach_custom": self.beach_custom_var,
            "sand_vanilla": self.sand_vanilla_var,
            "sand_custom": self.sand_custom_var,
            "land_vanilla": self.land_vanilla_var,
            "land_custom": self.land_custom_var,
            "sand_color_preset": self.sand_color_preset_var,
            "sand_color_strength": self.sand_color_strength_var,
            "sand_dry_rgb": self.sand_dry_rgb_var,
            "sand_wet_rgb": self.sand_wet_rgb_var,
            "sand_shell_rgb": self.sand_shell_rgb_var,
            "wet_beach_rgb": self.wet_beach_rgb_var,
            "seabed_rgb": self.seabed_rgb_var,
            "sand_texture_image": self.sand_texture_image_var,
            "sand_texture_strength": self.sand_texture_strength_var,
            "sand_texture_scale": self.sand_texture_scale_var,
            "water_color_preset": self.water_color_preset_var,
            "water_color_strength": self.water_color_strength_var,
            "water_deep_rgb": self.water_deep_rgb_var,
            "water_mid_rgb": self.water_mid_rgb_var,
            "water_shallow_rgb": self.water_shallow_rgb_var,
            "water_lagoon_rgb": self.water_lagoon_rgb_var,
            "water_surf_rgb": self.water_surf_rgb_var,
            "water_seabed_rgb": self.water_seabed_rgb_var,
            "water_texture_image": self.water_texture_image_var,
            "water_texture_strength": self.water_texture_strength_var,
            "water_texture_scale": self.water_texture_scale_var,
            "water_texture_smoothing": self.water_texture_smoothing_var,
            "water_texture_warp": self.water_texture_warp_var,
            "mask_color_tolerance": self.mask_color_tolerance_var,
            "debug_masks": self.debug_masks_var,
            "surf_width": self.surf_width_var,
            "shallow_width_factor": self.shallow_width_factor_var,
            "mid_width_factor": self.mid_width_factor_var,
            "deep_width_factor": self.deep_width_factor_var,
            "foam_strength": self.foam_strength_var,
            "wet_sand_width": self.wet_sand_width_var,
            "shore_profile": self.shore_profile_var,
            "water_profile": self.water_profile_var,
            "inland_profile": self.inland_profile_var,
            "sand_distance": self.sand_distance_var,
            "sand_slope": self.sand_slope_var,
            "sand_height": self.sand_height_var,
            "water_start": self.water_start_var,
            "water_end": self.water_end_var,
            "land_start": self.land_start_var,
            "inland_distance": self.inland_distance_var,
            "inland_strength": self.inland_strength_var,
            "target_size": self.target_size_var,
            "chunk_rows": self.chunk_rows_var,
            "block_size": self.block_size_var,
            "open_outputs": self.open_outputs_var,
        }

    def _load_launcher_settings(self) -> None:
        path = self.root_dir / LAUNCHER_SETTINGS_FILE
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            lang = data.get("language", "fr")
            self.language_var.set(LANGUAGE_LABEL_BY_CODE.get(lang, "🇫🇷 Français"))
            state = data.get("state", {})
            if isinstance(state, dict):
                loaded_any = False
                for key, var in self._state_variables().items():
                    if key not in state:
                        continue
                    try:
                        if isinstance(var, BooleanVar):
                            var.set(bool(state[key]))
                        else:
                            var.set(str(state[key]))
                        loaded_any = True
                    except Exception:
                        pass
                self._launcher_state_loaded = loaded_any
        except Exception:
            self.language_var.set("🇫🇷 Français")

    def _save_launcher_settings(self) -> None:
        path = self.root_dir / LAUNCHER_SETTINGS_FILE
        state = {}
        for key, var in self._state_variables().items():
            try:
                state[key] = bool(var.get()) if isinstance(var, BooleanVar) else var.get()
            except Exception:
                pass
        try:
            path.write_text(
                json.dumps({"language": self._current_lang(), "state": state}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _on_close(self) -> None:
        self._save_launcher_settings()
        self.destroy()

    def _update_texture_combos(self) -> None:
        if not hasattr(self, "beach_vanilla_combo"):
            return

        combos = [
            (self.beach_vanilla_combo, self.beach_vanilla_var),
            (self.sand_vanilla_combo, self.sand_vanilla_var),
            (self.land_vanilla_combo, self.land_vanilla_var),
        ]

        for combo, var in combos:
            current_internal = self._texture_internal_value(var.get())
            combo["values"] = self._texture_choice_values()
            var.set(self._texture_none_label() if current_internal == TEXTURE_NONE else current_internal)

    def _normalize_texture_choice_vars(self) -> None:
        for var in (self.beach_vanilla_var, self.sand_vanilla_var, self.land_vanilla_var):
            internal = self._texture_internal_value(var.get())
            if internal == TEXTURE_NONE:
                var.set(self._texture_none_label())

    def _apply_language(self, save: bool = True) -> None:
        if save:
            self._save_launcher_settings()

        if hasattr(self, "notebook"):
            tab_texts = ["1. Fichiers", "2. Profils", "3. Technique", "4. Lancement"]
            for idx, fr_text in enumerate(tab_texts):
                try:
                    self.notebook.tab(idx, text=self._tr(fr_text))
                except Exception:
                    pass

        self._translate_widget_tree(self)
        self._update_profile_combos()
        self._update_texture_combos()
        self._update_profile_details()
        self._refresh_details_text()
        self._refresh_status()
        self._update_command_preview()
        self.title(f"{APP_TITLE} v{APP_VERSION}")

    def _merge_texture_names(self, vanilla_value: str, custom_value: str, allow_none: bool = False) -> str:
        values: list[str] = []
        vanilla_value = self._texture_internal_value(vanilla_value)
        custom_value = (custom_value or "").strip()
        if vanilla_value and vanilla_value != TEXTURE_NONE:
            values.append(vanilla_value)
        if custom_value:
            for part in custom_value.split(','):
                name = part.strip()
                if name and name not in values:
                    values.append(name)
        return ','.join(values)

    def _sync_texture_layer_vars(self) -> None:
        self.beach_layers_var.set(self._merge_texture_names(self.beach_vanilla_var.get(), self.beach_custom_var.get()))
        self.sand_layers_var.set(self._merge_texture_names(self.sand_vanilla_var.get(), self.sand_custom_var.get()))
        self.land_layers_var.set(self._merge_texture_names(self.land_vanilla_var.get(), self.land_custom_var.get(), allow_none=True))

    def _display_path(self, value: str | Path | None) -> str:
        """Affiche un chemin sans exposer le profil Windows complet.

        - Dans le dossier du launcher : chemin relatif.
        - Dans le dossier utilisateur : ~\\...
        - En dehors : [chemin externe]\\nom_du_fichier
        """
        if value is None:
            return self._tr("non détecté")
        raw = str(value).strip().strip('"')
        if not raw:
            return self._tr("chemin vide")

        path = Path(raw)
        try:
            resolved = self._resolve_user_path(path).resolve()
        except Exception:
            # Nettoyage minimal si le chemin est invalide ou partiel.
            cleaned = raw.replace(str(Path.home()), "~").replace(str(Path.home()).replace("/", "\\"), "~")
            cleaned = cleaned.replace(str(self.root_dir), ".").replace(str(self.root_dir).replace("/", "\\"), ".")
            return cleaned

        try:
            rel = resolved.relative_to(self.root_dir.resolve())
            return str(rel).replace("/", "\\")
        except Exception:
            pass

        home = Path.home()
        try:
            rel_home = resolved.relative_to(home.resolve())
            return "~\\" + str(rel_home).replace("/", "\\")
        except Exception:
            pass

        return "[chemin externe]\\" + resolved.name

    def _looks_like_path_arg(self, value: str) -> bool:
        if not isinstance(value, str) or not value:
            return False
        if "\\" in value or "/" in value:
            return True
        if re.match(r"^[A-Za-z]:", value):
            return True
        suffix = Path(value).suffix.lower()
        return suffix in {".py", ".pyw", ".asc", ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".cfg", ".txt", ".md", ".json"}

    def _format_cmd_display(self, cmd: list[str]) -> str:
        display_parts: list[str] = []
        for part in cmd:
            shown = self._display_path(part) if self._looks_like_path_arg(str(part)) else part
            display_parts.append(f'"{shown}"' if " " in shown else shown)
        return " ".join(display_parts)

    def _custom_presets_path(self) -> Path:
        return self.root_dir / CUSTOM_PRESETS_FILE

    def _load_custom_presets(self) -> dict:
        path = self._custom_presets_path()
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_custom_presets(self, data: dict) -> None:
        self._custom_presets_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _current_preset_payload(self) -> dict:
        self._sync_texture_layer_vars()
        return {
            "app_version": APP_VERSION,
            "shore_profile": self.shore_profile_var.get(),
            "water_profile": self.water_profile_var.get(),
            "inland_profile": self.inland_profile_var.get(),
            "sand_distance": self.sand_distance_var.get(),
            "sand_slope": self.sand_slope_var.get(),
            "sand_height": self.sand_height_var.get(),
            "water_start": self.water_start_var.get(),
            "water_end": self.water_end_var.get(),
            "land_start": self.land_start_var.get(),
            "inland_distance": self.inland_distance_var.get(),
            "inland_strength": self.inland_strength_var.get(),
            "target_size": self.target_size_var.get(),
            "chunk_rows": self.chunk_rows_var.get(),
            "block_size": self.block_size_var.get(),
            "beach_vanilla": self.beach_vanilla_var.get(),
            "beach_custom": self.beach_custom_var.get(),
            "sand_vanilla": self.sand_vanilla_var.get(),
            "sand_custom": self.sand_custom_var.get(),
            "land_vanilla": self.land_vanilla_var.get(),
            "land_custom": self.land_custom_var.get(),
            "sand_color_preset": self.sand_color_preset_var.get(),
            "sand_color_strength": self.sand_color_strength_var.get(),
            "sand_dry_rgb": self.sand_dry_rgb_var.get(),
            "sand_wet_rgb": self.sand_wet_rgb_var.get(),
            "sand_shell_rgb": self.sand_shell_rgb_var.get(),
            "wet_beach_rgb": self.wet_beach_rgb_var.get(),
            "seabed_rgb": self.seabed_rgb_var.get(),
            "sand_texture_image": self.sand_texture_image_var.get(),
            "sand_texture_strength": self.sand_texture_strength_var.get(),
            "sand_texture_scale": self.sand_texture_scale_var.get(),
            "water_color_preset": self.water_color_preset_var.get(),
            "water_color_strength": self.water_color_strength_var.get(),
            "water_deep_rgb": self.water_deep_rgb_var.get(),
            "water_mid_rgb": self.water_mid_rgb_var.get(),
            "water_shallow_rgb": self.water_shallow_rgb_var.get(),
            "water_lagoon_rgb": self.water_lagoon_rgb_var.get(),
            "water_surf_rgb": self.water_surf_rgb_var.get(),
            "water_seabed_rgb": self.water_seabed_rgb_var.get(),
            "water_texture_image": self.water_texture_image_var.get(),
            "water_texture_strength": self.water_texture_strength_var.get(),
            "water_texture_scale": self.water_texture_scale_var.get(),
            "water_texture_smoothing": self.water_texture_smoothing_var.get(),
            "water_texture_warp": self.water_texture_warp_var.get(),
            "mask_color_tolerance": self.mask_color_tolerance_var.get(),
            "debug_masks": bool(self.debug_masks_var.get()),
            "surf_width": self.surf_width_var.get(),
            "shallow_width_factor": self.shallow_width_factor_var.get(),
            "mid_width_factor": self.mid_width_factor_var.get(),
            "deep_width_factor": self.deep_width_factor_var.get(),
            "foam_strength": self.foam_strength_var.get(),
            "wet_sand_width": self.wet_sand_width_var.get(),
        }

    def _apply_preset_payload(self, payload: dict) -> None:
        def set_if(var: StringVar, key: str) -> None:
            if key in payload:
                var.set(str(payload[key]))
        for var, key in [
            (self.shore_profile_var, "shore_profile"), (self.water_profile_var, "water_profile"), (self.inland_profile_var, "inland_profile"),
            (self.sand_distance_var, "sand_distance"), (self.sand_slope_var, "sand_slope"), (self.sand_height_var, "sand_height"),
            (self.water_start_var, "water_start"), (self.water_end_var, "water_end"), (self.land_start_var, "land_start"),
            (self.inland_distance_var, "inland_distance"), (self.inland_strength_var, "inland_strength"),
            (self.target_size_var, "target_size"), (self.chunk_rows_var, "chunk_rows"), (self.block_size_var, "block_size"),
            (self.beach_vanilla_var, "beach_vanilla"), (self.beach_custom_var, "beach_custom"),
            (self.sand_vanilla_var, "sand_vanilla"), (self.sand_custom_var, "sand_custom"),
            (self.land_vanilla_var, "land_vanilla"), (self.land_custom_var, "land_custom"),
            (self.sand_color_preset_var, "sand_color_preset"),
            (self.sand_color_strength_var, "sand_color_strength"),
            (self.sand_dry_rgb_var, "sand_dry_rgb"),
            (self.sand_wet_rgb_var, "sand_wet_rgb"),
            (self.sand_shell_rgb_var, "sand_shell_rgb"),
            (self.wet_beach_rgb_var, "wet_beach_rgb"),
            (self.seabed_rgb_var, "seabed_rgb"),
            (self.sand_texture_image_var, "sand_texture_image"),
            (self.sand_texture_strength_var, "sand_texture_strength"),
            (self.sand_texture_scale_var, "sand_texture_scale"),
            (self.water_color_preset_var, "water_color_preset"),
            (self.water_color_strength_var, "water_color_strength"),
            (self.water_deep_rgb_var, "water_deep_rgb"),
            (self.water_mid_rgb_var, "water_mid_rgb"),
            (self.water_shallow_rgb_var, "water_shallow_rgb"),
            (self.water_lagoon_rgb_var, "water_lagoon_rgb"),
            (self.water_surf_rgb_var, "water_surf_rgb"),
            (self.water_seabed_rgb_var, "water_seabed_rgb"),
            (self.water_texture_image_var, "water_texture_image"),
            (self.water_texture_strength_var, "water_texture_strength"),
            (self.water_texture_scale_var, "water_texture_scale"),
            (self.water_texture_smoothing_var, "water_texture_smoothing"),
            (self.water_texture_warp_var, "water_texture_warp"),
            (self.mask_color_tolerance_var, "mask_color_tolerance"),
            (self.surf_width_var, "surf_width"),
            (self.shallow_width_factor_var, "shallow_width_factor"),
            (self.mid_width_factor_var, "mid_width_factor"),
            (self.deep_width_factor_var, "deep_width_factor"),
            (self.foam_strength_var, "foam_strength"),
            (self.wet_sand_width_var, "wet_sand_width"),
        ]:
            set_if(var, key)
        if "debug_masks" in payload:
            self.debug_masks_var.set(bool(payload.get("debug_masks")))
        if "sand_color_preset" in payload and not any(
            key in payload for key in ("sand_dry_rgb", "sand_wet_rgb", "sand_shell_rgb", "wet_beach_rgb", "seabed_rgb")
        ):
            self._apply_sand_color_preset_to_rgb(force=True)
        if "water_color_preset" in payload and not any(
            key in payload for key in ("water_deep_rgb", "water_mid_rgb", "water_shallow_rgb", "water_lagoon_rgb", "water_surf_rgb", "water_seabed_rgb")
        ):
            self._apply_water_color_preset_to_rgb(force=True)
        self._sync_texture_layer_vars()
        self._update_profile_details()
        self._update_command_preview()

    def _refresh_custom_preset_combo(self) -> None:
        data = self._load_custom_presets()
        names = sorted(data.keys(), key=str.lower)
        if hasattr(self, "custom_preset_combo"):
            self.custom_preset_combo["values"] = names
        if names and self.custom_preset_var.get() not in names:
            self.custom_preset_var.set(names[0])
        elif not names:
            self.custom_preset_var.set("")

    def _save_current_custom_preset(self) -> None:
        name = simpledialog.askstring(self._tr("Sauvegarder profil"), self._tr("Nom du profil personnalisé :"), parent=self)
        if not name:
            return
        name = name.strip()
        if not name:
            return
        data = self._load_custom_presets()
        if name in data and not messagebox.askyesno(self._tr("Remplacer"), self._tr("Le profil '{name}' existe déjà. Le remplacer ?", name=name)):
            return
        data[name] = self._current_preset_payload()
        self._write_custom_presets(data)
        self._refresh_custom_preset_combo()
        self.custom_preset_var.set(name)
        self._append_log(f"[OK] {self._tr('Profil personnalisé sauvegardé : {name}', name=name)}\n")

    def _load_selected_custom_preset(self) -> None:
        name = self.custom_preset_var.get().strip()
        data = self._load_custom_presets()
        if not name or name not in data:
            messagebox.showwarning(self._tr("Profil"), self._tr("Aucun profil personnalisé sélectionné."))
            return
        self._apply_preset_payload(data[name])
        self._append_log(f"[OK] {self._tr('Profil personnalisé chargé : {name}', name=name)}\n")

    def _delete_selected_custom_preset(self) -> None:
        name = self.custom_preset_var.get().strip()
        data = self._load_custom_presets()
        if not name or name not in data:
            messagebox.showwarning(self._tr("Profil"), self._tr("Aucun profil personnalisé sélectionné."))
            return
        if not messagebox.askyesno(self._tr("Supprimer"), self._tr("Supprimer le profil personnalisé '{name}' ?", name=name)):
            return
        data.pop(name, None)
        self._write_custom_presets(data)
        self._refresh_custom_preset_combo()
        self._append_log(f"[OK] {self._tr('Profil personnalisé supprimé : {name}', name=name)}\n")

    def _setup_status_watchers(self) -> None:
        """Actualise automatiquement l'état dès qu'un chemin obligatoire change."""
        self.language_var.trace_add("write", lambda *_args: self._apply_language(save=True))
        for var in (
            self.generator_var,
            self.heightmap_var,
            self.mask_var,
            self.satmap_var,
            self.layers_var,
        ):
            var.trace_add("write", lambda *_args: self._refresh_status())
        for var in (
            self.beach_vanilla_var, self.beach_custom_var,
            self.sand_vanilla_var, self.sand_custom_var,
            self.land_vanilla_var, self.land_custom_var,
        ):
            var.trace_add("write", lambda *_args: (self._sync_texture_layer_vars(), self._update_command_preview()))

    def _start_status_blink(self, mode: str) -> None:
        """
        Fait clignoter le statut global.

        mode = "red"   : fichier obligatoire manquant ou invalide
        mode = "green" : tous les fichiers obligatoires sont validés
        """
        self._status_blink_mode = mode
        if self._status_blink_job is not None:
            return

        def blink() -> None:
            if self._is_running:
                self._stop_status_blink()
                return

            missing = self._missing_files(include_generator=True)

            # Le mode peut changer automatiquement si l'utilisateur ajoute ou retire un fichier.
            self._status_blink_mode = "red" if missing else "green"
            self._status_blink_on = not self._status_blink_on

            if self._status_blink_mode == "red":
                self.status_label.configure(
                    foreground="#ff0000" if self._status_blink_on else "#8b0000"
                )
            else:
                self.status_label.configure(
                    foreground="#00b050" if self._status_blink_on else "#006b2e"
                )

            self._status_blink_job = self.after(550, blink)

        blink()

    def _stop_status_blink(self) -> None:
        if self._status_blink_job is not None:
            try:
                self.after_cancel(self._status_blink_job)
            except Exception:
                pass
            self._status_blink_job = None
        self._status_blink_on = False
        self._status_blink_mode = "idle"
        self.status_label.configure(foreground="black")

    def _has_required_files(self) -> bool:
        return len(self._missing_files(include_generator=True)) == 0

    def _store_path_for_ui(self, path_value: str | Path) -> str:
        """Stocke un chemin affichable sans profil Windows quand le fichier est dans le dossier launcher."""
        path = Path(path_value)
        try:
            rel = path.resolve().relative_to(self.root_dir.resolve())
            return str(rel).replace("/", "\\")
        except Exception:
            # Pour un fichier externe, on garde le vrai chemin en interne afin que le script puisse le lire.
            # L'affichage dans la commande, les logs et les messages reste offusqué via _display_path().
            return str(path)

    def _resolve_user_path(self, value: str | Path) -> Path:
        """Résout un chemin saisi dans l'interface.

        - Chemin absolu : utilisé tel quel.
        - Chemin relatif : résolu depuis le dossier du launcher.
        """
        raw = str(value).strip().strip('"')
        path = Path(raw)
        if not raw:
            return path
        if path.is_absolute():
            return path
        return self.root_dir / path

    def _filetypes_for_var(self, var: StringVar):
        if var is self.generator_var:
            return SCRIPT_FILETYPES
        if var is self.heightmap_var:
            return ASC_FILETYPES
        if var in (self.mask_var, self.satmap_var, self.sand_texture_image_var, self.water_texture_image_var):
            return IMAGE_FILETYPES
        if var is self.layers_var:
            return CFG_FILETYPES
        return [("Tous les fichiers", "*.*")]

    def _initial_dir_for_var(self, var: StringVar) -> str:
        if var in (self.heightmap_var, self.mask_var, self.satmap_var, self.layers_var):
            input_dir = self.root_dir / DEFAULT_INPUT_DIR
            if input_dir.exists():
                return str(input_dir)
        return str(self.root_dir)

    def _browse_file(self, var: StringVar) -> None:
        path = filedialog.askopenfilename(
            initialdir=self._initial_dir_for_var(var),
            filetypes=self._filetypes_for_var(var),
        )
        if path:
            var.set(self._store_path_for_ui(path))
            self._refresh_status()
            self._update_command_preview()

    def _create_folders(self) -> None:
        (self.root_dir / "input").mkdir(exist_ok=True)
        (self.root_dir / "outputs").mkdir(exist_ok=True)
        messagebox.showinfo("Dossiers créés", "Les dossiers input et outputs sont prêts.")
        self._refresh_status()

    def _install_deps(self) -> None:
        self._append_log("Installation des dépendances : numpy pillow scipy\n")
        cmd = [sys.executable, "-m", "pip", "install", "numpy", "pillow", "scipy"]
        threading.Thread(target=self._run_simple_command, args=(cmd,), daemon=True).start()

    def _run_simple_command(self, cmd: list[str]) -> None:
        try:
            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUNBUFFERED"] = "1"
            proc = subprocess.Popen(
                cmd,
                cwd=self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
            )
            assert proc.stdout is not None
            for line in proc.stdout:
                self._append_log(line)
            code = proc.wait()
            self._append_log(f"\nCommande terminée avec code {code}.\n")
        except Exception as exc:
            self._append_log(f"Erreur : {exc}\n")

    def _open_root(self) -> None:
        self._open_path(self.root_dir)

    def _open_outputs(self) -> None:
        out = self.root_dir / "outputs"
        out.mkdir(exist_ok=True)
        self._open_path(out)

    def _open_path(self, path: Path) -> None:
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", str(path)], check=False)
            else:
                subprocess.run(["xdg-open", str(path)], check=False)
        except Exception as exc:
            messagebox.showerror("Erreur", str(exc))

    def _update_profile_details(self) -> None:
        """Affiche le détail lisible du profil sélectionné dans l'onglet Profils."""
        shore = SHORE_PROFILES.get(self.shore_profile_var.get(), {})
        water = WATER_PROFILES.get(self.water_profile_var.get(), {})
        inland = INLAND_PROFILES.get(self.inland_profile_var.get(), {})

        if shore:
            self.shore_detail_var.set(
                f"{self._tr('Détail')} : {self._tr_desc(shore.get('desc', ''))}\n"
                f"{self._tr('Largeur plage max')} : {shore.get('distance')} px\n"
                f"{self._tr('Pente autorisée')} : {shore.get('slope')}\n"
                f"{self._tr('Hauteur plage max')} : {shore.get('height')} m"
            )
        if water:
            self.water_detail_var.set(
                f"{self._tr('Détail')} : {self._tr_desc(water.get('desc', ''))}\n"
                f"{self._tr('Eau profonde sous')} : {water.get('water_start')} m\n"
                f"{self._tr('Limite eau')} : {water.get('water_end')} m\n"
                f"{self._tr('Terre à partir de')} : {water.get('land_start')} m"
            )
        if inland:
            self.inland_detail_var.set(
                f"{self._tr('Détail')} : {self._tr_desc(inland.get('desc', ''))}\n"
                f"{self._tr('Largeur fusion terre')} : {inland.get('distance')} px\n"
                f"{self._tr('Force fusion terre')} : {inland.get('strength')}"
            )

    def _apply_sand_color_preset_to_rgb(self, force: bool = False) -> None:
        """Met à jour les champs RGB quand un preset couleur sable est choisi.

        En mode custom, on conserve les valeurs tapées par l'utilisateur.
        """
        preset = (self.sand_color_preset_var.get() or "belle_ile").strip()
        if preset == "custom":
            return

        values = SAND_COLOR_PRESETS.get(preset)
        if not values:
            return

        # Sur changement de preset, on remplace les codes couleur visibles.
        self.sand_dry_rgb_var.set(values["dry"])
        self.sand_wet_rgb_var.set(values["wet"])
        self.sand_shell_rgb_var.set(values["shell"])
        self.wet_beach_rgb_var.set(values["wet_beach"])
        self.seabed_rgb_var.set(values["seabed"])

    def _on_sand_color_preset_change(self) -> None:
        self._apply_sand_color_preset_to_rgb(force=True)
        self._refresh_rgb_previews()
        self._update_command_preview()

    def _apply_water_color_preset_to_rgb(self, force: bool = False) -> None:
        """Met à jour les champs RGB quand un preset couleur eau est choisi."""
        preset = (self.water_color_preset_var.get() or "atlantic_belle_ile").strip()
        if preset == "custom":
            return

        values = WATER_COLOR_PRESETS.get(preset)
        if not values:
            return

        self.water_deep_rgb_var.set(values["deep"])
        self.water_mid_rgb_var.set(values["mid"])
        self.water_shallow_rgb_var.set(values["shallow"])
        self.water_lagoon_rgb_var.set(values["lagoon"])
        self.water_surf_rgb_var.set(values["surf"])
        self.water_seabed_rgb_var.set(values["seabed"])

    def _on_water_color_preset_change(self) -> None:
        self._apply_water_color_preset_to_rgb(force=True)
        self._refresh_rgb_previews()
        self._update_command_preview()

    def _on_shore_profile_change(self) -> None:
        p = SHORE_PROFILES[self.shore_profile_var.get()]
        self.sand_distance_var.set(str(p["distance"]))
        self.sand_slope_var.set(str(p["slope"]))
        self.sand_height_var.set(str(p["height"]))
        self._update_profile_details()
        self._update_profile_combos()
        self._update_command_preview()

    def _on_water_profile_change(self) -> None:
        p = WATER_PROFILES[self.water_profile_var.get()]
        self.water_start_var.set(str(p["water_start"]))
        self.water_end_var.set(str(p["water_end"]))
        self.land_start_var.set(str(p["land_start"]))
        self._update_profile_details()
        self._update_profile_combos()
        self._update_command_preview()

    def _on_inland_profile_change(self) -> None:
        p = INLAND_PROFILES[self.inland_profile_var.get()]
        self.inland_distance_var.set(str(p["distance"]))
        self.inland_strength_var.set(str(p["strength"]))
        self._update_profile_details()
        self._update_profile_combos()
        self._update_command_preview()

    def _apply_profile_combo(self, shore: str, water: str, inland: str) -> None:
        """Applique un trio de profils et met à jour les champs numériques."""
        self.shore_profile_var.set(shore)
        self.water_profile_var.set(water)
        self.inland_profile_var.set(inland)
        self._on_shore_profile_change()
        self._on_water_profile_change()
        self._on_inland_profile_change()
        self._update_profile_combos()

    def _apply_recommended_profile(self) -> None:
        # Conservé pour compatibilité interne : le réglage recommandé par défaut est la référence validée.
        self._apply_reference_414_profile()

    def _apply_reference_414_profile(self) -> None:
        """Réglage de référence validé : profil côte 4 / eau 1 / terre 4."""
        self._apply_profile_combo("4 - Plage large", "1 - Standard", "4 - Net marqué")

    def _apply_natural_balanced_profile(self) -> None:
        """Réglage doux polyvalent : moins large que la référence, transition naturelle."""
        self._apply_profile_combo("3 - Équilibré", "1 - Standard", "3 - Net naturel")

    def _apply_low_coast_profile(self) -> None:
        """Réglage utile si la limite eau/terre est trop haute ou déborde légèrement."""
        self._apply_profile_combo("4 - Plage large", "2 - Littoral bas", "3 - Net naturel")

    def _apply_wide_clean_profile(self) -> None:
        """Réglage large mais propre, proche de la référence avec plus de plage."""
        self._apply_profile_combo("5 - Grande plage", "1 - Standard", "4 - Net marqué")

    def _apply_clean_edge_profile(self) -> None:
        """Réglage prudent pour un bord plus net et peu intrusif."""
        self._apply_profile_combo("2 - Bord naturel", "1 - Standard", "2 - Net léger")

    def _apply_sharp_profile(self) -> None:
        # Ancien bouton conservé si appelé ailleurs.
        self._apply_clean_edge_profile()

    def _apply_wide_soft_profile(self) -> None:
        """Grande plage avec retouche intérieure plus douce."""
        self._apply_profile_combo("5 - Grande plage", "1 - Standard", "3 - Net naturel")

    def _apply_strong_extension_profile(self) -> None:
        """Réglage fort pour tester une plage plus étendue."""
        self._apply_profile_combo("6 - Extension forte", "1 - Standard", "5 - Dune courte")

    def _float_value(self, var: StringVar, name: str, minimum: float | None = None, maximum: float | None = None) -> float:
        try:
            value = float(var.get().strip().replace(",", "."))
        except ValueError as exc:
            raise ValueError(f"{name} doit être un nombre valide.") from exc
        if minimum is not None and value < minimum:
            raise ValueError(f"{name} doit être >= {minimum}.")
        if maximum is not None and value > maximum:
            raise ValueError(f"{name} doit être <= {maximum}.")
        return value

    def _int_value(self, var: StringVar, name: str, minimum: int, maximum: int) -> int:
        value = int(self._float_value(var, name, minimum, maximum))
        return value

    def _build_command(self, validate_only: bool = False) -> list[str]:
        generator_raw = self.generator_var.get().strip().strip('"')
        if not generator_raw:
            raise FileNotFoundError(self._tr("Script introuvable : {path}", path=self._display_path(generator_raw)))
        generator = self._resolve_user_path(generator_raw)
        if not generator.exists() or not generator.is_file():
            raise FileNotFoundError(self._tr("Script introuvable : {path}", path=self._display_path(generator)))

        self._sync_texture_layer_vars()
        shore = SHORE_PROFILES[self.shore_profile_var.get()]
        target_size = self._int_value(self.target_size_var, "Résolution finale", 512, 30000)
        chunk_rows = self._int_value(self.chunk_rows_var, "Mémoire / vitesse", 64, 8192)
        block_size = self._int_value(self.block_size_var, "Taille variations couleur", 4, 512)
        if not self.beach_layers_var.get().strip():
            raise ValueError("Layers plage ne doit pas être vide.")
        if not self.sand_layers_var.get().strip():
            raise ValueError("Layers source sable ne doit pas être vide.")

        cmd = [
            sys.executable,
            "-u",
            str(generator),
            "--heightmap", str(self._resolve_user_path(self.heightmap_var.get())),
            "--mask", str(self._resolve_user_path(self.mask_var.get())),
            "--satmap", str(self._resolve_user_path(self.satmap_var.get())),
            "--layers", str(self._resolve_user_path(self.layers_var.get())),
            "--target-size", str(target_size),
            "--chunk-rows", str(chunk_rows),
            "--block-size", str(block_size),
            "--mask-color-tolerance", str(self._int_value(self.mask_color_tolerance_var, "Tolérance couleurs du mask", 0, 255)),
            "--surf-width", str(self._float_value(self.surf_width_var, "Épaisseur de l\'écume", 1.0, 128.0)),
            "--shallow-width-factor", str(self._float_value(self.shallow_width_factor_var, "Zone eau claire", 0.05, 5.0)),
            "--mid-width-factor", str(self._float_value(self.mid_width_factor_var, "Zone eau intermédiaire", 0.05, 5.0)),
            "--deep-width-factor", str(self._float_value(self.deep_width_factor_var, "Zone eau profonde", 0.05, 5.0)),
            "--foam-strength", str(self._float_value(self.foam_strength_var, "Intensité de l'écume", 0.0, 2.0)),
            "--wet-sand-width", str(self._float_value(self.wet_sand_width_var, "Largeur sable mouillé", 1.0, 128.0)),
            "--sand-preset", str(shore["key"]),
            "--sand-distance", str(self._float_value(self.sand_distance_var, "Largeur plage max", 1, 300)),
            "--sand-slope-max", str(self._float_value(self.sand_slope_var, "Pente autorisée", 0.01, 1.0)),
            "--sand-max-height", str(self._float_value(self.sand_height_var, "Hauteur plage max", 0.1, 50)),
            "--water-start-level", str(self._float_value(self.water_start_var, "Eau profonde sous", -100, 100)),
            "--water-end-level", str(self._float_value(self.water_end_var, "Limite eau", -100, 100)),
            "--land-start-level", str(self._float_value(self.land_start_var, "Terre à partir de", -100, 100)),
            "--land-pass-distance", str(self._float_value(self.inland_distance_var, "Largeur fusion terre", 0, 160)),
            "--land-pass-strength", str(self._float_value(self.inland_strength_var, "Force fusion terre", 0, 1)),
            "--beach-layer-names", self.beach_layers_var.get().strip(),
            "--sand-layer-names", self.sand_layers_var.get().strip(),
        ]
        land_layers = self.land_layers_var.get().strip()
        if land_layers:
            cmd.extend(["--land-layer-names", land_layers])

        sand_color_preset = self.sand_color_preset_var.get().strip() or "belle_ile"
        cmd.extend([
            "--sand-color-preset", sand_color_preset,
            "--sand-color-strength", str(self._float_value(self.sand_color_strength_var, "Intensité sable", 0.0, 1.5)),
        ])

        # Important :
        # Les arguments RGB sont des overrides dans le générateur.
        # Si on les envoie toujours, ils peuvent écraser le preset choisi.
        # On les envoie donc uniquement en mode custom.
        if sand_color_preset == "custom":
            cmd.extend([
                "--sand-dry-rgb", self.sand_dry_rgb_var.get().strip(),
                "--sand-wet-rgb", self.sand_wet_rgb_var.get().strip(),
                "--sand-shell-rgb", self.sand_shell_rgb_var.get().strip(),
                "--wet-beach-rgb", self.wet_beach_rgb_var.get().strip(),
                "--seabed-rgb", self.seabed_rgb_var.get().strip(),
            ])

        sand_texture_path = self.sand_texture_image_var.get().strip()
        if sand_texture_path:
            cmd.extend([
                "--sand-texture-image", str(self._resolve_user_path(sand_texture_path)),
                "--sand-texture-strength", str(self._float_value(self.sand_texture_strength_var, "Intensité texture", 0.0, 1.0)),
                "--sand-texture-scale", str(self._float_value(self.sand_texture_scale_var, "Taille texture", 0.1, 8.0)),
            ])

        water_color_preset = self.water_color_preset_var.get().strip() or "atlantic_belle_ile"
        cmd.extend([
            "--water-color-preset", water_color_preset,
            "--water-color-strength", str(self._float_value(self.water_color_strength_var, "Intensité eau", 0.0, 1.5)),
        ])
        if water_color_preset == "custom":
            cmd.extend([
                "--water-deep-rgb", self.water_deep_rgb_var.get().strip(),
                "--water-mid-rgb", self.water_mid_rgb_var.get().strip(),
                "--water-shallow-rgb", self.water_shallow_rgb_var.get().strip(),
                "--water-lagoon-rgb", self.water_lagoon_rgb_var.get().strip(),
                "--water-surf-rgb", self.water_surf_rgb_var.get().strip(),
                "--water-seabed-rgb", self.water_seabed_rgb_var.get().strip(),
            ])

        water_texture_path = self.water_texture_image_var.get().strip()
        if water_texture_path:
            cmd.extend([
                "--water-texture-image", str(self._resolve_user_path(water_texture_path)),
                "--water-texture-strength", str(self._float_value(self.water_texture_strength_var, "Intensité texture eau", 0.0, 1.0)),
                "--water-texture-scale", str(self._float_value(self.water_texture_scale_var, "Taille texture eau", 0.1, 8.0)),
                "--water-texture-smoothing", str(self._float_value(self.water_texture_smoothing_var, "Lissage eau", 0.0, 64.0)),
                "--water-texture-warp", str(self._float_value(self.water_texture_warp_var, "Anti-répétition eau", 0.0, 96.0)),
            ])
        if self.debug_masks_var.get():
            cmd.append("--debug-masks")
        if validate_only:
            cmd.append("--validate-only")
        return cmd

    def _format_cmd(self, cmd: list[str]) -> str:
        return " ".join(f'"{c}"' if " " in c else c for c in cmd)

    def _update_command_preview(self) -> None:
        try:
            self.cmd_preview_var.set(self._format_cmd_display(self._build_command()))
        except Exception as exc:
            self.cmd_preview_var.set(self._tr("Commande invalide : {error}", error=self._clean_log_text(str(exc))))

    def _expected_files(self) -> list[tuple[str, StringVar, bool]]:
        """Retourne les fichiers obligatoires de l'interface.

        Le booléen indique si le fichier est obligatoire pour lancer le script.
        Tous les fichiers ci-dessous sont obligatoires dans la version actuelle.
        """
        return [
            ("Script générateur", self.generator_var, True),
            ("Heightmap ASC", self.heightmap_var, True),
            ("Mask image", self.mask_var, True),
            ("Satmap image", self.satmap_var, True),
            ("Layers CFG", self.layers_var, True),
        ]

    def _missing_files(self, include_generator: bool = True) -> list[str]:
        missing: list[str] = []
        resolved_files: dict[str, Path] = {}

        expected_ext = {
            "Script générateur": {".py", ".pyw"},
            "Heightmap ASC": {".asc"},
            "Mask image": set(IMAGE_EXTENSIONS),
            "Satmap image": set(IMAGE_EXTENSIONS),
            "Layers CFG": {".cfg"},
        }

        for label, var, required in self._expected_files():
            if not include_generator and label == "Script générateur":
                continue

            value = var.get().strip().strip('"')
            if not value:
                missing.append(f"{label} : {self._tr('chemin vide')}")
                continue

            path = self._resolve_user_path(value)
            if not path.exists():
                missing.append(f"{label} : {self._display_path(path)}")
                continue

            if not path.is_file():
                missing.append(f"{label} : {self._tr('ce n\'est pas un fichier')} ({self._display_path(path)})")
                continue

            ext = path.suffix.lower()
            allowed_ext = expected_ext.get(label)
            if allowed_ext and ext not in allowed_ext:
                missing.append(
                    f"{label} : {self._tr('extension invalide')} `{ext or self._tr('aucune extension')}` "
                    f"{self._tr('attendu')} {', '.join(sorted(allowed_ext))} ({self._display_path(path)})"
                )
                continue

            if label == "Mask image" and ext in LOSSY_MASK_EXTENSIONS:
                try:
                    tolerance = float(self.mask_color_tolerance_var.get().strip().replace(",", "."))
                except Exception:
                    tolerance = 0.0
                if tolerance <= 0.0:
                    missing.append(
                        "Mask image : JPG/JPEG bloqué avec tolérance RGB à 0. "
                        "Utilise PNG/BMP/TIFF ou augmente la tolérance mask."
                    )

            resolved_files[label] = path.resolve()

        # Contrôle anti-erreur : chaque rôle obligatoire doit utiliser un fichier différent.
        seen: dict[str, str] = {}
        for label, path in resolved_files.items():
            key = str(path).lower()
            if key in seen:
                missing.append(
                    self._tr(
                        "Fichier dupliqué : {a} et {b} utilisent le même fichier ({path})",
                        a=seen[key],
                        b=label,
                        path=self._display_path(path),
                    )
                )
            else:
                seen[key] = label

        return missing

    def _reset_default_paths(self) -> None:
        # Réinitialisation : valeurs visuelles par défaut + détection automatique des inputs.
        self.generator_var.set(self._auto_detect_file([GENERATOR_NAME, "satmap_generator_optimized_presets"], (".py", ".pyw"), include_input=False))
        self.heightmap_var.set(self._auto_detect_file(["heightmap"], (".asc",), include_input=True))
        self.mask_var.set(self._auto_detect_file(["mask"], IMAGE_EXTENSIONS, include_input=True))
        self.satmap_var.set(self._auto_detect_file(["satmap"], IMAGE_EXTENSIONS, include_input=True))
        self.layers_var.set(self._auto_detect_file(["layers"], (".cfg",), include_input=True))
        self.beach_vanilla_var.set(self._texture_none_label())
        self.beach_custom_var.set("hp_beach")
        self.sand_vanilla_var.set(self._texture_none_label())
        self.sand_custom_var.set("hp_sand")
        self.land_vanilla_var.set(self._texture_none_label())
        self.land_custom_var.set("")
        self.sand_color_preset_var.set("belle_ile")
        self.sand_color_strength_var.set("1.0")
        self.sand_dry_rgb_var.set("222,204,178")
        self.sand_wet_rgb_var.set("190,168,145")
        self.sand_shell_rgb_var.set("208,196,182")
        self.wet_beach_rgb_var.set("181,156,128")
        self.seabed_rgb_var.set("160,120,90")
        self.sand_texture_image_var.set("")
        self.sand_texture_strength_var.set("0.45")
        self.sand_texture_scale_var.set("1.0")
        self.water_color_preset_var.set("atlantic_belle_ile")
        self.water_color_strength_var.set("1.0")
        self.water_deep_rgb_var.set("58,88,122")
        self.water_mid_rgb_var.set("70,112,142")
        self.water_shallow_rgb_var.set("93,149,156")
        self.water_lagoon_rgb_var.set("118,181,174")
        self.water_surf_rgb_var.set("156,202,190")
        self.water_seabed_rgb_var.set("160,120,90")
        self.water_texture_image_var.set("")
        self.water_texture_strength_var.set("0.25")
        self.water_texture_scale_var.set("1.0")
        self.water_texture_smoothing_var.set("12.0")
        self.water_texture_warp_var.set("18.0")
        self._sync_texture_layer_vars()
        self._refresh_status()
        self._append_log(f"[INFO] {self._tr('Chemins réinitialisés : tous les chemins de fichiers sont maintenant vides.')}\n")

    def _parse_layers_cfg_names(self, path: Path) -> set[str]:
        """Retourne les noms de layers déclarés dans layers.cfg.

        Supporte :
        - class layer_name {
        - layer_name[] = {{r,g,b}};
        """
        content = path.read_text(encoding="utf-8", errors="ignore")
        names: set[str] = set()

        for match in re.findall(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{", content):
            if match.lower() not in {"layers", "legend", "colors"}:
                names.add(match)

        for match in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\[\]\s*=\s*\{\{", content):
            if match.lower() not in {"layers", "legend", "colors"}:
                names.add(match)

        return names

    def _selected_texture_names(self) -> dict[str, list[str]]:
        self._sync_texture_layer_vars()
        return {
            self._tr("Texture déjà plage"): [
                part.strip() for part in self.beach_layers_var.get().split(",") if part.strip()
            ],
            self._tr("Texture sable à agrandir"): [
                part.strip() for part in self.sand_layers_var.get().split(",") if part.strip()
            ],
            self._tr("Texture terre à mélanger"): [
                part.strip() for part in self.land_layers_var.get().split(",") if part.strip()
            ],
        }

    def _verify_layers_textures(self) -> None:
        layers_value = self.layers_var.get().strip().strip('"')
        if not layers_value:
            messagebox.showwarning(
                self._tr("Vérifier textures layers.cfg"),
                self._tr("Chemin layers.cfg vide. Sélectionne d'abord un fichier layers.cfg.")
            )
            self._append_log(f"[WARNING] {self._tr('Vérification textures impossible : chemin layers.cfg vide.')}\\n")
            return

        layers_path = self._resolve_user_path(layers_value)
        if not layers_path.exists() or not layers_path.is_file():
            messagebox.showwarning(
                self._tr("Vérifier textures layers.cfg"),
                self._tr("Fichier layers.cfg introuvable ou invalide.")
            )
            self._append_log(f"[ERROR] {self._tr('Fichier layers.cfg introuvable ou invalide.')} {self._display_path(layers_path)}\\n")
            return

        try:
            available = self._parse_layers_cfg_names(layers_path)
        except Exception as exc:
            messagebox.showerror(
                self._tr("Vérifier textures layers.cfg"),
                self._tr("Erreur lecture layers.cfg : {error}", error=exc)
            )
            self._append_log(f"[ERROR] {self._tr('Erreur lecture layers.cfg : {error}', error=exc)}\\n")
            return

        available_lower = {name.lower(): name for name in available}
        groups = self._selected_texture_names()

        lines: list[str] = []
        log_lines: list[str] = []
        missing_required = False

        for group_name, names in groups.items():
            lines.append(f"{group_name} :")
            if not names:
                if group_name == self._tr("Texture terre à mélanger"):
                    lines.append(f"  {self._tr('INFO : vide, option non utilisée.')}")
                    log_lines.append(f"[INFO] {group_name} : {self._tr('vide, option non utilisée.')}")
                else:
                    lines.append(f"  {self._tr('ERROR : aucune texture renseignée.')}")
                    log_lines.append(f"[ERROR] {group_name} : {self._tr('aucune texture renseignée.')}")
                    missing_required = True
                lines.append("")
                continue

            for name in names:
                if name.lower() in available_lower:
                    lines.append(f"  OK : {name}")
                    log_lines.append(f"[OK] {group_name} : {name}")
                else:
                    lines.append(f"  WARNING : {name} {self._tr('introuvable dans layers.cfg')}")
                    log_lines.append(f"[WARNING] {group_name} : {name} {self._tr('introuvable dans layers.cfg')}")
                    if group_name != self._tr("Texture terre à mélanger"):
                        missing_required = True
            lines.append("")

        lines.append(self._tr("Textures détectées dans layers.cfg : {count}", count=len(available)))
        if available:
            preview = ", ".join(sorted(available)[:80])
            lines.append(preview)
            if len(available) > 80:
                lines.append(self._tr("... liste tronquée"))

        report = "\n".join(lines)
        for line in log_lines:
            self._append_log(line + "\n")

        if missing_required:
            messagebox.showwarning(self._tr("Vérifier textures layers.cfg"), report)
        else:
            messagebox.showinfo(self._tr("Vérifier textures layers.cfg"), report)

    def _show_missing_files(self) -> None:
        missing = self._missing_files(include_generator=True)
        if not missing:
            messagebox.showinfo(self._tr("Vérification"), self._tr("Tous les fichiers obligatoires sont présents."))
            return
        messagebox.showwarning(self._tr("Fichiers manquants"), self._tr("Fichiers manquants ou chemins invalides :\n\n") + "\n".join(missing))

    def _refresh_status(self) -> None:
        missing = self._missing_files(include_generator=True)
        if missing:
            self.status_var.set(
                self._tr("ATTENTION : fichier obligatoire manquant ou invalide - ")
                + " | ".join(missing[:2])
                + (" ..." if len(missing) > 2 else "")
            )
            self._start_status_blink("red")
            if hasattr(self, "run_button"):
                self.run_button.config(state=DISABLED)
        else:
            self.status_var.set(self._tr("Tous les fichiers obligatoires sont présents."))
            self._start_status_blink("green")
            if hasattr(self, "run_button") and not self._is_running:
                self.run_button.config(state=NORMAL)
        self._update_command_preview()

    def _set_progress(self, value: int, detail: str | None = None) -> None:
        value = max(0, min(100, int(value)))
        self._progress_value = value

        def apply() -> None:
            self.progress_var.set(f"{value}%")
            if hasattr(self, "progress_bar"):
                self.progress_bar["value"] = value
            if self._is_running:
                base = f"{self._tr('Génération en cours...')} {value}%"
                self.status_var.set(base if not detail else f"{base} - {self._tr(detail)}")

        self.after(0, apply)

    def _progress_from_output(self, line: str) -> None:
        stripped = line.strip()
        if stripped.startswith("PROGRESS|"):
            parts = stripped.split("|", 2)
            if len(parts) == 3:
                try:
                    self._set_progress(int(parts[1]), parts[2])
                    return
                except Exception:
                    pass
        l = stripped.lower()
        mapping = [
            ("lecture layers.cfg", 5, "Lecture des couches"),
            ("chargement heightmap", 10, "Chargement heightmap"),
            ("resize heightmap", 16, "Redimensionnement heightmap"),
            ("chargement mask", 24, "Chargement masque"),
            ("chargement satmap", 32, "Chargement satmap"),
            ("calcul pente", 40, "Calcul de pente"),
            ("extension locale", 46, "Extension zone sable"),
            ("détection zones sous 0m", 52, "Détection niveaux eau"),
            ("distance au rivage", 60, "Calcul distance au rivage"),
            ("création bruit multi-échelle", 68, "Création du bruit"),
            ("construction vectorisée des catégories", 74, "Construction des catégories"),
            ("correction vectorisée de la satmap", 78, "Correction satmap"),
            ("application vectorisée eau / fond marin / plage", 82, "Application eau / plage"),
            ("contouring", 82, "Application eau / plage"),
            ("deuxième passe côté terre", 88, "Application côté terre"),
            ("génération hp_beach + hp_sand", 90, "Génération rivage"),
            ("génération textures plage + sable", 90, "Génération rivage"),
            ("création beach mask", 94, "Création beach mask"),
            ("sauvegarde beach mask", 97, "Sauvegarde beach mask"),
            ("sauvegarde satmap", 98, "Sauvegarde satmap"),
            ("terminé.", 100, "Terminé"),
        ]
        for key, pct, detail in mapping:
            if key in l and pct >= self._progress_value:
                self._set_progress(pct, detail)
                break

    def _log_tag_for(self, text: str) -> str:
        lower = text.lower()
        if "erreur" in lower or "failed" in lower or "échoué" in lower or "traceback" in lower or "[error]" in lower:
            return "error"
        if "attention" in lower or "warning" in lower or "[warning]" in lower:
            return "warning"
        if "terminé" in lower or "[ok]" in lower or "code 0" in lower:
            return "ok"
        if lower.startswith(("lecture", "chargement", "resize", "calcul", "distance", "création", "construction", "correction", "application", "sauvegarde", "contouring", "deuxième", "génération")):
            return "step"
        return "info"

    def _clean_log_text(self, text: str) -> str:
        cleaned = text
        try:
            root = str(self.root_dir.resolve())
            cleaned = cleaned.replace(root, ".")
            cleaned = cleaned.replace(root.replace("/", "\\"), ".")
            home = str(Path.home().resolve())
            cleaned = cleaned.replace(home, "~")
            cleaned = cleaned.replace(home.replace("/", "\\"), "~")
            # Masque les chemins Windows restants de type C:\\Users\\Nom\\...
            cleaned = re.sub(r"[A-Za-z]:\\\\Users\\\\[^\\\\\r\n]+", "~", cleaned)
            # Masque les chemins absolus externes trop longs, tout en gardant le nom de fichier.
            cleaned = re.sub(
                r"([A-Za-z]:\\\\(?:[^\\\\\r\n]+\\\\)+)([^\\\\\r\n]+\.[A-Za-z0-9_]+)",
                r"[chemin externe]\\\\\2",
                cleaned,
            )
        except Exception:
            pass
        return cleaned

    def _append_log(self, text: str) -> None:
        text = self._clean_log_text(text)
        text = self._translate_generator_line(text)
        tag = self._log_tag_for(text.strip())
        def write() -> None:
            self.log_text.insert(END, text, tag)
            self.log_text.see(END)
        self.after(0, write)

    def _set_running(self, running: bool) -> None:
        self._is_running = running
        if running:
            self._stop_status_blink()
            self.status_label.configure(foreground="black")
            self.run_button.config(state=DISABLED)
            if hasattr(self, "diagnostic_button"):
                self.diagnostic_button.config(state=DISABLED)
            self.stop_button.config(state=NORMAL)
            self._set_progress(0, self._tr("Démarrage"))
        else:
            self.run_button.config(state=NORMAL)
            if hasattr(self, "diagnostic_button"):
                self.diagnostic_button.config(state=NORMAL)
            self.stop_button.config(state=DISABLED)
            if hasattr(self, "progress_bar"):
                self.progress_bar["value"] = self._progress_value
            self._refresh_status()


    def _settings_summary_markdown(self, cmd: list[str], output_dir: Path | None) -> str:
        """Crée le rapport de génération dans la langue actuellement sélectionnée."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shore_name = self.shore_profile_var.get()
        water_name = self.water_profile_var.get()
        inland_name = self.inland_profile_var.get()
        shore_desc = self._tr_desc(SHORE_PROFILES.get(shore_name, {}).get("desc", ""))
        water_desc = self._tr_desc(WATER_PROFILES.get(water_name, {}).get("desc", ""))
        inland_desc = self._tr_desc(INLAND_PROFILES.get(inland_name, {}).get("desc", ""))

        output_text = self._display_path(output_dir) if output_dir else self._tr("Dossier output non détecté automatiquement")
        duration_text = self._tr("non disponible")
        if self.last_start_time is not None:
            duration_seconds = max(0, int((datetime.now() - self.last_start_time).total_seconds()))
            minutes, seconds = divmod(duration_seconds, 60)
            if self._current_lang() == "en":
                duration_text = f"{minutes} min {seconds:02d} sec"
            elif self._current_lang() == "ru":
                duration_text = f"{minutes} мин {seconds:02d} сек"
            else:
                duration_text = f"{minutes} min {seconds:02d} sec"

        title = {
            "fr": "# Rapport complet de génération Satmap",
            "en": "# Complete Satmap generation report",
            "ru": "# Полный отчёт генерации Satmap",
        }.get(self._current_lang(), "# Rapport complet de génération Satmap")

        lines = [
            title,
            "",
            f"{self._tr('Date de génération')} : `{now}`",
            f"{self._tr('Durée totale')} : `{duration_text}`",
            f"{self._tr('Version launcher')} : `{APP_VERSION}`",
            f"{self._tr('Version générateur attendue')} : `{GENERATOR_EXPECTED_VERSION}`",
            f"{self._tr('Langue du rapport')} : `{self.language_var.get()}`",
            f"{self._tr('Dossier de sortie')} : `{output_text}`",
            "",
            f"## {self._tr('Fichiers source')}",
            "",
            f"- {self._tr('Script générateur')} : `{self._display_path(self.generator_var.get().strip())}`",
            f"- Heightmap ASC : `{self._display_path(self.heightmap_var.get().strip())}`",
            f"- {self._tr('Mask image')} : `{self._display_path(self.mask_var.get().strip())}`",
            f"- {self._tr('Satmap image')} : `{self._display_path(self.satmap_var.get().strip())}`",
            f"- Layers CFG : `{self._display_path(self.layers_var.get().strip())}`",
            "",
            f"## {self._tr('Textures DayZ à reconnaître')}",
            "",
            f"- {self._tr('Texture déjà plage')} : `{self.beach_layers_var.get().strip()}`",
            f"- {self._tr('Texture sable à agrandir')} : `{self.sand_layers_var.get().strip()}`",
            f"- {self._tr('Texture terre à mélanger')} : `{self.land_layers_var.get().strip() or self._tr('non utilisé')}`",
            f"- {self._tr('Mode textures')} : `{self._tr('liste vanilla DayZ + champ custom manuel')}`",
            "",
            f"## {self._tr('Couleurs du sable')}",
            "",
            f"- {self._tr('Type de sable')} : `{self.sand_color_preset_var.get()}`",
            f"- {self._tr('Intensité sable')} : `{self.sand_color_strength_var.get()}`",
            f"- {self._tr('Sable sec')} : `{self.sand_dry_rgb_var.get()}`",
            f"- {self._tr('Sable mouillé')} : `{self.sand_wet_rgb_var.get()}`",
            f"- {self._tr('Sable clair / coquillages')} : `{self.sand_shell_rgb_var.get()}`",
            f"- {self._tr('Bord mouillé')} : `{self.wet_beach_rgb_var.get()}`",
            f"- {self._tr('Fond sableux')} : `{self.seabed_rgb_var.get()}`",
            f"- {self._tr('Texture sable')} : `{self.sand_texture_image_var.get() or self._tr('non utilisé')}`",
            f"- {self._tr('Intensité texture')} : `{self.sand_texture_strength_var.get()}`",
            f"- {self._tr('Taille texture')} : `{self.sand_texture_scale_var.get()}`",
            "",
            "## " + self._tr("Couleurs de l'eau"),
            "",
            "- " + self._tr("Type d'eau") + f" : `{self.water_color_preset_var.get()}`",
            f"- {self._tr('Intensité eau')} : `{self.water_color_strength_var.get()}`",
            f"- {self._tr('Eau profonde')} : `{self.water_deep_rgb_var.get()}`",
            f"- {self._tr('Eau intermédiaire')} : `{self.water_mid_rgb_var.get()}`",
            f"- {self._tr('Eau peu profonde')} : `{self.water_shallow_rgb_var.get()}`",
            f"- {self._tr('Eau très claire')} : `{self.water_lagoon_rgb_var.get()}`",
            f"- {self._tr('Écume / ressac')} : `{self.water_surf_rgb_var.get()}`",
            "- " + self._tr("Fond sous l'eau") + f" : `{self.water_seabed_rgb_var.get()}`",
            f"- {self._tr('Texture eau')} : `{self.water_texture_image_var.get() or self._tr('non utilisé')}`",
            f"- {self._tr('Intensité texture eau')} : `{self.water_texture_strength_var.get()}`",
            f"- {self._tr('Taille texture eau')} : `{self.water_texture_scale_var.get()}`",
            f"- {self._tr('Lissage eau')} : `{self.water_texture_smoothing_var.get()}`",
            f"- {self._tr('Anti-répétition eau')} : `{self.water_texture_warp_var.get()}`",
            "",
            f"## {self._tr('Plage : taille et pente')}",
            "",
            f"- {self._tr('Profil')} : `{self._profile_label(shore_name)}`",
            f"- {self._tr('Description')} : {shore_desc}",
            f"- {self._tr('Largeur plage max')} : `{self.sand_distance_var.get()}` px",
            f"- {self._tr('Pente autorisée')} : `{self.sand_slope_var.get()}`",
            f"- {self._tr('Hauteur plage max')} : `{self.sand_height_var.get()}` m",
            "",
            "## " + self._tr("Eau : niveaux d'altitude"),
            "",
            f"- {self._tr('Profil')} : `{self._profile_label(water_name)}`",
            f"- {self._tr('Description')} : {water_desc}",
            f"- {self._tr('Eau profonde sous')} : `{self.water_start_var.get()}` m",
            "- " + self._tr("Limite eau") + f" : `{self.water_end_var.get()}` m",
            f"- {self._tr('Terre à partir de')} : `{self.land_start_var.get()}` m",
            "",
            f"## {self._tr('Fusion sable → terre')}",
            "",
            f"- {self._tr('Profil')} : `{self._profile_label(inland_name)}`",
            f"- {self._tr('Description')} : {inland_desc}",
            f"- {self._tr('Largeur fusion terre')} : `{self.inland_distance_var.get()}` px",
            f"- {self._tr('Force fusion terre')} : `{self.inland_strength_var.get()}`",
            "",
            f"## {self._tr('Réglages moteur')}",
            "",
            f"- {self._tr('Résolution finale')} : `{self.target_size_var.get()}`",
            f"- {self._tr('Mémoire / vitesse')} : `{self.chunk_rows_var.get()}`",
            f"- {self._tr('Taille variations couleur')} : `{self.block_size_var.get()}`",
            "",
            f"## {self._tr('Commande utilisée')}",
            "",
            "```bat",
            self._format_cmd(cmd),
            "```",
            "",
            f"## {self._tr('Fichiers générés attendus')}",
            "",
            "- `satmap_final_10240.png`",
            "- `beach_mask_10240.png`",
            f"- `{self._tr('RAPPORT_GENERATION_COMPLET.md')}`",
            "",
        ]
        return "\n".join(lines)

    def _latest_output_dir(self) -> Path | None:
        """Retourne le dernier dossier output_Vx créé/modifié."""
        outputs = self.root_dir / DEFAULT_OUTPUT_DIR
        if not outputs.exists():
            return None
        candidates = [p for p in outputs.iterdir() if p.is_dir() and p.name.lower().startswith("output_v")]
        if not candidates:
            return outputs
        return max(candidates, key=lambda p: p.stat().st_mtime)

    def _write_output_readme(self, cmd: list[str]) -> None:
        """Écrit le rapport complet uniquement dans le dossier output_Vx de la génération."""
        output_dir = self._latest_output_dir()
        if output_dir is None or output_dir == self.root_dir / DEFAULT_OUTPUT_DIR:
            self._append_log(f"[WARNING] {self._tr('Aucun dossier output_Vx détecté pour écrire le rapport complet.')}\n")
            return

        content = self._settings_summary_markdown(cmd, output_dir)
        output_dir.mkdir(exist_ok=True)
        report_path = output_dir / self._tr("RAPPORT_GENERATION_COMPLET.md")
        report_path.write_text(content, encoding="utf-8")
        self._append_log(f"[OK] {self._tr('Rapport complet créé')} : {self._display_path(report_path)}\n")

    def _start_generation(self) -> None:
        if self.process is not None:
            messagebox.showwarning(self._tr("Déjà en cours"), self._tr("Une génération est déjà en cours."))
            return
        try:
            cmd = self._build_command()
        except Exception as exc:
            messagebox.showerror("Erreur de configuration", str(exc))
            return

        # Vérification finale identique à l'onglet Fichiers.
        # Les chemins relatifs sont bien résolus depuis le dossier du launcher.
        missing = self._missing_files(include_generator=False)
        if missing:
            messagebox.showerror(
                self._tr("Fichiers manquants"),
                self._tr("Fichiers manquants ou chemins invalides :\n\n") + "\n".join(missing)
            )
            return

        self.notebook.select(self.tab_output)
        self._append_log("\n" + "=" * 80 + "\n")
        self._append_log("[INFO] Lancement de la génération\n")
        self._append_log(self._format_cmd_display(cmd) + "\n\n")
        self.last_command = cmd
        self.last_start_time = datetime.now()
        self._progress_value = 0
        self.progress_var.set("0%")
        self._set_running(True)
        self.worker = threading.Thread(target=self._run_generation_thread, args=(cmd,), daemon=True)
        self.worker.start()


    def _start_diagnostic(self) -> None:
        if self.process is not None:
            messagebox.showwarning(self._tr("Déjà en cours"), self._tr("Une génération est déjà en cours."))
            return
        try:
            cmd = self._build_command(validate_only=True)
        except Exception as exc:
            messagebox.showerror("Erreur de configuration", str(exc))
            return

        self._run_mode = "diagnostic"
        self._save_launcher_settings()
        self.notebook.select(self.tab_output)
        self._append_log("\n" + "=" * 80 + "\n")
        self._append_log("[INFO] Diagnostic complet\n")
        self._append_log(self._format_cmd_display(cmd) + "\n\n")
        self.last_command = cmd
        self.last_start_time = datetime.now()
        self._progress_value = 0
        self.progress_var.set("0%")
        if hasattr(self, "progress_bar"):
            self.progress_bar["value"] = 0
        self._set_running(True)
        self.worker = threading.Thread(target=self._run_generation_thread, args=(cmd,), daemon=True)
        self.worker.start()

    def _run_generation_thread(self, cmd: list[str]) -> None:
        code = -1
        try:
            env = os.environ.copy()
            # Force le sous-process Python à écrire en UTF-8 dans le pipe.
            # Cela évite les caractères cassés dans le journal Tkinter sur Windows.
            env["PYTHONUTF8"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUNBUFFERED"] = "1"
            self.process = subprocess.Popen(
                cmd,
                cwd=self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=env,
            )
            assert self.process.stdout is not None
            for line in self.process.stdout:
                self._append_log(line)
                self._progress_from_output(line)
            code = self.process.wait()
        except Exception as exc:
            self._append_log(f"\nErreur : {exc}\n")
        finally:
            self.process = None
            self.after(0, lambda: self._finish_generation(code))

    def _finish_generation(self, code: int) -> None:
        self._set_running(False)
        if code == 0:
            self._progress_value = 100
            self.progress_var.set("100%")
            if hasattr(self, "progress_bar"):
                self.progress_bar["value"] = 100
            if self._run_mode == "diagnostic":
                self.status_var.set("Diagnostic terminé. 100%")
                self._append_log("\n[OK] Diagnostic terminé.\n")
            else:
                self.status_var.set(f"{self._tr('Génération terminée.')} 100%")
                self._append_log("\n[OK] Génération terminée.\n")
                if self.open_outputs_var.get():
                    self._open_outputs()
        else:
            label = "Le diagnostic a échoué." if self._run_mode == "diagnostic" else self._tr("La génération a échoué.")
            self.status_var.set(f"{label} {self._progress_value}%")
            self._append_log(f"\n[ERROR] {label} Code : {code}\n")

    def _stop_generation(self) -> None:
        if self.process is not None:
            if messagebox.askyesno("Arrêter", "Arrêter la génération en cours ?"):
                self.process.terminate()
                self._append_log("\n[WARNING] Arrêt demandé par l'utilisateur.\n")


if __name__ == "__main__":
    app = SatmapGui()
    app.mainloop()
