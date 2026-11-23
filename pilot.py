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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", choices=DEMOS)
    parser.add_argument("--seed", type=int, default=491)
    args = parser.parse_args()
    print(json.dumps(DEMOS[args.skill](*split(args.seed)), indent=2))


if __name__ == "__main__":
    main()
