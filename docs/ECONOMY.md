# Economy and stocks

## Commodity markets

Each of seven planet slots has 18 commodities, arranged as three tiers of six.
`comR` is a supply rating, `comP` a price, and `comA` the available tonnage.
Buying and selling change tonnage immediately; supply ratings and prices are
rebuilt at the round boundary. See [market transactions](MARKET.md).

For commodity number `k = tier*6 + item + 1`, difficulty `d` (0–4), and supply
rating `R`, the ordinary price is:

```text
floorPrice = (d+1)*5*k
ceilingPrice = 40*k
price = floor((ceilingPrice-floorPrice)*(100-R)/100) + floorPrice
```

Higher difficulty raises the floor without changing the ceiling. Initial
ratings are random integers 0–100. Each round independently adds or subtracts
a random integer 0–20, then clamps the result to 0–100.

Availability is replaced each round, rather than replenished by adding a
fixed amount to unsold stock:

```text
available = rnd(0.2*R, R)
advertisedSupply = advertC[planet]*R/100
available += rnd(0.2*advertisedSupply, advertisedSupply)
if rnd(0,130) >= R: available = 0
```

The last test can erase the advertising benefit. Without other overrides,
the chance of nonzero stock at integer rating `R` is at most `R/131`.
Initial generation uses the first draw and the same zero-stock test, without
the advertising draw. Here `rnd(a,b)` means the game's exact
`floor(a + Math.random()*(b-a+1))`; fractional bounds are not first converted
to integer bounds.

Before the availability update, opponents contribute
`floor(shipTons/4 - 100)` at their destination if that expression is positive.
Human departures contribute `floor(advertInvestedC/50)` plus any cargo
capacity above 100 at their destination. The update consumes and clears all
seven `advertC` accumulators. This is why larger ships can increase available
stock without buying advertising.

Round-wide events run after ordinary prices and availability, so an event can
overwrite the formula for that round. They do not rewrite `comR`.
See [events](EVENTS.md#world-events).

## Human stock trading

The stock screen displays several planets, but trades use the current planet.
The buy/sell handlers accept that planet's view or the combined view (7),
and reject a crashed exchange. Current price is column `turn` below turn 15,
otherwise column 15, converted to an integer.

A purchase is limited to the larger of:

```text
floor(0.01*(cash+savings)/price)
floor(10000/price)
```

The 10,000-kubar floor is a purchase allowance, not an affordability check.
Payment uses `subtract_cash`, which can consume savings and create bank debt.
Both purchases and sales also charge `floor(0.01*price*quantity)` commission.
Purchase averages exclude commission and use the same rounded weighted-average
method as cargo. Full liquidation clears the average.

Only one successful stock purchase is allowed per human turn: `stockFlag`
is cleared on buying and reset by `frm_PlayerTurn_load`. Sales do not clear
it. Opponents have their own [allocation rules](OPPONENTS.md#stocks).

## Stock price updates

Each planet starts with trend 50 and price `1700 - 100*slot`. Prices occupy
columns 1–15: early rounds fill the next column; after turn 15 the history
shifts left and column 15 becomes the latest value.

An ordinary update draws a price change between 1% and 10% of the previous
price. Below 250, it instead draws 50–75 and sets trend to 1. The direction
test is `rnd(1,95) <= trend`, so trend is not literally a percentage:

| Direction | Trend update | Price update |
|---|---|---|
| Rise | If above 50, add 5, capped at 85; otherwise set to 51 | Add the change |
| Fall | If at/below 50, subtract 5, floored at 15; otherwise set to 50 | Subtract, floored at zero |

A zero price sets `stockCrash`. The human turn-start crash handler clears
that human's shares and purchase average; human 0's handler also clears all
opponent shares on that exchange. The following price update clears the
crash flag and restarts the exchange at 1,000 with trend 50.

From turn 4, news has a 15% chance to attempt a special stock story at a random
planet, provided that exchange has not crashed. IDs 1000/1001 raise/lower its
price by `25 + newsData/4` percent (25.25–50%), round down, and reset trend to
50, but only when price exceeds 250. Otherwise they become ordinary news.
IDs 1002/1003 set trend to 0 when it was at/below 50, otherwise 100. Ordinary
news also supplies context to travel events; it is not all decorative text.

## Source reference

Raw `Gazillionaire.as`, under `$GAZ_DATA_DIR/src/decompiled/scripts/`:

| Functions | Subject |
|---|---|
| `initializeGame` (49459), `frm_Travel3_economicChange` (69867), `frm_Travel3_commodityAvailable` (69907), `frm_Travel3_commodityPrice` (69956) | Commodity generation and refresh |
| `frm_Stock_buy` (53750), `frm_Stock_sell` (53793), stock branch of `doAmount` (48617–48685) | Human trades and commission |
| `frm_PlayerTurn_load` (50723), `frm_PlayerTurn2_stockCrash` (51221) | Purchase limit and crash losses |
| `frm_Travel3_stockMarket` (69504), `frm_Travel3_newsEvent` (69640) | Price evolution and news |
