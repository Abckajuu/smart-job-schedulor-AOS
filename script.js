"use strict";

/* ---------------- Algorithm catalogue ---------------- */
const ALGOS = {
  fcfs:  { name: "FCFS",                      note: "First come, first served. Non-preemptive. Simple, but short jobs can get stuck behind long ones (convoy effect)." },
  sjf:   { name: "SJF (non-preemptive)",      note: "Runs the ready job with the shortest burst. Minimises average waiting time for non-preemptive scheduling, but long jobs can starve." },
  srtf:  { name: "SRTF (preemptive SJF)",     note: "Always runs the job with the least time remaining. Optimal average waiting time, but causes many context switches." },
  prio:  { name: "Priority (non-preemptive)", note: "Runs the highest-priority ready job to completion. Low-priority jobs may starve." },
  prioP: { name: "Priority (preemptive)",     note: "A newly arrived higher-priority job takes the CPU immediately. Low-priority jobs may starve." },
  rr:    { name: "Round Robin",               note: "Each job gets a fixed time quantum in turn. Fair and good response time; waiting time depends on the quantum." },
  hrrn:  { name: "HRRN",                      note: "Highest response ratio next: (waiting + burst) / burst. Favours short jobs but ages long ones, so nothing starves." },
  smart: { name: "Smart MLFQ + aging",        note: "Three-level feedback queue. New jobs start at the top with the base quantum, which doubles on each lower level. Jobs that wait too long are promoted (aging), so short jobs finish fast and long jobs never starve." }
};
const AGING_LIMIT = 15;   // ticks a job may wait before it is promoted in MLFQ
const MAX_LEVEL = 2;

/* ---------------- Scheduler engine ---------------- */
function simulate(jobs, algo, quantum) {
  const P = jobs.map(j => ({ ...j, rem: j.bt, start: null, ft: null, lvl: 0, since: j.at }));
  const ready = [], gantt = [];
  let t = 0, done = 0, cur = null, slice = 0, switches = 0, lastPid = null, busy = 0;

  const pickNonPre = () => {
    if (algo === "fcfs") return ready[0];
    const key = {
      sjf:  p => p.bt,
      prio: p => p.pr,
      hrrn: p => -((t - p.at + p.bt) / p.bt)
    }[algo];
    return ready.reduce((b, p) => (key(p) < key(b) ? p : b), ready[0]);
  };
  const pickMin = key => ready.reduce((b, p) => (key(p) < key(b) ? p : b), cur && ready.includes(cur) ? cur : ready[0]);
  const sliceFor = p => (algo === "smart" ? quantum * Math.pow(2, p.lvl) : quantum);

  while (done < P.length) {
    P.filter(p => p.at === t).forEach(p => ready.push(p));   // arrivals first

    if (algo === "smart") {                                  // aging
      ready.forEach(p => { if (p !== cur && p.lvl > 0 && t - p.since >= AGING_LIMIT) { p.lvl--; p.since = t; } });
    }

    if (ready.length) {
      if (algo === "srtf") cur = pickMin(p => p.rem);
      else if (algo === "prioP") cur = pickMin(p => p.pr);
      else if (algo === "rr") {
        if (cur && slice >= quantum) { ready.push(ready.splice(ready.indexOf(cur), 1)[0]); cur = null; }
        if (!cur) { cur = ready[0]; slice = 0; }
      } else if (algo === "smart") {
        if (cur && slice >= sliceFor(cur)) {                 // slice used up: demote and requeue
          cur.lvl = Math.min(cur.lvl + 1, MAX_LEVEL);
          cur.since = t;
          ready.push(ready.splice(ready.indexOf(cur), 1)[0]);
          cur = null;
        }
        const top = ready.reduce((b, p) => (p.lvl < b.lvl ? p : b), ready[0]);
        if (!cur || top.lvl < cur.lvl) { cur = top; slice = 0; }
      } else if (!cur) cur = pickNonPre();
    }

    if (!cur) {                                              // idle tick
      const g = gantt[gantt.length - 1];
      if (g && g.pid === null) g.end = t + 1; else gantt.push({ pid: null, start: t, end: t + 1 });
      t++; continue;
    }

    if (cur.start === null) cur.start = t;
    if (lastPid !== cur.id) { if (lastPid !== null) switches++; lastPid = cur.id; }
    const g = gantt[gantt.length - 1];
    if (g && g.pid === cur.id && g.end === t) g.end = t + 1; else gantt.push({ pid: cur.id, start: t, end: t + 1 });

    cur.rem--; slice++; busy++; t++;
    if (cur.rem === 0) {
      cur.ft = t; done++;
      ready.splice(ready.indexOf(cur), 1);
      cur = null;
    }
  }

  const rows = P.map(p => ({
    id: p.id, at: p.at, bt: p.bt, start: p.start, ft: p.ft,
    tat: p.ft - p.at, wt: p.ft - p.at - p.bt, rt: p.start - p.at
  }));
  const avg = k => rows.reduce((s, r) => s + r[k], 0) / rows.length;
  return {
    gantt, rows, switches,
    avgWT: avg("wt"), avgTAT: avg("tat"), avgRT: avg("rt"),
    util: (busy / t) * 100, throughput: rows.length / t, total: t
  };
}

/* ---------------- State and helpers ---------------- */
let jobs = [], nextId = 1;
const $ = id => document.getElementById(id);
const f2 = n => n.toFixed(2);
const color = id => `hsl(${(parseInt(id.slice(1), 10) * 137) % 360} 62% 40%)`;
const chip = id => `<span class="chip" style="background:${color(id)}">${id}</span>`;

function showMsg(text) { $("msg").textContent = text || ""; }

/* ---------------- Job list ---------------- */
function addJob(at, bt, pr) {
  jobs.push({ id: "P" + nextId++, at, bt, pr });
  renderJobs();
}
function renderJobs() {
  const body = $("jobTable").tBodies[0];
  body.innerHTML = jobs.length
    ? jobs.map(j => `<tr><td>${chip(j.id)}</td><td>${j.at}</td><td>${j.bt}</td><td>${j.pr}</td>
        <td><button data-del="${j.id}" aria-label="Remove ${j.id}">Remove</button></td></tr>`).join("")
    : `<tr><td colspan="5">No jobs yet. Add one above or load a sample.</td></tr>`;
}
function reset(list) { jobs = []; nextId = 1; list.forEach(([a, b, p]) => addJob(a, b, p)); }

$("addBtn").onclick = () => {
  const at = parseInt($("at").value, 10), bt = parseInt($("bt").value, 10), pr = parseInt($("pr").value, 10);
  if (isNaN(at) || at < 0 || isNaN(bt) || bt < 1 || isNaN(pr) || pr < 1) return showMsg("Arrival must be 0 or more. Burst and priority must be 1 or more.");
  if (jobs.length >= 20) return showMsg("The simulator supports up to 20 jobs.");
  showMsg(""); addJob(at, bt, pr);
};
$("jobTable").onclick = e => {
  const id = e.target.dataset.del;
  if (id) { jobs = jobs.filter(j => j.id !== id); renderJobs(); }
};
$("sampleBtn").onclick = () => { showMsg(""); reset([[0, 8, 3], [1, 4, 1], [2, 9, 4], [3, 5, 2], [20, 3, 1], [22, 6, 2]]); };
$("randomBtn").onclick = () => {
  showMsg("");
  const r = (a, b) => a + Math.floor(Math.random() * (b - a + 1));
  reset(Array.from({ length: 6 }, () => [r(0, 12), r(1, 12), r(1, 5)]));
};
$("clearBtn").onclick = () => { jobs = []; nextId = 1; renderJobs(); $("resultPanel").hidden = true; showMsg(""); };

/* ---------------- Running a simulation ---------------- */
function inputs() {
  const q = parseInt($("quantum").value, 10);
  if (!jobs.length) { showMsg("Add at least one job first."); return null; }
  if (isNaN(q) || q < 1) { showMsg("Time quantum must be 1 or more."); return null; }
  showMsg(""); return q;
}

$("algo").innerHTML = Object.entries(ALGOS).map(([k, a]) => `<option value="${k}">${a.name}</option>`).join("");
$("algo").value = "smart";
const updateNote = () => { $("algoNote").textContent = ALGOS[$("algo").value].note; };
$("algo").onchange = updateNote; updateNote();

$("runBtn").onclick = () => {
  const q = inputs(); if (q === null) return;
  const res = simulate(jobs, $("algo").value, q);

  $("gantt").innerHTML = res.gantt.map((g, i) => {
    const d = g.end - g.start;
    const bg = g.pid ? `background:${color(g.pid)};` : "";
    const last = i === res.gantt.length - 1 ? `<b>${g.end}</b>` : "";
    return `<div class="seg ${g.pid ? "" : "idle"}" style="flex:${d} 1 0;min-width:${Math.max(26, d * 6)}px;${bg}" title="${g.pid || "Idle"}: ${g.start} to ${g.end}">${g.pid || "idle"}<i>${g.start}</i>${last}</div>`;
  }).join("");

  const stat = (v, l) => `<div class="stat"><strong>${v}</strong><span>${l}</span></div>`;
  $("stats").innerHTML =
    stat(f2(res.avgWT), "Average waiting time") + stat(f2(res.avgTAT), "Average turnaround") +
    stat(f2(res.avgRT), "Average response") + stat(res.util.toFixed(1) + "%", "CPU utilisation") +
    stat(f2(res.throughput), "Jobs per time unit") + stat(res.switches, "Context switches");

  $("resTable").tBodies[0].innerHTML = res.rows.map(r =>
    `<tr><td>${chip(r.id)}</td><td>${r.at}</td><td>${r.bt}</td><td>${r.start}</td><td>${r.ft}</td><td>${r.wt}</td><td>${r.tat}</td><td>${r.rt}</td></tr>`).join("");
  $("resultPanel").hidden = false;
  $("resultPanel").scrollIntoView({ behavior: "smooth", block: "nearest" });
};

/* ---------------- Compare and recommend ---------------- */
$("cmpBtn").onclick = () => {
  const q = inputs(); if (q === null) return;
  const out = Object.keys(ALGOS).map(k => ({ k, r: simulate(jobs, k, q) }));
  out.sort((a, b) => a.r.avgWT - b.r.avgWT || a.r.switches - b.r.switches);
  const best = out[0];

  $("cmpTable").hidden = false;
  $("cmpTable").tBodies[0].innerHTML = out.map((o, i) =>
    `<tr class="${i === 0 ? "best" : ""}"><td>${ALGOS[o.k].name}</td><td>${f2(o.r.avgWT)}</td><td>${f2(o.r.avgTAT)}</td><td>${f2(o.r.avgRT)}</td><td>${o.r.switches}</td><td>${o.r.util.toFixed(1)}%</td></tr>`).join("");

  // Workload analysis feeds the explanation
  const bursts = jobs.map(j => j.bt), mean = bursts.reduce((s, b) => s + b, 0) / bursts.length;
  const spread = Math.max(...bursts) / Math.min(...bursts);
  const worstRT = Math.max(...best.r.rows.map(r => r.rt));
  const why = [
    `Burst times vary by ${spread.toFixed(1)}x (mean ${mean.toFixed(1)}).`,
    spread >= 3 ? "A wide spread favours algorithms that serve short jobs first." : "Similar burst sizes keep the algorithms close together.",
    `The longest first-response delay under this schedule is ${worstRT}.`
  ].join(" ");
  const runner = out[1];
  $("recommend").hidden = false;
  $("recommend").innerHTML =
    `<strong>Recommended: ${ALGOS[best.k].name}.</strong> It gives the lowest average waiting time (${f2(best.r.avgWT)}) with ${best.r.switches} context switches. ` +
    `${why} Runner-up: ${ALGOS[runner.k].name} (${f2(runner.r.avgWT)}).` +
    (best.k === "smart" ? "" : ` Note that ${ALGOS[best.k].name} may starve some jobs on heavier workloads. Smart MLFQ + aging avoids that at a small cost in waiting time.`);
};

renderJobs();
