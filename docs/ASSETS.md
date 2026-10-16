# Asset inventory

`tools/export_all.sh` creates this local inventory under `GAZ_DATA_DIR`
(default `.local-data/`). These files are ignored by Git. The `original/`
copies preserve the input binaries for repeat exports.

```
assets/
├── audio/          175 .MP3   (copies of the game's MP3/ directory)
├── images/          30 .PNG   (copies of the game's PNG/ directory)
├── main_embedded/  135 files  (assets compiled into Gazillionaire.swf)
├── swf/            609 files  (converted SWF/ movies, one subdir per file)
└── resources/       81 files  (converted resources/ widgets/intros)

original/
├── Gazillionaire.swf           main Flex/AIR application (1.5 MB)
├── swf/                       156 untouched .SWF character/animation movies
├── resources/                  60 untouched resource SWFs
├── AIR/application.xml         AIR descriptor
├── extensions/.../             FRESteamWorks ANE
├── mimetype, signatures.xml
```

## `assets/swf/` and `assets/resources/`

Each SWF is expanded into a sibling folder named after the file, containing
whichever of `images/`, `shapes/`, `sprites/`, `fonts/`, `sounds/` it uses:

* `images/` — bitmaps as PNG/GIF/JPEG (e.g. character portraits).
* `shapes/` — vector shapes as SVG. Note several character shapes are large
  (up to ~2.9 MB) because the original vector/bitmap hybrid is serialized in
  full fidelity.
* `sprites/` — animations exported as animated GIF.
* `fonts/` — embedded fonts as TTF.
* `sounds/` — embedded audio as MP3.

These SWFs contain **no ActionScript** — they are pure artwork/animation used
by the main application (confirmed with `ffdec -dumpAS3`/`-dumpAS2`, which
return nothing for them). The character names are the game's cast: HORK, BASS,
FRAC, LORO, MIRA, NOSH, OOOM, PYKE, QUEG, STYE, TILO, VEXX, XEEN, ZILE (planets),
plus brokers, police, bandits, crew, dealers, etc.

## `assets/main_embedded/`

The Flex compiler embedded a subset of art directly into `Gazillionaire.swf`:

* `binaryData/*.bin` — the planet intro movies (`*_PlanetHork1Class_dataClass`,
  …, identical to `original/resources/*1.SWF`) and the loader art.
* `images/*.png` — UI icons (`i_market.png`, `i_crew.png`, …) and the
  boy/girl hand-up icons.
* `shapes/`, `sprites/`, `fonts/`, `sounds/` — remaining embedded assets.

## Referenced assets

`reference/asset_references.txt` lists all 257 fully-qualified
`SWF/…`, `MP3/…`, `PNG/…` paths referenced by the code. In addition, some paths
are built dynamically:

* `SWF/SHIP<n>.SWF` and `SWF/SHIP<n>A.SWF` for n = 1…12
* `MP3/OP<n>.MP3` and `PNG/OP<n>.PNG` for n = 1…6
* `SWF/STARS2.SWF`, `SWF/STARS_BG.SWF`, `SWF/WHITE_V.SWF`, `SWF/WHITE_H.SWF`

All of these exist in the Steam install.

## Regenerating

```bash
tools/export_all.sh
# or point at another install:
tools/export_all.sh /path/to/Gazillionaire
```

The exported art remains derived game material; the repository contains the
extraction tools and reference text, not this local asset inventory.
