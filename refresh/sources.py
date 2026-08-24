"""Fetch public half-PPR draft ADP from three free, no-auth sources.

Replaces the old hand-pasted FantasyPros ECR and Flock Fantasy exports, which were
paid products. Everything here is a public endpoint that returns JSON without a key.

  FFC     fantasyfootballcalculator.com -- REAL half-PPR 12-team ADP from public
          mock drafts. This is the only source whose format exactly matches the
          league (half PPR, 12 teams), so it is the anchor.
  ESPN    ESPN's real ADP (ownership.averageDraftPosition), not their editorial
          board -- that board's STANDARD and PPR variants are byte-identical.
  YAHOO   Yahoo's public draft-analysis feed -- average_pick across their drafts,
          where the default league scoring is 0.5/reception.

Every column is real ADP from real drafts. Sleeper is still fetched, but only for
the trending signal: `search_rank` is search popularity, not draft position, and
Sleeper publishes no ADP anywhere. See fetch_mfl for why MyFantasyLeague is out.

Results are cached to pubranks_cache.json (gitignored) so a draft-day rebuild still
works without a network, and so repeated builds don't hammer anyone's API.
"""
import json, pathlib, sys, time, urllib.request, urllib.error

HERE = pathlib.Path(__file__).parent
CACHE = HERE / "pubranks_cache.json"
TTL = 6 * 3600          # refetch at most every 6 hours
UA = {"User-Agent": "sleeper-draft-guide/1.0 (personal fantasy draft board)"}


def _get(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


# ---------------------------------------------------------------- sources ---
def fetch_ffc(year):
    """Half-PPR, 12-team ADP from real public mock drafts. Format-exact."""
    d = _get(f"https://fantasyfootballcalculator.com/api/v1/adp/half-ppr"
             f"?teams=12&year={year}")
    meta = d.get("meta", {})
    out = {p["name"]: p["adp"] for p in d["players"] if p.get("adp")}
    extra = {p["name"]: {"bye": p.get("bye"), "stdev": p.get("stdev"),
                         "high": p.get("high"), "low": p.get("low"),
                         "pos": p.get("position"), "team": p.get("team")}
             for p in d["players"]}
    note = (f"{meta.get('total_drafts','?')} drafts, "
            f"{meta.get('start_date','?')}..{meta.get('end_date','?')}")
    return out, note, extra


def fetch_espn(year):
    """ESPN's real ADP from ESPN drafts (ownership.averageDraftPosition).

    Deliberately NOT draftRanksByRankType: that is a generic editorial board, and
    ESPN's STANDARD and PPR variants of it are byte-identical, so it carries no
    format information at all. averageDraftPosition is what people actually did.
    """
    filt = json.dumps({"players": {"limit": 400, "sortDraftRanks": {
        "sortPriority": 100, "sortAsc": True, "value": "PPR"}}})
    d = _get(f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/"
             f"{year}/segments/0/leaguedefaults/3?view=kona_player_info",
             headers={"x-fantasy-filter": filt, "accept": "application/json"})
    out = {}
    for p in d.get("players", []):
        pp = p.get("player", p)
        adp = (pp.get("ownership") or {}).get("averageDraftPosition")
        nm = pp.get("fullName")
        if nm and adp and adp > 0:
            out[nm] = float(adp)
    return out, f"{len(out)} with ADP", {}


def fetch_sleeper(_year):
    """Sleeper's public player dump. search_rank is their draft-room ordering."""
    d = _get("https://api.sleeper.app/v1/players/nfl", timeout=90)
    out = {}
    for v in d.values():
        if not v.get("active"):
            continue
        if v.get("position") not in ("QB", "RB", "WR", "TE", "K", "DEF"):
            continue
        r, nm = v.get("search_rank"), v.get("full_name") or v.get("last_name")
        # Sleeper parks unranked players at a sentinel far past any draft
        if nm and r is not None and r < 2000:
            out[nm] = min(r, out.get(nm, r))
    return out, f"{len(out)} ranked", {}


def fetch_yahoo(_year):
    """Yahoo's public draft-analysis feed, paged 50 at a time."""
    out = {}
    for start in range(0, 300, 50):
        try:
            d = _get("https://pub-api-ro.fantasysports.yahoo.com/fantasy/v2/game/"
                     f"nfl/players;position=ALL;start={start};count=50;"
                     "sort=rank_season/draft_analysis?format=json_f",
                     headers={"accept": "application/json"})
        except urllib.error.HTTPError:
            break
        found = 0
        for p in _yahoo_players(d):
            nm = (p.get("name") or {}).get("full")
            ap = (p.get("draft_analysis") or {}).get("average_pick")
            if nm and ap:
                try:
                    out[nm] = float(ap)
                    found += 1
                except ValueError:
                    pass
        if not found:
            break
        time.sleep(0.4)          # be polite to a free endpoint
    return out, f"{len(out)} with ADP", {}


def _yahoo_players(node):
    """Yahoo nests players irregularly; walk for dicts that look like a player."""
    stack = [node]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            if "draft_analysis" in o and "name" in o:
                yield o
            stack.extend(o.values())
        elif isinstance(o, list):
            stack.extend(o)


def fetch_trending(_year):
    """Sleeper's public trending-adds feed over the past week.

    Not a ranking -- a momentum signal. A player being added in volume right now
    is a player whose ADP is stale and who will go earlier than his board rank
    says. That is exactly the situation where you either reach a round early or
    lose him, so it is worth seeing next to the ranks.
    """
    trend = _get("https://api.sleeper.app/v1/players/nfl/trending/add"
                 "?lookback_hours=168&limit=200")
    ids = _get("https://api.sleeper.app/v1/players/nfl", timeout=90)
    out = {}
    for t in trend:
        v = ids.get(str(t.get("player_id")))
        if not v:
            continue
        nm = v.get("full_name") or v.get("last_name")
        if nm and t.get("count"):
            out[nm] = int(t["count"])
    return out, f"{len(out)} trending", {}


def fetch_mfl(year):
    """MyFantasyLeague ADP. NOT USED -- kept only so nobody re-adds it blind.

    MFL's ADP endpoint has no way to exclude superflex / 2QB drafts, and their
    pool is full of them. Measured against FFC on the 2026 board, MFL's QBs went
    an average of 38 slots EARLIER (Josh Allen 3rd overall vs FFC's 33rd) while
    its RBs and WRs went 7 and 20 slots later. That is superflex contamination,
    and it would wreck QB ranking in this 1QB league. IS_PPR=1 filters scoring,
    not roster format, so there is no fix on their side.
    """
    d = _get(f"https://api.myfantasyleague.com/{year}/export"
             "?TYPE=adp&FCOUNT=12&IS_PPR=1&IS_MOCK=-1&IS_KEEPER=N&JSON=1")
    adp = d["adp"]
    rows = adp["player"]
    names = _get(f"https://api.myfantasyleague.com/{year}/export?TYPE=players&JSON=1",
                 timeout=60)["players"]["player"]
    idx = {p["id"]: p for p in names}
    out = {}
    for r in rows:
        p = idx.get(r.get("id"))
        ap = r.get("averagePick")
        if not p or not ap:
            continue
        raw = p.get("name", "")
        if p.get("position") == "Def":
            nm = raw.replace(",", " ").strip() + " Defense"   # "Texans, Houston"
        elif "," in raw:
            last, first = [t.strip() for t in raw.split(",", 1)]
            nm = f"{first} {last}"
        else:
            nm = raw.strip()
        if nm:
            out[nm] = float(ap)
    return out, f"{adp.get('totalDrafts','?')} drafts", {}


SOURCES = [("ffc", fetch_ffc), ("espn", fetch_espn), ("yahoo", fetch_yahoo),
           ("trending", fetch_trending)]

# Every ranking column is now REAL ADP from real drafts. Sleeper was dropped as a
# column -- search_rank is search popularity, not draft position, and Sleeper
# publishes no ADP anywhere -- but is still fetched for the trending signal.
RANK_SOURCES = ("ffc", "espn", "yahoo")


# ------------------------------------------------------------------ cache ---
def load(year=2026, refresh=False, quiet=False):
    """Return {source: {name: adp_or_rank}} plus notes and FFC extras.

    Falls back to cache per-source on any network failure, so a build on draft
    day never dies because someone's API is having a bad afternoon.
    """
    cache = {}
    if CACHE.exists():
        try:
            cache = json.loads(CACHE.read_text())
        except json.JSONDecodeError:
            cache = {}

    fresh = (not refresh and cache.get("fetched_at", 0) > time.time() - TTL)
    data, notes = {}, {}
    extras = cache.get("extras", {})

    for key, fn in SOURCES:
        if fresh and key in cache.get("data", {}):
            data[key] = cache["data"][key]
            notes[key] = cache.get("notes", {}).get(key, "cached") + " (cached)"
            continue
        try:
            got, note, extra = fn(year)
            floor = 50 if key in RANK_SOURCES else 10
            if len(got) < floor:
                raise ValueError(f"only {len(got)} rows -- looks broken")
            data[key], notes[key] = got, note
            if extra:
                extras = extra
        except Exception as e:                     # noqa: BLE001 - any failure falls back
            stale = cache.get("data", {}).get(key)
            if stale:
                data[key] = stale
                notes[key] = f"FETCH FAILED ({type(e).__name__}) -- using cache"
            else:
                notes[key] = f"FETCH FAILED ({type(e).__name__}) -- NO CACHE, dropped"
        if not quiet:
            print(f"  {key:8} {len(data.get(key, {})):4} {notes[key]}")

    if any(k in data for k, _ in SOURCES):
        CACHE.write_text(json.dumps(
            {"fetched_at": time.time(), "data": data, "notes": notes,
             "extras": extras}))
    return data, notes, extras


if __name__ == "__main__":
    print("fetching public half-PPR rankings...")
    d, n, x = load(refresh="--refresh" in sys.argv)
    print(f"\n{len(d)} sources, {len(x)} FFC extras")
