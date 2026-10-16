# Opponent cash balancing

Three independent mechanisms affect cash in an opponent turn: commodity
proceeds, positive-cash growth, and the signed `opponentLevel` adjustment.
[Opponent economy](OPPONENTS.md) describes the first. This page gives the
other two, in execution order. Values come from raw `Gazillionaire.as`:
`frm_Travel3_opponentTurn` (67147–67349) and
`frm_Travel3_opponentLevel` (68208–69502).

`H` and `L` mean the richest and poorest non-bankrupt human's stored net worth;
`N` is the current opponent's stored worth; `O1` … `O6` are other opponents'
stored worth. These are snapshots, not cash recalculated during the turn.

## Positive-cash growth

This runs only when cash `C > 0`, after trading and purchases. Below a stated
cash boundary, multiply and round down; at/above it, add the fixed payment.

| Level | Turns | Cash boundary | Below boundary | At/above boundary |
|---|---|---:|---|---:|
| Tutorial | Below 50 | — | No change | No change |
| Tutorial | 50–99 | 10 million | ×1.01 | +100,000 |
| Tutorial | 100+ | 5 million | ×1.02 | +100,000 |
| Novice | Below 50 | 10 million | ×1.01 | +100,000 |
| Novice | 50+ | 5 million | ×1.02 | +100,000 |
| Beginner | Below 50 | 5 million | ×1.02 | +100,000 |
| Beginner | 50+ | 5 million | ×1.03, subject to leading rule | +150,000 |
| Intermediate | Below 50 | 7.5 million | ×1.02, subject to leading rule | +150,000 |
| Intermediate | 50+ | 5 million | ×1.03, subject to leading rule | +150,000 |
| Expert | Any | 5 million | ×1.03, subject to leading rule | +150,000 |
| Master | Any | 6 million | ×1.03, subject to leading rule | +200,000 |

The leading rule replaces multiplication by a flat +100,000 when `N > H`
and the **whole multiplied cash balance**, `C*multiplier`, exceeds 100,000.
The code does not compare just the interest increment to 100,000.

## Signed adjustment

The caller starts invoking `opponentLevel` at turn 3. Its level-specific block
also requires `H > 0` or `turn > 20` for levels 1–4, `turn > 16` for levels
5–6. Before that gate opens the adjustment is zero.

The amount added is `floor(B*M)`, where
`B = floor(rate*shipTons/4)` and rate is 35 for Tutorial/Novice, 30 Beginner,
25 Intermediate, 20 Expert, 15 Master. First draw a base multiplier, then
apply the listed overrides. Overrides **replace**, rather than add to, that
base draw; unused base draws still consume randomness.

Notation `p; +a…b / −c…d` means probability `p` of a positive inclusive integer
draw a…b, otherwise the negative of an inclusive integer draw c…d.

### Base multiplier

| ID | Tutorial (p=1/3) | Novice (p=1/3) | Beginner (p=1/3) | Intermediate (p=1/5) | Expert (p=1/4) | Master (p=1/4) |
|---|---|---|---|---|---|---|
| 1 | +1…18 / −3…22 | +1…18 / −2…22 | +1…16 / −5…18 | +1…18 / −3…19 | +1…20 / −1…19 | +2…20 / −1…18 |
| 2 | +1…16 / −5…20 | +1…18 / −3…20 | +1…16 / −5…18 | +1…18 / −3…19 | +1…20 / −1…19 | +2…20 / −1…18 |
| 3 | +1…14 / −7…20 | +1…16 / −5…20 | +1…15 / −5…18 | +1…16 / −4…19 | +1…18 / −2…19 | +2…18 / −2…18 |
| 4 | +1…12 / −8…20 | +1…14 / −6…20 | +1…14 / −6…18 | +1…14 / −4…19 | +1…16 / −2…19 | +1…18 / −2…18 |
| 5 | +1…18 / −4…20 | +1…20 / −4…20 | +1…18 / −4…18 | +1…18 / −2…18 | +5…20 / −1…16 | +5…20 / −1…15 |
| 6 | +1…18 / −3…20 | +1…20 / −3…20 | +1…18 / −4…18 | +2…18 / −2…18 | +5…20 / −1…16 | +5…20 / −1…15 |

IDs 5/6 get an additional chance to replace this draw at larger winning
targets: Beginner above 20 million, 1/10 for +18…30; Intermediate above
10 million, 1/10 for +18…36; Expert above 10 million, 1/8 for +18…36;
Master above 10 million, 1/8 for +20…40. Later overrides can replace it again.

### Tutorial and Novice overrides

For IDs 1–4, require `N < L`. Use the severe-lag column if `N < fraction*L`;
otherwise use the second column only when `L < H`. If neither applies, keep
the base draw.

| Level | ID | Fraction | Severe lag (p=1/2) | Otherwise, L < H (p=1/3) |
|---|---:|---:|---|---|
| Tutorial | 1 | .60 | +5…18 / −1…12 | +1…18 / −1…12 |
| Tutorial | 2 | .50 | +5…18 / −1…13 | +1…18 / −1…13 |
| Tutorial | 3 | .45 | +3…18 / −1…16 | +1…18 / −1…16 |
| Tutorial | 4 | .40 | +3…18 / −1…18 | +1…18 / −1…18 |
| Novice | 1 | .60 | +5…20 / −1…12 | +1…20 / −1…10 |
| Novice | 2 | .50 | +5…20 / −2…10 | +1…20 / −1…10 |
| Novice | 3 | .45 | +3…20 / −1…15 | +1…20 / −1…15 |
| Novice | 4 | .40 | +3…20 / −1…15 | +1…20 / −1…17 |

For IDs 5/6, require `N < H` instead. Tutorial's severe threshold is `.7*H`;
Novice's is `.75*H`.

| Level | ID | Severe lag (p=1/2) | Otherwise (p=1/3) |
|---|---:|---|---|
| Tutorial | 5 | +1…14 / −4…18 | +1…18 / −4…20 |
| Tutorial | 6 | +1…16 / −3…18 | +1…18 / −3…20 |
| Novice | 5 | +1…18 / −2…18 | +1…18 / −4…20 |
| Novice | 6 | +1…16 / −3…18 | +1…18 / −3…20 |

### Beginner overrides

Only IDs 1–4, and only when `N < H`. Test columns left to right; the first
matching condition replaces the base. `L < H` is required for columns B/C
and also for D for ID 3 only.

| ID | A: condition → p=3/4 draw | B: condition → p=1/2 draw | C: condition → p=1/2 draw | D: condition → p=2/3 draw |
|---|---|---|---|---|
| 1 | N < .8*O6 → +4…19 / −0…18 | N < .85*L → +10…20 / −1…12 | N < L → +10…18 / −1…10 | N < .85*H → +10…18 / −1…18 |
| 2 | N < .8*O5 → +3…19 / −0…18 | N < .8*L → +10…20 / −1…12 | N < L → +8…16 / −1…10 | N < .8*H → +10…18 / −1…18 |
| 3 | N < .8*O1 → +2…19 / −0…18 | N < .75*L → +1…20 / −1…12 | N < L → +1…18 / −1…10 | N < .75*H → +10…18 / −1…18 |
| 4 | N < .7*O2 → +2…19 / −0…18 | N < .65*L → +1…20 / −1…12 | N < L → +1…18 / −1…10 | N < .65*H → +10…18 / −1…18 |

### Intermediate, Expert and Master overrides

Only IDs 1–4. Intermediate also requires `N < H`; Expert/Master do not.
Test the opponent-relative condition first, then the human-relative one.
Every loss draw is −0…18; positive ranges and probabilities are below.

| Level | ID | Opponent-relative condition | Positive range / probability | Human-relative condition | Positive range / probability |
|---|---:|---|---|---|---|
| Intermediate | 1 | N < .8*O6 | 4…20 / 3/4 | N < .9*H | 1…20 / 3/4 |
| Intermediate | 2 | N < .8*O5 | 4…20 / 3/4 | N < .8*H | 1…20 / 3/4 |
| Intermediate | 3 | N < .7*O1 | 3…20 / 3/4 | N < .7*H | 1…20 / 3/4 |
| Intermediate | 4 | N < .7*O2 | 3…20 / 3/4 | N < .7*H | 1…20 / 2/3 |
| Expert | 1 | N < .8*O6 | 1…20 / 3/4 | N < .9*H | 1…20 / 3/4 |
| Expert | 2 | N < .8*O5 | 1…20 / 3/4 | N < .8*H | 1…20 / 3/4 |
| Expert | 3 | N < .8*O1 | 1…20 / 3/4 | N < .7*H | 1…20 / 3/4 |
| Expert | 4 | N < .8*O2 | 1…20 / 3/4 | N < .7*H | 1…20 / 2/3 |
| Master | 1 | N < .85*O6 | 1…20 / 3/4 | N < .9*H | 1…20 / 3/4 |
| Master | 2 | N < .85*O5 | 1…20 / 3/4 | N < .8*H | 1…20 / 3/4 |
| Master | 3 | N < .75*O1 | 1…20 / 3/4 | N < .6*H | 1…20 / 3/4 |
| Master | 4 | N < .75*O2 | 1…20 / 3/4 | N < .7*H | 1…20 / 2/3 |

These are literal comparisons, including when worth is negative. Reading a
fractional threshold as “percentage behind” can be misleading below zero.
