"""Semantic filters for git commands.

Strategy: for commands we understand (status, log, diff) we run our OWN compact
variant of the command so we get parseable/short output regardless of what flags
the agent passed. For everything else we fall back to generic dedupe+truncate.
"""
import os
import subprocess
from collections import defaultdict

from .common import strip_ansi, dedupe_consecutive, truncate_middle


def _run(args):
    """Run a git command and return combined output (Windows)."""
    proc = subprocess.run(
        args,
        capture_output=True,
        text=True,
        shell=False,
    )
    return (proc.stdout or "") + (proc.stderr or ""), proc.returncode


def handle(sub, args):
    """args = full arg list after 'git'. Returns (raw_text, slim_text, rc).

    raw_text is the agent's actual command output (the 'before' baseline);
    slim_text is the compressed version.
    """
    raw, rc = _run(["git"] + args)
    if sub == "status":
        return raw, _status(args[1:]), rc
    if sub == "log":
        return raw, _log(args[1:]), rc
    if sub in ("diff", "show"):
        return raw, _diff(args), rc
    return raw, _generic(raw), rc


def _status(extra):
    # extra = any paths/flags the caller passed after 'status' (e.g. '-- src/'),
    # appended so a scoped call doesn't silently widen to the whole repo.
    raw, rc = _run(["git", "status", "--porcelain=v1", "-b"] + extra)
    lines = raw.splitlines()
    if not lines:
        return "(clean working tree, no output)"

    branch = ""
    staged, modified, untracked = [], [], []
    for ln in lines:
        if ln.startswith("##"):
            branch = ln[2:].strip()
            continue
        if len(ln) < 3:
            continue
        x, y, path = ln[0], ln[1], ln[3:]
        if ln.startswith("??"):
            untracked.append(path)
        elif x != " ":
            staged.append(f"{x} {path}")
        elif y != " ":
            modified.append(f"{y} {path}")

    out = []
    if branch:
        out.append(f"branch: {branch}")
    out.append(
        f"summary: {len(staged)} staged, {len(modified)} modified, {len(untracked)} untracked"
    )

    def section(title, items, group=False):
        if not items:
            return
        out.append(f"\n{title} ({len(items)}):")
        if group and len(items) > 12:
            # Group untracked files by directory to save tokens.
            by_dir = defaultdict(int)
            for p in items:
                by_dir[os.path.dirname(p) or "."] += 1
            for d, n in sorted(by_dir.items()):
                out.append(f"  {d}/  -> {n} file(s)")
        else:
            out.extend(f"  {p}" for p in items)

    section("staged", staged)
    section("modified", modified)
    section("untracked", untracked, group=True)
    return "\n".join(out)


def _log(extra):
    # extra = any flags/paths the caller passed after 'log' (e.g. '--author=x',
    # '-- file.py'), appended so a scoped call doesn't silently widen to all commits.
    raw, _ = _run(["git", "log", "--oneline", "-n", "20"] + extra)
    lines = raw.splitlines()
    text = "\n".join(truncate_middle(lines, head=20, tail=0))
    return text or "(no commits)"


def _diff(args):
    # Full diffs are large; show the stat summary instead, respecting the paths
    # the caller passed. --stat must come before paths, so insert it right after
    # the subcommand (args[0] is 'diff'/'show').
    raw, _ = _run(["git", args[0], "--stat"] + args[1:])
    lines = strip_ansi(raw).splitlines()
    return "\n".join(truncate_middle(lines, head=40, tail=2)) or "(no changes)"


def _generic(raw):
    lines = dedupe_consecutive(strip_ansi(raw).splitlines())
    return "\n".join(truncate_middle(lines))
