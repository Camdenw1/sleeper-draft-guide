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

# ---- availability safety net ------------------------------------------------
# `avail` is hand-set judgement and stays that way -- but "this player is on IR"
# is a FACT the feed reports, not a judgement, and a stale 1.00 against it used to
# hard-abort the build. That is right for a human at a keyboard and wrong for a
# daily job: the refresh stalled for two days in September 2026 because Isiah
# Pacheco went on IR and nobody was there to unblock it.
#
# So a feed-confirmed inactive status now CAPS avail automatically. The cap only
# ever lowers a value, so every deliberate number Camden has set -- Benson at
# 0.00, Conner at 0.70 -- survives untouched. Only a stale 1.00 gets clamped, and
# it is reported loudly so the real number can be set deliberately later.
AVAIL_CAP = {"IR": 0.35, "PUP": 0.35, "NA": 0.35, "DNR": 0.35, "Sus": 0.35,
             "Out": 0.60, "Doubtful": 0.75}
_CAPPED = []


# Anything below this has clearly been looked at by a human, so leave it alone.
# Only an essentially untouched 1.00 counts as stale.
UNTOUCHED = 0.95


def capped_avail(name, av):
    if av < UNTOUCHED:          # a considered number -- never override it
        return av
    st = (R.INJ_N.get(R.norm(name)) or {}).get("status")
    cap = AVAIL_CAP.get(st)
    if cap is not None and av > cap:
        _CAPPED.append((name, st, av, cap))
        return cap
    return av


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
        # Zero is a real projection, not missing data. Dropping it inflated
        # peripheral roles (a feed projecting 0 rush TDs used to disappear
        # beside another feed projecting 1). Missing fields are already
        # excluded by the comprehension above.
        out[f] = sum(vals) / len(vals) if vals else 0.0
    NSRC[name] = len(lines)
    STATS[name] = out
    return out


# ---- rebuild players.py's tables with consensus numbers ---------------------
QB, RB, WR, TE = [], [], [], []

for n, tm, a, py, ptd, ry, rtd, av in P.QB:
    b = _blend(n, {"passYd": py, "passTD": ptd, "ruYd": ry, "ruTD": rtd})
    QB.append((n, tm, a, b["passYd"], b["passTD"], b["ruYd"], b["ruTD"], capped_avail(n, av)))

for n, tm, a, ra, ry, rtd, rc, red, retd, av in P.RB:
    b = _blend(n, {"ruAtt": ra, "ruYd": ry, "ruTD": rtd,
                   "rec": rc, "reYd": red, "reTD": retd})
    RB.append((n, tm, a, b["ruAtt"] or ra, b["ruYd"], b["ruTD"],
               b["rec"], b["reYd"], b["reTD"], capped_avail(n, av)))

for n, tm, a, rc, red, retd, ra, ry, rtd, av in P.WR:
    b = _blend(n, {"rec": rc, "reYd": red, "reTD": retd,
                   "ruAtt": ra, "ruYd": ry, "ruTD": rtd})
    WR.append((n, tm, a, b["rec"], b["reYd"], b["reTD"],
               b["ruAtt"] or ra, b["ruYd"], b["ruTD"], capped_avail(n, av)))

for n, tm, a, rc, red, retd, av in P.TE:
    b = _blend(n, {"rec": rc, "reYd": red, "reTD": retd})
    TE.append((n, tm, a, b["rec"], b["reYd"], b["reTD"], capped_avail(n, av)))

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
    if _CAPPED:
        print(f"  {len(_CAPPED)} availability caps applied from the live injury feed:")
        for n, st, was, now in _CAPPED:
            print(f"    {n:24} {st:9} avail {was} -> {now}  (set it deliberately in players.py)")
    if _SKIPPED:
        print(f"  {len(_SKIPPED)} source-lines skipped on role disagreement:")
        for n, t, why in _SKIPPED[:8]:
            print(f"    {n:24} {t:8} {why}")


if __name__ == "__main__":
    report()
