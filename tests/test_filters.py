"""Unit tests for the pure compression helpers (no git/npm needed)."""
from filters import common, npm_filter, git_filter


# ---- common helpers --------------------------------------------------------

def test_estimate_tokens_positive():
    assert common.estimate_tokens("") >= 1
    assert common.estimate_tokens("hello world") >= 1


def test_strip_ansi_removes_color():
    colored = "\x1b[31mERROR\x1b[0m done"
    assert common.strip_ansi(colored) == "ERROR done"


def test_dedupe_consecutive_collapses_runs():
    lines = ["a", "a", "a", "b", "a"]
    out = common.dedupe_consecutive(lines)
    assert out == ["a  (x3)", "b", "a"]


def test_truncate_middle_keeps_head_and_tail():
    lines = [str(i) for i in range(100)]
    out = common.truncate_middle(lines, head=5, tail=3)
    assert out[:5] == ["0", "1", "2", "3", "4"]
    assert out[-3:] == ["97", "98", "99"]
    assert any("hidden by slim" in line for line in out)


def test_truncate_middle_noop_when_short():
    lines = ["a", "b", "c"]
    assert common.truncate_middle(lines, head=5, tail=5) == lines


# ---- npm filter (pure, operate on line lists) ------------------------------

def test_npm_install_drops_noise_keeps_signal():
    lines = [
        "npm http fetch GET 200 ...",
        "npm timing ...",
        "added 12 packages in 3s",
        "found 0 vulnerabilities",
    ]
    out = npm_filter._install(lines)
    assert "added 12 packages in 3s" in out
    assert "found 0 vulnerabilities" in out
    assert "npm http" not in out


def test_npm_test_keeps_failures():
    lines = ["ok 1", "ok 2"] + ["noise"] * 20 + [
        "FAILED: expected 4 got 5",
        "Tests: 2 passing, 1 failing",
    ]
    out = npm_filter._test(lines)
    assert "FAILED: expected 4 got 5" in out
    assert "Tests: 2 passing, 1 failing" in out


# ---- git filter (generic path is pure) -------------------------------------

def test_git_generic_dedupes_and_strips():
    raw = "\x1b[32msame\x1b[0m\nsame\nsame\nother\n"
    out = git_filter._generic(raw)
    assert "same  (x3)" in out
    assert "other" in out
    assert "\x1b[" not in out


# ---- security regressions ---------------------------------------------------
# These pin down the two audit findings (command injection, tiktoken crash) and
# the path-scoping bug so they can't silently come back.

def test_npm_run_uses_shell_false_and_arg_list(monkeypatch):
    """A malicious argument like 'pkg & echo x' must arrive as ONE literal argv
    element, never get joined into a string a shell could re-parse."""
    captured = {}

    class FakeResult:
        stdout = ""
        stderr = ""
        returncode = 0

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["shell"] = kwargs.get("shell")
        return FakeResult()

    monkeypatch.setattr(npm_filter.subprocess, "run", fake_run)
    npm_filter._run(["npm", "install", "pkg & echo INJECTED"])

    assert captured["shell"] is False
    assert isinstance(captured["args"], list)
    assert "pkg & echo INJECTED" in captured["args"]


def test_estimate_tokens_survives_special_token_string():
    # tiktoken raises ValueError on strings like <|endoftext|> unless
    # disallowed_special=() is passed; this must never crash the whole command.
    n = common.estimate_tokens("commit mentions <|endoftext|> in the message")
    assert n >= 1


def test_git_status_appends_extra_args(monkeypatch):
    captured = {}

    def fake_run(args):
        captured["args"] = args
        return "", 0

    monkeypatch.setattr(git_filter, "_run", fake_run)
    git_filter._status(["--", "src/"])
    assert captured["args"][:4] == ["git", "status", "--porcelain=v1", "-b"]
    assert captured["args"][4:] == ["--", "src/"]


def test_git_log_appends_extra_args(monkeypatch):
    captured = {}

    def fake_run(args):
        captured["args"] = args
        return "", 0

    monkeypatch.setattr(git_filter, "_run", fake_run)
    git_filter._log(["--author=alice"])
    assert captured["args"] == ["git", "log", "--oneline", "-n", "20", "--author=alice"]
