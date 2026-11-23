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
    return rows[20:], rows[:20]


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



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", choices=DEMOS)
    parser.add_argument("--seed", type=int, default=491)
    args = parser.parse_args()
    print(json.dumps(DEMOS[args.skill](*split(args.seed)), indent=2))


if __name__ == "__main__":
    main()
