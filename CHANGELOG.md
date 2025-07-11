# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.3.0] - 2025-07-08

### Added
- **AI-Powered Matching**: Introduced a new `AIMapper` class that uses an LLM (via `litellm`) to match transcripts to calendar events based on their raw text content.
- **Force AI Flag**: Added a `--force-ai` command-line argument to bypass standard matching logic and use the AI mapper exclusively.

### Changed
- **AI Prompt Engineering**: Refined the prompt sent to the LLM to ensure it returns a structured, predictable response (either a numeric index or 'None'), improving reliability.

### Fixed
- **Dependency Conflicts**: Resolved complex dependency issues between `litellm` and `openai`. The project now uses versions compatible with each other and with Python 3.13.
- **Python 3.13 Compatibility**: Fixed a `ModuleNotFoundError` for `imghdr` by upgrading `litellm` to a version where this legacy module is no longer used.


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

## [0.2.0] - 2025-07-01

### Added
- **Two-Stage Matching Logic**: Implemented a more robust process for pairing calendar events with TLDV recordings. The script now first attempts to match by `conferenceId` and then falls back to matching by the closest time proximity (within a 5-minute window).
- **Cleanup Script**: Added a new command-line tool (`cleanup_attachments.py`) to safely find and delete documents and calendar attachments created by the connector. It includes a `--dry-run` mode for safe listing before deletion.
- **Standardized Document Titling**: All generated Google Docs are now prefixed with `ANAIT: Transcript for` for easier identification.

### Changed
- The script now processes events that have concluded in the past 7 days, instead of upcoming events.
- Updated `README.md` with detailed setup and usage instructions for the main script and the new cleanup utility.

## [0.1.0] - Initial Version

- Initial setup of the project structure.
- TLDV API integration to fetch meetings and transcripts.
- Basic Google Calendar and Docs integration (stubbed).
- Core transcript formatting logic.
- Setup of logging, environment variables, and unit tests.
