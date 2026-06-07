# Changelog

## [Unreleased]

### Security
- Mark the dedup `md5` hash `usedforsecurity=False` — it's only a repost fingerprint, never a security check, so this states the intent and stops Bandit flagging it as weak crypto

## [1.6.0] - 2026-06-04

### Added
- Press `e` on /queue to expand every preview panel at once — Escape already collapsed them all, this is the other half of the shortcut
- Character count on the Pollinations key field, same as the API hash — both are masked, so without it there's no way to tell whether a pasted key came through whole or got truncated
- Last-run timestamp on the /analytics page — the 30-day charts never said how fresh the data behind them was
- FAQ note on backing up the SQLite database — it's a single file, but people kept missing where it lives
- "No matching items" message on /queue when a filter hides everything — /published already showed one, the queue just left a blank gap that read like a load failure

### Changed
- Reject button now uses the same shade as Approve — red-800 sat noticeably darker than the green beside it
- Copy buttons give a small pop when they flip to "Copied!" — the text swap alone was easy to miss
- Escape now also clears the search box, not just the open details panels
- `scope="col"` on the recent-runs table headers so screen readers tie each cell back to its column

### Fixed
- Expired-session error now links to the relevant FAQ entry instead of dead-ending you on an error with no next step
- Validate `channel_id` on the backend too — the form's check only runs in the browser, so a direct POST could still write a bad value

## [1.5.1] - 2026-05-31

### Added
- Optional HTTP Basic Auth for the dashboard via `DASHBOARD_USER`/`DASHBOARD_PASSWORD` — leave the password unset to keep it open on localhost, set it to lock down deployments bound to `0.0.0.0` where the settings page and pipeline trigger were otherwise reachable by anyone on the network (`/health` stays unauthenticated for uptime probes)

## [1.5.0] - 2026-05-29

### Added
- Last-scanned timestamp under the /queue heading — the nav's "Last run" readout is hidden on phones, so there was no way to gauge how fresh the queued items were without flipping back to the dashboard

### Changed
- Auto-refresh timers (queue, published, sources, analytics, dashboard stats poll) now skip their tick while the tab is hidden instead of reloading background tabs for nothing; the timer keeps ticking so the next visible tick picks up the latest state

### Fixed
- Stop iOS Safari from zooming in when you tap a search/input field on mobile
- Wrap the `/published` list route in try/except — it was the last list route still able to surface a raw 500 instead of a friendly error
- `aria-hidden` on the published-page accordion chevron so screen readers don't announce the decorative open/close graphic as noise

## [1.4.7] - 2026-05-24

### Fixed
- Drop a non-numeric `telegram_api_id` on settings save and keep the previous value instead — the form's `pattern="[0-9]+"` only fires in the browser, so a curl/devtools POST with `telegram_api_id=abc` used to write straight to `.env` and then crash Telethon at the next pipeline login

## [1.4.6] - 2026-05-24

### Fixed
- Reject non-object JSON bodies in the `POST /api/sources` endpoint — `request.get_json() or {}` only fell back to `{}` for the falsy parse results (None/empty list/empty string), so a posted body of `[1,2,3]` or `"foo"` or `42` slipped past the fallback and the next `data.get("username", ...)` raised `AttributeError`, which the 500 handler swallowed into a generic "internal server error" instead of a proper 400 about invalid input

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
