"""Compare all algorithms over many random workloads and export the averages.

    python compare.py --kind mixed --runs 200 --jobs 10 --csv results.csv
"""
import argparse
import csv

from scheduler import ALGOS, make_jobs, simulate
from workloads import KINDS, generate


def run_experiment(kind="mixed", runs=100, n=10, quantum=3, seed=42):
    """Return {algo: {metric: average over all runs}}."""
    totals = {k: {"wt": 0.0, "tat": 0.0, "rt": 0.0, "switches": 0.0, "util": 0.0} for k in ALGOS}
    wins = {k: 0 for k in ALGOS}
    for i in range(runs):
        jobs = make_jobs(generate(kind, n, seed + i))
        results = {k: simulate(jobs, k, quantum) for k in ALGOS}
        wins[min(results, key=lambda k: results[k].avg_wt)] += 1
        for k, r in results.items():
            t = totals[k]
            t["wt"] += r.avg_wt
            t["tat"] += r.avg_tat
            t["rt"] += r.avg_rt
            t["switches"] += r.switches
            t["util"] += r.util
    out = {k: {m: v / runs for m, v in t.items()} for k, t in totals.items()}
    for k in out:
        out[k]["wins"] = wins[k]
    return out


def print_table(stats):
    print(f"{'Algorithm':<28}{'Wait':>8}{'TAT':>8}{'Resp':>8}{'Switches':>10}{'Wins':>6}")
    for k, s in sorted(stats.items(), key=lambda kv: kv[1]["wt"]):
        print(f"{ALGOS[k]:<28}{s['wt']:>8.2f}{s['tat']:>8.2f}{s['rt']:>8.2f}{s['switches']:>10.1f}{s['wins']:>6}")


def save_csv(stats, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["algorithm", "avg_wait", "avg_turnaround", "avg_response", "avg_switches", "wins"])
        for k, s in stats.items():
            w.writerow([ALGOS[k], round(s["wt"], 3), round(s["tat"], 3), round(s["rt"], 3),
                        round(s["switches"], 2), s["wins"]])


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Batch algorithm comparison")
    ap.add_argument("--kind", default="mixed", choices=KINDS)
    ap.add_argument("--runs", type=int, default=100)
    ap.add_argument("--jobs", type=int, default=10)
    ap.add_argument("--quantum", type=int, default=3)
    ap.add_argument("--csv", help="optional path to save results")
    a = ap.parse_args()
    stats = run_experiment(a.kind, a.runs, a.jobs, a.quantum)
    print(f"{a.runs} runs of {a.jobs} '{a.kind}' jobs, quantum {a.quantum}\n")
    print_table(stats)
    if a.csv:
        save_csv(stats, a.csv)
        print(f"\nSaved {a.csv}")
