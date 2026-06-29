"""slim - shrink AI-agent command output to save tokens.

Usage:
    slim git <args...>      run git, return compressed output
    slim npm <args...>      run npm, return compressed output
    slim expand             print the full output of the last slim command
    slim gain               show savings dashboard (tokens saved, by tool, biggest)
    slim reset              clear saved stats
    slim doctor             health check (PATH, hook, tokenizer, tools)
    slim init [-g]          install the Claude Code auto-rewrite hook
                            (-g / --global = your user settings, default = this project)
    slim hook               internal: stdin->stdout PreToolUse rewriter (called by the hook)
    slim --version          print version
    slim --raw git ...      show before/after comparison (debug)

Scope: Windows, git + npm.
"""
import json
import os
import shutil
import sys

import installer
from filters import git_filter, npm_filter
from filters.common import estimate_tokens, tokenizer_name, is_real_tokenizer

__version__ = "0.1.2"

# Tools slim wraps, and operators that make a blind `slim ` prefix unsafe.
WRAP = ("git", "npm")
UNSAFE = ("&&", "||", "|", ";", ">", "<", "`", "$(", "\n")

# Store stats + the last full output in a stable per-user location. (Next to the
# script breaks once packaged as a one-file .exe, which unpacks to a temp dir.)
STATS_DIR = os.path.join(os.path.expanduser("~"), ".slim")
STATS_FILE = os.path.join(STATS_DIR, "stats.json")
LAST_OUTPUT_FILE = os.path.join(STATS_DIR, "last_output.txt")
LAST_META_FILE = os.path.join(STATS_DIR, "last_meta.json")


def _blank_stats():
    return {
        "runs": 0,
        "tokens_raw": 0,
        "tokens_slim": 0,
        "losses": 0,                       # times slim output was >= raw
        "by_tool": {},                     # {"git": {runs, raw, slim}, ...}
        "biggest": {"cmd": "", "saved": 0},  # single best save so far
    }


def _load_stats():
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return _blank_stats()
    # Merge in any keys missing from older stats files.
    base = _blank_stats()
    base.update(data)
    return base


def _save_stats(stats):
    os.makedirs(STATS_DIR, exist_ok=True)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)


def _record(tool, cmd_str, raw_t, slim_t):
    saved = raw_t - slim_t

    stats = _load_stats()
    stats["runs"] += 1
    stats["tokens_raw"] += raw_t
    stats["tokens_slim"] += slim_t
    if slim_t >= raw_t:
        stats["losses"] += 1

    t = stats["by_tool"].setdefault(tool, {"runs": 0, "raw": 0, "slim": 0})
    t["runs"] += 1
    t["raw"] += raw_t
    t["slim"] += slim_t

    if saved > stats["biggest"]["saved"]:
        stats["biggest"] = {"cmd": cmd_str, "saved": saved}

    _save_stats(stats)


def _cache_last(cmd_str, raw_text, raw_t, slim_t):
    """Stash the full output so `slim expand` can recover anything slim hid."""
    os.makedirs(STATS_DIR, exist_ok=True)
    with open(LAST_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(raw_text)
    with open(LAST_META_FILE, "w", encoding="utf-8") as f:
        json.dump({"cmd": cmd_str, "raw_tokens": raw_t, "slim_tokens": slim_t}, f)


def cmd_expand():
    try:
        with open(LAST_META_FILE, "r", encoding="utf-8") as f:
            meta = json.load(f)
        with open(LAST_OUTPUT_FILE, "r", encoding="utf-8") as f:
            raw = f.read()
    except (FileNotFoundError, json.JSONDecodeError):
        print("slim: no cached output yet. Run a slim git/npm command first.", file=sys.stderr)
        return 1
    print(f"=== full output of: {meta.get('cmd', '?')} ===")
    sys.stdout.write(raw)
    if raw and not raw.endswith("\n"):
        print()
    return 0


def _bar(pct, width=20):
    filled = int(round(pct / 100 * width))
    return "#" * filled + "-" * (width - filled)


def cmd_gain():
    s = _load_stats()
    raw, slim = s["tokens_raw"], s["tokens_slim"]
    saved = raw - slim
    pct = (saved / raw * 100) if raw else 0

    print("=" * 44)
    print("  slim gain report")
    print("=" * 44)
    if s["runs"] == 0:
        print("  No commands run yet. Try:  slim git status")
        return
    print(f"  commands run : {s['runs']:,}")
    print(f"  tokens raw   : ~{raw:,}")
    print(f"  tokens slim  : ~{slim:,}")
    print(f"  tokens saved : ~{saved:,}")
    print(f"  reduction    : {pct:5.1f}%  [{_bar(pct)}]")
    if is_real_tokenizer():
        print(f"  (~ counted with {tokenizer_name()}; approximates Claude's tokenizer)")
    else:
        print(f"  (~ rough {tokenizer_name()}; pip install slim-shady for real counts)")

    big = s["biggest"]
    if big["cmd"]:
        print(f"\n  biggest save : {big['saved']:,} tokens")
        print(f"                 ({big['cmd']})")

    if s["losses"]:
        print(f"\n  note: {s['losses']} run(s) got bigger, not smaller "
              "(tiny outputs where the summary costs more).")

    if s["by_tool"]:
        print("\n  by tool:")
        for tool, t in sorted(s["by_tool"].items()):
            tsaved = t["raw"] - t["slim"]
            tpct = (tsaved / t["raw"] * 100) if t["raw"] else 0
            print(f"    {tool:<5} {t['runs']:>4} runs   "
                  f"{tsaved:>8,} saved   {tpct:5.1f}%")
    print("=" * 44)


def cmd_reset():
    _save_stats(_blank_stats())
    print("slim: stats reset.")


def cmd_doctor():
    print("slim doctor")
    print("-" * 44)
    ok = True

    def check(label, passed, detail="", warn=False):
        nonlocal ok
        if passed:
            tag = "[OK]  "
        elif warn:
            tag = "[WARN]"
        else:
            tag = "[X]   "
            ok = False
        print(f"  {tag} {label}" + (f"  {detail}" if detail else ""))

    check("slim on PATH", bool(shutil.which("slim")),
          shutil.which("slim") or "not found -- the hook command 'slim hook' won't resolve",
          warn=True)
    check("git available", bool(shutil.which("git")), shutil.which("git") or "")
    check("npm available", bool(shutil.which("npm")), shutil.which("npm") or "")

    real = is_real_tokenizer()
    check(f"tokenizer: {tokenizer_name()}", True,
          "" if real else "(estimate -- pip install slim-shady for real counts)")

    proj_on, proj_path = installer.is_installed(False)
    glob_on, glob_path = installer.is_installed(True)
    check("hook installed (this project)", proj_on,
          proj_path if proj_on else "run 'slim init' here", warn=not proj_on)
    check("hook installed (global)", glob_on,
          glob_path if glob_on else "run 'slim init -g'", warn=not glob_on)

    has_stats = os.path.exists(STATS_FILE)
    check("stats file", has_stats, STATS_FILE if has_stats else "none yet (run a command)", warn=True)

    print("-" * 44)
    if not (proj_on or glob_on):
        print("  Hook not installed anywhere -> slim won't run automatically.")
        print("  Fix: run 'slim init -g' (all projects) or 'slim init' (this one).")
    print("  doctor: " + ("all critical checks passed." if ok else "issues found above."))
    return 0 if ok else 1


def cmd_hook():
    """PreToolUse rewriter: read the runtime's JSON on stdin and, for a plain
    git/npm command, emit JSON that rewrites it to `slim git/npm ...`. Decides
    from the command, not the tool name, so it works for any shell tool.
    Set SLIM_HOOK_DEBUG=1 to log raw input to ~/.slim/hook_debug.log."""
    raw_in = sys.stdin.read()

    if os.environ.get("SLIM_HOOK_DEBUG"):
        try:
            os.makedirs(STATS_DIR, exist_ok=True)
            with open(os.path.join(STATS_DIR, "hook_debug.log"), "a", encoding="utf-8") as f:
                f.write(raw_in + "\n")
        except Exception:
            pass

    try:
        data = json.loads(raw_in)
    except Exception:
        return 0

    cmd = data.get("tool_input", {}).get("command", "")
    if not isinstance(cmd, str):
        return 0
    stripped = cmd.strip()
    if not stripped or stripped.startswith("slim "):
        return 0
    if any(op in cmd for op in UNSAFE):
        return 0
    if stripped.split(None, 1)[0] not in WRAP:
        return 0

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "updatedInput": {"command": "slim " + stripped},
        }
    }))
    return 0


def main(argv):
    if not argv:
        print(__doc__)
        return 1

    if argv[0] in ("--version", "-V", "version"):
        print(f"slim {__version__}")
        return 0

    if argv[0] in ("--help", "-h", "help"):
        print(__doc__)
        return 0

    show_raw = False
    if argv[0] == "--raw":
        show_raw = True
        argv = argv[1:]

    tool = argv[0]
    rest = argv[1:]

    if tool == "gain":
        cmd_gain()
        return 0

    if tool == "expand":
        return cmd_expand()

    if tool == "doctor":
        return cmd_doctor()

    if tool == "reset":
        return cmd_reset() or 0

    if tool == "hook":
        return cmd_hook()

    if tool == "init":
        global_scope = any(a in ("-g", "--global") for a in rest)
        return installer.init(global_scope)

    if tool not in ("git", "npm"):
        print(f"slim: unsupported tool '{tool}' (slim supports git, npm)", file=sys.stderr)
        return 2

    if not rest:
        print(f"slim: missing subcommand for {tool}", file=sys.stderr)
        return 2

    sub = rest[0]

    # Filters run the tool once and return (raw_baseline, compressed, returncode).
    if tool == "git":
        raw_text, slim_text, rc = git_filter.handle(sub, rest)
    else:
        raw_text, slim_text, rc = npm_filter.handle(sub, rest)

    cmd_str = " ".join([tool] + rest)
    raw_t, slim_t = estimate_tokens(raw_text), estimate_tokens(slim_text)
    _record(tool, cmd_str, raw_t, slim_t)
    _cache_last(cmd_str, raw_text, raw_t, slim_t)

    if show_raw:
        pct = (raw_t - slim_t) / raw_t * 100 if raw_t else 0
        print(f"=== RAW ({raw_t} tokens) ===")
        print(raw_text)
        print(f"\n=== SLIM ({slim_t} tokens, -{pct:.0f}%) ===")

    print(slim_text)
    # Tell the reader compression happened and how to recover the full output.
    if slim_t < raw_t:
        print(f"[slim: hid ~{raw_t - slim_t} tokens - run 'slim expand' for full output]")
    return rc


def cli():
    """Console-script entry point (used by pip install and the .exe)."""
    sys.exit(main(sys.argv[1:]))


if __name__ == "__main__":
    cli()
