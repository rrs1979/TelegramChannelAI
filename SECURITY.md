# Security Policy

## Reporting a vulnerability

If you find a security issue (credential leak, RCE, auth bypass, anything that could compromise users running this code), **do not file a public issue**.

Email: `rebrov.roman@gmail.com` with:
- A description of the issue
- Steps to reproduce
- Affected version / commit

Expect a response within 7 days. Confirmed issues are usually patched within 14 days; coordinated disclosure timing depends on impact.

## In scope

- The Python code in this repo (`channel_ai.py`, `web/`, `tests/`)
- Default configuration in `.env.example`
- The Docker setup and `docker-compose.yml`

## Out of scope

- Vulnerabilities in upstream dependencies — report those upstream (`pip install pip-audit && pip-audit` is a good first check)
- Pollinations.ai service issues — report to https://pollinations.ai
- Telegram client / Telethon issues — report to https://github.com/LonamiWebs/Telethon
- Issues that require admin-level access to a deployed instance to exploit

## Things that are **not** vulnerabilities

- API keys printed in your own logs when `LOG_LEVEL=DEBUG` (don't ship that to prod)
- The dashboard being accessible without auth on `localhost` (that's the point — put it behind your own reverse proxy with auth if exposing it)
- Telegram session strings stored unencrypted in `.env` (they're meant for your own machine; don't commit `.env`)
