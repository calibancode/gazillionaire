# Turns and travel

The game has two clocks: an individual departure advances `dateYear`, while
the shared round counter `turn` advances after the whole turn order finishes.
These are separate operations, especially in a game with several humans.

## Departure and scheduling

Choosing a destination sets `planetLast` and `planet` before any departure
events. Quick-deposit mode first transfers all cash to savings. An auction
prompt or departure animation may intervene, but both routes reach
`frm_Travel2_exit`. `frm_Travel1_move_ship` only moves the animation.

| Departure stage | Operations, subject to tutorial gates |
|---|---|
| 1 | Refresh stored random draw; contribute commodity ads at destination; advance dateYear by 1/50; clear sellingProfit and special flag; apply interest and payroll; start event scan |
| 2 | Resume event choices/scans and update luck on completion |
| 3 | Apply early-level luck minima, consume fuel, check crew strike |
| 4–5 | Check negative fuel and process rescue reports |
| 6 | Check tax audit |
| 7 | Add export tariffs, reroll insurance quote, compute passengers, expire insurance and paid ads, mark turn taken, enter scheduler |

Callbacks resume these stages. Several independent `if` blocks can complete
within one invocation when no report interrupts them.

`frm_Travel3_load` increments `playerTurnCounter` and reads the next entry in
`playerOrder`. Human entries select `g.player` and open `frm_PlayerTurn`;
bankrupt humans are skipped. Opponent entries call `frm_Travel3_opponentTurn`.
A false return immediately continues scheduling; a true return waits on a
purchase report. Opponent action order and decisions are in
[opponent economy](OPPONENTS.md).

| State | Encoding |
|---|---|
| Human index in `g.p` | 0 through `playerNumberOf - 1` |
| Opponent index in `g.o` | 1 through `opNumberOf` |
| Human entry in `playerOrder` | Human index |
| Opponent entry in `playerOrder` | Opponent index + 6 (first opponent is 7) |

When the counter reaches the combined player count, `frm_Travel3_load` sets
it to −1, increments `turn`, and performs these operations in order:

1. Update tutorial progression and clear `turnTaken` flags.
2. Update stocks, then unlocked news and weather.
3. Choose opponent destinations and construct the new travel order.
4. Run auctions after turn 2.
5. Update supply ratings, commodity availability and commodity prices.
6. Reroll fuel prices; run game events after turn 4 and opponent events when
   their additional tutorial gate permits them.
7. Recalculate net worth, record history, and check for a winner.

An uninterrupted continuation calls `frm_Travel3_load` again: the counter then
becomes zero and dispatches the first entry of the new order. Opponent-event
presentation can defer that continuation.

## Destinations and arrival order

`frm_Travel3_travel` chooses each opponent's destination by scanning all seven
slots for the lowest supply rating (`comR`) of its tagged commodity
(`comTag1`, `comTag2`). Because the comparison is `<=`, equal minima resolve
to the last matching slot in the scan. The current planet is eligible.
This reads supply ratings before the round's economic update.

Travel time uses Euclidean distance between the fixed map coordinates:

```text
distance = sqrt(dx*dx + dy*dy)
opponent travelTime = distance * 5 / engine
human travelTime = floor(distance * 5 / engine * travelDelayed)
```

Each human's `travelDelayed` is then reset to 1. The routine repeatedly picks
the next unused human and opponent with the shortest travel time and merges
them into `playerOrder`. Equal times invoke `f_rnd(0,1)` during selection;
this is a sequence of coin flips, not a uniform shuffle of tied players.
The temporary `turnTaken` flags are cleared again before returning.

The fuel calculation in `frm_Travel2_exit` uses a separate expression with
bitwise XOR operators. It must not be substituted for this distance formula.

## Human arrival

The turn-start screen autosaves assigned games and routes an existing winner
to the win screens. Otherwise `frm_PlayerTurn2_continue` processes crashed
exchanges, low-price reports and unresolved auction reports. `frm_Travel4_ok`
then presents sabotage, settled auctions, earlier arrivals and world events.
`frm_Travel5_ok` applies import tariffs, pays others' facility fees, then
collects the human's local facility revenue. It clears `supplyPlanet` before
the planet welcome screen, tutorial/graphs and main menu.

The supply screen's target is a remembered map marker (`supplyPlanet`), not
an automatic purchase or travel command. Arrival reports likewise do not
execute another merchant's trade a second time.

## Net worth and winning

The round-end calculation in `frm_Travel3_load` uses:

```text
human netWorth = cash + savings + share value - loan - zinnLoan
opponent netWorth = cash + share value
```

Shares use `stockPrice[planet][turn]` through turn 15, then column 15.
Ships, held commodities, warehouses and facilities do not enter these sums.
Bankrupt humans receive a net worth of −10,000,000,000.

`frm_Travel3_winCheck` selects the richest opponent and the richest
non-bankrupt human. A human wins if their worth is at least the richest
opponent's and **strictly greater** than `winningPoint`. Otherwise an opponent
wins if its worth is strictly greater than the target. Exact human/opponent
ties therefore favor the human; an exact tie with the target does not win.
Strict comparisons within each group retain the earlier index on equal worth.

If `winner` was already set on entry, the function clears it and raises the
target before checking again: 5 million → 10 million, then steps of 10 million
below 100 million, 100 million below 1 billion, and 1 billion below 10 billion.
The final branch sets the target to 10 billion.

## Source reference

All locations are in raw `Gazillionaire.as`.

| Function | Lines | Subject |
|---|---|---|
| `frm_LeavePlanet_select_planet` | 62452–62493 | Destination choice and debt gates |
| `frm_Travel2_exit` | 63082–63333 | Departure stages |
| `frm_PlayerTurn2_continue`, `frm_Travel4_ok`, `frm_Travel5_ok` | 51169, 51331, 51918 | Arrival sequence |
| `frm_Travel3_load` | 66994–67145 | Dispatch, round updates and net worth |
| `frm_Travel3_opponentTurn` | 67147–67349 | Opponent action order |
| `frm_Travel3_opponentBuySell` | 67382–67472 | Separate opponent trading rules |
| `frm_Travel3_travel` | 69724–69865 | Destination selection, timing and ordering |
| `frm_Travel3_winCheck` | 71249–71315 | Winner selection and escalating targets |
