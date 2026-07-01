# Changelog

## 0.2.0
Security & production-readiness hardening, based on an external audit.

- **Security (Critical):** fixed a command-injection vulnerability in
  `slim npm ...` (`shell=True` + naive string join let shell metacharacters like
  `&`/`|` in any argument execute as a second command). Now resolves npm's real
  path and runs with `shell=False`, matching `git_filter`'s existing safe pattern.
- **Security (High):** `slim` could crash entirely (no output at all, not even
  the raw fallback) if command output contained a tiktoken special-token string
  like `<|endoftext|>`. Fixed with `disallowed_special=()` plus a safety net.
- **Correctness:** `git status`/`git log` now respect the paths/flags you pass
  (matching the `git diff`/`show` fix from 0.1.3) instead of silently widening to
  the whole repo.
- Capped the `~/.slim/last_output.txt` cache so one huge command can't grow it
  without bound.
- Pinned `tiktoken<1.0`; added `SECURITY.md`.
- CI now runs `ruff` and `bandit` on a Python 3.8-3.12 matrix, so this class of
  bug can't silently regress.
- `.exe` releases now ship a `SHA256SUMS` file alongside `slim.exe`.
- Added regression tests for the injection fix, the crash fix, path scoping, the
  auto-rewrite hook, and installer idempotency (13 new tests, 21 total).

## 0.1.4
- slim now never emits output larger than the original: if compression doesn't
  shrink a command, the raw output is returned unchanged. No more "got bigger"
  runs, so `slim gain` is a clean cumulative "saved you X tokens".
- `slim gain` report reworked to lead with the total saved.

## 0.1.3
- Fix: `git diff`/`git show` now respect the paths you pass, summarizing only
  those files instead of the whole working tree. Removes wrong-scope output and
  the spurious "got bigger" losses it caused in `slim gain`.

## 0.1.2
- Fix: the auto-rewrite hook now fires for any shell tool (Bash, PowerShell, cmd),
  not just Bash. `slim hook` decides from the command, and `slim init` registers
  matcher `*`. Re-running `slim init` upgrades an older `Bash`-matcher install.
- Add `SLIM_HOOK_DEBUG=1` to log raw hook input to `~/.slim/hook_debug.log`.

## 0.1.1
First PyPI release (`pip install slim-shady`). No functional changes from 0.1.0.

## 0.1.0
First public release.

- Compress `git` and `npm` command output (filter / group / truncate / dedupe).
- `slim init` installs a Claude Code hook to auto-rewrite `git`/`npm` commands.
- `slim expand` recovers the full output of the last command.
- `slim gain` savings dashboard; `slim doctor` health check; `slim reset`.
- Real local token counting via tiktoken (bundled into the standalone `.exe`).
- Standalone Windows `.exe` plus `pip install`.
