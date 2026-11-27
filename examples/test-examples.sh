#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Tests examples/check-examples.py: the repository passes, and each broken copy fails
# for the reason that its case names. Each case copies the files that the check reads,
# breaks one rule, and expects the check to report that rule.
set -uo pipefail
here=$(cd "$(dirname "$0")/.." && pwd)
check="$here/examples/check-examples.py"
fail=0
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

if ! python3 -I "$check" "$here"; then
  echo "FAIL: the repository itself does not pass"; fail=1
fi

# setup_case NAME PYTHON: the script runs in a copy of the repository.
setup_case() {
  local name=$1 script=$2 dir="$tmp/$1"
  mkdir -p "$dir"
  cp -r "$here/model" "$here/profiles" "$here/registry" "$here/examples" "$dir/"
  (cd "$dir" && python3 -I -c "import json, yaml
def rj(p): return json.load(open(p, encoding='utf-8'))
def wj(p, d): json.dump(d, open(p, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
def ry(p): return yaml.safe_load(open(p, encoding='utf-8'))
def wy(p, d): yaml.safe_dump(d, open(p, 'w', encoding='utf-8'), allow_unicode=True, sort_keys=False)
PC, QB, IR = 'examples/pleasure-craft/application.json', 'examples/quebec-business-permit/application.json', 'examples/information-request/application.json'
OB, PI, DM = 'examples/on-behalf/application.json', 'examples/paper-intake/application.json', 'examples/draft-migration/application.json'
FPC, FB0 = 'examples/forms/pleasure-craft-license-2.0.0.json', 'examples/forms/example-benefit-1.0.0.json'
SFB, SQG = 'examples/services/example-federal-benefit.yaml', 'examples/services/example-home-adaptation-grant.yaml'
QC, CF = 'profiles/ca-qc.yaml', 'profiles/ca-federal.yaml'
FEN, FFR = 'examples/features/en/applications.feature', 'examples/features/fr/applications.feature'
E1 = 'examples/pleasure-craft/events/receipt-issued.json'
$script") || { echo "FAIL: case $name: the setup script failed"; fail=1; return 1; }
}

# case_fails NAME EXPECTED-REGEX PYTHON: the broken copy fails for the rule that the regex names.
case_fails() {
  local name=$1 want=$2 out
  setup_case "$name" "$3" || return
  if out=$(python3 -I "$check" "$tmp/$name" 2>&1); then
    echo "FAIL: case $name passed but should fail"; fail=1
  elif ! grep -qE -- "$want" <<<"$out"; then
    echo "FAIL: case $name failed for another reason:"; echo "$out" | head -5; fail=1
  else
    echo "ok: case $name fails"
  fi
}

# case_passes NAME PYTHON: the changed copy still passes, which shows that the check accepts it.
case_passes() {
  local name=$1 out
  setup_case "$name" "$2" || return
  if ! out=$(python3 -I "$check" "$tmp/$name" 2>&1); then
    echo "FAIL: case $name should pass:"; echo "$out" | head -5; fail=1
  else
    echo "ok: case $name passes"
  fi
}

# Reference numbers (APP-045, APP-046).
case_fails reference-wrong-check-character 'check character does not match \(APP-045, APP-046\)' \
  'd = rj(PC); d["files"][0]["reference"] = "7HQ3-MZ4K-5"; wj(PC, d)'
case_fails reference-sequential 'does not match the pattern of ReferenceNumber' \
  'd = rj(PC); d["files"][0]["reference"] = "APP-2026-000001"; wj(PC, d)'

# Digests: SHA-256 only, over the exact bytes (APP-036, APP-040, APP-062).
case_fails attachment-md5-digest "not a value of DigestAlgorithm|only digest algorithm is sha-256 \(APP-062\)" \
  'd = rj(PC); d["attachments"][0]["digest"]["algorithm"] = "md5"; wj(PC, d)'
case_fails md5-transport-checksum 'names a weak digest: MD5 and SHA-1 are not used at all \(APP-062\)' \
  'd = rj(PC); d["versions"][0]["contentMd5"] = "rL0Y20zC+Fzt72VPzMSk2A=="; wj(PC, d)'
case_fails sha1-in-a-profile 'names a weak digest' \
  'd = ry(QC); d["rules"][0]["code"] = "sha1-checksum-of-receipt"; wy(QC, d)'
case_fails form-changed-after-submission 'formDigest does not match the SHA-256 digest .* \(APP-036\)' \
  'd = rj(FPC); d["title"][0]["text"] = "Apply for a license"; wj(FPC, d)'
case_fails answers-rewritten-after-submission 'answersDigest does not match the SHA-256 digest .* \(APP-040\)' \
  'd = rj(PC); d["versions"][0]["answers"]["craftLengthMeters"] = "7.2"; wj(PC, d)'
case_fails attachment-file-changed 'attachment .* does not match the SHA-256 digest .* \(APP-062\)' \
  'open("examples/pleasure-craft/attachments/bill-of-sale.pdf", "ab").write(b"x")'
case_fails attachment-type-from-extension 'is not a image/png by its content \(APP-061\)' \
  'd = rj(QB); d["attachments"][0]["detectedMediaType"] = "image/png"; wj(QB, d)'
case_fails attachment-type-not-allowed 'which question proofOfOwnership does not accept \(APP-060\)' \
  'import shutil; shutil.copy("examples/quebec-business-permit/attachments/plan-etablissement.pdf", "examples/pleasure-craft/attachments/bill-of-sale.pdf")
d = rj(PC); a = d["attachments"][0]; b = open("examples/pleasure-craft/attachments/bill-of-sale.pdf", "rb").read()
open("examples/pleasure-craft/attachments/bill-of-sale.pdf", "wb").write(b"\x89PNG\r\n\x1a\n" + b)
import hashlib; b = open("examples/pleasure-craft/attachments/bill-of-sale.pdf", "rb").read()
a["detectedMediaType"] = "image/png"; a["byteSize"] = len(b); a["digest"]["value"] = hashlib.sha256(b).hexdigest()
d["receiptRecords"][0]["attachmentDigests"][0]["digest"]["value"] = a["digest"]["value"]; wj(PC, d)'

# Scans fail closed (APP-063).
case_fails submitted-while-scan-pending 'whose scan state is pending \(APP-036, APP-063\)' \
  'd = rj(PC); a = d["attachments"][0]; a["scanState"] = "pending"; del a["scannedAt"]; wj(PC, d)'
case_fails submitted-while-scan-error 'whose scan state is error \(APP-036, APP-063\)' \
  'd = rj(PC); d["attachments"][0]["scanState"] = "error"; wj(PC, d)'

# Versions never change and never overwrite (APP-037, APP-064).
case_fails reply-overwrites-attachment 'replaces an attachment without a new attachment version \(APP-064\)' \
  'd = rj(IR); a = d["attachments"][1]; a["version"] = 1; del a["previousAttachmentId"]; wj(IR, d)'
case_fails second-version-without-previous 'is number 2 and does not name version 1 of its file \(APP-037\)' \
  'd = rj(IR); del d["versions"][1]["previousVersionId"]; wj(IR, d)'

# Receipt records and acknowledgments (APP-040 to APP-044).
case_fails receipt-time-is-processing-time 'another received instant than its version \(APP-041\)' \
  'd = rj(PC); d["receiptRecords"][0]["receivedAt"] = "2026-03-10T15:00:00Z"; wj(PC, d)'
case_fails receipt-without-legal-time-zone 'not the legal time zone of its profile \(APP-040, APP-012\)' \
  'd = rj(PC); d["receiptRecords"][0]["receivedLocal"] = {"localDateTime": "2026-03-10T14:58:30", "timeZone": "UTC"}; wj(PC, d)'
case_fails receipt-local-time-wrong 'the local time does not match the received instant in America/Toronto \(APP-040\)' \
  'd = rj(PC); d["receiptRecords"][0]["receivedLocal"]["localDateTime"] = "2026-03-10T09:58:30"; wj(PC, d)'
case_fails paper-received-at-keying 'another received instant than its version \(APP-041\)' \
  'd = rj(PI); d["receiptRecords"][0]["receivedAt"] = d["versions"][0]["keyedAt"]; wj(PI, d)'
case_fails two-receipt-records 'has 2 receipt records, and each submission creates one \(APP-040\)' \
  'd = rj(PC); r = dict(d["receiptRecords"][0], id="019c5a00-0003-7000-8000-0000000000ff"); d["receiptRecords"].append(r); wj(PC, d)'
case_fails receipt-below-seal-log 'below seal-log \(APP-042\)' \
  'd = rj(PC); d["receiptRecords"][0]["sealProfile"] = "unsealed"; wj(PC, d)'
case_fails no-acknowledgment 'has 0 acknowledgments, and each submission gets one \(APP-043\)' \
  'd = rj(PC); d["acknowledgments"] = []; del d["acknowledgments"]; wj(PC, d)'
case_fails acknowledgment-in-another-language 'is not in the language of the file \(APP-043\)' \
  'd = rj(QB); d["acknowledgments"][0]["language"] = "en"; wj(QB, d)'
case_fails acknowledgment-without-date-or-standard 'gives neither an expected date nor a service standard \(APP-043\)' \
  'd = rj(PC); del d["acknowledgments"][0]["serviceStandard"]; wj(PC, d)'
case_fails no-receipt-notification 'has no notification of receipt \(APP-084\)' \
  'd = rj(PC); d["notifications"] = d["notifications"][1:]; wj(PC, d)'

# Lifecycle (APP-021, APP-030 to APP-032).
case_fails reopen-after-decision 'moves after the final state decided \(APP-030\)' \
  'd = rj(PC); f = d["files"][0]; f["stateHistory"].append(dict(f["stateHistory"][2], at="2026-03-11T13:00:00Z")); f["state"] = "in-review"; d["projections"][0]["label"] = "in-progress"; wj(PC, d)'
case_fails decided-without-decision-record 'without its decision record and its result kind \(APP-032\)' \
  'd = rj(PC); del d["files"][0]["stateHistory"][3]["decisionRecordId"]; wj(PC, d)'
case_fails referred-moves-to-decided 'on a referred result, which is not a decision \(APP-032, DEC-024\)' \
  'd = rj(PC); h = d["files"][0]["stateHistory"][3]; h["resultKind"] = "referred"; del h["outcome"]; wj(PC, d)'
case_fails draft-on-retired-form 'starts a draft on .* after it was retired \(APP-021\)' \
  'd = rj(OB); d["files"][0]["draftStartedAt"] = "2026-09-02T13:00:00Z"; wj(OB, d)'
case_fails submitted-without-draft "moves from None to submitted, which APP-031 does not allow" \
  'd = rj(PC); d["files"][0]["stateHistory"] = d["files"][0]["stateHistory"][1:]; wj(PC, d)'

# Requests, clocks and deadlines (APP-050 to APP-057).
case_fails adverse-decision-while-request-open 'decided on an adverse outcome while request .* is open and in time \(APP-052\)' \
  'd = rj(IR); f = d["files"][0]; h = f["stateHistory"]; h[-1] = {"state": "decided", "at": "2026-06-01T13:00:00Z", "actor": h[-2]["actor"], "reason": "decision-recorded", "decisionRecordId": "019c5a00-000b-7000-8000-0000000000aa", "resultKind": "decided", "outcome": "refused"}
f["state"] = "decided"; q = d["requests"][0]; q["status"] = "open"; del q["resolvedAt"]; del q["resolvedByVersionId"]; wj(IR, d)'
case_fails deadline-not-rolled-past-holiday 'the deadline after the roll must be 2026-06-25 \(APP-055\)' \
  'd = rj(IR); d["requests"][0]["deadline"]["date"] = "2026-06-24"; wj(IR, d)'
case_fails deadline-on-federal-calendar "uses calendar ca-federal-national, which no profile of its service holds \(APP-055\)" \
  'd = rj(IR); d["requests"][0]["deadline"]["calendar"] = "ca-federal-national"; wj(IR, d)'
case_fails deadline-outside-calendar 'does not cover 2027-03-21, a missing value \(APP-013\)' \
  'd = rj(IR); dl = d["requests"][0]["deadline"]; dl["periodDays"] = 300; dl["rawDate"] = "2027-03-21"; dl["date"] = "2027-03-22"; wj(IR, d)'
case_fails holiday-removed-from-profile 'the deadline after the roll must be 2026-06-24 \(APP-055\)' \
  'd = ry(QC); d["calendars"][0]["holidays"] = [h for h in d["calendars"][0]["holidays"] if h["date"] != "2026-06-24"]; wy(QC, d)'
case_fails holiday-without-source 'cites nowhere, which is not a source of the profile \(APP-011\)' \
  'd = ry(CF); d["calendars"][0]["holidays"][0]["sourceId"] = "nowhere"; wy(CF, d)'
case_fails extension-without-outage 'applies an extension without its outage .* \(APP-056\)' \
  'd = rj(IR); d["outages"] = []; del d["outages"]; wj(IR, d)'
case_fails two-open-requests 'more than one open request \(APP-051\)' \
  'd = rj(IR); q = dict(d["requests"][1], id="019c5a00-0005-7000-8000-0000000000aa", status="open"); del q["expiredAt"]; d["requests"][1]["status"] = "open"; del d["requests"][1]["expiredAt"]; d["requests"].append(q); wj(IR, d)'
case_fails clock-not-suspended 'records no suspension when it opened \(APP-054\)' \
  'd = rj(IR); c = d["files"][0]["clocks"][0]["changes"]; d["files"][0]["clocks"][0]["changes"] = [x for x in c if x["change"] != "suspended"]; wj(IR, d)'
case_fails clock-effect-missing 'does not state its effect on each clock of the program \(APP-050, APP-054\)' \
  'd = rj(IR); d["requests"][0]["clockEffects"] = d["requests"][0]["clockEffects"][:1]; wj(IR, d)'
case_fails closed-without-contact-attempt 'closed without a logged contact attempt .* \(APP-057\)' \
  'd = rj(IR); del d["files"][1]["stateHistory"][3]["contactAttemptId"]; wj(IR, d)'
case_fails closed-on-failed-channel 'contact attempt through a channel that failed \(APP-057, APP-087\)' \
  'd = rj(IR); d["contactAttempts"][0]["notificationId"] = "019c5a00-0007-7000-8000-000000000008"; d["contactAttempts"][0]["at"] = "2026-08-10T14:00:05Z"; wj(IR, d)'
case_fails closed-before-expiry 'closed without a request that expired before \(APP-057\)' \
  'd = rj(IR); d["requests"][1]["expiredAt"] = "2026-09-17T04:00:00Z"; wj(IR, d)'
case_fails expired-before-deadline-ended 'expired before the end of its deadline \(APP-057\)' \
  'd = rj(IR); d["requests"][1]["expiredAt"] = "2026-09-15T13:00:00Z"; wj(IR, d)'
case_fails closing-not-allowed 'closed for no response, which its program does not allow \(APP-057\)' \
  'd = ry(SQG); d["closingForNoResponse"] = False; wy(SQG, d)'

# Representation (APP-070 to APP-073).
case_fails representative-authority-not-checked 'an act of the role representative without a check of its authority \(APP-070\)' \
  'd = rj(OB); del d["versions"][0]["submittedBy"]["authorityCheckedAt"]; wj(OB, d)'
case_fails representative-without-representation 'a representative acts on a representation that the service checked \(APP-070\)' \
  'd = rj(OB); del d["files"][0]["stateHistory"][1]["actor"]["representationId"]; wj(OB, d)'
case_fails acting-party-merged-with-subject 'the subject of the act is not the party of the file \(APP-071\)' \
  'd = rj(OB); a = d["files"][0]["stateHistory"][1]["actor"]; a["subjectPartyId"] = a["actingPartyId"]; wj(OB, d)'
case_fails self-declared-not-allowed 'is self-declared, which its service does not allow \(APP-072\)' \
  'd = ry(SFB); d["selfDeclaredSubmissions"] = False; wy(SFB, d)'
case_fails represented-party-not-notified 'who received no notice \(APP-073\)' \
  'd = rj(OB); d["notifications"] = [n for n in d["notifications"] if not (n["fileId"].endswith("5") and n["recipientRole"] == "represented-party")]; wj(OB, d)'

# Channels (APP-091 to APP-093).
case_fails paper-without-keying-instant 'so it records keyedAt \(APP-092\)' \
  'd = rj(PI); del d["versions"][0]["keyedAt"]; wj(PI, d)'
case_fails assisted-without-staff 'records in capturedBy who keyed it in \(APP-091\)' \
  'd = rj(PI); del d["versions"][0]["capturedBy"]; wj(PI, d)'
case_fails digital-only-without-law 'names the source of its profile that allows it \(APP-093\)' \
  'd = ry(SFB); d["channels"] = ["digital"]; wy(SFB, d)'

# Languages (APP-025).
case_fails business-permit-in-english "rule charter-21-9 of the profile asks for fr only .* \(APP-025\)" \
  'd = rj(QB); d["files"][0]["languageBasis"] = "french-default"; wj(QB, d)'
case_fails language-without-basis 'records a language basis that no profile gives for its language \(APP-025\)' \
  'd = rj(PC); d["files"][0]["languageBasis"] = "charter-21-9"; wj(PC, d)'

# Status and notifications (APP-080 to APP-087).
case_fails projection-shows-queue 'queue is not a slot of StatusProjection' \
  'd = rj(QB); d["projections"][0]["queue"] = "inspection-team-b"; wj(QB, d)'
case_fails projection-shows-outcome 'is decided, so its label is decision-made, not granted' \
  'd = rj(PC); d["projections"][0]["label"] = "granted"; wj(PC, d)'
case_fails projection-internal-state 'is in-review, so its label is in-progress, not received \(APP-080\)' \
  'd = rj(QB); d["projections"][0]["label"] = "received"; wj(QB, d)'
case_fails action-needed-without-request 'shows action-needed without its open request \(APP-081\)' \
  'd = rj(QB); p = d["projections"][0]; p["label"] = "action-needed"; p["actionNeeded"] = {"requestId": "019c5a00-0005-7000-8000-0000000000aa", "items": ["floorPlan"], "deadline": "2026-07-15", "howToRespond": "https://permis.example.org/etat"}; d["files"][0]["state"] = "information-requested"; wj(QB, d)'
case_fails notification-with-decision-content 'reasons is not a slot of Notification' \
  'd = rj(PC); d["notifications"][1]["reasons"] = ["eligible"]; wj(PC, d)'
case_fails notification-link-other-domain 'which is not a domain of the body, in full, over HTTPS \(APP-086\)' \
  'd = rj(PC); d["notifications"][0]["links"] = ["https://short.example.com/abc"]; wj(PC, d)'
case_fails notification-tracking-link 'through a redirect or a tracking parameter \(APP-086\)' \
  'd = rj(PC); d["notifications"][0]["links"] = ["https://licensing.example.org/status?utm_source=email"]; wj(PC, d)'
case_fails delivery-failure-without-instant 'records a failure without its instant, or an instant without a failure \(APP-087\)' \
  'd = rj(IR); del d["notifications"][4]["failedAt"]; wj(IR, d)'

# Draft migration (APP-035).
case_fails migration-drops-answer-silently 'lists other new or dropped questions than the two versions hold \(APP-035\)' \
  'd = rj(DM); d["draftEvents"][0]["droppedQuestionIds"] = ["fullName"]; wj(DM, d)'
case_fails migration-hides-changed-question 'shows other changed questions than the two versions differ on \(APP-035\)' \
  'd = rj(DM); d["draftEvents"][0]["changedQuestionIds"] = ["fullName"]; wj(DM, d)'

# Events (APP-088) and scenarios (APP-102, TST-032).
case_fails event-holds-party-id 'subjectPartyId is not allowed by the schema' \
  'd = rj(E1); d["data"]["subjectPartyId"] = "019c4e00-0010-7000-8000-000000000001"; wj(E1, d)'
case_fails event-holds-reference 'holds a party id, an account or a reference number: events hold no personal value \(APP-088\)' \
  'd = rj(E1); d["id"] = "7HQ3-MZ4K-4"; wj(E1, d)'
case_fails feature-french-differs 'same tags and steps, with the same quoted values \(TST-032\)' \
  's = open(FFR, encoding="utf-8").read().replace("\"2026-06-25\"", "\"2026-06-26\""); open(FFR, "w", encoding="utf-8").write(s)'

# Review cases: each one was accepted by the check before the fix pass.
# An adverse decision after a cancel, or after an expiry that the applicant never heard of (APP-052).
case_fails cancel-then-adverse 'decided on an adverse outcome before the deadline of cancelled request .* \(APP-052, APP-053\)' \
  'd = rj(IR); f = d["files"][0]; h = f["stateHistory"]; st = h[-2]["actor"]
h[-1] = {"state": "in-review", "at": "2026-05-26T13:00:00Z", "actor": st, "reason": "request-cancelled", "requestId": "019c5a00-0005-7000-8000-000000000001"}
h.append({"state": "decided", "at": "2026-05-27T13:00:00Z", "actor": st, "reason": "decision-recorded", "decisionRecordId": "019c5a00-000b-7000-8000-0000000000aa", "resultKind": "decided", "outcome": "refused"})
f["state"] = "decided"; d["projections"][0]["label"] = "decision-made"
q = d["requests"][0]; q["status"] = "cancelled"; q["cancelledAt"] = "2026-05-26T13:00:00Z"; q["cancelReason"] = "no-longer-needed"; del q["resolvedAt"]; del q["resolvedByVersionId"]; wj(IR, d)'
case_fails expired-unheard-then-adverse 'decided on an adverse outcome after request .*, with no delivered notice of it and no logged contact attempt \(APP-052\)' \
  'd = rj(IR); f = d["files"][1]; h = f["stateHistory"]; st = h[-1]["actor"]
h[-1] = {"state": "in-review", "at": "2026-09-16T13:00:00Z", "actor": st, "reason": "request-expired", "requestId": "019c5a00-0005-7000-8000-000000000002"}
h.append({"state": "decided", "at": "2026-09-17T13:00:00Z", "actor": st, "reason": "decision-recorded", "decisionRecordId": "019c5a00-000b-7000-8000-0000000000ab", "resultKind": "decided", "outcome": "refused"})
f["state"] = "decided"; d["projections"][1]["label"] = "decision-made"
del d["contactAttempts"]; d["notifications"] = [n for n in d["notifications"] if n["id"] != "019c5a00-0007-7000-8000-000000000009"]; wj(IR, d)'
case_fails request-never-notified 'no notice of request .* \(APP-084\)' \
  'd = rj(IR); d["notifications"] = [n for n in d["notifications"] if n["id"] != "019c5a00-0007-7000-8000-000000000005"]; wj(IR, d)'
# A decision result that is not a full grant, while a request is open (APP-032, APP-052).
case_fails insufficient-information-while-open 'while request .* is open .* \(APP-052\)' \
  'd = rj(IR); f = d["files"][0]; h = f["stateHistory"]; h[-1] = {"state": "decided", "at": "2026-06-01T13:00:00Z", "actor": h[-2]["actor"], "reason": "decision-recorded", "decisionRecordId": "019c5a00-000b-7000-8000-0000000000aa", "resultKind": "insufficient-information"}
f["state"] = "decided"; d["projections"][0]["label"] = "decision-made"; q = d["requests"][0]; q["status"] = "open"; del q["resolvedAt"]; del q["resolvedByVersionId"]; wj(IR, d)
s = ry(SQG); s["favorableWhileOpenAllowed"] = True; wy(SQG, s)'
# A federal deadline on the national days only (APP-013, APP-055).
case_fails federal-deadline-on-national-days 'missing value \(APP-013\)' \
  's = ry(SQG); s["profiles"].append("ca-federal"); wy(SQG, s)
d = rj(IR); dl = d["requests"][0]["deadline"]; dl["calendar"] = "ca-federal-national"; dl["date"] = "2026-06-24"; wj(IR, d)'
case_fails roll-leaves-calendar 'missing value \(APP-013\)' \
  'p = ry(QC); p["calendars"][0]["holidays"].append({"date": "2026-12-31", "name": {"en": "Test day", "fr": "Jour d’essai"}, "sourceId": "interpretation-act-qc"}); wy(QC, p)
d = rj(IR); dl = d["requests"][0]["deadline"]; dl["periodDays"] = 220; dl["rawDate"] = "2026-12-31"; dl["date"] = "2027-01-01"; wj(IR, d)'
# Later acts of a self-declared declarant (APP-072).
case_fails self-declared-declarant-withdraws 'a self-declared act after the submission, .* \(APP-072\)' \
  'd = rj(OB); f = d["files"][1]; h = f["stateHistory"]; h.append(dict(h[-1], state="withdrawn", at="2026-07-23T15:00:00Z", reason="applicant-withdrew")); f["state"] = "withdrawn"; d["projections"][1]["label"] = "withdrawn"; wj(OB, d)'
case_fails self-declared-declarant-gets-status-link 'links .* to the declarant .* \(APP-072\)' \
  'd = rj(OB); n = [n for n in d["notifications"] if n["id"] == "019c5a00-0007-7000-8000-00000000000c"][0]; n["links"] = ["https://benefit.example.org/status"]; wj(OB, d)'
# A paper stamp with a date only (APP-040, APP-041, APP-092).
case_fails stamp-with-date-only-and-invented-time 'start of its local day \(APP-041, APP-092\)' \
  'd = rj(PI); r = d["receiptRecords"][0]; r["receivedPrecision"] = "day"; r["receivedAt"] = "2026-04-02T17:20:00Z"; r["receivedLocal"]["localDateTime"] = "2026-04-02T13:20:00"; d["versions"][0]["submittedAt"] = r["receivedAt"]; d["projections"][0]["receivedAt"] = r["receivedAt"]; d["acknowledgments"][0]["receivedLocal"] = r["receivedLocal"]; wj(PI, d)'
case_fails digital-receipt-to-the-day 'to the second \(APP-040\)' \
  'd = rj(PC); d["receiptRecords"][0]["receivedPrecision"] = "day"; wj(PC, d)'
# The contact attempt before closing (APP-057).
case_fails closed-on-the-request-notice 'distinct from the notice of the request \(APP-057\)' \
  'd = rj(IR); n = [n for n in d["notifications"] if n["id"] == "019c5a00-0007-7000-8000-000000000008"][0]; n["deliveryStatus"] = "pending"; del n["failedAt"]
d["contactAttempts"][0]["notificationId"] = n["id"]; d["contactAttempts"][0]["at"] = n["sentAt"]; wj(IR, d)'
case_fails closed-on-unconfirmed-same-channel 'neither delivered nor on another channel .* \(APP-057, APP-087\)' \
  'd = rj(IR); n = [n for n in d["notifications"] if n["id"] == "019c5a00-0007-7000-8000-000000000009"][0]; n["channel"] = "sms"; n["deliveryStatus"] = "pending"; wj(IR, d)'
# Staff act on the authority of their role, and the service checks it on every act (APP-070).
case_fails staff-act-without-authority-check 'without a check of its authority \(APP-070\)' \
  'd = rj(IR); d["files"][0]["stateHistory"][2]["actor"].pop("authorityCheckedAt", None); wj(IR, d)'

# Accepted changes: the check does not refuse what the rules allow.
case_passes extra-delivered-notification \
  'd = rj(PC); n = dict(d["notifications"][0], id="019c5a00-0007-7000-8000-0000000000aa", kind="reminder", sentAt="2026-03-10T15:00:00Z"); d["notifications"].append(n); wj(PC, d)'
case_passes registration-notice-before-acknowledgment \
  'd = rj(PC); k = dict(d["acknowledgments"][0], id="019c5a00-0004-7000-8000-0000000000aa", kind="registration-notice")
for x in ("handlingBodyPartyId", "handlingContact", "serviceStandard", "statusUri"): k.pop(x, None)
d["acknowledgments"].insert(0, k); wj(PC, d)'

case_passes foreign-legal-person-writes-in-english \
  'import hashlib; FQ = "examples/forms/quebec-operating-permit-1.0.0.json"; f = rj(FQ); f["languages"] = ["fr", "en"]
f["title"].append({"language": "en", "text": "Operating permit application"}); f["collectionNotice"].append({"language": "en", "uri": "https://formulaires.example.org/collection-notice"})
for q in f["questions"]: q["labels"].append({"language": "en", "text": q["id"]})
wj(FQ, f); dg = hashlib.sha256(open(FQ, "rb").read()).hexdigest()
d = rj(QB); d["versions"][0]["formDigest"]["value"] = dg; d["receiptRecords"][0]["formDigest"]["value"] = dg
d["files"][0]["correspondenceLanguage"] = "en"; d["files"][0]["languageBasis"] = "charter-21-6-foreign-party"; d["acknowledgments"][0]["language"] = "en"; wj(QB, d)'

[ $fail -eq 0 ] && echo "PASS: every case"
exit $fail
