# Beach Satmap Generator — README utilisateur

Documentation simplifiée pour utiliser le générateur de satmap avec l'interface graphique.

Cette version est destinée à l'utilisateur final. Elle garde uniquement les informations nécessaires pour installer, lancer, régler et récupérer les fichiers générés.

---

## 1. À quoi sert cet outil ?

Beach Satmap Generator sert à créer une satmap plus propre pour une carte DayZ, surtout autour des plages, de l'eau et du bord de mer.

À partir de quatre fichiers source, l'outil génère :

- une satmap finale corrigée ;
- un beach mask ;
- un dossier de sortie versionné pour ne pas écraser les anciens résultats.

Il est prévu pour travailler avec des cartes de grande taille, par exemple `10240 x 10240 px`.

---

## 2. Fichiers nécessaires

Place les fichiers suivants dans le même dossier :

```text
satmap_gui_launcher.pyw
satmap_generator_optimized_presets.py
input/
  heightmap.asc
  mask.png
  satmap.png
  layers.cfg
```

### Rôle des fichiers

| Fichier | Utilité |
|---|---|
| `heightmap.asc` | Sert à détecter l'altitude, l'eau, la pente et les zones côtières. |
| `mask.png` | Sert à reconnaître les textures grâce aux couleurs du `layers.cfg`. |
| `satmap.png` | Image satellite de base qui sera corrigée. |
| `layers.cfg` | Relie les couleurs du mask aux noms de textures DayZ. |

Formats image acceptés : `PNG`, `JPG`, `JPEG`, `BMP`, `TIFF`.

Pour le `mask`, le format recommandé est `PNG`, `BMP` ou `TIFF`. Évite le `JPG`, car il peut modifier les couleurs du mask.

---

## 3. Installation

### Méthode simple depuis le launcher

1. Lance `satmap_gui_launcher.pyw`.
2. Va dans l'onglet **Fichiers**.
3. Clique sur **Installer dépendances** si les dépendances ne sont pas encore installées.

### Méthode manuelle

Ouvre un terminal dans le dossier du script et lance :

```bash
py -m pip install numpy pillow scipy
```

---

## 4. Lancer le programme

Tu peux lancer l'interface de deux façons :

```bash
py satmap_gui_launcher.pyw
```

ou en double-cliquant sur :

```text
satmap_gui_launcher.pyw
```

L'interface contient quatre onglets :

1. **Fichiers**
2. **Profils**
3. **Technique**
4. **Lancement**

---

## 5. Onglet Fichiers

Cet onglet sert à choisir les fichiers utilisés par le générateur.

Vérifie surtout :

- le chemin du script générateur ;
- le chemin de la heightmap ;
- le chemin du mask ;
- le chemin de la satmap ;
- le chemin du `layers.cfg`.

### Textures DayZ à reconnaître

Tu dois indiquer les textures que le script doit utiliser pour reconnaître la plage, le sable et éventuellement la terre côté intérieur.

| Champ | Utilisation |
|---|---|
| Texture déjà plage | Texture déjà considérée comme plage ou littoral. |
| Texture sable à agrandir | Texture source que le script doit étendre autour du rivage. |
| Texture terre à mélanger | Optionnel. Limite la fusion sable → terre à une texture précise. |

Exemple :

```text
Texture déjà plage : hp_beach
Texture sable à agrandir : hp_sand
Texture terre à mélanger : cp_grass
```

Si tu utilises une texture custom, écris son nom exactement comme dans `layers.cfg`.

---

## 6. Onglet Profils

C'est l'onglet principal pour régler le rendu.

### Réglages recommandés pour commencer

| Réglage | Valeur conseillée |
|---|---|
| Plage : taille et pente | `4 - Plage large` ou `3 - Équilibré` |
| Eau : niveaux d'altitude | `1 - Standard` |
| Fusion sable → terre | `4 - Net marqué` ou `3 - Net naturel` |
| Type de sable | `belle_ile` ou `atlantic_light` |
| Type d'eau | `atlantic_belle_ile` |
| Texture sable | Optionnel |
| Texture eau | Optionnel |

### Plage : taille et pente

Ces réglages contrôlent où le sable peut être généré.

| Paramètre | Effet |
|---|---|
| Largeur plage max | Plus la valeur est haute, plus la plage peut aller loin du rivage. |
| Pente autorisée | Plus la valeur est basse, plus le script évite les talus et falaises. |
| Hauteur plage max | Altitude maximale où le sable peut être créé. |

Conseil : commence avec `4 - Plage large`, puis ajuste si le sable va trop loin ou pas assez loin.

### Eau : niveaux d'altitude

Ces réglages déterminent quelles zones sont considérées comme eau ou terre selon la heightmap.

Dans la plupart des cas, garde :

```text
1 - Standard
```

Utilise un profil plus bas ou plus haut seulement si ton niveau d'eau ne correspond pas bien à ta heightmap.

### Fusion sable → terre

Ce réglage améliore la transition entre la plage et la terre.

| Profil | Résultat |
|---|---|
| Désactivé | Pas de transition côté terre. |
| Net léger | Transition courte et discrète. |
| Net naturel | Bon compromis. |
| Net marqué | Transition plus visible et propre. |
| Dune courte | Effet de dune plus présent. |

---

## 7. Couleurs et textures

### Couleurs du sable

Exemples utiles :

| Preset | Utilisation |
|---|---|
| `belle_ile` | Sable naturel clair, bon choix par défaut. |
| `atlantic_light` | Côte atlantique claire. |
| `golden` | Sable plus doré. |
| `pale_white` | Sable très clair. |
| `grey_shell` | Sable gris/coquillier. |
| `dark_volcanic` | Sable sombre. |
| `red_ochre` | Sable ocre/rouge. |

### Couleurs de l'eau

Exemples utiles :

| Preset | Utilisation |
|---|---|
| `atlantic_belle_ile` | Bon choix par défaut pour une côte Atlantique. |
| `atlantic_open_ocean` | Eau plus profonde et bleue. |
| `tropical_lagoon` | Eau turquoise claire. |
| `mediterranean_blue` | Bleu méditerranéen. |
| `fjord_dark` | Eau sombre. |
| `muddy_water` | Eau trouble ou vaseuse. |

### Textures optionnelles

Les textures sable et eau ajoutent du détail visuel. Elles ne changent pas la zone générée.

| Texture | Intensité conseillée | Taille conseillée |
|---|---:|---:|
| Sable | `0.30` à `0.60` | `1.0` |
| Eau | `0.15` à `0.35` | `1.0` |

---

## 8. Onglet Technique

### Résolution finale

Pour une carte DayZ 10K, utilise :

```text
10240
```

### Mémoire / vitesse

Ce réglage contrôle le nombre de lignes traitées par paquet.

| Valeur | Utilisation |
|---:|---|
| `512` / `1024` | Très sûr, mais plus lent. |
| `2048` | Bon compromis. |
| `4096` | Recommandé si tu as 32 ou 64 Go de RAM. |
| `8192` | Plus rapide, mais demande plus de RAM. |

Pour commencer, utilise `2048`.

### Tolérance couleurs du mask

Garde généralement :

```text
0
```

Utilise une valeur supérieure uniquement si ton mask a été compressé ou modifié et que les couleurs ne correspondent plus exactement au `layers.cfg`.

### Images de diagnostic

Active **Créer images de diagnostic** seulement si tu veux comprendre un problème de génération.

---

## 9. Générer la satmap

Dans l'onglet **Lancement** :

1. Clique sur **Vérifier les fichiers**.
2. Corrige les erreurs si nécessaire.
3. Clique sur **Lancer la génération**.
4. Attends la fin du traitement.
5. Récupère les fichiers dans le dossier `outputs`.

---

## 10. Fichiers générés

Les sorties sont créées dans un dossier du type :

```text
outputs/output_V1/
outputs/output_V2/
outputs/output_V3/
```

Chaque génération crée une nouvelle version pour éviter d'écraser les anciens résultats.

Fichiers principaux :

| Fichier | Utilité |
|---|---|
| `satmap_final_10240.png` | Satmap finale à utiliser dans ton projet. |
| `beach_mask_10240.png` | Mask de plage/eau généré. |

Fichiers complémentaires :

| Fichier | Utilité |
|---|---|
| `generation_settings.json` | Sauvegarde des réglages utilisés. |
| `RAPPORT_GENERATION_COMPLET.md` | Rapport lisible de la génération. |
| `debug_masks/` | Images de diagnostic, uniquement si l'option est activée. |

---

## 11. Problèmes courants

### Le script ne trouve pas mes textures

Vérifie que les noms saisis correspondent exactement aux noms présents dans `layers.cfg`.

Exemple :

```text
hp_sand
```

n'est pas la même chose que :

```text
hp sand
```

### Le mask ne correspond pas au layers.cfg

Utilise de préférence un mask en `PNG`, `BMP` ou `TIFF`.

Si ton mask est en `JPG`, les couleurs peuvent être altérées. Dans ce cas, repasse par un format sans perte ou augmente légèrement la tolérance couleur.

### Le sable va trop loin dans les terres

Diminue :

- Largeur plage max ;
- Hauteur plage max ;
- Pente autorisée ;
- Force fusion terre.

### Il n'y a pas assez de sable

Augmente progressivement :

- Largeur plage max ;
- Hauteur plage max ;
- Pente autorisée.

### La génération est lente

C'est normal avec une satmap 10K.

Pour améliorer la vitesse :

- ferme les logiciels lourds ;
- utilise `chunk rows = 4096` si ton PC est stable ;
- garde une résolution adaptée à ton projet.

### Le programme manque de RAM

Réduis :

```text
Mémoire / vitesse
```

Essaie `1024` ou `2048`.

---

## 12. Utilisation en ligne de commande

L'utilisation recommandée reste le launcher graphique.

Commande simple :

```bash
py satmap_generator_optimized_presets.py
```

Exemple avec une carte 10K :

```bash
py satmap_generator_optimized_presets.py --target-size 10240 --chunk-rows 2048 --sand-preset 4
```

---

## 13. Réglage conseillé pour un premier test

```text
Plage : 4 - Plage large
Eau : 1 - Standard
Fusion sable → terre : 4 - Net marqué
Type de sable : belle_ile
Type d'eau : atlantic_belle_ile
Résolution finale : 10240
Mémoire / vitesse : 2048
Tolérance couleurs du mask : 0
Debug masks : désactivé
```

---

## 14. Conseil important

Fais toujours une première génération avec les réglages recommandés avant de personnaliser les couleurs, les textures ou les valeurs avancées.

Cela permet de vérifier que les fichiers source, le mask et le `layers.cfg` sont correctement reconnus.
