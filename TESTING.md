# End-to-End Test Scenarios

This document outlines the end-to-end (E2E) test scenarios for the Transcripts Connector. These scenarios should be tested manually or with an automated E2E testing suite once the stubbed API calls are replaced with real implementations.

## Scenario 1: Happy Path - First Time Processing

- **Description:** The script successfully processes a calendar event that has a corresponding TLDV meeting with a transcript, and no document has been attached yet.
- **Preconditions:**
    - A Google Calendar event exists.
    - The event has a `conferenceId` that matches a TLDV meeting ID.
    - The TLDV meeting has a transcript available.
    - The calendar event has one or more participants.
    - No Google Doc is attached to the event.
- **Steps:**
    1. Run the main script (`main.py`).
- **Expected Outcome:**
    - A new Google Doc is created with a title derived from the event summary.
    - The formatted transcript from TLDV is inserted into the new document.
    - The new Google Doc is attached to the corresponding Google Calendar event.
    - The Google Doc is shared with all event participants.
    - Logs indicate a successful run for the event.

## Scenario 2: Skip Logic - Meeting Already Processed

- **Description:** The script identifies that a transcript document has already been attached to the event and skips processing.
- **Preconditions:**
    - Same as the happy path, but a Google Doc is **already** attached to the calendar event.
- **Steps:**
    1. Run the main script.
- **Expected Outcome:**
    - The script logs that an attachment already exists for the event.
    - No new Google Doc is created.
    - No new attachment is added.
    - The script skips the event and moves to the next one (if any) or finishes cleanly.

## Scenario 3: Error Case - Transcript Not Found

- **Description:** The script handles a case where the TLDV meeting exists but the transcript is not available.
- **Preconditions:**
    - A Google Calendar event exists with a matching `conferenceId`.
    - The TLDV API call to fetch the transcript for that meeting fails or returns no data.
- **Steps:**
    1. Run the main script.
- **Expected Outcome:**
    - The script logs an error indicating that the transcript could not be fetched for the specific meeting.
    - No Google Doc is created for the event.
    - The script gracefully moves to the next event.

## Scenario 4: Edge Case - No Matching TLDV Meeting

- **Description:** The script handles a calendar event that has no corresponding meeting in TLDV.
- **Preconditions:**
    - A Google Calendar event exists, but its `conferenceId` does not match any meeting in TLDV.
- **Steps:**
    1. Run the main script.
- **Expected Outcome:**
    - The script logs that no matching TLDV meeting was found for the event.
    - No action is taken for this event.
    - The script moves to the next event or finishes cleanly.
