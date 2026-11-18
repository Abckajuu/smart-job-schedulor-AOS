# Smart Job Scheduler

A CPU scheduling simulator built for an Advanced Operating Systems project. It runs entirely in the browser with plain HTML, CSS and JavaScript.

## Features

- Add jobs with arrival time, burst time and priority, or load sample and random workloads
- Eight algorithms: FCFS, SJF, SRTF, Priority (non-preemptive and preemptive), Round Robin, HRRN, and Smart MLFQ with aging
- Animated Gantt chart that shows idle time
- Per-job waiting, turnaround and response times, plus averages, CPU utilisation, throughput and context switches
- Compare all algorithms on one workload and get a recommendation

## The "smart" scheduler

Smart MLFQ + aging uses three queues. Every job starts at the top level with the base time quantum. A job that uses up its slice drops one level and gets double the quantum. A job that waits 15 ticks or more is promoted one level (aging), so long jobs cannot starve. A higher-level job preempts a lower-level one.

The recommender runs every algorithm on your workload, ranks them by average waiting time (ties go to fewer context switches), and explains the choice using the spread of burst times.

## Run it

Open `index.html` in a browser. No build step.

To publish with GitHub Pages: push the repo, then go to Settings, Pages, and choose the `main` branch root.

## Project layout

```
index.html   page structure
style.css    layout and theme (light and dark)
script.js    scheduling engine and UI
```

## How the engine works

`simulate(jobs, algo, quantum)` advances a clock one tick at a time. On each tick it adds arrivals, applies the algorithm's pick rule (and preemption rule where relevant), runs one unit of work, and records Gantt segments. Metrics are then derived:

- Turnaround = finish - arrival
- Waiting = turnaround - burst
- Response = first start - arrival

## Ideas to extend

- Multi-core scheduling
- I/O bursts and blocked states
- Export results as CSV
- Real-time scheduling (EDF, Rate Monotonic)
