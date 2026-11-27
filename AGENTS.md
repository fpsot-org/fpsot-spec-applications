# Instructions for agents

This repository holds the FPSOT applications specification: what software must record and prove when a public body takes in an application, in any channel. It covers forms as versioned JSON Schema documents with stable question ids; one lifecycle of seven states with drafts, explicit form migrations and immutable file versions; sealed receipt records of the instant when a submission became accessible, and acknowledgments; random reference numbers with a Crockford check character; requests for information with their reason, items, deadline from the calendar of the profile and effect on each clock; attachments checked by content, hashed with SHA-256 only and scanned before submission; representation checked on every act; a closed list of status labels; notifications without decisions or answers; channels that all feed the same file; and the events of each change. The decision itself belongs to the decisions specification.

- The normative text is in `spec/en/` and `spec/fr/`. Every rule has an ID such as `APP-001`.
- Follow `skill/SKILL.md` when you write or review code that takes in applications, keeps drafts, issues receipt records or acknowledgments, opens requests for information, computes deadlines, handles attachments, acts for another party, shows the status of an application or sends notifications about it. The spec text wins on any difference.
- Every page exists in English and in French, with the same file name and the same IDs.
- Terms and abbreviations come from the term base of `fpsot-spec-writing`. Add a missing term there first; `TERMS-NEEDED.md` lists the ones this spec waits for.
- This is a layer 2 specification. It may cite every published layer 0, layer 1 and layer 2 specification by rule ID.
- Other specifications own instants, dates and time zones (data types), decision results, decision records and review steps (decisions), the party (data models), accounts and representation (identity), fee orders (fees), filings (registry), seals and the log (log), audit and business events (observability), idempotency and events (api-restful), the level of assurance (security), accessibility, languages and scenarios. Cite their rules; never redefine them.
- MD5 and SHA-1 appear nowhere, not even as a transport checksum. The only digest is SHA-256, recorded as an algorithm and a value.
- `model/applications.yaml` is the source of the record forms. `model/imports/` holds unchanged copies of the data types, decisions and party models. When you change the model, a profile, a form, a service declaration or a fixture, run `bash examples/test-examples.sh`.
- Jurisdiction values live in `profiles/` and in service declarations, never in the model or the check script. A calendar holds dated holidays; never compute a holiday in code.
- Examples hold synthetic data only: fictional people, bodies, programs and references, domains reserved for documentation.
- Do not copy text from statutes, regulations or standards. Summarize in your own words and cite the exact version, with an archived copy.
- Do not state a legal point as a rule. Points that need a lawyer go in an informative note or in `questions-for-counsel.adoc`, and a text that nobody read at the source is marked "to be verified". France has comparison data only, no profile.
- Commits follow Conventional Commits and are signed. Pull requests are squash-merged.
