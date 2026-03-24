# Changelog

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
- AI rewriting via Claude (Pollinations.ai)
- Fact-checking via Perplexity search
- Image generation via Flux model (768x432)
- GPT humanization pass
- Telegram publishing with polls and reactions
- Duplicate detection (48h hash-based)
- Web dashboard with queue management
- Docker Compose + Railway/Render deployment
