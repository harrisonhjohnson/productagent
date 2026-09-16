#!/usr/bin/env python3
"""Plan quota for Loops: snapshot, floor gate, and the dollars→percent estimate.

Claude Code caches the plan's utilization (five-hour and seven-day windows, percent used,
reset time) in ~/.claude.json under `cachedUsageUtilization` whenever an interactive
session fetches it. This module:

  snapshot   append a row to quota-ledger.jsonl when that cache changes (the checker calls
             this every ten minutes; it costs nothing)
  status     print the freshest snapshot as JSON: week/5h percent used, resets, age in hours
  estimate   --usd X [--model M]: percent of the week X dollars is worth, as JSON with a
             confidence tag: "calibrated on N pairs", "seeded", or "none"
  line       --usd X [--model M]: one plain sentence for the morning report

Calibration: the runner's cost-ledger rows carry `finished` timestamps. For every pair of
consecutive snapshots whose seven-day percent rose within the same reset period, the
dollars of runs finished between them give one (dollars, points) pair. The rate is the
median points-per-dollar over pairs that contain at least one run. Your own daytime use
between snapshots adds noise, which is why it is a median and why it says "estimate".

Seed: if the charter sets `plan_weekly_usd_equivalent`, that is used until enough pairs
exist. It ships blank. Nothing here invents a number for you.
"""
import argparse, datetime as dt, json, os, statistics, sys

LOOPS_HOME = os.environ.get("LOOPS_HOME", os.path.expanduser("~/ventures"))
OPS = os.path.join(LOOPS_HOME, "00-ops", "night")
QUOTA_LEDGER = os.path.join(OPS, "quota-ledger.jsonl")
COST_LEDGER = os.path.join(OPS, "cost-ledger.jsonl")
CHARTER = os.path.join(LOOPS_HOME, "pm", "CHARTER.md")
CLAUDE_JSON = os.environ.get("CLAUDE_CONFIG_JSON", os.path.expanduser("~/.claude.json"))
MIN_PAIRS = 5


def dial(key, default=None):
    try:
        for line in open(CHARTER):
            if line.startswith(f"- {key}:"):
                v = line.split(":", 1)[1].split("#", 1)[0].strip()
                return v or default
    except FileNotFoundError:
        pass
    return default


def _rows(path):
    try:
        return [json.loads(l) for l in open(path) if l.strip()]
    except FileNotFoundError:
        return []


def _parse_ts(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone()
    except ValueError:
        try:
            return dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").astimezone()
        except ValueError:
            return None


def read_cache():
    """Normalise whatever shape the CLI cached into {fetched_at, windows:{name:{pct,resets_at}}}."""
    try:
        d = json.load(open(CLAUDE_JSON))
    except (FileNotFoundError, ValueError):
        return None
    u = d.get("cachedUsageUtilization")
    if not u:
        return None
    fetched = u.get("fetchedAtMs")
    windows = {}
    src = u.get("utilization", u)
    limits = src.get("limits") if isinstance(src, dict) else None
    if isinstance(limits, list):                      # shape A: limits[{kind, percent, resets_at, scope}]
        for l in limits:
            kind = l.get("kind", "")
            name = {"weekly_all": "seven_day", "five_hour": "five_hour", "session": "five_hour"}.get(kind, kind)
            if kind == "weekly_scoped":
                m = ((l.get("scope") or {}).get("model") or {}).get("display_name", "scoped")
                name = "seven_day_" + m.lower().split()[0]
            windows[name] = {"pct": l.get("percent"), "resets_at": l.get("resets_at")}
    elif isinstance(src, dict):                       # shape B: {five_hour:{utilization,resets_at}, seven_day:{...}}
        for k, v in src.items():
            if isinstance(v, dict) and ("utilization" in v or "percent" in v):
                pct = v.get("utilization", v.get("percent"))
                if isinstance(pct, (int, float)) and pct <= 1.0 and k != "utilization_pct":
                    pct = pct * 100
                windows[k] = {"pct": pct, "resets_at": v.get("resets_at")}
    if not windows:
        return None
    return {"fetched_at_ms": fetched, "windows": windows}


def snapshot():
    cur = read_cache()
    if not cur:
        return 0
    rows = _rows(QUOTA_LEDGER)
    if rows and rows[-1].get("fetched_at_ms") == cur["fetched_at_ms"] and rows[-1].get("windows") == cur["windows"]:
        return 0
    cur["ts"] = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    os.makedirs(OPS, exist_ok=True)
    with open(QUOTA_LEDGER, "a") as f:
        f.write(json.dumps(cur) + "\n")
    return 1


def status():
    rows = _rows(QUOTA_LEDGER)
    cur = read_cache()
    if cur:
        cur = dict(cur, ts=dt.datetime.now().astimezone().isoformat(timespec="seconds"))
    latest = cur or (rows[-1] if rows else None)
    if not latest:
        return {"available": False}
    fetched = latest.get("fetched_at_ms")
    age_h = (dt.datetime.now().timestamp() - fetched / 1000) / 3600 if fetched else None
    w = latest["windows"]
    week = w.get("seven_day") or {}
    five = w.get("five_hour") or {}
    return {
        "available": True, "age_h": round(age_h, 1) if age_h is not None else None,
        "week_pct": week.get("pct"), "week_resets_at": week.get("resets_at"),
        "five_hour_pct": five.get("pct"), "five_hour_resets_at": five.get("resets_at"),
        "scoped": {k: v.get("pct") for k, v in w.items() if k.startswith("seven_day_")},
    }


def _window_for(model):
    m = (model or "").lower()
    if "sonnet" in m: return "seven_day_sonnet"
    if "opus" in m: return "seven_day_opus"
    return "seven_day"


def calibrate(model=None):
    """Return (points_per_dollar, n_pairs) from the two ledgers, or (None, 0)."""
    snaps = _rows(QUOTA_LEDGER)
    runs = [r for r in _rows(COST_LEDGER) if r.get("finished") and r.get("cost_usd")]
    if len(snaps) < 2 or not runs:
        return None, 0
    win = _window_for(model)
    rates = []
    for a, b in zip(snaps, snaps[1:]):
        wa, wb = a["windows"].get(win) or a["windows"].get("seven_day"), b["windows"].get(win) or b["windows"].get("seven_day")
        if not wa or not wb or wa.get("resets_at") != wb.get("resets_at"):
            continue
        dp = (wb.get("pct") or 0) - (wa.get("pct") or 0)
        if dp <= 0:
            continue
        ta, tb = _parse_ts(a.get("ts")), _parse_ts(b.get("ts"))
        if not ta or not tb:
            continue
        usd = sum(r["cost_usd"] for r in runs if (lambda t: t and ta < t <= tb)(_parse_ts(r["finished"])))
        if usd <= 0:
            continue
        rates.append(dp / usd)
    if len(rates) < MIN_PAIRS:
        return None, len(rates)
    return statistics.median(rates), len(rates)


def estimate(usd, model=None):
    rate, n = calibrate(model)
    if rate:
        return {"pct": round(usd * rate, 1), "basis": f"calibrated on {n} pairs", "confidence": "calibrated"}
    seed = dial("plan_weekly_usd_equivalent")
    try:
        seed = float(seed) if seed else None
    except ValueError:
        seed = None
    if seed and seed > 0:
        return {"pct": round(usd / seed * 100, 1), "basis": f"seeded from plan_weekly_usd_equivalent={seed:g} in the charter", "confidence": "seeded", "pairs_so_far": n}
    return {"pct": None, "basis": f"calibrating ({n} of {MIN_PAIRS} pairs)", "confidence": "none", "pairs_so_far": n}


def line(usd, model=None):
    e = estimate(usd, model)
    s = status()
    parts = [f"spent ${usd:.2f}"]
    if e["pct"] is not None:
        parts.append(f"≈ {e['pct']:g}% of the week ({e['basis']})")
    else:
        parts.append(f"share of the week unknown, {e['basis']}")
    if s.get("available") and s.get("week_pct") is not None:
        w = f"week now {s['week_pct']:g}% used"
        r = _parse_ts(s.get("week_resets_at"))
        if r: w += f", resets {r.strftime('%a %H:%M')}"
        if s.get("age_h") is not None and s["age_h"] > 1: w += f" (as of {s['age_h']:.0f}h ago)"
        parts.append(w)
    return " · ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["snapshot", "status", "estimate", "line"])
    ap.add_argument("--usd", type=float, default=0.0)
    ap.add_argument("--model", default=None)
    a = ap.parse_args()
    if a.cmd == "snapshot":
        print(snapshot())
    elif a.cmd == "status":
        print(json.dumps(status()))
    elif a.cmd == "estimate":
        print(json.dumps(estimate(a.usd, a.model)))
    else:
        print(line(a.usd, a.model))


if __name__ == "__main__":
    main()
