# Passengers, advertising, storage and insurance

## Passengers

Passenger income is collected once per stop by `frm_Passengers_pick_up`, not
automatically on arrival. `passFlag` prevents a second pickup. The handler
adds `profitPerPassenger*passengers` to cash and accrues passenger tax when
unlocked. Changing the advertised ticket price affects the next demand
calculation, rather than recomputing the current passengers immediately.

At departure, `computePassengers` clears `passFlag`, snapshots ticket price
as `profitPerPassenger` (minimum 100), and draws potential demand:

```text
demand = rnd(0, passengerCapacity) + rnd(advertP/4, advertP)
passT = floor(demand*1000/(price*penalty))
passengers = min(passT, passengerCapacity)
```

| Ticket price | Penalty |
|---|---:|
| Up to 4,000 | 1 |
| 4,001–5,000 | 1.5 |
| 5,001–6,000 | 2.25 |
| 6,001–7,000 | 3.25 |
| 7,001–8,000 | 4.75 |
| 8,001–9,000 | 7 |
| 9,001–10,000 | 10 |
| Above 10,000 | No demand |

`passT` retains uncapped demand, which capacity upgrades can use. Fresh ship
selection instead starts with a random 1–capacity passenger count.

## Advertising

The two campaigns have separate configured budgets (`advertFixP/C`) and paid
budgets (`advertInvestedP/C`). Placing an ad refunds the previously paid budgets
into cash, replaces them with the configured amounts, and charges the new sum.
It therefore replaces an existing campaign rather than stacking repeated
payments. Affordability includes those refunds, but excludes savings.

Passenger advertising sets `advertP = advertInvestedP/125`; commodity ads feed
the destination's [availability accumulator](ECONOMY.md#commodity-markets).
Departure computes demand using the campaign, then clears the paid budgets
and `advertP`. Configured budgets remain for the next purchase.

## Warehouse

Every human has a storage grid at each of seven planets. `warehouseSpace`
starts at 50 and limits each planet separately. `warehouseT[planet]` caches
the local total; `warehouseGoodsValue` stores average cost per commodity,
not total inventory value.

Storing moves tons from ship to the current planet. Taking reverses the
transfer. Neither changes cash or local market availability. Each transfer
blends the destination's average with the source's average using a rounded-
down weighted mean, as in [cargo purchases](MARKET.md#buying).
The amount-dialog path checks quantities and capacity again in `doAmount`.
Quick mode transfers the largest amount that fits; a row click takes when
that commodity exists in storage, otherwise stores from the ship.

Emptying a warehouse holding clears its stored average. Emptying a ship
holding by storing it does **not** clear `comPP`: both paths contain a bare
read where a reset might be expected. A later weighted-average purchase with
zero held tons ignores that stale value. Warehouse fires can erase a whole
planet's inventory and averages unless the player is insured.

## Fuel and insurance

Ordinary fuel buying is cash-only and limited by tank space. Normal prices
are rerolled each round between `fuelPriceRange` and ten times that value;
world events and Nosh visits can override them. Consumption occurs during
departure. With coordinate differences `dx`, `dy`, the source uses
`sqrt(dx ^ 2 + dy ^ 2)/2` as the first random draw's upper bound, plus a
second draw bounded by `shipTons/100`; both lower bounds are 1. In
ActionScript `^` is bitwise XOR, not squaring. Preserve this expression when
reconstructing behavior; [arrival timing](TURNS.md#destinations-and-arrival-order)
uses the separate, ordinary Euclidean formula.

Fuel below zero triggers a rescue, not fuel equal to zero. Rescue costs
`fuelCapacity*fuelPriceRange*10 + 10000`, uses the shared payment helper,
fills the tank and adds 1 to `travelDelayed`.

Insurance is a cash purchase for the next departure sequence. Departure
rerolls its next quote with `rnd(insurancePriceRange, insurancePriceRange*1000)`
and clears coverage after events, fuel checks and passenger computation.
Coverage is not a universal loss shield: some branches avoid costs or cargo
loss, while others only change the explanatory text. In particular, strikes,
audits, rescue charges and several delays still take effect.
See [events](EVENTS.md).

## Source reference

Raw `Gazillionaire.as`:

| Functions | Subject |
|---|---|
| `computePassengers` (66946), `frm_Passengers_pick_up` (55733), passenger branch of `doAmount` (48909) | Demand, ticket setting and revenue |
| `frm_Advertising_place_ad` (55987), `frm_Travel2_exit` (63082) | Campaign replacement and consumption |
| `frm_Warehouse_take_store` (55520), `frm_Warehouse_take` (55552), `frm_Warehouse_store` (55606), warehouse branch of `doAmount` (48851) | Transfers and cost basis |
| `frm_Fuel_buy` (62302), `frm_Travel2_fuelRunsOut` (66806), `frm_Insurance_buy` (56199) | Fuel and insurance |
