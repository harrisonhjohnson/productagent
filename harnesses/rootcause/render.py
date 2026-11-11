#!/usr/bin/env python3
"""Render a rootcause.json to rootcause.html next to it.

Usage: render.py path/to/rootcause.json [--open]
"""
import html, json, subprocess, sys
from pathlib import Path

CONF = {"high": "●●●", "medium": "●●○", "low": "●○○"}


def e(x):
    return html.escape(str(x or ""))


def render(path):
    p = Path(path)
    d = json.loads(p.read_text())
    sig = {s["id"]: s for s in d["signals"]}
    rcs = d["root_causes"]
    outcomes = d.get("outcomes", [])
    out_ids = {o["signal"] for o in outcomes}

    def chip(sid, cls=""):
        s = sig.get(sid, {"text": sid})
        flag = "" if s.get("denominator_known", True) else '<i title="no denominator">?</i>'
        return f'<span class="chip {cls}" title="{e(s.get("text"))}">{e(sid)}{flag}</span>'

    sig_rows = ""
    for s in d["signals"]:
        homes = [r["id"] for r in rcs if s["id"] in r.get("signals", [])]
        cells = "".join(f'<td class="{"hit" if r["id"] in homes else ""}">{"■" if r["id"] in homes else ""}</td>' for r in rcs)
        tag = '<span class="tag">outcome</span>' if s["id"] in out_ids else ""
        gap = '' if s.get("denominator_known", True) else '<span class="tag warn">no denominator</span>'
        sig_rows += f'<tr><th>{e(s["id"])}</th><td class="txt">{e(s["text"])} {tag}{gap}<small>{e(s.get("source"))}</small></td>{cells}</tr>'
    rc_head = "".join(f'<th class="rc">{e(r["id"])}</th>' for r in rcs)

    rc_cards = ""
    for r in rcs:
        chips = "".join(chip(s) for s in r.get("signals", []))
        rc_cards += f"""<article class="rcard"><header><b>{e(r['id'])} · {e(r['name'])}</b>
<span class="conf" title="confidence">{CONF.get(r.get('confidence'), '')} {e(r.get('confidence'))}</span></header>
<p class="mech">{e(r.get('mechanism'))}</p><div class="chips">{chips}</div>
<p class="gap"><b>Evidence gap:</b> {e(r.get('evidence_gap'))}</p></article>"""

    out_html = ""
    if outcomes:
        out_html = "<h2>Outcomes, not causes</h2><ul class='outs'>" + "".join(
            f"<li>{chip(o['signal'], 'out')} is a symptom of {' + '.join(chip(x) if x in sig else '<b>'+e(x)+'</b>' for x in o.get('explained_by', []))}: {e(o.get('note'))}</li>"
            for o in outcomes) + "</ul>"

    qs = sorted(d.get("questions", []), key=lambda q: q.get("priority", 99))
    q_html = "".join(f"""<li><div class="q">{e(q['q'])}</div>
<div class="qmeta"><span class="tag">{e(q.get('type'))}</span><span class="tag">tests {e(q.get('tests'))}</span></div>
<div class="ifs"><div><b>If yes →</b> {e(q.get('if_yes'))}</div><div><b>If no →</b> {e(q.get('if_no'))}</div></div></li>""" for q in qs)

    page = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Root causes</title><style>
:root{{--bg:#f6f5f1;--fg:#1d1d1b;--mut:#6b6a65;--card:#fff;--line:#e2e0d8;--acc:#1d4ed8;--soft:#eef2ff;--warn:#b45309}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151514;--fg:#ecebe6;--mut:#9a988f;--card:#1f1f1d;--line:#33322e;--acc:#93b4ff;--soft:#1b2140;--warn:#fbbf24}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Inter",sans-serif}}
main{{max-width:1400px;margin:0 auto;padding:28px 20px 60px}}h1{{margin:0 0 4px;font-size:28px}}.sub{{color:var(--mut);margin:0 0 18px}}
.kicker{{color:var(--acc);font-weight:600;text-transform:uppercase;font-size:12px;letter-spacing:.08em}}
h2{{font-size:16px;margin:26px 0 10px}}
.cols{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}}
.rcard{{background:var(--card);border:1px solid var(--line);border-top:4px solid var(--acc);border-radius:12px;padding:14px 16px}}
.rcard header{{display:flex;justify-content:space-between;gap:8px}}.conf{{color:var(--mut);font-size:12px;white-space:nowrap}}
.mech{{font-size:14px;margin:8px 0}}.gap{{font-size:13px;color:var(--mut);margin:8px 0 0}}
.chips{{display:flex;flex-wrap:wrap;gap:6px}}
.chip{{display:inline-flex;gap:3px;align-items:center;background:var(--soft);color:var(--acc);border-radius:99px;padding:1px 10px;font-weight:600;font-size:13px;cursor:help}}
.chip i{{font-style:normal;color:var(--warn)}}.chip.out{{background:transparent;border:1px dashed var(--mut);color:var(--mut)}}
table{{border-collapse:collapse;width:100%;background:var(--card);border-radius:10px;overflow:hidden}}
th,td{{border:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top;font-size:14px}}
td.hit{{background:var(--soft);color:var(--acc);text-align:center}}td:not(.txt){{text-align:center;width:52px}}th.rc{{text-align:center}}
td.txt small{{display:block;color:var(--mut);font-size:12px}}
.tag{{display:inline-block;border:1px solid var(--line);border-radius:6px;padding:0 6px;font-size:11px;color:var(--mut);margin-right:4px}}.tag.warn{{color:var(--warn);border-color:var(--warn)}}
.outs li{{margin:6px 0}}
ol.qs{{padding-left:22px}}ol.qs li{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin-bottom:10px}}
.q{{font-weight:600}}.qmeta{{margin:4px 0}}.ifs{{display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:14px;color:var(--mut)}}
.ifs b{{color:var(--fg)}}
@media (max-width:700px){{.ifs{{grid-template-columns:1fr}}}}
</style></head><body><main>
<div class="kicker">Root causes</div><h1>{e(d.get('title','Root causes'))}</h1><p class="sub">{e(d.get('summary'))}</p>
<h2>{len(rcs)} root causes behind {len(d['signals'])} signals</h2><div class="cols">{rc_cards}</div>
{out_html}
<h2>Questions to ask first</h2><ol class="qs">{q_html}</ol>
<h2>Signal map</h2><table><tr><th></th><th>Signal</th>{rc_head}</tr>{sig_rows}</table>
</main></body></html>"""
    out = p.with_suffix(".html")
    out.write_text(page)
    return out


if __name__ == "__main__":
    o = render(sys.argv[1])
    print(o)
    if "--open" in sys.argv:
        subprocess.run(["open", str(o)])
