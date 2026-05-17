# Changelog

## [1.4.5] - 2026-05-17

### Fixed
- Add `rel="noopener noreferrer"` to the `target="_blank"` t.me links on /queue (source on each card) and /sources (`@username` cell) — modern browsers imply `noopener` on `_blank` but older ones (Chrome <88, Safari <12.1) hand `window.opener` to the new tab, letting the destination redirect the dashboard via `window.opener.location`

## [1.4.4] - 2026-05-10

### Fixed
- Drop the `CERT_NONE` SSL context on the aiohttp session that talks to Pollinations — TLS verification was disabled, so the API key in the Authorization header and every model response were riding an unverified channel

## [1.4.3] - 2026-05-03

### Fixed
- Settings save creates `.env` with 0600 from the start (via `os.open` with explicit mode) instead of relying on a post-write `chmod`, closing the race window where a freshly-created file briefly sat at the default-umask perms

## [1.4.2] - 2026-04-26

### Fixed
- Settings save now restricts `.env` to owner read/write (0600) so secrets don't inherit a world-readable umask on the server

## [1.4.1] - 2026-04-19

### Fixed
- Debug mode no longer defaults to on when `FLASK_ENV` is unset (prevents the Werkzeug debugger from being exposed in production if the env file is incomplete)

## [1.4.0] - 2026-04-15

### Added
- Copy button for channel ID on settings page
- Copy button for telegram msg_id in published posts
- Filter sources by username or title
- Configurable dedup window via `DEDUP_HOURS` env var
- FAQ entries about pipeline interval and duplicate detection
- `.hint` utility class for form help text

### Changed
- Smooth fade-in animation for details/accordion panels

## [1.3.1] - 2026-04-12

### Fixed
- Mask secret values (API key, API hash) on settings page so they don't leak in HTML source

## [1.3.0] - 2026-04-06

### Added
- Copy button for source channel usernames
- Skip-to-content link and aria attributes on navigation
- Search filter on published posts page
- Loading state for queue approve/reject buttons
- Channel username validation in add-source form
- `.muted` utility class for subdued text

### Changed
- Smooth hover transitions for nav links and cards
- Friendlier API error messages for sources and pipeline

### Fixed
- Inconsistent input colors on settings page

## [1.2.2] - 2026-04-05

### Fixed
- Sanitize newline characters in settings values to prevent .env injection

## [1.2.1] - 2026-03-29

### Fixed
- Replaced hardcoded fallback secret key with random token generation
- Added missing input validation on form-based source add endpoint

## [1.2.0] - 2026-03-24

### Added
- GitHub Actions CI pipeline (lint + tests on Python 3.11/3.12)
- Unit tests: deduplication logic, config validation, module imports
- Configuration examples for 3 channel types (news, crypto, tech)
- `examples/` folder with ready-to-use templates

### Changed
- Improved error handling in AI calls

## [1.1.0] - 2026-03-23

### Added
- Favicon and theme-color meta tag for mobile browsers
- robots.txt route to prevent search engine indexing
- Web dashboard analytics with pipeline performance charts
- Settings page for API key management

## [1.0.0] - 2026-03-22

### Added
- Multi-source Telegram channel scanning (40+ channels)
- Smart rewriting via Pollinations.ai
- Fact-checking via Perplexity search
- Image generation via Flux model (768x432)
- Humanization pass (natural language polish)
- Telegram publishing with polls and reactions
- Duplicate detection (48h hash-based)
- Web dashboard with queue management
- Docker Compose + Railway/Render deployment
