# Serialized game layout

This is the ordered payload of a save slot's `ByteArray`, not the outer
SharedObject `.sol` container. Source: `serialize` and `deserialize` in raw
`GameType.as`, `PlayerType.as` and `OpponentType.as`. See [save behavior](../SAVE_FORMAT.md).

Types name the actual ByteArray operations: `I` = writeInt, `D` = writeDouble,
`B` = writeBoolean, `U` = writeUTF. Comma-separated fields are consecutive
writes in the stated order. A repeated row writes its entire group per index;
it does not write all of one field followed by all of the next. No array
lengths, record tags or schema version are written except the initial human
and opponent counts. Index ranges are inclusive.

## GameType

| Type / repetition | Ordered fields |
|---|---|
| I | playerNumberOf, opNumberOf |
| Human records, 0…playerNumberOf−1 | PlayerType below |
| Opponent records, 1…opNumberOf | OpponentType below |
| I | activateTurn, activateZinn, activateSupply, activateLoan, activateInsurance, activateViewCity, activateFuel, activatePassengers, activateCrew, activateAdvertising, activateTax, activateBank, activateWarehouse, activateExplore, activateDistance, activateFacility, activateStock |
| D × slots 0…6 | advertC[slot] |
| I | auction, auctionLast, auctionCompany, auctionNextCompany, auctionCompanyLast, auctionNextCompanyLast |
| D | auctionHighBid, auctionNextBid, auctionHighBidLast, auctionNextBidLast |
| I, I, D, I, I, D | auctionFacilityType, auctionFacilityPlanet, auctionFacilityFee, auctionFacilityTypeLast, auctionFacilityPlanetLast, auctionFacilityFeeLast |
| D, D, D × slot 0…6, tier 0…2, item 0…5 | comR, comP, comA at each cell |
| I, D, I, D | difficulty, dateYear, exportTariff, fuelPriceRange |
| D × slots 0…6 | fuelCost[slot] |
| I, I, I, B | game, gameEvent, importTariff, isMidTurn |
| I | level, news, newsData, newsPlanet, passTax |
| I, I, I × slots 0…6 | planetIndex[slot], planetX[slot], planetY[slot] |
| I | player |
| I × combined player count | playerOrder[0…playerNumberOf+opNumberOf−1] |
| I, D | playerTurnCounter, sellingProfit |
| Per slot 0…6 | B stockCrash; D stockPrice[1…15]; I stockTrend |
| B, D, B | stockFlag, turn, tutor |
| I, I, D, D | weather, weatherPlanet, winner, winningPoint |

## PlayerType

| Type / repetition | Ordered fields |
|---|---|
| D | advertInvestedP, advertInvestedC, advertFixP, advertFixC, advertP |
| I, B | age, bankrupt |
| D, D × tier 0…2, item 0…5 | comS, comPP at each cell |
| D, D, I, D, D | cargoCapacity, cash, crew, crewSalary, crewWagesOwed |
| I, I, B | engine, eventGood, eventLastGood |
| I, D, D × slots 0…6 | facility, facilityFee, facilityRevenue at each slot |
| D, D | fuel, fuelCapacity |
| D × 0…20 | history |
| B, D, D, D, I, D, D, D | insurance, insurancePriceRange, insuranceCost, loan, loanRate, loanInterest, loanMax, netWorth |
| I | planet, planetLast, playerShip |
| U | playerName, playerNameShort |
| B | quickWarehouse, quickBuy, quickDeposit, quickBank, quickLoan, quickAdvertising, quickCrew, quickFuel, quickExplore, quickTravel, quickPassengers, quickTax, quickInsurance |
| I, D, D, I, D | random, sabotageDamage, savings, savingsRate, savingsInterest |
| D, D × slots 0…6 | sharePrice[slot], share[slot] |
| I, I, D, D, B | shipTons, supplyPlanet, travelTime, travelDelayed, turnTaken |
| D | passengers, passengerCapacity, passT, passTicketPrice, profitPerPassenger |
| B, B, D, D, D | passFlag, planetSpecialFlag, tariff, tax, warehouseSpace |
| D, D × slot 0…6, tier 0…2, item 0…5 | warehouse, warehouseGoodsValue at each cell |
| D, D, I, D | zinnLoan, zinnMax, zinnRate, zinnInterest |

`cargoTons` and `warehouseT[slot]` are absent: deserialization recomputes them
by summing quantities. Cached totals in a live session need not survive a
save round trip if they disagree with the grids.

## OpponentType

| Type / repetition | Ordered fields |
|---|---|
| D, I, I, I, D, B | netWorth, engine, planet, planetLast, travelTime, turnTaken |
| I, I, D, D, D, I | comTag1, comTag2, comS, shipTons, cash, iQ |
| D × 0…20 | history |
| I, D, D, D × slots 0…6 | facility, facilityFee, facilityRevenue, share at each slot |

The game does not serialize its random-number generator, temporary
`frame_globals`, active popup or media playback. Loading restores state, not
an instruction-by-instruction continuation of a random event dialog.
