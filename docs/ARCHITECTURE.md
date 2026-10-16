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

The source sets `buildLevel = 2` and `is_free_game = false`. Web handlers
remain compiled but are not the Steam startup/save path. They use an external
PHP backend, FlashVars and browser `ExternalInterface`; the recovered client
does not include that server.

The installation bundles `com.amanitadesign.steam.FRESteamWorks` 0.7.0;
its extracted ActionScript API lives in `$GAZ_DATA_DIR/src/steam_ane/`.
The main `Gazillionaire.as` contains no calls to that API. A bundled extension
does not by itself establish gameplay integration with Steam services.

## Presentation

The main class mixes screen construction, event wiring, domain rules and
dialogs. `GameType` and its nested player records contain serializable state;
temporary screen state is held separately in `frame_globals`. There is no
separate game simulation module. See [reading the UI code](CODE_MAP.md#reading-the-ui-code).

`GameStrings` supplies the English game text; Flex resource bundles supply
framework text. Speech and effects share one current `SoundChannel`: starting
a new sound stops the previous one. `playSound` requests 255 repeats;
`playSoundNoLoop` requests none. Animation SWFs are loaded into image controls.
Video helpers exist, but their presence does not establish that the Steam
gameplay path uses every referenced media format.
