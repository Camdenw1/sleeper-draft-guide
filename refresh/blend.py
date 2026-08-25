import json, numpy as np, hp_data as D, players as P, ranks as R

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
    return dict(p=name,tm=tm,pos=pos,bye=BYE.get(tm,0),
        base=b,bonus=round(ydb,1),quirk=round(q,1),
        tot=(b+ydb) if b is not None else None,av=AV.get(key,1.0),g=g,r=r,
        ffc=R.FFC_N.get(nn), espn=R.ESPN_N.get(nn),
        yahoo=R.YAHOO_N.get(nn), fcalc=R.FC_N.get(nn),
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

# All four sources are real ADP in picks -> dense integer rank within this pool,
# so the columns are directly comparable to each other and to our own rank.
for key in ("ffc","espn","yahoo","fcalc"):
    have=sorted([x for x in rows if x[key] is not None], key=lambda z:z[key])
    for i,x in enumerate(have): x[key+"r"]=i+1
    for x in rows: x.setdefault(key+"r",None)

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

mr=sorted([x for x in rows if x["vor"] is not None],key=lambda z:-z["vor"])
for i,x in enumerate(mr): x["model"]=i+1
for x in rows: x.setdefault("model",None)

TIERS_LATER=True

# The old "scoring fit" score lived here. It was display-only -- it never touched
# the ranking -- and the league's quirks are already priced into `tot` via the
# yardage bonuses and the TE premium. Removed rather than kept as decoration.

# The four sources do not deserve equal say.
#   ffc     REAL half-PPR 12-team ADP from thousands of actual drafts. The only
#           source whose format matches this league, so it carries double weight.
#   yahoo   real ADP, and Yahoo's default scoring is 0.5/reception -> half PPR.
#   espn    real ADP from ESPN drafts (ownership.averageDraftPosition). Not their
#           editorial board, whose STANDARD and PPR variants are byte-identical
#           and therefore carry no format information at all.
#   fcalc   FantasyCalc at half PPR / 1QB / 12 teams -- exactly this league. A
#           market VALUE rather than an ADP, so it answers the same question from
#           a different direction. Format-exact, so it sits just under FFC.
# MyFantasyLeague was trialled as a fourth and dropped: its pool is riddled with
# superflex drafts, which pulled QBs 38 slots early. See fetch_mfl in sources.py.
# Sleeper is deliberately absent: search_rank is search popularity, not draft
# position, and Sleeper publishes no ADP anywhere (their GraphQL has no adp field
# either). It is still fetched for the trending signal.
SRCW={"ffcr":2.0,"fcalcr":1.5,"yahoor":1.0,"espnr":1.0}
for x in rows:
    pairs=[(x[k],w) for k,w in SRCW.items() if x[k] is not None]
    x["nsrc"]=len(pairs)
    if pairs:
        tw=sum(w for _,w in pairs)
        x["avg"]=round(sum(v*w for v,w in pairs)/tw,1)
    else:
        x["avg"]=float(len(rows))     # nobody ranked him at all -- sort him last
    vs=[v for v,_ in pairs]
    x["spread"]=max(vs)-min(vs) if len(vs)>1 else 0
# Translate each player's average public rank into points-above-replacement by
# reading off the model's own value curve at that slot -> a "market value".
curve=sorted([x["vor"] for x in rows if x["vor"] is not None], reverse=True)
def market(rank):
    i=int(round(rank))-1
    return curve[max(0,min(len(curve)-1,i))]
W=0.50                       # half model, half market
# K and DST are the exception. Their VOR edge is real on paper -- the best defense
# really is ~38 points better than a replacement one -- but it is not actionable:
# both are streamable off waivers, both have week-to-week variance that swamps the
# projection, and neither is remotely predictable year over year. The room's
# TIMING is right and the model's is not, so weight them almost entirely to market
# and let them fall to the rounds where they are actually drafted.
# Earliest slot a K or DST is allowed to appear. You start exactly one of each,
# both are streamable off waivers all season, and neither is predictable year over
# year -- so capital spent on them before the endgame is capital wasted regardless
# of what VOR says. The model's opinion is still visible in the Model column.
FLOOR={"DST":120, "K":140}
for x in rows:
    mv=market(x["avg"])
    x["mktvor"]=round(mv,1)
    if x["pos"] in FLOOR:
        # pinned to the later of public consensus and the floor -- no model pull
        x["blend"]=round(market(max(x["avg"], FLOOR[x["pos"]])),1)
    elif x["vor"] is not None:
        x["blend"]=round(W*x["vor"]+(1-W)*mv,1)
    else:
        x["blend"]=round(mv,1)
rows.sort(key=lambda z:-z["blend"])
for i,x in enumerate(rows): x["rk"]=i+1
for x in rows: x["gap"]=round(x["avg"]-x["rk"])


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
          f"{str(x['yahoor']):>4} {x['avg']:5} {x['gap']:+4}")
print("\nBIGGEST FOUR-SYSTEM DISAGREEMENTS")
for x in sorted(rows,key=lambda z:-z["spread"])[:12]:
    print(f"  {x['p']:22} FFC {str(x['ffcr']):>3} ESPN {str(x['espnr']):>3} "
          f"YH {str(x['yahoor']):>3}  spread {x['spread']}")
