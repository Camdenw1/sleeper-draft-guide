# Betting-market layer, Aug 24 2026.
# Team win totals: consensus of major books (complete, all 32).
WIN = {"BAL":11.5,"LAR":11.5,"BUF":10.5,"KC":10.5,"DET":10.5,"GB":10.5,"PHI":10.5,"SF":10.5,
"SEA":10.5,"CIN":9.5,"DEN":9.5,"HOU":9.5,"LAC":9.5,"NE":9.5,"CHI":9.5,"JAC":8.5,"PIT":8.5,
"DAL":8.5,"MIN":8.5,"TB":8.5,"IND":7.5,"ATL":7.5,"CAR":7.5,"NO":7.5,"NYG":7.5,"WAS":7.5,
"TEN":6.5,"CLE":5.5,"LV":5.5,"NYJ":5.5,"MIA":4.5,"ARI":4.5}

# Season-long O/U lines actually available for free (DraftKings unless noted).
# (stat, line) -> compared against the projection driving my rank.
PROPS = {
 "Jalen Hurts":("passYd",3249.5),"Drake Maye":("passYd",3799.5),"Baker Mayfield":("passYd",3599.5),
 "Jordan Love":("passYd",3549.5),"Caleb Williams":("passYd",3624.5),
 "Justin Herbert":("passTD",24.5),"Jared Goff":("passTD",29.5),"Tyler Shough":("passTD",20.5),
 "Bo Nix":("passTD",24.5),"Josh Allen":("passTD",24.5),
 "David Montgomery":("ruYd",774.5),"D'Andre Swift":("ruYd",799.5),"Kyren Williams":("ruYd",999.5),
 "Kenneth Walker III":("ruYd",924.5),
 "Jonathan Taylor":("ruTD",11.5),"Jahmyr Gibbs":("ruTD",12.5),"Christian McCaffrey":("ruTD",8.5),
 "Jalen Hurts2":("ruTD",8.5),
 "D.K. Metcalf":("reYd",824.5),"George Pickens":("reYd",999.5),"Denzel Boston":("reYd",474.5),
 "Colston Loveland":("reYd",749.5),"Michael Pittman Jr.":("reYd",774.5),
 "Tetairoa McMillan":("reTD",6.5),"Trey McBride":("reTD",6.5),"Drake London":("reTD",7.5),
 "Justin Jefferson":("reTD",6.5),"Chris Olave":("reTD",5.5),
}
# Award-market confidence (shortest odds = market believes in the season outcome)
AWARDS = {"Josh Allen":"MVP fav (+600)","Lamar Jackson":"MVP 2nd (+700)","Joe Burrow":"MVP (+1000)",
"Drake Maye":"MVP (+1100)","Justin Herbert":"MVP (+1100)","Jahmyr Gibbs":"OPOY fav (+850)",
"Bijan Robinson":"OPOY (+900)","Ja'Marr Chase":"OPOY (+1100)","Puka Nacua":"OPOY (+1200)",
"Jaxon Smith-Njigba":"OPOY (+1500)","Jeremiyah Love":"ORoY fav (+320)",
"Jordyn Tyson":"ORoY (+700)","Carnell Tate":"ORoY (+700)","Jadarian Price":"ORoY (+750)",
"Patrick Mahomes":"CPOY fav (+185)","Jayden Daniels":"CPOY (+400)","Kyler Murray":"CPOY (+600)",
"Malik Nabers":"CPOY (+1300)"}
