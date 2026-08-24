import json, numpy as np, hp_data as D, players as P, ranks as R, market as M
exec(open('blend.py').read().split('json.dump(rows,open("blend_out.json","w"))')[0].replace(
     'json.dump(rows,open("blend_out.json","w"))',''))

# ---------- market layer -------------------------------------------------
PROJ={}
for n,tm,a,py,ptd,ry,rtd,av in P.QB: PROJ[n]={"passYd":py,"passTD":ptd,"ruYd":ry,"ruTD":rtd}
for n,tm,a,ra,ry,rtd,rc,red,retd,av in P.RB: PROJ[n]={"ruYd":ry,"ruTD":rtd,"reYd":red,"reTD":retd}
for n,tm,a,rc,red,retd,ra,ry,rtd,av in P.WR: PROJ[n]={"reYd":red,"reTD":retd,"ruYd":ry,"ruTD":rtd}
for n,tm,a,rc,red,retd,av in P.TE: PROJ[n]={"reYd":red,"reTD":retd}
ALIAS2={"D.K. Metcalf":"D.K. Metcalf","Kenneth Walker III":"Kenneth Walker III"}

wins=np.array(list(M.WIN.values())); wmu,wsd=wins.mean(),wins.std()
for x in rows:
    wt=M.WIN.get(x["tm"])
    x["win"]=wt
    x["mktnote"]=M.AWARDS.get(x["p"],"")
    tz=(wt-wmu)/wsd if wt else 0.0          # team-strength signal, everyone gets one
    prop=M.PROPS.get(x["p"])
    x["prop"]=None; x["propdelta"]=None
    pz=None
    if prop:
        stat,line=prop
        mine=PROJ.get(ALIAS2.get(x["p"],x["p"]),{}).get(stat)
        if mine:
            d=(mine-line)/max(line,1)
            x["prop"]=f"{stat} O/U {line}"
            x["propdelta"]=round(d*100,1)     # % my projection sits above the book
            pz=np.clip(d*4.0,-1.5,1.5)
    # market score -10..+10: prop signal dominates when present, else team strength
    ms = (0.75*pz + 0.25*tz) if pz is not None else 0.55*tz
    x["mkt"]=int(round(float(np.clip(ms*5.0,-10,10))))

# fold market in with modest weight; props move a player more than win totals do
curve2=sorted([x["blend"] for x in rows], reverse=True)
span=(curve2[0]-curve2[-1]) or 1
for x in rows:
    w = 0.13 if x["prop"] else 0.06
    x["final"]=round(x["blend"] + w*(x["mkt"]/10.0)*span*0.35,1)
rows.sort(key=lambda z:-z["final"])
for i,x in enumerate(rows): x["rk"]=i+1
for x in rows: x["gap"]=round(x["avg"]-x["rk"])

# ---------- sleeper / value tags ----------------------------------------
for x in rows:
    sl=x["sleeperr"]; tag=""
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
print("TOP 22"); print("RK T POS  PLAYER                  AVG  MODEL GAP FIT MKT  TAG")
for x in rows[:22]:
    print(f"{x['rk']:3} {x['otier']} {x['pos']}{x['ptier']}  {x['p']:22} {x['avg']:5} "
          f"{str(x['model']):>4} {x['gap']:+4} {_f(x['fit'])} {x['mkt']:+3}  {x['tag2']}")
print("\nSLEEPERS"); 
for x in [y for y in rows if y["tag2"]=="SLEEPER"][:14]:
    print(f"  #{x['rk']:3} {x['p']:22} {x['pos']}  Sleeper board rank {x['sleeperr']:>3}  fit {_f(x['fit'])} mkt {x['mkt']:+3}")
print("\nMARKET DISAGREES MOST WITH PROJECTION")
for x in sorted([y for y in rows if y["propdelta"] is not None],key=lambda z:-abs(z["propdelta"]))[:10]:
    print(f"  {x['p']:22} {x['prop']:22} proj {x['propdelta']:+6.1f}% vs line")
