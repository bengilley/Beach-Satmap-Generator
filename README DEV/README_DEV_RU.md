# Полная документация — Beach Satmap Generator

Документированные версии: генератор `1.3.5` / launcher `1.7.7`.

Документ описывает работу `satmap_generator_optimized_presets.py` и `satmap_gui_launcher.pyw`: входные файлы, алгоритм, настройки, профили, выходные файлы, диагностику и типичные ошибки.

---

## 1. Назначение

Проект создаёт улучшенную satmap для DayZ в зоне побережья: пляжи, градиент воды, оттенок морского дна, прибой, мокрый песок, переход песок → суша и цветовую коррекцию по категориям terrain.

Основные входные файлы:

```text
input/heightmap.asc
input/mask.png
input/satmap.png
input/layers.cfg
```

Основные выходные файлы:

```text
outputs/output_Vx/satmap_final_10240.png
outputs/output_Vx/beach_mask_10240.png
outputs/output_Vx/generation_settings.json
outputs/output_Vx/RAPPORT_GENERATION_COMPLET.md
```

---

## 2. Файлы проекта

| Файл | Назначение |
|---|---|
| `satmap_generator_optimized_presets.py` | Движок генерации. Запускается из командной строки или через launcher. |
| `satmap_gui_launcher.pyw` | Графический интерфейс Tkinter для настройки и запуска без `.bat`. |
| `info.png` | Иконка для подсказок в интерфейсе. |
| `custom_profiles.json` | Создаётся launcher для пользовательских профилей. |
| `launcher_settings.json` | Создаётся launcher для сохранения путей и последних настроек. |

---

## 3. Установка

### Требования

- Рекомендуется Windows.
- Рекомендуется Python 3.10+.
- Зависимости Python:

```bash
py -m pip install numpy pillow scipy
```

Tkinter обычно уже входит в Python для Windows.

### Рекомендуемая структура

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

Launcher может автоматически найти стандартные файлы в папке `input/`.

---

## 4. Быстрый запуск

### Через GUI

Запусти:

```text
satmap_gui_launcher.pyw
```

Далее:

1. **1. Files / Файлы**: проверь пути к generator, heightmap, mask, satmap и layers.cfg.
2. **2. Profiles / Профили**: выбери ширину пляжа, уровни воды, смешивание с сушей, цвета и текстуры.
3. **3. Technical / Техника**: настрой разрешение, память/скорость и диагностику.
4. **4. Run / Запуск**: проверь команду и запусти генерацию.

### Через CLI

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

---

## 5. Обязательные входные файлы

### `heightmap.asc`

ASC heightmap используется для определения воды/суши, расчёта уклона, ограничения песка по высоте и расчёта расстояния до берега.

### `mask.png`

Изображение mask terrain. Каждый RGB-цвет должен соответствовать цвету layer в `layers.cfg`.

Поддерживаемые форматы: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tif`, `.tiff`.

Рекомендуются PNG/BMP/TIFF. JPG/JPEG отклоняется при `--mask-color-tolerance 0`, потому что сжатие меняет RGB-цвета.

### `satmap.png`

Базовая satellite texture. Генератор изменяет размер и корректирует её визуально по категориям terrain.

### `layers.cfg`

Связывает RGB-цвета mask с именами DayZ layers. Ожидаемый формат:

```cpp
texture_name[] = {{ R, G, B }};
```

Имена beach/sand/land textures должны существовать в этом файле.

---

## 6. Внутренний алгоритм

1. Чтение `layers.cfg` и создание RGB → layer легенды.
2. Загрузка ASC heightmap.
3. Resize heightmap, mask и satmap до `target-size`.
4. Расчёт нормализованного уклона.
5. Классификация пикселей mask по категориям terrain.
6. Поиск source sand layer из `--sand-layer-names`.
7. Локальное расширение зоны source sand.
8. Определение воды и суши по высоте.
9. Расчёт расстояния до берега.
10. Создание многоуровневого шума для естественных вариаций.
11. Базовая цветовая коррекция satmap по категориям.
12. Создание sand mask по условиям distance + height + slope + source layer + allowed categories.
13. Рендеринг water/beach: deep water → shallow water → surf → wet sand → dry sand.
14. Второй проход смешивания песок → суша.
15. Сохранение `beach_mask_10240.png`.
16. Сохранение финальной satmap.
17. Запись отчётов, если они не отключены.

---

## 7. Разделы GUI

### `1. Files`

Настройка путей к generator, heightmap, mask, satmap, layers.cfg и textures.

Список vanilla textures:

```text
cp_grass, cp_dirt, cp_rock, cp_concrete1, cp_concrete2, cp_broadleaf_dense1, cp_broadleaf_dense2, cp_broadleaf_sparse1, cp_broadleaf_sparse2, cp_conifer_common1, cp_conifer_common2, cp_conifer_moss1, cp_conifer_moss2, cp_grass_tall, cp_gravel, en_flowers1, en_flowers2, en_flowers3, en_forest_con, en_forest_dec, en_grass1, en_grass2, en_soil, en_stones, en_stubble, en_tarmac_old, sa_forest_spruce, sa_grass_brown, sa_concrete, sa_beach, sa_forest_birch, sa_gravel, sa_snow, sa_snow_forest, sa_volcanic_red, sa_volcanic_yellow, sa_grass_green
```

### `2. Profiles`

Профили пляжа, уровни воды, переход к суше, цвета песка, texture sand, цвета воды, texture water и финальная обработка берега.

### `3. Technical`

Финальное разрешение, chunk rows, размер цветовых блоков, допуск цвета mask и debug masks.

### `4. Run`

Сгенерированная команда, validation, запуск, log и progress.

---

## 8. Профили пляжа

### Engine presets

| ID | Имя | Дистанция px | Макс. уклон | Макс. высота м | Описание |
| --- | --- | --- | --- | --- | --- |
| 1 | tres_propre | 45.0 | 0.16 | 4.8 | Тонкий, строго контролируемый пляж |
| 2 | propre_marge | 55.0 | 0.18 | 5.2 | Немного больше песка без сильного выхода за пределы |
| 3 | equilibre | 60.0 | 0.2 | 5.5 | Хорошая базовая настройка |
| 4 | large | 70.0 | 0.22 | 6.0 | Более заметные пляжи с безопасным запасом |
| 5 | tres_large | 85.0 | 0.25 | 7.0 | Песок уходит дальше вглубь суши |
| 6 | agressif | 100.0 | 0.28 | 8.0 | Может начать заходить на откосы |
| 7 | tres_agressif | 120.0 | 0.32 | 10.0 | Высокий риск песка слишком высоко/далеко |
| 8 | custom | 70.0 | 0.22 | 6.0 | Пользовательские значения из меню |

### GUI profiles

| GUI профиль | CLI preset | Ширина пляжа px | Уклон | Высота м | Назначение |
| --- | --- | --- | --- | --- | --- |
| 1 - Bord net | 1 | 45.0 | 0.16 | 4.8 | Тонкий и ненавязчивый пляж |
| 2 - Bord naturel | 2 | 55.0 | 0.18 | 5.2 | Умеренный запас |
| 3 - Équilibré | 3 | 60.0 | 0.2 | 5.5 | Универсальная настройка |
| 4 - Plage large | 4 | 70.0 | 0.22 | 6.0 | Универсальный широкий пляж |
| 5 - Grande plage | 5 | 85.0 | 0.25 | 7.0 | Более заметный песок |
| 6 - Extension forte | 6 | 100.0 | 0.28 | 8.0 | Может заходить на откосы |
| 7 - Extension max | 7 | 120.0 | 0.32 | 10.0 | Только для теста |
| 8 - Personnalisé | 8 | 70.0 | 0.22 | 6.0 | Свободные значения |

Профиль `3` — базовый сбалансированный. Профиль `4` — хороший вариант для более заметного берега. Профили `6` и `7` агрессивные и могут поднять песок слишком высоко.

---

## 9. Профили воды

| GUI профиль | Глубокая вода ниже м | Вода до м | Суша от м | Назначение |
| --- | --- | --- | --- | --- |
| 1 - Standard | 0.0 | 1.0 | 1.0 | Вода <= 1.0 м |
| 2 - Littoral bas | 0.0 | 0.8 | 0.8 | Низкий уровень побережья |
| 3 - Eau plus large | 0.0 | 1.3 | 1.3 | Более заметная вода |
| 4 - Personnalisé | 0.0 | 1.0 | 1.0 | Свободные уровни |

Правило:

```text
water-start-level < water-end-level <= land-start-level < sand-max-height
```

---

## 10. Смешивание песок → суша

| GUI профиль | Дистанция px | Сила | Назначение |
| --- | --- | --- | --- |
| 1 - Désactivé | 0.0 | 0.0 | Без ретуши со стороны суши |
| 2 - Net léger | 12.0 | 0.6 | Ореол почти убран |
| 3 - Net naturel | 18.0 | 0.78 | Сбалансированная ретушь |
| 4 - Net marqué | 24.0 | 0.92 | Более заметный переход |
| 5 - Dune courte | 32.0 | 1.0 | Выраженный короткий dune-эффект |
| 6 - Personnalisé | 18.0 | 0.78 | Свободные значения |

Distance или strength = `0` отключает второй проход. Большие значения дают сильный переход, но могут загрязнить внутреннюю сушу.

---

## 11. Полная справка CLI

| Опция | По умолчанию | Значения | Назначение |
| --- | --- | --- | --- |
| --heightmap | input/heightmap.asc | ASC | Исходная ASC heightmap для высот, воды, уклонов и берега. |
| --mask | input/mask.png | PNG/JPG/BMP/TIF | Terrain mask. Цвета должны совпадать с layers.cfg. |
| --satmap | input/satmap.png | PNG/JPG/BMP/TIF | Базовая satmap, которую генератор корректирует и улучшает. |
| --layers | input/layers.cfg | CFG | Файл соответствия RGB-цветов mask и имён DayZ layers. |
| --output-satmap | outputs/output_Vx/satmap_final_10240.png | PNG | Финальная satmap. При имени по умолчанию создаются output_V1, output_V2 и т.д. |
| --output-beach-mask | outputs/output_Vx/beach_mask_10240.png | PNG | Финальный mask пляжа/воды. |
| --target-size | 10240 | 512–30000 | Финальное квадратное разрешение. Для DayZ 10K обычно 10240. |
| --chunk-rows | 512 CLI / 2048 GUI | 64–8192 | Количество строк за chunk. Больше = быстрее, но больше RAM. |
| --block-size | 32 | 4–512 | Размер блоков цветовой коррекции terrain. |
| --sand-preset | manual/default или GUI profile | 1-8 или имя | Beach preset как база перед ручными override. |
| --sand-distance | preset | 1–300 px | Максимальная дистанция от берега для генерации песка. |
| --sand-slope-max | preset | 0.01–1.00 | Максимальный нормализованный уклон. Меньше = лучше избегает скал/откосов. |
| --sand-max-height | preset | 0.1–50 m | Максимальная высота появления песка. |
| --water-start-level | 0.0 | -100–100 m | Ниже этого уровня вода считается глубже/темнее. |
| --water-end-level | 1.0 | -100–100 m | Верхняя граница высоты, считающаяся водой. |
| --land-start-level | 1.0 | -100–100 m | Высота, с которой terrain считается сушей/надводным пляжем. |
| --land-pass-distance | 18 CLI / GUI profile | 0–160 px | Ширина второго прохода песок → суша. |
| --land-pass-strength | 0.72 CLI / GUI profile | 0–1 | Сила внутреннего перехода. |
| --beach-layer-names | обязательно, GUI: hp_beach | список через запятые | Layers, уже считающиеся пляжем/берегом. |
| --sand-layer-names | обязательно, GUI: hp_sand | список через запятые | Source layers, разрешающие расширение песка. |
| --land-layer-names | пусто | опционально | Опциональные inland layers для ограничения перехода. Пусто = общий режим. |
| --sand-color-preset | belle_ile | preset или custom | Палитра цвета песка. |
| --sand-color-strength | 1.0 | 0.0–1.5 | Интенсивность выбранной палитры песка. |
| --sand-dry-rgb | None | R,G,B или #RRGGBB | Custom override сухого песка в custom mode. |
| --sand-wet-rgb | None | R,G,B или #RRGGBB | Custom override мокрого песка. |
| --sand-shell-rgb | None | R,G,B или #RRGGBB | Custom override светлой/ракушечной вариации. |
| --wet-beach-rgb | None | R,G,B или #RRGGBB | Custom мокрый край между водой и пляжем. |
| --seabed-rgb | None | R,G,B или #RRGGBB | Custom песчаное дно рядом с берегом. |
| --sand-texture-image | пусто | изображение | Опциональная texture для зернистости песка без изменения зон. |
| --sand-texture-strength | 0.45 | 0.0–1.0 | Сила texture песка. |
| --sand-texture-scale | 1.0 | 0.1–8.0 | Масштаб повторения texture песка. |
| --water-color-preset | atlantic_belle_ile | preset или custom | Палитра градиента воды. |
| --water-color-strength | 1.0 | 0.0–1.5 | Интенсивность выбранной палитры воды. |
| --water-deep-rgb | None | R,G,B или #RRGGBB | Custom цвет глубокой воды. |
| --water-mid-rgb | None | R,G,B или #RRGGBB | Custom цвет средней воды. |
| --water-shallow-rgb | None | R,G,B или #RRGGBB | Custom цвет мелководья. |
| --water-lagoon-rgb | None | R,G,B или #RRGGBB | Custom цвет лагуны / очень светлой воды. |
| --water-surf-rgb | None | R,G,B или #RRGGBB | Custom цвет прибоя / пены. |
| --water-seabed-rgb | None | R,G,B или #RRGGBB | Custom цвет дна под водой. |
| --water-texture-image | пусто | изображение | Опциональная texture для волн, шума, пены или отражений. |
| --water-texture-strength | 0.25 | 0.0–1.0 | Сила texture воды. |
| --water-texture-scale | 1.0 | 0.1–8.0 | Масштаб texture воды. |
| --water-texture-smoothing | 12.0 | 0.0–64.0 px | Сглаживание texture воды перед повторением. |
| --water-texture-warp | 18.0 | 0.0–96.0 px | Искажение координат для уменьшения видимых повторов. |
| --surf-width | 8.0 | 1–128 px | Толщина светлой полосы прибоя. |
| --shallow-width-factor | 0.42 | 0.05–5.0 | Множитель ширины мелководья на основе sand-distance. |
| --mid-width-factor | 0.95 | 0.05–5.0 | Множитель ширины средней воды. |
| --deep-width-factor | 1.70 | 0.05–5.0 | Дистанция до глубокой/тёмной воды. |
| --foam-strength | 1.0 | 0–2 | Визуальная сила пены и контурных полос. |
| --wet-sand-width | 10.0 | 1–128 px | Ширина мокрого песка у воды. |
| --mask-color-tolerance | 0 | 0–255 | RGB tolerance для match mask/layers.cfg. 0 = exact, JPG запрещён. |
| --debug-masks | false | флаг | Создаёт diagnostic images в debug_masks. |
| --validate-only | false | флаг | Проверяет файлы и настройки без генерации. |
| --no-report | false | флаг | Отключает generation_settings.json и RAPPORT_GENERATION_COMPLET.md. |
| --list-sand-presets | false | флаг | Выводит beach presets и завершает работу. |
| --list-sand-color-presets | false | флаг | Выводит sand color presets и завершает работу. |
| --list-water-color-presets | false | флаг | Выводит water color presets и завершает работу. |

---

## 12. Presets цвета песка

| Preset | Описание | Сухой | Мокрый | Shell | Мокрый край | Дно |
| --- | --- | --- | --- | --- | --- | --- |
| belle_ile | Бель-Иль / натуральный светлый песок | 222,204,178 | 190,168,145 | 208,196,182 | 181,156,128 | 160,120,90 |
| atlantic_light | Светлая Атлантика | 230,214,184 | 196,176,150 | 220,210,196 | 188,164,134 | 170,132,98 |
| golden | Золотой песок | 226,190,126 | 176,140,95 | 218,200,164 | 166,132,92 | 152,112,72 |
| pale_white | Белый / очень светлый песок | 238,230,204 | 205,194,170 | 236,230,218 | 196,184,160 | 176,160,130 |
| grey_shell | Серый / ракушечный песок | 200,196,184 | 158,154,145 | 220,218,210 | 150,145,132 | 128,120,108 |
| dark_volcanic | Тёмный / вулканический песок | 112,105,96 | 70,68,66 | 150,145,135 | 82,76,70 | 74,68,62 |
| red_ochre | Охристый / красный песок | 196,128,82 | 132,82,58 | 205,176,150 | 144,92,62 | 122,76,52 |
| custom | Ручной RGB | --sand-dry-rgb | --sand-wet-rgb | --sand-shell-rgb | --wet-beach-rgb | --seabed-rgb |

Формат custom RGB:

```text
R,G,B
#RRGGBB
```

---

## 13. Presets цвета воды

| Preset | Описание | Глубокая | Средняя | Мелкая | Лагуна | Прибой | Дно |
| --- | --- | --- | --- | --- | --- | --- | --- |
| atlantic_belle_ile | Атлантика / Бель-Иль | 58,88,122 | 70,112,142 | 93,149,156 | 118,181,174 | 156,202,190 | 160,120,90 |
| atlantic_open_ocean | Открытая Атлантика / глубокий синий | 28,72,112 | 45,100,135 | 76,135,150 | 105,165,160 | 165,205,195 | 135,115,90 |
| atlantic_grey_coast | Серое атлантическое побережье / Ла-Манш | 48,70,88 | 72,96,108 | 105,130,125 | 132,154,145 | 178,190,178 | 125,115,100 |
| tropical_lagoon | Тропическая лагуна | 20,95,145 | 35,165,185 | 95,220,210 | 130,235,220 | 220,245,230 | 210,190,130 |
| caribbean_turquoise | Карибы / светлая бирюза | 0,87,143 | 18,156,188 | 72,218,220 | 125,238,225 | 230,248,238 | 218,202,145 |
| maldives_atoll | Мальдивы / атолл с белым песком | 5,76,132 | 25,150,190 | 85,225,220 | 155,242,225 | 235,250,238 | 225,207,150 |
| coral_reef_shallow | Коралловый риф / мелководье | 16,80,138 | 30,145,170 | 95,205,190 | 150,225,205 | 225,245,225 | 190,165,120 |
| mediterranean_blue | Средиземное море / минеральный синий | 25,75,138 | 42,110,165 | 70,155,185 | 105,190,195 | 180,220,215 | 150,130,95 |
| aegean_clear | Эгейское море / светло-синий | 18,80,150 | 35,125,180 | 75,175,205 | 110,205,210 | 195,230,225 | 165,145,105 |
| adriatic_clear | Адриатика / светло-сине-зелёный | 35,85,120 | 55,125,150 | 90,170,175 | 130,200,190 | 200,225,210 | 155,140,110 |
| red_sea_clear | Красное море / очень прозрачная вода | 15,72,132 | 28,130,170 | 78,190,195 | 120,220,205 | 220,240,220 | 190,165,115 |
| pacific_deep | Глубокий Тихий океан | 12,48,95 | 30,80,130 | 62,125,155 | 90,160,165 | 160,210,200 | 105,95,85 |
| indian_ocean | Индийский океан | 10,70,125 | 28,125,160 | 70,185,190 | 115,215,200 | 220,240,225 | 190,175,125 |
| cold_ocean | Холодный океан | 35,65,85 | 55,95,115 | 90,135,140 | 105,155,155 | 180,205,205 | 120,115,105 |
| north_sea_grey | Северное море / серо-зелёный | 45,65,78 | 65,88,95 | 92,118,112 | 120,140,130 | 170,185,175 | 115,105,88 |
| baltic_green | Балтика / холодный зелёный | 36,70,72 | 58,100,88 | 90,130,100 | 125,155,115 | 178,195,165 | 115,105,75 |
| arctic_glacial | Арктика / ледяная вода | 25,70,95 | 55,115,135 | 100,165,170 | 145,205,200 | 220,238,230 | 130,130,120 |
| fjord_dark | Фьорд / тёмная вода | 15,42,58 | 28,65,78 | 55,95,100 | 85,125,120 | 150,175,165 | 78,74,68 |
| deep_ocean | Глубокий океан | 18,50,82 | 35,82,116 | 70,130,150 | 95,165,165 | 150,205,195 | 115,105,88 |
| black_sea_deep | Чёрное море / тёмно-синий | 18,43,70 | 32,70,90 | 62,105,112 | 88,130,125 | 150,175,165 | 90,85,72 |
| muddy_water | Илистая / мутная вода | 70,85,75 | 100,110,85 | 135,130,95 | 155,145,105 | 190,185,150 | 125,105,70 |
| river_delta_silty | Дельта / вода с илом | 78,88,70 | 112,112,78 | 148,136,90 | 170,150,102 | 200,190,145 | 135,110,70 |
| mangrove_lagoon | Мангры / зелёная лагуна | 38,72,58 | 70,105,72 | 105,132,82 | 135,155,95 | 180,190,145 | 105,85,55 |
| amazon_brown | Тропическая река / органический коричневый | 80,62,42 | 120,88,55 | 155,112,70 | 180,135,90 | 210,185,145 | 110,82,52 |
| great_lakes_fresh | Великие озёра / пресная вода | 32,75,98 | 55,110,125 | 90,150,145 | 125,175,160 | 185,210,195 | 120,115,95 |
| alpine_lake | Альпийское озеро / светлый сине-зелёный | 22,76,110 | 48,125,145 | 95,175,170 | 135,205,190 | 210,235,220 | 120,125,110 |
| glacial_lake_milky | Ледниковое озеро / молочная бирюза | 55,98,120 | 85,135,150 | 130,180,180 | 170,210,200 | 225,240,230 | 150,150,135 |
| green_algae_lake | Заросшее озеро / зелёные водоросли | 35,70,45 | 65,105,55 | 105,140,65 | 140,165,80 | 185,195,135 | 90,85,55 |
| volcanic_crater_lake | Вулканическое озеро / тёмный сине-зелёный | 12,55,72 | 25,92,95 | 65,135,115 | 95,170,135 | 165,210,180 | 60,58,55 |
| salt_lake_pale | Солёное озеро / очень бледная вода | 88,130,140 | 125,170,165 | 170,210,190 | 205,230,205 | 240,245,225 | 220,205,165 |
| dark_stormy | Тёмное штормовое море | 25,45,60 | 40,70,85 | 65,95,100 | 80,115,112 | 145,165,160 | 85,80,70 |
| custom | Ручной RGB | --water-deep-rgb | --water-mid-rgb | --water-shallow-rgb | --water-lagoon-rgb | --water-surf-rgb | --water-seabed-rgb |

`atlantic_belle_ile` — базовый preset. Tropical presets делают воду гораздо светлее. Muddy/delta/mangrove/river presets подходят для мутной или речной воды.

---

## 14. Текстуры песка и воды

### Texture sand

```text
--sand-texture-image
--sand-texture-strength
--sand-texture-scale
```

Добавляет визуальную зернистость песка. Не изменяет саму зону песка.

Рекомендуется:

```text
strength : 0.30–0.60
scale    : 1.0–3.0
```

### Texture water

```text
--water-texture-image
--water-texture-strength
--water-texture-scale
--water-texture-smoothing
--water-texture-warp
```

Добавляет волны, шум, отражения или пену без изменения water areas. Mirror tiling и warp уменьшают видимые повторы.

Рекомендуется:

```text
strength  : 0.15–0.35
scale     : 1.0–4.0
smoothing : 8–16
warp      : 12–24
```

---

## 15. Финальная обработка берега

| Параметр | Назначение | Рекомендация |
|---|---|---|
| `surf-width` | Толщина полосы прибоя/пены | 6–10 px |
| `foam-strength` | Интенсивность светлых полос и пены | 0.6–1.1 |
| `wet-sand-width` | Ширина мокрого песка | 8–14 px |
| `shallow-width-factor` | Ширина светлого мелководья у берега | 0.30–0.50 |
| `mid-width-factor` | Переход shallow → mid water | 0.70–1.10 |
| `deep-width-factor` | Дистанция до глубокой/тёмной воды | 1.25–1.70 |

Эти настройки меняют только визуальный вид берега, не зону генерации.

---

## 16. Выходные файлы

| Файл | Описание |
|---|---|
| `satmap_final_10240.png` | Финальная corrected satmap. |
| `beach_mask_10240.png` | Mask: `0` суша, `128` вода, `255` generated beach/sand. |
| `generation_settings.json` | Все аргументы и дополнительные данные генерации. |
| `RAPPORT_GENERATION_COMPLET.md` | Читаемый отчёт. |
| `debug_masks/` | Диагностические masks, создаются только с `--debug-masks`. |

---

## 17. Validation

```bash
py satmap_generator_optimized_presets.py --validate-only ^
  --heightmap input/heightmap.asc ^
  --mask input/mask.png ^
  --satmap input/satmap.png ^
  --layers input/layers.cfg ^
  --beach-layer-names hp_beach ^
  --sand-layer-names hp_sand
```

Validation проверяет наличие файлов, форматы, layer names, размеры ASC, оценку RAM и диапазоны основных значений.

---

## 18. Рекомендуемые настройки

Стабильный профиль 10K:

```text
target-size       : 10240
chunk-rows        : 2048 или 4096
block-size        : 32
sand-preset       : 4 - Wide beach
water-profile     : 1 - Standard
inland-profile    : 4 - Strong blend
sand-color        : belle_ile
water-color       : atlantic_belle_ile
mask tolerance    : 0 для PNG/BMP/TIFF
debug masks       : включить для тестов, выключить для финального run
```

---

## 19. Типичные проблемы

| Проблема | Причина | Исправление |
|---|---|---|
| Нет beach layer name | Пустой `--beach-layer-names`. | Указать `hp_beach` или существующую texture из layers.cfg. |
| Нет sand source layer | Пустой `--sand-layer-names`. | Указать `hp_sand` или существующую sand texture. |
| Source sand не найден | Несовпадение имени или mask не использует этот цвет. | Проверить names в layers.cfg. |
| JPG отклонён | Mask сжат, tolerance = 0. | Использовать PNG или tolerance > 0. |
| Пляж слишком широкий | Distance/height/slope слишком permissive. | Уменьшить sand distance, max height или slope. |
| Пляж не создаётся | Source layer отсутствует или ограничения слишком строгие. | Проверить source layer и ослабить distance/height/slope. |
| Видны повторы в воде | Texture маленькая или слабый smoothing/warp. | Увеличить scale, smoothing и warp. |
| Много RAM | Большой target size или chunk rows. | Уменьшить chunk rows и закрыть другие программы. |

---

## 20. Рекомендуемый workflow

1. Подготовить input files.
2. Запустить GUI.
3. Проверить пути и layer names.
4. Запустить validation.
5. Сгенерировать один раз с debug masks.
6. Проверить debug masks.
7. Настроить beach/water/blend.
8. Сгенерировать финальный результат без debug.
9. Сохранить проверенную папку `output_Vx`.
