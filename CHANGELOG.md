# Changelog

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
