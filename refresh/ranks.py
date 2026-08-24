# Flock Fantasy redraft order (rank = index+1), from user's export
FLOCK = """Jahmyr Gibbs|Bijan Robinson|Ja'Marr Chase|Puka Nacua|Jaxon Smith-Njigba|Christian McCaffrey|
Amon-Ra St. Brown|Jonathan Taylor|James Cook|CeeDee Lamb|Justin Jefferson|Chase Brown|Devon Achane|
Omarion Hampton|Saquon Barkley|Kenneth Walker|Drake London|Derrick Henry|Brock Bowers|A.J. Brown|
Nico Collins|Malik Nabers|George Pickens|Rashee Rice|Chris Olave|Trey McBride|Ashton Jeanty|Breece Hall|
DeVonta Smith|Jeremiyah Love|Kyren Williams|Javonte Williams|Zay Flowers|Tee Higgins|Jaylen Waddle|
Josh Jacobs|Josh Allen|Ladd McConkey|Emeka Egbuka|Colston Loveland|Tetairoa McMillan|Travis Etienne|
Garrett Wilson|Bucky Irving|Cam Skattebo|D'Andre Swift|Bhayshul Tuten|Davante Adams|David Montgomery|
Quinshon Judkins|Luther Burden|Terry McLaurin|Jameson Williams|TreVeyon Henderson|Jadarian Price|
Lamar Jackson|Mike Evans|Rome Odunze|Carnell Tate|Tyler Warren|Brian Thomas|DJ Moore|Christian Watson|
Marvin Harrison|Jaylen Warren|Parker Washington|Drake Maye|Jayden Daniels|Joe Burrow|Caleb Williams|
Jonathon Brooks|Jalen Hurts|Tucker Kraft|Rhamondre Stevenson|Tony Pollard|Sam LaPorta|Michael Pittman|
Makai Lemon|Chris Godwin|Jordan Addison|Quentin Johnston|DK Metcalf|J.K. Dobbins|Trevor Lawrence|
Stefon Diggs|Justin Herbert|Alec Pierce|Courtland Sutton|Michael Wilson|Rico Dowdle|RJ Harvey|
Dak Prescott|Rachaad White|Jordan Mason|Kyle Pitts|Harold Fannin|Chuba Hubbard|Josh Downs|Blake Corum|
Wan'Dale Robinson|Jacory Croskey-Merritt|KC Concepcion|Brock Purdy|Jaxson Dart|George Kittle|
Jordyn Tyson|Kyle Monangai|Bo Nix|Jayden Reed|Patrick Mahomes|Xavier Worthy|Kenneth Gainwell|
Matthew Stafford|De'Zhaun Stribling|Matthew Golden|Jared Goff|Deebo Samuel|Kyler Murray|Aaron Jones|
Travis Kelce|Jakobi Meyers|Romeo Doubs|Travis Hunter|Jalen Coker|Jake Ferguson|Denzel Boston|
Baker Mayfield|Isaiah Likely|Dalton Kincaid|Chris Rodriguez|Tyler Shough|Dallas Goedert|Jonah Coleman|
Malik Willis|Mark Andrews|Khalil Shakir|Jordan Love|Woody Marks|Rashid Shaheed|Keaton Mitchell|
Tyler Allgeier|Tank Bigsby|Keenan Allen|Omar Cooper Jr.|Juwan Johnson|Jalen McMillan|Chig Okonkwo|
Mike Washington Jr.|Brenton Strange|Tyrone Tracy|Tre Tucker|Isiah Pacheco|C.J. Stroud|Sam Darnold|
Cam Ward|Daniel Jones|Hunter Henry|Oronde Gadsden|MarShawn Lloyd|Dylan Sampson|Alvin Kamara|
Zach Charbonnet|Bryce Young|Kenyon Sadiq|Tyjae Spears|T.J. Hockenson|Dalton Schultz|AJ Barner|
Brian Robinson|Jalen Nailor|Tre Harris|Sean Tucker|Caleb Douglas|Tank Dell|Nicholas Singleton|
Kaytron Allen|Ja'Kobi Lane|Darnell Mooney|Antonio Williams|Ryan Flournoy|Emmett Johnson|Kayshon Boutte|
Zachariah Branch|Calvin Ridley|Malik Washington|Cyrus Allen|Terrance Ferguson|Demond Claiborne|
Ray Davis|Chris Brooks|Germie Bernard|Jerry Jeudy|Braelon Allen|Devin Singletary|Gunnar Helm|
Brashard Smith|Jauan Jennings|Isaac TeSlaa|Najee Harris|Aaron Rodgers|David Njoku|Jaydon Blue|
Jacoby Brissett|Kimani Vidal|Pat Freiermuth|Chris Bell|Adonai Mitchell|Troy Franklin|Elijah Sarratt|
Ollie Gordon II|Greg Dulcich|Cade Otton|Eli Stowers|Fernando Mendoza|Geno Smith|Elic Ayomanor|
Dontayvion Wicks|Darius Slayton|Ted Hurst|Adam Randall|Malachi Fields|Jaylin Noel|Jordan James|
Calvin Austin|Keon Coleman|Pat Bryant|Luke McCaffrey|Jack Bech|Justice Hill|Chimere Dike|
Christian Kirk|Ty Johnson|James Conner|Tyquan Thornton|Tory Horton|Tez Johnson|DJ Giddens|Bryce Lance|
Tua Tagovailoa|Charlie Kolar|Isaiah Davis|Skyler Bell|Samaje Perine|Kendre Miller|George Holani|
Emanuel Wilson|Cedric Tillman|Max Klare|Devaughn Vele|Rashod Bateman"""

# FantasyPros half-PPR expert consensus, grouped by their published tiers
FP_TIERS = {
1:"""Jahmyr Gibbs|Bijan Robinson|Ja'Marr Chase|Puka Nacua|Jaxon Smith-Njigba|Amon-Ra St. Brown|
Jonathan Taylor|Christian McCaffrey|CeeDee Lamb""",
2:"""Justin Jefferson|James Cook III|Drake London|Chase Brown|A.J. Brown|Saquon Barkley|De'Von Achane|
Brock Bowers|Nico Collins|Omarion Hampton|Kenneth Walker III|Derrick Henry""",
3:"""George Pickens|Trey McBride|Chris Olave|Malik Nabers|Rashee Rice|DeVonta Smith|Zay Flowers|
Kyren Williams|Ashton Jeanty|Tee Higgins|Josh Allen|Tetairoa McMillan|Javonte Williams|Breece Hall|
Garrett Wilson|Josh Jacobs|Jaylen Waddle|Ladd McConkey""",
4:"""Emeka Egbuka|Jeremiyah Love|Colston Loveland|Travis Etienne Jr.|Lamar Jackson|Terry McLaurin|
Davante Adams|D'Andre Swift|Luther Burden III|Drake Maye|Cam Skattebo|Tyler Warren|Jameson Williams|
Bucky Irving|Quinshon Judkins|David Montgomery|DJ Moore|Christian Watson|Mike Evans|Rome Odunze|
Joe Burrow|Bhayshul Tuten""",
5:"""TreVeyon Henderson|Jadarian Price|Jayden Daniels|Parker Washington|Jalen Hurts|Tucker Kraft|
Carnell Tate|Marvin Harrison Jr.|Jaylen Warren|Rhamondre Stevenson|Caleb Williams|Brian Thomas Jr.|
Tony Pollard|Harold Fannin Jr.|DK Metcalf|Sam LaPorta|Justin Herbert|Chris Godwin Jr.|Rico Dowdle|
Kyle Pitts Sr.|Courtland Sutton|Trevor Lawrence|Jonathon Brooks|Dak Prescott|J.K. Dobbins|
Michael Pittman Jr.""",
6:"""Michael Wilson|Quentin Johnston|Blake Corum|Chuba Hubbard|Alec Pierce|George Kittle|Josh Downs|
Wan'Dale Robinson|RJ Harvey|Mike Washington Jr.|Stefon Diggs|Jacory Croskey-Merritt|Travis Kelce|
Brock Purdy|Jordan Addison|Jordan Mason|Kenny Gainwell|Jaxson Dart|Jayden Reed|Kyle Monangai|
Rachaad White|Patrick Mahomes II|Bo Nix|Makai Lemon|Dalton Kincaid|Jakobi Meyers|Aaron Jones Sr.|
Matthew Stafford|Dallas Goedert|Jared Goff|Isaiah Likely|Kyler Murray|KC Concepcion|Mark Andrews|
Chris Rodriguez Jr.|Xavier Worthy|Jalen Coker|Matthew Golden|Jake Ferguson|Khalil Shakir""",
7:"""Tyler Allgeier|Baker Mayfield|Jordan Love|Jordyn Tyson|Woody Marks|Tyler Shough|Romeo Doubs|
Tyjae Spears|Juwan Johnson|Malik Willis|Deebo Samuel Sr.|Keaton Mitchell|Tyrone Tracy Jr.|Tank Bigsby|
De'Zhaun Stribling|Jonah Coleman|Hunter Henry|Zach Charbonnet|C.J. Stroud|Chig Okonkwo|Brenton Strange|
Sam Darnold|Dylan Sampson|Alvin Kamara|Denzel Boston|Rashid Shaheed|Daniel Jones|Adonai Mitchell|
Dalton Schultz|Cam Ward|Brian Robinson Jr.|Isiah Pacheco|Tre Tucker|Jauan Jennings|Jalen McMillan|
Jerry Jeudy|Braelon Allen|T.J. Hockenson""",
8:"""MarShawn Lloyd|AJ Barner|Bryce Young|Jalen Nailor|Dontayvion Wicks|Oronde Gadsden II|Tre' Harris|
Omar Cooper Jr.|Ray Davis|Terrance Ferguson|Emmett Johnson|Jacoby Brissett|Ryan Flournoy|Sean Tucker|
Pat Bryant|Malik Washington|Keenan Allen|Kenyon Sadiq|Houston Texans|Jaylin Noel|Kayshon Boutte|
Gunnar Helm|Kimani Vidal|Nicholas Singleton|Denver Broncos|Tank Dell|Calvin Ridley|Seattle Seahawks|
Los Angeles Rams|Travis Hunter|Philadelphia Eagles|Geno Smith|Aaron Rodgers|Cade Otton|
Jacksonville Jaguars|Pat Freiermuth|New England Patriots|Pittsburgh Steelers|Kaytron Allen|
James Conner|Los Angeles Chargers|Minnesota Vikings|Isaac TeSlaa|Jaydon Blue|Brandon Aubrey|
Emanuel Wilson|Rashod Bateman|Baltimore Ravens|Ka'imi Fairbairn|Cameron Dicker|Kansas City Chiefs|
Cam Little""",
}
# Tier 9 members that appear in our pool, with their published FP rank
FP_T9 = {"Darnell Mooney":219,"Troy Franklin":220,"Cooper Kupp":225,"Jaylen Wright":227,
"George Holani":229,"Colby Parkinson":230,"David Njoku":231,"Germie Bernard":235,"Evan Engram":236,
"Ollie Gordon II":238,"Zachariah Branch":239,"Malachi Fields":243,"Justice Hill":244,"Jack Bech":245,
"Demond Claiborne":246,"Devaughn Vele":247,"Antonio Williams":248,"Elic Ayomanor":250,
"Isaiah Davis":251,"Tory Horton":253,"Ted Hurst":254,"Samaje Perine":255,"Kaelon Black":256,
"Chris Brooks":257,"Keon Coleman":259,"Najee Harris":260,"Chris Bell":261,"Ja'Kobi Lane":262,
"Chimere Dike":263,"Jordan James":264,"Christian Kirk":276,"DJ Giddens":277,"Elijah Sarratt":278,
"Trey Benson":281,"Caleb Douglas":282,"Xavier Legette":283,"Marvin Mims Jr.":289,
"Kendre Miller":291,"Tyquan Thornton":273,"Mason Taylor":274,"Greg Dulcich":272,"Ty Johnson":269,
"Theo Johnson":288,"Malik Davis":280,"Adam Randall":285,"Seth McGowan":286,"Devin Neal":287,
"Brashard Smith":290,"Eli Stowers":292}

def _split(s): return [x.strip() for x in s.replace("\n","").split("|") if x.strip()]

FLOCK_RANK = {n:i+1 for i,n in enumerate(_split(FLOCK))}
FP_RANK, FP_TIER = {}, {}
r = 0
for t in sorted(FP_TIERS):
    for n in _split(FP_TIERS[t]):
        r += 1; FP_RANK[n]=r; FP_TIER[n]=t
for n,v in FP_T9.items(): FP_RANK[n]=v; FP_TIER[n]=9

SUF = (" jr"," sr"," ii"," iii"," iv")
ALIAS = {"devon achane":"devon achane","kenneth walker":"kenneth walker",
 "dj moore":"d j moore","dk metcalf":"d k metcalf","kenny gainwell":"kenneth gainwell",
 "chig okonkwo":"chig okonkwo","cam ward":"cameron ward","tre harris":"tre harris"}
def norm(n):
    s = n.lower().replace(".","").replace("'","").replace("`","")
    s = " ".join(s.split())
    for x in SUF:
        if s.endswith(x): s = s[:-len(x)].strip()
    s = " ".join(s.split())
    s = ALIAS.get(s, s)
    return s

FLOCK_N = {norm(k):v for k,v in FLOCK_RANK.items()}
FP_N    = {norm(k):v for k,v in FP_RANK.items()}
FPT_N   = {norm(k):v for k,v in FP_TIER.items()}
