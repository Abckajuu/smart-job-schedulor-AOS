"""CPU scheduling engine: a Python port of simulate() in ../script.js.

Run from the command line:
    python scheduler.py --algo smart --quantum 3
    python scheduler.py --algo all --jobs jobs.json
"""
import argparse
import json
import sys
from dataclasses import dataclass, field

ALGOS = {
    "fcfs": "FCFS",
    "sjf": "SJF (non-preemptive)",
    "srtf": "SRTF (preemptive SJF)",
    "prio": "Priority (non-preemptive)",
    "prioP": "Priority (preemptive)",
    "rr": "Round Robin",
    "hrrn": "HRRN",
    "smart": "Smart MLFQ + aging",
}
AGING_LIMIT = 15  # ticks a job may wait before promotion in MLFQ
MAX_LEVEL = 2

SAMPLE_JOBS = [(0, 8, 3), (1, 4, 1), (2, 9, 4), (3, 5, 2), (20, 3, 1), (22, 6, 2)]


@dataclass
class Job:
    id: str
    at: int          # arrival time
    bt: int          # burst time
    pr: int = 1      # priority (lower number = higher priority)
    rem: int = field(default=0, repr=False)
    start: int = field(default=None, repr=False)
    ft: int = field(default=None, repr=False)
    lvl: int = field(default=0, repr=False)
    since: int = field(default=0, repr=False)


@dataclass
class Result:
    gantt: list      # [(pid or None, start, end), ...]
    rows: list       # per-job metric dicts
    switches: int
    avg_wt: float
    avg_tat: float
    avg_rt: float
    util: float
    throughput: float
    total: int


def make_jobs(triples):
    """Build jobs from (arrival, burst, priority) tuples, named P1, P2, ..."""
    return [Job(f"P{i + 1}", a, b, p) for i, (a, b, p) in enumerate(triples)]


def simulate(jobs, algo, quantum=3):
    if algo not in ALGOS:
        raise ValueError(f"Unknown algorithm: {algo}")
    if quantum < 1:
        raise ValueError("quantum must be 1 or more")
    P = [Job(j.id, j.at, j.bt, j.pr, rem=j.bt, since=j.at) for j in jobs]
    ready, gantt = [], []
    t = done = slice_used = switches = busy = 0
    cur, last_pid = None, None

    def pick_min(key):
        best = cur if cur in ready else ready[0]
        for p in ready:
            if key(p) < key(best):
                best = p
        return best

    def pick_non_preemptive():
        if algo == "fcfs":
            return ready[0]
        key = {
            "sjf": lambda p: p.bt,
            "prio": lambda p: p.pr,
            "hrrn": lambda p: -((t - p.at + p.bt) / p.bt),
        }[algo]
        best = ready[0]
        for p in ready:
            if key(p) < key(best):
                best = p
        return best

    def slice_for(p):
        return quantum * (2 ** p.lvl) if algo == "smart" else quantum

    while done < len(P):
        ready.extend(p for p in P if p.at == t)          # arrivals first

        if algo == "smart":                              # aging
            for p in ready:
                if p is not cur and p.lvl > 0 and t - p.since >= AGING_LIMIT:
                    p.lvl -= 1
                    p.since = t

        if ready:
            if algo == "srtf":
                cur = pick_min(lambda p: p.rem)
            elif algo == "prioP":
                cur = pick_min(lambda p: p.pr)
            elif algo == "rr":
                if cur and slice_used >= quantum:
                    ready.remove(cur)
                    ready.append(cur)
                    cur = None
                if not cur:
                    cur, slice_used = ready[0], 0
            elif algo == "smart":
                if cur and slice_used >= slice_for(cur):  # slice used: demote
                    cur.lvl = min(cur.lvl + 1, MAX_LEVEL)
                    cur.since = t
                    ready.remove(cur)
                    ready.append(cur)
                    cur = None
                top = ready[0]
                for p in ready:
                    if p.lvl < top.lvl:
                        top = p
                if cur is None or top.lvl < cur.lvl:
                    cur, slice_used = top, 0
            elif cur is None:
                cur = pick_non_preemptive()

        if cur is None:                                   # idle tick
            if gantt and gantt[-1][0] is None:
                gantt[-1] = (None, gantt[-1][1], t + 1)
            else:
                gantt.append((None, t, t + 1))
            t += 1
            continue

        if cur.start is None:
            cur.start = t
        if last_pid != cur.id:
            if last_pid is not None:
                switches += 1
            last_pid = cur.id
        if gantt and gantt[-1][0] == cur.id and gantt[-1][2] == t:
            gantt[-1] = (cur.id, gantt[-1][1], t + 1)
        else:
            gantt.append((cur.id, t, t + 1))

        cur.rem -= 1
        slice_used += 1
        busy += 1
        t += 1
        if cur.rem == 0:
            cur.ft = t
            done += 1
            ready.remove(cur)
            cur = None

    rows = [{
        "id": p.id, "at": p.at, "bt": p.bt, "start": p.start, "ft": p.ft,
        "tat": p.ft - p.at, "wt": p.ft - p.at - p.bt, "rt": p.start - p.at,
    } for p in P]
    n = len(rows)
    return Result(
        gantt=gantt, rows=rows, switches=switches,
        avg_wt=sum(r["wt"] for r in rows) / n,
        avg_tat=sum(r["tat"] for r in rows) / n,
        avg_rt=sum(r["rt"] for r in rows) / n,
        util=busy / t * 100, throughput=n / t, total=t,
    )


def format_gantt(gantt):
    line = "".join(f"| {g[0] or 'idle'} " for g in gantt) + "|"
    marks = "".join(f"{g[1]:<{len(g[0] or 'idle') + 3}}" for g in gantt) + str(gantt[-1][2])
    return line + "\n" + marks


def print_result(name, r):
    print(f"\n=== {name} ===")
    print(format_gantt(r.gantt))
    print(f"\n{'Job':<5}{'Arr':>5}{'Burst':>7}{'Start':>7}{'Finish':>8}{'Wait':>6}{'TAT':>6}{'Resp':>6}")
    for x in r.rows:
        print(f"{x['id']:<5}{x['at']:>5}{x['bt']:>7}{x['start']:>7}{x['ft']:>8}{x['wt']:>6}{x['tat']:>6}{x['rt']:>6}")
    print(f"\nAvg waiting {r.avg_wt:.2f} | Avg turnaround {r.avg_tat:.2f} | Avg response {r.avg_rt:.2f}")
    print(f"CPU use {r.util:.1f}% | Throughput {r.throughput:.2f} | Context switches {r.switches}")


def load_jobs(path):
    """JSON file: [{"at": 0, "bt": 5, "pr": 1}, ...]"""
    with open(path) as f:
        data = json.load(f)
    return make_jobs([(d["at"], d["bt"], d.get("pr", 1)) for d in data])


def main():
    ap = argparse.ArgumentParser(description="CPU scheduling simulator")
    ap.add_argument("--algo", default="smart", choices=[*ALGOS, "all"])
    ap.add_argument("--quantum", type=int, default=3)
    ap.add_argument("--jobs", help="JSON file of jobs (default: built-in sample)")
    args = ap.parse_args()
    try:
        jobs = load_jobs(args.jobs) if args.jobs else make_jobs(SAMPLE_JOBS)
        for key in (ALGOS if args.algo == "all" else [args.algo]):
            print_result(ALGOS[key], simulate(jobs, key, args.quantum))
    except (OSError, ValueError, KeyError) as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()
