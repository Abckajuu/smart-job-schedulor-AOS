"""Charts for your report (needs matplotlib).

    python plot_results.py gantt --algo smart
    python plot_results.py compare --kind mixed --runs 200
Images are saved as PNG files in the current folder.
"""
import argparse

import matplotlib
matplotlib.use("Agg")  # save to file, no display needed
import matplotlib.pyplot as plt

from compare import run_experiment
from scheduler import ALGOS, SAMPLE_JOBS, make_jobs, simulate
from workloads import KINDS


def plot_gantt(jobs, algo, quantum, path):
    r = simulate(jobs, algo, quantum)
    ids = [j.id for j in jobs]
    cmap = plt.get_cmap("tab10")
    fig, ax = plt.subplots(figsize=(10, 1.2 + 0.4 * len(ids)))
    for pid, s, e in r.gantt:
        if pid is None:
            continue
        ax.barh(ids.index(pid), e - s, left=s, color=cmap(ids.index(pid) % 10), edgecolor="white")
    ax.set_yticks(range(len(ids)), ids)
    ax.invert_yaxis()
    ax.set_xlabel("Time")
    ax.set_title(f"{ALGOS[algo]}: avg waiting {r.avg_wt:.2f}, {r.switches} context switches")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    print(f"Saved {path}")


def plot_compare(kind, runs, n, quantum, path):
    stats = run_experiment(kind, runs, n, quantum)
    order = sorted(stats, key=lambda k: stats[k]["wt"])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.5))
    a1.barh([ALGOS[k] for k in order], [stats[k]["wt"] for k in order], color="#2748d8")
    a1.invert_yaxis()
    a1.set_xlabel("Average waiting time")
    a2.barh([ALGOS[k] for k in order], [stats[k]["switches"] for k in order], color="#0b7a54")
    a2.invert_yaxis()
    a2.set_yticklabels([])
    a2.set_xlabel("Average context switches")
    fig.suptitle(f"{runs} random '{kind}' workloads of {n} jobs, quantum {quantum}")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    print(f"Saved {path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Plot scheduler results")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gantt")
    g.add_argument("--algo", default="smart", choices=ALGOS)
    g.add_argument("--quantum", type=int, default=3)
    c = sub.add_parser("compare")
    c.add_argument("--kind", default="mixed", choices=KINDS)
    c.add_argument("--runs", type=int, default=100)
    c.add_argument("--jobs", type=int, default=10)
    c.add_argument("--quantum", type=int, default=3)
    a = ap.parse_args()
    if a.cmd == "gantt":
        plot_gantt(make_jobs(SAMPLE_JOBS), a.algo, a.quantum, f"gantt_{a.algo}.png")
    else:
        plot_compare(a.kind, a.runs, a.jobs, a.quantum, f"compare_{a.kind}.png")
