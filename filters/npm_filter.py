"""Semantic filters for npm commands.

Unlike git, we DON'T re-run npm (installs/tests have side effects and are slow).
We run the agent's actual command once and compress the captured output.
"""
import re
import shutil
import subprocess

from .common import strip_ansi, dedupe_consecutive, truncate_middle

# Progress/noise lines npm emits that an LLM never needs.
NOISE_PREFIXES = (
    "npm http",
    "npm timing",
    "npm verb",
    "npm sill",
    "npm info",
    "[",          # progress bars like [##  ]
)

# Lines worth keeping even in a big install/test dump.
KEEP_RE = re.compile(
    r"(error|err!|fail|warn|deprecat|vulnerab|added|removed|changed|audited|"
    r"passing|failing|pending|✓|✗|×|✔|✘|tests?:|suites?:)",
    re.IGNORECASE,
)


def _run(args):
    # args[0] is the literal string "npm"; resolve its real (.cmd) path so we can
    # run it with shell=False -- joining args into a shell=True string let shell
    # metacharacters in any argument (e.g. "pkg & del ...") execute as a second
    # command. shutil.which resolves the npm.cmd shim without needing a shell.
    npm_path = shutil.which("npm") or shutil.which("npm.cmd") or "npm"
    proc = subprocess.run(
        [npm_path] + args[1:],
        capture_output=True,
        text=True,
        shell=False,
    )
    return (proc.stdout or "") + (proc.stderr or ""), proc.returncode


def handle(sub, args):
    """Returns (raw_text, slim_text, rc). npm is run exactly once."""
    raw, rc = _run(["npm"] + args)
    lines = [strip_ansi(line).rstrip() for line in raw.splitlines()]

    if sub in ("install", "i", "ci", "add"):
        return raw, _install(lines), rc
    if sub in ("test", "t", "run"):
        return raw, _test(lines), rc
    return raw, _generic(lines), rc


def _install(lines):
    kept = []
    dropped = 0
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith(NOISE_PREFIXES):
            dropped += 1
            continue
        if KEEP_RE.search(s):
            kept.append(s)
        else:
            dropped += 1
    kept = dedupe_consecutive(kept)
    footer = f"\n(slim dropped {dropped} progress/noise lines)" if dropped else ""
    return ("\n".join(truncate_middle(kept, head=15, tail=10)) or "(install ok)") + footer


def _test(lines):
    # Keep failures and summaries; truncate the long passing list.
    important = [line for line in lines if line.strip() and KEEP_RE.search(line)]
    important = dedupe_consecutive(important)
    if not important:
        return _generic(lines)
    return "\n".join(truncate_middle(important, head=25, tail=15))


def _generic(lines):
    lines = [line for line in lines if line.strip()]
    return "\n".join(truncate_middle(dedupe_consecutive(lines)))
