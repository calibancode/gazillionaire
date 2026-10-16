# Ships, auctions and facilities

## Starting ships

All human ships start at 400 tons, with a full tank after selection.
Ship identity controls the following starting capacities and later expansion
increments. Starting cash and Zinn debt depend on difficulty, not ship.

| Ship ID | Engine | Fuel | Cargo | Passengers | Crew |
|---|---:|---:|---:|---:|---:|
| 1 | 7 | 20 | 100 | 8 | 4 |
| 2 | 5 | 40 | 120 | 8 | 5 |
| 3 | 5 | 65 | 80 | 8 | 3 |
| 4 | 2 | 50 | 130 | 11 | 6 |
| 5 | 5 | 40 | 100 | 6 | 3 |
| 6 | 5 | 40 | 100 | 8 | 4 |
| 7 | 7 | 30 | 80 | 7 | 4 |
| 8 | 6 | 40 | 110 | 5 | 4 |
| 9 | 4 | 40 | 90 | 10 | 3 |
| 10 | 3 | 35 | 150 | 1 | 2 |
| 11 | 6 | 30 | 75 | 16 | 12 |
| 12 | 6 | 40 | 110 | 8 | 6 |

## Auctions

The scheduler resolves an existing auction after turn 2, then selects the
next one. Humans submit bids when choosing a destination. A bid at least
equal to the current high bid replaces the leader and moves that leader to
second place; a lower bid replaces second place only if strictly higher.
The amount dialog warns, rather than rejects, bids beyond available bank
credit or above 200,000. Winners pay their own high bid, not the second bid.

| Human count | Ship auction chance | Facility chance if no ship auction |
|---|---:|---:|
| 1 | 1/12 | 1/4 |
| 2 | 1/10 | 1/3 |
| 3–6 | 1/8 | 1/2 |

Tutorial gates require progression strictly beyond exploration for ships,
and strictly beyond facilities for facilities. An unresolved nonzero tie
sets `auctionLast` to −1 (ship) or −2 (facility) and schedules a repeat;
facility repeats retain the same type, planet and fee. Opponent bids are
redrawn until the highest two opponent bids differ, then merged with human
bids. A nonzero equal final high/second bid defers the award.

Opponent facility bids scale with the offered fee and stored net worth;
ship bids use a net-worth bracket. Both have an independent 1/6 chance to
double. Ship bidders can also try to beat the human high bid when their ship
is smaller than the largest non-bankrupt human ship, then cap that attempted
bid at their net worth (and at least zero). Facility bidding has no equivalent
affordability cap. Settlement deducts opponent cash directly or uses
`subtract_cash` for a human.

### Bid brackets

Intervals are open at the lower boundary, closed at the upper boundary.
Facility entries give the random draw's bounds as multiples of the offered
fee; ship entries are kubars. The draw is applied to the resulting amounts,
not to an integer multiplier selected first.
The first row includes every worth at or below −100,000.

| Stored worth | Ship draw | Facility draw |
|---|---|---|
| ≤ −100,000 | 5,000–10,000 | 2.5–5 × fee |
| −100,000 to −50,000 | 7,500–15,000 | 5–10 × fee |
| −50,000 to 0 | 10,000–20,000 | 7.5–15 × fee |
| 0 to 100,000 | 12,500–50,000 | 10–20 × fee |
| 100,000 to 200,000 | 15,000–55,000 | 11–22 × fee |
| 200,000 to 300,000 | 17,500–60,000 | 12–24 × fee |
| 300,000 to 400,000 | 20,000–65,000 | 13–26 × fee |
| 400,000 to 500,000 | 22,500–70,000 | 14–28 × fee |
| 500,000 to 600,000 | 25,000–75,000 | 15–30 × fee |
| 600,000 to 700,000 | 27,500–80,000 | 16–32 × fee |
| 700,000 to 800,000 | 30,000–85,000 | 17–34 × fee |
| 800,000 to 900,000 | 32,500–90,000 | 18–36 × fee |
| 900,000 to 1 million | 35,000–95,000 | 19–38 × fee |
| 1 to 2 million | 37,500–100,000 | 20–40 × fee |
| 2 to 3 million | 40,000–110,000 | 20–40 × fee |
| 3 to 4 million | 50,000–120,000 | 20–40 × fee |
| 4 to 5 million | 60,000–130,000 | 20–40 × fee |
| 5 to 6 million | 70,000–140,000 | 20–40 × fee |
| 6 to 7 million | 80,000–150,000 | 20–40 × fee |
| 7 to 8 million | 90,000–160,000 | 20–40 × fee |
| 8 to 9 million | 100,000–170,000 | 20–40 × fee |
| 9 to 10 million | 110,000–180,000 | 20–40 × fee |
| 10 to 100 million | 120,000–190,000 | 20–40 × fee |
| > 100 million | 130,000–200,000 | 20–40 × fee |

## Human ship expansion

A ship auction adds 200 tons and the following increments. The travel-event
ship offer uses the same table and also adds 25,000 to `loanMax`; the auction
path does not add that credit. Neither path replaces the chosen ship identity.
Configured ad budgets are scaled to the new tonnage bracket, and passenger
demand is recomputed.

| Ship ID | Engine | Fuel capacity | Cargo | Passengers | Crew | Insurance range |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 5 | 50 | 4 | 2 | 6 |
| 2 | 0 | 10 | 60 | 3 | 2 | 8 |
| 3 | 0 | 30 | 40 | 3 | 1 | 2 |
| 4 | 0 | 10 | 65 | 5 | 3 | 8 |
| 5 | 0 | 15 | 50 | 2 | 1 | 6 |
| 6 | 0 | 15 | 50 | 4 | 2 | 6 |
| 7 | 1 | 10 | 40 | 3 | 2 | 6 |
| 8 | 0 | 15 | 55 | 3 | 2 | 6 |
| 9 | 0 | 15 | 45 | 5 | 2 | 4 |
| 10 | 0 | 10 | 75 | 1 | 1 | 10 |
| 11 | 0 | 10 | 40 | 8 | 6 | 2 |
| 12 | 0 | 15 | 55 | 4 | 3 | 6 |

## Facilities

A new facility offer draws a type 1–100, a slot 0–6 and a fee 500–5,000.
The type supplies its displayed name. Ownership stores **counts and total
fees per planet**, not a list of individual facility types. Each win adds
one to `facility[planet]` and the offered fee to `facilityFee[planet]`.

On a visit, a merchant pays every other owner's total fee at that planet.
Each owner receives that amount in `facilityRevenue[planet]`. The visitor
then collects their own accumulated local revenue and resets it to zero.
Human payment uses the shared cash/savings/debt helper; opponents subtract
cash directly. Bankruptcy erases a human's facilities and uncollected revenue.
Facility acquisition cost and revenue are not included as assets in the
[winning net-worth calculation](TURNS.md#net-worth-and-winning).

## Source reference

Raw `Gazillionaire.as`:

| Functions | Subject |
|---|---|
| `select_player_ship` (50486), `PlayerType.init` (`PlayerType.as`:445) | Starting stats |
| Auction branches of `doAmount` (48963) and `doYesNo_yes` (48496); `frm_Travel3_auction` (69983) | Bid submission and auction scheduling |
| `frm_Travel3_auctionShip` (70073), `frm_Travel3_auctionFacility` (70462) | Bid draws, settlement and awards |
| `frm_Travel2_yes` (63585–63758) | Travel-event ship expansion |
| `frm_Travel5_payFacilities` (51972), `frm_Travel5_revenueFacilities` (52015), `frm_Travel3_opponentFacilities` (67351) | Fees and collections |
