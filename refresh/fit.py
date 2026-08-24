"""Quantify how much THIS league's quirks help each player:
   - 100 / 200 yard rushing & receiving game bonuses (assumed +3 each)
   - 300 / 400 yard passing game bonuses (assumed +3 each)
   - 0.75 per reception for TE (0.25 above the 0.5 baseline)
   - only 6 bench spots -> contingent/injury-risk assets are worth less
Bonuses reward BIG GAMES, so this needs the per-game distribution, not season averages."""
import numpy as np, json
import players as P
from model import (touches, per_touch_yards, script, N, RNG)

def sim(mean_yd_fn, n=N):
    pass

out = {}

def rec_rush_bonus(att, ypc, rc, ypr, is_te=False, avail=1.0):
    g = script(0.28)
    ry = per_touch_yards((touches(att/17.0, 8.0)*g).round().astype(int), ypc, 0.85, 2.0) if att>0 else np.zeros(N)
    cy = per_touch_yards(touches(rc/17.0, 4.5), ypr, 0.80) if rc>0 else np.zeros(N)
    b  = 3*(ry>=100) + 2*(ry>=200) + 3*(cy>=100) + 2*(cy>=200)
    te = 0.25*rc if is_te else 0.0          # season-long TE reception premium
    return float(b.mean())*17*avail + te*avail

for n,tm,adp,py,ptd,ry,rtd,av in P.QB:
    g = script(0.20)
    pyg = RNG.gamma(16.0, (py/17.0)/16.0, N)*g
    rg  = RNG.gamma(2.2, (ry/17.0)/2.2, N)*np.sqrt(g) if ry>0 else np.zeros(N)
    b = 3*(pyg>=300) + 2*(pyg>=400) + 3*(rg>=100)
    out[n] = float(b.mean())*17*av

for n,tm,adp,ra,ryd,rtd,rc,red,retd,av in P.RB:
    out[n] = rec_rush_bonus(ra, ryd/max(ra,1), rc, red/max(rc,1), False, av)

for n,tm,adp,rc,red,retd,ra,ryd,rtd,av in P.WR:
    out[n] = rec_rush_bonus(ra, ryd/max(ra,1) if ra else 0, rc, red/max(rc,1), False, av)

for n,tm,adp,rc,red,retd,av in P.TE:
    out[n] = rec_rush_bonus(0, 0, rc, red/max(rc,1), True, av)

json.dump(out, open("bonus_pts.json","w"))
top = sorted(out.items(), key=lambda x:-x[1])
print("MOST HELPED BY THIS LEAGUE'S QUIRKS (bonus pts/season)")
for k,v in top[:16]: print(f"  {k:24} {v:6.1f}")
print("\nLEAST HELPED")
for k,v in top[-14:]: print(f"  {k:24} {v:6.1f}")
