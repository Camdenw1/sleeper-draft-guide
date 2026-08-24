"""Quantify how much THIS league's quirks help each player.

  - 100-199 / 200+ yard rushing & receiving games: +3 / +4, EXCLUSIVE tiers
    (a 210-yard game pays 4, not 7 -- confirmed against the league scoring page)
  - 300-399 / 400+ yard passing games: +3 / +4, same exclusive structure
  - 0.75 per reception for TE (0.25 above the 0.5 baseline)

Bonuses reward BIG GAMES, so this needs the per-game distribution, not season
averages: a bonus is a step function and E[bonus] != bonus(E[yards]). Yardage is
built up from individual carries and catches (heavy-tailed lognormal per touch),
so the long-play tail is generated rather than assumed.

The sampling primitives below used to live in model.py, which also carried a full
simulation under a DIFFERENT league's bucketed scoring -- ~7s per build, output
discarded. They were moved here and model.py deleted.
"""
import json
import numpy as np
import players as P

RNG = np.random.default_rng(20260823)
N = 40000


def touches(mean, disp=6.0):
    """Negative-binomial touch counts -- overdispersed relative to Poisson."""
    if mean <= 0:
        return np.zeros(N, int)
    return RNG.negative_binomial(disp, disp / (disp + mean), N)


def per_touch_yards(counts, ypt, sigma, shift=0.0):
    """Sum lognormal per-touch yardage, so the long-play tail is generated."""
    total = np.zeros(N)
    if ypt <= 0 or counts.size == 0 or counts.max() == 0:
        return total
    mu = np.log(ypt + shift) - sigma ** 2 / 2
    for k in range(int(counts.max())):
        total += np.where(counts > k, np.exp(RNG.normal(mu, sigma, N)) - shift, 0.0)
    return total


def script(cv):
    """Game-script multiplier: blowouts and shootouts move volume around."""
    k = 1.0 / cv ** 2
    return RNG.gamma(k, 1.0 / k, N)


def yd_bonus(y, lo=100, hi=200, lo_pts=3, hi_pts=4):
    """Exclusive tiers: hi_pts at or above hi, else lo_pts at or above lo."""
    return np.where(y >= hi, hi_pts, np.where(y >= lo, lo_pts, 0))


out = {}


def rec_rush_bonus(att, ypc, rc, ypr, is_te=False, avail=1.0):
    g = script(0.28)
    ry = (per_touch_yards((touches(att / 17.0, 8.0) * g).round().astype(int), ypc, 0.85, 2.0)
          if att > 0 else np.zeros(N))
    cy = per_touch_yards(touches(rc / 17.0, 4.5), ypr, 0.80) if rc > 0 else np.zeros(N)
    b = yd_bonus(ry) + yd_bonus(cy)
    te = 0.25 * rc if is_te else 0.0          # season-long TE reception premium
    return float(b.mean()) * 17 * avail + te * avail


for n,tm,adp,py,ptd,ry,rtd,av in P.QB:
    g = script(0.20)
    pyg = RNG.gamma(16.0, (py / 17.0) / 16.0, N) * g
    rg  = RNG.gamma(2.2, (ry / 17.0) / 2.2, N) * np.sqrt(g) if ry > 0 else np.zeros(N)
    b = yd_bonus(pyg, 300, 400) + yd_bonus(rg)
    out[n] = float(b.mean()) * 17 * av

for n,tm,adp,ra,ryd,rtd,rc,red,retd,av in P.RB:
    out[n] = rec_rush_bonus(ra, ryd / max(ra, 1), rc, red / max(rc, 1), False, av)

for n,tm,adp,rc,red,retd,ra,ryd,rtd,av in P.WR:
    out[n] = rec_rush_bonus(ra, ryd / max(ra, 1) if ra else 0, rc, red / max(rc, 1), False, av)

for n,tm,adp,rc,red,retd,av in P.TE:
    out[n] = rec_rush_bonus(0, 0, rc, red / max(rc, 1), True, av)

# K and DST earn no per-game yardage bonuses; their scoring is fully handled in
# score.py. They still need keys so the blend can find them.
for n,tm,a,fgm,fga,xpm,leg in P.K:
    out[n] = 0.0
for n,tm,a,sk,fr,it,dtd,pa,saf,ktd in P.DST:
    out[f"{tm} {n}"] = 0.0

json.dump(out, open("bonus_pts.json", "w"))
top = sorted(out.items(), key=lambda x: -x[1])
print("MOST HELPED BY THIS LEAGUE'S QUIRKS (bonus pts/season)")
for k, v in top[:16]:
    print(f"  {k:24} {v:6.1f}")
