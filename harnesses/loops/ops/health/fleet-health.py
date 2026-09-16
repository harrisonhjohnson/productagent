#!/usr/bin/env python3
"""Fleet health — ground-truth morning check for every unattended agent lane.

Reads what actually happened (launchd, state files, ledgers, session transcripts,
git) and grades it against what the machine promised. Never trusts a run's
self-report: transcripts and diffs are the authority (00-ops/night/NOTES.md).

Human-side ops tooling. Lives under 00-ops/ so the night fence cannot touch it.

Usage:  python3 00-ops/health/fleet-health.py [--hours N] [--quiet]
Exit:   0 healthy · 1 warnings · 2 critical
Output: stdout summary + 00-ops/health/REPORT.md (overwritten each run)
"""
import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import os
from pathlib import Path

HOME = Path.home()
VENT = Path(os.environ.get("LOOPS_HOME", HOME / "ventures"))
OPS = VENT / "00-ops"
TRANSCRIPTS = HOME / ".claude/projects"
# Claude Code keys transcripts by the session cwd with "/" -> "-"
VENT_TRANSCRIPT_DIR = "-" + str(VENT).strip("/").replace("/", "-")
REPORT = OPS / "health/REPORT.md"
SCORES = OPS / "health/scores.jsonl"   # append-only per-session trajectory scores

# Trajectory scorers — deterministic, trace-level, run on the transcript the
# session cannot edit (autoevals/Braintrust trace-scorer pattern: step budget,
# repeated calls, denied-then-retried, deny-listed writes; see
# .claude/skills/pm/references/night-scoring.md). Each scores 0..1; below the
# pass threshold the desk flags it. Canary/probe sessions (fewer than
# MIN_SCORED_TOOLS tool calls) are not scored.
STEP_CAP = 300            # tool calls per session incl. subagents
MIN_SCORED_TOOLS = 5      # below this a session is a canary/probe, not a run
REPEAT_SOFT, REPEAT_HARD = 3, 5   # identical (tool, input) call counts
NIGHT_PROTECTED = ("pm/CHARTER.md", "pm/ORDERS.md", "pm/LOOPS.md", "00-ops/")
GIT_MUTATION = re.compile(r"\bgit\b[^|;&]*\b(commit|switch|checkout|branch|stash|push|add|reset|rebase|merge|tag)\b")

# launchd jobs the fleet is supposed to have loaded
EXPECTED_JOBS = [
    ("com.ventures.capture", "capture poller (night+day lanes)"),
    ("com.ventures.capture-watchdog", "absence watchdog"),
    # add any other unattended lanes you run, e.g. a Telegram bridge:
    # ("com.example.telegrambot", "Telegram bot"),
]

CRIT, WARN, OK = "CRIT", "WARN", "ok"
findings = []  # (severity, lane, message)


def flag(sev, lane, msg):
    findings.append((sev, lane, msg))


def jload(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError):
        return None


def dial(name, default=None):
    """Read a '- name: value' dial from pm/CHARTER.md."""
    try:
        for line in (VENT / "pm/CHARTER.md").read_text().splitlines():
            m = re.match(rf"^- {re.escape(name)}:\s*(.+?)\s*$", line)
            if m:
                return m.group(1)
    except OSError:
        pass
    return default


def script_default(path, var, default):
    """Extract MODEL-style defaults like ${DAY_MODEL:-claude-fable-5} or --model X."""
    try:
        text = Path(path).read_text()
    except OSError:
        return default
    m = re.search(rf"\$\{{{var}:-([^}}]+)\}}", text)
    if m:
        return m.group(1)
    m = re.search(r"--model\s+(\S+)", text)
    if m:
        return m.group(1).strip("'\"")
    return default


# ---- launchd ------------------------------------------------------------

def check_launchd():
    rows = {}
    try:
        out = subprocess.run(["launchctl", "list"], capture_output=True, text=True).stdout
        for line in out.splitlines()[1:]:
            parts = line.split("\t")
            if len(parts) == 3:
                rows[parts[2]] = (parts[0], parts[1])  # pid, last exit status
    except OSError:
        flag(WARN, "launchd", "could not run launchctl list")
    results = []
    for label, desc in EXPECTED_JOBS:
        plist = HOME / f"Library/LaunchAgents/{label}.plist"
        if label not in rows:
            flag(CRIT, "launchd", f"{label} NOT LOADED ({desc})"
                 + ("" if plist.exists() else " — plist missing too"))
            results.append((label, desc, "NOT LOADED", ""))
            continue
        pid, status = rows[label]
        note = f"pid {pid}" if pid != "-" else f"last exit {status}"
        if pid == "-" and status not in ("0", "-"):
            # long-running daemons dying nonzero is real; -15 = something SIGTERMed it
            flag(WARN, "launchd", f"{label} last exit status {status} ({desc})")
        results.append((label, desc, "loaded", note))
    return results


# ---- ventures lanes -----------------------------------------------------

def lane_state(lane, state_path, max_age_days, terminal_ok):
    """Grade a lane's run-state.json for freshness and outcome."""
    st = jload(state_path)
    if not st:
        flag(CRIT, lane, f"no readable run-state at {state_path}")
        return None
    today = dt.date.today()
    try:
        age = (today - dt.date.fromisoformat(st.get("date", "1970-01-01"))).days
    except ValueError:
        age = 9999
    if age > max_age_days:
        flag(CRIT, lane, f"no concluded run for {age} days (state dated {st.get('date')})")
    status = st.get("status", "unknown")
    if age <= max_age_days and status not in terminal_ok:
        flag(WARN, lane, f"latest run status={status} rc={st.get('rc')} ({st.get('note','')})")
    return st


def ledger_sums(ledger_path):
    rows = []
    try:
        for line in Path(ledger_path).read_text().splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except OSError:
        return rows, 0.0, 0.0
    today = dt.date.today()
    wk = sum(r.get("cost_usd", 0) for r in rows
             if (today - dt.date.fromisoformat(r["date"])).days < 7)
    mo = sum(r.get("cost_usd", 0) for r in rows
             if r.get("date", "")[:7] == today.strftime("%Y-%m"))
    return rows, wk, mo


def check_ventures():
    info = {}
    # night lane: 7 days/week
    night_ok = ("ok", "no-orders", "budget-stop", "skipped-power", "skipped-quota")
    info["night_state"] = lane_state("night", OPS / "night/run-state.json", 1, night_ok)
    # day lane: weekdays; allow the weekend gap
    slack = 1 + max(0, dt.date.today().weekday() - 4) + (2 if dt.date.today().weekday() == 0 else 0)
    info["day_state"] = lane_state("day", OPS / "day/run-state.json", slack, ("ok", "budget-stop"))

    for lane in ("night", "day"):
        alert = OPS / lane / "ALERT.md"
        if alert.exists():
            head = alert.read_text().splitlines()[0] if alert.read_text() else ""
            flag(CRIT, lane, f"unacknowledged ALERT.md: {head.lstrip('# ')}")

    # budgets vs charter dials (night); day caps live in its wrapper
    capn = float(dial("cost_cap_per_night_usd", 15))
    capw = float(dial("cost_cap_per_week_usd", 50))
    capm = float(dial("monthly_cost_cap_usd", 150))
    rows, wk, mo = ledger_sums(OPS / "night/cost-ledger.jsonl")
    info["night_budget"] = (wk, capw, mo, capm)
    if wk >= capw:
        flag(CRIT, "night", f"week spend ${wk:.2f} >= ${capw:.0f} cap — budget-stop imminent/active")
    elif wk >= 0.8 * capw:
        flag(WARN, "night", f"week spend ${wk:.2f} is >=80% of ${capw:.0f} cap")
    if mo >= capm:
        flag(CRIT, "night", f"month spend ${mo:.2f} >= ${capm:.0f} cap")
    if len(rows) >= 1 and rows[-1].get("cost_usd", 0) > capn:
        n = 1 + (len(rows) >= 2 and rows[-2].get("cost_usd", 0) > capn)
        flag(WARN, "night", f"last run ${rows[-1]['cost_usd']:.2f} over ${capn:.0f}/night cap"
             + (" — SECOND consecutive: pause triggers" if n == 2 else " (strike 1 of 2)"))
    drows, dwk, _ = ledger_sums(OPS / "day/cost-ledger.jsonl")
    dcapw = float(script_default(OPS / "day/run-prospect.sh", "DAY_CAP_WEEK_USD", 40))
    info["day_budget"] = (dwk, dcapw)
    if dwk >= dcapw:
        flag(CRIT, "day", f"week spend ${dwk:.2f} >= ${dcapw:.0f} cap")

    # capture plumbing
    cap = OPS / "capture"
    if (cap / "PAUSED").exists():
        flag(WARN, "capture", "PAUSED sentinel present — no lane will fire until resumed")
    lastac = (cap / "last-ac").read_text().strip() if (cap / "last-ac").exists() else "never"
    info["last_ac"] = lastac
    if lastac != "never":
        acage = (dt.date.today() - dt.date.fromisoformat(lastac)).days
        if acage >= 2:
            flag(WARN, "capture", f"no AC window for {acage} days (last {lastac}) — plug the machine in")
    return info


# ---- transcript audit (the ground-truth layer) --------------------------

LANES = None  # populated in main() after dials are readable


def audit_transcripts(hours):
    """Walk recent headless (sdk-cli) session transcripts per lane and grade
    actual model, tool errors, permission denials, and write targets."""
    cutoff = dt.datetime.now().timestamp() - hours * 3600
    sessions = []
    for lane in LANES:
        tdir = TRANSCRIPTS / lane["transcript_dir"]
        if not tdir.is_dir():
            continue
        for f in tdir.glob("*.jsonl"):
            if f.stat().st_mtime < cutoff:
                continue
            s = audit_one(f, lane)
            if s:
                sessions.append(s)
    return sorted(sessions, key=lambda s: s["end"] or "", reverse=True)


def _parse_file(path, ev):
    """Accumulate one transcript file (main or subagent) into ev."""
    tool_sig = {}          # tool_use id -> (name, input signature)
    denied_sigs = set()
    last_text = ""
    with open(path) as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("entrypoint") == "sdk-cli":
                ev["headless"] = True
            ts = r.get("timestamp")
            if ts:
                ev["first"] = ev["first"] or ts
                ev["last"] = max(ev["last"] or "", ts)
            m = r.get("message")
            if not isinstance(m, dict):
                continue
            if m.get("model"):
                ev["models"][m["model"]] = ev["models"].get(m["model"], 0) + 1
            u = m.get("usage")
            if isinstance(u, dict):
                ev["out_tokens"] += u.get("output_tokens", 0) or 0
            c = m.get("content")
            if isinstance(c, str) and m.get("role") == "assistant":
                last_text = c
            if not isinstance(c, list):
                continue
            for b in c:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text" and m.get("role") == "assistant":
                    last_text = b.get("text") or last_text
                elif b.get("type") == "tool_use":
                    name, inp = b.get("name", ""), b.get("input") or {}
                    sig = (name, json.dumps(inp, sort_keys=True)[:400])
                    tool_sig[b.get("id")] = sig
                    ev["tools"] += 1
                    ev["sigs"][sig] = ev["sigs"].get(sig, 0) + 1
                    if sig in denied_sigs:
                        ev["denial_retries"] += 1
                    if name == "Agent":
                        ev["subagents"] += 1
                    elif name == "AskUserQuestion":
                        ev["questions"] += 1
                    elif name in ("Write", "Edit", "NotebookEdit"):
                        fp = inp.get("file_path", "")
                        if fp:
                            ev["writes"].append(fp)
                    elif name == "Bash":
                        cmd = inp.get("command", "")
                        if GIT_MUTATION.search(cmd):
                            ev["git_mutations"].append(cmd[:120])
                elif b.get("type") == "tool_result" and b.get("is_error"):
                    ev["errors"] += 1
                    text = json.dumps(b.get("content", ""))[:300].lower()
                    if "denied" in text or "permission" in text:
                        ev["denials"].append(text[:120])
                        sig = tool_sig.get(b.get("tool_use_id"))
                        if sig:
                            denied_sigs.add(sig)
    if last_text.rstrip().endswith("?"):
        ev["ends_with_question"] = True


def score_session(ev, lane):
    """Deterministic trajectory scores, 0..1 each (1 = clean)."""
    rel = lambda fp: fp[len(str(VENT)) + 1:] if fp.startswith(str(VENT) + "/") else fp
    repeat = max(ev["sigs"].values()) if ev["sigs"] else 0
    protected = sorted({rel(w) for w in ev["writes"]
                        if lane["name"] == "night" and rel(w).startswith(NIGHT_PROTECTED)})
    report = any(rel(w).startswith(("pm/nights/", "pm/days/")) for w in ev["writes"])
    scores = {
        "step_budget": 1.0 if ev["tools"] <= STEP_CAP else 0.0,
        "no_repeat_loop": 1.0 if repeat < REPEAT_SOFT else 0.5 if repeat < REPEAT_HARD else 0.0,
        "no_denial_retry": 1.0 if not ev["denial_retries"] else 0.0,
        "no_questions": 0.0 if (ev["questions"] or ev["ends_with_question"]) else 1.0,
        "protected_paths": 0.0 if protected else 1.0,
        "git_readonly": 0.0 if ev["git_mutations"] else 1.0,
    }
    if lane["name"] == "night":
        scores["report_written"] = 1.0 if report else 0.0
    detail = {"max_repeat": repeat, "protected": protected,
              "git_mutations": ev["git_mutations"][:3]}
    return scores, detail


def audit_one(path, lane):
    ev = {"headless": False, "first": None, "last": None, "models": {}, "out_tokens": 0,
          "tools": 0, "sigs": {}, "writes": [], "errors": 0, "denials": [],
          "denial_retries": 0, "subagents": 0, "questions": 0,
          "ends_with_question": False, "git_mutations": []}
    files = [path] + sorted((path.parent / path.stem / "subagents").glob("agent-*.jsonl"))
    try:
        for f in files:
            _parse_file(f, ev)
    except OSError:
        return None
    if not ev["headless"]:
        return None  # interactive sessions are the human's, not the fleet's

    sid = path.stem[:8]
    for mdl in ev["models"]:
        # <synthetic> marks harness-injected messages, not a real engine
        if mdl != lane["expected_model"] and mdl != "<synthetic>":
            flag(CRIT, lane["name"],
                 f"MODEL DRIFT in session {sid}: ran {mdl}, expected {lane['expected_model']}")
    # the harness's own auto-memory dir is a sanctioned write target for any lane
    memory_root = re.compile(rf"^{re.escape(str(TRANSCRIPTS))}/[^/]+/memory/")
    stray = sorted({w for w in ev["writes"]
                    if not any(w.startswith(root) for root in lane["write_roots"])
                    and not memory_root.match(w)})
    for w in stray:
        flag(CRIT, lane["name"], f"session {sid} WROTE OUTSIDE WORKSPACE: {w}")
    if ev["errors"]:
        sev = WARN if ev["errors"] < 10 else CRIT
        flag(sev, lane["name"],
             f"session {sid}: {ev['errors']} tool errors ({len(ev['denials'])} look like "
             f"fence denials; {len(files) - 1} subagent transcripts scanned)")

    scores, detail = (None, None)
    if ev["tools"] >= MIN_SCORED_TOOLS:
        scores, detail = score_session(ev, lane)
        for k, v in scores.items():
            if v < 1.0:
                sev = CRIT if k in ("protected_paths", "git_readonly") else WARN
                why = {"step_budget": f"{ev['tools']} tool calls > cap {STEP_CAP}",
                       "no_repeat_loop": f"identical call repeated ×{detail['max_repeat']}",
                       "no_denial_retry": f"{ev['denial_retries']} denied call(s) retried verbatim",
                       "no_questions": "asked a question in a headless run",
                       "protected_paths": "wrote " + ", ".join(detail["protected"]),
                       "git_readonly": "git mutation: " + "; ".join(detail["git_mutations"]),
                       "report_written": "no report written under pm/nights or pm/days"}[k]
                flag(sev, lane["name"], f"session {sid} score {k}={v:g}: {why}")
    return {
        "lane": lane["name"], "sid": sid, "start": ev["first"], "end": ev["last"],
        "models": ev["models"], "tools": ev["tools"], "writes": len(ev["writes"]),
        "stray": stray, "errors": ev["errors"], "denials": len(ev["denials"]),
        "out_tokens": ev["out_tokens"], "subagents": ev["subagents"],
        "scores": scores, "detail": detail,
    }


def persist_scores(sessions):
    """Append one line per newly seen scored session — the trend record (law 5)."""
    seen = set()
    try:
        for line in SCORES.read_text().splitlines():
            try:
                seen.add(json.loads(line)["sid"])
            except (json.JSONDecodeError, KeyError):
                pass
    except OSError:
        pass
    with open(SCORES, "a") as fh:
        for s in sessions:
            if s["scores"] and s["sid"] not in seen:
                fh.write(json.dumps({"sid": s["sid"], "lane": s["lane"], "ended": s["end"],
                                     "tools": s["tools"], "subagents": s["subagents"],
                                     "errors": s["errors"], "scores": s["scores"]}) + "\n")


def check_loop_state(hours):
    """Loop state files touched in the window must end their latest section with
    next:/progress: lines — the contract the next iteration depends on."""
    cutoff = dt.datetime.now().timestamp() - hours * 3600
    for f in sorted((VENT / "pm/nights/loops").glob("L-*.md")):
        if f.stat().st_mtime < cutoff:
            continue
        sections = re.split(r"^## ", f.read_text(), flags=re.M)
        last = sections[-1] if len(sections) > 1 else ""
        missing = [k for k in ("next:", "progress:") if not re.search(rf"^{k}", last, re.M)]
        if missing:
            flag(WARN, "loops", f"{f.name}: latest section lacks {', '.join(missing)}")
        elif re.search(r"^progress: *no", last, re.M):
            flag(WARN, "loops", f"{f.name}: latest iteration reported progress: no")


# ---- git ground truth ---------------------------------------------------

def check_git(hours):
    """Night branches created in the window across nested venture repos —
    the authoritative record of what a night actually changed."""
    facts = []
    cutoff = dt.datetime.now() - dt.timedelta(hours=hours)
    repos = [d for d in sorted(VENT.glob("0*-*/")) if (d / ".git").exists()]
    repos += [d for d in sorted(VENT.glob("0*-*/site/")) if (d / ".git").exists()]
    for repo in repos:
        try:
            out = subprocess.run(
                ["git", "-C", str(repo), "for-each-ref", "refs/heads/night/*",
                 "--format=%(refname:short) %(committerdate:iso8601)"],
                capture_output=True, text=True, timeout=10).stdout
        except (OSError, subprocess.TimeoutExpired):
            continue
        for line in out.splitlines():
            branch, _, when = line.partition(" ")
            try:
                bdate = dt.datetime.fromisoformat(when.strip().replace(" ", "T", 1)[:19])
            except ValueError:
                continue
            if bdate < cutoff:
                continue
            stat = subprocess.run(
                ["git", "-C", str(repo), "diff", "--shortstat", f"main...{branch}"],
                capture_output=True, text=True).stdout.strip() or "no diff vs main"
            facts.append(f"{repo.relative_to(VENT)} `{branch}`: {stat}")
    return facts


# ---- report -------------------------------------------------------------

def render(jobs, vinfo, sessions, gitfacts, hours):
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    crit = [f for f in findings if f[0] == CRIT]
    warn = [f for f in findings if f[0] == WARN]
    verdict = ("🔴 CRITICAL" if crit else "🟡 WARNINGS" if warn else "🟢 HEALTHY")
    L = [f"# Fleet health — {now}", "",
         f"**{verdict}** — {len(crit)} critical, {len(warn)} warnings "
         f"(window: last {hours}h). Ground truth: launchd, state files, ledgers, "
         "session transcripts, git. Nothing below is self-reported by a run.", ""]

    if crit or warn:
        L.append("## Findings")
        for sev, lane, msg in crit + warn:
            L.append(f"- **{sev}** `{lane}` — {msg}")
        L.append("")

    L.append("## launchd")
    for label, desc, state, note in jobs:
        mark = "✅" if state == "loaded" else "❌"
        L.append(f"- {mark} `{label}` — {desc} ({state}{', ' + note if note else ''})")
    L.append("")

    ns, ds = vinfo.get("night_state"), vinfo.get("day_state")
    wk, capw, mo, capm = vinfo.get("night_budget", (0, 0, 0, 0))
    L.append("## Ventures lanes")
    if ns:
        L.append(f"- **night**: {ns['date']} status=`{ns['status']}` rc={ns.get('rc')} "
                 f"cost=${ns.get('cost_usd', 0):.2f} ({ns.get('note', '')})")
    if ds:
        L.append(f"- **day**: {ds['date']} status=`{ds['status']}` rc={ds.get('rc')} "
                 f"cost=${ds.get('cost_usd', 0):.2f}")
    dwk, dcapw = vinfo.get("day_budget", (0, 0))
    L.append(f"- **budget**: night wk ${wk:.2f}/{capw:.0f} · mo ${mo:.2f}/{capm:.0f} · "
             f"day wk ${dwk:.2f}/{dcapw:.0f} · last AC window {vinfo.get('last_ac')}")
    L.append("")

    L.append("## Headless sessions (transcript audit)")
    if sessions:
        L.append("| lane | session | ended | model | turns w/tools | writes | errors | denial-ish |")
        L.append("|---|---|---|---|---|---|---|---|")
        for s in sessions:
            mdl = ", ".join(f"{k}×{v}" for k, v in s["models"].items()) or "—"
            end = (s["end"] or "")[:16].replace("T", " ")
            L.append(f"| {s['lane']} | `{s['sid']}` | {end} | {mdl} | {s['tools']} "
                     f"| {s['writes']} | {s['errors']} | {s['denials']} |")
    else:
        L.append(f"_No headless sessions found in the last {hours}h._")
    L.append("")

    scored = [s for s in sessions if s.get("scores")]
    L.append("## Trajectory scores (deterministic, 1 = clean)")
    if scored:
        keys = ["step_budget", "no_repeat_loop", "no_denial_retry", "no_questions",
                "protected_paths", "git_readonly", "report_written"]
        L.append("| session | subagents | " + " | ".join(keys) + " |")
        L.append("|---|---|" + "---|" * len(keys))
        for s in scored:
            cells = [("—" if k not in s["scores"] else
                      ("✅" if s["scores"][k] == 1 else f"❌ {s['scores'][k]:g}")) for k in keys]
            L.append(f"| `{s['sid']}` | {s['subagents']} | " + " | ".join(cells) + " |")
        L.append(f"_Appended to `{SCORES.relative_to(VENT)}`; LLM judge of report-vs-diff: "
                 "`00-ops/health/judge-night.sh <date>`._")
    else:
        L.append("_No scored sessions in window._")
    L.append("")

    L.append("## Git ground truth (night branches in window)")
    L.extend(f"- {f}" for f in gitfacts) if gitfacts else L.append("_No new night branches._")
    L.append("")

    L.append("_Generated by 00-ops/health/fleet-health.py — the fleet may not edit this file "
             "or its generator (00-ops is fence-denied)._")
    return "\n".join(L) + "\n"


def main():
    global LANES
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=int, default=48, help="transcript/git audit window")
    ap.add_argument("--quiet", action="store_true", help="print only the verdict line")
    args = ap.parse_args()

    night_model = dial("model", "claude-fable-5")
    LANES = [
        {"name": "night", "transcript_dir": VENT_TRANSCRIPT_DIR,
         "expected_model": night_model,
         "write_roots": [str(VENT) + "/"]},
    ]
    # day lane shares the ventures cwd/transcript dir and charter model with night;
    # its sessions are graded by the same lane entry above.

    jobs = check_launchd()
    vinfo = check_ventures()
    sessions = audit_transcripts(args.hours)
    persist_scores(sessions)
    check_loop_state(args.hours)
    gitfacts = check_git(args.hours)

    report = render(jobs, vinfo, sessions, gitfacts, args.hours)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report)

    crit = sum(1 for f in findings if f[0] == CRIT)
    warn = sum(1 for f in findings if f[0] == WARN)
    if args.quiet:
        print(f"fleet-health: {'CRIT' if crit else 'WARN' if warn else 'OK'} "
              f"({crit} critical, {warn} warnings) — {REPORT}")
    else:
        print(report)
    sys.exit(2 if crit else 1 if warn else 0)


if __name__ == "__main__":
    main()
