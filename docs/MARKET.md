# Market transactions

The human market trades at the current planet's posted price. Buying reduces
the available quantity; selling adds it back. Neither transaction recalculates
the posted price in its handler. Round-wide price changes happen separately.

These are human trades; [opponents](OPPONENTS.md) use a separate routine.

## State and selection

| Field | Meaning |
|---|---|
| `g.comP[planet][tier][item]` | Posted price per ton |
| `g.comA[planet][tier][item]` | Available tons |
| `player.comS[tier][item]` | Tons held aboard the ship |
| `player.comPP[tier][item]` | Average purchase price, rounded down on buying |
| `player.cargoTons` / `cargoCapacity` | Total load / capacity |
| `g.sellingProfit` | Sale margin accumulated since its departure reset |

`frm_Market_refresh_grid` builds a row-to-commodity mapping. A visible row is
not necessarily its commodity index: filtered views omit commodities.

| Market `frame_globals` index | Meaning |
|---|---|
| 108 | View: 0 = all, 1 = available or held, 2 = held cargo |
| 109 | Selected visible row, or −1 |
| 110 | Pending amount-dialog action: 0 = buy, 1 = sell |
| 111 + row | Commodity index (0–17), or −1 for an unused row |

The commodity index decodes as `tier = floor(index/6)`, `item = index%6`.
The “available” view includes commodities already held even when none remain
for sale. Changing the view clears the selection.

## Buying

`frm_Market_buy` rejects an absent selection, cash below one ton's price, a
full cargo hold, or zero availability. It computes the maximum quantity from
available stock, free cargo space and `floor(cash/price)`.

Quick-buy mode immediately buys that maximum. Normal mode opens an amount
dialog with quarter, half and maximum presets. The actual normal-mode
transaction is in `doAmount`, in the branch for `frm_Market`; it checks cash,
availability and remaining cargo space again before applying the amount.

For quantity `q`, posted price `price`, existing quantity `held` and purchase
average `average`, the successful purchase updates:

```text
average = floor((average*held + price*q) / (held+q))
cash -= price*q
cargoTons += q
held += q
available -= q
```

The source pays through `subtract_cash`. That helper can draw savings and
increase bank debt for other callers, but both market purchase paths limit
the purchase to cash first. Savings are not extra buying power here.
Normal-mode quantity writes are explicitly floored; the quick path directly
adds or subtracts its integer maximum.

Example: 10 tons bought at 101, followed by 5 at 110, produce a stored average
of `floor(1560/15) = 104`. The stored average, rather than a separate lot
ledger, determines later reported sale profit.

## Selling

`frm_Market_sell` rejects an absent selection or an empty holding. Quick mode
sells the entire holding. Normal mode opens the amount dialog, and `doAmount`
rejects quantities larger than the holding before applying the sale.

```text
sellingProfit += (price-average)*q
cash += price*q
cargoTons -= q
available += q
held -= q
```

Normal mode floors the margin and proceeds before adding them, and floors
the updated quantity fields. Quick mode uses the whole holding directly.
The purchase average is cleared only when the holding reaches zero; a partial
sale retains it. Selling below the average is permitted.

The sound cue is separate from the transaction: below-average prices play
`BADDEAL`; a price above the average and at least `36*(tier*6+item+1)` plays
`GOODDEAL`. Neither cue changes the price or adds a bonus.

## Quick mode

`frm_Market_buy_sell` makes a row click sell all if that commodity is already
held. Otherwise it buys the maximum if space and stock permit. Thus clicking
a held commodity in quick mode sells it even if more is available to buy.
`frm_Market_quick` disables the separate buy/sell buttons while this mode is on.

## Source reference

All locations are in raw `Gazillionaire.as`.

| Function | Lines | Subject |
|---|---|---|
| `doAmount` (market branch) | 48789–48850 | Normal-mode transaction commit |
| `subtract_cash` | 49130–49147 | Shared payment helper |
| `frm_Market_refresh_grid` | 54559–54683 | Filtered rows and screen state |
| `frm_Market_quick` | 54685–54701 | Quick-mode toggle |
| `frm_Market_buy_sell` | 54703–54737 | Row-click dispatch |
| `frm_Market_buy` | 54739–54795 | Buy limits, quick purchase and amount dialog |
| `frm_Market_sell` | 54797–54838 | Sale handling and amount dialog |
