"""
Loops — Navi's write path for ~/ventures/pm/LOOPS.md (Loops ruling, 2026-09-14).

Navi is the only place besides the desk where you edit loop knobs: goal, budget,
cadence, model, pause/resume. It also reads the morning standup back from the latest
night/day report in the four-line plain-English format. Everything here lands in a
ventures file, dated, marked "via Navi". The night fence never touches this module.

Vocabulary on the phone: Loop, Run, Order, Decision. Nothing else.
"""

import logging
import os
import re
from datetime import date, datetime

logger = logging.getLogger(__name__)

STATES = ("draft", "trial", "active", "parked", "done")
CADENCES = ("nightly", "every-2nd-night", "every-3rd-night", "weekly")
MODELS = {
    "sonnet": "claude-sonnet-5",
    "opus": "claude-opus-5",
    "fable": "claude-fable-5",
    "haiku": "claude-haiku-4-5-20251001",
}
TRIAL_RUNS = 3          # runs before a trial loop may be promoted to active
FOUR_LINES = ("Trying to", "Did", "Decided", "Need from you")


def _root():
    try:
        import config
        root = getattr(config, "VENTURES_ROOT", None)
    except Exception:
        root = None
    return root or os.path.expanduser("~/ventures")


def _loops_path():
    return os.path.join(_root(), "pm", "LOOPS.md")


def _state_dir():
    return os.path.join(_root(), "pm", "nights", "loops")


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _dial(name, default=None):
    """A `- name: value` line from pm/CHARTER.md (same reader as the wrapper)."""
    try:
        with open(os.path.join(_root(), "pm", "CHARTER.md")) as f:
            for line in f:
                m = re.match(rf"^- {re.escape(name)}: *(.+?)\s*(#.*)?$", line)
                if m:
                    return m.group(1).strip()
    except Exception:
        pass
    return default


# ---- readers ---------------------------------------------------------------

_SECTION_RE = re.compile(r"^## (L-\d+)\s*[—-]?\s*([^\n]*)\n(.*?)(?=^## |\Z)", re.M | re.S)


def _field(body, key, default=""):
    m = re.search(rf"^- {re.escape(key)}: *(.+?)$", body, re.M)
    return m.group(1).strip() if m else default


def parse_loops():
    """Every loop section in LOOPS.md as a dict. Never raises; [] on failure."""
    try:
        text = open(_loops_path()).read()
    except Exception as e:
        logger.error(f"LOOPS.md unreadable: {e}")
        return []
    loops = []
    for m in _SECTION_RE.finditer(text):
        lid, name, body = m.group(1), m.group(2).strip(), m.group(3)
        status_raw = _field(body, "status")
        loops.append({
            "id": lid,
            "name": name,
            "status": status_raw.split()[0].strip("—-,;:") if status_raw else "missing",
            "status_raw": status_raw,
            "goal": _field(body, "goal"),
            "lane": _field(body, "lane", "any"),
            "cadence": _field(body, "cadence"),
            "model": _field(body, "model"),
            "per": _field(body, "budget_per_iteration_usd"),
            "total": _field(body, "budget_loop_total_usd"),
            "review_by": _field(body, "review_by"),
        })
    return loops


def runs(lid):
    """(count, last_date, last_progress) from the loop's append-only state file."""
    try:
        st = open(os.path.join(_state_dir(), lid + ".md")).read()
    except FileNotFoundError:
        return 0, None, None
    sects = re.findall(r"^## (\d{4}-\d{2}-\d{2})[^\n]*\n(.*?)(?=^## |\Z)", st, re.M | re.S)
    if not sects:
        return 0, None, None
    last_date, last_body = sects[-1]
    prog = re.search(r"^progress: *(yes|no)", last_body, re.M)
    return len(sects), last_date, (prog.group(1) if prog else None)


def _short_model(model):
    for short, full in MODELS.items():
        if model == full or model == short:
            return short
    return model or "charter"


def _when(iso):
    if not iso:
        return "never"
    try:
        d = (date.today() - date.fromisoformat(iso)).days
    except ValueError:
        return iso
    return {0: "today", 1: "yesterday"}.get(d, f"{d}d ago")


def quota_line():
    """The CLI's cached weekly utilization — the real currency behind the dollar proxies."""
    try:
        import json
        u = json.load(open(os.path.expanduser("~/.claude.json")))["cachedUsageUtilization"]
        lim = {l["kind"]: l for l in u["utilization"].get("limits", [])}
        wk, sc = lim.get("weekly_all", {}), lim.get("weekly_scoped", {})
        age_h = (datetime.now().timestamp() - u["fetchedAtMs"] / 1000) / 3600
        reset = datetime.fromisoformat(wk["resets_at"]).astimezone() if wk.get("resets_at") else None
        left = f", {(reset - datetime.now(reset.tzinfo)).total_seconds() / 86400:.1f}d left" if reset else ""
        return (f"quota: week {wk.get('percent')}% used"
                + (f" ({sc.get('scope', {}).get('model', {}).get('display_name', 'scoped')} {sc.get('percent')}%)" if sc else "")
                + (f", resets {reset.strftime('%a %H:%M')}{left}" if reset else "")
                + f" · as of {age_h:.0f}h ago" + (" (stale)" if age_h > 36 else ""))
    except Exception:
        return "quota: not cached"


def render_list():
    loops = parse_loops()
    if not loops:
        return ["🔁 LOOPS: LOOPS.md unreadable or empty"]
    lines = ["🔁 LOOPS", quota_line()]
    for l in loops:
        n, last, prog = runs(l["id"])
        per, tot = l["per"] or "?", l["total"] or "?"
        flag = {"trial": "🧪", "active": "🟢", "parked": "⏸", "done": "✅", "draft": "📝"}.get(l["status"], "❔")
        head = (f"{flag} {l['id']} {l['name']} — {l['status']} · {l['cadence'] or '?'} · "
                f"{_short_model(l['model'])} · ${per}/run, ${tot} total")
        lines.append(head)
        lines.append(f"   runs: {n}, last {_when(last)}"
                     + (f" ({'progress' if prog == 'yes' else 'no progress'})" if prog else "")
                     + f" · review by {l['review_by'] or '?'}")
        goal = l["goal"] or f"(none — set with /loop {l['id']} goal …)"
        lines.append(f"   goal: {goal}")
    lines.append("")
    lines.append("edit: /loop L-NN goal|budget|total|cadence|model|pause|resume|promote …")
    return lines


# ---- writer (ported from 00-ops/glass/serve.mjs writeLoop/validate) ------------

def _write_field(lid, key, value):
    """Replace (or append) one `- key: value` line inside the loop's section.
    Multi-line continuation of the old value is replaced too. Returns True if changed."""
    path = _loops_path()
    text = open(path).read()
    sec = re.search(rf"^## {re.escape(lid)}\b[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not sec:
        raise ValueError(f"{lid} is not a section in pm/LOOPS.md")
    body = sec.group(1)
    line = f"- {key}: {value}"
    field_re = re.compile(rf"^- {re.escape(key)}: *[^\n]*(?:\n[ \t]+\S[^\n]*)*", re.M)
    if field_re.search(body):
        new_body = field_re.sub(lambda _m: line, body, count=1)
    else:
        # put new knobs right after status so the section reads top-down
        status_re = re.compile(r"^- status: *[^\n]*(?:\n[ \t]+\S[^\n]*)*\n", re.M)
        if status_re.search(body):
            new_body = status_re.sub(lambda m: m.group(0) + line + "\n", body, count=1)
        else:
            new_body = body.rstrip("\n") + "\n" + line + "\n"
    if new_body == body:
        return False
    start = sec.start(1)
    open(path, "w").write(text[:start] + new_body + text[sec.end(1):])
    return True


def _log(lid, what):
    try:
        log_path = os.path.join(_root(), "00-ops", "night", "logs", f"{date.today().isoformat()}.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a") as f:
            f.write(f"[navi] {_now()} {lid} {what} (the user via Navi)\n")
    except Exception as e:
        logger.error(f"loop log failed: {e}")


def _find(lid):
    for l in parse_loops():
        if l["id"] == lid:
            return l
    return None


def set_knob(lid, key, value):
    """goal | budget | total | cadence | model → validated write. Returns reply text."""
    l = _find(lid)
    if not l:
        return f"{lid} is not a loop. /loops lists them."
    value = value.strip()
    if key == "goal":
        if not value:
            return "Usage: /loop L-NN goal <one plain sentence>"
        if len(value) > 160:
            return "Keep the goal to one sentence (≤160 characters)."
        _write_field(lid, "goal", value)
        _log(lid, f"goal set: {value}")
        return f"{lid} goal → {value}"
    if key in ("budget", "total"):
        try:
            v = float(value)
        except ValueError:
            return f"Usage: /loop L-NN {key} <dollars>"
        if v <= 0:
            return "Budget must be above 0."
        cap = float(_dial("cost_cap_per_night_usd", 15))
        if key == "budget" and v > cap:
            return f"${v:g} is over the night per-run cap ${cap:g}; the run would skip this loop."
        other = float(l["total"] or 0) if key == "budget" else float(l["per"] or 0)
        if key == "budget" and other and other < v:
            return f"Per-run ${v:g} is above the loop total ${other:g} — raise total first."
        if key == "total" and other and v < other:
            return f"Total ${v:g} is below one run (${other:g})."
        field = "budget_per_iteration_usd" if key == "budget" else "budget_loop_total_usd"
        _write_field(lid, field, f"{v:g}")
        _log(lid, f"{field} → {v:g}")
        return f"{lid} {key} → ${v:g}"
    if key == "cadence":
        if value not in CADENCES:
            return "Cadence must be one of: " + ", ".join(CADENCES)
        _write_field(lid, "cadence", value)
        _log(lid, f"cadence → {value}")
        return f"{lid} cadence → {value}"
    if key == "model":
        full = MODELS.get(value, value)
        if not full.startswith("claude-"):
            return "Model must be sonnet, opus, fable, haiku, or a full claude-* id."
        _write_field(lid, "model", full)
        _log(lid, f"model → {full}")
        return f"{lid} model → {full}"
    return "Knobs: goal · budget · total · cadence · model · pause · resume · promote"


def set_state(lid, action):
    l = _find(lid)
    if not l:
        return f"{lid} is not a loop. /loops lists them."
    n, _, _ = runs(lid)
    if action == "pause":
        if l["status"] == "parked":
            return f"{lid} is already parked."
        _write_field(lid, "status", f"parked — was {l['status']} (the user via Navi {_now()})")
        _log(lid, "paused")
        return f"⏸ {lid} parked. It stays off the line until /loop {lid} resume."
    if action == "resume":
        new = "active" if n >= TRIAL_RUNS else "trial"
        _write_field(lid, "status", f"{new} (resumed via Navi {_now()})")
        _log(lid, f"resumed → {new}")
        return f"▶️ {lid} → {new} ({n} runs so far)."
    if action == "promote":
        if n < TRIAL_RUNS:
            return f"{lid} has {n} run(s); trial needs {TRIAL_RUNS} before promotion."
        _write_field(lid, "status", f"active (promoted via Navi {_now()})")
        _log(lid, "promoted → active")
        return f"🟢 {lid} → active."
    return "Actions: pause · resume · promote"


# ---- morning standup: the four lines per loop/order --------------------------

def _latest_report(kind):
    d = os.path.join(_root(), "pm", "nights" if kind == "night" else "days")
    try:
        names = sorted(n for n in os.listdir(d) if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.md", n))
    except FileNotFoundError:
        return None, None
    if not names:
        return None, None
    return names[-1][:-3], os.path.join(d, names[-1])


def _four_lines(body):
    """Reports wrap at ~90 columns, so a line's value continues on indented lines."""
    out = []
    for label in FOUR_LINES:
        m = re.search(rf"^- {label}: *([^\n]*(?:\n[ \t]+\S[^\n]*)*)", body, re.M)
        if m:
            val = re.sub(r"\s*\n\s*", " ", m.group(1)).replace("`", "").strip()
            out.append(f"   {label}: {val}")
    return out


def standup_lines(only_today=True):
    """Plain-English read-back of the latest night and day reports."""
    lines = []
    for kind in ("night", "day"):
        rdate, path = _latest_report(kind)
        if not path:
            continue
        if only_today and rdate != date.today().isoformat():
            lines.append(f"🌙 {kind}: no report today (latest {rdate})" if kind == "night"
                         else f"☀️ {kind}: no report today (latest {rdate})")
            continue
        text = open(path).read()
        header = f"🌙 NIGHT {rdate}" if kind == "night" else f"☀️ DAY {rdate}"
        lines.append(header)
        found = False
        for m in re.finditer(r"^## ((?:L|N|D)-\d+)[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S):
            found = True
            lines.append(f" {m.group(1)}")
            fl = _four_lines(m.group(2))
            if fl:
                lines.extend(fl)
            else:
                first = [x.strip() for x in m.group(2).splitlines() if x.strip()][:2]
                lines.extend("   " + x[:140] for x in first)
                lines.append("   (old report format — no four lines)")
        if not found:
            lines.append("   nothing ran")
        dec = re.search(r"^## Decisions needed[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
        if dec:
            items = re.findall(r"^(?:[-*]|\d+\.) +([^\n]*(?:\n[ \t]+\S[^\n]*)*)", dec.group(1), re.M)
            if items:
                lines.append(" Decisions for you:")
                for x in items[:5]:
                    x = re.sub(r"\s*\n\s*", " ", x).replace("**", "").replace("`", "").strip()
                    lines.append("   " + (x[:220] + ("…" if len(x) > 220 else "")))
    return lines or ["no reports found"]


# ---- command surface -------------------------------------------------------

def handle_loops_command(text):
    """'/loops [standup]'  and  '/loop L-NN <knob> <value>' → reply str."""
    parts = text.split()
    cmd = parts[0].lower()
    if cmd == "/loops":
        if len(parts) > 1 and parts[1].lower() == "standup":
            return "\n".join(standup_lines(only_today=False))
        return "\n".join(render_list())
    # /loop
    if len(parts) < 3:
        return ("Usage:\n/loop L-NN goal <sentence>\n/loop L-NN budget <$ per run>\n"
                "/loop L-NN total <$ for the loop>\n/loop L-NN cadence nightly|every-2nd-night|every-3rd-night|weekly\n"
                "/loop L-NN model sonnet|opus|fable\n/loop L-NN pause|resume|promote")
    lid, key = parts[1].upper(), parts[2].lower()
    if not re.fullmatch(r"L-\d+", lid):
        return "Loop ids look like L-03."
    if key in ("pause", "resume", "promote"):
        return set_state(lid, key)
    value = text.split(None, 3)[3] if len(parts) > 3 else ""
    try:
        return set_knob(lid, key, value)
    except Exception as e:
        return f"Write failed: {e}"
