"""Public half-PPR ranking columns, normalized for joining onto the player pool.

Previously this module held a hand-pasted FantasyPros ECR board and a Flock
Fantasy export. Both were paid products, so they were replaced with four free
public sources (see sources.py). The name-normalizer below is unchanged --
blend.py joins on it and the aliases were tuned against the real pool.
"""
import sources

SUF = (" jr", " sr", " ii", " iii", " iv")
ALIAS = {"devon achane": "devon achane", "kenneth walker": "kenneth walker",
         "dj moore": "d j moore", "dk metcalf": "d k metcalf",
         "kenny gainwell": "kenneth gainwell", "chig okonkwo": "chig okonkwo",
         "cam ward": "cameron ward", "tre harris": "tre harris"}


# Defenses are named four different ways across the sources -- "Houston Defense"
# (FFC), "Texans D/ST" (ESPN), "Steelers" (Yahoo), "HOU Texans" (our pool). All of
# them collapse to "dst <abbr>".
TEAMS = {
 "ARI":("arizona","cardinals"),   "ATL":("atlanta","falcons"),
 "BAL":("baltimore","ravens"),    "BUF":("buffalo","bills"),
 "CAR":("carolina","panthers"),   "CHI":("chicago","bears"),
 "CIN":("cincinnati","bengals"),  "CLE":("cleveland","browns"),
 "DAL":("dallas","cowboys"),      "DEN":("denver","broncos"),
 "DET":("detroit","lions"),       "GB":("green bay","packers"),
 "HOU":("houston","texans"),      "IND":("indianapolis","colts"),
 "JAC":("jacksonville","jaguars"),"KC":("kansas city","chiefs"),
 "LV":("las vegas","raiders"),    "LAC":("la chargers","chargers"),
 "LAR":("la rams","rams"),        "MIA":("miami","dolphins"),
 "MIN":("minnesota","vikings"),   "NE":("new england","patriots"),
 "NO":("new orleans","saints"),   "NYG":("ny giants","giants"),
 "NYJ":("ny jets","jets"),        "PHI":("philadelphia","eagles"),
 "PIT":("pittsburgh","steelers"), "SF":("san francisco","49ers"),
 "SEA":("seattle","seahawks"),    "TB":("tampa bay","buccaneers"),
 "TEN":("tennessee","titans"),    "WAS":("washington","commanders"),
}
NICK = {v[1]: k for k, v in TEAMS.items()}
CITY = {v[0]: k for k, v in TEAMS.items()}
ABBR = {k.lower(): k for k in TEAMS}
DST_MARK = ("defense", "d/st", "dst", "def")


def _dst_abbr(s):
    """Return a team abbr if s names a team defense, else None."""
    toks = s.replace("/", " ").split()
    body = [t for t in toks if t not in ("defense", "dst", "d", "st", "def")]
    if not body:
        return None
    for t in body:                       # nickname is unique across all 32
        if t in NICK:
            return NICK[t]
    joined = " ".join(body)
    if joined in CITY:
        return CITY[joined]
    if body[0] in ABBR:                  # our own pool keys: "HOU Texans"
        return ABBR[body[0]]
    return None


def norm(n):
    s = n.lower().replace(".", "").replace("'", "").replace("`", "")
    s = " ".join(s.split())
    looks_dst = any(m in s for m in DST_MARK) or s in NICK
    if looks_dst:
        a = _dst_abbr(s)
        if a:
            return f"dst {a}"
    for x in SUF:
        if s.endswith(x):
            s = s[:-len(x)].strip()
    s = " ".join(s.split())
    s = ALIAS.get(s, s)
    return s


DATA, NOTES, EXTRAS = sources.load()

# Each source is a name -> (ADP or board rank). Lower is better in all four, so
# they are directly comparable once densely re-ranked within the pool (blend.py).
FFC_N     = {norm(k): v for k, v in DATA.get("ffc", {}).items()}
ESPN_N    = {norm(k): v for k, v in DATA.get("espn", {}).items()}
SLEEPER_N = {norm(k): v for k, v in DATA.get("sleeper", {}).items()}
YAHOO_N   = {norm(k): v for k, v in DATA.get("yahoo", {}).items()}

# FFC also hands us bye weeks and real ADP dispersion for free. The dispersion is
# the useful part: it is measured disagreement among actual drafters, per player,
# which is what tells you whether someone will still be there at your next pick.
BYE_N   = {norm(k): v.get("bye") for k, v in EXTRAS.items() if v.get("bye")}
ADP_N   = {norm(k): DATA.get("ffc", {}).get(k) for k in EXTRAS}
SD_N    = {norm(k): v.get("stdev") for k, v in EXTRAS.items() if v.get("stdev")}
HI_N    = {norm(k): v.get("high") for k, v in EXTRAS.items() if v.get("high")}
LO_N    = {norm(k): v.get("low") for k, v in EXTRAS.items() if v.get("low")}

# Momentum, not a rank: raw weekly add count, rescaled 0-100 against the busiest
# player so it reads as "how hot is he right now".
_tr = DATA.get("trending", {})
_mx = max(_tr.values()) if _tr else 1
TREND_N = {norm(k): round(100.0 * v / _mx) for k, v in _tr.items()}

COLUMNS = [("ffc", FFC_N), ("espn", ESPN_N),
           ("sleeper", SLEEPER_N), ("yahoo", YAHOO_N)]

if __name__ == "__main__":
    for k, v in NOTES.items():
        print(f"{k:8} {v}")
