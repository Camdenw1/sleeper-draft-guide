# Sleeper draft guide — 2026

A draft board for a 12-team half-PPR league with a TE premium and 100/200-yard
bonuses. Rankings blend a projection model rescored for this exact scoring with
four public ranking systems and the betting market.

```
draft-board-2026.html   presentation — hand-edited, never overwritten
board-data.js           generated — overwritten every refresh
rankings.csv            generated — same data, spreadsheet form
CLAUDE.md               project context for Claude Code
REFRESH.md              runbook: "Read REFRESH.md and do a full refresh"
refresh/                inputs + build chain
```

## Use

Open `draft-board-2026.html` in any browser. Tap a row to cross a player off;
state persists in localStorage so closing the tab mid-draft is safe. "Reset board"
clears it. Filter by position to switch the tier bands from overall to positional.

## Rebuild

```bash
python3 refresh/build.py
```

Takes about ten seconds. Fetches the four public ranking sources live, then aborts
rather than overwriting if the pipeline produces fewer than 150 players. Fetched
ranks are cached for six hours in `refresh/pubranks_cache.json` (gitignored), and
any source that fails to fetch falls back to that cache — so a draft-day rebuild
still works if someone's API is down or the wifi isn't cooperating.

## Columns

| | |
|---|---|
| **#** | blended rank — half model, half public consensus, nudged by market |
| **FFC / ESPN / Sleeper / Yahoo** | each public system's rank, densely re-ranked to one slot per player |
| **Where they land** | the four systems plotted against their own average |
| **Model** | the unblended projection view |
| **Gap** | public average minus blended rank; positive means he should fall to you |
| **Market** | −10 to +10; prop line vs projection, or team win total as fallback |
| **Scoring fit** | −10 to +10; how much this league's quirks help or hurt him |

Badges: **SLEEPER** = 25+ slots later on Sleeper than he ranks here, outside the
top 75. **VALUE** = 18+ slots of edge. **FADE** = 18+ the other way.

Full methodology is behind the "How this works" button on the board itself.

## Refresh schedule

Aug 28 and Sept 8. Draft is Sept 9.

## Data sources

All rankings come from free, public, no-auth endpoints, fetched at build time by
`refresh/sources.py`. Nothing here is scraped from behind a paywall.

| Source | What it gives | Endpoint |
|---|---|---|
| [Fantasy Football Calculator](https://fantasyfootballcalculator.com) | Real **half-PPR, 12-team ADP** from thousands of public mock drafts — the only source whose format matches this league exactly, so it anchors the blend | `/api/v1/adp/half-ppr` |
| ESPN | Public fantasy draft-rank board | `lm-api-reads.fantasy.espn.com` |
| Sleeper | Public player dump, draft-room ordering | `api.sleeper.app/v1/players/nfl` |
| Yahoo | Public draft-analysis average pick | `pub-api-ro.fantasysports.yahoo.com` |

Season stat projections and the betting-market layer are point-in-time snapshots
in `refresh/players.py` and `refresh/market.py`. Green/red flag notes are
hand-written. Coverage is uneven by design: a player unranked by one source shows
`NR` and is simply excluded from that player's average, and Sleeper covers the
full pool so every player keeps at least one column.

## Built with Claude

This project is developed with [Claude Code](https://claude.com/claude-code).
The architecture split that makes it work — generated data in `board-data.js`,
hand-tuned presentation in `draft-board-2026.html`, never regenerated from a
template — exists so that Claude can refresh the numbers without touching the
design, and rework the design without touching the pipeline. `CLAUDE.md` is the
context file that keeps that boundary intact across sessions.
