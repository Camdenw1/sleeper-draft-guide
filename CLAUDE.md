# Project context

Fantasy football draft board for a 12-team half-PPR league with a tight-end premium
and yardage bonuses. Camden opens `draft-board-2026.html` in a browser during his
draft on **Sept 9, 2026**.

## Architecture — the one thing to understand

`draft-board-2026.html` is **presentation**, hand-tuned, and loads `board-data.js`
as a sibling `<script>`. `board-data.js` is **generated**. The split exists so data
refreshes never clobber UI work, and UI work never has to touch the pipeline.

- Changing how the board *looks or behaves* → edit the HTML
- Changing *what the numbers say* → edit `refresh/*.py`, then `python3 refresh/build.py`
- Never regenerate the HTML from a template. There isn't one anymore. It's the source.

## Pipeline

`refresh/build.py` chains three steps and writes `board-data.js` + `rankings.csv`:

1. `score.py` → rescores season projections for this league's scoring
2. `fit.py` → Monte Carlo (40k games/player) for the 100/200-yard bonuses, since a
   bonus is a step function and E[bonus] ≠ bonus(E[yards])
3. `board.py` (which execs `blend.py`) → VOR against endogenous replacement level,
   blends model with public consensus, applies the market layer, assigns tiers and tags

Data modules: `players.py` (projections + availability), `hp_data.py` (player pool
+ hand-written green/red flags), `sources.py` (fetches four free public ranking
sources live: FFC half-PPR ADP, ESPN, Sleeper, Yahoo — cached 6h, falls back to
cache on failure), `ranks.py` (normalizes those into joinable columns),
`market.py` (win totals, props, award odds).

The paid sources this project started with — FantasyPros ECR and a Flock Fantasy
export — were removed when the repo went public. Don't reintroduce paid or
paywalled rankings; `sources.py` is the place to add a new free one.

## League rules — don't change these without being asked

Half PPR · **0.75 per catch for TE** (0.5 baseline + 0.25 premium) · INT **-2** ·
yardage bonuses are **exclusive tiers**: **+3 for 100-199 rush/rec, +4 for 200+**;
+3 for 300-399 pass, +4 for 400+ · kickers use **normal** fantasy scoring (3 under
40, 4 from 40-49, 5 from 50+, PAT 1, miss -1) · DST
points-allowed tiers 0 / 1-6 / 7-13 / 14-20 / 21-27 / 28-34 / 35+ pay
+10 / +7 / +4 / +1 / 0 / -1 / -4 · 12 teams · QB, 2RB, 2WR, TE, RB/WR/TE flex,
WR/TE flex, K, DST, 6 bench.

Verified against the league's scoring page on 24 Aug 2026. Fumble lost (-2) and
2-pt conversions are NOT modelled -- players.py carries no fumble or 2-pt data.

The scoring page currently shows kicker FG buckets of 1/2/3/4/5/6 plus a 0.10
per-yard bonus, which would make a 45-yarder worth 8.5 and put a kicker around
pick 50. Camden confirmed on 24 Aug 2026 that this is a league setup error being
fixed, so score.py models normal kicker scoring instead. **Don't "correct" it back
to match the page** without asking -- that mismatch is deliberate.

## Known limitations — worth stating rather than papering over

- No role-change modelling. A backup is valued at projected volume, not the volume
  he'd get if the starter went down. Handcuffs are undervalued by construction.
- Projections come from one source, which is why the rank is blended 50/50 with
  public consensus rather than trusting the model outright.
- Season-long props were free for only ~30 players; the rest of the market column
  is a team win-total proxy and carries half the weight.
- Deep bench players are smoothed across 17 games rather than modelled as spiky.

## Next build

Sleeper live-draft sync. The league is on Sleeper, whose API is public and needs no
auth: `GET https://api.sleeper.app/v1/draft/{draft_id}/picks` returns every pick.
Poll it and cross players off automatically instead of tapping rows. Roughly an
hour of work and the highest-value thing left.
