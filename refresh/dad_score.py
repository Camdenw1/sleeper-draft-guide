"""Score projections for Dad's unusual weekly-bucket league.

The source projections are season totals, while this league awards points from
per-game yardage and reception buckets. We therefore simulate one representative
game per player and multiply its expected score by 17. Touchdown *distance* is
not projected by any input feed, so TD points use documented league-average
distance distributions rather than pretending every TD is worth one fixed rule
bucket. Two-point conversions remain unmodelled, as in the main profile.
"""
import json

import numpy as np

import proj as P

RNG = np.random.default_rng(20260827)
N = 40000


def touches(mean, disp=6.0):
    if mean <= 0:
        return np.zeros(N, int)
    return RNG.negative_binomial(disp, disp / (disp + mean), N)


def per_touch_yards(counts, ypt, sigma, shift=0.0):
    total = np.zeros(N)
    if ypt <= 0 or counts.size == 0 or counts.max() == 0:
        return total
    mu = np.log(ypt + shift) - sigma ** 2 / 2
    for k in range(int(counts.max())):
        total += np.where(counts > k, np.exp(RNG.normal(mu, sigma, N)) - shift, 0.0)
    return total


def script(cv):
    k = 1.0 / cv ** 2
    return RNG.gamma(k, 1.0 / k, N)


def bucket(values, step, cap):
    """One point per full step, capped at the league's top bucket."""
    return np.minimum(np.floor(np.maximum(values, 0) / step), cap)


def reception_bucket(counts, pos):
    # RB/TE: 3-4=1, 5-6=2 ... 19+=9. WR starts two catches later.
    start = 3 if pos in ("RB", "TE") else 5
    return np.where(counts >= start,
                    np.minimum(((counts - start) // 2) + 1, 9), 0)


# Approximate league-wide TD-distance distributions. Rushing scores are much
# more concentrated near the goal line than passing/receiving scores. The rule
# gives passing and receiving TDs the same points by distance.
PASS_DIST = np.array([.28, .18, .20, .12, .08, .05, .04, .025, .015, .007, .003])
RUSH_DIST = np.array([.58, .16, .12, .055, .03, .02, .014, .009, .005, .004, .003])
PASS_TD_VALUE = np.array([3, 3, 4, 4, 5, 5, 6, 6, 7, 8, 9], dtype=float)
RUSH_TD_VALUE = np.array([4, 4, 5, 5, 6, 6, 7, 7, 8, 9, 10], dtype=float)
PASS_TD_EV = float(PASS_DIST @ PASS_TD_VALUE)
RUSH_TD_EV = float(RUSH_DIST @ RUSH_TD_VALUE)


def skill_game(att, rush_yards, receptions, rec_yards, pos):
    g = script(0.28)
    rush_counts = (touches(att / 17.0, 8.0) * g).round().astype(int)
    rec_counts = touches(receptions / 17.0, 4.5)
    ryg = per_touch_yards(rush_counts, rush_yards / max(att, 1), 0.85, 2.0)
    cyg = per_touch_yards(rec_counts, rec_yards / max(receptions, 1), 0.80)
    yards = float((bucket(ryg, 25, 9) + bucket(cyg, 20, 10)).mean()) * 17
    catches = float(reception_bucket(rec_counts, pos).mean()) * 17
    return yards, catches


scores = {}


def save(name, yards=0.0, receptions=0.0, touchdowns=0.0, other=0.0, avail=1.0):
    parts = {
        "yard_buckets": yards * avail,
        "reception_buckets": receptions * avail,
        "touchdown_distance": touchdowns * avail,
        "other": other * avail,
    }
    parts["total"] = sum(parts.values())
    scores[name] = {k: round(v, 3) for k, v in parts.items()}


for n, tm, adp, py, ptd, ry, rtd, avail in P.QB:
    g = script(0.20)
    pyg = RNG.gamma(16.0, (py / 17.0) / 16.0, N) * g
    ryg = (RNG.gamma(2.2, (ry / 17.0) / 2.2, N) * np.sqrt(g)
           if ry > 0 else np.zeros(N))
    yards = float((bucket(pyg, 75, 7) + bucket(ryg, 25, 9)).mean()) * 17
    save(n, yards=yards, touchdowns=ptd * PASS_TD_EV + rtd * RUSH_TD_EV,
         avail=avail)

for n, tm, adp, att, ry, rtd, rec, rey, retd, avail in P.RB:
    yards, catches = skill_game(att, ry, rec, rey, "RB")
    save(n, yards, catches, rtd * RUSH_TD_EV + retd * PASS_TD_EV, avail=avail)

for n, tm, adp, rec, rey, retd, att, ry, rtd, avail in P.WR:
    yards, catches = skill_game(att, ry, rec, rey, "WR")
    save(n, yards, catches, rtd * RUSH_TD_EV + retd * PASS_TD_EV, avail=avail)

for n, tm, adp, rec, rey, retd, avail in P.TE:
    yards, catches = skill_game(0, 0, rec, rey, "TE")
    save(n, yards, catches, retd * PASS_TD_EV, avail=avail)


# Kicker rule: 1 through 40 yards, 2 at 41-50, 3 at 51-60, 4 at 61+; XP=.5.
# Projection feeds do not carry exact attempt distance, so use the same public
# distance mix/leg-strength tilt as the main profile.
FG_BASE_P = np.array([.02, .22, .27, .27, .19, .03])
FG_VALUE = np.array([1., 1., 1., 2., 3., 4.])


def fg_ev(leg):
    z = np.arange(6) - 2.5
    w = FG_BASE_P * np.exp(0.45 * (leg - 1.0) * z / 2.5)
    w /= w.sum()
    return float(w @ FG_VALUE)


for n, tm, adp, fgm, fga, xpm, leg in P.K:
    save(n, other=fgm * fg_ev(leg) + 0.5 * xpm)


def pa_points(pa_season):
    mu = pa_season / 17.0
    pa_g = 7 * RNG.poisson(mu / 9.5, N) + 3 * RNG.poisson(mu / 11.4, N)
    return float(np.select([pa_g == 0, pa_g <= 9], [5.0, 3.0], default=0.0).mean()) * 17


for n, tm, adp, sacks, recoveries, interceptions, dtd, pa, safeties, ktd in P.DST:
    # The feed projects recoveries, not forced fumbles; use recoveries as the
    # closest available proxy for the league's +1 forced-fumble category.
    other = (sacks + recoveries + interceptions + 5 * (dtd + ktd)
             + 2 * safeties + pa_points(pa))
    save(f"{tm} {n}", other=other)

json.dump(scores, open("dad_pts.json", "w"))
print(f"Dad profile scored {len(scores)} players; TD EV pass/rec={PASS_TD_EV:.2f}, "
      f"rush={RUSH_TD_EV:.2f}")

