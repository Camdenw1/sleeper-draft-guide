"""Consensus season projections: our baseline plus ESPN plus Sleeper.

WHY THIS EXISTS
The board used to run on ONE hand-entered projection set. It was the largest
weakness in the model -- every ranking inherited its errors, and there was no way
to tell a real edge from a data-entry opinion. It also carried INTEGER touchdown
counts: 28 players sat at exactly 7 receiving TDs, 28 more at exactly 3. A TD is
6 points, so that rounding alone moved players several slots.

Two free feeds fix both problems (see sources.py):
  espnproj     ESPN's own season projections. Fractional, 99% pool coverage.
  sleeperproj  Sleeper's, natively half-PPR scored, and the only source carrying
               fum_lost -- the -2 this league charges for a lost fumble, which
               the board previously could not model at all.

This module averages whatever is available per player and exposes tables in
exactly the shape players.py used, so score.py and fit.py consume it unchanged.

WHAT STAYS FROM players.py
  - the player POOL. These feeds do not get to add or remove players.
  - `avail`, the hand-set share of the season a player is expected to be up for.
    It is judgement about injury risk, not a stat projection, and build.py audits
    it against the live injury feed.
  - K and DST, which neither feed projects usefully.
"""
import players as P
import ranks as R
import sources

_D, _N, _X = sources.load(quiet=True)
ESPN = {R.norm(k): v for k, v in _X.get("espnproj", {}).items()}
SLP  = {R.norm(k): v for k, v in _X.get("sleeperproj", {}).items()}

FIELDS = ("passYd", "passTD", "int", "ruAtt", "ruYd", "ruTD",
          "rec", "reYd", "reTD", "fumLost")
STATS = {}          # name -> consensus line
NSRC = {}           # name -> how many sources agreed on him
_SKIPPED = []       # (name, source, reason) for the build report


def _sane(ours, theirs):
    """Reject a source that clearly has a different player in mind.

    A feed listing a projected starter as a deep backup (or the reverse) is a role
    disagreement, not a better estimate, and averaging it in would quietly halve a
    real player. Compared on total yards, which is the stable part of a line.
    """
    a = ours.get("ruYd", 0) + ours.get("reYd", 0) + 0.25 * ours.get("passYd", 0)
    b = theirs.get("ruYd", 0) + theirs.get("reYd", 0) + 0.25 * theirs.get("passYd", 0)
    if a < 150 or b < 150:          # deep bench either way; nothing to protect
        return True
    return 0.4 <= (b / a) <= 2.5


def _blend(name, ours):
    """Average our line with whatever feeds have a sane read on the same player."""
    nn = R.norm(name)
    lines = [ours]
    for tag, src in (("espn", ESPN), ("sleeper", SLP)):
        t = src.get(nn)
        if not t:
            continue
        if not _sane(ours, t):
            _SKIPPED.append((name, tag, "role disagreement"))
            continue
        lines.append(t)
    out = {}
    for f in FIELDS:
        vals = [l[f] for l in lines if l.get(f) is not None and (f in l)]
        vals = [v for v in vals if v or f in ("int", "fumLost")]
        out[f] = sum(vals) / len(vals) if vals else 0.0
    NSRC[name] = len(lines)
    STATS[name] = out
    return out


# ---- rebuild players.py's tables with consensus numbers ---------------------
QB, RB, WR, TE = [], [], [], []

for n, tm, a, py, ptd, ry, rtd, av in P.QB:
    b = _blend(n, {"passYd": py, "passTD": ptd, "ruYd": ry, "ruTD": rtd})
    QB.append((n, tm, a, b["passYd"], b["passTD"], b["ruYd"], b["ruTD"], av))

for n, tm, a, ra, ry, rtd, rc, red, retd, av in P.RB:
    b = _blend(n, {"ruAtt": ra, "ruYd": ry, "ruTD": rtd,
                   "rec": rc, "reYd": red, "reTD": retd})
    RB.append((n, tm, a, b["ruAtt"] or ra, b["ruYd"], b["ruTD"],
               b["rec"], b["reYd"], b["reTD"], av))

for n, tm, a, rc, red, retd, ra, ry, rtd, av in P.WR:
    b = _blend(n, {"rec": rc, "reYd": red, "reTD": retd,
                   "ruAtt": ra, "ruYd": ry, "ruTD": rtd})
    WR.append((n, tm, a, b["rec"], b["reYd"], b["reTD"],
               b["ruAtt"] or ra, b["ruYd"], b["ruTD"], av))

for n, tm, a, rc, red, retd, av in P.TE:
    b = _blend(n, {"rec": rc, "reYd": red, "reTD": retd})
    TE.append((n, tm, a, b["rec"], b["reYd"], b["reTD"], av))

K, DST = P.K, P.DST          # neither feed projects these usefully

# Interceptions and lost fumbles now come from the feeds rather than a hand table.
INT = {n: STATS[n]["int"] for n, *_ in P.QB if STATS.get(n, {}).get("int")}
FUM = {n: v["fumLost"] for n, v in STATS.items() if v.get("fumLost")}


def report():
    multi = sum(1 for v in NSRC.values() if v > 1)
    print(f"projections: {multi}/{len(NSRC)} players have 2+ sources"
          f" (espn {len(ESPN)}, sleeper {len(SLP)})")
    print(f"  interceptions projected for {len(INT)} QBs,"
          f" lost fumbles for {len(FUM)} players")
    if _SKIPPED:
        print(f"  {len(_SKIPPED)} source-lines skipped on role disagreement:")
        for n, t, why in _SKIPPED[:8]:
            print(f"    {n:24} {t:8} {why}")


if __name__ == "__main__":
    report()
