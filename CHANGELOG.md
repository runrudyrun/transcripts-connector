# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial project structure with stubs for Google APIs (Docs, Calendar).
- TLDV API integration to fetch meetings and transcripts.
- Transcript formatting utility.
- Core orchestration logic in `main.py`.
- Centralized logging using Python's `logging` module.
- Unit tests for all API modules (`tldv_api`, `google_calendar_api`, `google_docs_api`).
- `TESTING.md` with end-to-end test scenarios.
- Comprehensive `README.md` with setup and usage instructions.

### Changed
- Replaced all `print` statements with structured logger calls.
- Fixed TLDV API endpoint and authentication logic.
- Corrected `format_transcript` function call signature.

### Fixed
- Corrected exception types in unit tests to match application code.
