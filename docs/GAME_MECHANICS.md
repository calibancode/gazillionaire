# Game mechanics

Gazillionaire's merchants trade commodities, carry passengers and invest
across seven planets. The initial winning target is 5 million kubars. The
round-end winner must strictly exceed it; the calculation counts cash,
savings and shares minus loans, excluding ships, cargo and facilities.

This reference describes the recovered Steam code in our own words. Source
locations use raw files under `$GAZ_DATA_DIR/src/decompiled/scripts/`
(default `.local-data/src/decompiled/scripts/`); function names remain useful
if a different export shifts the line numbers. Source readings are separate
from [runtime verification](VERIFICATION.md).

## Systems

| Reference | Contents |
|---|---|
| [Market](MARKET.md) | Human buying, selling, cost basis and quick mode |
| [Economy and stocks](ECONOMY.md) | Supply, price generation, advertising effects, share trading and crashes |
| [Turns and travel](TURNS.md) | Departure, round scheduling, arrival order and winning |
| [Finance](FINANCE.md) | Payment sources, credit, interest, wages, tariffs and bankruptcy |
| [Operations](OPERATIONS.md) | Passengers, advertising, warehouses, fuel and insurance |
| [Ships and auctions](SHIPS_AND_AUCTIONS.md) | Starting stats, expansions, bids and facility revenue |
| [Opponent economy](OPPONENTS.md) | Commodity selection, synthetic payouts, stocks and upgrades |
| [AI balancing](AI_BALANCING.md) | Cash growth and difficulty-dependent catch-up tables |
| [Events](EVENTS.md) | Ordered event scans, choices, sabotage, hazards and world changes |
| [Planet specials](PLANET_SPECIALS.md) | Local services, discounts, upgrades and gambling |
| [Saves](SAVE_FORMAT.md) | Slots, resume behavior and complete binary layout |
| [Code map](CODE_MAP.md) | State classes, screen conventions and source entry points |

## Difficulty and initial state

| Level | Name | Internal difficulty | Human cash | Zinn debt | Initial good-event threshold | Opponent cash | Opponent iQ |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | Tutorial | 0 | 50,000 | 100,000 | 85 | −50,000 | 50 |
| 2 | Novice | 0 | 25,000 | 110,000 | 75 | −85,000 | 75 |
| 3 | Beginner | 1 | 0 | 120,000 | 65 | −120,000 | 100 |
| 4 | Intermediate | 2 | 0 | 130,000 | 55 | −130,000 | 125 |
| 5 | Expert | 3 | 0 | 140,000 | 50 | −140,000 | 150 |
| 6 | Master | 4 | 0 | 150,000 | 50 | −150,000 | 175 |

`level` selects AI branches; `difficulty` sets ordinary commodity price
floors. `iQ` scales opponent cargo quantity, rather than selecting a general
search algorithm. There are six opponents and one to six human slots.
Each opponent starts at 400 tons on the slot matching its ID; engine ratings
for IDs 1–6 are 5, 5, 5, 4, 5, 6. Humans also start at 400 tons, with
[ship-dependent capacities](SHIPS_AND_AUCTIONS.md#starting-ships).
The calendar starts at year 139 and round 1.

Source: `initializeGame` (49459), `set_up_players` (49708),
`PlayerType.init` (`PlayerType.as`:445), `OpponentType.init`
(`OpponentType.as`:116).

## Tutorial progression

The tutorial starts with `activateTurn = 1`. Features unlock against this
counter, rather than directly against `g.turn`:

| Threshold | Feature | Threshold | Feature |
|---:|---|---:|---|
| 2 | Zinn | 10 | Advertising |
| 3 | Supply | 11 | Tax |
| 4 | Bank loan | 12 | Bank savings |
| 5 | Insurance | 13 | Warehouse |
| 6 | City view | 14 | Explore |
| 7 | Fuel | 15 | Distance |
| 8 | Passengers | 16 | Facilities |
| 9 | Crew | 17 | Stocks |

`frm_Tutorial_load` (52055) maps rounds 3, 4, 6, 7, 8, 9 to progression
2, 3, 4, 5, 6, 7. After that, single-player exposes a button to add complexity;
multiplayer increments progression at round boundaries. The scheduler clears
`tutor` at progression 17. Individual handlers choose `>=` or `>` at feature
boundaries; see `frm_Travel3_load` (66994).

## Planets and map slots

A session selects seven distinct identities from fourteen, stored in
`planetIndex[0…6]`. `randomize_planets` makes six replacement passes over an
initial seven-slot list, rejecting identities already present; it is not
implemented as a uniform seven-element sample.

| Identity | Planet | Special service |
|---:|---|---|
| 0 | Vexx | Imperial tax changes |
| 1 | Pyke | Engines |
| 2 | Mira | Luck |
| 3 | Stye | Bank terms |
| 4 | Loro | Crew |
| 5 | Zile | Zinn credit |
| 6 | Frac | Insurance |
| 7 | Tilo | Gambling |
| 8 | Queg | Bulk cargo |
| 9 | Xeen | Ship upgrades |
| 10 | Ooom | Luck reading |
| 11 | Hork | Publicity |
| 12 | Bass | Stock analysis |
| 13 | Nosh | Fuel |

Map coordinates belong to slots, not identities:
`(20,0), (14,6), (11,13), (8,3), (3,10), (21,11), (0,1)`.
Changing planet selection changes the local services at those coordinates.
Source: `randomize_planets` (49647), `initializeGame` and
`GameStrings.initialize`.

## Commodities

| Tier | Items in index order (0–5) |
|---|---|
| 0 | Cantaloupe, Jelly Beans, Moon Ferns, Frog Legs, Whip Cream, Babel Seeds |
| 1 | Diapers, Umbrellas, Toasters, Polyester, Hair Tonic, Lava Lamps |
| 2 | Oxygen, Oggle Sand, Kryptoons, X Fuels, Gems, Exotic |

Source: `GameStrings` keys `comName_<tier>_<item>`.
