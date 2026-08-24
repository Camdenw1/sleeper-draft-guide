"""Rescore season projections under this league's actual scoring.

Half PPR, 0.75/catch for TE (0.5 baseline + 0.25 premium), interceptions at -2.

Two positions need more than a multiply-and-sum:

  K    FG points depend on DISTANCE (1-6 by bucket) plus 0.10 per yard, so a
       45-yarder is worth 8.5. Each kick is independent and we only need the
       season total, so the expectation is exact -- no simulation required.
  DST  Points-allowed scoring is a per-GAME step function (0 -> +10, 35+ -> -4).
       E[tier(PA)] != tier(E[PA]), the same reason fit.py exists, so the PA
       component is simulated per game rather than read off the season average.

Per-game yardage bonuses live in fit.py.
"""
import json
import numpy as np
import players as P

RNG = np.random.default_rng(20260823)
N = 40000


def base(passYd=0, passTD=0, ints=0, ruYd=0, ruTD=0, rec=0, reYd=0, reTD=0, ppr=0.5):
    return (0.04 * passYd + 4 * passTD - 2 * ints + 0.1 * ruYd + 6 * ruTD
            + 0.1 * reYd + 6 * reTD + ppr * rec)


QBINT = {"Josh Allen":9,"Drake Maye":9,"Lamar Jackson":8,"Jayden Daniels":11,"Jalen Hurts":7,
 "Bo Nix":12,"Joe Burrow":10,"Brock Purdy":13,"Caleb Williams":8,"Dak Prescott":10,
 "Jaxson Dart":9,"Justin Herbert":11,"Trevor Lawrence":11,"Jared Goff":10,"Tyler Shough":10,
 "Patrick Mahomes":11,"Kyler Murray":12,"Matthew Stafford":9,"Baker Mayfield":12,
 "Malik Willis":10,"Sam Darnold":13,"Jordan Love":10,"Daniel Jones":12,"Bryce Young":10,
 "C.J. Stroud":10,"Geno Smith":14,"Cam Ward":11,"Aaron Rodgers":8,"Jacoby Brissett":10,
 "Fernando Mendoza":10}

# ------------------------------------------------------------------ kicker ---
# Standard fantasy kicker scoring: 3 under 40, 4 from 40-49, 5 from 50+, PAT 1,
# missed FG -1. The league's scoring page currently also shows a 0.10/yard bonus
# and 1/2/3 buckets under 40, which would make a 45-yarder worth 8.5 and push
# kickers into the top 60. Camden confirmed that is a setup error being fixed, so
# normal scoring is what is modelled here.
FG_BASE_P = np.array([.02, .22, .27, .27, .19, .03])   # made-FG distance mix
FG_VALUE  = np.array([3., 3., 3., 4., 5., 5.])         # 0-19 20-29 30-39 40-49 50-59 60+


def fg_ev(leg):
    """Expected points per made FG, tilting the distance mix by leg strength.

    A big-leg kicker attempts more long field goals, so he earns slightly more per
    make even under flat-ish scoring. That is the only thing `leg` buys now.
    """
    z = np.arange(6) - 2.5
    w = FG_BASE_P * np.exp(0.45 * (leg - 1.0) * z / 2.5)
    w = w / w.sum()
    return float((w * FG_VALUE).sum())


# ------------------------------------------------------------------- defense ---
def pa_points(pa_season):
    """Simulate per-game points allowed and average the tier payout."""
    mu = pa_season / 17.0
    pa_g = 7 * RNG.poisson(mu / 9.5, N) + 3 * RNG.poisson(mu / 11.4, N)
    pts = np.select(
        [pa_g == 0, pa_g <= 6, pa_g <= 13, pa_g <= 20, pa_g <= 27, pa_g <= 34],
        [10.0,      7.0,       4.0,        1.0,        0.0,        -1.0],
        default=-4.0)
    return float(pts.mean()) * 17


pts = {}
for n,tm,a,py,ptd,ry,rtd,av in P.QB: pts[n]=base(py,ptd,QBINT.get(n,10),ry,rtd)*av
for n,tm,a,ra,ry,rtd,rc,red,retd,av in P.RB: pts[n]=base(ruYd=ry,ruTD=rtd,rec=rc,reYd=red,reTD=retd)*av
for n,tm,a,rc,red,retd,ra,ry,rtd,av in P.WR: pts[n]=base(ruYd=ry,ruTD=rtd,rec=rc,reYd=red,reTD=retd)*av
for n,tm,a,rc,red,retd,av in P.TE: pts[n]=base(rec=rc,reYd=red,reTD=retd,ppr=0.75)*av   # TE premium

for n,tm,a,fgm,fga,xpm,leg in P.K:
    pts[n] = fgm * fg_ev(leg) + xpm - (fga - fgm)      # FG missed is -1

for n,tm,a,sk,fr,it,dtd,pa,saf,ktd in P.DST:
    pts[f"{tm} {n}"] = sk + 2*it + 2*fr + 6*(dtd+ktd) + 2*saf + pa_points(pa)

json.dump(pts, open("halfppr_pts.json", "w"))
print(f"scored {len(pts)} players")
ks = sorted([(v, k) for k, v in pts.items() if any(k == r[0] for r in P.K)], reverse=True)[:3]
print("  top kickers:", ", ".join(f"{k} {v:.0f}" for v, k in ks))
