# Changelog

All notable changes to this specification are listed here.
The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and versions follow [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Scope, conformance classes, legal status, owners of the parts and conformance APP-001 to APP-006: any application to a public body, in any channel; the classes `service`, `front-end`, `profile` and `operator`; no claim that an intake, an acknowledgment or a deadline meets a law; each part taken from the specification that owns it; pinned versions; suites that check output only.
- Jurisdiction profiles APP-010 to APP-014: profile files with sources marked read or to be verified; dated holidays and profile versions; no calendar, language rule or time of receipt in the core; referral to a person when a value is missing; core defaults of 10 MiB, PDF, JPEG and PNG, SHA-256 only, `seal-log` and a notice 14 days before a purge. Profiles `core`, `ca-federal` (Interpretation Act, Directive on Service and Digital, Official Languages Act, Privacy Act and its regulations, Part 2 of the federal law on electronic documents) and `ca-qc` (Loi d'interprétation, Loi concernant le cadre juridique des technologies de l'information, Loi sur la justice administrative, Charte de la langue française, access law, law on information resources, Loi sur l'administration publique, SGQRI 008 3.0) in `profiles/`.
- Forms APP-020 to APP-025: JSON Schema 2020-12 forms with a canonical address, a business version and stable question ids; `draft`, `active` and `retired` versions that never change once active; no user interface schema required; required flags, purposes and collection notices; prefill from a named source on a basis of the profile; languages and the basis of the language of correspondence.
- Lifecycle APP-030 to APP-038: seven states and their moves; decisions only from a decision record, and reviews under DEC-062 and DEC-063; drafts on the service side that survive the session; draft periods, notices, logged purges and resume without security questions; explicit, logged migrations to a new form version; the check of answers, fail-closed submission and a sealed copy of the form; immutable file versions; withdrawal as a move.
- Receipts and acknowledgments APP-040 to APP-046: sealed receipt records with the instant of accessibility in UTC and in the legal time zone, the channel, the parties and the SHA-256 digests; acknowledgments and notices of registration; random Crockford Base32 reference numbers with a mod-37 check character; lookup with a second factor and no hint of existence.
- Requests for information and clocks APP-050 to APP-057: requests with a reason, items, a deadline and clock effects; one open request at a time; no adverse decision while one is open and in time; replies as new versions; clocks as data; deadlines from the calendar of the profile; outage windows and extension rules of the program; closing only after an expired deadline and a logged contact attempt.
- Attachments APP-060 to APP-066: declared types and sizes; type by content; SHA-256 only, with `Content-Digest` of RFC 9530 on upload and no MD5 or SHA-1 at all; scan states and fail-closed submission; originals kept and versions never overwritten; a tagged PDF/A rendition of each submission.
- Representation APP-070 to APP-074: authority checked on every act under IAM-061 and IAM-064; the acting party apart from the subject; a marked self-declared mode; notice to the represented party; revocation.
- Status and notifications APP-080 to APP-088: seven published labels mapped from the states; one label for action needed; no queue, flag, staff name or outcome; projections from the file of record; notifications without decisions or answers, with full links to the domains of the body; delivery records; five CloudEvents types with schemas in `registry/events/`.
- Channels APP-090 to APP-096: one file for every channel; the channel and the staff member of assisted entry; the stamp on arrival as received instant for paper; a route that is not digital; idempotent submit; flagged duplicates; outage pages.
- Interfaces, handoffs and conformance APP-100 to APP-105.
- Informative pages on the alignment with GovStack Registration 1.0.1, Démarche Numérique, FHIR Questionnaire, GOV.UK Forms, the Dutch ZGW APIs and CloudEvents, and on questions for counsel.
- The LinkML model `model/applications.yaml`, which imports the data types, decisions and party models.
- The state diagram of a file in `diagrams/`, in English and French.
- Synthetic examples in `examples/`: five form definitions, four service declarations, and application files for a pleasure craft license that starts the fee order and the filing of the fees and registry examples; a Québec business permit in French only under article 21.9 of the Charter; a request for information whose deadline rolls past 24 June and that suspends a clock, with a second file closed after an expired request and a logged contact attempt; a submission by a representative and a self-declared one; a paper application keyed in five days after it arrived; a draft moved to a new form version. A check, its test of 65 broken copies and 2 accepted copies, and scenarios in English and French run in the `examples` job of the continuous integration.
- Comparison data with international rows and rows for Canada, Québec and France.
- How-to guide that takes a program through the specification.

### Known gaps

- The 1.0.1 page of GovStack Registration did not load; the research read its repository at a matching commit.
- The French code des relations entre le public et l'administration was read only in archived copies of 2024 and 2025.
- The proclamations behind Thanksgiving Day and the birthday of the Sovereign in 2026, and whether a Saturday is a working day in Québec outside the land register, are to be verified.
- The calendars hold 2026 only; the next release of each profile adds 2027.
- The generated forms of the model under DMO-014 and DMO-015, and the `model/examples/` folder of DMO-017, are deferred to the conformance suite.
