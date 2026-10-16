# Save format

The desktop/Steam build (`buildLevel == 2`) is fully offline. Preferences and
save slots live in a single Flash `SharedObject` named
**`LavamindGazillionaireSaveData`**. Its `.sol` container holds preferences,
slot names and serialized game bytes; it is not itself the game payload.

## Preference keys

| Key | Type | Meaning |
|-----|------|---------|
| `fullscreen` | `"true"` / `"false"` | Full-screen state, toggled in `fullscreen()` / `init_fullscreen()` |
| `sound` | `int` (0/1/2) | 0 = off, 1 = reduced, 2 = on (`disableSound` / `lessSound` / `enableSound`) |

## Game slots

`autosave()` writes serialized games into `data.game_1` … `data.game_5`, i.e.
five local save slots, selected by `GameType.game` (1–5). A new, unassigned
game (`game == 0`) is not saved by this path. `name_1` … `name_5` store slot
labels separately. Each game slot is a `flash.utils.ByteArray` produced by
`GameType.serialize()`:

```as3
bytes = thisgame.serialize();
bytes.position = 0;
saves.data.game_1 = bytes;
saves.flush();
```

Load uses `GameType.deserialize(bytes)`, which resets `bytes.position = 0`
defensively before reading.

The game payload is a hand-rolled binary format (no AMF object graph).
It is a flat sequence of `writeInt` / `writeDouble` / `writeBoolean` / `writeUTF`
calls. The exact field order is the authoritative source of truth and is
implemented in:

* `$GAZ_DATA_DIR/src/decompiled/scripts/GameType.as` (`serialize` / `deserialize`)
* `$GAZ_DATA_DIR/src/decompiled/scripts/PlayerType.as`
* `$GAZ_DATA_DIR/src/decompiled/scripts/OpponentType.as`

The [complete ordered layout](reference/SAVE_LAYOUT.md) records field types,
array nesting and interleaving for all three records. No compression, schema
version or checksum is added by these serializers.

### Layout sketch

```
GameType
├─ int    playerNumberOf
├─ int    opNumberOf
├─ PlayerType[playerNumberOf]
├─ OpponentType[1..opNumberOf]          (1-based)
├─ int[17] activate*                     feature unlock turn numbers
├─ double[7] advertC
├─ auction state (ints/doubles)
├─ double[7][3][6] comR, comP, comA       supply / price / available
├─ int    difficulty, double dateYear, int exportTariff
├─ double fuelPriceRange, double[7] fuelCost
├─ int    game, gameEvent, importTariff
├─ bool   isMidTurn, int level, news, newsData, newsPlanet, passTax
├─ int[7] planetIndex, planetX, planetY
├─ int    player, int[playerNumber+opNumber] playerOrder, playerTurnCounter
├─ double sellingProfit
├─ per planet: bool stockCrash, double[1..15] stockPrice, int stockTrend
├─ bool   stockFlag, double turn, bool tutor
├─ int    weather, weatherPlanet
└─ double winner, winningPoint
```

`GameType.serialize()` and `GameType.deserialize()` must be kept in lock-step
with `PlayerType` / `OpponentType`; a single mismatched read corrupts the
remainder of the stream. `deserialize()` also derives some fields that are not
stored, e.g. `PlayerType.cargoTons` and `warehouseT` are recomputed from the
cargo/warehouse grids. The format does not preserve the random generator or
temporary popup state.

## Save and resume behavior

`frm_PlayerTurn_load` autosaves an assigned slot at turn start, except on the
first visit after loading (`justLoaded`). Entering the main menu sets
`isMidTurn = true`; the scheduler clears it before dispatching turns.
`frm_LoadGame_loadgame` saves the currently assigned game before switching,
deserializes the selected slot, then opens the main menu for a mid-turn save
or the turn-start screen otherwise.

Source: raw `Gazillionaire.as`, `autosave` (45811), `frm_PlayerTurn_load`
(50723), `frm_MainMenu_load` (52778), `frm_Travel3_load` (66994),
`frm_LoadGame_loadgame` (61424). A persisted save-slot gameplay session is
still outside the [verified runtime coverage](VERIFICATION.md).

## Online mode (not used by the Steam build)

`buildLevel == 1` and the web build talk to a PHP backend. Those paths call
`/gazXML.php` with `command=gamesave` / `gameload` and encode the same
`GameType` bytes with base64. They are dead code on the Steam release but
explain the `username` / `password` / `frame_globals` fields.
