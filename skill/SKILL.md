---
name: fpsot-applications
description: Application intake rules for FPSOT software. Use when writing or reviewing code that takes in an application to a public body in any channel; that keeps drafts, publishes or versions forms, issues receipt records, acknowledgments or reference numbers, opens requests for information, computes deadlines or clocks, handles attachments, acts for another party, shows the status of an application, sends notifications about it, or emits application events.
---

# FPSOT applications

Summary of the FPSOT applications specification. It adds no rules of its own.
The spec text in `spec/` wins on any difference. Each line cites its requirement ID.
The model is `model/applications.yaml`; profiles are in `profiles/`, event schemas in `registry/events/`; `examples/check-examples.py` checks the forms, service declarations, application files and events in `examples/`.

Each line keeps the strength of its rule: "must" and "must not" are MUST and MUST NOT, "should" and "should not" are SHOULD and SHOULD NOT, "may" is MAY.

Other specs own instants, dates and time zones (DAT), decision results, records and review steps (DEC), the party (DMO), accounts and representation (IAM), fee orders (FEE), filings (REG), seals and the log (LOG), audit and business events (OBS), idempotency and events (API), the assurance level (SEC), accessibility (ACC), languages (LOC) and scenarios (TST). Cite them; never redefine them (APP-004).

## Scope, roles and legal status

- Applies to software that takes in an application to a public body, in any channel, from the first draft to its end; builders, case work, the decision, fees, identity proofing and records schedules are out of scope (APP-001).
- State your conformance classes: `service`, `front-end`, `profile`, `operator` (APP-002).
- Never claim that an intake, an acknowledgment or a deadline meets a law (APP-003).
- Follow the pinned versions (APP-005); suites check output only, under TST-044 (APP-006).

## Profiles

- Name the profiles whose law applies; each is an `ApplicationProfile` file in `profiles/` with sources marked `read` or `to-be-verified`; an archived copy counts as read only when it holds the text in force (APP-010).
- Every rule and value cites a source of its profile; holidays carry their dates; profiles have their own SemVer, and removing or relaxing a value is a major release (APP-011).
- Take every calendar, legal time zone, language rule, time of receipt, acknowledgment period, retention floor and prefill basis from a profile, never from code (APP-012).
- When a needed value is missing, such as a calendar for the year or for a day of the roll, or a calendar marked incomplete like the national `ca-federal` one, compute nothing, refer the file to a person with a code, assume nothing (APP-013).
- `core` defaults: 10 MiB per attachment, PDF, JPEG and PNG, SHA-256 only, receipt records sealed at `seal-log` or higher, a notice 14 days before a purge (APP-014).

## Forms

- A form is a `FormDefinition` with `url`, `version`, `status` and a JSON Schema 2020-12 `schema`; each question keeps its `id` while its meaning stays, and takes a new one when it changes (APP-020).
- Status is `draft`, `active` or `retired`; an active version never changes; start new drafts only on active versions (APP-021).
- A front end may use any layout or user interface schema, which must not change what the schema accepts; none is required (APP-022).
- Each question states `required` and `purpose`; each form points to a collection notice per language; labels meet ACC-023 (APP-023).
- Prefill only from a named source on a basis code of the profile; show what was filled and let the applicant correct it unless a binding official source; fill again what the applicant gave earlier (APP-024).
- List `languages`, give each question a label in each; offer the languages that the profile requires; record the language of correspondence and its basis; text comes from message catalogs (APP-025).

## Lifecycle

- An `ApplicationFile` has one of seven states: `draft`, `submitted`, `in-review`, `information-requested`, `decided`, `withdrawn`, `closed`; the last three are final (APP-030).
- Move only along the table, and add each move to `stateHistory` with instant, acting party and reason code (APP-031).
- Only a decision record moves a file to `decided`; the entry names it and copies its `resultKind` and `outcome`; `referred` never moves a file to `decided`; a move is adverse unless `decided` with an outcome in `fullGrantOutcomes`; a review after a decision follows DEC-062 and DEC-063 and never reopens the file (APP-032).
- Keep drafts on the service side by default, or on the device when declared; record `url|version`; drafts survive session expiry; session limits meet WCAG 2.2.1 (APP-033).
- Declare the draft period, tell the applicant, send a notice before a purge, log the purge; resume by sign-in or a single-use expiring link, never by security questions alone (APP-034).
- A draft stays on its form version; a move to a newer version is an explicit logged `migrated` event that carries answers by `id`, drops none silently and shows changed and new questions (APP-035).
- Before submission show every answer and attachment and ask for confirmation; check the answers against the schema; refuse while an attachment is not `clean`; create the first `FileVersion`, the receipt record and a sealed byte-exact copy of the form version (APP-036).
- A `FileVersion` never changes; a reply adds a new version that names the previous one; nothing is overwritten (APP-037).
- An applicant, or a representative whose scope covers it, may withdraw a submitted file; withdrawal is a move, never a deletion (APP-038).

## Receipt records and acknowledgments

- Each submission and each reply creates one immutable `ReceiptRecord`: file, version, reference, received instant in UTC to the second with its `receivedPrecision`, local time with the legal time zone, channel, submitter and representative, destination, SHA-256 digests of form, answers, attachments and rendition (APP-040).
- The received instant is when the submission became accessible in the system of the body, never when someone opened or processed it; for paper, the stamp on arrival; a date-only stamp gives the start of that local day with precision `day`, a stamp to the minute the start of the minute with precision `minute`, everything else `second`; it survives channel and system moves (APP-041).
- Seal each receipt record under LOG at `seal-log` or higher, its id being the id of its seal manifest; correct by a new record (APP-042).
- Send an `Acknowledgment` for each submission, in the language of the file: reference, received time, handling body with contact, expected date or service standard, known missing items with deadlines, how to see the status (APP-043).
- Should acknowledge at once on a digital channel; otherwise send a notice of registration at once and the acknowledgment within the period of the profile; offer a copy to keep; a revisit never resubmits (APP-044).
- Reference: eight random Crockford Base32 characters from a cryptographic source plus a mod-37 check character, shown `XXXX-XXXX-C`; never sequential, encodes nothing (APP-045).
- Read references without regard to case, spaces and hyphens, I and L as 1, O as 0; refuse a wrong check character; status lookup needs a second factor and answers the same whether or not the reference exists (APP-046).

## Requests for information and clocks

- An `InformationRequest` has a reason (`incorrect`, `incomplete`, `outdated`, `complement`), items by question id or attachment, a deadline, its effect on each clock (`start-on-completion`, `suspend`, `none`) and who opened it (APP-050).
- Never more than one open request per file; opening it moves the file to `information-requested`; ask only for what the form or program needs; status `open`, `resolved`, `cancelled` or `expired` (APP-051).
- While a request is open and in time, no adverse decision; tell the decision service, so a missing fact gives `insufficient-information` or `referred` under DEC-025 and the file waits; after a request expires or is cancelled, no adverse decision unless its notice was delivered or a contact attempt meets APP-057; a full grant may go ahead if the program allows (APP-052).
- A reply is a submission (APP-036, APP-063, APP-065 apply): it adds a new file version, a new receipt record that seals the form copy again, and new attachment versions, and resolves the request; cancel only as `issued-in-error`, `no-longer-needed` or `superseded`, with the instant; no adverse decision before the deadline of a cancelled request ends, and none on its items; fill the reply with earlier answers (APP-053).
- Each service declares its clocks; each clock change is a file entry with its instant; apply request effects from data (APP-054).
- Compute each deadline from a `CalendarRule` of the profile and record calendar, version, start, period, raw date and rolled date; never hard-code a calendar; federal holidays include those of the province and place (APP-055).
- Record each outage as an `OutageWindow` and publish it; apply the extension rule that the program declares, from data, and record it on the deadline (APP-056).
- Close for no response only when the program allows it, the request expired, and a logged contact attempt, distinct from the notice of the request, did not fail and was delivered or went through another channel than the notice; should come once part of the period has passed (APP-057).

## Attachments

- Each attachment question declares its media types and maximum size, or takes the core defaults; refuse empty, too large, password-locked or disallowed files with a specific message (APP-060).
- Check the type by content, never by extension or client media type; store under a generated name (APP-061).
- SHA-256 only, recorded as algorithm and value, for integrity, seals and duplicate checks; never MD5 or SHA-1, not even in transit; an upload checksum is a SHA-256 `Content-Digest` under RFC 9530, checked against the file (APP-062).
- Scan state `pending`, `clean`, `infected` or `error`; refuse submission while any file is pending or in error; an infected file never joins a submission (APP-063).
- Keep each original byte for byte; renditions are separate files with their own digest; a new file for an item is a new attachment version, never an overwrite (APP-064).
- On each submission, render a tagged PDF/A of the answers and attachment list, and record its digest in the receipt record (APP-065).
- Show each attachment with its name, size and arrival before and after submission; may reuse an attachment across files of the same applicant (APP-066).

## Representation

- An act of a representative rests on a representation of IAM-061 chosen in the session under IAM-064; ask the authorization engine on every act of an applicant, representative or staff member and record `authorityCheckedAt`; refuse when the check fails or no valid representation covers it; act from one's own account (APP-070).
- Each act records an `ActingParty`: actor account by opaque id, acting party, subject, role, representation id and instant of the check; staff who key in appear as actor with role `staff` (APP-071).
- A self-declared submission for someone else only when declared, marked `self-declared` on the file, each act and the receipt record; only the draft and its submission may be self-declared; later acts come from the subject or a representation; a notice to the declarant only confirms, with no link (APP-072).
- Notify the represented party of a submission in their name, unless no contact exists or the profile or a court order says it puts someone at risk, with the reason recorded (APP-073).
- A revoked representation blocks new acts, keeps past ones, and the represented party sees who acted (APP-074).

## Status, notifications and events

- The applicant sees a `StatusProjection` with one of seven published labels mapped from the state: `not-sent`, `received`, `in-progress`, `action-needed`, `decision-made`, `withdrawn`, `closed` (APP-080).
- Only `action-needed` asks the applicant to act, and shows the items, the deadline and how to respond (APP-081).
- Never show a queue, a sub-state, a risk flag, a score or a staff name; a label must not show the outcome, which comes in the notice of DEC-057; show reference, received instant, handling body and expected date or standard (APP-082).
- Derive the projection from the file of record on read, or rebuild it in the same transaction as each change, staff changes included; keep no drifting copy (APP-083).
- Notify on each submission and when a request opens, recording that notice with the request; should notify before its deadline, when a decision is available and before a purge; should not notify a change that keeps the label (APP-084).
- Notifications hold no decision, reasons, answers or sensitive data, ask for no personal information, carry no attachment and say where to read (APP-085).
- Links point to a domain of the body, in full, with no redirect or tracking; should come from a sender that the body publishes (APP-086).
- Record each notification and each delivery failure on the file; should try another channel after a failure (APP-087).
- Send the five CloudEvents types of `registry/events/` with `subject` the file id and data of ids, codes and instants only, also as business events under OBS-070 (APP-088).

## Channels

- Paper, telephone, counter and digital intake feed the same file and lifecycle, with the same form version and checks (APP-090).
- Record the `channel`, and `capturedBy` for assisted entry, who also appears as the actor (APP-091).
- For paper and counter documents, the received instant is the stamp on arrival, with its precision; record `keyedAt` apart; keep the original or a scan with its digest (APP-092).
- A digital-by-default service offers a non-digital route to the same file, unless its profile cites a law that allows digital only (APP-093).
- Submit is idempotent: a repeat returns the existing reference and receipt record; accept `Idempotency-Key` under API-060 to API-063 and refuse a reused key with another body (APP-094).
- Should flag a second open file of the same subject for the same program; never merge, drop or refuse it automatically (APP-095).
- During an outage accept the same applications through another channel, unless the service is digital only, which then applies its extension rule; error pages say whether answers were kept, until when, when the service returns and what happens to deadlines (APP-096).

## Interfaces, handoffs and conformance

- Create with `POST` and accept `Idempotency-Key`; never edit or delete submitted versions, receipt records, acknowledgments or the content of requests; withdraw, cancel or change a request status as a new resource; authorize every request (APP-100).
- Record in `handoffs` each fee order, filing or decision that a submission starts; never set their statuses or results (APP-101).
- Suites hold forms, service declarations, files, versions, receipt records, requests and EN/FR scenarios with dates and states; should test events under TST-043 (APP-102).
- Synthetic data only, with fictional parties, accounts, references and attachments, and documentation domains (APP-103).
- May offer a GovStack Registration adapter mapped requirement by requirement (APP-104).
- A replacement service or front end passes the same suite under TST-045 (APP-105).
