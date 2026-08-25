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
# Hard floor on draft position. Pinning their VALUE to public consensus was not
# enough -- the value curve is so flat this deep that a defense still surfaced
# around pick 105. So place them by ORDER instead: skill players fill the board,
# then K and DST are slotted in no earlier than FLOOR (see blend.py).
_skill=[x for x in rows if x["pos"] not in FLOOR]
_late={p:[x for x in rows if x["pos"]==p] for p in FLOOR}
rows=list(_skill)
for pos in sorted(FLOOR, key=lambda p: FLOOR[p]):
    for i,x in enumerate(_late[pos]):
        rows.insert(min(len(rows), FLOOR[pos]-1+i), x)
for i,x in enumerate(rows): x["rk"]=i+1
for x in rows: x["gap"]=round(x["avg"]-x["rk"])

# ---------- sleeper / value tags ----------------------------------------
for x in rows:
    sl=x["ffcr"]; tag=""
    if sl and sl-x["rk"]>=25 and x["rk"]>=75: tag="SLEEPER"
    elif x["gap"]>=18: tag="VALUE"
    elif x["gap"]<=-18: tag="FADE"
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
          f"{str(x['model']):>4} {x['gap']:+4}  {x['tag2']}")
print("\nSLEEPERS"); 
for x in [y for y in rows if y["tag2"]=="SLEEPER"][:14]:
    print(f"  #{x['rk']:3} {x['p']:22} {x['pos']}  FFC half-PPR ADP rank {x['ffcr']:>3}  gap {x['gap']:+3}")
