#!/usr/bin/env python3
"""The planner: where should tonight's run go?

Builds a small structural graph of the work from files that already exist, ranks the next
points of leverage with explicit rules, and writes the pick where the runner can read it.
Every pick carries its reasons, so the morning can disagree with it.

Nodes
  state · permit-type cell (rows, filed, verified)     from the coverage JSON
  feed (ok, last change, rows)                         from the coverage JSON
  queue (resolve / extract eligible)                   from extract-queue.json
  decision (pending | settled, blocks: <action key>)   from pm/DECISIONS.md
  loop history (dated sections, progress, next:)       from pm/nights/loops/*.md

Actions are candidate nights. Score = value × readiness ÷ cost, then:
  −  repeated in the last `repeat_window` nights   (do not grind one thing)
  −  a pending decision blocks it                  (surface it, do not guess)
  −  two no-progress nights in a row               (parked)

Commands
  plan       print the ranked list and write pm/nights/plan-<date>.md; prints the pick line
  simulate   --nights N: apply each pick's expected effect to an in-memory copy and re-plan,
             to test that the planner moves rather than repeats
  decisions  --from <envelope.md>: turn "Need from you:" lines into pending Decisions

This is a graph of facts and rules, not embeddings. Karma can index DECISIONS.md and the
plan files as seeds; the planner does not read karma.
"""
import argparse, datetime as dt, glob, json, os, re, sys

LOOPS_HOME = os.environ.get("LOOPS_HOME", os.path.expanduser("~/ventures"))
CORPUS = os.environ.get("PLAN_CORPUS", os.path.join(LOOPS_HOME, "009-grid"))
NIGHTS = os.path.join(LOOPS_HOME, "pm", "nights")
DECISIONS = os.path.join(LOOPS_HOME, "pm", "DECISIONS.md")
CHARTER = os.path.join(LOOPS_HOME, "pm", "CHARTER.md")
TODAY = dt.date.today()


def dial(key, default=None):
    try:
        for line in open(CHARTER):
            if line.startswith(f"- {key}:"):
                return line.split(":", 1)[1].split("#", 1)[0].strip() or default
    except FileNotFoundError:
        pass
    return default


# ---------------------------------------------------------------- load the graph
def load_graph():
    g = {"cells": {}, "feeds": {}, "queue": {}, "decisions": [], "history": [], "date": str(TODAY)}
    covs = sorted(glob.glob(os.path.join(CORPUS, "data", "coverage-*.json")))
    if covs:
        c = json.load(open(covs[-1]))
        g["date"] = c.get("date", g["date"])
        for state, types in (c.get("matrix") or {}).items():
            for t, m in types.items():
                g["cells"][(state, t)] = {"rows": m.get("rows", 0), "filed": m.get("filed", 0), "verified": m.get("verified", 0), "feed": m.get("feed")}
        g["feeds"] = c.get("feeds") or {}
        g["states_tab"] = c.get("states_tab") or {}
        g["totals"] = c.get("totals") or {}
    qp = os.path.join(CORPUS, "data", "extract-queue.json")
    if os.path.exists(qp):
        q = json.load(open(qp))
        g["queue"] = {"resolve": q.get("eligible_resolve", 0), "extract": q.get("eligible_extract", 0),
                      "by_state": {}}
        for r in (q.get("resolve") or []) + (q.get("extract") or []):
            g["queue"]["by_state"].setdefault(r.get("state", "?"), 0)
            g["queue"]["by_state"][r.get("state", "?")] += 1
    g["decisions"] = read_decisions()
    g["history"] = read_history()
    return g


def read_decisions():
    out = []
    try:
        text = open(DECISIONS).read()
    except FileNotFoundError:
        return out
    for m in re.finditer(r"^## (D-\d+)[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S):
        body = m.group(2)
        f = lambda k, d="": (re.search(r"^- %s: *(.+)$" % k, body, re.M) or [None, d])[1].strip()
        out.append({"id": m.group(1), "status": f("status", "pending"), "blocks": f("blocks"), "question": f("question"), "date": f("date")})
    return out


def read_history():
    """Every dated loop section, newest first: (date, loop, progress, action_key)."""
    rows = []
    for p in glob.glob(os.path.join(NIGHTS, "loops", "L-*.md")):
        lid = os.path.basename(p)[:-3]
        if "backlog" in lid:
            continue
        text = open(p).read()
        for m in re.finditer(r"^## (\d{4}-\d{2}-\d{2})[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S):
            body = m.group(2)
            prog = "yes" if re.search(r"^progress: *yes", body, re.M) else ("no" if re.search(r"^progress: *no", body, re.M) else "?")
            key = (re.search(r"^action: *(\S+)", body, re.M) or [None, ""])[1]
            rows.append({"date": m.group(1), "loop": lid, "progress": prog, "action": key})
    # plan files record the planner's own picks too
    for p in glob.glob(os.path.join(NIGHTS, "plan-*.md")):
        text = open(p).read()
        d = os.path.basename(p)[5:15]
        k = (re.search(r"^pick: *(\S+)", text, re.M) or [None, ""])[1]
        if k:
            rows.append({"date": d, "loop": "planner", "progress": "?", "action": k})
    rows.sort(key=lambda r: r["date"], reverse=True)
    return rows


# ---------------------------------------------------------------- candidate actions
def candidates(g):
    acts = []
    cells, feeds, q = g["cells"], g["feeds"], g.get("queue", {})
    states = sorted({s for s, _ in cells} | {f.get("state") for f in feeds.values() if f.get("state")})

    # 1. verify: extract figures where documents are ready
    if q.get("extract", 0) > 0:
        acts.append(dict(key="extract-figures", value=9, readiness=min(1, q["extract"] / 5), cost=8,
                         why=f"{q['extract']} permits have a document ready and no verified figures yet; verified fraction is {g.get('totals', {}).get('verified_fraction', 0):.0%}"))
    # 2. resolve: turn record pages into document links (unlocks 1)
    if q.get("resolve", 0) > 0:
        acts.append(dict(key="resolve-documents", value=7 if q.get("extract", 0) == 0 else 4, readiness=min(1, q["resolve"] / 5), cost=6,
                         why=f"{q['resolve']} filed permits point at a record page, not a document; nothing can be verified until they resolve"))
    # 3. onboard: a state whose feed is live but has no rows in the sheet
    for fid, f in feeds.items():
        s = f.get("state")
        if not s:
            continue
        has_rows = any(st == s and c["rows"] > 0 for (st, _), c in cells.items())
        if f.get("ok") and (f.get("rows") or 0) > 0 and not has_rows:
            acts.append(dict(key=f"onboard-{s.lower()}", value=8, readiness=1, cost=5,
                             why=f"feed {fid} is live with {f['rows']} rows but {s} has no rows in the sheet"))
    # 4. widen: a state with rows in one permit type only, whose feed has more
    for s in states:
        typed = [(t, c) for (st, t), c in cells.items() if st == s and c["rows"] > 0]
        if 0 < len(typed) <= 1:
            acts.append(dict(key=f"widen-{s.lower()}", value=5, readiness=0.7, cost=5,
                             why=f"{s} has rows in {len(typed)} permit type only ({typed[0][0]}); the matrix is {len(typed)}/{len(set(t for _, t in cells))} for that state"))
    # 5. stale feeds
    for fid, f in feeds.items():
        lc = f.get("last_change")
        if f.get("ok") and lc and lc != "—":
            try:
                age = (TODAY - dt.date.fromisoformat(lc[:10])).days
            except ValueError:
                age = 0
            if age >= 14:
                acts.append(dict(key=f"check-feed-{fid}", value=3, readiness=1, cost=2,
                                 why=f"feed {fid} has not changed in {age} days; confirm the agency, not the parser, is quiet"))
        if not f.get("ok"):
            acts.append(dict(key=f"fix-feed-{fid}", value=6, readiness=1, cost=3, why=f"feed {fid} reports ok: false"))
    # 6. ledger link: sites in the sheet not linked to the curated ledger
    t = g.get("totals", {})
    if t.get("sites", 0) and t.get("ledger_linked", 0) < t["sites"] * 0.2:
        acts.append(dict(key="link-ledger", value=4, readiness=0.8, cost=4,
                         why=f"only {t['ledger_linked']} of {t['sites']} sites are linked to the curated ledger, so the News page cannot see most permits"))
    return acts


# ---------------------------------------------------------------- score
def score(acts, g, repeat_window=3):
    recent = {}
    for h in g["history"]:
        if h["action"]:
            recent.setdefault(h["action"], []).append(h)
    pending = {d["blocks"]: d for d in g["decisions"] if d["status"] == "pending" and d["blocks"]}
    out = []
    for a in acts:
        s = a["value"] * a["readiness"] / a["cost"]
        notes = []
        hist = recent.get(a["key"], [])
        last_n = [h for h in hist if (TODAY - dt.date.fromisoformat(h["date"])).days < repeat_window]
        if last_n:
            s *= 0.35
            notes.append(f"done {len(last_n)}× in the last {repeat_window} nights")
        if len(hist) >= 2 and all(h["progress"] == "no" for h in hist[:2]):
            s = 0
            notes.append("parked: two no-progress nights")
        if a["key"] in pending:
            s = 0
            notes.append(f"blocked by {pending[a['key']]['id']}: {pending[a['key']]['question']}")
        out.append(dict(a, score=round(s, 3), notes=notes))
    out.sort(key=lambda x: -x["score"])
    return out


def pick_line(ranked):
    if not ranked or ranked[0]["score"] <= 0:
        return None, "no runnable focus tonight; every candidate is blocked, parked, or absent"
    p = ranked[0]
    return p["key"], f"[planner] Tonight's focus: {p['key']}. Why: {p['why']}. Record `action: {p['key']}` in the loop's dated section."


def write_plan(ranked, key, line, date):
    os.makedirs(NIGHTS, exist_ok=True)
    p = os.path.join(NIGHTS, f"plan-{date}.md")
    with open(p, "w") as f:
        f.write(f"# Plan — {date}\n\npick: {key or 'none'}\n\n{line}\n\n## Ranked\n")
        for r in ranked:
            f.write(f"- {r['key']} · score {r['score']} · {r['why']}" + (f" · {'; '.join(r['notes'])}" if r["notes"] else "") + "\n")
    return p


# ---------------------------------------------------------------- simulate
def apply_effect(g, key):
    """What one successful night of this action does to the graph. Rough on purpose."""
    q = g.setdefault("queue", {"resolve": 0, "extract": 0})
    t = g.setdefault("totals", {})
    if key == "resolve-documents":
        n = min(5, q["resolve"]); q["resolve"] -= n; q["extract"] += n
    elif key == "extract-figures":
        n = min(5, q["extract"]); q["extract"] -= n
        t["verified"] = t.get("verified", 0) + n; t["verified_fraction"] = t["verified"] / max(1, t.get("permits", 1))
    elif key.startswith("onboard-"):
        s = key[8:].upper(); g["cells"][(s, "air")] = {"rows": 20, "filed": 10, "verified": 0, "feed": None}
    elif key.startswith("widen-"):
        s = key[6:].upper(); g["cells"][(s, "stormwater-construction")] = {"rows": 10, "filed": 5, "verified": 0, "feed": None}
    elif key == "link-ledger":
        t["ledger_linked"] = t.get("ledger_linked", 0) + 15
    elif key.startswith("check-feed-") or key.startswith("fix-feed-"):
        fid = key.split("-", 2)[2]; g["feeds"][fid]["last_change"] = str(TODAY); g["feeds"][fid]["ok"] = True
    g["history"].insert(0, {"date": str(TODAY), "loop": "sim", "progress": "yes", "action": key})


def simulate(nights):
    import copy
    g = load_graph()
    picks = []
    for n in range(nights):
        ranked = score(candidates(g), g)
        key, line = pick_line(ranked)
        top3 = [(r["key"], r["score"]) for r in ranked[:3]]
        picks.append(key)
        print(f"night {n + 1}: {key or 'none'}\n   {ranked[0]['why'] if ranked else ''}\n   next best: {top3[1:]}")
        if not key:
            break
        apply_effect(g, key)
        # a simulated night is "yesterday" for the next one
        for h in g["history"]:
            if h["loop"] == "sim":
                h["date"] = str(dt.date.fromisoformat(h["date"]) - dt.timedelta(days=1))
    distinct = len(set(k for k in picks if k))
    print(f"\n{len(picks)} nights · {distinct} distinct picks · repeats: {len(picks) - distinct}")
    return picks


# ---------------------------------------------------------------- decisions
def decisions_from(envelope):
    text = open(envelope).read()
    existing = read_decisions()
    n = max([int(d["id"][2:]) for d in existing] + [0])
    qs = set(d["question"] for d in existing)
    new = []
    for m in re.finditer(r"^- Need from you: *(.+)$", text, re.M):
        q = m.group(1).strip()
        if q in qs or q.lower().startswith(("nothing", "none")):
            continue
        n += 1
        new.append(f"\n## D-{n:02d} — {q[:80]}\n- date: {TODAY}\n- status: pending\n- question: {q}\n- blocks: \n- chosen: \n- evidence: pm/nights/{TODAY}.md\n")
    if new:
        header = "" if os.path.exists(DECISIONS) else "# Decisions\n\nWhat a run could not settle. Set `status: settled` and fill `chosen:` to release it. Put an action key in `blocks:` to keep the planner off it until then.\n"
        with open(DECISIONS, "a") as f:
            f.write(header + "".join(new))
    return len(new)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["plan", "simulate", "decisions", "graph"])
    ap.add_argument("--nights", type=int, default=5)
    ap.add_argument("--from", dest="src")
    ap.add_argument("--date", default=str(TODAY))
    a = ap.parse_args()
    if a.cmd == "graph":
        g = load_graph(); g["cells"] = {f"{s}/{t}": v for (s, t), v in g["cells"].items()}; print(json.dumps(g, indent=1, default=str)[:4000])
    elif a.cmd == "plan":
        g = load_graph(); ranked = score(candidates(g), g); key, line = pick_line(ranked)
        p = write_plan(ranked, key, line, a.date)
        for r in ranked: print(f"{r['score']:6.2f}  {r['key']:<28} {r['why']}" + (f"  [{'; '.join(r['notes'])}]" if r["notes"] else ""))
        print(f"\n{line}\nwrote {p}")
    elif a.cmd == "simulate":
        simulate(a.nights)
    else:
        print(decisions_from(a.src))


if __name__ == "__main__":
    main()
