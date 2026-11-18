"""Generate job workloads and save them as JSON or CSV.

    python workloads.py --kind mixed --jobs 10 --seed 1 --out jobs.json
"""
import argparse
import csv
import json
import random

KINDS = {
    "uniform": "burst times spread evenly between 1 and 12",
    "short":   "mostly short interactive jobs",
    "mixed":   "many short jobs plus a few long CPU-bound ones",
    "bursty":  "jobs arrive in tight clusters with idle gaps between them",
}


def generate(kind="uniform", n=8, seed=None):
    """Return a list of (arrival, burst, priority) tuples."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {list(KINDS)}")
    rng = random.Random(seed)
    jobs = []
    for i in range(n):
        if kind == "uniform":
            at, bt = rng.randint(0, 15), rng.randint(1, 12)
        elif kind == "short":
            at, bt = rng.randint(0, 20), rng.randint(1, 4)
        elif kind == "mixed":
            at = rng.randint(0, 15)
            bt = rng.randint(15, 30) if rng.random() < 0.2 else rng.randint(1, 5)
        else:  # bursty
            at = (i // 3) * 25 + rng.randint(0, 3)
            bt = rng.randint(2, 9)
        jobs.append((at, bt, rng.randint(1, 5)))
    return sorted(jobs)


def save_json(jobs, path):
    with open(path, "w") as f:
        json.dump([{"at": a, "bt": b, "pr": p} for a, b, p in jobs], f, indent=2)


def save_csv(jobs, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["arrival", "burst", "priority"])
        w.writerows(jobs)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Workload generator")
    ap.add_argument("--kind", default="uniform", choices=KINDS)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--out", default="jobs.json", help="ends in .json or .csv")
    a = ap.parse_args()
    data = generate(a.kind, a.jobs, a.seed)
    (save_csv if a.out.endswith(".csv") else save_json)(data, a.out)
    print(f"Wrote {len(data)} jobs ({KINDS[a.kind]}) to {a.out}")
