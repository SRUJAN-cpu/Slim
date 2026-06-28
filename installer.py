"""`slim init` - install the Claude Code auto-rewrite hook.

Registers a PreToolUse/Bash hook in settings.json whose command is `slim hook`.
After this, Claude Code transparently rewrites `git ...`/`npm ...` to
`slim git ...`/`slim npm ...`. No separate hook file is written -- the rewrite
logic lives inside slim itself (`slim hook`), so this works for both pip
installs and the standalone .exe.
"""
import json
import os

HOOK_COMMAND = "slim hook"


def _settings_path(global_scope):
    root = os.path.expanduser("~") if global_scope else os.getcwd()
    return os.path.join(root, ".claude", "settings.json")


def _load(path):
    if not os.path.exists(path):
        return {}, True
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), True
    except json.JSONDecodeError:
        return None, False  # don't clobber a file we can't parse


def _already_installed(pretool):
    for entry in pretool:
        for h in entry.get("hooks", []):
            if h.get("command") == HOOK_COMMAND:
                return True
    return False


def is_installed(global_scope):
    """For `slim doctor`: returns (installed_bool, settings_path)."""
    path = _settings_path(global_scope)
    settings, ok = _load(path)
    if not ok or not settings:
        return False, path
    pretool = settings.get("hooks", {}).get("PreToolUse", [])
    return _already_installed(pretool), path


def init(global_scope=False):
    path = _settings_path(global_scope)
    scope = "global (user)" if global_scope else "project"

    settings, ok = _load(path)
    if not ok:
        print(f"slim: {path} exists but isn't valid JSON. Fix or remove it, then retry.")
        return 1

    hooks = settings.setdefault("hooks", {})
    pretool = hooks.setdefault("PreToolUse", [])

    if _already_installed(pretool):
        print(f"slim: hook already installed in {scope} settings ({path}). Nothing to do.")
        return 0

    pretool.append({
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": HOOK_COMMAND}],
    })

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

    print(f"slim: installed auto-rewrite hook in {scope} settings.")
    print(f"  file: {path}")
    print("  Restart Claude Code (or start a new session) to activate it.")
    print("  git/npm commands the agent runs will now be compressed automatically.")
    return 0
