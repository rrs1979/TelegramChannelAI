# Contributing to TelegramChannelAI

Thanks for considering a contribution. This is a small, focused project — keep changes scoped, tested, and documented.

## Development setup

```bash
git clone https://github.com/rrs1979/TelegramChannelAI.git
cd TelegramChannelAI
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
pip install ruff pytest     # dev tools

cp .env.example .env
# fill in test credentials (Pollinations key works on free tier)
```

## Before opening a PR

1. **Tests pass locally**: `pytest tests/ -v`
2. **No lint regressions**: `ruff check --select E,F,W --ignore E501,F401 .`
3. **Imports still work**: `python -c "import channel_ai; from web.app import app"`
4. **CHANGELOG.md updated** for user-visible changes (under "Unreleased")
5. **README.md updated** if you added/changed config knobs or commands

CI (.github/workflows/ci.yml) runs the same checks on `push` to master and PRs — your branch must be green there too.

## What kinds of changes are welcome

**Yes, please:**
- Bug fixes with a regression test
- New AI provider integrations (e.g. additional Pollinations models)
- Better humanizer prompts
- Performance / cost optimizations
- Docs improvements, typos, examples

**Discuss first via issue before submitting:**
- New top-level features (large refactors, new pipeline stages)
- Breaking changes to `.env` keys or DB schema
- New mandatory dependencies

**Out of scope:**
- Telegram-protocol violations (mass-DM, automation that breaks ToS)
- Bypassing Pollinations rate limits
- Anything tied to a specific channel's editorial content

## Coding style

- Python 3.10+ syntax
- Type hints on new public functions are appreciated, not required
- Keep functions small; prefer explicit over clever
- Async where the code is already async (channel_ai.py, scanner)
- One logical change per commit; squash trivial fixups before opening PR

## Commit messages

Lowercase, present tense, focused on the *why* when not obvious:

```
add SCAN_HOURS env var so scan window can outlast pipeline interval
fix dedup hash collision on stories with identical leading paragraph
remove broken Render deploy badge — service is gone
```

## Reporting bugs

Open an issue with:
- What you expected
- What actually happened
- Minimal reproduction (env values you can share, command sequence)
- Logs from `web/logs/app.log` if relevant

For security issues, see [SECURITY.md](SECURITY.md) — please do not file public issues.
