"""Build the alternate board for Dad's 10-team scoring and 18-player roster.

Public half-PPR sources remain useful for draft timing, but the unusual league
model receives 65% of the final blend.
"""
import copy
import json
import statistics

TEAMS = 10
MODEL_WEIGHT = 0.65
RELIABILITY = {"K": 0.15, "DST": 0.30}
# 18 rounds: wait until round 15 for DST and round 17 for K.
FLOOR = {"DST": 141, "K": 161}

rows = copy.deepcopy(json.load(open("board_out.json")))
scores = json.load(open("dad_pts.json"))

for x in rows:
    part = scores.get(x.get("key", x["p"]))
    x["dad_parts"] = part
    x["tot"] = part["total"] if part else None
    x["bonus"] = ((part["yard_buckets"] + part["reception_buckets"])
                  if part else 0.0)
    x["profile"] = "dad"

    # Dad's league needs public data for draft timing, not as a scoring oracle.
    # Use the median of three half-PPR market signals so one unusual platform
    # cannot define the headline number by itself (Bowers: 45 / 21 / 21 -> 21).
    market_inputs = [x.get(k) for k in ("ffcr", "yahoor", "fcalcr")
                     if x.get(k) is not None]
    x["market"] = (round(statistics.median(market_inputs), 1)
                   if market_inputs else None)
    x["market_n"] = len(market_inputs)
    expert = x.get("expert_lane")
    if x["market"] is not None and expert is not None:
        x["anchor"] = round(0.70 * x["market"] + 0.30 * expert, 1)
    elif x["market"] is not None:
        x["anchor"] = x["market"]
    elif expert is not None:
        x["anchor"] = expert
    x["avg"] = x["anchor"]
    lane_values = market_inputs + ([expert] if expert is not None else [])
    x["spread"] = (round(max(lane_values) - min(lane_values), 1)
                   if len(lane_values) >= 2 else 0)

have = [x for x in rows if x["tot"] is not None]


def top(pos, count):
    return sorted([x for x in have if x["pos"] == pos],
                  key=lambda z: -z["tot"])[:count]


# QB, 2RB, 2WR, TE, two unrestricted RB/WR/TE flexes, K, DST.
taken = {id(x) for pos, count in (("QB", TEAMS), ("RB", 2 * TEAMS),
                                  ("WR", 2 * TEAMS), ("TE", TEAMS),
                                  ("K", TEAMS), ("DST", TEAMS))
         for x in top(pos, count)}
flex = [x for x in have if id(x) not in taken and x["pos"] in ("RB", "WR", "TE")]
taken |= {id(x) for x in sorted(flex, key=lambda z: -z["tot"])[:2 * TEAMS]}

replacement = {}
for pos in ("QB", "RB", "WR", "TE", "K", "DST"):
    rest = sorted([x for x in have if x["pos"] == pos and id(x) not in taken],
                  key=lambda z: -z["tot"])
    replacement[pos] = rest[0]["tot"] if rest else 0.0

for x in rows:
    x["vor"] = (round(x["tot"] - replacement[x["pos"]], 1)
                if x["tot"] is not None else None)
    if x["vor"] is not None and x["pos"] in RELIABILITY:
        x["vor_raw"] = x["vor"]
        x["vor"] = round(x["vor"] * RELIABILITY[x["pos"]], 1)

model_rows = sorted([x for x in rows if x["vor"] is not None], key=lambda z: -z["vor"])
for i, x in enumerate(model_rows, 1):
    x["model"] = i

curve = sorted([x["vor"] for x in rows if x["vor"] is not None], reverse=True)


def outside_value(rank):
    i = int(round(rank)) - 1
    return curve[max(0, min(len(curve) - 1, i))]


for x in rows:
    mv = outside_value(x["anchor"])
    x["mktvor"] = round(mv, 1)
    if x["pos"] in FLOOR:
        x["blend"] = round(outside_value(max(x["anchor"], FLOOR[x["pos"]])), 1)
    elif x["vor"] is not None:
        x["blend"] = round(MODEL_WEIGHT * x["vor"] + (1 - MODEL_WEIGHT) * mv, 1)
    else:
        x["blend"] = round(mv, 1)
    x["final"] = x["blend"]

rows.sort(key=lambda z: -z["final"])

# Insert only one draftable K and DST per team, interleaved with bench fliers.
skill = [x for x in rows if x["pos"] not in FLOOR]
late = {p: [x for x in rows if x["pos"] == p] for p in FLOOR}
rows = list(skill)
tail = []
for pos in sorted(FLOOR, key=lambda p: FLOOR[p]):
    group = late[pos]
    for i, x in enumerate(group[:TEAMS]):
        rows.insert(min(len(rows), FLOOR[pos] - 1 + i * 2), x)
    tail.extend(group[TEAMS:])
rows.extend(tail)

for i, x in enumerate(rows, 1):
    x["rk"] = i
    x["gap"] = round(x["anchor"] - i) if x["nsrc"] else None
    tag = ""
    if x.get("inj") in {"IR", "PUP", "Out", "Sus", "NA", "DNR", "Doubtful"}:
        tag = ""
    elif x["pos"] not in ("K", "DST"):
        if x.get("ffcr") and x["ffcr"] - i >= 25 and i >= 75:
            tag = "SLEEPER"
        elif x["nsrc"] >= 2 and x["gap"] is not None and x["gap"] >= 18:
            tag = "VALUE"
        elif x["nsrc"] >= 2 and x["gap"] is not None and x["gap"] <= -18:
            tag = "FADE"
    x["tag2"] = tag


def tier(seq, gap, cap):
    number, run = 1, 0
    for i, x in enumerate(seq):
        if i and (seq[i - 1]["final"] - x["final"] >= gap or run >= cap):
            number, run = number + 1, 0
        x["_tier"] = number
        run += 1


tier(rows, 8, 10)
for x in rows:
    x["otier"] = x.pop("_tier")
for pos in ("QB", "RB", "WR", "TE", "K", "DST"):
    group = [x for x in rows if x["pos"] == pos]
    tier(group, 6, 7)
    for x in group:
        x["ptier"] = x.pop("_tier")

json.dump(rows, open("dad_board_out.json", "w"))
print("Dad profile replacement:", {k: round(v, 1) for k, v in replacement.items()})
print("Dad profile top 12:", ", ".join(f"{x['rk']} {x['p']}" for x in rows[:12]))
