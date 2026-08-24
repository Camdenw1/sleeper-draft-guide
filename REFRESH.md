# Refresh runbook

Paste into Claude Code as: **"Read REFRESH.md and do a full refresh."**

Run this twice: **Aug 28** and **Sept 8** (the day before the draft).

---

## Rule zero

Edit files in `refresh/` only. **Never edit `draft-board-2026.html` during a refresh** —
that file is hand-tuned presentation and the whole architecture exists to protect it.
`board-data.js` and `rankings.csv` are generated; overwrite them freely.

## 1. Re-pull the inputs

**`refresh/players.py`** — season stat projections and `avail`
- `avail` is the share of the 17-game season the player is expected to be available
  (1.00 = full). Lower it for new injuries; raise it when someone is cleared.
- Check: training-camp and preseason injury reports, IR moves, roster cuts,
  suspensions, depth-chart changes. Delete anyone out for the year.
- Source used originally: FFToday consensus projections.

**`refresh/hp_data.py`** — the player pool and the green/red flags
- The `sl`/`es`/`fpros`/`cons` numeric columns are **no longer read** by the build;
  rankings are fetched live now. The columns that still matter are the player list
  itself (name, team, pos) and the two flag strings.
- Rewrite any flag that has gone stale. A red flag saying "groin injury, missing
  preseason" is wrong once he's playing. This is the part that decays fastest and
  the part most worth your attention.

**`refresh/sources.py`** — the four public ranking feeds
- Nothing to paste. FFC, ESPN, Sleeper and Yahoo are fetched at build time.
- Cached six hours in `pubranks_cache.json`; force a pull with
  `python3 refresh/sources.py --refresh`.
- If a source fails it falls back to cache and says so in the build output. **If a
  source printed FETCH FAILED, say so in the report** — a stale column silently
  dragging the average is exactly the kind of thing to surface, not bury.
- Don't add paid or paywalled rankings here. The repo is public.

**`refresh/market.py`** — betting layer
- `WIN`: team win totals, all 32.
- `PROPS`: season-long over/unders. Only ~30 were free last time. Add any new ones
  found — each real prop is worth far more than a win-total proxy.
- `AWARDS`: MVP / OPOY / ORoY / CPOY favourites.

## 2. Rebuild

```bash
python3 refresh/build.py
```

Runs scoring → bonus simulation → blending → writes `board-data.js` and `rankings.csv`.
It aborts rather than overwriting if fewer than 150 players survive, so a broken
input can't silently wipe the board. Takes about a minute (the bonus step is a
40,000-game Monte Carlo per player).

## 3. Verify

- `board-data.js` has a fresh `BOARD_META.generated` date and ~190+ players
- Open `draft-board-2026.html`, confirm it renders and rows still cross off
- Spot-check two or three players whose news you just changed

## 4. Report

Only the delta. Don't restate the board.
- Players who moved 10+ slots, and why
- New or dropped SLEEPER / VALUE / FADE badges
- Availability changes
- Any source that couldn't be reached

---

## Locked unless Camden says otherwise

- **Scoring:** half PPR · 0.75 per catch for TE · +3 at 100 rush/rec yards,
  +2 more at 200 · +3 at 300 and +2 at 400 passing · no other bonuses
- **Roster:** 12 teams — QB, 2RB, 2WR, TE, RB/WR/TE flex, WR/TE flex, K, DST, 6 bench
- **Blend** (`refresh/board.py`): 50% projection model, 50% public consensus, then a
  market nudge — 13% weight where a real prop exists, 6% where it's only a win total
- **Replacement level** is computed endogenously by filling every starting slot in
  the league first. Don't hardcode it.
