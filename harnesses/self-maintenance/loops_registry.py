"""loops_registry — the few readers and writers loopctl needs for pm/LOOPS.md.

On the author's machine these live in the phone bot's loops module; they are vendored here
so the lane runs standalone. Every write is one `- key: value` line inside one `## L-NN`
section, and every write is logged to the lane's log for the day.

Root: `$LOOPS_HOME`, default `~/ventures` (the same home the Loops harness uses).
"""
import os
import re
from datetime import date, datetime

STATES = ("draft", "trial", "active", "parked", "done")
CADENCES = ("nightly", "every-2nd-night", "every-3rd-night", "weekly")

_SECTION_RE = re.compile(r"^## (L-\d+)\s*[—-]?\s*([^\n]*)\n(.*?)(?=^## |\Z)", re.M | re.S)


def _root():
    return os.environ.get("LOOPS_HOME") or os.path.expanduser("~/ventures")


def _loops_path():
    return os.path.join(_root(), "pm", "LOOPS.md")


def _state_dir():
    return os.path.join(_root(), "pm", "nights", "loops")


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _dial(name, default=None):
    """A `- name: value` line from pm/CHARTER.md (same reader as the runner)."""
    try:
        with open(os.path.join(_root(), "pm", "CHARTER.md")) as f:
            for line in f:
                m = re.match(rf"^- {re.escape(name)}: *(.+?)\s*(#.*)?$", line)
                if m:
                    return m.group(1).strip()
    except Exception:
        pass
    return default


def _field(body, key, default=""):
    m = re.search(rf"^- {re.escape(key)}: *(.+?)$", body, re.M)
    return m.group(1).strip() if m else default


def parse_loops():
    """Every loop section in LOOPS.md as a dict. Never raises; [] on failure."""
    try:
        text = open(_loops_path()).read()
    except Exception:
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
            "pod": _field(body, "pod"),
            "cadence": _field(body, "cadence"),
            "model": _field(body, "model"),
            "per": _field(body, "budget_per_iteration_usd"),
            "total": _field(body, "budget_loop_total_usd"),
            "review_by": _field(body, "review_by"),
        })
    return loops


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
    """One line in today's night log, so a registry write is never silent."""
    try:
        log_path = os.path.join(_root(), "00-ops", "night", "logs", f"{date.today().isoformat()}.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a") as f:
            f.write(f"[loopctl] {_now()} {lid} {what}\n")
    except Exception:
        pass


def _find(lid):
    for l in parse_loops():
        if l["id"] == lid:
            return l
    return None
