# Code map

Raw application source: `$GAZ_DATA_DIR/src/decompiled/scripts/`.

| Class | Purpose |
|---|---|
| `Gazillionaire` | UI and game logic |
| `GameStrings` | Localization |
| `GameType` | Session state and serialization |
| `PlayerType`, `OpponentType` | Human and AI state |
| `CustomPreloader`, `LoadScreen` | Startup UI |
| `Gazillionaire_*Class`, `*_dataClass` | Embedded assets |

`frm_<Screen>_<action>` methods implement screen behavior. `__frm_*` methods
and hash-prefixed fields are generated Flex bindings. Bundled `mx.*` and
`spark.*` classes come from the SDK during reconstruction.

## Lifecycle

| Function | Purpose |
|----------|---------|
| `doInit()` | Entry point: loads preferences, chooses offline/online path, shows `frm_Init` |
| `new_game()` | Starts a new game (build-level dependent) |
| `initializeGame(level)` | Builds a fresh `GameType` (planets, prices, stocks, AI) |
| `randomize_planets()` | Picks 7 of 14 planets |
| `set_up_players(n)` | Creates human `PlayerType` slots |
| `select_player_ship(player, ship)` | Applies ship stats |
| `autosave()` / `process_autosave()` | Serializes the game into a save slot |
| `doQuit*()` | Save-on-quit flows |

## Key logic functions (non-exhaustive)

| Area | Functions |
|------|-----------|
| Market | `frm_Market_buy`, `frm_Market_sell`, `frm_Market_buy_sell`, `frm_Market_refresh_grid` |
| Supply | `frm_Supply_select`, `frm_Supply_set_target`, `frm_Supply_refresh_grid` |
| Warehouse | `frm_Warehouse_store`, `frm_Warehouse_take`, `frm_Warehouse_take_store` |
| Bank/loans | `frm_Bank_deposit`, `frm_Bank_withdraw`, `frm_Loan_borrow`, `frm_Loan_repay`, `frm_ZinnLoan_repay`, `subtract_cash` |
| Travel | `frm_Travel1_move_ship`, `frm_Travel3_travel`, `frm_Travel3_winCheck` |
| AI | `frm_Travel3_opponent*`, `frm_Travel4_opponentArrivesOnPlanet`, `frm_PlayerTurn2_*` |
| Events | `frm_Travel2_badEvent/goodEvent`, `frm_Travel3_economicChange/gameEvents/newsEvent`, `frm_Travel4_gameEvents` |
| Facilities | `frm_Travel5_payFacilities`, `frm_Travel5_revenueFacilities`, `frm_PlayerTurn2_AuctionFacility`, `frm_Special_action` |
| Stocks | `frm_Stock_buy/sell/draw`, `frm_PlayerTurn2_stockCrash/stockFall`, `frm_Travel3_stockMarket` |
| Persistence | `autosave`, `frm_File_savegame`, `frm_LoadGame_loadgame`, `frm_SaveGame_savegame` |
| Rendering | `drawBarChart`, `drawLineChart`, `drawPieChart`, `frm_Graph_*`, `frm_Stock_draw` |
| Media | `playSound`, `playSoundNoLoop`, `commodity_sound`, `planet_sound`, `status_name` |
