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


def norm(n):
    s = n.lower().replace(".", "").replace("'", "").replace("`", "")
    s = " ".join(s.split())
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

# FFC also hands us bye weeks and real ADP dispersion for free.
BYE_N   = {norm(k): v.get("bye") for k, v in EXTRAS.items() if v.get("bye")}
STDEV_N = {norm(k): v.get("stdev") for k, v in EXTRAS.items() if v.get("stdev")}

COLUMNS = [("ffc", FFC_N), ("espn", ESPN_N),
           ("sleeper", SLEEPER_N), ("yahoo", YAHOO_N)]

if __name__ == "__main__":
    for k, v in NOTES.items():
        print(f"{k:8} {v}")
