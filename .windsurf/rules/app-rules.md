---
trigger: always_on
---

You have the MVP
- You have to figure out how to implement new providers besides tldv

Authentication & Access
– Use OAuth 2.0 to access Google Calendar API and Google Docs API.
– Store tokens securely and auto-refresh them upon expiration.

Fetching Transcripts
– Call TLDV API to retrieve the list of recorded meetings and their transcripts.
– Filter recordings by the Google Calendar event ID (stored in TLDV metadata).

Linking Events & Documents
– For each Calendar event, look for an attached Google Doc via the Calendar API’s attachments.
– If no Doc exists, create a new one in the user’s designated folder.

Inserting the Transcript
– Format the transcript (heading, timestamps, speaker labels).
– Append or prepend it to the Google Doc, preserving version history.

Error Handling & Logging
– On failure (API errors, permission issues), return a clear message and error code.
– Log key steps: TLDV request, Doc lookup/creation, text insertion.

Developer Interaction
– Ask clarifying questions for ambiguous parameters (e.g. time format, document structure).
– Propose alternatives when hitting API limits.

Code & Style Guidelines
– Generate code samples in the chosen language (Node.js or Python) with clear comments.
– Follow best practices (async/await or Promises, exception handling, modularity).

Testing
– Automatically suggest unit tests for each API call.
– Outline end-to-end scenarios (simulate a meeting, fetch transcript, insert into Doc).

Documentation
– After each major step, update a README with endpoint descriptions and examples.
– Maintain a CHANGELOG for key feature additions.

Version Control
– Recommend a repo structure (e.g. src/, tests/, docs/).
– Integrate linters/formatters (ESLint & Prettier or Black & isort).

Iterative Workflow
– After completing each milestone (transcript retrieval, Doc insertion, etc.), request user feedback.
– Only proceed to the next phase once approved.

Security & Privacy
– Never log full transcript text in public logs.
– Encrypt sensitive data at rest and in transit.

Extensibility
– Architect the code so new note-taking services can be added with minimal changes.