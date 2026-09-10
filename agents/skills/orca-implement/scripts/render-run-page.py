#!/usr/bin/env python3
"""Render <RUNDIR>/run-page.html from run-state.json, timeline.md, and plan/brief.md.

Usage: render-run-page.py <RUNDIR> [--standalone]

Reads only. Writes one file, <RUNDIR>/run-page.html, and prints its path.
Without --standalone the output is a body fragment for the Claude Artifact
tool, which wraps it. With --standalone it is a complete HTML document for
`orca artifacts` or a browser.
Standard library only.
"""
import html
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    LOCAL_TZ = ZoneInfo("Australia/Brisbane")  # AEST all year, no daylight shift
except Exception:  # no tz database on this host
    LOCAL_TZ = timezone(timedelta(hours=10), "AEST")

PHASES = [
    ("setup", "Setup"),
    ("scout", "Scout"),
    ("understanding", "Brief"),
    ("plan", "Plan"),
    ("plan_gate", "Plan gate"),
    ("build", "Build"),
    ("verification", "Verify"),
    ("code_review", "Review"),
    ("qa", "QA"),
    ("pr", "PR"),
]
WAITING_PHASES = {"understanding", "plan_gate"}
TERMINAL_OK = {"pr"}
TERMINAL_BAD = {"failed", "blocked"}
TEMPLATE = Path(__file__).resolve().parent.parent / "references" / "templates" / "run-page.html"


def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def short(sha):
    return sha[:7] if isinstance(sha, str) else ""


def rail(phase, status):
    keys = [k for k, _ in PHASES]
    current = keys.index(phase) if phase in keys else -1
    out = []
    for i, (key, label) in enumerate(PHASES):
        if status in TERMINAL_OK:
            cls = "done"
        elif i < current:
            cls = "done"
        elif i == current:
            if status in TERMINAL_BAD:
                cls = "failed"
            elif key in WAITING_PHASES:
                cls = "waiting"
            else:
                cls = "active"
        else:
            cls = "pending"
        state = {"failed": status, "waiting": "waiting on you", "active": "in progress"}.get(cls, "")
        small = f"<small>{esc(state)}</small>" if state else ""
        out.append(f'<li class="{cls}"><span>{esc(label)}{small}</span></li>')
    return "".join(out)


def now_state(phase, status):
    if phase not in {k for k, _ in PHASES} and status not in TERMINAL_OK | TERMINAL_BAD:
        return "active", f"In progress, phase {phase!r} not recognised"
    if status in TERMINAL_OK:
        return "done", "Delivered"
    if status in TERMINAL_BAD:
        return "failed", status.capitalize()
    if phase in WAITING_PHASES:
        return "waiting", "Waiting on you"
    return "active", "In progress"


def read_timeline(path):
    """Lines of the form `- <ISO-8601 UTC> <text>`, oldest first in the file."""
    events = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^-\s+(\S+)(?:\s+(.*?))?\s*$", line)
        if m:
            events.append((m.group(1), m.group(2) or ""))
    fallback = datetime.min.replace(tzinfo=timezone.utc)
    events.sort(key=lambda e: parse_time(e[0]) or fallback)
    return events


def parse_time(stamp):
    if not stamp:
        return None
    try:
        dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%MZ"):
        try:
            return datetime.strptime(stamp, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def fmt_time(stamp):
    """`10 Sep 10:40 UTC` on one line, the AEST time on the next."""
    dt = parse_time(stamp)
    if dt is None:
        return esc(stamp)
    local = dt.astimezone(LOCAL_TZ)
    return f"{esc(dt.strftime('%d %b %H:%M'))} UTC<small>{esc(local.strftime('%d %b %H:%M %Z'))}</small>"


def elapsed(started, until):
    if not started or not until:
        return ""
    minutes = max(0, int((until - started).total_seconds() // 60))
    return f"{minutes // 60}h {minutes % 60:02d}m"


def fmt_updated(dt):
    local = dt.astimezone(LOCAL_TZ)
    return f"{dt.strftime('%Y-%m-%d %H:%M')} UTC, {local.strftime('%H:%M %Z')}"


def read_decisions(brief):
    """The Constraints section of plan/brief.md, as list items."""
    if not brief.exists():
        return []
    text = brief.read_text(encoding="utf-8")
    m = re.search(r"^## Constraints\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        return []
    items = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if line.startswith(("- ", "* ")):
            items.append(line[2:].strip())
        elif line and not line.startswith("#") and not items:
            items.append(line)
    return items


def first_paragraph(path, heading):
    """The first paragraph under `## <heading>` in a Markdown file, or an empty string."""
    if not path.exists():
        return ""
    m = re.search(r"^## " + re.escape(heading) + r"\s*$(.*?)(?=^## |\Z)", path.read_text(encoding="utf-8"), re.S | re.M)
    if not m:
        return ""
    para = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            para.append(re.sub(r"^[-*]\s+", "", line) if not para else line)
        elif para:
            break
    return " ".join(para)


def read_title(brief, fallback):
    if brief.exists():
        m = re.search(r"^# Brief:\s*(.+)$", brief.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1).strip()
    return fallback


def stat(value, label):
    return f'<div class="stat"><b>{esc(value)}</b><span>{esc(label)}</span></div>'


def task_rows(tasks):
    rows = []
    for t in sorted(tasks, key=lambda t: (len(str(t.get("seq") or "")), str(t.get("seq") or ""))):
        status = t.get("status") or "pending"
        cls = {"merged": "done", "completed": "active", "dispatched": "active", "failed": "failed", "ready": "waiting"}.get(status, "pending")
        if t.get("kind") == "fix":
            origin = f"fix · {t.get('origin_phase', '')}"
            if t.get("origin_round"):
                origin += f" r{t['origin_round']}"
        else:
            origin = "build"
        builder = " · ".join(str(x) for x in (t.get("model"), t.get("effort")) if x)
        retries = []
        if (t.get("worker_attempt") or 1) > 1:
            retries.append("replacement worker")
        if t.get("verify_fix_cycles"):
            retries.append(f"{t['verify_fix_cycles']} fix cycle" + ("s" if t["verify_fix_cycles"] != 1 else ""))
        rows.append(
            "<tr>"
            f'<td class="mono">{esc(t.get("seq"))}</td>'
            f"<td><strong>{esc(t.get('slug'))}</strong></td>"
            f"<td>{esc(origin)}</td>"
            f"<td>{esc(builder)}</td>"
            f'<td><span class="pill {cls}">{esc(status)}</span></td>'
            f'<td class="muted">{esc(", ".join(retries))}</td>'
            f'<td class="mono">{esc(short(t.get("merge_commit")))}</td>'
            "</tr>"
        )
    return "".join(rows) or '<tr><td colspan="7" class="muted">No tasks registered yet.</td></tr>'


def counts(d, order):
    """`1 high, 3 medium` from a severity dict, or `no findings`."""
    if not isinstance(d, dict):
        return ""
    parts = [f"{d[k]} {k}" for k in order if d.get(k)]
    return ", ".join(parts) if parts else "no findings"


def with_counts(text, c):
    return f"{text} · {c}" if c else text


def review_rows(manifest):
    """One row per review stage: (stage, head, fix waves, outcome text, pill class)."""
    rows = []
    pr = manifest.get("plan_review") or {}
    crit = (pr.get("rounds") or [{}])[0] or {}
    if pr.get("rounds_run") or crit.get("start_head"):
        reason = pr.get("stop_reason")
        cls = "done" if reason == "critique complete" else "failed" if reason else "active"
        rows.append(("Plan critique", short(crit.get("start_head")), "", with_counts(reason or "in progress", counts(crit.get("accepted_findings"), ("blocking", "risky", "note"))), cls))
    bv = manifest.get("browser_verification") or {}
    for r in manifest.get("review_rounds") or []:
        n = r.get("round")
        try:
            n = int(n)
        except (TypeError, ValueError):
            pass
        head = short(r.get("start_head"))
        reason = r.get("stop_reason")
        if reason:
            cls = "done"
        elif r.get("severe_fix_merged"):
            reason, cls = "severe fix merged, next round", "active"
        else:
            reason, cls = "in progress", "active"
        af = r.get("accepted_findings") or {}
        sev = ("critical", "high", "medium")
        rows.append((f"Code review r{n}", head, r.get("fix_waves") or 0, with_counts(reason, counts(af.get("code"), sev)), cls))
        if r.get("security_lenses_run", True):
            done = len(r.get("security_reviewer_reports") or [])
            sec_counts = counts(af.get("security"), sev)
            sec_cls = "failed" if (af.get("security") or {}).get("critical") or (af.get("security") or {}).get("high") else ("done" if done else "active")
            rows.append((f"Security review r{n}", head, "", with_counts("completed" if done else "in progress", sec_counts if done else ""), sec_cls))
        else:
            rows.append((f"Security review r{n}", head, "", "skipped" + (f", {r['security_skip_reason']}" if r.get("security_skip_reason") else ""), "pending"))
        if n == 1 and bv.get("policy") == "run":
            result = r.get("browser_result") or bv.get("result")
            cls = {"passed": "done", "failed": "failed", "not verified": "pending"}.get(result, "active")
            bcount = af.get("browser")
            rows.append((f"Browser verification r{n}", head, "", with_counts(result or "in progress", f"{bcount} finding" + ("s" if bcount != 1 else "") if bcount else ""), cls))
        elif n == 1 and bv.get("policy") == "not_needed":
            rows.append((f"Browser verification r{n}", head, "", "not needed", "pending"))
    qa = manifest.get("qa") or {}
    if qa.get("status") not in (None, "pending") or qa.get("head"):
        status = qa.get("status") or "pending"
        text = status + (f", {qa['reason']}" if qa.get("reason") else "")
        cls = {"completed": "done", "not_verified": "failed", "skipped": "pending"}.get(status, "active")
        rows.append(("Adversarial QA", short(qa.get("head")), qa.get("fix_waves") or 0, with_counts(text, counts(qa.get("accepted_findings"), ("critical", "high", "medium")) if status == "completed" else ""), cls))
    html_rows = "".join(
        f'<tr><td>{esc(stage)}</td><td class="mono">{esc(head)}</td><td>{esc(waves)}</td>'
        f'<td><span class="pill {cls}">{esc(text)}</span></td></tr>'
        for stage, head, waves, text, cls in rows
    )
    return html_rows or '<tr><td colspan="4" class="muted">No reviews yet.</td></tr>'


def main(argv):
    flags = [a for a in argv[1:] if a.startswith("--")]
    args = [a for a in argv[1:] if not a.startswith("--")]
    standalone = "--standalone" in flags
    if len(args) != 1 or any(f != "--standalone" for f in flags):
        print(__doc__, file=sys.stderr)
        return 2
    rundir = Path(args[0]).resolve()
    manifest = json.loads((rundir / "run-state.json").read_text(encoding="utf-8")) or {}
    brief = rundir / "plan" / "brief.md"
    events = read_timeline(rundir / "timeline.md")

    page_text = manifest.get("run_page") or {}
    phase = manifest.get("phase", "setup")
    status = manifest.get("status", "active")
    cls, state = now_state(phase, status)
    now_html = "<p>" + esc(events[-1][1] if events else "Run started.") + "</p>"
    if status in TERMINAL_OK | TERMINAL_BAD:
        outcome = page_text.get("outcome") or first_paragraph(rundir / "summary.md", "Outcome")
        if outcome:
            if len(outcome) > 512:
                outcome = outcome[:511].rstrip() + "…"
            state = "What was built" if status in TERMINAL_OK else "Outcome"
            now_html = "<p>" + esc(outcome) + "</p>"

    tasks = manifest.get("tasks") or []
    build = [t for t in tasks if t.get("kind") != "fix"]
    fixes = [t for t in tasks if t.get("kind") == "fix"]
    merged = sum(1 for t in build if t.get("status") == "merged")
    pr = manifest.get("plan_review") or {}
    rounds = manifest.get("review_rounds") or []
    qa = manifest.get("qa") or {}
    bv = manifest.get("browser_verification") or {}
    wt = manifest.get("integration_worktree") or {}
    ver = manifest.get("verification") or {}

    stats = "".join([
        stat(f"{merged}/{len(build)}", "build tasks merged"),
        stat(str(len(fixes)), "fix tasks"),
        stat(f"{len(rounds)}/{manifest.get('code_review_cap', '?')}", "review rounds used" + (f" · {rounds[-1].get('stop_reason')}" if rounds and rounds[-1].get("stop_reason") else "")),
        stat(str(sum(1 for r in rounds if r.get("security_lenses_run", True))), "security reviews run"),
        stat(str(qa.get("status", "pending")), f"adversarial QA · policy {manifest.get('qa_policy', 'pending')}"),
    ])

    started = parse_time(manifest.get("started_at") or "")
    last_event = parse_time(events[-1][0]) if events else None
    if status in TERMINAL_OK | TERMINAL_BAD:
        ended = last_event or started
    else:
        ended = max(t for t in (datetime.now(timezone.utc), last_event) if t)
    started_text = ""
    if started:
        started_text = f"{esc(started.strftime('%d %b %H:%M'))} UTC, {esc(started.astimezone(LOCAL_TZ).strftime('%H:%M %Z'))} · {esc(elapsed(started, ended))} " + ("so far" if status == "active" else "total")
    details = "".join(
        f"<dt>{esc(k)}</dt><dd>{v}</dd>" for k, v in [
            ("Source", esc(manifest.get("source") or "ad-hoc")),
            ("Started", started_text or "unknown"),
            ("Target", f'<span class="mono">{esc(manifest.get("base_ref"))}</span> at <span class="mono">{esc(short(manifest.get("base_sha")))}</span>'),
            ("Start ref", f'<span class="mono">{esc(manifest.get("start_ref") or "none")}</span>'),
            ("Worktree", f'{esc(wt.get("origin", "created"))} · <span class="mono">{esc(wt.get("branch"))}</span> · <span class="mono">{esc(wt.get("path"))}</span>'),
            ("Tiers", f'plan review {esc(manifest.get("plan_review_tier"))} · run complexity {esc(manifest.get("run_complexity"))}'),
            ("Fix waves", f'verification {esc(ver.get("fix_waves") or 0)} · post-review {esc(ver.get("post_review_fix_waves") or 0)} · QA {esc(qa.get("fix_waves") or 0)}'),
        ]
    )

    goal = page_text.get("goal") or first_paragraph(brief, "Goal") or first_paragraph(rundir / "plan" / "plan.md", "Overview")
    if len(goal) > 512:
        goal = goal[:511].rstrip() + "…"
    goal_html = f'<p class="goal"><span class="eyebrow">Goal</span>{esc(goal)}</p>' if goal else ""
    decisions = read_decisions(brief)
    decisions_html = "<ul>" + "".join(f"<li>{esc(d)}</li>" for d in decisions) + "</ul>" if decisions else '<p class="muted">None recorded yet. Decisions appear here once the brief is approved.</p>'

    timeline_html = "".join(
        f"<li><time>{fmt_time(ts)}</time><p>{esc(text)}</p></li>" for ts, text in reversed(events)
    ) or '<li><time></time><p class="muted">No events yet.</p></li>'

    pr_url = manifest.get("pr_url")
    pr_link = f' · <a href="{esc(pr_url)}">PR</a>' if isinstance(pr_url, str) and pr_url.startswith("https://") else ""

    values = {
        "title": esc(read_title(brief, manifest.get("run_name", "Orca run"))),
        "run_name": esc(manifest.get("run_name")),
        "base": esc(manifest.get("base_ref")) + " @ " + esc(short(manifest.get("base_sha"))),
        "updated": esc(fmt_updated(datetime.now(timezone.utc))),
        "pr_link": pr_link,
        "goal": goal_html,
        "rail": rail(phase, status),
        "now_class": cls,
        "now_state": esc(state),
        "now": now_html,
        "stats": stats,
        "details": details,
        "tasks": task_rows(tasks),
        "reviews": review_rows(manifest),
        "decisions": decisions_html,
        "timeline": timeline_html,
    }
    page = re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), TEMPLATE.read_text(encoding="utf-8"))

    if standalone:
        head, _, body = page.partition("<main>")
        page = (
            "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
            + head + "</head>\n<body>\n<main>" + body + "\n</body>\n</html>\n"
        )
    out = rundir / "run-page.html"
    tmp = out.with_suffix(".html.tmp")
    tmp.write_text(page, encoding="utf-8")
    os.replace(tmp, out)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
