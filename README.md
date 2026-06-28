# slim

[![ci](https://github.com/SRUJAN-cpu/Slim/actions/workflows/ci.yml/badge.svg)](https://github.com/SRUJAN-cpu/Slim/actions/workflows/ci.yml)
[![release](https://img.shields.io/github/v/release/SRUJAN-cpu/Slim?include_prereleases&sort=semver)](https://github.com/SRUJAN-cpu/Slim/releases)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**Shrink AI-agent command output so it burns fewer tokens.**

When an AI coding assistant runs `git status` or `npm install`, the raw output can
be hundreds of lines — and every line costs tokens, money, and context-window
space. `slim` runs the command, compresses the output (keeping what matters,
dropping the noise), and returns the compact version. Same information, ~70–90%
fewer tokens.

> Windows · works with `git` and `npm` · integrates with Claude Code

```
$ slim git status
branch: main
summary: 0 staged, 1 modified, 3 untracked
modified (1):
  M src/app.py
untracked (3):
  README.md  LICENSE  tests/
[slim: hid ~58 tokens - run 'slim expand' for full output]
```

## Install

### Download the .exe (no Python needed) — easiest
1. Grab `slim.exe` from the [latest release](https://github.com/SRUJAN-cpu/Slim/releases/latest).
2. Put it in a folder on your `PATH`.
3. Run `slim git status`. (You only need `git`/`npm` installed — the tools it wraps.)

### Or install with pip
```
pip install git+https://github.com/SRUJAN-cpu/Slim
```

## Quick start

```
slim init -g          # turn on automatic mode for all projects (see below)
slim git status       # try it manually
slim gain             # see how many tokens you've saved
slim doctor           # check everything is wired up
```

## Make it automatic (recommended)

Typing `slim` every time is annoying. `slim init` installs a Claude Code hook so
your agent's `git`/`npm` commands are compressed **automatically** — when it runs
`git status`, it's transparently rewritten to `slim git status`.

```
slim init       # this project only
slim init -g    # all projects (global ~/.claude settings)
```

Restart Claude Code afterwards. See [hooks/README.md](hooks/README.md) for details
and manual setup.

## Commands

```
slim git <args>     run git, return compressed output
slim npm <args>     run npm, return compressed output
slim expand         print the full output of the last slim command
slim gain           savings dashboard (tokens saved, by tool, biggest)
slim reset          clear saved stats
slim doctor         health check: PATH, hook, tokenizer, tools
slim init [-g]      install the Claude Code auto-rewrite hook (-g = global)
slim --version      print version
slim --raw git ...  debug: show before/after + % saved
```

## How it works

1. `slim` dispatches to a per-tool filter that understands that command's output.
2. Each filter applies four strategies:
   - **filter** — drop noise (ANSI colors, progress bars, `npm http`/timing lines)
   - **group** — e.g. untracked files grouped by directory
   - **truncate** — keep the head/tail of long blocks, hide the redundant middle
   - **dedupe** — collapse repeated lines into `line (xN)`
3. For `git`, known subcommands re-run a compact native variant (`--porcelain`,
   `--oneline`, `--stat`). For `npm`, the command runs **once** (installs/tests have
   side effects) and the captured output is compressed.
4. Errors, failures, warnings and summaries are always kept. Anything hidden is
   recoverable with `slim expand`.

## How tokens are counted

slim measures savings by tokenizing text **locally** — no API calls during normal use:

```
saved = count(raw output) - count(compressed output)
```

- Both the `.exe` and the pip install count with `tiktoken`, a real tokenizer. The
  `.exe` bundles tiktoken's vocab so it works fully offline.
- tiktoken uses GPT's vocabulary — a close proxy for Claude, usually within a few
  percent, not exact. That's why counts are labelled `~`.
- A `~4 chars/token` estimate remains only as a crash-safety fallback; `slim doctor`
  shows which counter is active.

## Build the .exe yourself

```
build.bat        # produces dist\slim.exe (bundles tiktoken, fully offline)
```

## Scope & limitations

- Windows, `git` + `npm` only (more commands planned).
- tiktoken approximates Claude's tokenizer, so counts aren't Claude-exact (`~`).
- Some Unicode glyphs (e.g. ✓) can be mangled by the Windows console; failures and
  summaries are always preserved.

## License

MIT — see [LICENSE](LICENSE).
