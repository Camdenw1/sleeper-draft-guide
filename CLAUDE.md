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

Data modules: `players.py` (projections + availability), `hp_data.py` (Sleeper/ESPN
ADP + green/red flags), `ranks.py` (FantasyPros ECR + tiers, Flock), `market.py`
(win totals, props, award odds).

## League rules — don't change these without being asked

Half PPR · **0.75 per catch for TE** (0.5 baseline + 0.25 premium) · **+3 at 100
rush/rec yards, +2 more at 200** · +3 at 300 and +2 at 400 passing · 12 teams ·
QB, 2RB, 2WR, TE, RB/WR/TE flex, WR/TE flex, K, DST, 6 bench.

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
