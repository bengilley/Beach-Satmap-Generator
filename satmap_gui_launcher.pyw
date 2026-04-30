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
from tkinter import Tk, StringVar, BooleanVar, Text
from tkinter.ttk import Button, Checkbutton, Combobox, Entry, Frame, Label, LabelFrame, Notebook, Progressbar, Scrollbar, Spinbox

APP_TITLE = "Beach Satmap Generator"
APP_VERSION = "1.2.6"
GENERATOR_EXPECTED_VERSION = "1.1.0"
CUSTOM_PRESETS_FILE = "custom_profiles.json"
LAUNCHER_SETTINGS_FILE = "launcher_settings.json"
GENERATOR_NAME = "satmap_generator_optimized_presets.py"

DEFAULT_INPUT_DIR = "input"
DEFAULT_OUTPUT_DIR = "outputs"


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
        "Mask PNG": "Mask PNG",
        "Satmap PNG": "Satmap PNG",
        "Layers CFG": "Layers CFG",
        "Parcourir": "Browse",
        "Textures utilisées dans layers.cfg": "Textures used in layers.cfg",
        "Type": "Type",
        "Texture vanilla DayZ": "Vanilla DayZ texture",
        "Texture custom / mod": "Custom / mod texture",
        "Plage / littoral existant": "Existing beach / coastline",
        "Sable source à étendre": "Source sand to extend",
        "Terre cible côté intérieur": "Target inland texture",
        "ex vanilla : sa_beach | custom : hp_beach,my_beach": "ex vanilla: sa_beach | custom: hp_beach,my_beach",
        "ex vanilla : cp_gravel | custom : hp_sand,my_sand": "ex vanilla: cp_gravel | custom: hp_sand,my_sand",
        "optionnel | ex : cp_grass ou custom_grass": "optional | ex: cp_grass or custom_grass",
        "Choisis une texture vanilla DayZ dans la liste, puis ajoute si besoin une ou plusieurs textures custom à la main. Les deux seront combinées automatiquement. Les customs peuvent être séparées par des virgules. Terre vide = comportement précédent.": "Choose a vanilla DayZ texture from the list, then add one or more custom textures manually if needed. Both are combined automatically. Custom names can be separated with commas. Empty inland texture = previous behavior.",
        "Actions rapides": "Quick actions",
        "Créer input / outputs": "Create input / outputs",
        "Installer dépendances": "Install dependencies",
        "Ouvrir dossier du script": "Open script folder",
        "Réinitialiser chemins": "Reset paths",
        "Fichiers attendus par défaut : input/heightmap.asc, input/mask.png, input/satmap.png, input/layers.cfg": "Default expected files: input/heightmap.asc, input/mask.png, input/satmap.png, input/layers.cfg",
        "Profil zone côtière": "Coastal zone profile",
        "Profil seuils d'altitude": "Altitude thresholds profile",
        "Profil transition intérieure": "Inland transition profile",
        "Distance sable px": "Sand distance px",
        "Pente max": "Max slope",
        "Hauteur max m": "Max height m",
        "Eau forte sous m": "Strong water below m",
        "Eau jusqu'à m": "Water up to m",
        "Terre dès m": "Land from m",
        "Distance retouche px": "Retouch distance px",
        "Force retouche": "Retouch strength",
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
        "Détail complet des profils": "Full profile details",
        "Paramètres techniques": "Technical settings",
        "Taille finale": "Final size",
        "Lignes par chunk": "Chunk rows",
        "Taille blocs couleur": "Color block size",
        "Ouvrir le dossier outputs à la fin": "Open outputs folder when finished",
        "Lignes par chunk - observations RAM": "Chunk rows - RAM observations",
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
        "Mask PNG": "Mask PNG",
        "Satmap PNG": "Satmap PNG",
        "Layers CFG": "Layers CFG",
        "Parcourir": "Обзор",
        "Textures utilisées dans layers.cfg": "Текстуры из layers.cfg",
        "Type": "Тип",
        "Texture vanilla DayZ": "Vanilla-текстура DayZ",
        "Texture custom / mod": "Custom / mod текстура",
        "Plage / littoral existant": "Существующий пляж / берег",
        "Sable source à étendre": "Исходный песок для расширения",
        "Terre cible côté intérieur": "Целевая земля внутри",
        "ex vanilla : sa_beach | custom : hp_beach,my_beach": "пример vanilla: sa_beach | custom: hp_beach,my_beach",
        "ex vanilla : cp_gravel | custom : hp_sand,my_sand": "пример vanilla: cp_gravel | custom: hp_sand,my_sand",
        "optionnel | ex : cp_grass ou custom_grass": "опционально | пример: cp_grass или custom_grass",
        "Choisis une texture vanilla DayZ dans la liste, puis ajoute si besoin une ou plusieurs textures custom à la main. Les deux seront combinées automatiquement. Les customs peuvent être séparées par des virgules. Terre vide = comportement précédent.": "Выберите vanilla-текстуру DayZ из списка, затем при необходимости добавьте одну или несколько custom-текстур вручную. Они будут объединены автоматически. Custom-текстуры можно разделять запятыми. Пустая внутренняя земля = прежнее поведение.",
        "Actions rapides": "Быстрые действия",
        "Créer input / outputs": "Создать input / outputs",
        "Installer dépendances": "Установить зависимости",
        "Ouvrir dossier du script": "Открыть папку скрипта",
        "Réinitialiser chemins": "Сбросить пути",
        "Fichiers attendus par défaut : input/heightmap.asc, input/mask.png, input/satmap.png, input/layers.cfg": "Файлы по умолчанию: input/heightmap.asc, input/mask.png, input/satmap.png, input/layers.cfg",
        "Profil zone côtière": "Профиль береговой зоны",
        "Profil seuils d'altitude": "Профиль высотных порогов",
        "Profil transition intérieure": "Профиль перехода к суше",
        "Distance sable px": "Дистанция песка px",
        "Pente max": "Макс. уклон",
        "Hauteur max m": "Макс. высота м",
        "Eau forte sous m": "Сильная вода ниже м",
        "Eau jusqu'à m": "Вода до м",
        "Terre dès m": "Суша от м",
        "Distance retouche px": "Дистанция ретуши px",
        "Force retouche": "Сила ретуши",
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
        "Détail complet des profils": "Полное описание профилей",
        "Paramètres techniques": "Технические параметры",
        "Taille finale": "Финальный размер",
        "Lignes par chunk": "Строк на chunk",
        "Taille blocs couleur": "Размер цветовых блоков",
        "Ouvrir le dossier outputs à la fin": "Открыть outputs после завершения",
        "Lignes par chunk - observations RAM": "Строки chunk — наблюдения RAM",
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
        "RAPPORT_GENERATION_COMPLET.md": "ПОЛНЫЙ_ОТЧЕТ_ГЕНЕРАЦИИ.md",
    },
}


# Compléments i18n utilisés par les textes dynamiques.
UI_TRANSLATIONS["en"].update({
    "Détail": "Detail",
    "Distance sable": "Sand distance",
    "Hauteur max": "Max height",
    "Eau forte sous": "Strong water below",
    "Eau jusqu'à": "Water up to",
    "Terre / plage dès": "Land / beach from",
    "Distance retouche": "Retouch distance",
    "Force retouche": "Retouch strength",
})
UI_TRANSLATIONS["ru"].update({
    "Détail": "Детали",
    "Distance sable": "Дистанция песка",
    "Hauteur max": "Макс. высота",
    "Eau forte sous": "Сильная вода ниже",
    "Eau jusqu'à": "Вода до",
    "Terre / plage dès": "Суша / пляж от",
    "Distance retouche": "Дистанция ретуши",
    "Force retouche": "Сила ретуши",
})
UI_TRANSLATIONS["en"].update({
    "PROFIL ZONE CÔTIÈRE": "COASTAL ZONE PROFILE",
    "PROFIL SEUILS D'ALTITUDE": "ALTITUDE THRESHOLD PROFILE",
    "PROFIL TRANSITION INTÉRIEURE": "INLAND TRANSITION PROFILE",
    "distance": "distance",
    "pente": "slope",
    "hauteur": "height",
    "eau forte": "strong water",
    "eau": "water",
    "terre": "land",
    "force": "strength",
})
UI_TRANSLATIONS["ru"].update({
    "PROFIL ZONE CÔTIÈRE": "ПРОФИЛЬ БЕРЕГОВОЙ ЗОНЫ",
    "PROFIL SEUILS D'ALTITUDE": "ПРОФИЛЬ ВЫСОТНЫХ ПОРОГОВ",
    "PROFIL TRANSITION INTÉRIEURE": "ПРОФИЛЬ ПЕРЕХОДА К СУШЕ",
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
    "Paramètres techniques": "Technical settings",
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
    "Paramètres techniques": "Технические параметры",
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

PROFILE_LABELS = {
    "1 - Bord net": {"en": "1 - Sharp edge", "ru": "1 - Чёткий край"},
    "2 - Bord naturel": {"en": "2 - Natural edge", "ru": "2 - Естественный край"},
    "3 - Équilibré": {"en": "3 - Balanced", "ru": "3 - Сбалансированный"},
    "4 - Plage large": {"en": "4 - Wide beach", "ru": "4 - Широкий пляж"},
    "5 - Grande plage": {"en": "5 - Large beach", "ru": "5 - Большой пляж"},
    "6 - Extension forte": {"en": "6 - Strong extension", "ru": "6 - Сильное расширение"},
    "7 - Extension max": {"en": "7 - Max extension", "ru": "7 - Максимальное расширение"},
    "8 - Personnalisé": {"en": "8 - Custom", "ru": "8 - Пользовательский"},

    "1 - Standard": {"en": "1 - Standard", "ru": "1 - Стандарт"},
    "2 - Littoral bas": {"en": "2 - Low coastline", "ru": "2 - Низкий берег"},
    "3 - Eau plus large": {"en": "3 - Wider water", "ru": "3 - Больше воды"},
    "4 - Personnalisé": {"en": "4 - Custom", "ru": "4 - Пользовательский"},

    "1 - Désactivé": {"en": "1 - Disabled", "ru": "1 - Отключено"},
    "2 - Net léger": {"en": "2 - Light sharp", "ru": "2 - Лёгкая чёткость"},
    "3 - Net naturel": {"en": "3 - Natural sharp", "ru": "3 - Естественная чёткость"},
    "4 - Net marqué": {"en": "4 - Strong sharp", "ru": "4 - Выраженная чёткость"},
    "5 - Dune courte": {"en": "5 - Short dune", "ru": "5 - Короткая дюна"},
    "6 - Personnalisé": {"en": "6 - Custom", "ru": "6 - Пользовательский"},
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
        self._profile_combo_bindings = []
        self._translatable_combo_values = []

        self.title(APP_TITLE)
        self.geometry("980x720")
        self.minsize(900, 560)

        self._build_vars()
        self._load_launcher_settings()
        self._build_ui()
        self._apply_reference_414_profile()
        self._sync_texture_layer_vars()
        self._refresh_status()

    def _build_vars(self) -> None:
        self.language_var = StringVar(value="🇫🇷 Français")
        # Chemins vierges par défaut : l'utilisateur choisit explicitement ses fichiers.
        self.generator_var = StringVar(value="")
        self.heightmap_var = StringVar(value="")
        self.mask_var = StringVar(value="")
        self.satmap_var = StringVar(value="")
        self.layers_var = StringVar(value="")
        self.beach_layers_var = StringVar(value="hp_beach")
        self.sand_layers_var = StringVar(value="hp_sand")
        self.land_layers_var = StringVar(value="")

        self.beach_vanilla_var = StringVar(value=TEXTURE_NONE)
        self.beach_custom_var = StringVar(value="hp_beach")
        self.sand_vanilla_var = StringVar(value=TEXTURE_NONE)
        self.sand_custom_var = StringVar(value="hp_sand")
        self.land_vanilla_var = StringVar(value=TEXTURE_NONE)
        self.land_custom_var = StringVar(value="")

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

    def _build_ui(self) -> None:
        # Structure principale en grille :
        #   ligne 0 = titre fixe
        #   ligne 1 = onglets qui prennent toute la place disponible
        #   ligne 2 = barre basse fixe, toujours visible même quand la fenêtre est réduite
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        top = Frame(self, padding=10)
        top.grid(row=0, column=0, sticky="ew")
        self.title_label = Label(top, text=f"Beach Satmap Generator v{APP_VERSION}", font=("Segoe UI", 18, "bold"))
        self.title_label.pack(side="left", anchor="w")

        self.language_label = Label(top, text="Langue")
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
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))

        self.tab_paths = Frame(self.notebook, padding=10)
        self.tab_profiles = Frame(self.notebook, padding=10)
        self.tab_advanced = Frame(self.notebook, padding=10)
        self.tab_output = Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_paths, text="1. Fichiers")
        self.notebook.add(self.tab_profiles, text="2. Profils")
        self.notebook.add(self.tab_advanced, text="3. Technique")
        self.notebook.add(self.tab_output, text="4. Lancement")

        self._build_paths_tab()
        self._build_profiles_tab()
        self._build_advanced_tab()
        self._build_output_tab()

        bottom = Frame(self, padding=(10, 4, 10, 8))
        bottom.grid(row=2, column=0, sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=0)

        self.status_label = Label(
            bottom,
            textvariable=self.status_var,
            anchor="w",
            justify="left",
            wraplength=620,
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        # Signature créateurs / copyright affichée en bas à droite sur toutes les pages.
        self.signature_label = Label(
            bottom,
            text=f"MIT License Copyright (c) 2026 Bengilley & SleepingWolf · Launcher v{APP_VERSION}",
            font=("Segoe UI", 8),
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
        content = Frame(self.tab_paths)
        content.pack(fill=BOTH, expand=True)

        box = LabelFrame(content, text="Fichiers utilisés par le script", padding=10)
        box.pack(fill="x")

        rows = [
            ("Script générateur", self.generator_var, "file"),
            ("Heightmap ASC", self.heightmap_var, "file"),
            ("Mask PNG", self.mask_var, "file"),
            ("Satmap PNG", self.satmap_var, "file"),
            ("Layers CFG", self.layers_var, "file"),
        ]
        for i, (label, var, kind) in enumerate(rows):
            Label(box, text=label).grid(row=i, column=0, sticky="w", pady=4)
            Entry(box, textvariable=var, width=95).grid(row=i, column=1, sticky="ew", padx=8, pady=4)
            Button(box, text="Parcourir", command=lambda v=var: self._browse_file(v)).grid(row=i, column=2, pady=4)
        box.columnconfigure(1, weight=1)

        texture_box = LabelFrame(content, text="Textures utilisées dans layers.cfg", padding=10)
        texture_box.pack(fill="x", pady=10)

        Label(texture_box, text="Type", width=24).grid(row=0, column=0, sticky="w", pady=(0, 6))
        Label(texture_box, text="Texture vanilla DayZ").grid(row=0, column=1, sticky="w", pady=(0, 6))
        Label(texture_box, text="Texture custom / mod").grid(row=0, column=2, sticky="w", padx=8, pady=(0, 6))

        Label(texture_box, text="Plage / littoral existant", width=24).grid(row=1, column=0, sticky="w", pady=4)
        self.beach_vanilla_combo = Combobox(texture_box, textvariable=self.beach_vanilla_var, values=self._texture_choice_values(), state="readonly", width=28)
        self.beach_vanilla_combo.grid(row=1, column=1, sticky="ew", pady=4)
        Entry(texture_box, textvariable=self.beach_custom_var, width=50).grid(row=1, column=2, sticky="ew", padx=8, pady=4)
        Label(texture_box, text="ex vanilla : sa_beach | custom : hp_beach,my_beach").grid(row=1, column=3, sticky="w", pady=4)

        Label(texture_box, text="Sable source à étendre", width=24).grid(row=2, column=0, sticky="w", pady=4)
        self.sand_vanilla_combo = Combobox(texture_box, textvariable=self.sand_vanilla_var, values=self._texture_choice_values(), state="readonly", width=28)
        self.sand_vanilla_combo.grid(row=2, column=1, sticky="ew", pady=4)
        Entry(texture_box, textvariable=self.sand_custom_var, width=50).grid(row=2, column=2, sticky="ew", padx=8, pady=4)
        Label(texture_box, text="ex vanilla : cp_gravel | custom : hp_sand,my_sand").grid(row=2, column=3, sticky="w", pady=4)

        Label(texture_box, text="Terre cible côté intérieur", width=24).grid(row=3, column=0, sticky="w", pady=4)
        self.land_vanilla_combo = Combobox(texture_box, textvariable=self.land_vanilla_var, values=self._texture_choice_values(), state="readonly", width=28)
        self.land_vanilla_combo.grid(row=3, column=1, sticky="ew", pady=4)
        Entry(texture_box, textvariable=self.land_custom_var, width=50).grid(row=3, column=2, sticky="ew", padx=8, pady=4)
        Label(texture_box, text="optionnel | ex : cp_grass ou custom_grass").grid(row=3, column=3, sticky="w", pady=4)

        texture_box.columnconfigure(1, weight=1)
        texture_box.columnconfigure(2, weight=1)

        Label(
            content,
            text="Choisis une texture vanilla DayZ dans la liste, puis ajoute si besoin une ou plusieurs textures custom à la main. Les deux seront combinées automatiquement. Les customs peuvent être séparées par des virgules. Terre vide = comportement précédent.",
            foreground="#444444",
            wraplength=930,
            justify="left",
        ).pack(anchor="w", pady=(0, 4))

        quick = LabelFrame(content, text="Actions rapides", padding=10)
        quick.pack(fill="x", pady=10)
        Button(quick, text="Créer input / outputs", command=self._create_folders).pack(side="left", padx=(0, 8))
        Button(quick, text="Installer dépendances", command=self._install_deps).pack(side="left", padx=(0, 8))
        Button(quick, text="Ouvrir dossier du script", command=self._open_root).pack(side="left", padx=(0, 8))
        Button(quick, text="Ouvrir outputs", command=self._open_outputs).pack(side="left", padx=(0, 8))
        Button(quick, text="Vérifier les fichiers", command=lambda: (self._refresh_status(), self._show_missing_files())).pack(side="left", padx=(0, 8))
        Button(quick, text="Vérifier textures layers.cfg", command=self._verify_layers_textures).pack(side="left", padx=(0, 8))
        Button(quick, text="Réinitialiser chemins", command=self._reset_default_paths).pack(side="left")

        Label(content, text="Fichiers attendus par défaut : input/heightmap.asc, input/mask.png, input/satmap.png, input/layers.cfg").pack(anchor="w", pady=(8, 0))

    def _build_profiles_tab(self) -> None:
        # Conteneur unique de l'onglet : les zones sont imbriquées proprement dans une colonne.
        content = Frame(self.tab_profiles)
        content.pack(fill=BOTH, expand=True)

        top_grid = Frame(content)
        top_grid.pack(fill="x")
        top_grid.columnconfigure(0, weight=1)
        top_grid.columnconfigure(1, weight=1)
        top_grid.columnconfigure(2, weight=1)

        shore = LabelFrame(top_grid, text="Profil zone côtière", padding=10)
        water = LabelFrame(top_grid, text="Profil seuils d'altitude", padding=10)
        inland = LabelFrame(top_grid, text="Profil transition intérieure", padding=10)
        shore.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        water.grid(row=0, column=1, sticky="nsew", padx=6)
        inland.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        self._profile_box(shore, self.shore_profile_var, list(SHORE_PROFILES), self._on_shore_profile_change)
        Label(shore, textvariable=self.shore_detail_var, justify="left", wraplength=270).pack(anchor="w", fill="x", pady=(0, 10))
        self._field(shore, "Distance sable px", self.sand_distance_var)
        self._field(shore, "Pente max", self.sand_slope_var)
        self._field(shore, "Hauteur max m", self.sand_height_var)

        self._profile_box(water, self.water_profile_var, list(WATER_PROFILES), self._on_water_profile_change)
        Label(water, textvariable=self.water_detail_var, justify="left", wraplength=270).pack(anchor="w", fill="x", pady=(0, 10))
        self._field(water, "Eau forte sous m", self.water_start_var)
        self._field(water, "Eau jusqu'à m", self.water_end_var)
        self._field(water, "Terre dès m", self.land_start_var)

        self._profile_box(inland, self.inland_profile_var, list(INLAND_PROFILES), self._on_inland_profile_change)
        Label(inland, textvariable=self.inland_detail_var, justify="left", wraplength=270).pack(anchor="w", fill="x", pady=(0, 10))
        self._field(inland, "Distance retouche px", self.inland_distance_var)
        self._field(inland, "Force retouche", self.inland_strength_var)

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

        custom_box = LabelFrame(content, text="Profils personnalisés sauvegardés", padding=10)
        custom_box.pack(fill="x", pady=(0, 10))
        self.custom_preset_combo = Combobox(custom_box, textvariable=self.custom_preset_var, values=[], state="readonly", width=38)
        self.custom_preset_combo.pack(side="left", padx=(0, 8))
        Button(custom_box, text="Charger", command=self._load_selected_custom_preset).pack(side="left", padx=(0, 8))
        Button(custom_box, text="Sauvegarder réglage actuel", command=self._save_current_custom_preset).pack(side="left", padx=(0, 8))
        Button(custom_box, text="Supprimer", command=self._delete_selected_custom_preset).pack(side="left")
        Label(custom_box, text="Sauvegarde locale : custom_profiles.json", foreground="#444444").pack(side="left", padx=(12, 0))
        self._refresh_custom_preset_combo()

        details = LabelFrame(content, text="Détail complet des profils", padding=10)
        details.pack(fill=BOTH, expand=True, pady=(0, 10))
        details_text = Text(details, height=10, wrap="word")
        details_text.pack(fill=BOTH, expand=True)
        details_content = []
        details_content.append("PROFIL ZONE CÔTIÈRE\n")
        for name, p in SHORE_PROFILES.items():
            details_content.append(f"- {name} : {p['desc']} | distance {p['distance']} px | pente {p['slope']} | hauteur {p['height']} m\n")
        details_content.append("\nPROFIL SEUILS D'ALTITUDE\n")
        for name, p in WATER_PROFILES.items():
            details_content.append(f"- {name} : {p['desc']} | eau forte < {p['water_start']} m | eau <= {p['water_end']} m | terre > {p['land_start']} m\n")
        details_content.append("\nPROFIL TRANSITION INTÉRIEURE\n")
        for name, p in INLAND_PROFILES.items():
            details_content.append(f"- {name} : {p['desc']} | distance {p['distance']} px | force {p['strength']}\n")
        self.details_text = details_text
        self._refresh_details_text()

    def _refresh_details_text(self) -> None:
        if not hasattr(self, "details_text"):
            return
        details_content = []
        details_content.append(self._tr("PROFIL ZONE CÔTIÈRE") + "\n")
        for name, p in SHORE_PROFILES.items():
            details_content.append(f"- {self._profile_label(name)} : {self._tr_desc(p['desc'])} | {self._tr('distance')} {p['distance']} px | {self._tr('pente')} {p['slope']} | {self._tr('hauteur')} {p['height']} m\n")
        details_content.append("\n" + self._tr("PROFIL SEUILS D'ALTITUDE") + "\n")
        for name, p in WATER_PROFILES.items():
            details_content.append(f"- {self._profile_label(name)} : {self._tr_desc(p['desc'])} | {self._tr('eau forte')} < {p['water_start']} m | {self._tr('eau')} <= {p['water_end']} m | {self._tr('terre')} > {p['land_start']} m\n")
        details_content.append("\n" + self._tr("PROFIL TRANSITION INTÉRIEURE") + "\n")
        for name, p in INLAND_PROFILES.items():
            details_content.append(f"- {self._profile_label(name)} : {self._tr_desc(p['desc'])} | {self._tr('distance')} {p['distance']} px | {self._tr('force')} {p['strength']}\n")
        self.details_text.config(state=NORMAL)
        self.details_text.delete("1.0", END)
        self.details_text.insert("1.0", "".join(details_content))
        self.details_text.config(state=DISABLED)

    def _build_advanced_tab(self) -> None:
        # Conteneur unique de l'onglet : aucune section n'est posée en surcouche sur l'onglet.
        content = Frame(self.tab_advanced)
        content.pack(fill=BOTH, expand=True)

        box = LabelFrame(content, text="Paramètres techniques", padding=10)
        box.pack(fill="x")
        self._field(box, "Taille finale", self.target_size_var)
        self._field(box, "Lignes par chunk", self.chunk_rows_var)
        self._field(box, "Taille blocs couleur", self.block_size_var)
        Checkbutton(box, text="Ouvrir le dossier outputs à la fin", variable=self.open_outputs_var).pack(anchor="w", pady=8)

        help_box = LabelFrame(content, text="Lignes par chunk - observations RAM", padding=10)
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
        content = Frame(self.tab_output)
        content.pack(fill=BOTH, expand=True)

        cmd_box = LabelFrame(content, text="Commande générée", padding=10)
        cmd_box.pack(fill="x")
        Entry(cmd_box, textvariable=self.cmd_preview_var, width=130).pack(fill="x")
        Button(cmd_box, text="Actualiser la commande", command=self._update_command_preview).pack(anchor="e", pady=(8, 0))

        actions_box = LabelFrame(content, text="Actions de génération", padding=10)
        actions_box.pack(fill="x", pady=(10, 0))
        self.run_button = Button(actions_box, text="Lancer la génération", command=self._start_generation)
        self.run_button.pack(side="left", padx=(0, 8))
        self.stop_button = Button(actions_box, text="Arrêter", command=self._stop_generation, state=DISABLED)
        self.stop_button.pack(side="left")

        self.progress_bar = Progressbar(actions_box, mode="determinate", length=260, maximum=100)
        self.progress_bar.pack(side="left", padx=(18, 8), fill="x", expand=True)
        self.progress_label = Label(actions_box, textvariable=self.progress_var, width=8)
        self.progress_label.pack(side="left")

        log_box = LabelFrame(content, text="Journal", padding=10)
        log_box.pack(fill=BOTH, expand=True, pady=10)
        scrollbar = Scrollbar(log_box)
        scrollbar.pack(side="right", fill="y")
        self.log_text = Text(log_box, height=20, wrap="word", yscrollcommand=scrollbar.set)
        self.log_text.pack(fill=BOTH, expand=True)
        self.log_text.tag_configure("info", foreground="#1f4e79")
        self.log_text.tag_configure("ok", foreground="#008000")
        self.log_text.tag_configure("warning", foreground="#b36b00")
        self.log_text.tag_configure("error", foreground="#c00000")
        self.log_text.tag_configure("step", foreground="#7030a0")
        scrollbar.config(command=self.log_text.yview)

    def _profile_box(self, parent: Frame, variable: StringVar, values: list[str], callback) -> None:
        display_var = StringVar()
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

    def _field(self, parent: Frame, label: str, var: StringVar) -> None:
        row = Frame(parent)
        row.pack(fill="x", pady=4)
        Label(row, text=label, width=22).pack(side="left")
        Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)

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
        if lang == "fr":
            return internal_name
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
            "Taille finale : résolution de sortie de la satmap et du beach mask. "
            "10240 est recommandé pour une carte 10K. Plus la valeur est haute, plus le rendu est précis, "
            "mais plus la génération consomme de RAM et de temps. Limite acceptée par l'interface : 512 à 30000.\n\n"
            "Lignes par chunk : nombre de lignes traitées en une seule passe. "
            "Sur une sortie 10240 x 10240, l'observation actuelle donne environ 8.5 Go RAM au pic pour le script seul. "
            "Le chunk-rows influence surtout la vitesse et la stabilité : 4096 est recommandé, 8192 est le mode performance si stable. "
            "Limite acceptée par l'interface : 64 à 8192.\n\n"
            "Taille blocs couleur : taille des zones utilisées pour casser les aplats et ajouter des variations de couleur. "
            "16 donne un rendu plus détaillé mais plus bruité, 32 est recommandé, 64 donne un rendu plus doux, "
            "128 ou plus peut créer de gros blocs visibles. Limite acceptée par l'interface : 4 à 512.\n\n"
            "Réglage conseillé général : Taille finale 10240, Lignes par chunk 4096 recommandé / 8192 performance, Taille blocs couleur 32 ou 64 selon le rendu souhaité."
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

    def _load_launcher_settings(self) -> None:
        path = self.root_dir / LAUNCHER_SETTINGS_FILE
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            lang = data.get("language", "fr")
            self.language_var.set(LANGUAGE_LABEL_BY_CODE.get(lang, "🇫🇷 Français"))
        except Exception:
            self.language_var.set("🇫🇷 Français")

    def _save_launcher_settings(self) -> None:
        path = self.root_dir / LAUNCHER_SETTINGS_FILE
        try:
            path.write_text(json.dumps({"language": self._current_lang()}, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

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
        return suffix in {".py", ".pyw", ".asc", ".png", ".cfg", ".txt", ".md", ".json"}

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
        ]:
            set_if(var, key)
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

    def _browse_file(self, var: StringVar) -> None:
        path = filedialog.askopenfilename(initialdir=str(self.root_dir))
        if path:
            var.set(self._store_path_for_ui(path))
            self._refresh_status()

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
                f"{self._tr('Distance sable')} : {shore.get('distance')} px\n"
                f"{self._tr('Pente max')} : {shore.get('slope')}\n"
                f"{self._tr('Hauteur max')} : {shore.get('height')} m"
            )
        if water:
            self.water_detail_var.set(
                f"{self._tr('Détail')} : {self._tr_desc(water.get('desc', ''))}\n"
                f"{self._tr('Eau forte sous')} : {water.get('water_start')} m\n"
                f"{self._tr('Eau jusqu\'à')} : {water.get('water_end')} m\n"
                f"{self._tr('Terre / plage dès')} : {water.get('land_start')} m"
            )
        if inland:
            self.inland_detail_var.set(
                f"{self._tr('Détail')} : {self._tr_desc(inland.get('desc', ''))}\n"
                f"{self._tr('Distance retouche')} : {inland.get('distance')} px\n"
                f"{self._tr('Force retouche')} : {inland.get('strength')}"
            )

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

    def _build_command(self) -> list[str]:
        generator_raw = self.generator_var.get().strip().strip('"')
        if not generator_raw:
            raise FileNotFoundError(self._tr("Script introuvable : {path}", path=self._display_path(generator_raw)))
        generator = self._resolve_user_path(generator_raw)
        if not generator.exists() or not generator.is_file():
            raise FileNotFoundError(self._tr("Script introuvable : {path}", path=self._display_path(generator)))

        self._sync_texture_layer_vars()
        shore = SHORE_PROFILES[self.shore_profile_var.get()]
        target_size = self._int_value(self.target_size_var, "Taille finale", 512, 30000)
        chunk_rows = self._int_value(self.chunk_rows_var, "Lignes par chunk", 64, 8192)
        block_size = self._int_value(self.block_size_var, "Taille blocs couleur", 4, 512)
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
            "--sand-preset", str(shore["key"]),
            "--sand-distance", str(self._float_value(self.sand_distance_var, "Distance sable", 1, 300)),
            "--sand-slope-max", str(self._float_value(self.sand_slope_var, "Pente max", 0.01, 1.0)),
            "--sand-max-height", str(self._float_value(self.sand_height_var, "Hauteur max", 0.1, 50)),
            "--water-start-level", str(self._float_value(self.water_start_var, "Eau forte sous", -100, 100)),
            "--water-end-level", str(self._float_value(self.water_end_var, "Eau jusqu'à", -100, 100)),
            "--land-start-level", str(self._float_value(self.land_start_var, "Terre dès", -100, 100)),
            "--land-pass-distance", str(self._float_value(self.inland_distance_var, "Distance transition", 0, 160)),
            "--land-pass-strength", str(self._float_value(self.inland_strength_var, "Force transition", 0, 1)),
            "--beach-layer-names", self.beach_layers_var.get().strip(),
            "--sand-layer-names", self.sand_layers_var.get().strip(),
        ]
        land_layers = self.land_layers_var.get().strip()
        if land_layers:
            cmd.extend(["--land-layer-names", land_layers])
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
            ("Mask PNG", self.mask_var, True),
            ("Satmap PNG", self.satmap_var, True),
            ("Layers CFG", self.layers_var, True),
        ]

    def _missing_files(self, include_generator: bool = True) -> list[str]:
        missing: list[str] = []
        resolved_files: dict[str, Path] = {}

        expected_ext = {
            "Script générateur": {".py", ".pyw"},
            "Heightmap ASC": {".asc"},
            "Mask PNG": {".png"},
            "Satmap PNG": {".png"},
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
        # Réinitialisation volontairement vierge : aucun chemin automatique imposé.
        self.generator_var.set("")
        self.heightmap_var.set("")
        self.mask_var.set("")
        self.satmap_var.set("")
        self.layers_var.set("")
        self.beach_vanilla_var.set(self._texture_none_label())
        self.beach_custom_var.set("hp_beach")
        self.sand_vanilla_var.set(self._texture_none_label())
        self.sand_custom_var.set("hp_sand")
        self.land_vanilla_var.set(self._texture_none_label())
        self.land_custom_var.set("")
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
            self._tr("Plage / littoral existant"): [
                part.strip() for part in self.beach_layers_var.get().split(",") if part.strip()
            ],
            self._tr("Sable source à étendre"): [
                part.strip() for part in self.sand_layers_var.get().split(",") if part.strip()
            ],
            self._tr("Terre cible côté intérieur"): [
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
                if group_name == self._tr("Terre cible côté intérieur"):
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
                    if group_name != self._tr("Terre cible côté intérieur"):
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
        l = line.strip().lower()
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
            self.stop_button.config(state=NORMAL)
            self._set_progress(0, self._tr("Démarrage"))
        else:
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
            f"- Mask PNG : `{self._display_path(self.mask_var.get().strip())}`",
            f"- Satmap PNG : `{self._display_path(self.satmap_var.get().strip())}`",
            f"- Layers CFG : `{self._display_path(self.layers_var.get().strip())}`",
            "",
            f"## {self._tr('Textures utilisées dans layers.cfg')}",
            "",
            f"- {self._tr('Plage / littoral existant')} : `{self.beach_layers_var.get().strip()}`",
            f"- {self._tr('Sable source à étendre')} : `{self.sand_layers_var.get().strip()}`",
            f"- {self._tr('Terre cible côté intérieur')} : `{self.land_layers_var.get().strip() or self._tr('non utilisé')}`",
            f"- {self._tr('Mode textures')} : `{self._tr('liste vanilla DayZ + champ custom manuel')}`",
            "",
            f"## {self._tr('Profil zone côtière')}",
            "",
            f"- {self._tr('Profil')} : `{self._profile_label(shore_name)}`",
            f"- {self._tr('Description')} : {shore_desc}",
            f"- {self._tr('Distance sable')} : `{self.sand_distance_var.get()}` px",
            f"- {self._tr('Pente max')} : `{self.sand_slope_var.get()}`",
            f"- {self._tr('Hauteur max')} : `{self.sand_height_var.get()}` m",
            "",
            "## " + self._tr("Profil seuils d\'altitude"),
            "",
            f"- {self._tr('Profil')} : `{self._profile_label(water_name)}`",
            f"- {self._tr('Description')} : {water_desc}",
            f"- {self._tr('Eau forte sous')} : `{self.water_start_var.get()}` m",
            "- " + self._tr("Eau jusqu\'à") + f" : `{self.water_end_var.get()}` m",
            f"- {self._tr('Terre / plage dès')} : `{self.land_start_var.get()}` m",
            "",
            f"## {self._tr('Profil transition intérieure')}",
            "",
            f"- {self._tr('Profil')} : `{self._profile_label(inland_name)}`",
            f"- {self._tr('Description')} : {inland_desc}",
            f"- {self._tr('Distance retouche')} : `{self.inland_distance_var.get()}` px",
            f"- {self._tr('Force retouche')} : `{self.inland_strength_var.get()}`",
            "",
            f"## {self._tr('Paramètres techniques')}",
            "",
            f"- {self._tr('Taille finale')} : `{self.target_size_var.get()}`",
            f"- {self._tr('Lignes par chunk')} : `{self.chunk_rows_var.get()}`",
            f"- {self._tr('Taille blocs couleur')} : `{self.block_size_var.get()}`",
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

        missing = [p for p in [Path(self.heightmap_var.get()), Path(self.mask_var.get()), Path(self.satmap_var.get()), Path(self.layers_var.get())] if not p.exists()]
        if missing:
            messagebox.showerror("Fichiers manquants", "Fichiers introuvables :\n" + "\n".join(self._display_path(p) for p in missing))
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
            self.status_var.set(f"{self._tr('Génération terminée.')} 100%")
            self._append_log("\n[OK] Génération terminée.\n")
            if self.last_command is not None:
                try:
                    self._write_output_readme(self.last_command)
                except Exception as exc:
                    self._append_log(f"\nImpossible de créer le README de réglages : {exc}\n")
            if self.open_outputs_var.get():
                self._open_outputs()
        else:
            self.status_var.set(f"{self._tr('La génération a échoué.')} {self._progress_value}%")
            self._append_log(f"\n[ERROR] La génération a échoué. Code : {code}\n")

    def _stop_generation(self) -> None:
        if self.process is not None:
            if messagebox.askyesno("Arrêter", "Arrêter la génération en cours ?"):
                self.process.terminate()
                self._append_log("\n[WARNING] Arrêt demandé par l'utilisateur.\n")


if __name__ == "__main__":
    app = SatmapGui()
    app.mainloop()
