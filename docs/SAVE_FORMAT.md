# Save format

The desktop/Steam build (`buildLevel == 2`) is fully offline. Preferences and
save slots live in a single Flash `SharedObject` named
**`LavamindGazillionaireSaveData`**. On Linux AIR stores this as a `.sol` file
under the user's Adobe/AIR local storage directory.

## Preference keys

| Key | Type | Meaning |
|-----|------|---------|
| `fullscreen` | `"true"` / `"false"` | Full-screen state, toggled in `fullscreen()` / `init_fullscreen()` |
| `sound` | `int` (0/1/2) | 0 = off, 1 = reduced, 2 = on (`disableSound` / `lessSound` / `enableSound`) |

## Game slots

`autosave()` writes serialized games into `data.game_1` … `data.game_5`, i.e.
five local save slots. Each slot is a `flash.utils.ByteArray` produced by
`GameType.serialize()`:

```as3
bytes = thisgame.serialize();
bytes.position = 0;
saves.data.game_1 = bytes;
saves.flush();
```

Load uses `GameType.deserialize(bytes)`, which resets `bytes.position = 0`
defensively before reading.

The `Serializable` state is a hand-rolled binary format (no AMF object graph).
It is a flat sequence of `writeInt` / `writeDouble` / `writeBoolean` / `writeUTF`
calls. The exact field order is the authoritative source of truth and is
implemented in:

* `$GAZ_DATA_DIR/src/decompiled/scripts/GameType.as` (`serialize` / `deserialize`)
* `$GAZ_DATA_DIR/src/decompiled/scripts/PlayerType.as`
* `$GAZ_DATA_DIR/src/decompiled/scripts/OpponentType.as`

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
├─ double[7][1..15] stockPrice, bool[7] stockCrash, int[7] stockTrend
├─ bool   stockFlag, double turn, bool tutor
├─ int    weather, weatherPlanet
└─ double winner, winningPoint
```

`GameType.serialize()` and `GameType.deserialize()` must be kept in lock-step
with `PlayerType` / `OpponentType`; a single mismatched read corrupts the
remainder of the stream. `deserialize()` also derives some fields that are not
stored, e.g. `PlayerType.cargoTons` and `warehouseT` are recomputed from the
cargo/warehouse grids.

## Online mode (not used by the Steam build)

`buildLevel == 1` and the web build talk to a PHP backend. Those paths call
`/gazXML.php` with `command=gamesave` / `gameload` and encode the same
`GameType` bytes with base64. They are dead code on the Steam release but
explain the `username` / `password` / `frame_globals` fields.
