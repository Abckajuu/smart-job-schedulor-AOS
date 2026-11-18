"""Unit tests. Run with:  python -m unittest -v   (from this folder)"""
import unittest

from scheduler import ALGOS, make_jobs, simulate
from workloads import KINDS, generate


def waits(r):
    return [x["wt"] for x in r.rows]


class TextbookAnswers(unittest.TestCase):
    def test_fcfs(self):
        r = simulate(make_jobs([(0, 5, 1), (1, 3, 1), (2, 8, 1), (3, 6, 1)]), "fcfs")
        self.assertEqual(waits(r), [0, 4, 6, 13])
        self.assertAlmostEqual(r.avg_wt, 5.75)

    def test_sjf_non_preemptive(self):
        r = simulate(make_jobs([(0, 5, 1), (1, 3, 1), (2, 8, 1), (3, 6, 1)]), "sjf")
        self.assertEqual(waits(r), [0, 4, 12, 5])
        self.assertAlmostEqual(r.avg_wt, 5.25)

    def test_srtf(self):
        r = simulate(make_jobs([(0, 8, 1), (1, 4, 1), (2, 9, 1), (3, 5, 1)]), "srtf")
        self.assertEqual(waits(r), [9, 0, 15, 2])
        self.assertAlmostEqual(r.avg_wt, 6.5)

    def test_round_robin(self):
        r = simulate(make_jobs([(0, 24, 1), (0, 3, 1), (0, 3, 1)]), "rr", 4)
        self.assertEqual(waits(r), [6, 4, 7])
        self.assertAlmostEqual(r.avg_wt, 17 / 3)

    def test_priority_non_preemptive(self):
        r = simulate(make_jobs([(0, 10, 3), (0, 1, 1), (0, 2, 4), (0, 1, 5), (0, 5, 2)]), "prio")
        self.assertEqual(waits(r), [6, 0, 16, 18, 1])
        self.assertAlmostEqual(r.avg_wt, 8.2)

    def test_priority_preemptive(self):
        r = simulate(make_jobs([(0, 5, 3), (1, 2, 1)]), "prioP")
        self.assertEqual(r.rows[1]["start"], 1)     # urgent job takes the CPU at once
        self.assertEqual(r.rows[1]["ft"], 3)
        self.assertEqual(r.rows[0]["ft"], 7)


class Behaviour(unittest.TestCase):
    def test_idle_gap_is_recorded(self):
        r = simulate(make_jobs([(0, 2, 1), (5, 2, 1)]), "fcfs")
        self.assertIn((None, 2, 5), r.gantt)
        self.assertAlmostEqual(r.util, 4 / 7 * 100)

    def test_smart_mlfq_demotes_long_job(self):
        # P1 is long, so it drops a level and short P2 finishes first.
        r = simulate(make_jobs([(0, 20, 1), (3, 2, 1)]), "smart", 2)
        by_id = {x["id"]: x for x in r.rows}
        self.assertLess(by_id["P2"]["ft"], by_id["P1"]["ft"])

    def test_smart_mlfq_aging_prevents_starvation(self):
        # A steady stream of short jobs must not push the long job back forever.
        stream = [(i * 2, 2, 1) for i in range(1, 40)]
        r = simulate(make_jobs([(0, 30, 1)] + stream), "smart", 2)
        self.assertEqual(r.rows[0]["ft"] is not None, True)

    def test_unknown_algorithm_rejected(self):
        with self.assertRaises(ValueError):
            simulate(make_jobs([(0, 1, 1)]), "nope")


class Invariants(unittest.TestCase):
    """Properties that must hold for every algorithm on every workload."""

    def test_all_algorithms_all_workloads(self):
        for kind in KINDS:
            for seed in range(15):
                jobs = make_jobs(generate(kind, 8, seed))
                total_burst = sum(j.bt for j in jobs)
                for algo in ALGOS:
                    r = simulate(jobs, algo, 3)
                    ran = sum(e - s for pid, s, e in r.gantt if pid)
                    self.assertEqual(ran, total_burst, f"{algo}/{kind}/{seed}")
                    for x in r.rows:
                        self.assertGreaterEqual(x["start"], x["at"])
                        self.assertGreaterEqual(x["ft"], x["at"] + x["bt"])
                        self.assertEqual(x["wt"], x["tat"] - x["bt"])
                        self.assertGreaterEqual(x["wt"], 0)

    def test_srtf_never_worse_than_sjf_on_average(self):
        for seed in range(30):
            jobs = make_jobs(generate("mixed", 8, seed))
            self.assertLessEqual(simulate(jobs, "srtf").avg_wt, simulate(jobs, "sjf").avg_wt + 1e-9)


if __name__ == "__main__":
    unittest.main()
