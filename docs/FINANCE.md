# Cash, debt and obligations

## Payment rules

The shared `subtract_cash(player, amount)` helper spends cash first, then
savings, then adds the unpaid remainder to the bank loan. It never checks
the loan limit and never uses Zinn credit. Individual action handlers decide
whether that payment path is allowed.

| Action | Funds checked / used |
|---|---|
| Market cargo, ordinary fuel, wages, tax, insurance | Cash only |
| Bank deposit / withdrawal | Transfer between cash and savings |
| Manual loan repayment | Cash only, limited to outstanding debt |
| Manual bank borrowing | Remaining `loanMax - loan` |
| Stock purchase | Size allowance from cash + savings, with a 10,000-kubar floor; payment may create debt |
| Facility fees, forced event costs, many planet specials | Shared helper; may create debt |
| Auction bid | Warns above available cash + savings + unused bank credit, or above 200,000; confirmation can still accept it |

## Interest and credit

Every individual departure applies unlocked interest, rounding down:

```text
loanInterest = floor(loan*loanRate/100); loan += loanInterest
zinnInterest = floor(zinnLoan*zinnRate/100); zinnLoan += zinnInterest
savingsInterest = min(100000, floor(savings*savingsRate/100))
savings += savingsInterest
```

The 100,000 cap applies to interest per departure, not the savings balance.
Initial rates are 5% bank loan, 4% Zinn, and 1% savings. Initial limits are
100,000 bank credit and 200,000 Zinn debt. Events and planet visits can change
rates and limits. The normal Zinn screen offers repayment, not a borrow button;
additional Zinn advances come through events and specials.

Choosing a destination is blocked when either debt is **greater than** its
limit. Exact equality permits departure; departure interest can then push it
above the limit. An over-limit balance is not an immediate global bankruptcy
trigger. The departure prompt lets the human return to the main menu or
accept bankruptcy. `bankrupt_player` marks the human bankrupt and clears all
facility counts, fees and uncollected revenue. Scheduling skips bankrupt
humans; the round-end worth calculation gives them a sentinel value.

## Crew

Each departure adds `crew*crewSalary` to unpaid wages. Manual payment requires
enough cash to pay the entire balance. When wages reach five payrolls, the
departure handler has a 1/3 chance of a strike. A strike forces payment through
`subtract_cash`, clears arrears, and raises per-crew salary by 500. The main
menu warning begins at four payrolls, before the strike threshold.

## Tax and tariffs

Passenger pickup accrues `floor(ticketRevenue*passTax/100)`. Export tariffs
accrue on each held commodity at departure using the previous planet's price;
imports use the destination's price in `frm_Travel5_ok`:

```text
tariff += floor(heldTons*postedPrice*tariffRate/100)  // per commodity
```

The import branch additionally requires an existing nonzero tax/tariff
balance. That condition is part of the recovered code, even though it is not
an obvious rule of the game. Defaults are 15% passenger tax, 2% export and
3% import. Manual payment clears tax and tariff together and requires cash.

At departure, a combined balance of at least `35*shipTons` has a 1/3 chance
of an audit. The audit collects three times the balance from cash, savings,
then bank debt and clears both balances. It runs before the current trip's
export tariff is added. Insurance changes the audit message, not collection.

## Source reference

Raw `Gazillionaire.as` unless stated otherwise:

| Functions | Subject |
|---|---|
| `subtract_cash` (49130), `doAmount` (48578), `frm_Bank_*`, `frm_Loan_*`, `frm_ZinnLoan_*` | Payments and manual banking |
| `PlayerType.init` (`PlayerType.as`:445) | Initial rates and limits |
| `frm_LeavePlanet_select_planet` (62452), `doYesNo_no` (48521), `bankrupt_player` (48564) | Debt limits and bankruptcy |
| `frm_Travel2_exit` (63082), `frm_Travel2_crewStrikes` (66758), `frm_Travel2_taxAudit` (66878) | Interest, payroll and enforcement |
| `frm_Passengers_pick_up` (55733), `frm_Travel5_ok` (51918), `frm_Tax_pay` (56134) | Tax accrual and payment |
