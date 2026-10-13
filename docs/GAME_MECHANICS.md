# Game mechanics (as implemented in `Gazillionaire.as`)

This is a reverse-engineered description of the systems implemented in the
decompiled source. Line references are to `$GAZ_DATA_DIR/src/decompiled/scripts/Gazillionaire.as`
and the state classes.

## Premise

You are a space merchant in the Kukubia system. Buy commodities cheaply on one
planet, travel, and sell them for a profit. The first merchant to reach a net
worth of **5 000 000 kubars** (`g.winningPoint = 5000000`, `initializeGame`)
wins.

## Difficulty levels

`GameStrings` names six levels; `initializeGame(level)` maps them to an
internal `difficulty` 0–4 and the `tutor` flag:

| Level | Name | difficulty | tutor |
|-------|------|-----------|-------|
| 1 | Tutorial | 0 | true |
| 2 | Novice | 0 | false |
| 3 | Beginner | 1 | false |
| 4 | Intermediate | 2 | false |
| 5 | Expert | 3 | false |
| 6 | Master | 4 | false |

The tutorial progressively unlocks features. `GameType.activate*` fields store
the turn at which each feature turns on:

```
turn(1) Zinn(2) Supply(3) Loan(4) Insurance(5) ViewCity(6) Fuel(7)
Passengers(8) Crew(9) Advertising(10) Tax(11) Bank(12) Warehouse(13)
Explore(14) Distance(15) Facility(16) Stock(17)
```

## Planets

There are **14 named planets** (`planet_0` … `planet_13` in `GameStrings`):

| idx | Name | Description |
|----|------|-------------|
| 0 | Vexx | capital, Imperial Magistrate |
| 1 | Pyke | industrial center; sells L-Tech engines |
| 2 | Mira | religious heart of Kukubia |
| 3 | Stye | financial hub, Traders' Union |
| 4 | Loro | vacation world |
| 5 | Zile | home of Mr. Zinn (loans) |
| 6 | Frac | Voyager's Insurance HQ |
| 7 | Tilo | casinos (gambling) |
| 8 | Queg | smuggler's haven |
| 9 | Xeen | junkyard of spare ship parts |
| 10 | Ooom | fortune teller |
| 11 | Hork | media capital |
| 12 | Bass | stock-market analysts |
| 13 | Nosh | fuel depot |

Each game selects **7 of the 14** planets (`randomize_planets()`) into
`planetIndex[0..6]`. The seven map slots have fixed coordinates
(`initializeGame`):

```
slot: 0     1     2     3     4     5     6
x:   20    14    11     8     3    21     0
y:    0     6    13     3    10    11     1
```

## Commodities

Six commodities per tier, three tiers (18 total), named `comName_<tier>_<i>`:

| Tier | Items |
|------|-------|
| 0 | Cantaloupe, Jelly Beans, Moon Ferns, Frog Legs, Whip Cream, Babel Seeds |
| 1 | Diapers, Umbrellas, Toasters, Polyester, Hair Tonic, Lava Lamps |
| 2 | Oxygen, Oggle Sand, Kryptoons, X Fuels, Gems, Exotic |

Per planet, per tier, per commodity the game stores three numbers in
`GameType`:

* `comR[planet][tier][item]` — **supply** 0–100 (0 = rare/expensive).
* `comP[planet][tier][item]` — **price** per ton.
* `comA[planet][tier][item]` — **amount available**.

### Economy generation (pseudocode)

From `initializeGame`, with `idx = tier*6 + item + 1` (1…18):

```
comR = f_rnd(0, 100)
comP = floor( (40*idx - (difficulty+1)*(5*idx)) * (100 - comR) / 100 )
       + (difficulty+1)*(5*idx)
comA = f_rnd(0.2*comR, comR)
if (f_rnd(0,130) >= comR) comA = 0
```

So base price rises with commodity index (later tiers are worth more) and falls
as supply rises; higher difficulty raises the floor price. A commodity has a
chance of being entirely unavailable.

## Travel

Distance is Euclidean over the planet grid:

```
distance = sqrt((x1-x2)^2 + (y1-y2)^2)
```

Travel time (`frm_Travel3_travel`):

```
travelTime = distance * 5 / engine          // opponents
travelTime = floor(distance * 5 / engine * travelDelayed)   // players
```

`travelDelayed` accumulates bad-luck multipliers (storms, pirates, …) and is
reset to 1 after each trip. Players/opponents with the shortest travel time
tend to arrive first and get first pick of the market.

### Fuel

Fuel is consumed per trip (`frm_Travel1_move_ship`), roughly:

```
distance/2  and  shipTons/100  →  fuel -= f_rnd(1, distance/2) + f_rnd(1, shipTons/100)
```

The fuel-distance expression uses bitwise XOR where the travel-time
calculation uses squared differences. It therefore does not compute Euclidean
distance and may produce `NaN`. The reconstruction preserves this behavior.

## Ships and engines

Twelve playable ships/companies (`SWF/SHIP1..12.SWF`), each with fixed
crew/passenger/fuel/cargo/engine stats in `select_player_ship`. Engines are
rated in "kuarp"; travel time is inversely proportional. A faster engine can be
bought on **Pyke**, and **Xeen** can turbocharge an existing engine
(`frm_Travel3_opponentBuysEngine`).

## Facilities

Planetary facilities are an investment system: 100 named facility types
(`facility_1` … `facility_100`) — e.g. *Conference Center*, *Fuel Pumps*,
*Water Works*, *Asteroid Destruction Unit*. Each player owns up to one facility
per planet (`facility[7]`, `facilityFee[7]`, `facilityRevenue[7]`) that charges
fees and yields revenue. Facilities are also won at auctions
(`frm_PlayerTurn2_AuctionFacility`).

## Banking, loans, savings

* **Traders' Union Bank** (`frm_Bank_*`) — deposit/withdraw savings; interest
  is paid per week (per planet hop) up to a 100 000-kubar cap.
* **Traders' Union Loan** (`frm_Loan_*`) — borrow up to `loanMax` (initial
  100 000) at `loanRate` (initial 5 %/week); interest accrues on departure.
* **Mr. Zinn** (`frm_ZinnLoan_*`) — a second, larger line of credit
  (`zinnMax`, initial 200 000, `zinnRate` initial 4 %) used when the bank
  cuts you off; it is the starting debt (`zinnLoan` 100 000–150 000 by ship).
* **Bankruptcy** (`bankrupt_player`) — triggered when you cannot meet
  obligations.

## Stocks

Each planet has a stock exchange (`frm_Stock_*`). Prices are stored as
`stockPrice[planet][1..15]`, with `stockTrend[planet]` and `stockCrash[planet]`.
Initial price is `1700 - 100*planet` and shares can only be traded on the
planet where the exchange is. Events that move the market:
`frm_PlayerTurn2_stockFall` and `frm_PlayerTurn2_stockCrash`.

## Passengers, crew and cargo

* **Passengers** (`frm_Passengers_*`, `computePassengers`) — set a ticket
  price, carry up to `passengerCapacity`; profit per passenger is computed and
  an advertising investment (`advertP`) drives demand.
* **Crew** (`frm_Employee_*`) — crew count, salary and accrued
  `crewWagesOwed`; too much unpaid wages causes strikes
  (`frm_Travel2_crewStrikes`, checked at `crewWagesOwed >= crew*salary*5`).
* **Warehouse** (`frm_Warehouse_*`) — per-planet storage grid
  `warehouse[planet][tier][item]` plus `warehouseGoodsValue`; a warehouse fire
  event can destroy stock.
* **Advertising** (`frm_Advertising_*`) — commodity ads increase
  `comA` (availability, not price) on the next planet for one week; passenger
  ads set `advertP`.

## Specials, events and sabotage

* **Planet Specials** (`frm_Explore_special`, `frm_Special_action`) — a
  one-shot random benefit/cost per planet (fuel discounts, engine boosts,
  cash, …).
* **Travel events** (`frm_Travel4_*`, `frm_Travel2_*`) — good and bad events:
  pirates, asteroids, stellar whirlpools/typhoons, storms, fuel shortage,
  tax audits, commodity price shocks, news.
* **Sabotage** (`sabotageDamage`, `frm_Travel4_showSabotageResult`).
* **Auctions** (`frm_PlayerTurn2_AuctionShip/AuctionFacility`) — competing
  players bid on ships and facilities.
* **Weather / news** — `game.weather`, `game.news` with
  124 news items; the News and Weather screens surface them.

## Turn structure

Human turns are driven by `frm_PlayerTurn_*`; the AI acts during
`frm_Travel3_opponentTurn` / `frm_Travel4_opponentArrivesOnPlanet`. A "week"
advances every time a player travels between planets, at which point interest,
wages, and market changes are applied. Autosave runs via `autosave()`.

## Win / lose

`frm_Travel3_winCheck` compares net worth to `winningPoint`. On reaching it,
`frm_WinGame*` screens run. Bankruptcy routes to `frm_Bankrupt*`.

## Quick reference: core state fields

`GameType`: `turn`, `dateYear`, `level`, `difficulty`, `tutor`, `player`,
`playerNumberOf`, `opNumberOf`, `playerOrder`, `planetIndex`, `planetX/Y`,
`comR/P/A[7][3][6]`, `fuelCost[7]`, `importTariff`, `exportTariff`,
`passTax`, `stockPrice[7][16]`, `stockTrend[7]`, `stockCrash[7]`,
`winningPoint`, `winner`.

`PlayerType`: `cash`, `savings`, `loan`(+`loanRate`/`loanMax`),
`zinnLoan`(+`zinnRate`/`zinnMax`), `fuel`/`fuelCapacity`, `cargoCapacity`,
`shipTons`, `crew`/`crewSalary`/`crewWagesOwed`, `engine`, `planet`/`planetLast`,
`playerShip`, `passengers`/`passengerCapacity`/`passTicketPrice`,
`warehouse[7][3][6]`, `facility[7]`/`facilityFee[7]`/`facilityRevenue[7]`,
`share[7]`/`sharePrice[7]`, `insurance`, `netWorth`, `history[21]`,
`travelTime`, `travelDelayed`, `eventGood`, `bankrupt`.

`OpponentType`: `cash`, `iQ`, `engine`, `planet`/`planetLast`, `comTag1/2`,
`comS`, `shipTons`, `travelTime`, `netWorth`, `history[21]`, `facility[7]`,
`facilityFee[7]`, `facilityRevenue[7]`, `share[7]`.
