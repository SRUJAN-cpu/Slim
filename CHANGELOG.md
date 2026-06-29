# Changelog

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
