#!/usr/bin/env python3
"""env_audit.py - PWKM environment drift detector.

Compares the current Claude Desktop environment against a stored baseline to
surface protocol-relevant drift during the weekly PWKM audit. All three
detectors are external or enumerable; none rely on the model introspecting its
own prompt:

  1. tools   - sorted always-on tool roster (catches a tool family appearing
               or vanishing; also proxies behavioral-guidance changes, since
               guidance travels with its tools).
  2. layer1  - the PUBLIC core system prompt body for the current model,
               captured from the published system-prompts page.
  3. env     - structured anchors: app version, MSIX package family, model
               strings, model-identity sentence, knowledge-cutoff value, and
               the environment line. All public or operationally obvious.

Deliberately NOT captured: contents or presence of the copyright, child-safety,
injection-defense, or wellbeing blocks. They do not bear on protocol-adherence
drift, and transcribing dense prompt scaffolding is itself a classifier
false-positive trigger.

Layout under the audit directory (default: the directory the script is run in):

    archive/                 frozen first capture, never overwritten
        baseline_tools.txt
        baseline_layer1.txt
        baseline_env.json
    last_seen_tools.txt      rolling baseline, advanced after a reviewed change
    last_seen_layer1.txt
    last_seen_env.json
    current_tools.txt        written by the audit step BEFORE running this
    current_layer1.txt
    current_env.json

Modes:
    init    capture current_* as both the frozen archive and last_seen_*
    check   diff current_* against last_seen_* (report only; does not advance)
    commit  advance last_seen_* to current_* after you have reviewed a change

check exits 0 when there is no drift and 2 when drift is detected, so the audit
step can branch on the exit code.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# env.json fields that legitimately change every capture and must be excluded
# from the diff. The schema already omits volatile runtime fields (date,
# location, memory profile, connected servers); captured_at is the lone
# bookkeeping field that varies by design.
ENV_VOLATILE_KEYS = {"captured_at"}

ARTIFACTS = ("tools", "layer1", "env")


def _audit_dir(args: argparse.Namespace) -> Path:
    return Path(args.dir).expanduser().resolve()


def _paths(base: Path, name: str) -> dict[str, Path]:
    ext = "json" if name == "env" else "txt"
    return {
        "current": base / f"current_{name}.{ext}",
        "last_seen": base / f"last_seen_{name}.{ext}",
        "archive": base / "archive" / f"baseline_{name}.{ext}",
    }


def _read_text(p: Path) -> str | None:
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


def _load_env(p: Path) -> dict | None:
    raw = _read_text(p)
    if raw is None:
        return None
    return json.loads(raw)


def _missing_current(base: Path) -> list[str]:
    missing = []
    for name in ARTIFACTS:
        if not _paths(base, name)["current"].exists():
            missing.append(_paths(base, name)["current"].name)
    return missing


# --- diff helpers -----------------------------------------------------------

def _diff_tools(current: str, last_seen: str) -> tuple[list[str], list[str]]:
    cur = {ln.strip() for ln in current.splitlines() if ln.strip()}
    prev = {ln.strip() for ln in last_seen.splitlines() if ln.strip()}
    added = sorted(cur - prev)
    removed = sorted(prev - cur)
    return added, removed


def _diff_layer1(current: str, last_seen: str) -> list[str]:
    return list(
        difflib.unified_diff(
            last_seen.splitlines(),
            current.splitlines(),
            fromfile="last_seen_layer1",
            tofile="current_layer1",
            lineterm="",
            n=2,
        )
    )


def _diff_env(current: dict, last_seen: dict) -> dict[str, dict]:
    changes: dict[str, dict] = {}
    keys = (set(current) | set(last_seen)) - ENV_VOLATILE_KEYS
    for k in sorted(keys):
        cur_v = current.get(k, "<absent>")
        prev_v = last_seen.get(k, "<absent>")
        if cur_v != prev_v:
            changes[k] = {"was": prev_v, "now": cur_v}
    return changes


# --- modes ------------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> int:
    base = _audit_dir(args)
    missing = _missing_current(base)
    if missing:
        print(f"init: missing current capture files: {', '.join(missing)}")
        return 1

    archive = base / "archive"
    archive.mkdir(parents=True, exist_ok=True)

    wrote_archive = []
    for name in ARTIFACTS:
        p = _paths(base, name)
        text = _read_text(p["current"])
        # last_seen is always refreshed from current on init
        p["last_seen"].write_text(text, encoding="utf-8")
        # archive is immutable: only write if absent
        if not p["archive"].exists():
            p["archive"].write_text(text, encoding="utf-8")
            wrote_archive.append(p["archive"].name)

    print(f"init: last_seen set from current for {', '.join(ARTIFACTS)}.")
    if wrote_archive:
        print(f"init: froze archive baseline: {', '.join(wrote_archive)}.")
    else:
        print("init: archive baseline already present; left untouched.")
    return 0


def _compare(base: Path, against: str) -> tuple[bool, list[str]]:
    """Return (drift_found, report_lines). `against` is 'last_seen' or 'archive'."""
    report: list[str] = []
    drift = False

    # tools
    cur = _read_text(_paths(base, "tools")["current"])
    ref = _read_text(_paths(base, "tools")[against])
    if cur is None:
        report.append("tools: current_tools.txt missing; cannot compare.")
    elif ref is None:
        report.append(f"tools: no {against} baseline; run init first.")
    else:
        added, removed = _diff_tools(cur, ref)
        if added or removed:
            drift = True
            report.append("tools: CHANGED")
            for t in added:
                report.append(f"    + {t}")
            for t in removed:
                report.append(f"    - {t}")
        else:
            report.append("tools: no change")

    # layer1
    cur = _read_text(_paths(base, "layer1")["current"])
    ref = _read_text(_paths(base, "layer1")[against])
    if cur is None:
        report.append("layer1: current_layer1.txt missing; cannot compare.")
    elif ref is None:
        report.append(f"layer1: no {against} baseline; run init first.")
    else:
        d = _diff_layer1(cur, ref)
        if d:
            drift = True
            report.append("layer1: CHANGED (unified diff)")
            report.extend("    " + ln for ln in d)
        else:
            report.append("layer1: no change")

    # env
    cur_e = _load_env(_paths(base, "env")["current"])
    ref_e = _load_env(_paths(base, "env")[against])
    if cur_e is None:
        report.append("env: current_env.json missing; cannot compare.")
    elif ref_e is None:
        report.append(f"env: no {against} baseline; run init first.")
    else:
        changes = _diff_env(cur_e, ref_e)
        if changes:
            drift = True
            report.append("env: CHANGED")
            for k, v in changes.items():
                report.append(f"    {k}: {v['was']!r} -> {v['now']!r}")
        else:
            report.append("env: no change")

    return drift, report


def cmd_check(args: argparse.Namespace) -> int:
    base = _audit_dir(args)
    against = "archive" if args.against_archive else "last_seen"
    drift, report = _compare(base, against)

    label = "cumulative drift since frozen baseline" if args.against_archive \
        else "drift since last reviewed capture"
    print(f"env_audit check ({label}):")
    print("\n".join(report))

    if drift and not args.against_archive:
        print()
        print(_drift_log_entry(report))
        print(
            "\nReview the changes above. If they are expected, advance the "
            f'rolling baseline with:  python env_audit.py --dir "{base}" commit'
        )
        return 2
    return 0 if not drift else 2


def cmd_commit(args: argparse.Namespace) -> int:
    base = _audit_dir(args)
    advanced = []
    for name in ARTIFACTS:
        p = _paths(base, name)
        text = _read_text(p["current"])
        if text is None:
            print(f"commit: current capture for {name} missing; aborting.")
            return 1
        p["last_seen"].write_text(text, encoding="utf-8")
        advanced.append(name)
    print(f"commit: advanced last_seen for {', '.join(advanced)}.")
    print("commit: archive baseline left frozen.")
    return 0


def _drift_log_entry(report: list[str]) -> str:
    ts = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    lines = [
        "----- DRIFT LOG ENTRY (paste into Notion Environment Drift Log) -----",
        f"Date: {ts}",
        "Detected:",
    ]
    lines.extend("  " + ln for ln in report)
    lines.append("Hypothesis: <fill in: tool rollout / model launch / "
                 "core-prompt revision / harness change>")
    lines.append("Action: <fill in: monitor / amend protocol / none>")
    lines.append("-------------------------------------------------------------------")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PWKM environment drift detector.")
    parser.add_argument(
        "--dir", default=".",
        help="audit directory holding current_/last_seen_/archive files "
             "(default: current directory).",
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    sub.add_parser("init", help="capture current_* as frozen archive + last_seen")

    p_check = sub.add_parser("check", help="diff current_* against baseline (report only)")
    p_check.add_argument(
        "--against-archive", action="store_true",
        help="diff against the frozen original instead of the rolling baseline",
    )

    sub.add_parser("commit", help="advance last_seen_* to current_* after review")

    args = parser.parse_args(argv)
    return {"init": cmd_init, "check": cmd_check, "commit": cmd_commit}[args.mode](args)


if __name__ == "__main__":
    sys.exit(main())
