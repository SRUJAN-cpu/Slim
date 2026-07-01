# Security Policy

## Reporting a vulnerability

Please report security issues privately by emailing **srujansmurty@gmail.com**
rather than opening a public issue. Include steps to reproduce if possible.
We'll acknowledge within a few days.

## Supported versions

Only the latest release on PyPI/GitHub Releases is supported. Please upgrade
(`pip install -U slim-shady`) before reporting, in case the issue is already fixed.

## Scope

slim runs `git`/`npm` locally and never sends your commands, output, or repo
contents over the network. Reports about local behavior (subprocess handling,
file caching under `~/.slim/`, the Claude Code hook) are in scope.
