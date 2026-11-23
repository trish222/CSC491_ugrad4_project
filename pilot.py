"""AI-authored development pilot for the CSC 491 shrinking-code project."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from random import Random
from statistics import mean, median


DATA = Path(__file__).parent / "data" / "nasa93dem.csv"
GOALS = ("Kloc+", "Effort-", "Defects-")
DEMOS = {}


def load():
    with DATA.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    return [
        {key: float(value) if key in GOALS else value.strip()
         for key, value in row.items()}
        for row in rows
    ]


def distance(a, b, exclude=()):
    features = [key for key in a if key.islower() and key not in exclude
                and a[key] != "?" and b[key] != "?"]
    return mean(a[key] != b[key] for key in features) if features else 1.0


def peers(proposal, history, count=5):
    return sorted(history, key=lambda row: distance(proposal, row))[:count]


def typical(rows):
    return {key: median(row[key] for row in rows) for key in GOALS}


def score(row, history, weights=(1, 1, 1)):
    gaps = []
    for key, weight in zip(GOALS, weights):
        low = min(other[key] for other in history)
        high = max(other[key] for other in history)
        ideal = high if key.endswith("+") else low
        gaps.append(weight * abs(row[key] - ideal) / (high - low or 1))
    return max(gaps)


def demo(function):
    DEMOS[function.__name__] = function
    return function


@demo
def remember(history, test):
    best = sorted(history, key=lambda row: score(row, history))[:5]
    return {"strong_projects": [row["idX"] for row in best],
            "typical_near_proposal": typical(peers(test[0], history))}


def split(seed):
    rows = load()
    Random(seed).shuffle(rows)
    holdout_ids = {row["idX"] for row in rows[:20]}
    history = [row for row in rows if row["idX"] not in holdout_ids]
    holdout = [row for row in rows if row["idX"] in holdout_ids]
    return history, holdout


@demo
def guess(history, test):
    estimate = typical(peers(test[0], history))
    return {"effort_person_months": estimate["Effort-"],
            "defects": estimate["Defects-"]}



def matched_comparison(history, feature, goal):
    levels = ("vl", "l", "n", "h", "vh", "xh")
    high = [row for row in history if row[feature] in levels[3:]]
    low = [row for row in history if row[feature] in levels[:3]]
    gaps = []
    for row in high:
        if not low:
            break
        peer = min(low, key=lambda other: distance(row, other, (feature,)))
        low.remove(peer)
        gaps.append(row[goal] - peer[goal])
    wins = sum(gap < 0 for gap in gaps)
    losses = sum(gap > 0 for gap in gaps)
    from math import comb
    total = wins + losses
    p = min(1.0, 2 * sum(comb(total, i) for i in range(min(wins, losses) + 1))
            / (2 ** total))
    return {"pairs": len(gaps), "median_difference": median(gaps) if gaps else None,
            "sign_test_p": p, "evidence_of_lower_outcome": wins > losses and p <= 0.025}


@demo
def certify(history, test):
    return {"analyst_capability": matched_comparison(history, "acap", "Effort-"),
            "tool_support": matched_comparison(history, "tool", "Defects-")}



@demo
def flow(history, test):
    targets = typical(history)
    total = 0
    results = []
    for row in test:
        estimate = guess(history, [row])
        total += (row["Effort-"] <= targets["Effort-"]
                  and row["Defects-"] <= targets["Defects-"])
        results.append({"project": row["idX"], "met_targets_so_far": total,
                        "budget_alert": estimate["effort_person_months"] > targets["Effort-"]})
    return {"targets": targets, "arrivals": results}



def residual(row, history, goal):
    return row[goal] - typical(peers(row, history))[goal]


@demo
def blame(history, test):
    worst_effort = max(test, key=lambda row: residual(row, history, "Effort-"))
    effort_peers = peers(worst_effort, history)
    large_defects = sorted(test, key=lambda row: residual(row, history, "Defects-"))[-5:]
    return {"effort_project": worst_effort["idX"],
            "effort_differences": {key: worst_effort[key] for key in worst_effort
                                   if key.islower() and all(
                                       p[key] != worst_effort[key] for p in effort_peers)},
            "frequent_conditions_for_defect_outliers": Counter(
                f"{key}={row[key]}" for row in large_defects for key in row
                if key.islower() and row[key] != "?").most_common(8)}



@demo
def justify(history, test):
    budget = typical(history)["Effort-"]
    ranked = sorted(test, key=lambda row: guess(history, [row])["effort_person_months"])
    low = [row for row in ranked if guess(history, [row])["effort_person_months"] <= budget]
    high = [row for row in ranked if guess(history, [row])["effort_person_months"] > budget]
    pair = min(((a, b) for a in low for b in high),
               key=lambda ab: distance(*ab), default=None)
    rows = [test[0], *pair] if pair else [test[0]]
    return {"budget": budget, "opposite_ratings_found": pair is not None, "evidence": [
        {"project": row["idX"], "estimate": guess(history, [row]),
         "past_projects": [{"id": p["idX"], "effort": p["Effort-"]}
                           for p in peers(row, history)]}
        for row in rows]}



def shortlist(history, proposals, budget, weights):
    return sorted(proposals, key=lambda row: score(typical(peers(row, history)),
                                                   history, weights))[:budget]


@demo
def choose(history, test):
    return {label: [row["idX"] for row in shortlist(history, test, 4, weights)]
            for label, weights in {"effort_and_defects": (0, 1, 1),
                                   "defects_first": (0, 0.25, 1)}.items()}



@demo
def fix(history, test):
    proposal = test[0]
    levels = ("vl", "l", "n", "h", "vh", "xh")
    options = []
    for feature in ("tool", "pmat", "docu"):
        old = proposal[feature]
        observed = {row[feature] for row in history}
        if old in levels:
            for new in observed.intersection(levels[levels.index(old) + 1:]):
                options.append((levels.index(new) - levels.index(old), feature, new,
                                guess(history, [dict(proposal, **{feature: new})])))
    baseline = guess(history, [proposal])
    targets = typical(history)
    result = {"baseline": baseline}
    for metric, goal in (("effort_person_months", "Effort-"), ("defects", "Defects-")):
        feasible = [option for option in options if
                    option[3][metric] <= targets[goal] and option[3][metric] < baseline[metric]]
        result[metric] = min(feasible, default=None,
                             key=lambda option: (option[0], option[3][metric], option[1]))
    return result



@demo
def spot(history, test):
    far = sorted(test, key=lambda row: distance(row, peers(row, history, 1)[0]),
                 reverse=True)
    unusual = sorted(test, key=lambda row: abs(residual(row, history, "Defects-")),
                     reverse=True)
    return {"proposals_to_review": [row["idX"] for row in far[:3]],
            "records_to_double_check": [row["idX"] for row in unusual[:3]]}



@demo
def race(history, test):
    targets = typical(history)
    reviewed = shortlist(history, test, 4, (0, 1, 1))
    random_four = Random(491).sample(test, 4)
    return {"effort_mae": {
                "peer_estimate": mean(abs(residual(row, history, "Effort-")) for row in test),
                "typical_effort": mean(abs(row["Effort-"] - targets["Effort-"]) for row in test)},
            "review_budget": 4, "hits": {
                label: sum(row["Effort-"] <= targets["Effort-"]
                           and row["Defects-"] <= targets["Defects-"] for row in rows)
                for label, rows in {"shortlist": reviewed, "random": random_four}.items()}}



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", choices=DEMOS)
    parser.add_argument("--seed", type=int, default=491)
    args = parser.parse_args()
    print(json.dumps(DEMOS[args.skill](*split(args.seed)), indent=2))


if __name__ == "__main__":
    main()
