"""Tests for slim.cmd_hook() and installer.py, per the audit's coverage gap."""
import io
import json
import sys

import installer
import slim


def _run_hook(monkeypatch, capsys, payload):
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    slim.cmd_hook()
    return capsys.readouterr().out


def test_hook_rewrites_git(monkeypatch, capsys):
    out = _run_hook(monkeypatch, capsys, {"tool_name": "Bash", "tool_input": {"command": "git status"}})
    data = json.loads(out)
    assert data["hookSpecificOutput"]["updatedInput"]["command"] == "slim git status"


def test_hook_rewrites_regardless_of_tool_name(monkeypatch, capsys):
    # PowerShell/cmd carry the command the same way Bash does; the hook must
    # not key off tool_name.
    out = _run_hook(monkeypatch, capsys, {"tool_name": "PowerShell", "tool_input": {"command": "npm test"}})
    data = json.loads(out)
    assert data["hookSpecificOutput"]["updatedInput"]["command"] == "slim npm test"


def test_hook_ignores_non_shell_tool(monkeypatch, capsys):
    out = _run_hook(monkeypatch, capsys, {"tool_name": "Read", "tool_input": {"file_path": "x.txt"}})
    assert out == ""


def test_hook_ignores_already_slimmed(monkeypatch, capsys):
    out = _run_hook(monkeypatch, capsys, {"tool_name": "Bash", "tool_input": {"command": "slim git status"}})
    assert out == ""


def test_hook_ignores_chained_commands(monkeypatch, capsys):
    out = _run_hook(monkeypatch, capsys, {
        "tool_name": "Bash",
        "tool_input": {"command": "git add . && git commit -m x"},
    })
    assert out == ""


def test_hook_ignores_unrelated_commands(monkeypatch, capsys):
    out = _run_hook(monkeypatch, capsys, {"tool_name": "Bash", "tool_input": {"command": "python app.py"}})
    assert out == ""


def test_installer_init_then_idempotent(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert installer.init(global_scope=False) == 0

    settings_path = tmp_path / ".claude" / "settings.json"
    data = json.loads(settings_path.read_text())
    assert data["hooks"]["PreToolUse"][0]["matcher"] == "*"

    capsys.readouterr()
    assert installer.init(global_scope=False) == 0
    assert "Nothing to do" in capsys.readouterr().out


def test_installer_upgrades_old_bash_matcher(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    settings_path = claude_dir / "settings.json"
    settings_path.write_text(json.dumps({
        "hooks": {
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "slim hook"}]}
            ]
        }
    }))

    installer.init(global_scope=False)
    data = json.loads(settings_path.read_text())
    assert data["hooks"]["PreToolUse"][0]["matcher"] == "*"


def test_installer_does_not_clobber_other_hooks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    settings_path = claude_dir / "settings.json"
    settings_path.write_text(json.dumps({
        "hooks": {
            "PreToolUse": [
                {"matcher": "Edit", "hooks": [{"type": "command", "command": "echo edited"}]}
            ]
        }
    }))

    installer.init(global_scope=False)
    data = json.loads(settings_path.read_text())
    matchers = [e["matcher"] for e in data["hooks"]["PreToolUse"]]
    assert "Edit" in matchers
    assert "*" in matchers
