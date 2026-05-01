# Documentation complète — Beach Satmap Generator

Version documentée : générateur `1.3.5` / launcher `1.7.7`.

Cette documentation explique le fonctionnement du script `satmap_generator_optimized_presets.py`, l'interface `satmap_gui_launcher.pyw`, les fichiers nécessaires, les réglages disponibles, les profils, les sorties et les erreurs courantes.

---

## 1. Objectif

Le projet sert à générer une satmap DayZ enrichie autour du littoral : plages, eau, fond marin, ressac, sable humide, transitions sable → terre et corrections de couleur par catégories de terrain.

Le générateur travaille à partir de quatre fichiers principaux :

```text
input/heightmap.asc
input/mask.png
input/satmap.png
input/layers.cfg
```

Il produit principalement :

```text
outputs/output_Vx/satmap_final_10240.png
outputs/output_Vx/beach_mask_10240.png
outputs/output_Vx/generation_settings.json
outputs/output_Vx/RAPPORT_GENERATION_COMPLET.md
```

---

## 2. Fichiers du projet

| Fichier | Rôle |
|---|---|
| `satmap_generator_optimized_presets.py` | Moteur de génération. Peut être lancé en ligne de commande ou par le launcher. |
| `satmap_gui_launcher.pyw` | Interface graphique Tkinter pour configurer et lancer le générateur sans `.bat`. |
| `info.png` | Icône utilisée pour les infobulles d'aide dans l'interface. |
| `custom_profiles.json` | Créé par le launcher pour stocker les profils utilisateur. |
| `launcher_settings.json` | Créé par le launcher pour conserver les chemins et derniers réglages. |

---

## 3. Installation

### 3.1 Prérequis

- Windows recommandé.
- Python 3.10+ conseillé.
- Dépendances Python :

```bash
py -m pip install numpy pillow scipy
```

Tkinter est normalement inclus avec Python sous Windows.

### 3.2 Arborescence recommandée

Place les fichiers comme ceci :

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

Le launcher peut détecter automatiquement les fichiers dans `input/` si les noms sont standards.

---

## 4. Lancement rapide

### 4.1 Avec l'interface graphique

Double-clique sur :

```text
satmap_gui_launcher.pyw
```

Puis :

1. Onglet **1. Fichiers** : vérifie le script, la heightmap, le mask, la satmap et le layers.cfg.
2. Onglet **2. Profils** : choisis la largeur de plage, les niveaux d'eau, la fusion côté terre, les couleurs et textures.
3. Onglet **3. Technique** : règle résolution, mémoire/vitesse, diagnostic.
4. Onglet **4. Lancement** : vérifie la commande générée puis lance la génération.

### 4.2 En ligne de commande

Exemple simple :

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

Exemple avec rendu d'eau et textures :

```bash
py satmap_generator_optimized_presets.py ^
  --heightmap input/heightmap.asc ^
  --mask input/mask.png ^
  --satmap input/satmap.png ^
  --layers input/layers.cfg ^
  --beach-layer-names hp_beach ^
  --sand-layer-names hp_sand ^
  --land-layer-names cp_grass ^
  --sand-preset large ^
  --sand-color-preset belle_ile ^
  --water-color-preset atlantic_belle_ile ^
  --surf-width 8 ^
  --foam-strength 1.0 ^
  --wet-sand-width 10 ^
  --debug-masks
```

---

## 5. Entrées obligatoires

### 5.1 `heightmap.asc`

Fichier ASC contenant les altitudes. Il sert à :

- déterminer l'eau et la terre ;
- calculer la pente ;
- limiter la plage selon l'altitude maximale ;
- calculer la distance au rivage.

Le script lit l'en-tête ASC, notamment `cellsize`, puis redimensionne la heightmap à la résolution finale.

### 5.2 `mask.png`

Image de mask terrain. Chaque couleur RGB doit correspondre à une entrée de `layers.cfg`.

Formats supportés : `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tif`, `.tiff`.

Recommandation : utilise PNG/BMP/TIFF pour éviter les couleurs modifiées par compression. JPG/JPEG est refusé si `--mask-color-tolerance` vaut `0`.

### 5.3 `satmap.png`

Image satellite de base. Le script la redimensionne et la corrige visuellement par catégories : champ, herbe, forêt, roche, sable, plage, gravier, route, eau, etc.

### 5.4 `layers.cfg`

Fichier de correspondance entre couleurs du mask et noms de textures DayZ. Le générateur lit les lignes du type :

```cpp
nom_texture[] = {{ R, G, B }};
```

Les noms renseignés dans **Texture déjà plage**, **Texture sable à agrandir** et **Texture terre à mélanger** doivent exister dans ce fichier.

---

## 6. Fonctionnement interne du générateur

Le traitement suit cette logique :

1. **Lecture de `layers.cfg`** : création d'une légende couleur RGB → nom de layer.
2. **Chargement de la heightmap ASC** : conversion des altitudes en tableau NumPy.
3. **Redimensionnement** : heightmap, mask et satmap sont adaptés à `target-size`.
4. **Calcul de pente** : gradient de la heightmap, puis normalisation.
5. **Classification du mask** : chaque pixel reçoit une catégorie terrain.
6. **Détection de la source sable** : le script cherche les layers indiqués dans `--sand-layer-names`.
7. **Dilatation locale de la source sable** : permet d'étendre la plage autour des pixels source sans l'autoriser partout.
8. **Détection de l'eau** : selon `water-start-level`, `water-end-level` et `land-start-level`.
9. **Distance au rivage** : distance de chaque pixel terrestre à la zone d'eau.
10. **Bruit multi-échelle** : variations larges, moyennes et fines pour éviter les aplats.
11. **Correction satmap globale** : harmonisation par catégorie de terrain.
12. **Création du masque sable** : conditions cumulées distance + hauteur + pente + source sable + catégorie autorisée.
13. **Rendu eau/plage** : dégradé eau profonde → eau claire → ressac → sable humide → sable sec.
14. **Deuxième passe côté terre** : raccord sable → terre/herbe avec transition plus ou moins visible.
15. **Sortie beach mask** : eau en valeur intermédiaire, sable/plage en blanc.
16. **Sauvegarde satmap finale** : contraste global léger, conversion `uint8`, écriture PNG.
17. **Rapport** : sauvegarde des paramètres utilisés.

---

## 7. Interface graphique

### 7.1 Onglet `1. Fichiers`

Permet de renseigner :

- script générateur ;
- heightmap ASC ;
- mask ;
- satmap ;
- layers.cfg ;
- textures DayZ à reconnaître.

La partie textures combine une liste de textures DayZ vanilla et un champ custom manuel. Plusieurs textures custom peuvent être séparées par virgules.

Textures vanilla disponibles :

```text
cp_grass, cp_dirt, cp_rock, cp_concrete1, cp_concrete2, cp_broadleaf_dense1, cp_broadleaf_dense2, cp_broadleaf_sparse1, cp_broadleaf_sparse2, cp_conifer_common1, cp_conifer_common2, cp_conifer_moss1, cp_conifer_moss2, cp_grass_tall, cp_gravel, en_flowers1, en_flowers2, en_flowers3, en_forest_con, en_forest_dec, en_grass1, en_grass2, en_soil, en_stones, en_stubble, en_tarmac_old, sa_forest_spruce, sa_grass_brown, sa_concrete, sa_beach, sa_forest_birch, sa_gravel, sa_snow, sa_snow_forest, sa_volcanic_red, sa_volcanic_yellow, sa_grass_green
```

### 7.2 Onglet `2. Profils`

Contient :

- plage : taille, pente, hauteur ;
- eau : niveaux d'altitude ;
- fusion sable → terre ;
- couleurs du sable ;
- texture sable ;
- couleurs de l'eau ;
- texture eau ;
- finition du bord de mer.

### 7.3 Onglet `3. Technique`

Contient :

- résolution finale ;
- chunk rows / mémoire-vitesse ;
- taille des variations couleur ;
- tolérance couleur du mask ;
- génération des images de diagnostic.

### 7.4 Onglet `4. Lancement`

Affiche :

- la commande générée ;
- les actions de validation ;
- le bouton de génération ;
- le journal ;
- la progression.

---

## 8. Profils plage

### 8.1 Presets moteur

| ID | Nom | Distance px | Pente max | Hauteur max m | Description |
| --- | --- | --- | --- | --- | --- |
| 1 | tres_propre | 45.0 | 0.16 | 4.8 | Plage fine, tres controlee |
| 2 | propre_marge | 55.0 | 0.18 | 5.2 | Un peu plus de sable sans trop deborder |
| 3 | equilibre | 60.0 | 0.2 | 5.5 | Bon reglage de base |
| 4 | large | 70.0 | 0.22 | 6.0 | Plages plus visibles, bonne marge |
| 5 | tres_large | 85.0 | 0.25 | 7.0 | Sable plus loin dans les terres |
| 6 | agressif | 100.0 | 0.28 | 8.0 | Peut commencer a manger les talus |
| 7 | tres_agressif | 120.0 | 0.32 | 10.0 | Fort risque de sable trop haut / trop loin |
| 8 | custom | 70.0 | 0.22 | 6.0 | Valeurs personnalisées via le menu |

### 8.2 Profils GUI

| Profil GUI | Preset CLI | Largeur plage px | Pente | Hauteur m | Usage |
| --- | --- | --- | --- | --- | --- |
| 1 - Bord net | 1 | 45.0 | 0.16 | 4.8 | Plage fine et peu intrusive |
| 2 - Bord naturel | 2 | 55.0 | 0.18 | 5.2 | Marge modérée |
| 3 - Équilibré | 3 | 60.0 | 0.2 | 5.5 | Réglage polyvalent |
| 4 - Plage large | 4 | 70.0 | 0.22 | 6.0 | Plage large polyvalente |
| 5 - Grande plage | 5 | 85.0 | 0.25 | 7.0 | Sable plus présent |
| 6 - Extension forte | 6 | 100.0 | 0.28 | 8.0 | Risque de remonter sur talus |
| 7 - Extension max | 7 | 120.0 | 0.32 | 10.0 | Test uniquement |
| 8 - Personnalisé | 8 | 70.0 | 0.22 | 6.0 | Valeurs libres |

Conseils :

- `1 - Bord net` : plage fine, propre, peu intrusive.
- `3 - Équilibré` : bon réglage de base.
- `4 - Plage large` : bon profil pour une côte visible.
- `6` et `7` : à tester uniquement si la côte est très plate ; risque de sable trop haut ou trop loin.

---

## 9. Profils eau

| Profil GUI | Eau profonde sous m | Eau jusqu'à m | Terre dès m | Usage |
| --- | --- | --- | --- | --- |
| 1 - Standard | 0.0 | 1.0 | 1.0 | Eau <= 1.0 m |
| 2 - Littoral bas | 0.0 | 0.8 | 0.8 | Niveau côtier bas |
| 3 - Eau plus large | 0.0 | 1.3 | 1.3 | Eau plus présente |
| 4 - Personnalisé | 0.0 | 1.0 | 1.0 | Niveaux libres |

Conseils :

- `1 - Standard` convient si le niveau d'eau de la heightmap est autour de 1 m.
- `2 - Littoral bas` réduit la zone d'eau.
- `3 - Eau plus large` augmente la présence visuelle de l'eau.

Règle importante :

```text
water-start-level < water-end-level <= land-start-level < sand-max-height
```

---

## 10. Fusion sable → terre

| Profil GUI | Distance px | Force | Usage |
| --- | --- | --- | --- |
| 1 - Désactivé | 0.0 | 0.0 | Aucune retouche côté terre |
| 2 - Net léger | 12.0 | 0.6 | Halo presque supprimé |
| 3 - Net naturel | 18.0 | 0.78 | Retouche équilibrée |
| 4 - Net marqué | 24.0 | 0.92 | Transition plus visible |
| 5 - Dune courte | 32.0 | 1.0 | Dune courte marquée |
| 6 - Personnalisé | 18.0 | 0.78 | Valeurs libres |

- Distance `0` ou force `0` désactive la passe côté terre.
- Une distance courte donne un bord net.
- Une distance plus grande crée un effet dune/transition mais peut salir l'intérieur si elle est trop forte.

---

## 11. Référence complète des paramètres CLI

| Option | Défaut | Valeurs | Rôle |
| --- | --- | --- | --- |
| --heightmap | input/heightmap.asc | ASC | Heightmap source utilisée pour les altitudes, l'eau, les pentes et le littoral. |
| --mask | input/mask.png | PNG/JPG/BMP/TIF | Image mask dont les couleurs doivent correspondre aux couleurs définies dans layers.cfg. |
| --satmap | input/satmap.png | PNG/JPG/BMP/TIF | Satmap de base que le script corrige et enrichit. |
| --layers | input/layers.cfg | CFG | Fichier qui associe les couleurs du mask aux noms de layers DayZ. |
| --output-satmap | outputs/output_Vx/satmap_final_10240.png | PNG | Image satmap finale. Si le nom par défaut est utilisé, le script crée output_V1, output_V2, etc. |
| --output-beach-mask | outputs/output_Vx/beach_mask_10240.png | PNG | Masque final : eau et plage générée. |
| --target-size | 10240 | 512 à 30000 | Résolution carrée finale. Pour une carte DayZ 10K : 10240. |
| --chunk-rows | 512 CLI / 2048 GUI | 64 à 8192 | Nombre de lignes traitées par bloc. Plus haut = plus rapide mais plus de RAM. |
| --block-size | 32 | 4 à 512 | Taille des blocs de variation/correction couleur. |
| --sand-preset | manuel/default ou profil GUI | 1-8 ou nom | Preset plage utilisé comme base avant overrides manuels. |
| --sand-distance | preset | 1 à 300 px | Distance maximale depuis le rivage où le sable peut être généré. |
| --sand-slope-max | preset | 0.01 à 1.00 | Pente maximale autorisée. Plus bas évite mieux falaises et talus. |
| --sand-max-height | preset | 0.1 à 50 m | Altitude maximale où le sable peut apparaître. |
| --water-start-level | 0.0 | -100 à 100 m | Sous ce seuil, l'eau est considérée comme plus profonde/sombre. |
| --water-end-level | 1.0 | -100 à 100 m | Limite haute considérée comme eau. |
| --land-start-level | 1.0 | -100 à 100 m | Seuil à partir duquel le terrain devient terre/plage émergée. |
| --land-pass-distance | 18 CLI / profil GUI | 0 à 160 px | Largeur de la deuxième passe sable → terre. |
| --land-pass-strength | 0.72 CLI / profil GUI | 0 à 1 | Force de la transition côté terre. |
| --beach-layer-names | obligatoire, GUI: hp_beach | liste séparée par virgules | Layers déjà considérés comme plage/littoral. |
| --sand-layer-names | obligatoire, GUI: hp_sand | liste séparée par virgules | Layers source servant à autoriser l'extension du sable. |
| --land-layer-names | vide | optionnel | Layers côté terre limitant la transition intérieure. Vide = comportement général. |
| --sand-color-preset | belle_ile | preset ou custom | Palette couleur du sable. |
| --sand-color-strength | 1.0 | 0.0 à 1.5 | Intensité d'application de la palette sable. |
| --sand-dry-rgb | None | R,G,B ou #RRGGBB | Override custom du sable sec si preset custom. |
| --sand-wet-rgb | None | R,G,B ou #RRGGBB | Override custom du sable humide. |
| --sand-shell-rgb | None | R,G,B ou #RRGGBB | Variation claire/coquillière. |
| --wet-beach-rgb | None | R,G,B ou #RRGGBB | Bord humide entre eau et plage. |
| --seabed-rgb | None | R,G,B ou #RRGGBB | Fond marin sableux visible près du rivage. |
| --sand-texture-image | vide | image | Texture optionnelle ajoutant du grain au sable sans modifier la zone générée. |
| --sand-texture-strength | 0.45 | 0.0 à 1.0 | Force de la texture sable. |
| --sand-texture-scale | 1.0 | 0.1 à 8.0 | Échelle de répétition de la texture sable. |
| --water-color-preset | atlantic_belle_ile | preset ou custom | Palette du dégradé d'eau. |
| --water-color-strength | 1.0 | 0.0 à 1.5 | Intensité d'application de la palette eau. |
| --water-deep-rgb | None | R,G,B ou #RRGGBB | Couleur eau profonde. |
| --water-mid-rgb | None | R,G,B ou #RRGGBB | Couleur eau intermédiaire. |
| --water-shallow-rgb | None | R,G,B ou #RRGGBB | Couleur eau peu profonde. |
| --water-lagoon-rgb | None | R,G,B ou #RRGGBB | Couleur lagon/eau très claire. |
| --water-surf-rgb | None | R,G,B ou #RRGGBB | Couleur ressac/écume. |
| --water-seabed-rgb | None | R,G,B ou #RRGGBB | Fond marin sous l'eau. |
| --water-texture-image | vide | image | Texture optionnelle pour vagues, bruit, écume ou reflets. |
| --water-texture-strength | 0.25 | 0.0 à 1.0 | Force de la texture eau. |
| --water-texture-scale | 1.0 | 0.1 à 8.0 | Échelle de la texture eau. |
| --water-texture-smoothing | 12.0 | 0.0 à 64.0 px | Lissage appliqué à la texture eau avant répétition. |
| --water-texture-warp | 18.0 | 0.0 à 96.0 px | Déformation des coordonnées pour casser les répétitions. |
| --surf-width | 8.0 | 1 à 128 px | Épaisseur de la bande claire de ressac. |
| --shallow-width-factor | 0.42 | 0.05 à 5.0 | Multiplicateur de la zone d'eau claire basé sur sand-distance. |
| --mid-width-factor | 0.95 | 0.05 à 5.0 | Multiplicateur de la zone d'eau intermédiaire. |
| --deep-width-factor | 1.70 | 0.05 à 5.0 | Distance avant eau profonde/sombre. |
| --foam-strength | 1.0 | 0 à 2 | Intensité visuelle de l'écume et du contouring. |
| --wet-sand-width | 10.0 | 1 à 128 px | Largeur du sable humide près de l'eau. |
| --mask-color-tolerance | 0 | 0 à 255 | Tolérance RGB pour associer mask et layers.cfg. 0 = exact, JPG refusé. |
| --debug-masks | false | flag | Génère des images de diagnostic dans debug_masks. |
| --validate-only | false | flag | Vérifie fichiers et paramètres sans générer. |
| --no-report | false | flag | Désactive génération_settings.json et RAPPORT_GENERATION_COMPLET.md. |
| --list-sand-presets | false | flag | Affiche les presets plage puis quitte. |
| --list-sand-color-presets | false | flag | Affiche les presets couleur sable puis quitte. |
| --list-water-color-presets | false | flag | Affiche les presets couleur eau puis quitte. |

---

## 12. Couleurs du sable

| Preset | Label | Dry | Wet | Shell | Wet beach | Seabed |
| --- | --- | --- | --- | --- | --- | --- |
| belle_ile | Belle-Île / sable clair naturel | 222,204,178 | 190,168,145 | 208,196,182 | 181,156,128 | 160,120,90 |
| atlantic_light | Atlantique clair | 230,214,184 | 196,176,150 | 220,210,196 | 188,164,134 | 170,132,98 |
| golden | Sable doré | 226,190,126 | 176,140,95 | 218,200,164 | 166,132,92 | 152,112,72 |
| pale_white | Sable blanc / très clair | 238,230,204 | 205,194,170 | 236,230,218 | 196,184,160 | 176,160,130 |
| grey_shell | Sable gris / coquillier | 200,196,184 | 158,154,145 | 220,218,210 | 150,145,132 | 128,120,108 |
| dark_volcanic | Sable sombre / volcanique | 112,105,96 | 70,68,66 | 150,145,135 | 82,76,70 | 74,68,62 |
| red_ochre | Sable ocre / rouge | 196,128,82 | 132,82,58 | 205,176,150 | 144,92,62 | 122,76,52 |
| custom | Manual RGB | --sand-dry-rgb | --sand-wet-rgb | --sand-shell-rgb | --wet-beach-rgb | --seabed-rgb |

Le mode `custom` active les valeurs RGB manuelles. Format accepté :

```text
R,G,B
#RRGGBB
```

Exemple :

```bash
--sand-color-preset custom --sand-dry-rgb 230,214,184 --sand-wet-rgb 196,176,150
```

---

## 13. Couleurs de l'eau

| Preset | Label | Deep | Mid | Shallow | Lagoon | Surf | Seabed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| atlantic_belle_ile | Atlantique / Belle-Île | 58,88,122 | 70,112,142 | 93,149,156 | 118,181,174 | 156,202,190 | 160,120,90 |
| atlantic_open_ocean | Atlantique ouvert / bleu profond | 28,72,112 | 45,100,135 | 76,135,150 | 105,165,160 | 165,205,195 | 135,115,90 |
| atlantic_grey_coast | Côte atlantique grise / Manche | 48,70,88 | 72,96,108 | 105,130,125 | 132,154,145 | 178,190,178 | 125,115,100 |
| tropical_lagoon | Lagon tropical | 20,95,145 | 35,165,185 | 95,220,210 | 130,235,220 | 220,245,230 | 210,190,130 |
| caribbean_turquoise | Caraïbes / turquoise clair | 0,87,143 | 18,156,188 | 72,218,220 | 125,238,225 | 230,248,238 | 218,202,145 |
| maldives_atoll | Maldives / atoll sable blanc | 5,76,132 | 25,150,190 | 85,225,220 | 155,242,225 | 235,250,238 | 225,207,150 |
| coral_reef_shallow | Récif corallien / haut-fond | 16,80,138 | 30,145,170 | 95,205,190 | 150,225,205 | 225,245,225 | 190,165,120 |
| mediterranean_blue | Méditerranée / bleu minéral | 25,75,138 | 42,110,165 | 70,155,185 | 105,190,195 | 180,220,215 | 150,130,95 |
| aegean_clear | Mer Égée / bleu clair | 18,80,150 | 35,125,180 | 75,175,205 | 110,205,210 | 195,230,225 | 165,145,105 |
| adriatic_clear | Adriatique / bleu vert clair | 35,85,120 | 55,125,150 | 90,170,175 | 130,200,190 | 200,225,210 | 155,140,110 |
| red_sea_clear | Mer Rouge / eau très claire | 15,72,132 | 28,130,170 | 78,190,195 | 120,220,205 | 220,240,220 | 190,165,115 |
| pacific_deep | Pacifique profond | 12,48,95 | 30,80,130 | 62,125,155 | 90,160,165 | 160,210,200 | 105,95,85 |
| indian_ocean | Océan Indien | 10,70,125 | 28,125,160 | 70,185,190 | 115,215,200 | 220,240,225 | 190,175,125 |
| cold_ocean | Océan froid | 35,65,85 | 55,95,115 | 90,135,140 | 105,155,155 | 180,205,205 | 120,115,105 |
| north_sea_grey | Mer du Nord / gris vert | 45,65,78 | 65,88,95 | 92,118,112 | 120,140,130 | 170,185,175 | 115,105,88 |
| baltic_green | Baltique / vert froid | 36,70,72 | 58,100,88 | 90,130,100 | 125,155,115 | 178,195,165 | 115,105,75 |
| arctic_glacial | Arctique / eau glaciale | 25,70,95 | 55,115,135 | 100,165,170 | 145,205,200 | 220,238,230 | 130,130,120 |
| fjord_dark | Fjord / eau sombre | 15,42,58 | 28,65,78 | 55,95,100 | 85,125,120 | 150,175,165 | 78,74,68 |
| deep_ocean | Océan profond | 18,50,82 | 35,82,116 | 70,130,150 | 95,165,165 | 150,205,195 | 115,105,88 |
| black_sea_deep | Mer Noire / bleu sombre | 18,43,70 | 32,70,90 | 62,105,112 | 88,130,125 | 150,175,165 | 90,85,72 |
| muddy_water | Eau vaseuse / trouble | 70,85,75 | 100,110,85 | 135,130,95 | 155,145,105 | 190,185,150 | 125,105,70 |
| river_delta_silty | Delta / eau chargée en limon | 78,88,70 | 112,112,78 | 148,136,90 | 170,150,102 | 200,190,145 | 135,110,70 |
| mangrove_lagoon | Mangrove / lagune verte | 38,72,58 | 70,105,72 | 105,132,82 | 135,155,95 | 180,190,145 | 105,85,55 |
| amazon_brown | Fleuve tropical / brun organique | 80,62,42 | 120,88,55 | 155,112,70 | 180,135,90 | 210,185,145 | 110,82,52 |
| great_lakes_fresh | Grands lacs / eau douce | 32,75,98 | 55,110,125 | 90,150,145 | 125,175,160 | 185,210,195 | 120,115,95 |
| alpine_lake | Lac alpin / bleu vert clair | 22,76,110 | 48,125,145 | 95,175,170 | 135,205,190 | 210,235,220 | 120,125,110 |
| glacial_lake_milky | Lac glaciaire / turquoise laiteux | 55,98,120 | 85,135,150 | 130,180,180 | 170,210,200 | 225,240,230 | 150,150,135 |
| green_algae_lake | Lac végétal / algues vertes | 35,70,45 | 65,105,55 | 105,140,65 | 140,165,80 | 185,195,135 | 90,85,55 |
| volcanic_crater_lake | Lac volcanique / bleu sombre vert | 12,55,72 | 25,92,95 | 65,135,115 | 95,170,135 | 165,210,180 | 60,58,55 |
| salt_lake_pale | Lac salé / eau très pâle | 88,130,140 | 125,170,165 | 170,210,190 | 205,230,205 | 240,245,225 | 220,205,165 |
| dark_stormy | Mer sombre / tempête | 25,45,60 | 40,70,85 | 65,95,100 | 80,115,112 | 145,165,160 | 85,80,70 |
| custom | Manual RGB | --water-deep-rgb | --water-mid-rgb | --water-shallow-rgb | --water-lagoon-rgb | --water-surf-rgb | --water-seabed-rgb |

Le preset `atlantic_belle_ile` est le profil de base. Les presets tropicaux donnent une eau beaucoup plus claire. Les presets `muddy_water`, `river_delta_silty`, `mangrove_lagoon` et `amazon_brown` sont adaptés aux eaux troubles ou fluviales.

---

## 14. Textures sable et eau

### 14.1 Texture sable

Paramètres :

```text
--sand-texture-image
--sand-texture-strength
--sand-texture-scale
```

Effet :

- ajoute du grain visuel au sable ;
- ne change pas la zone de sable générée ;
- agit uniquement sur la couleur finale.

Valeurs conseillées :

```text
strength : 0.30 à 0.60
scale    : 1.0 à 3.0
```

### 14.2 Texture eau

Paramètres :

```text
--water-texture-image
--water-texture-strength
--water-texture-scale
--water-texture-smoothing
--water-texture-warp
```

Effet :

- ajoute vagues, bruit, reflets ou écume ;
- ne change pas les zones d'eau ;
- utilise une répétition miroir et une déformation pour limiter l'effet de tuile.

Valeurs conseillées :

```text
strength  : 0.15 à 0.35
scale     : 1.0 à 4.0
smoothing : 8 à 16
warp      : 12 à 24
```

---

## 15. Finition du bord de mer

| Paramètre | Rôle | Valeur conseillée |
|---|---|---|
| `surf-width` | Épaisseur de l'écume/ressac | 6 à 10 px |
| `foam-strength` | Intensité de l'écume et des bandes claires | 0.6 à 1.1 |
| `wet-sand-width` | Largeur du sable humide | 8 à 14 px |
| `shallow-width-factor` | Largeur de l'eau claire près du rivage | 0.30 à 0.50 |
| `mid-width-factor` | Transition eau claire → eau moyenne | 0.70 à 1.10 |
| `deep-width-factor` | Distance avant eau profonde | 1.25 à 1.70 |

Ces réglages changent l'apparence du bord de mer, pas la zone réellement générée.

---

## 16. Sorties

### 16.1 `satmap_final_10240.png`

Satmap finale corrigée.

### 16.2 `beach_mask_10240.png`

Masque final :

| Valeur | Signification |
|---|---|
| `0` | Terre / non plage |
| `128` | Eau |
| `255` | Plage / sable généré |

### 16.3 `generation_settings.json`

Sauvegarde complète des arguments et extras.

### 16.4 `RAPPORT_GENERATION_COMPLET.md`

Rapport lisible avec les chemins, profils, paramètres de rendu et réglages techniques.

### 16.5 `debug_masks/`

Créé uniquement avec `--debug-masks`. Contient notamment :

- `debug_category_map.png`
- `debug_water_mask.png`
- `debug_below_zero_mask.png`
- `debug_slope.png`
- `debug_dist_to_water.png`
- `debug_sand_core.png`
- `debug_sand_edge.png`
- `debug_land_side_mask.png` si applicable.

---

## 17. Validation et diagnostic

Commande :

```bash
py satmap_generator_optimized_presets.py --validate-only ^
  --heightmap input/heightmap.asc ^
  --mask input/mask.png ^
  --satmap input/satmap.png ^
  --layers input/layers.cfg ^
  --beach-layer-names hp_beach ^
  --sand-layer-names hp_sand
```

Le diagnostic vérifie :

- existence des fichiers ;
- format du mask et de la satmap ;
- lecture de `layers.cfg` ;
- présence des layers demandés ;
- dimensions de la heightmap ;
- estimation RAM ;
- cohérence de `target-size`, `chunk-rows` et `mask-color-tolerance`.

---

## 18. Réglages recommandés

### Profil stable 10K / 32-64 Go RAM

```text
target-size       : 10240
chunk-rows        : 2048 ou 4096
block-size        : 32
sand-preset       : 4 - Plage large
water-profile     : 1 - Standard
inland-profile    : 4 - Net marqué
sand-color        : belle_ile
water-color       : atlantic_belle_ile
mask tolerance    : 0 si PNG/BMP/TIFF
debug masks       : activé pour les tests, désactivé pour les runs propres
```

### Profil prudent

```text
chunk-rows        : 512 ou 1024
sand-preset       : 2 ou 3
inland-profile    : 2 ou 3
foam-strength     : 0.8
```

### Profil plage large

```text
sand-distance     : 70 à 85
sand-slope-max    : 0.22 à 0.25
sand-max-height   : 6 à 7
land-pass-distance: 24 à 32
land-pass-strength: 0.9 à 1.0
```

---

## 19. Erreurs courantes

| Erreur | Cause probable | Correction |
|---|---|---|
| `--beach-layer-names doit contenir au moins un nom de layer` | Aucun layer plage fourni. | Renseigner `hp_beach` ou une texture existante du `layers.cfg`. |
| `--sand-layer-names doit contenir au moins un nom de layer source` | Aucun layer source sable fourni. | Renseigner `hp_sand` ou une texture sable existante. |
| `Aucune texture source sable trouvée` | Le nom ne correspond pas au `layers.cfg` ou le mask n'utilise pas cette couleur. | Utiliser le bouton de vérification textures du launcher. |
| `JPG/JPEG refusé avec tolerance 0` | Le mask est compressé. | Exporter le mask en PNG ou mettre une tolérance > 0. |
| Plage trop large | Distance, hauteur ou pente trop permissives. | Réduire `sand-distance`, `sand-max-height` ou `sand-slope-max`. |
| Plage absente | Source sable non détectée, hauteur trop basse, pente trop restrictive. | Vérifier `sand-layer-names`, augmenter hauteur/distance ou pente. |
| Eau trop claire | Preset eau trop tropical ou facteurs trop faibles. | Utiliser `atlantic_belle_ile`, augmenter `deep-width-factor`. |
| Répétition visible dans l'eau | Texture eau trop petite ou warp/lissage insuffisants. | Augmenter `water-texture-scale`, `water-texture-smoothing`, `water-texture-warp`. |
| RAM trop élevée | `target-size` ou `chunk-rows` trop hauts. | Réduire `chunk-rows`; fermer les autres logiciels. |

---

## 20. Workflow conseillé

1. Préparer `heightmap.asc`, `mask.png`, `satmap.png`, `layers.cfg`.
2. Lancer le launcher.
3. Vérifier les chemins.
4. Vérifier les textures dans `layers.cfg`.
5. Lancer un diagnostic `validate-only`.
6. Générer avec `debug-masks` activé.
7. Contrôler `debug_sand_edge`, `debug_water_mask`, `debug_dist_to_water`.
8. Ajuster plage/eau/fusion.
9. Relancer sans debug pour une sortie propre.
10. Archiver le dossier `output_Vx` correspondant au rendu validé.

---

## 21. Notes importantes

- Le script ne modifie pas les fichiers source.
- Chaque génération par défaut crée un dossier `outputs/output_Vx`.
- Les textures sable/eau n'étendent pas les zones : elles changent uniquement le rendu visuel.
- Les noms de layers doivent correspondre exactement aux noms du `layers.cfg`, hors casse.
- Pour un mask compressé, la tolérance RGB peut aider, mais le PNG reste fortement recommandé.
