# Events

## Departure event selection

Ordinary player events start after turn 3, subject to the tutorial's loan
unlock. `frm_Travel2_playerEvents` first offers a route change on a 1/40 draw
when a randomly selected slot differs from the destination. Accepting sets
`eventGood` to 85; declining sets it to 15. Otherwise it chooses the good
or bad event scan with `rnd(1,100) <= eventGood`.

These scans are ordered tests, **not uniform draws from an event list**.
Each eligible branch gets its own random check and the first success returns.
The good scan uses 1/10 for its early ship/warehouse/wage/tax opportunities,
then generally 1/40. The bad scan generally uses 1/35, with insurance-premium
increases at 1/8 and hazards also tied to the news or weather.
Feature gates, held assets and the previous event index affect eligibility.
Callbacks resume the scan, allowing more than one event during a departure.

When departure stage 2 completes a good scan, a previous bad result resets `eventGood` to 50
and sets `eventLastGood`; consecutive good results add 5, with values above
95 reset to 85. Completing a bad scan resets a previous good result to 50,
otherwise subtracts 5 with a floor of 15. Tutorial/Novice departure then
enforces minima of 45/35. These updates belong to the scan-completion path,
not every dialog. If the initial stage-1 event attempt returns false, it skips
straight to stage 3 without those updates. Several outcomes explicitly set
their own luck value.

## Good-scan outcomes

“Good” is the source routine's category, not a guarantee of a benefit.
IDs below are `frame_globals[1]`. Offers apply on acceptance; immediate
effects occur in the scanner. `V` means cargo purchase-cost value, falling
back to `cargoTons*300` when that value is zero. `Q` is the offer's drawn
amount, usually scaled by ship tonnage. Dialog prose is omitted.

| ID | Effect |
|---|---|
| 2 | Ship expansion for 25,000–100,000; +25,000 bank limit; [ship increments](SHIPS_AND_AUCTIONS.md#human-ship-expansion) |
| 3 | Pay 15,000–50,000 for +50 warehouse space, +5 insurance range, +25,000 bank limit |
| 4 / 5 | Immediately clear unpaid wages / tax and tariffs |
| 6 | Immediately add one engine point |
| 7 | Reduce insurance range by 5; quote becomes new range + rnd(0,1000) |
| 8 / 9 / 10 | Reduce Zinn rate / bank rate / raise savings rate, subject to bounds and standing |
| 11 | Add 50,000 cash and Zinn debt, plus 100,000 Zinn limit |
| 12 / 13 | Immediately add 50,000 to Zinn / bank limit |
| 14 / 15 | Immediately receive rnd(25,75)*shipTons |
| 16 | Immediately add 25 warehouse space and 5 insurance range |
| 17 | Sell all cargo for 4V; 1/5 risk of an additional 7V charge and luck set to 45 |
| 18 | Replace cargo with a full hold of Exotic at redistributed cost basis; 1/5 risk of confiscation and a 50,000 charge |
| 19 | Pay Q; 1/4 chance to receive 6Q |
| 20 | Pay Q; no further state change in this callback |
| 21 | Pay Q; 2/3 chance to receive 3Q, otherwise set luck to 45 |
| 22 / 42 | Pay Q for sabotage; 1/5 risk of a further 4Q charge, otherwise charge other merchants; 42 also delays the caught saboteur |
| 23 | Charge half Q, rounded down |
| 24 | Surrender cargo, set luck to 85 and last result good |
| 25 | Receive 150,000 for losing three engine points; requires engine ≥5 |
| 26 / 36 | Report only; no state change in the event or acceptance callback |
| 27 | Receive Q |
| 28 | Sell the last indexed shareholding found for 115% of its current price |
| 29 | Buy shares at 80% of the departure planet's price; budget is 25% of cash+savings, capped at 2 million |
| 30 | Receive 5,000 per empty passenger berth and fill the passenger count |
| 31 | Receive fuel*1,750 and halve fuel, rounded down |
| 32 / 35 | Surrender all cargo for 3V / 2V |
| 33 | Fill remaining hold with Exotic at 100 per ton; requires no existing Exotic |
| 34 | Replace all cargo with a full hold of a currently unheld random commodity, redistributing its cost basis |
| 37 | Pay random*newsData*6 for engine +1, cargo +10, passengers +1 or fuel capacity +5, selected by random%4 |
| 38 | Pay Q and lose one crew member, or on a 1/2 bad draw pay 2Q, add delay and set luck to 45 |
| 39 | Pay Q, add delay and set luck to 45 |
| 40 | Pay Q for a salary reduction of 100; 1/5 instead forces back-pay, raises salary 100 and sets luck to 45 |
| 41 | Receive Q; 1/4 risk of paying 2Q, adding delay and setting luck to 45 |
| 43 | Immediately halve `travelDelayed` |
| 44 | Receive Q and change destination |
| 45 | Change destination; 1/4 chance to receive Q |
| 46 | Change destination and receive Q |
| 47 | Receive Q; 1/4 risk of rerouting, delay and luck set to 45 |

For successful sabotage, each other merchant's loss starts with
`floor(targetShipTons*Q/attackerShipTons)`, is redrawn between twice and three
times that amount, then multiplied by 1.5 and rounded down. Human victims
pay through `subtract_cash`; `sabotageDamage` records the later report,
including a negative sign when payment needed credit. Bankrupt humans and
the attacker are skipped. Opponents lose cash directly.

## Bad-scan outcomes

| ID | Effect |
|---|---|
| −2 | Pay an offered tax-related charge or add that amount to tax by refusing |
| −3 | Fire at a random warehouse planet; uninsured inventory and cost basis erased |
| −4 | Insurance range +5 and a new high-end quote |
| −5 / −6 | Zinn / bank interest rate +1; insurance changes the message, not the increase |
| −7 | Uninsured crew-related cash loss of rnd(25,75)*shipTons |
| −8 | Accept salary +100 or face a 1/5 chance of a strike on refusal |
| −9 | Forced repayment of half Zinn debt through the shared payment helper |
| −10 | News-linked hazard: repair charge, cargo loss, or both; insurance can avoid those losses; delay still added |
| −11 | Weather-linked repair charge unless insured; delay still added |
| −12 | Lose half, rounded up, of the last occupied commodity in scan order unless insured |
| −13 / −15 | Repair cost unless insured, plus delay |
| −14 | Halve fuel unless insured, plus delay |
| −16 | Lose all cargo unless insured, plus delay |
| −17 | Reroute to another planet; clear passenger advertising and recompute demand even if insured |
| −18 | Double `travelDelayed` |
| −19 | Summary of accumulated hazard delays; no additional loss |

Most hazard delays add 1 to `travelDelayed`; this multiplier is later applied
to human travel time. Insurance does not skip the whole bad-event routine.
The separate [strike, fuel-rescue and audit checks](FINANCE.md) follow it.

## World events

After turn 4, `frm_Travel3_gameEvents` draws an ID 1–20 and uses slot
`turn%7` for local effects. `A` below is average ship tonnage of non-bankrupt
humans, rounded down; `floorPrice` and `ceilingPrice` are from the
[ordinary commodity formula](ECONOMY.md#commodity-markets).

| ID | Effect, subject to feature gates |
|---|---|
| 1–3 | Selected tier 0–2: price = floorPrice+rnd(0,3); availability += A+rnd(10,1000) |
| 4–6 | Selected tier 0–2: price = ceilingPrice−rnd(0,3); availability = rnd(1,4) |
| 7 | Fuel range ×1.2, rounded down; all fuel prices near ten times the new range |
| 8 | If range ≥15, fuel range ×.8, rounded down; all fuel prices near the new range |
| 9 / 10 / 11 | Passenger / export / import rate +1, capped at 50 / 15 / 15 |
| 12 / 13 / 14 | Passenger / export / import rate −1, stopping at 0 / 1 / 1 |
| 15 | All tiers: low prices and extra supply as in 1–3, but draw rnd(1,1000) |
| 16 | All tiers: high prices and scarce supply as in 4–6 |
| 17–20 | No state change in this routine |

Opponent news events are a separate draw: one opponent (1–6), one story
(1–108). Positive stories add `2*rnd(25,75)*shipTons`; negative stories
subtract `rnd(25,75)*shipTons`; IDs 10/18 add one engine point. Other stories
only display a report. This runs after turn 4 when the stock tutorial gate
permits it, independently of the selected opponent's own turn.

## Source reference

Raw `Gazillionaire.as`:

| Functions | Subject |
|---|---|
| `frm_Travel2_playerEvents` (64506), `frm_Travel2_goodEvent` (64534), `frm_Travel2_badEvent` (65559) | Eligibility, ordered draws and immediate effects |
| `frm_Travel2_yes` (63564), `frm_Travel2_no` (64460), `frm_Travel2_ok` (63335) | Deferred choices and sabotage |
| `frm_Travel2_exit` (63082) | Scan completion, luck and remaining departure stages |
| `frm_Travel3_gameEvents` (70610), `frm_Travel3_opponentEvents` (70833), `frm_Travel4_gameEvents` (51627) | World mutations and arrival reports |
