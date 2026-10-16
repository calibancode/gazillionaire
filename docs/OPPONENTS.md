# Opponent economy

Opponents trade in the shared markets, but their money follows different rules
from human money. After turn 15, commodity purchases can be free and sales can
use a synthetic payout. Separate cash adjustments run after trading.

This page describes `OpponentType.as` and the `frm_Travel3_opponent*` methods
in raw `Gazillionaire.as`, under `$GAZ_DATA_DIR/src/decompiled/scripts/`
(default `.local-data/`). It covers commodity selection, sale payouts, stocks
and engine/ship purchases. [Cash balancing](AI_BALANCING.md) and
[events](EVENTS.md) cover the additional adjustments. These are source
findings, not a measurement of AI performance across played games.

## State and turn order

Each opponent holds one commodity at a time: `comTag1` and `comTag2` identify
it, and `comS` is its quantity. Unlike `PlayerType`, `OpponentType` has no
commodity grid, purchase-average grid, savings or loan fields.

`frm_Travel3_opponentTurn` runs facility payments, commodity trading, stock
trading, then possible engine and ship purchases. It next applies a positive-
cash growth rule and, from turn 3, calls `opponentLevel`. See
[turn scheduling](TURNS.md) for the surrounding round sequence.

The trading and balancing comparisons read stored `netWorth` fields. They do
not recalculate them after each transaction. The round-end scheduler refreshes
those values after dispatching the preceding turn order.

| ID | Company |
|---|---|
| 1 | Gizzy Shipping |
| 2 | Trading Corp. IV |
| 3 | Vandergriff Ltd. |
| 4 | Puffer Inc. |
| 5 | Roke Transport |
| 6 | Hoff Meister |

## Commodity choice

`opponentBuySell` first unloads any held commodity, adding its tons to the
planet's availability. It then scans all 18 commodities in tier/item order.
For commodity index `k = tier*6 + item + 1`, define `ceiling = 40*k`.
A candidate must satisfy all four conditions:

- It is not the commodity just unloaded.
- Its posted price is strictly below `0.9*ceiling`.
- `ceiling - price` is strictly greater than the best margin found so far.
- Its availability is strictly greater than `shipTons/16`.

The selected quantity is `floor(shipTons/4 * iQ/100)`, capped at available
stock. The routine ranks the absolute margin per ton; it does not compare
percentage return, travel distance or total profit. Exact margin ties retain
the earlier commodity. It contains no cash-affordability check.

If no candidate qualifies after unloading, quantity stays zero and the old
commodity tags remain. Destination selection later still reads those tags.
It chooses the lowest supply rating for the tagged commodity, as described in
[destinations and arrival order](TURNS.md#destinations-and-arrival-order).

## Purchase costs

Let `H` be the richest non-bankrupt human's stored net worth and `N` the
opponent's stored net worth. The cost rules are:

| Round | Condition | Cash deducted for selected cargo |
|---|---|---|
| `turn <= 15` | Any standing | Full posted price × quantity |
| `turn > 15` | `N <= H` | Nothing |
| `turn > 15` | `N > H` | Discounted posted price × quantity |

For the last row, the random percentage is 70–100% for IDs 1/2, 90–100% for
3/4, 65–100% for 5, and 60–100% for 6. The final cost is rounded down.
All ranges here are inclusive integer draws through `f_rnd`.
Availability is reduced by the selected quantity in every case, including
free purchases. A purchase can make cash negative; there is no borrowing or
bankruptcy check in this routine.

## Sale proceeds

When an opponent arrives with cargo, its unloaded quantity enters the local
market regardless of how the cash payout is calculated:

| Round | Condition | Cash received |
|---|---|---|
| `turn <= 15` | Any standing | Posted price × held tons |
| `16 <= turn < 50` | `N >= H` | Posted price × held tons |
| `16 <= turn < 50` | `N < H` | `opponentProfit` payout |
| `turn >= 50` | Any standing | `opponentProfit` payout |

The synthetic payout **replaces** sale proceeds; it is not added to them.
It depends on ship tonnage, level, company and human standings, rather than
the unloaded commodity's price or quantity. The caller requires positive
held cargo, but the payout formula itself never reads that quantity.

`opponentProfit` starts with `B = floor(rate * shipTons/4)`:

| Level | Tutorial / Novice | Beginner | Intermediate | Expert | Master |
|---|---:|---:|---:|---:|---:|
| Rate | 35 | 30 | 25 | 20 | 15 |

It then adds `floor(B * multiplier)` to cash. With `L` denoting the poorest
non-bankrupt human's stored worth, multiplier selection is:

| ID | First applicable condition | Multiplier |
|---|---|---|
| 1 | `N < 0.7*H` | 1/3: 5–20; otherwise: 6–18 |
| 1 | Otherwise | 5–18 |
| 2 | `N < 0.6*H` | 1/3: 5–20; otherwise: 6–18 |
| 2 | Otherwise | 6–17 |
| 3 | `N < L` and `L != H` | 1/3: 3–20; otherwise: 6–18 |
| 3 | Otherwise, `N < 0.5*H` | 4–18 |
| 3 | Otherwise | 3–18 |
| 4 | `N < L` and `L != H` | 1/3: 1–20; otherwise: 3–18 |
| 4 | Otherwise, `N < 0.4*H` | 3–18 |
| 4 | Otherwise | 1–18 |
| 5 | `N < 0.8*H` | 1/4: 8–22; otherwise: 8–19 |
| 5 | Otherwise | 8–18 |
| 6 | `N < 0.85*H` | 1/4: 10–22; otherwise: 10–19 |
| 6 | Otherwise | 8–18 |

For example, a 400-ton Gizzy ship in Novice has `B = 3,500`. On its normal
multiplier branch, a synthetic sale adds 17,500–63,000 kubars regardless of
whether it unloaded one ton or fifty. This example isolates the sale payout;
it excludes other cash changes during the turn.

## Stocks

`opponentStock` starts at turn 15 when stocks are unlocked. It operates only
on the opponent's current planet. If the local trend is below its threshold,
it sells all shares held there. Otherwise it buys
`floor(standingFactor * allocation * cash / price)` shares, provided cash is
strictly greater than one share's price.

`standingFactor` is 0.5 when `N >= H`, otherwise 1. The price is column 14
on turn 15 and column 15 thereafter; it is converted to `int` before use.

| IDs | Minimum trend | Base cash allocation |
|---|---:|---:|
| 1 | 60 | 1% |
| 2 | 70 | 1% |
| 3 | 75 | 1% |
| 4 | 60 | 1% |
| 5 | 65 | 1.5% |
| 6 | 70 | 1.5% |

For IDs 1/2/5/6, allocation becomes 2% when the winning target is strictly
above 50 million and 3% when it is strictly above 100 million. IDs 3/4 stay
at 1%. Buying can round to zero shares even when the cash guard passes.

## Engine purchases

When the caller's exploration gate permits it, `opponentBuysEngine` draws a
cost of 5,000–25,000. On Pyke (planet identity 1), an upgrade succeeds with
probability 3/4. On Xeen (identity 9), the two nested draws give probability
`1/4 * 2/3 = 1/6`. Success adds exactly one engine point, deducts the cost,
and displays a report. The method has no affordability check.

## Ship purchases

After turn 4, if no engine was bought and the exploration gate permits it,
`opponentBuyShip` draws a chance to add 200 tons for 25,000–75,000 cash.
There is no affordability guard. Let `S` be its tonnage, `M` the rounded-down
mean human tonnage, and `X` the largest human tonnage. This routine includes
bankrupt humans in both statistics.

It succeeds when `rnd(1,D) == 1`. First set denominator `D`:

| Condition | IDs 1–6, respectively |
|---|---|
| S ≥ M | 10000 for all |
| S + 600 ≤ M | 13, 12, 14, 15, 11, 10 |
| Otherwise | 20, 19, 21, 22, 18, 17 |

Then determine a catch-up target `T`. Below Expert it is `X`. Expert uses
`X+200` when `turn*30 > X`, otherwise `X`; Master uses `X+400` when
`turn*40 > X`, otherwise `X`. Only if `S < T`, replace D as follows:

| Level | ID 1 | ID 2 | ID 3 | ID 4 | ID 5 | ID 6 |
|---|---:|---:|---:|---:|---|---|
| Tutorial / Novice | 9* | 9* | 9* | 10* | 5 if S+400 < X, else 8 | 2 if S+200 < X, else 5 |
| Beginner | 9* | 9* | 9* | 10* | 5 if S+200 < X, else 7 | 3 if S+200 < X, else 5 |
| Intermediate | 8 | 8 | 9* | 10* | 2 if S+200 < X, else 4 | 2 if S+200 < X, else 4 |
| Expert | 6 | 6 | 7 | 8 | 2 if S+200 < X, else 3 | 2 if S+200 < X, else 3 |
| Master | 4 | 4 | 5 | 6 | 2 if S+400 < X, else 3 | 2 if S+400 < X, else 3 |

An asterisk requires `S < M`; otherwise keep the initial D. This mechanism
lets opponents catch up to human ship growth, with stronger allowances at
Expert/Master. It is separate from [ship auction bidding](SHIPS_AND_AUCTIONS.md).

## Source reference

Locations below are in raw `Gazillionaire.as` unless another file is named.

| Function / source | Lines | Subject |
|---|---|---|
| `OpponentType.as` | 8–44 | Opponent state fields |
| `GameStrings.as` | 267–272 | Company names |
| `f_rnd` | 45432–45435 | Inclusive integer draw for integer bounds |
| `frm_Travel3_opponentTurn` | 67147–67349 | Action order and positive-cash adjustment |
| `frm_Travel3_opponentBuySell` | 67382–67472 | Selection, purchases and sale dispatch |
| `frm_Travel3_opponentStock` | 67474–67673 | Stock thresholds and allocation |
| `frm_Travel3_opponentBuysEngine` | 67675–67709 | Engine upgrade draws |
| `frm_Travel3_opponentBuyShip` | 67711–68042 | Tonnage catch-up and ship purchases |
| `frm_Travel3_opponentProfit` | 68044–68206 | Synthetic sale payouts |
| `frm_Travel3_opponentLevel` | 68208–69502 | Separate signed cash adjustment |
