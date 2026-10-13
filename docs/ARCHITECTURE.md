# Architecture

Gazillionaire 3.1.0 is a 64-bit Adobe AIR 32 captive-runtime application.
`Gazillionaire.exe` launches `Gazillionaire.swf` (SWF v43), a Flex
`WindowedApplication`. Its descriptor is preserved at
`$GAZ_DATA_DIR/original/AIR/application.xml`.

Most UI and logic live in `Gazillionaire.as`. `GameType`, `PlayerType` and
`OpponentType` hold state; `GameStrings` supplies localization.
[Code map](CODE_MAP.md) · [Mechanics](GAME_MECHANICS.md) · [Saves](SAVE_FORMAT.md)

## Assets

Embedded images and binary data are extracted for source compilation.
Synthetic Flex artwork symbols are recovered separately from the original SWF.
Runtime loads use paths relative to the application:

| Directory | Contents |
|---|---|
| `SWF/` | Ships and animations |
| `resources/` | UI widgets and planet intros |
| `MP3/` | Speech and effects |
| `PNG/` | Portraits and bitmaps |

`run.sh` assembles these directories from local game data beside the rebuild.

## Build variants

| `buildLevel` | Behavior |
|---|---|
| 0 | Offline shareware |
| 1 | Web backend and multiplayer |
| 2 | Offline paid Steam release; five local save slots |

Web handlers remain compiled into the Steam release but are dormant.
Steam integration uses `com.amanitadesign.steam.FRESteamWorks` 0.7.0;
its recovered API lives in `$GAZ_DATA_DIR/src/steam_ane/`.
