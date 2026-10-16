# Planet specials

`frm_Explore_special` opens the current planet's special unless
`planetSpecialFlag` is set. It is one flag per human, cleared on departure,
not a permanent “visited” flag per planet. Most actions consume the visit
even when the result is only a report. Bass analysis clears the flag again;
failed Queg cargo-space checks and invalid casino wagers also allow a retry.

Several offers use `random` (the human's stored 1–100 departure draw) and
`newsData` (the shared 1–100 news draw), so repeated opening is not necessarily
a fresh random offer. Payments generally use `subtract_cash`, allowing
savings and bank debt. A warning in the offer text is not always a hard
affordability guard in the action handler.

| ID / planet | Mechanical effects |
|---|---|
| 0 Vexx | Tax-rate changes and cancellation of the visitor's tax/tariff balance; many rolls are reports only |
| 1 Pyke | When newsData is not divisible by 4, pay random*newsData*6 for engine +1; otherwise report only |
| 2 Mira | Change `eventGood` and `eventLastGood`; beneficial thresholds range 60–85, adverse outcomes set 15 |
| 3 Stye | Bank credit +50,000/+75,000, rate changes, or partial bank-debt forgiveness |
| 4 Loro | Crew-related costs, salary −100 when above 1,000, or unpaid wages cleared; one fallback fills fuel |
| 5 Zile | Zinn rate/limit changes, partial forgiveness, or an advance paired with a larger credit limit |
| 6 Frac | Insurance range/quote changes or cash effects based on random*cargoCapacity*4 |
| 7 Tilo | Casino wager and repeated double-or-nothing choices; closed when newsData is divisible by 6 |
| 8 Queg | Discounted bulk cargo offer, subject to space; unavailable when newsData is divisible by 5 |
| 9 Xeen | 2/3 chance to pay for an upgrade selected by random%4: engine +1, cargo +10, passenger capacity +1, fuel capacity +5 |
| 10 Ooom | Paid luck reading and possible cash prize; report-only when turn is divisible by 5 |
| 11 Hork | Publicity stories, some adding or subtracting rnd(25,75)*shipTons |
| 12 Bass | Describes each planet's stock trend without changing it; periodic report-only alternative |
| 13 Nosh | Discounted full refuel unless newsData is divisible by 5 or tank is already full |

## Financial visits

Stye draws 1–31. Mechanical cases include bank-limit increases of 50,000
(roll 7) or 75,000 (22); bank-rate reductions (8, 23, 24) when rate is at
least 4, or at least 2 and cash+savings−both loans exceeds 5 million;
otherwise those cases increase it. Savings-rate cases toggle around 2.
Roll 10 removes one third of bank debt when debt exceeds 20; roll 26 removes
one quarter. Both round the remaining debt down and fall back to savings-rate
changes when debt is too small. Rolls 11/27 lower savings rate if above 1,
otherwise raise bank rate.

Zile also draws 1–31. Rolls 7/22/23 reduce Zinn rate by 1 when at least 2,
otherwise set it to 2. Rolls 8/24 add 50,000/75,000 to the limit. Rolls 9/25
forgive a third/quarter of debt above 20. Roll 10 adds 50,000 debt and cash,
plus 75,000 limit; roll 26 adds 40,000 debt and cash, plus 60,000 limit.

## Bulk cargo and refuelling

Queg's commodity is `tier=turn%3`, `item=random%6`. Quantity is
`max(floor(cargoCapacity*random/100), floor(cargoCapacity/2))`.
Price interpolates between the ordinary difficulty floor and ceiling using
`newsData/100`, capped at `floor(localPrice*.9)`. The entire lot must fit;
the action updates ship quantity and average cost without reducing the
ordinary market's availability. A failed space check does not consume the visit.

Nosh charges `floor(localFuelPrice*(1-(10+random/2)/100))` per missing fuel
unit and fills the tank. The discount therefore ranges from 10.5% to 60%
before rounding the unit price. Tank capacity is not increased.

## Gambling and fortune telling

Tilo accepts a positive initial wager up to 5% of cash. It deducts the wager,
then a draw 1–20 above 10 loses it. Otherwise the player can take twice the
stake or try again: the first further success test is 9/20, then 8/20, etc.
Each success doubles the prospective payout and reduces the threshold by 1.
Declining cashes out; a failed draw pays nothing. It is not a constant 50/50
double-or-nothing game.

Ooom's paid reading costs `floor(random*shipTons/10)`. Luck at/below 60 only
produces a reading. Above that, a 1/2 draw can pay 5, 10, 15, 20 or 25 times
the fee for luck bands ending at 65, 70, 75, 80 or above 80. It reads luck;
it does not improve `eventGood`.

## Source reference

Raw `Gazillionaire.as`: `frm_Special_load` (56289–56643) prepares offers;
`frm_Special_action` (56644–58645) applies the planet branches in ID order.
The casino's initial wager commits in `doAmount` (48922–48961), subsequent
draws in `doYesNo_yes` (48481–48494), and cash-out in `doYesNo_no` (48546–48550).
