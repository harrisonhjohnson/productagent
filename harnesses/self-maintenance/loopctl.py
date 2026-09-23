#!/usr/bin/env python3
"""loopctl — the self-maintenance lane.

The one way an unattended run may touch the loop registry, and the one place a
"need from you" becomes a decision you can settle with a single word.

Night/day lane (unattended) may run:
  loopctl.py park   L-NN "<why>"           status → parked (never upward: no trial/active)
  loopctl.py done   L-NN "<why>"           status → done
  loopctl.py cadence L-NN <cadence>        nightly | every-2nd-night | every-3rd-night | weekly
  loopctl.py decide <pod> "<one sentence>" [--apply "<command>"] [--patch <file>]
                                           append a row to pm/nights/DECISIONS.md
  loopctl.py issue  <pod> "<error verbatim>" "<workaround>"
                                           append to pm/nights/pods/<pod>-issues.md
  loopctl.py interventions [YYYY-MM-DD]    count the night's asks (the metric)
  loopctl.py check  L-NN [YYYY-MM-DD]      run the loop's `checks:` block; append a verdict row to
                                           pm/nights/loops/L-NN.checks.jsonl. Advisory — the fence
                                           is still the gate. Exit 1 if any check failed.
                                           [--root DIR] [--cost N] [--since GIT-REF] [--model M]
                                           [--source night|bench] [--no-write]
  loopctl.py model L-NN <model>            move the loop's model pin. A cheaper model needs
                                           bench_passes_to_demote consecutive bench passes first.
                                           Unattended runs may only propose it as a decision,
                                           unless CHARTER says `loopctl_may_set_model: yes`.
  loopctl.py guard  L-NN                   after night_fails_to_restore failed nights in a row,
                                           put the loop back on the charter default model

You (attended) also run:
  loopctl.py apply  D-NNN                  run the row's apply command / patch, tick it
  loopctl.py park-decision D-NNN           tick it as parked, nothing runs

Goal, budgets, review_by, scope and any upward status change stay human acts.
Every write here logs to pm/LOG.md and the loop's state file.

Root: `$LOOPS_HOME`, default `~/ventures`. Lives in 00-ops/night/ next to the runner, with
loops_registry.py beside it.
"""
import os, re, sys, subprocess, datetime

VENT = os.environ.get("LOOPS_HOME") or os.path.expanduser("~/ventures")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loops_registry as reg  # _write_field / _log / _find / parse_loops

DECISIONS = os.path.join(VENT, "pm", "nights", "DECISIONS.md")
PODS_DIR = os.path.join(VENT, "pm", "nights", "pods")
LOG = os.path.join(VENT, "pm", "LOG.md")
CADENCES = reg.CADENCES
# extra bases a cited file may be relative to in `traceable` checks (colon-separated), e.g.
# the folder a corpus lives in when candidates files name paths relative to it
RESOLVE_BASES = [b for b in os.environ.get("CHECK_RESOLVE_BASES", "").split(":") if b]


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def log(line):
    with open(LOG, "a") as f:
        f.write(f"- {now()} loopctl: {line}\n")


def need(lid):
    l = reg._find(lid)
    if not l:
        sys.exit(f"{lid} is not a loop")
    return l


def cmd_park(lid, why):
    l = need(lid)
    reg._write_field(lid, "status", f"parked {now()[:10]} — {why} (was {l['status'].split()[0]}; loopctl)")
    reg._log(lid, f"parked via loopctl: {why}")
    log(f"{lid} parked — {why}")
    print(f"{lid} → parked")


def cmd_done(lid, why):
    need(lid)
    reg._write_field(lid, "status", f"done {now()[:10]} — {why} (loopctl)")
    reg._log(lid, f"done via loopctl: {why}")
    log(f"{lid} done — {why}")
    print(f"{lid} → done")


def cmd_cadence(lid, cad):
    need(lid)
    if cad not in CADENCES:
        sys.exit(f"cadence must be one of {', '.join(CADENCES)}")
    reg._write_field(lid, "cadence", cad)
    reg._log(lid, f"cadence → {cad} via loopctl")
    log(f"{lid} cadence → {cad}")
    print(f"{lid} cadence → {cad}")


def next_decision_id():
    if not os.path.exists(DECISIONS):
        return 1
    ids = [int(x) for x in re.findall(r"^- \[[ x~]\] D-(\d+)", open(DECISIONS).read(), re.M)]
    return (max(ids) + 1) if ids else 1


def cmd_decide(pod, sentence, apply=None, patch=None):
    if len(sentence) > 200:
        sys.exit("one sentence, ≤200 characters")
    did = f"D-{next_decision_id():03d}"
    os.makedirs(os.path.dirname(DECISIONS), exist_ok=True)
    if not os.path.exists(DECISIONS):
        open(DECISIONS, "w").write(
            "# Decisions — what only you can settle\n\n"
            "One row per ask. Settle a row with `loopctl.py apply D-NNN` (runs its `apply:` or\n"
            "`patch:` and ticks it) or `loopctl.py park-decision D-NNN` (ticks it `~`, nothing runs).\n"
            "A row without `apply:`/`patch:` is a judgment call; tick it by hand after deciding.\n"
            "The night appends; it never edits or removes rows.\n\n"
        )
    row = f"- [ ] {did} · {pod} · {now()[:10]} · {sentence}"
    if apply:
        row += f"\n      apply: {apply}"
    if patch:
        row += f"\n      patch: {patch}"
    with open(DECISIONS, "a") as f:
        f.write(row + "\n")
    log(f"{did} queued ({pod}): {sentence}")
    print(did)


def cmd_issue(pod, error, workaround):
    os.makedirs(PODS_DIR, exist_ok=True)
    p = os.path.join(PODS_DIR, f"{pod}-issues.md")
    if not os.path.exists(p):
        open(p, "w").write(f"# Known issues — pod {pod}\n\nRead before a run. Append-only.\n\n")
    with open(p, "a") as f:
        f.write(f"- {now()[:10]} · `{error}` → {workaround}\n")
    print(p)


def find_row(did):
    text = open(DECISIONS).read()
    m = re.search(rf"^- \[( )\] {re.escape(did)} ·[^\n]*(?:\n      (?:apply|patch): [^\n]*)*", text, re.M)
    if not m:
        sys.exit(f"{did} not found or already settled")
    return text, m


def tick(text, m, mark):
    new = text[:m.start()] + text[m.start():m.end()].replace("- [ ]", f"- [{mark}]", 1) + text[m.end():]
    open(DECISIONS, "w").write(new)


def cmd_apply(did):
    # unattended runs carry the runner's LANE; a human at a terminal does not
    if os.environ.get("LANE") in ("night", "day", "hourly") and not os.environ.get("LOOPCTL_ATTENDED"):
        sys.exit("apply is an attended command; the night queues, you apply")
    text, m = find_row(did)
    block = m.group(0)
    apply = re.search(r"^      apply: (.+)$", block, re.M)
    patch = re.search(r"^      patch: (.+)$", block, re.M)
    if apply:
        print(f"$ {apply.group(1)}")
        rc = subprocess.call(apply.group(1), shell=True, cwd=VENT)
    elif patch:
        pf = os.path.join(VENT, patch.group(1))
        rc = subprocess.call(["git", "apply", pf], cwd=VENT)
    else:
        rc = 0
        print(f"{did} has no apply/patch — ticking it as decided")
    if rc != 0:
        sys.exit(f"{did}: exited {rc}; row left open")
    tick(text, m, "x")
    log(f"{did} applied")
    print(f"{did} ✓")


def cmd_park_decision(did):
    text, m = find_row(did)
    tick(text, m, "~")
    log(f"{did} parked")
    print(f"{did} ~ parked")


def cmd_interventions(date=None):
    """The number the machine is judged by: how many times the morning had to act."""
    date = date or datetime.date.today().isoformat()
    report = os.path.join(VENT, "pm", "nights", f"{date}.md")
    needs = pastes = errors = 0
    if os.path.exists(report):
        t = open(report).read()
        needs = len([l for l in re.findall(r"^- Need from you: *(.+)$", t, re.M)
                     if not re.match(r"(nothing|none|no)\b", l.strip(), re.I)])
        pastes = len(re.findall(r"^    \S", t, re.M))
        errors = len(re.findall(r"(?i)^\*\*errors?", t, re.M)) + t.lower().count("denied")
    # paste blocks in any same-day edits-*.md (a "paste these" doc is interventions too)
    import glob
    for f in glob.glob(os.path.join(VENT, "pm", "nights", f"*edits-*{date}.md")):
        pastes += len(re.findall(r"^    \S", open(f).read(), re.M))
    queued = 0
    if os.path.exists(DECISIONS):
        queued = len(re.findall(rf"^- \[ \] D-\d+ · \S+ · {date}", open(DECISIONS).read(), re.M))
    total = needs + pastes + queued
    print(f"{date} interventions={total} (need-lines={needs} paste-blocks={pastes} decisions-queued={queued} errors-seen={errors})")


# ---- checks: the loop's definition of done, run as facts ---------------------------------
# A `- checks:` block under a loop in pm/LOOPS.md lists sub-lines a script can settle with
# no model involved. Read-only except the loop's own .checks.jsonl. Advisory: the fence is
# still the gate. A check that cannot be settled honestly reports "skip", never "pass".
CHECK_KINDS = ("files_written_only", "state_section", "cursor_advanced", "parse", "traceable",
               "claims_match", "budget")


def _section_body(lid):
    text = open(reg._loops_path()).read()
    m = re.search(rf"^## {re.escape(lid)}\b[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def parse_checks(lid):
    """The `- checks:` block as [(kind, argument)]. Sub-lines are indented `- kind: arg`."""
    body = _section_body(lid)
    m = re.search(r"^- checks: *\n((?:[ \t]+-[^\n]*\n?)+)", body, re.M)
    if not m:
        return []
    out = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        kind, _, arg = line[2:].partition(":")
        out.append((kind.strip(), arg.split("#")[0].strip()))
    return out


def _dates_in(paths):
    return sorted(re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(p)).group(1)
                  for p in paths if re.search(r"\d{4}-\d{2}-\d{2}", os.path.basename(p)))


def _chk_state_section(root, arg, ctx):
    path = os.path.join(root, arg)
    if not os.path.exists(path):
        return "fail", f"{arg} missing"
    sec = re.search(rf"^## {ctx['date']}\b(.*?)(?=^## |\Z)", open(path).read(), re.M | re.S)
    if not sec:
        return "fail", f"no `## {ctx['date']}` section in {arg}"
    missing = [f for f, rx in (("next:", r"^next: *\S"), ("progress:", r"^progress: *(yes|no)\b"))
               if not re.search(rx, sec.group(1), re.M)]
    if missing:
        return "fail", (f"section has no {' and no '.join(missing)} line at line start "
                        "(the runner reads `^next:` / `^progress:`; bold or indented does not count)")
    return "pass", ""


def _chk_cursor_advanced(root, arg, ctx):
    state_rel, _, glob_pat = arg.partition(" vs ")
    path = os.path.join(root, state_rel.strip())
    if not os.path.exists(path):
        return "fail", f"{state_rel.strip()} missing"
    sec = re.search(rf"^## {ctx['date']}\b(.*?)(?=^## |\Z)", open(path).read(), re.M | re.S)
    if not sec:
        return "fail", f"no `## {ctx['date']}` section to read a cursor from"
    m = re.search(r"^next: *(\d{4}-\d{2}-\d{2})", sec.group(1), re.M)
    if not m:
        return "fail", "next: carries no date"
    if not glob_pat:
        return "skip", "no `vs <glob>` given, nothing to compare the cursor against"
    import glob as g
    # only inputs dated on or before the run — last night's run cannot have read today's diff
    newest = [d for d in _dates_in([f for pat in glob_pat.split()
                                    for f in g.glob(os.path.join(root, pat))]) if d <= ctx["date"]]
    if not newest:
        return "skip", f"no input files dated on or before {ctx['date']} matched {glob_pat}"
    return ("pass", f"next: {m.group(1)} = newest input") if m.group(1) >= newest[-1] else \
           ("fail", f"next: {m.group(1)} is behind the newest input {newest[-1]}")


def _chk_files_written_only(root, arg, ctx):
    allowed = [a.strip() for a in arg.split(",") if a.strip()]
    if not ctx.get("since"):
        missing = [a for a in allowed if not os.path.exists(os.path.join(root, a))]
        return ("skip", "no --since ref: existence only" + (f"; missing {', '.join(missing)}" if missing else "")) \
            if not missing else ("fail", f"declared output missing: {', '.join(missing)}")
    r = subprocess.run(["git", "-C", root, "diff", "--name-only", ctx["since"]],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return "skip", f"git diff against {ctx['since']} failed"
    changed = [f for f in r.stdout.split() if f]
    stray = [f for f in changed if f not in allowed]
    return ("fail", f"wrote outside the loop's files: {', '.join(stray[:5])}") if stray else \
           ("pass", f"{len(changed)} file(s), all declared")


def _chk_parse(root, arg, ctx):
    # a tool that is not in this tree cannot judge the output (bench sandboxes carry data, not tools)
    for tok in arg.split():
        if re.search(r"\.(mjs|js|py|sh)$", tok) and not os.path.exists(os.path.join(root, tok)):
            return "skip", f"{tok} is not in this tree"
    r = subprocess.run(arg, shell=True, cwd=root, capture_output=True, text=True)
    if r.returncode == 0:
        return "pass", ""
    # "a verified no-change is the job" — an output with nothing in it is for claims_match to judge
    if "no '## Candidate N' sections found" in (r.stdout + r.stderr):
        return "skip", "no candidate sections — a no-change iteration, see claims_match"
    tail = (r.stderr or r.stdout).strip().splitlines()
    return "fail", f"exit {r.returncode}: {tail[-1][:160] if tail else 'no output'}"


def _chk_traceable(root, arg, ctx):
    """Every quote: in the output must be traceable to a file the document cites.

    Quotes are faithful excerpts, not literal substrings — a feed row is quoted with its
    columns reordered or a middle column dropped. So each quote is split into tokens and
    every substantial token must appear in one cited file. Fabricated rows fail; honest
    excerpting passes.
    """
    path = os.path.join(root, arg)
    if not os.path.exists(path):
        return "fail", f"{arg} missing"
    text = open(path).read()
    FILE_RE = r"[\w./-]+\.(?:md|csv|json)"

    def resolve(rel):
        for base in [""] + RESOLVE_BASES:
            cand = os.path.normpath(os.path.join(base, rel))
            if os.path.exists(os.path.join(root, cand)):
                return cand
        return None

    # files cited anywhere in the document (the header paragraph often carries them) plus per-section
    doc_files = {f for f in re.findall(FILE_RE, text)}
    cache = {}

    def haystack(files):
        out = []
        for f in files:
            cand = resolve(f)
            if not cand:
                continue
            if cand not in cache:
                cache[cand] = re.sub(r"\s+", " ", open(os.path.join(root, cand), errors="replace").read())
            out.append(cache[cand])
        return out

    bad, checked = [], 0
    sections = re.split(r"^#{2,4} ", text, flags=re.M)[1:] or [text]
    for sec in sections:
        files = set(re.findall(FILE_RE, sec)) | doc_files
        hay = haystack(files)
        quotes = re.findall(r"^-? *quote: *(.+?)$", sec, re.M)
        claims = re.search(r"^-? *(?:field|kind|permit_id|project_id|record_id): *\S", sec, re.M)
        if claims and not quotes:
            checked += 1
            bad.append(f'candidate with no quote: line ("{sec.splitlines()[0][:50]}…")')
        for quote in quotes:
            checked += 1
            if not hay:
                bad.append(f'no cited file to trace it to ("{quote[:40]}…")')
                continue
            toks = [re.sub(r"\s+", " ", t).strip(' "\'`.,;→')
                    for t in re.split(r"[;,]|→", quote)]
            toks = [t for t in toks if len(t) >= 8]
            if not toks:
                toks = [re.sub(r"\s+", " ", quote).strip()[:40]]
            missing = [t for t in toks if not any(t in h for h in hay)]
            if missing:
                bad.append(f'{len(missing)}/{len(toks)} fragments not in the cited files — "{missing[0][:60]}"')
    if not checked:
        return "skip", "no quote: lines to trace"
    return ("fail", f"{len(bad)}/{checked} quotes untraceable — {bad[0]}") if bad else \
           ("pass", f"{checked}/{checked} traced")


def _chk_claims_match(root, arg, ctx):
    """What the state section says it wrote must be what the output file holds.

    This is the check that stops a vacuous pass: a run that reports work and leaves an empty
    output fails here even when every other check is skipped.
    """
    cand_rel, _, state_rel = arg.partition(" vs ")
    cand_path = os.path.join(root, cand_rel.strip())
    state_path = os.path.join(root, state_rel.strip())
    if not os.path.exists(state_path):
        return "fail", f"{state_rel.strip()} missing"
    sec = re.search(rf"^## {ctx['date']}\b(.*?)(?=^## |\Z)", open(state_path).read(), re.M | re.S)
    if not sec:
        return "fail", f"no `## {ctx['date']}` section to read a claim from"
    body = sec.group(1)
    actual = len(re.findall(r"^## Candidate\s+\d+", open(cand_path).read(), re.M)) \
        if os.path.exists(cand_path) else 0
    # an explicit count wins: a section can say "1 candidate" and still carry the words
    # "No new candidates from" in its prose, and the number is the claim.
    m = re.search(r"\b(\d+)\s+candidates?\b", body, re.I)
    if m:
        claimed = int(m.group(1))
    elif re.search(r"\b(no|zero) (new )?candidates?\b|no-change|nothing (new )?to (write|report)", body, re.I):
        claimed = 0
    else:
        return "skip", f"state section names no candidate count (file holds {actual})"
    if claimed == actual:
        return "pass", f"{actual} claimed, {actual} in the file"
    return "fail", (f"state section claims {claimed} candidate(s), the file holds {actual}"
                    + (" — nothing was written" if actual == 0 else ""))


def _chk_budget(root, arg, ctx):
    if ctx.get("cost") is None:
        return "skip", "no --cost given"
    l = reg._find(ctx["loop"])
    cap = (arg or (l or {}).get("per") or "").strip()
    try:
        cap = float(re.sub(r"[^0-9.]", "", cap))
    except ValueError:
        return "skip", "loop has no per-iteration budget to compare"
    return ("pass", f"{ctx['cost']:.2f} of {cap:.2f} per iteration") if ctx["cost"] <= cap else \
           ("fail", f"{ctx['cost']:.2f} over the {cap:.2f} per-iteration budget")


CHECKERS = {"state_section": _chk_state_section, "cursor_advanced": _chk_cursor_advanced,
            "claims_match": _chk_claims_match,
            "files_written_only": _chk_files_written_only, "parse": _chk_parse,
            "traceable": _chk_traceable, "budget": _chk_budget}


def cmd_check(lid, date=None, root=None, cost=None, since=None, write=True, model=None,
              source="night"):
    date = date or datetime.date.today().isoformat()
    root = os.path.abspath(root or VENT)
    checks = parse_checks(lid)
    if not checks:
        print(f"{lid}: no `- checks:` block in pm/LOOPS.md — nothing to settle")
        return 0
    ctx = {"date": date, "loop": lid, "cost": cost, "since": since}
    results, order = {}, []
    for kind, arg in checks:
        arg = arg.replace("{date}", date)
        fn = CHECKERS.get(kind)
        if not fn:
            verdict, why = "skip", f"unknown check kind (known: {', '.join(CHECK_KINDS)})"
        else:
            try:
                verdict, why = fn(root, arg, ctx)
            except Exception as e:  # a broken check never fails the loop
                verdict, why = "skip", f"checker error: {type(e).__name__}: {e}"
        name = kind if kind not in results else f"{kind}[{len(order)}]"
        results[name] = verdict if not why else f"{verdict}: {why}"
        order.append((name, verdict, why))
    failed = [n for n, v, _ in order if v == "fail"]
    skipped = [n for n, v, _ in order if v == "skip"]
    row = {"date": date, "loop": lid, "model": model, "cost": cost, "source": source,
           "checks": results, "pass": not failed, "skipped": len(skipped)}
    if write:
        import json
        with open(os.path.join(VENT, "pm", "nights", "loops", f"{lid}.checks.jsonl"), "a") as f:
            f.write(json.dumps(row) + "\n")
    for n, v, why in order:
        print(f"  {'PASS' if v == 'pass' else 'FAIL' if v == 'fail' else 'skip'}  {n}" + (f" — {why}" if why else ""))
    cover = f" [{len(skipped)} of {len(order)} not settled: {', '.join(skipped)}]" if skipped else ""
    print(f"{lid} {date}: {'PASS' if not failed else 'FAIL (' + ', '.join(failed) + ')'}{cover}")
    return 0 if not failed else 1


# ---- the model dial with a floor --------------------------------------------------------
# A loop may run on a cheaper model only once its own checks have passed in the bench that
# many times in a row, and it is put back on the charter default after that many night
# failures. Both numbers are CHARTER dials. Writing `model:` in pm/LOOPS.md is NOT in
# loopctl's ratified blast radius, so an unattended run may only PROPOSE the change as a
# decision row — unless CHARTER carries `- loopctl_may_set_model: yes`.
CHARTER = os.path.join(VENT, "pm", "CHARTER.md")
TIERS = ["claude-haiku", "claude-sonnet", "claude-opus", "claude-fable"]


def dial(key, default):
    try:
        m = re.search(rf"^- {re.escape(key)}: *([^\s#]+)", open(CHARTER).read(), re.M)
        return m.group(1) if m else default
    except Exception:
        return default


def _tier(model):
    return max([i for i, t in enumerate(TIERS) if (model or "").startswith(t)] or [-1])


def checks_rows(lid, source=None):
    path = os.path.join(VENT, "pm", "nights", "loops", f"{lid}.checks.jsonl")
    if not os.path.exists(path):
        return []
    import json
    rows = []
    for line in open(path):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if source is None or r.get("source", "night") == source:
            rows.append(r)
    return rows


def _may_write_model():
    unattended = os.environ.get("LANE") in ("night", "day", "hourly") and not os.environ.get("LOOPCTL_ATTENDED")
    return (not unattended) or dial("loopctl_may_set_model", "no").lower() in ("yes", "true")


def cmd_model(lid, target):
    """Move a loop's model pin, with the floor enforced. Attended, or CHARTER-granted."""
    l = need(lid)
    current = l.get("model") or dial("model", "claude-fable-5")
    if _tier(target) < _tier(current):
        need_n = int(dial("bench_passes_to_demote", "3"))
        # a bench pass counts only when it is a SETTLED pass: `parse` and `files_written_only`
        # cannot be settled in a sandbox (the tools and the fence's diff are not there), so two
        # unsettled checks are structural and anything beyond that is not evidence of anything.
        max_unsettled = 2
        bench = [r for r in checks_rows(lid, "bench")
                 if (r.get("model") == target or (r.get("model") or "").endswith(target.split("/")[-1]))
                 and (r.get("skipped") or 0) <= max_unsettled]
        streak = 0
        for r in reversed(bench):
            if r.get("pass"):
                streak += 1
            else:
                break
        if streak < need_n:
            sys.exit(f"{lid}: {target} has {streak} consecutive settled bench pass(es), needs {need_n} "
                     f"(record them with: loopctl.py check {lid} <date> --root <sandbox> --source bench --model {target})")
    if not _may_write_model():
        cmd_decide(l.get("pod") or "ops",
                   f"Move the {l['name']} loop from {current} to {target}? The floor is met. Detail: {lid}",
                   apply=f"LOOPCTL_ATTENDED=1 python3 00-ops/night/loopctl.py model {lid} {target}")
        print(f"{lid}: proposed {current} → {target} as a decision (unattended runs may not set model:)")
        return
    reg._write_field(lid, "model", target)
    reg._log(lid, f"model {current} → {target} via loopctl")
    log(f"{lid} model {current} → {target}")
    print(f"{lid} model → {target}")


def cmd_guard(lid):
    """After N night failures in a row, put the loop back on the charter default."""
    l = need(lid)
    default = dial("model", "claude-fable-5")
    current = l.get("model") or default
    need_n = int(dial("night_fails_to_restore", "2"))
    nights = checks_rows(lid, "night")
    streak = 0
    for r in reversed(nights):
        if r.get("pass") is False:
            streak += 1
        else:
            break
    if streak < need_n or _tier(current) >= _tier(default):
        return
    why = (f"{l['name']} failed its checks {streak} nights running on {current} — "
           f"put it back on {default}")
    if _may_write_model():
        reg._write_field(lid, "model", default)
        reg._log(lid, f"model {current} → {default} (checks failed {streak} nights; loopctl guard)")
        log(f"{lid} model restored to {default} after {streak} failed nights")
        print(f"{lid} model → {default} ({streak} failed nights)")
    else:
        cmd_decide(l.get("pod") or "ops", why[:200],
                   apply=f"LOOPCTL_ATTENDED=1 python3 00-ops/night/loopctl.py model {lid} {default}")
        print(f"{lid}: {why} — queued as a decision")


def main(a):
    if not a:
        sys.exit(__doc__)
    c, rest = a[0], a[1:]
    try:
        if c == "park": cmd_park(rest[0], rest[1])
        elif c == "done": cmd_done(rest[0], rest[1])
        elif c == "cadence": cmd_cadence(rest[0], rest[1])
        elif c == "decide":
            apply = patch = None
            if "--apply" in rest: apply = rest[rest.index("--apply") + 1]
            if "--patch" in rest: patch = rest[rest.index("--patch") + 1]
            cmd_decide(rest[0], rest[1], apply, patch)
        elif c == "issue": cmd_issue(rest[0], rest[1], rest[2])
        elif c == "apply": cmd_apply(rest[0])
        elif c == "park-decision": cmd_park_decision(rest[0])
        elif c == "interventions": cmd_interventions(rest[0] if rest else None)
        elif c == "check":
            opt = lambda k, d=None: rest[rest.index(k) + 1] if k in rest else d
            pos = [x for i, x in enumerate(rest)
                   if not x.startswith("--") and (i == 0 or not rest[i - 1].startswith("--"))]
            cost = opt("--cost")
            sys.exit(cmd_check(pos[0], pos[1] if len(pos) > 1 else None, root=opt("--root"),
                               cost=float(cost) if cost else None, since=opt("--since"),
                               write="--no-write" not in rest, model=opt("--model"),
                               source=opt("--source", "night")))
        elif c == "model": cmd_model(rest[0], rest[1])
        elif c == "guard": cmd_guard(rest[0])
        else: sys.exit(__doc__)
    except IndexError:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
