#!/usr/bin/env python3
"""Export the health desk's records as one scrubbed JSON for productagent.dev.

Aggregates what the machine already keeps about every unattended run: the cost
ledgers (wrapper-written), trajectory scores and judge rows (scores.jsonl), the
fence section and interventions line stamped on each report, the decisions file
and the loop registry. Numbers, dates, lanes and verdicts only; no prose, no
paths, no goals. The site renders the file as /evidence.

Human-side tooling under 00-ops/ (fence-denied to the fleet).

Usage: python3 00-ops/health/export-evidence.py [--out PATH] [--through YYYY-MM-DD]
--through freezes the record: nothing dated after it is exported.
Default out: ./evidence.json (point --out at your site repo)
"""
import argparse
import datetime as dt
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

HOME = Path.home()
VENT = Path(os.environ.get("LOOPS_HOME", HOME / "ventures"))
OPS = VENT / "00-ops"
NIGHTS = VENT / "pm/nights"
DEFAULT_OUT = Path("evidence.json")
LANES = ("night", "day", "hourly")
SCORERS = ("step_budget", "no_repeat_loop", "no_denial_retry", "no_questions",
           "protected_paths", "git_readonly", "report_written")


def jsonl(path):
    rows = []
    try:
        for line in Path(path).read_text().splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass
    return rows


def ledger_rows():
    out = []
    for lane in LANES:
        for r in jsonl(OPS / lane / "cost-ledger.jsonl"):
            if not r.get("date"):
                continue
            out.append({
                "date": r["date"], "lane": lane,
                "status": r.get("status", "unknown"),
                "cost_usd": round(float(r.get("cost_usd") or 0), 2),
                "secs": int(r.get("secs") or 0),
                "estimate": bool(r.get("cost_is_estimate", False)),
            })
    return out


def score_rows():
    sessions, judges = [], []
    for r in jsonl(OPS / "health/scores.jsonl"):
        if "judge" in r:
            j = r["judge"]
            judges.append({"date": r.get("date"), "choice": j.get("choice"),
                           "score": j.get("score"),
                           "unsupported": len(j.get("unsupported_claims") or []),
                           "unmentioned": len(j.get("unmentioned_changes") or [])})
        elif "scores" in r:
            ended = r.get("ended", "")
            sessions.append({"date": ended[:10], "lane": r.get("lane", "?"),
                             "tools": r.get("tools", 0), "subagents": r.get("subagents", 0),
                             "errors": r.get("errors", 0),
                             "scores": {k: r["scores"].get(k) for k in SCORERS if k in r["scores"]}})
    return sessions, judges


def report_facts():
    """Per report date: wrapper-observed refused calls and the interventions line."""
    denials, interventions = {}, {}
    for p in sorted(NIGHTS.glob("20??-??-??.md")):
        date = p.stem
        try:
            text = p.read_text()
        except OSError:
            continue
        m = re.search(r"^- (\d+) refused call\(s\) this run", text, re.M)
        if m:
            denials[date] = int(m.group(1))
        elif "## Blocked by the fence (wrapper-observed)\n- none" in text:
            denials[date] = 0
        m = re.search(r"interventions=(\d+) \(need-lines=(\d+) paste-blocks=(\d+) decisions-queued=(\d+) errors-seen=(\d+)\)", text)
        if m:
            interventions[date] = {"total": int(m.group(1)), "need_lines": int(m.group(2)),
                                   "paste_blocks": int(m.group(3)), "decisions_queued": int(m.group(4)),
                                   "errors_seen": int(m.group(5))}
    return denials, interventions


def decisions():
    c = Counter()
    try:
        for line in (NIGHTS / "DECISIONS.md").read_text().splitlines():
            m = re.match(r"^- \[([ x~])\] D-\d+", line)
            if m:
                c[{" ": "open", "x": "applied", "~": "parked"}[m.group(1)]] += 1
    except OSError:
        pass
    return dict(c)


def loops():
    c = Counter()
    try:
        for line in (VENT / "pm/LOOPS.md").read_text().splitlines():
            m = re.match(r"^- status:\s*(\w+)", line)
            if m:
                c[m.group(1)] += 1
    except OSError:
        pass
    return dict(c)


def build(through=None):
    ledger = ledger_rows()
    sessions, judges = score_rows()
    denials, interv = report_facts()
    if through:
        ledger = [r for r in ledger if r["date"] <= through]
        sessions = [s for s in sessions if s["date"] <= through]
        judges = [j for j in judges if (j["date"] or "") <= through]
        denials = {d: v for d, v in denials.items() if d <= through}
        interv = {d: v for d, v in interv.items() if d <= through}

    # one row per (date, lane) from the ledger, enriched from the other records
    by_key = defaultdict(lambda: {"status": None, "cost_usd": 0.0, "secs": 0, "runs": 0, "estimate": False})
    for r in ledger:
        k = (r["date"], r["lane"])
        row = by_key[k]
        row["runs"] += 1
        row["cost_usd"] = round(row["cost_usd"] + r["cost_usd"], 2)
        row["secs"] += r["secs"]
        row["estimate"] = row["estimate"] or r["estimate"]
        # a night that eventually succeeded reads ok; otherwise keep the worst word seen
        if row["status"] in (None, "ok") or r["status"] != "ok":
            row["status"] = r["status"] if row["status"] is None or r["status"] != "ok" else "ok"
    sess_by_key = defaultdict(list)
    for s in sessions:
        sess_by_key[(s["date"], s["lane"])].append(s)
    judge_by_date = {j["date"]: j for j in judges}

    nights = []
    for (date, lane), row in sorted(by_key.items()):
        ss = sess_by_key.get((date, lane), [])
        traj = {}
        for k in SCORERS:
            vals = [s["scores"][k] for s in ss if k in s["scores"]]
            if vals:
                traj[k] = min(vals)
        nights.append({
            "date": date, "lane": lane, "status": row["status"], "runs": row["runs"],
            "cost_usd": row["cost_usd"], "secs": row["secs"], "cost_is_estimate": row["estimate"],
            "sessions_scored": len(ss),
            "tool_calls": sum(s["tools"] for s in ss),
            "tool_errors": sum(s["errors"] for s in ss),
            "trajectory": traj,
            "refused_calls": denials.get(date) if lane == "night" else None,
            "judge": judge_by_date.get(date, {}).get("choice") if lane == "night" else None,
            "interventions": interv.get(date, {}).get("total") if lane == "night" else None,
        })

    night_rows = [n for n in nights if n["lane"] == "night"]
    status = Counter(n["status"] for n in night_rows)
    clean = {k: sum(1 for s in sessions if s["scores"].get(k) == 1.0) for k in SCORERS}
    scored = {k: sum(1 for s in sessions if k in s["scores"]) for k in SCORERS}
    iv = [v["total"] for _, v in sorted(interv.items())]

    totals = {
        "first_night": night_rows[0]["date"] if night_rows else None,
        "last_night": night_rows[-1]["date"] if night_rows else None,
        "nights": len(night_rows),
        "night_status": dict(status),
        "night_cost_usd": round(sum(n["cost_usd"] for n in night_rows), 2),
        "all_lanes_cost_usd": round(sum(n["cost_usd"] for n in nights), 2),
        "runs_all_lanes": sum(n["runs"] for n in nights),
        "sessions_scored": len(sessions),
        "trajectory_clean": {k: {"clean": clean[k], "scored": scored[k]} for k in SCORERS},
        "judge": dict(Counter(j["choice"] for j in judges)),
        "judge_rows": len(judges),
        "refused_calls_total": sum(v for v in denials.values()),
        "nights_with_fence_record": len(denials),
        "interventions": {"nights": len(iv), "latest": iv[-1] if iv else None,
                          "mean": round(sum(iv) / len(iv), 1) if iv else None,
                          "max": max(iv) if iv else None, "baseline_2026_09_18": 13},
        "decisions": decisions(),
        "loops": loops(),
    }
    return {
        "generated": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "through": through,
        "scope": "Every unattended run on the author's own machine, as the runner and the health desk recorded it. "
                 "Numbers only; the work itself was chores on the author's ventures, not product-management tasks.",
        "totals": totals,
        "nights": nights,
        "judges": judges,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--through", help="YYYY-MM-DD; drop everything dated after it")
    a = ap.parse_args()
    data = build(a.through)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=1) + "\n")
    t = data["totals"]
    print(f"wrote {out}: {t['nights']} nights, {t['sessions_scored']} sessions scored, "
          f"{t['judge_rows']} judge rows, ${t['night_cost_usd']} night spend")


if __name__ == "__main__":
    main()
