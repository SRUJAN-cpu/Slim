## What does this PR do?

<!-- One or two sentences. What changed and why. -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Security fix
- [ ] Documentation
- [ ] CI / build / tooling
- [ ] Refactor (no behavior change)

## Related issue

<!-- Closes #123, or "N/A" -->

## How was this tested?

<!-- e.g. "Added/updated unit tests", "Ran slim git status/npm test manually on repo X" -->

- [ ] `python -m pytest -q` passes locally
- [ ] `python -m ruff check .` passes locally
- [ ] `python -m bandit -r . -x ./tests,./build,./dist --severity-level medium` passes locally
- [ ] Tested manually against a real `git`/`npm` command (describe below)

## Security checklist (required if this touches subprocess/hook/filter code)

- [ ] No new `shell=True` / string-joined subprocess calls
- [ ] User-controlled input never reaches a shell for re-parsing
- [ ] No new unguarded exceptions on the hot path (`slim git`/`slim npm`/`slim hook`)

## Screenshots / output (if relevant)

<!-- Paste a before/after of `slim` output if this changes compression behavior -->

## Checklist

- [ ] I've read [CONTRIBUTING](../CONTRIBUTING.md) (if present) and this repo's scope (Windows, git + npm)
- [ ] I've added/updated tests for my change
- [ ] I've updated `CHANGELOG.md` if this is user-facing
- [ ] I have **not** bumped the version in `pyproject.toml`/`slim.py` (maintainer does this at release time)

<!--
This project requires maintainer (@SRUJAN-cpu) review + passing CI before merge.
Please be patient — every change is reviewed by hand.
-->
