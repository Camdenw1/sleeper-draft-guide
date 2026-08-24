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

rows=[]
for (n,tm,pos,sl,es,fpadp,cons,g,r) in D.ROWS:
    k=ALIAS.get(n,n); nn=R.norm(n)
    b=BASE.get(k); q=BONUS.get(k,0.0)
    rc=RECS.get(k,0)
    ydb = q - (0.25*rc if pos=="TE" else 0.0)     # strip the double-counted TE premium
    rows.append(dict(p=n,tm=tm,pos=pos,bye=BYE.get(tm,0),
        base=b,bonus=round(ydb,1),quirk=round(q,1),
        tot=(b+ydb) if b is not None else None,av=AV.get(k,1.0),
        ffc=R.FFC_N.get(nn), espn=R.ESPN_N.get(nn),
        sleeper=R.SLEEPER_N.get(nn), yahoo=R.YAHOO_N.get(nn)))

# All four public sources -> dense integer rank within this pool, so the columns
# are comparable (FFC/Yahoo are ADP in picks, ESPN/Sleeper are board ranks).
for key in ("ffc","espn","sleeper","yahoo"):
    have=sorted([x for x in rows if x[key] is not None], key=lambda z:z[key])
    for i,x in enumerate(have): x[key+"r"]=i+1
    for x in rows: x.setdefault(key+"r",None)

# VOR: 12 teams, QB/2RB/2WR/TE + W-R-T + W-T + K + DST
have=[x for x in rows if x["tot"] is not None]
def top(pos,k): return sorted([x for x in have if x["pos"]==pos],key=lambda z:-z["tot"])[:k]
taken={id(x) for pos,k in [("QB",12),("RB",24),("WR",24),("TE",12)] for x in top(pos,k)}
for elig in (("RB","WR","TE"),("WR","TE")):
    pool=[x for x in have if id(x) not in taken and x["pos"] in elig]
    taken|={id(x) for x in sorted(pool,key=lambda z:-z["tot"])[:12]}
REPL={}
for pos in ("QB","RB","WR","TE"):
    rest=sorted([x for x in have if x["pos"]==pos and id(x) not in taken],key=lambda z:-z["tot"])
    REPL[pos]=rest[0]["tot"] if rest else 0
for x in rows: x["vor"]=round(x["tot"]-REPL[x["pos"]],1) if x["tot"] is not None else None

mr=sorted([x for x in rows if x["vor"] is not None],key=lambda z:-z["vor"])
for i,x in enumerate(mr): x["model"]=i+1
for x in rows: x.setdefault("model",None)

TIERS_LATER=True

sh=[x["quirk"]/x["tot"] for x in rows if x["tot"]]
mu,sd=float(np.mean(sh)),float(np.std(sh))
for x in rows:
    if not x["tot"]: x["fit"]=None; continue
    f=np.clip((x["quirk"]/x["tot"]-mu)/sd*3.4,-10,10)
    if x["av"]<1.0: f-=(1.0-x["av"])*22
    if x["tot"]<70: f-=1.5
    x["fit"]=int(round(float(np.clip(f,-10,10))))

for x in rows:
    v=[y for y in (x["ffcr"],x["espnr"],x["sleeperr"],x["yahoor"]) if y is not None]
    x["nsrc"]=len(v)
    # Sleeper covers the whole pool, so v is never empty; guard anyway.
    x["avg"]=round(sum(v)/len(v),1) if v else float(len(rows))
    x["spread"]=max(v)-min(v) if len(v)>1 else 0
# Translate each player's average public rank into points-above-replacement by
# reading off the model's own value curve at that slot -> a "market value".
curve=sorted([x["vor"] for x in rows if x["vor"] is not None], reverse=True)
def market(rank):
    i=int(round(rank))-1
    return curve[max(0,min(len(curve)-1,i))]
W=0.50                       # half model, half market
for x in rows:
    mv=market(x["avg"])
    x["mktvor"]=round(mv,1)
    x["blend"]=round(W*x["vor"]+(1-W)*mv,1) if x["vor"] is not None else round(mv,1)
rows.sort(key=lambda z:-z["blend"])
for i,x in enumerate(rows): x["rk"]=i+1
for x in rows: x["gap"]=round(x["avg"]-x["rk"])

# carry flags
FL={n:(g,r) for (n,tm,pos,sl,es,fpadp,cons,g,r) in D.ROWS}
for x in rows: x["g"],x["r"]=FL[x["p"]]

def tier(seq,gap,cap):
    t,run=1,0
    for i,x in enumerate(seq):
        if i>0 and (seq[i-1]["blend"]-x["blend"]>=gap or run>=cap): t+=1; run=0
        yield x,t; run+=1
for x,t in tier(rows,13,10): x["otier"]=t
for pos in ("QB","RB","WR","TE"):
    for x,t in tier([y for y in rows if y["pos"]==pos],10,7): x["ptier"]=t
json.dump(rows,open("blend_out.json","w"))
print("replacement:",{k:round(v) for k,v in REPL.items()})
print("\nRK T  POS   PLAYER                FFC ESPN  SLP  YH  AVG  GAP FIT")
for x in rows[:26]:
    print(f"{x['rk']:3} {x['otier']} {x['pos']}{x['ptier']:<3} {x['p']:22} "
          f"{str(x['ffcr']):>3} {str(x['espnr']):>4} {str(x['sleeperr']):>4} "
          f"{str(x['yahoor']):>3} {x['avg']:5} {x['gap']:+4} {x['fit']:+3}")
print("\nBIGGEST FOUR-SYSTEM DISAGREEMENTS")
for x in sorted(rows,key=lambda z:-z["spread"])[:12]:
    print(f"  {x['p']:22} FFC {str(x['ffcr']):>3} ESPN {str(x['espnr']):>3} "
          f"SLP {str(x['sleeperr']):>3} YH {str(x['yahoor']):>3}  spread {x['spread']}")
