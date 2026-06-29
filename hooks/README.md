# Making slim work automatically (Claude Code hook)

After install, the `slim` command exists — but you still have to type
`slim git ...` yourself. The hook makes Claude Code do it **automatically**:
when the agent runs `git status`, it's silently rewritten to `slim git status`,
so the agent reads compressed output without knowing.

## Easy way (recommended): one command

```
slim init        # installs the hook into THIS project's .claude/settings.json
slim init -g     # installs into your GLOBAL ~/.claude/settings.json (all projects)
```

Then restart Claude Code (or start a new session). Done.

`slim init` is idempotent — running it twice won't duplicate anything, and it
won't clobber other hooks already in your settings.

## Manual way (if you prefer to edit settings yourself)

Add this to `.claude/settings.json` (project) or `~/.claude/settings.json` (global):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          { "type": "command", "command": "slim hook" }
        ]
      }
    ]
  }
}
```

The hook runs `slim hook`, which reads the runtime's command JSON on stdin and,
for plain `git`/`npm` commands, returns a rewrite to `slim git`/`slim npm`.

The matcher is `*` (all tools) on purpose: Windows agents may run commands
through the Bash, PowerShell, or cmd tool, and a `"Bash"`-only matcher would miss
the others. `slim hook` decides from the command text, so non-shell tools (Read,
Edit, ...) are ignored instantly.

## Confirm it works
Ask the agent to run `git status`. It becomes `slim git status` behind the
scenes and you'll see the compact output. Watch the savings add up with
`slim gain`.

## What it rewrites (and leaves alone)
- Rewrites:  `git ...` -> `slim git ...`,   `npm ...` -> `slim npm ...`
- Leaves untouched: anything else, commands already starting with `slim `, and
  any command containing `&&`, `||`, `|`, `;`, `>`, `` ` ``, `$(` (chained/piped
  commands a blind prefix would break).

## Requirements
- `slim` must be on PATH (it is, after `pip install` or copying `slim.exe` to a
  PATH folder).
- Works on Windows regardless of which shell tool the agent uses (Bash /
  PowerShell / cmd); `slim hook` is a normal command — no `jq` or extra tools.
