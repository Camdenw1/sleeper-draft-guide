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

0. `proj.py` → builds CONSENSUS season projections: the hand-entered baseline in
   `players.py` averaged with ESPN's and Sleeper's own season projections. Keeps
   the pool and `avail` from players.py; a feed whose line implies a different
   role for a player is rejected rather than averaged in.
1. `score.py` → rescores those projections for this league's scoring
2. `fit.py` → Monte Carlo (40k games/player) for the 100/200-yard bonuses, since a
   bonus is a step function and E[bonus] ≠ bonus(E[yards])
3. `board.py` (which execs `blend.py`) → VOR against endogenous replacement level,
   blends model with public consensus, assigns tiers and tags

Data modules: `players.py` (projections + availability), `hp_data.py` (player pool
+ hand-written green/red flags), `sources.py` (fetches three free public **ADP**
feeds live — FFC half-PPR 12-team, ESPN, Yahoo — cached 6h, falls back to cache
per-source on failure), `ranks.py` (normalizes those into joinable columns),
`market.py` (award odds only — see below).

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

Verified against the league's scoring page on 24 Aug 2026. Fumble lost (-2) IS
now modelled: Sleeper's projections carry `fum_lost` (102 players). Interceptions
come from the feeds too, replacing the hand-kept QBINT table. 2-pt conversions
remain unmodelled -- no source projects them.

The scoring page currently shows kicker FG buckets of 1/2/3/4/5/6 plus a 0.10
per-yard bonus, which would make a 45-yarder worth 8.5 and put a kicker around
pick 50. Camden confirmed on 24 Aug 2026 that this is a league setup error being
fixed, so score.py models normal kicker scoring instead. **Don't "correct" it back
to match the page** without asking -- that mismatch is deliberate.

## Draft-reality overrides — deliberate, don't "fix" them

- **K and DST are floored** (`FLOOR` in blend.py, enforced by order in board.py):
  no DST before pick 120, no K before pick 140. Their VOR is real but not
  actionable — one starter each, both streamable, neither predictable. Unfloored,
  a defense sorted to pick 71.
- The **Value coming up** panel caps at two per position and only shows players in
  range of the next pick. Uncapped it is entirely tight ends, because the 0.75
  premium means every TE beats public ADP. True, but not a draft strategy.

## Ranking sources — market data only, no editorial boards. Keep it that way.

Weighted **2 / 1.5 / 1 / 1** (FFC / FantasyCalc / Yahoo / ESPN) in `SRCW` in
blend.py, not averaged flat. The two format-exact sources lead:

- **FFC** — real half-PPR 12-team ADP from thousands of mock drafts. The anchor.
- **FantasyCalc** — market value at `ppr=0.5&numQbs=1&numTeams=12`, i.e. exactly
  this league. Value rather than ADP, so it reads the same question from a
  different direction. Also carries `sleeperId` and a 30-day value trend.
- **Yahoo** / **ESPN** — real ADP from their own drafts. ESPN must read
  `ownership.averageDraftPosition`, **not** `draftRanksByRankType` — that board's
  STANDARD and PPR variants are byte-identical and carry no format information.

## Injuries — live, and they audit players.py

`fetch_injuries` in sources.py reads Sleeper's player dump (already downloaded)
for `injury_status`, body part and roster status. Badges render on the board;
IR/PUP/Out/Doubtful/Sus players are struck through and excluded from the value
panel.

**build.py prints a LIVE INJURY vs avail block** whenever the feed says a player
is IR/PUP/Out but `players.py` still values him at `avail=1.00`. That is how the
Charbonnet (PUP, torn ACL, valued fully healthy) hole was found. Don't silence it
— fix `avail`, or accept it deliberately.

Two sources were tested and rejected. Don't re-add either without new evidence:

- **Sleeper** publishes no ADP anywhere. `search_rank` is search popularity, and
  their GraphQL has no adp field (every draft query needs a `draft_id`). Sleeper
  is still fetched, but only for the trending/HOT signal.
- **MyFantasyLeague** has a real public ADP endpoint and no way to exclude
  superflex drafts, which its pool is full of. Measured against FFC on this board,
  MFL's QBs ran 38 slots earlier (Josh Allen 3rd overall vs FFC's 33rd) while RBs
  and WRs ran 7 and 20 later. `IS_PPR` filters scoring, not roster format.
  `fetch_mfl` is kept in sources.py, unused, recording exactly this.

## Removed on purpose — don't restore without asking

- **The betting layer.** Win totals and season props used to nudge the final sort.
  Measured on this board it moved skill players a mean of **1.8 slots** (max 11),
  which did not justify a column or the explanation it needed. `market.py` still
  holds `WIN` and `PROPS` if it is ever wanted back; only `AWARDS` is used now,
  for the small odds badge next to a name.
- **The "scoring fit" column.** It was **display-only** — it never entered the
  ranking. The league's quirks are already priced into `tot` through the yardage
  bonuses and the TE premium, so the column was decoration.

## Known limitations — worth stating rather than papering over

- No role-change modelling. A backup is valued at projected volume, not the volume
  he'd get if the starter went down. Handcuffs are undervalued by construction.
- Projections are now a 3-source consensus (players.py + ESPN + Sleeper), 219 of
  220 players carrying 2+ sources. The 50/50 blend with public consensus stays,
  but the single-source risk that motivated it is much reduced.
- `avail` is still hand-set in players.py — it is injury *judgement*, not a stat
  projection. build.py audits it against the live injury feed on every run.
- Season-long props were free for only ~30 players; the rest of the market column
  is a team win-total proxy and carries half the weight.
- Deep bench players are smoothed across 17 games rather than modelled as spiky.

## Next build

Sleeper live-draft sync. The league is on Sleeper, whose API is public and needs no
auth: `GET https://api.sleeper.app/v1/draft/{draft_id}/picks` returns every pick.
Poll it and cross players off automatically instead of tapping rows. Roughly an
hour of work and the highest-value thing left.
