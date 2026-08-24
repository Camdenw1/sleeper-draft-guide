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

Takes about a minute. Aborts rather than overwriting if the pipeline produces
fewer than 150 players.

## Columns

| | |
|---|---|
| **#** | blended rank — half model, half public consensus, nudged by market |
| **Sleeper / ESPN / FPros / Flock** | each system's rank, one forced slot per player |
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
