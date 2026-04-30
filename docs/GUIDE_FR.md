# Guide rapide FR

## Installation

Installe Python puis les dépendances :

```bash
py -m pip install -r requirements.txt
```

## Fichiers nécessaires

Le launcher a besoin de :

```text
heightmap.asc
mask.png
satmap.png
layers.cfg
```

Les chemins sont vides par défaut. Sélectionne les fichiers manuellement dans l'onglet `1. Fichiers`.

## Textures

Tu peux choisir une texture vanilla DayZ dans la liste déroulante et/ou écrire une texture custom manuellement.

Exemple :

```text
Plage / littoral existant : hp_beach
Sable source à étendre   : hp_sand
Terre cible intérieur    : vide ou texture optionnelle
```

Utilise le bouton :

```text
Vérifier textures layers.cfg
```

pour contrôler que les noms existent dans `layers.cfg`.

## Génération

Le lancement se fait uniquement depuis l'onglet :

```text
4. Lancement
```

Les résultats sont créés dans :

```text
outputs/output_V...
```
