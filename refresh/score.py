"""Rescore season projections under this league: half PPR, 0.75/catch TE."""
import players as P, json

def base(passYd=0,passTD=0,ints=0,ruYd=0,ruTD=0,rec=0,reYd=0,reTD=0,ppr=0.5):
    return (0.04*passYd + 4*passTD - 1*ints + 0.1*ruYd + 6*ruTD
            + 0.1*reYd + 6*reTD + ppr*rec)

QBINT = {"Josh Allen":9,"Drake Maye":9,"Lamar Jackson":8,"Jayden Daniels":11,"Jalen Hurts":7,
 "Bo Nix":12,"Joe Burrow":10,"Brock Purdy":13,"Caleb Williams":8,"Dak Prescott":10,
 "Jaxson Dart":9,"Justin Herbert":11,"Trevor Lawrence":11,"Jared Goff":10,"Tyler Shough":10,
 "Patrick Mahomes":11,"Kyler Murray":12,"Matthew Stafford":9,"Baker Mayfield":12,
 "Malik Willis":10,"Sam Darnold":13,"Jordan Love":10,"Daniel Jones":12,"Bryce Young":10,
 "C.J. Stroud":10,"Geno Smith":14,"Cam Ward":11,"Aaron Rodgers":8,"Jacoby Brissett":10,
 "Fernando Mendoza":10}

pts={}
for n,tm,a,py,ptd,ry,rtd,av in P.QB: pts[n]=base(py,ptd,QBINT.get(n,10),ry,rtd)*av
for n,tm,a,ra,ry,rtd,rc,red,retd,av in P.RB: pts[n]=base(ruYd=ry,ruTD=rtd,rec=rc,reYd=red,reTD=retd)*av
for n,tm,a,rc,red,retd,ra,ry,rtd,av in P.WR: pts[n]=base(ruYd=ry,ruTD=rtd,rec=rc,reYd=red,reTD=retd)*av
for n,tm,a,rc,red,retd,av in P.TE: pts[n]=base(rec=rc,reYd=red,reTD=retd,ppr=0.75)*av   # TE premium
for n,tm,a,fgm,fga,xpm,leg in P.K: pts[n]=3*fgm+xpm
for n,tm,a,sk,fr,it,dtd,pa,saf,ktd in P.DST:
    papg=pa/17
    pab=10 if papg<11 else 7 if papg<14 else 4 if papg<18 else 1 if papg<22 else 0 if papg<28 else -3
    pts[f"{tm} {n}"]=sk+2*it+2*fr+6*(dtd+ktd)+2*saf+pab*17
json.dump(pts,open("halfppr_pts.json","w"))
print(f"scored {len(pts)} players")
