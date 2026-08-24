"""
Monte Carlo projection engine for a bucketed / big-play fantasy scoring system.

WHY SIMULATION INSTEAD OF PLUGGING SEASON AVERAGES INTO THE SCORING TABLE:
Every yardage and reception category in this league is a STEP FUNCTION. You get
credit only when you cross a threshold; everything above it is floored away.
So E[points] != points(E[yards]). A WR averaging 65 rec yds/gm does not earn
3.25 pts; he earns P(>=20)+P(>=40)+P(>=60)+P(>=80)+... which is closer to 2.8.
The size of that flooring loss depends on how volatile the player is, so you need
the whole distribution, not the mean.

Touchdown DISTANCE, by contrast, is linear in expectation -- E[pts] = P(TD) *
E[pts per TD] -- so what matters there is the right expected points per score for
each player type (deep threats earn more per TD than goal-line backs). We get
that by tilting an empirical NFL TD-length distribution using yards-per-reception
/ yards-per-carry as a proxy for average scoring depth.

Yardage is built up from individual carries and catches (heavy-tailed lognormal
per touch), so the long-play tail is generated rather than assumed.
"""
import numpy as np
import pandas as pd
import players as P

RNG = np.random.default_rng(20260823)
N = 40000
GAMES = 17

# ---------------------------------------------------------------- scoring ---
def pass_yd_pts(y):
    return np.where(y < 75, 0, np.minimum(7, 1 + (np.maximum(y, 75) - 75) // 75))

def rush_yd_pts(y):
    return np.where(y < 25, 0, np.minimum(9, 1 + (np.maximum(y, 25) - 25) // 25))

def rec_yd_pts(y):
    return np.where(y < 20, 0, np.minimum(10, 1 + (np.maximum(y, 20) - 20) // 20))

def rec_pts_rb_te(r):
    return np.where(r < 3, 0, np.minimum(9, 1 + (np.maximum(r, 3) - 3) // 2))

def rec_pts_wr(r):
    return np.where(r < 5, 0, np.minimum(9, 1 + (np.maximum(r, 5) - 5) // 2))

AIR_MID = np.array([3, 8, 15, 25, 35, 45, 55, 65, 75, 85, 95], float)
AIR_P   = np.array([.240,.210,.230,.110,.060,.045,.035,.025,.020,.015,.010])
AIR_PTS = np.array([3, 3, 4, 4, 5, 5, 6, 6, 7, 8, 9], float)
GND_P   = np.array([.640,.210,.090,.020,.014,.010,.007,.004,.0025,.0015,.001])
GND_PTS = np.array([4, 4, 5, 5, 6, 6, 7, 7, 8, 9, 10], float)

def tilted(base_p, z, beta=0.35):
    l = np.log(AIR_MID)
    m = (base_p * l).sum()
    s = np.sqrt((base_p * (l - m) ** 2).sum())
    w = base_p * np.exp(beta * np.clip(z, -1.5, 1.5) * (l - m) / s)
    return w / w.sum()

def td_points(counts, probs, pts):
    out = np.zeros(counts.shape, float)
    for k in range(int(counts.max()) if counts.size else 0):
        draw = RNG.choice(len(probs), size=counts.shape, p=probs)
        out += np.where(counts > k, pts[draw], 0.0)
    return out

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

# ------------------------------------------------------------- simulators ---
def sim_qb(r):
    _, _, _, pyd, ptd, ryd, rtd, avail = r
    g = script(0.20)
    py = RNG.gamma(16.0, (pyd / 17.0) / 16.0, N) * g
    ptd_n = RNG.poisson(np.maximum(ptd / 17.0 * g, 1e-6))
    z = (pyd / max(ptd, 1) / 130.0 - 1.0) * 1.2
    td = td_points(ptd_n, tilted(AIR_P, z), AIR_PTS)
    pts = pass_yd_pts(py) + td
    if ryd > 0:
        pts = pts + rush_yd_pts(RNG.gamma(2.2, (ryd / 17.0) / 2.2, N) * np.sqrt(g))
    rtd_n = RNG.poisson(np.maximum(rtd / 17.0 * np.sqrt(g), 1e-9))
    gtd = td_points(rtd_n, tilted(GND_P, -0.3), GND_PTS)
    return pts + gtd, td + gtd, avail

def sim_rb(r):
    _, _, _, ra, ryd, rtd, rc, red, retd, avail = r
    g = script(0.28)
    att = (touches(ra / 17.0, 8.0) * g).round().astype(int)
    ry = per_touch_yards(att, ryd / max(ra, 1), 0.85, 2.0)
    rtd_n = RNG.poisson(np.maximum(rtd / 17.0 * np.sqrt(g), 1e-9))
    td = td_points(rtd_n, tilted(GND_P, (ryd / max(ra, 1) - 4.3) / 0.7 * 0.6), GND_PTS)
    pts = rush_yd_pts(ry) + td
    if rc > 0:
        ypr = red / max(rc, 1)
        cat = touches(rc / 17.0, 5.0)
        cy = per_touch_yards(cat, ypr, 0.80)
        atd = td_points(RNG.poisson(np.maximum(retd / 17.0, 1e-9), N),
                        tilted(AIR_P, (ypr - 8.0) / 2.5), AIR_PTS)
        pts = pts + rec_yd_pts(cy) + rec_pts_rb_te(cat) + atd
        td = td + atd
    return pts, td, avail

def sim_wr(r):
    _, _, _, rc, red, retd, ra, ryd, rtd, avail = r
    ypr = red / max(rc, 1)
    cat = touches(rc / 17.0, 4.5)
    cy = per_touch_yards(cat, ypr, 0.80)
    td = td_points(RNG.poisson(np.maximum(retd / 17.0, 1e-9), N),
                   tilted(AIR_P, (ypr - 12.6) / 2.6), AIR_PTS)
    pts = rec_yd_pts(cy) + rec_pts_wr(cat) + td
    if ra > 0:
        att = touches(ra / 17.0, 3.0)
        gtd = td_points(RNG.poisson(np.maximum(rtd / 17.0, 1e-9), N),
                        tilted(GND_P, 1.0), GND_PTS)
        pts = pts + rush_yd_pts(per_touch_yards(att, ryd / max(ra, 1), 0.95, 2.0)) + gtd
        td = td + gtd
    return pts, td, avail

def sim_te(r):
    _, _, _, rc, red, retd, avail = r
    ypr = red / max(rc, 1)
    cat = touches(rc / 17.0, 5.0)
    cy = per_touch_yards(cat, ypr, 0.78)
    td = td_points(RNG.poisson(np.maximum(retd / 17.0, 1e-9), N),
                   tilted(AIR_P, (ypr - 11.0) / 2.2), AIR_PTS)
    return rec_yd_pts(cy) + rec_pts_rb_te(cat) + td, td, avail

FG_P, FG_PTS = np.array([.50, .29, .19, .02]), np.array([1., 2., 3., 4.])

def sim_k(r):
    _, _, _, fgm, fga, xpm, leg = r
    w = FG_P * (leg ** (np.arange(4) * 0.7)); w = w / w.sum()
    n = RNG.poisson(fgm / 17.0, N)
    pts = np.zeros(N)
    for k in range(int(n.max())):
        pts += np.where(n > k, FG_PTS[RNG.choice(4, size=N, p=w)], 0.0)
    xp = RNG.poisson(xpm / 17.0, N) * 0.5
    return pts + xp, np.zeros(N), 1.0

def sim_dst(r):
    _, _, _, sk, fr, ints, dtd, pa, saf, ktd = r
    m = sk / 17.0
    sacks = RNG.negative_binomial(6.0, 6.0 / (6.0 + m), N)
    ff = RNG.poisson(fr * 1.5 / 17.0, N)
    it = RNG.poisson(ints / 17.0, N)
    td = RNG.poisson((dtd + ktd) / 17.0, N)
    sf = RNG.poisson(saf / 17.0, N)
    mu = pa / 17.0
    pa_g = 7 * RNG.poisson(mu / 9.5, N) + 3 * RNG.poisson(mu / 11.4, N)
    pa_pts = np.where(pa_g == 0, 5.0, np.where(pa_g <= 9, 3.0, 0.0))
    return sacks + it + ff + 5.0 * td + 2.0 * sf + pa_pts, 5.0 * td, 1.0

SIMS = [("QB", P.QB, sim_qb), ("RB", P.RB, sim_rb), ("WR", P.WR, sim_wr),
        ("TE", P.TE, sim_te), ("K", P.K, sim_k), ("DST", P.DST, sim_dst)]

rows = []
for pos, table, fn in SIMS:
    for r in table:
        pts, td, avail = fn(r)
        rows.append(dict(
            player=(r[0] if pos != "DST" else f"{r[1]} {r[0]}"),
            team=r[1], pos=pos, adp=r[2], avail=avail,
            ppw=pts.mean() * avail,
            season=pts.mean() * avail * GAMES,
            tdshare=td.mean() / max(pts.mean(), 1e-9),
            med=float(np.median(pts)),
            p90=float(np.percentile(pts, 90)),
            boom=(pts >= 10).mean() * avail,
            dud=(pts <= 2).mean() * avail + (1 - avail),
            sd=float(pts.std()),
        ))

df = pd.DataFrame(rows)

if __name__ == "__main__":
    print(df.groupby("pos")[["ppw", "tdshare", "boom"]].mean().round(3))
