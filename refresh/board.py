import json, numpy as np, hp_data as D, proj as P, ranks as R, market as M
exec(open('blend.py').read().split('json.dump(rows,open("blend_out.json","w"))')[0].replace(
     'json.dump(rows,open("blend_out.json","w"))',''))

# ---------- award odds ---------------------------------------------------
# The betting layer used to nudge the ranking with team win totals and season
# props. It was removed: measured on this board it moved skill players a mean of
# 1.8 slots (max 11), which is not worth a column or the explanation it needs.
# The award-odds badge survives because it is flavour on the name, not a ranking
# input. market.py still holds WIN and PROPS if the layer is ever wanted back.
for x in rows:
    x["mktnote"]=M.AWARDS.get(x["p"],"")
    x["final"]=x["blend"]

rows.sort(key=lambda z:-z["final"])
# Hard floor on draft position. Pinning their VALUE to the outside anchor was not
# enough -- the value curve is so flat this deep that a defense still surfaced
# around pick 105. So place them by ORDER instead: skill players fill the board,
# then K and DST are slotted in no earlier than FLOOR (see blend.py).
# Only 12 of each is ever drafted -- one per team -- and they go interleaved with
# bench fliers, not in a block. Insert the top 12 of each on a stride from their
# floor and let the remainder fall to the bottom of the board. Dropping all 32
# defenses in consecutively made "best available" read DEF for two straight
# rounds, which is not how anyone drafts.
STRIDE, DRAFTED = 2, 12
_skill=[x for x in rows if x["pos"] not in FLOOR]
_late={p:[x for x in rows if x["pos"]==p] for p in FLOOR}   # already in final order
rows=list(_skill); _tail=[]
for pos in sorted(FLOOR, key=lambda p: FLOOR[p]):
    grp=_late[pos]
    for i,x in enumerate(grp[:DRAFTED]):
        rows.insert(min(len(rows), FLOOR[pos]-1+i*STRIDE), x)
    _tail.extend(grp[DRAFTED:])
rows.extend(_tail)
for i,x in enumerate(rows): x["rk"]=i+1
for x in rows:
    x["gap"]=round(x["avg"]-x["rk"]) if x["nsrc"] else None

# ---------- sleeper / value tags ----------------------------------------
for x in rows:
    sl=x["ffcr"]; tag=""
    if x.get("inj") in R.INJ_BAD:
        tag=""  # an unavailable player is cheap for a reason, not a value call
    elif sl and sl-x["rk"]>=25 and x["rk"]>=75: tag="SLEEPER"
    elif x["pos"] in ("K","DST"):
        # Their rank is set by the deliberate endgame floor, so `gap` for them is
        # a restatement of that floor, not a disagreement with the room. Left in,
        # 20 of the board's 39 FADE badges were floored defenses and kickers,
        # which drowned the real fades.
        tag=""
    elif x["nsrc"]>=2 and x["gap"] is not None and x["gap"]>=18: tag="VALUE"
    elif x["nsrc"]>=2 and x["gap"] is not None and x["gap"]<=-18: tag="FADE"
    x["tag2"]=tag

def tier(seq,gap,cap,key="final"):
    t,run=1,0
    for i,x in enumerate(seq):
        if i>0 and (seq[i-1][key]-x[key]>=gap or run>=cap): t+=1; run=0
        yield x,t; run+=1
for x,t in tier(rows,13,10): x["otier"]=t
for pos in ("QB","RB","WR","TE"):
    for x,t in tier([y for y in rows if y["pos"]==pos],10,7): x["ptier"]=t
json.dump(rows,open("board_out.json","w"))
def _f(v,w=3): return f"{v:+{w}}" if v is not None else " "*(w-2)+"NA"
print("TOP 22"); print("RK T POS  PLAYER                  AVG  MODEL GAP  TAG")
for x in rows[:22]:
    print(f"{x['rk']:3} {x['otier']} {x['pos']}{x['ptier']}  {x['p']:22} {x['avg']:5} "
          f"{str(x['model']):>4} {_f(x['gap'],4)}  {x['tag2']}")
print("\nSLEEPERS"); 
for x in [y for y in rows if y["tag2"]=="SLEEPER"][:14]:
    print(f"  #{x['rk']:3} {x['p']:22} {x['pos']}  FFC half-PPR ADP rank {x['ffcr']:>3}  gap {_f(x['gap'])}")
