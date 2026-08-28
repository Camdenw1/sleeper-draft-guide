import json, numpy as np, hp_data as D, proj as P, ranks as R

BYE={"BUF":7,"NE":11,"BAL":13,"WAS":7,"PHI":10,"DEN":10,"CIN":6,"SF":8,"CHI":10,"DAL":14,
"NYG":8,"LAC":7,"JAC":7,"DET":6,"NO":8,"KC":5,"MIN":6,"LAR":11,"TB":10,"MIA":6,"SEA":11,
"GB":11,"IND":13,"CAR":5,"HOU":8,"NYJ":13,"TEN":9,"PIT":9,"ARI":14,"LV":13,"CLE":11,"ATL":11}
BASE=json.load(open("halfppr_pts.json")); BONUS=json.load(open("bonus_pts.json"))
AV={r[0]:r[-1] for t in (P.QB,P.RB,P.WR,P.TE) for r in t}
RECS={r[0]:r[3] for r in P.TE}
ALIAS={"DJ Moore":"D.J. Moore","DK Metcalf":"D.K. Metcalf","Travis Etienne Jr.":"Travis Etienne",
"Kyle Pitts Sr.":"Kyle Pitts","Aaron Jones Sr.":"Aaron Jones","K.C. Concepcion":"KC Concepcion",
"Chig Okonkwo":"Chigoziem Okonkwo","Cameron Ward":"Cam Ward"}

def _mkrow(name, tm, pos, key, nn, g="", r=""):
    b=BASE.get(key); q=BONUS.get(key,0.0)
    rc=RECS.get(key,0)
    ydb = q - (0.25*rc if pos=="TE" else 0.0)     # strip the double-counted TE premium
    return dict(p=name,key=key,tm=tm,pos=pos,bye=BYE.get(tm,0),
        base=b,bonus=round(ydb,1),quirk=round(q,1),
        tot=(b+ydb) if b is not None else None,av=AV.get(key,1.0),g=g,r=r,
        ffc=R.FFC_N.get(nn), espn=R.ESPN_N.get(nn),
        yahoo=R.YAHOO_N.get(nn), fcalc=R.FC_N.get(nn), expert=R.EXPERT_N.get(nn),
        inj=(R.INJ_N.get(nn) or {}).get("status"),
        injbody=(R.INJ_N.get(nn) or {}).get("body"),
        adp=R.ADP_N.get(nn), adpsd=R.SD_N.get(nn),
        adphi=R.HI_N.get(nn), adplo=R.LO_N.get(nn),
        trend=R.TREND_N.get(nn))

rows=[]
for (n,tm,pos,sl,es,fpadp,cons,g,r) in D.ROWS:
    rows.append(_mkrow(n,tm,pos,ALIAS.get(n,n),R.norm(n),g,r))
# K and DST carry no hand-written flags; their scoring is fully in score.py.
for n,tm,a,fgm,fga,xpm,leg in P.K:
    rows.append(_mkrow(n,tm,"K",n,R.norm(n)))
for n,tm,a,sk,fr,it,dtd,pa,saf,ktd in P.DST:
    # our own DST key is built directly rather than sniffed by norm()
    rows.append(_mkrow(f"{tm} {n}",tm,"DST",f"{tm} {n}",f"dst {tm}"))

# Put market/value feeds on the same dense rank scale. RotoBaller's editorial
# overall rank stays exact as published. The lanes remain separate below:
# FFC/Yahoo are half-PPR draft market, RotoBaller is expert opinion,
# FantasyCalc is sentiment/value, and ESPN is PPR platform context only.
for key in ("ffc","yahoo","fcalc","espn"):
    have=sorted([x for x in rows if x[key] is not None], key=lambda z:z[key])
    for i,x in enumerate(have): x[key+"r"]=i+1
    for x in rows: x.setdefault(key+"r",None)
for x in rows:
    # An editorial overall rank must be shown exactly as published. Densifying
    # it against our smaller player pool silently changed RotoBaller #96 to #95.
    x["expertr"] = x["expert"]

# VOR: 12 teams, QB/2RB/2WR/TE + W-R-T + W-T + K + DST
have=[x for x in rows if x["tot"] is not None]
def top(pos,k): return sorted([x for x in have if x["pos"]==pos],key=lambda z:-z["tot"])[:k]
taken={id(x) for pos,k in [("QB",12),("RB",24),("WR",24),("TE",12),("K",12),("DST",12)]
       for x in top(pos,k)}
for elig in (("RB","WR","TE"),("WR","TE")):
    pool=[x for x in have if id(x) not in taken and x["pos"] in elig]
    taken|={id(x) for x in sorted(pool,key=lambda z:-z["tot"])[:12]}
REPL={}
for pos in ("QB","RB","WR","TE","K","DST"):
    rest=sorted([x for x in have if x["pos"]==pos and id(x) not in taken],key=lambda z:-z["tot"])
    REPL[pos]=rest[0]["tot"] if rest else 0
for x in rows: x["vor"]=round(x["tot"]-REPL[x["pos"]],1) if x["tot"] is not None else None

# ---- positional reliability -------------------------------------------------
# Raw VOR asks "how many more points than replacement is he PROJECTED for". For
# kickers and defenses that badly overstates what you actually bank, for two
# reasons that compound:
#
#   1. Predictability. Kicker scoring is close to noise year over year, and team
#      defense is not much better. The projected gap between the best kicker and
#      a replacement one mostly does not repeat, so it is not an edge you can
#      draft against -- unlike a target share or a backfield workload, which do.
#   2. Streaming. You never hold one defense all season; you play matchups off
#      waivers. The real baseline is "best available most weeks", which sits far
#      above the drafted-replacement baseline VOR measures against.
#
# So their VOR is scaled to the share of it worth planning around. This is what
# makes the MODEL rank them late rather than the display floor papering over a
# model that still wanted a kicker in round 5.
RELIABILITY={"K":0.15,"DST":0.30}
for x in rows:
    if x["vor"] is not None and x["pos"] in RELIABILITY:
        x["vor_raw"]=x["vor"]
        x["vor"]=round(x["vor"]*RELIABILITY[x["pos"]],1)

mr=sorted([x for x in rows if x["vor"] is not None],key=lambda z:-z["vor"])
for i,x in enumerate(mr): x["model"]=i+1
for x in rows: x.setdefault("model",None)

TIERS_LATER=True

# The old "scoring fit" score lived here. It was display-only -- it never touched
# the ranking -- and the league's quirks are already priced into `tot` via the
# yardage bonuses and the TE premium. Removed rather than kept as decoration.

# ---- outside-information lanes ---------------------------------------------
# Keep unlike signals unlike. ADP says when the room will take a player; expert
# rank says where an independent evaluator would take him; FantasyCalc says how
# the broader half-PPR market values him. ESPN is PPR ADP and remains visible for
# context, but it does not enter this half-PPR decision anchor.
MARKET_W={"ffcr":2.0,"yahoor":1.0}
LANE_W={"market":0.55,"expert_lane":0.30,"sentiment":0.15}

def weighted(row, weights):
    pairs=[(row[k],w) for k,w in weights.items() if row.get(k) is not None]
    if not pairs:
        return None,0
    tw=sum(w for _,w in pairs)
    return round(sum(v*w for v,w in pairs)/tw,1),len(pairs)

for x in rows:
    x["market"],x["market_n"]=weighted(x,MARKET_W)
    x["expert_lane"]=x["expert"]
    x["sentiment"]=x["fcalcr"]
    lane_pairs=[(x[k],w) for k,w in LANE_W.items() if x.get(k) is not None]
    x["nsrc"]=x["market_n"]+(1 if x["expert_lane"] is not None else 0)+(1 if x["sentiment"] is not None else 0)
    if lane_pairs:
        tw=sum(w for _,w in lane_pairs)
        x["anchor"]=round(sum(v*w for v,w in lane_pairs)/tw,1)
    else:
        x["anchor"]=float(len(rows))
    x["avg"]=x["anchor"]  # compatibility: AvgPublic now means decision anchor
    vs=[v for v in (x["market"],x["expert_lane"],x["sentiment"]) if v is not None]
    x["spread"]=round(max(vs)-min(vs)) if len(vs)>1 else 0

# Translate the outside-information anchor into points-above-replacement by
# reading off the model's own value curve at that slot.
curve=sorted([x["vor"] for x in rows if x["vor"] is not None], reverse=True)
def market(rank):
    i=int(round(rank))-1
    return curve[max(0,min(len(curve)-1,i))]
W=0.50                       # half league model, half outside-information anchor
# Earliest slot a K or DST is allowed to appear, on top of the reliability shrink
# above. The roster is 16 deep (QB/2RB/2WR/TE/2flex/K/DST/6bench) across 12 teams,
# so a full draft is 192 picks. Real 12-team drafts take a defense late in round 13
# and a kicker in the last round or two, and there is no reason to be the person
# who goes earlier: everyone gets one, and the difference between the 1st and 12th
# is mostly noise. Floors are set to the start of round 13 and round 15.
FLOOR={"DST":145, "K":169}
for x in rows:
    mv=market(x["anchor"])
    x["mktvor"]=round(mv,1)
    if x["pos"] in FLOOR:
        # pinned to the later of the outside anchor and the floor -- no model pull
        x["blend"]=round(market(max(x["anchor"], FLOOR[x["pos"]])),1)
    elif x["vor"] is not None:
        x["blend"]=round(W*x["vor"]+(1-W)*mv,1)
    else:
        x["blend"]=round(mv,1)
rows.sort(key=lambda z:-z["blend"])
for i,x in enumerate(rows): x["rk"]=i+1
for x in rows:
    # No outside signal means there is no defensible "edge" to advertise. The
    # fallback anchor still lets the model place deep players, but it must not
    # turn missing data into a giant VALUE badge.
    x["gap"]=round(x["avg"]-x["rk"]) if x["nsrc"] else None


def tier(seq,gap,cap):
    t,run=1,0
    for i,x in enumerate(seq):
        if i>0 and (seq[i-1]["blend"]-x["blend"]>=gap or run>=cap): t+=1; run=0
        yield x,t; run+=1
for x,t in tier(rows,13,10): x["otier"]=t
for pos in ("QB","RB","WR","TE","K","DST"):
    for x,t in tier([y for y in rows if y["pos"]==pos],10,7): x["ptier"]=t
# Cross-check the hand-set `avail` in players.py against the live injury feed.
# A player Sleeper lists as IR/PUP/Out but players.py still values at full health
# is a real hole in the board, so shout about it rather than burying it.
_stale=[x for x in rows if x.get("inj") in R.INJ_BAD and x["av"]>=1.0 and x["tot"]]
if _stale:
    print("\n!! LIVE INJURY vs players.py avail -- these are valued as fully healthy:")
    for x in sorted(_stale,key=lambda z:z["rk"]):
        print(f"   #{x['rk']:3} {x['p']:22} {x['pos']:3} {x['inj']:9} {str(x['injbody'])[:18]:18} avail={x['av']}")
    print("   -> fix avail in players.py, or accept and move on.")

json.dump(rows,open("blend_out.json","w"))
print("replacement:",{k:round(v) for k,v in REPL.items()})
print("\nRK T  POS   PLAYER                FFC  FC ESPN   YH  AVG  GAP")
for x in rows[:26]:
    print(f"{x['rk']:3} {x['otier']} {x['pos']}{x['ptier']:<3} {x['p']:22} "
          f"{str(x['ffcr']):>3} {str(x['fcalcr']):>3} {str(x['espnr']):>4} "
          f"{str(x['yahoor']):>4} {x['avg']:5} {str(x['gap']):>4}")
print("\nBIGGEST FOUR-SYSTEM DISAGREEMENTS")
for x in sorted(rows,key=lambda z:-z["spread"])[:12]:
    print(f"  {x['p']:22} FFC {str(x['ffcr']):>3} ESPN {str(x['espnr']):>3} "
          f"YH {str(x['yahoor']):>3}  spread {x['spread']}")
