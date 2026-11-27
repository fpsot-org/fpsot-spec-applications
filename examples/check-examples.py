# SPDX-License-Identifier: Apache-2.0
"""Checks the example files of the FPSOT applications specification.

Usage: python3 -I examples/check-examples.py [ROOT]

ROOT is the repository root, by default the parent of this folder. The check reads
model/applications.yaml with its imports, profiles/, registry/events/ and examples/. It needs the
Python standard library and PyYAML only (examples/requirements.txt), and the time zone database of
the system for zoneinfo.

It runs three kinds of checks, and reports every failure with the rule it breaks.

- Schema checks: each file against its class of the LinkML model, through a small reader of the
  parts of LinkML that the model uses (inheritance, required slots, ranges, types, patterns,
  enumerations, lists and closed classes). It is not a LinkML validator. The answers of each file
  version are checked against the JSON Schema of their form, and events against the JSON Schemas of
  their types, with a small reader of the keywords that they use.
- Integrity: every digest is SHA-256 and matches the bytes it covers (the form file, the answers in
  the canonical form of RFC 8785, each attachment file); no file of the examples names MD5 or SHA-1;
  each attachment matches its declared type by its magic bytes and fits its question.
- Structural checks of the rules: profiles cite their sources and date their holidays; forms keep a
  label per language and a schema whose properties are the question ids; services name forms and
  profiles that exist and offer a route that is not digital; reference numbers carry the right
  Crockford check character; files move only along the table of APP-031, copy the result kind and
  outcome of each decision, start drafts on active versions, record the acting party apart from the
  subject, check the authority of every act of a person, allow a self-declared act only up to the
  submission, and follow the language rules of their profile and its exceptions; versions chain,
  answer a request from number 2 and record staff and keying for assisted channels; each version has
  one receipt record whose instant, precision, local time and digests match, and one
  acknowledgment; requests are notified, compute their deadline from a complete calendar of the
  profile that covers each day of the roll, are one at a time, block adverse decisions while open,
  before the deadline of a cancel and after an end that never reached the applicant, move the clocks
  as their effects say, and close a file only after an expired deadline and a logged contact attempt
  that is distinct from the notice and delivered or on another channel;
  attachments chain their versions and are clean when submitted; projections show the label that the
  state maps to, and action-needed only with an open request; notifications link only to the domains
  of the body and record failures; draft migrations carry answers by question id; events hold no
  personal value; the English and French features match.
"""
import glob
import hashlib
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import yaml

BUILTIN = {"string", "integer", "boolean", "uri", "date", "datetime", "double", "float"}
URI = re.compile(r"^(https?://|mailto:|tel:)\S+$")
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
CHECK_SYMBOLS = CROCKFORD + "*~$=U"
FINAL = {"decided", "withdrawn", "closed"}
MOVES = {None: {"draft"}, "draft": {"submitted"},
         "submitted": {"in-review", "information-requested", "decided", "withdrawn"},
         "in-review": {"information-requested", "decided", "withdrawn"},
         "information-requested": {"in-review", "decided", "withdrawn", "closed"},
         "decided": set(), "withdrawn": set(), "closed": set()}
LABEL = {"draft": "not-sent", "submitted": "received", "in-review": "in-progress",
         "information-requested": "action-needed", "decided": "decision-made", "withdrawn": "withdrawn",
         "closed": "closed"}
ASSISTED = {"assisted-digital", "counter", "telephone", "paper"}
MAGIC = {"application/pdf": b"%PDF-", "image/png": b"\x89PNG\r\n\x1a\n", "image/jpeg": b"\xff\xd8\xff"}
SEAL_PROFILES = {"seal-log", "seal-log-preserve"}
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
WEAK_DIGEST = re.compile(r"(?i)(md5|sha-?1)(?![0-9])")

failures = []


def fail(where, message, rule):
    failures.append(f"FAIL: {where}: {message} ({rule})")


def load(path):
    with open(path, encoding="utf-8") as f:
        if path.endswith((".yaml", ".yml")):
            return yaml.safe_load(f)
        return json.load(f)


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def jcs(value):
    """The canonical form of RFC 8785 for the values that the examples use: no floats."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def instant(s):
    return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


def day(s):
    return date.fromisoformat(s)


def utc(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class Model:
    """The parts of a LinkML schema that the check reads."""

    def __init__(self, path):
        self.types, self.classes, self.enums = {}, {}, {}
        self.seen = set()
        self._read(path)

    def _read(self, path):
        path = os.path.normpath(path)
        if path in self.seen:
            return
        self.seen.add(path)
        schema = load(path)
        for imp in schema.get("imports") or []:
            if not imp.startswith("linkml:"):
                # LinkML resolves an import against the folder of the schema that imports it.
                self._read(os.path.join(os.path.dirname(path), imp + ".yaml"))
        for key, store in (("types", self.types), ("classes", self.classes), ("enums", self.enums)):
            for name, spec in (schema.get(key) or {}).items():
                if name in store and store[name] != spec:
                    old, new = dict(store[name]), dict(spec)
                    old.pop("description", None)
                    new.pop("description", None)
                    # Two imports may describe the same type in their own words, as decisions and
                    # party do for LanguageTag; only a different definition is a conflict.
                    if old != new:
                        fail(path, f"{name} is defined twice, in this schema and in an import", "APP-004")
                store.setdefault(name, spec)

    def attrs(self, cls):
        chain, c = [], cls
        while c:
            chain.append(c)
            c = self.classes[c].get("is_a")
        merged = {}
        for c in reversed(chain):
            for name, slot in (self.classes[c].get("attributes") or {}).items():
                merged[name] = dict(slot or {})
        return merged

    def identifier(self, cls):
        for slot in self.attrs(cls).values():
            if slot.get("identifier"):
                return slot
        return None

    def base(self, rng):
        patterns = []
        while rng not in BUILTIN:
            t = self.types[rng]
            if t.get("pattern"):
                patterns.append(t["pattern"])
            rng = t["typeof"]
        return rng, patterns

    def check(self, obj, cls, where, rule, path="$"):
        spec = self.classes[cls]
        if spec.get("class_uri") == "linkml:Any":
            return
        if not isinstance(obj, dict):
            fail(where, f"{path} must be an object of class {cls}", rule)
            return
        attrs = self.attrs(cls)
        for key in obj:
            if key not in attrs:
                fail(where, f"{path}.{key} is not a slot of {cls}", rule)
        for name, slot in attrs.items():
            if name not in obj:
                if slot.get("required") or slot.get("identifier"):
                    fail(where, f"{path}.{name} is required in {cls}", rule)
                continue
            value = obj[name]
            if slot.get("multivalued"):
                if not isinstance(value, list) or not value:
                    fail(where, f"{path}.{name} must be a list with at least one item", rule)
                    continue
                for i, item in enumerate(value):
                    self.value(item, slot, where, rule, f"{path}.{name}[{i}]")
            else:
                self.value(value, slot, where, rule, f"{path}.{name}")

    def value(self, v, slot, where, rule, path):
        rng = slot.get("range", "string")
        if rng in self.enums:
            if v not in (self.enums[rng].get("permissible_values") or {}):
                fail(where, f"{path} has {v!r}, which is not a value of {rng}", rule)
            return
        if rng in self.classes:
            ident = self.identifier(rng)
            if slot.get("inlined") or slot.get("inlined_as_list") or ident is None:
                self.check(v, rng, where, rule, path)
            else:
                self.value(v, ident, where, rule, path)
            return
        base, patterns = self.base(rng)
        if slot.get("pattern"):
            patterns.append(slot["pattern"])
        ok = {"integer": isinstance(v, int) and not isinstance(v, bool),
              "boolean": isinstance(v, bool),
              "uri": isinstance(v, str) and bool(URI.match(v))}.get(base, isinstance(v, str))
        if not ok:
            fail(where, f"{path} has {v!r}, which is not a {rng}", rule)
            return
        for p in patterns:
            if isinstance(v, str) and not re.search(p, v):
                fail(where, f"{path} has {v!r}, which does not match the pattern of {rng}", rule)
        if "minimum_value" in slot and v < slot["minimum_value"]:
            fail(where, f"{path} is below {slot['minimum_value']}", rule)


def walk(node, path="$"):
    yield path, node
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}[{i}]")


def check_digest(where, path, digest, data, rule):
    if digest.get("algorithm") != "sha-256":
        fail(where, f"{path} uses {digest.get('algorithm')!r}: the only digest algorithm is sha-256", "APP-062")
    elif digest.get("value") != sha256_bytes(data):
        fail(where, f"{path} does not match the SHA-256 digest of the bytes it covers", rule)


def reference_ok(ref):
    m = re.fullmatch(r"([0-9A-HJKMNP-TV-Z]{4})-([0-9A-HJKMNP-TV-Z]{4})-(.)", ref or "")
    if not m:
        return False
    v = 0
    for c in m.group(1) + m.group(2):
        v = v * 32 + CROCKFORD.index(c)
    return CHECK_SYMBOLS[v % 37] == m.group(3)


def json_schema_check(value, schema, where, path, rule):
    """The keywords that the forms and the event schemas use."""
    t = schema.get("type")
    kinds = {"object": dict, "string": str, "array": list, "boolean": bool}
    if t == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            fail(where, f"{path} must be an integer", rule)
        return
    if t in kinds and not isinstance(value, kinds[t]):
        fail(where, f"{path} must be of type {t}", rule)
        return
    if "enum" in schema and value not in schema["enum"]:
        fail(where, f"{path} has {value!r}, which the schema does not allow", rule)
    if "pattern" in schema and isinstance(value, str) and not re.search(schema["pattern"], value):
        fail(where, f"{path} does not match the pattern of the schema", rule)
    if "minLength" in schema and isinstance(value, str) and len(value) < schema["minLength"]:
        fail(where, f"{path} is shorter than the schema allows", rule)
    if t == "object":
        for k in schema.get("required") or []:
            if k not in value:
                fail(where, f"{path}.{k} is required by the schema", rule)
        for k, v in value.items():
            if k in (schema.get("properties") or {}):
                json_schema_check(v, schema["properties"][k], where, f"{path}.{k}", rule)
            elif schema.get("additionalProperties") is False:
                fail(where, f"{path}.{k} is not allowed by the schema", rule)


# ---------------------------------------------------------------------------------------------
# Profiles, forms and services


def check_profiles(model, root):
    profiles = {}
    for path in sorted(glob.glob(os.path.join(root, "profiles", "*.yaml"))):
        where = os.path.relpath(path, root)
        p = load(path)
        model.check(p, "ApplicationProfile", where, "APP-010")
        profiles[p.get("code")] = p
        ids = {s.get("id") for s in p.get("sources") or []}
        if p.get("code") != "core" and not ids:
            fail(where, "a jurisdiction profile lists its sources", "APP-010")
        for s in p.get("sources") or []:
            if s.get("verification") == "read" and "web.archive.org" in (s.get("url") or "") and not s.get("date"):
                fail(where, f"source {s.get('id')} is read in an archived copy, so it states the date of the text in force", "APP-010")
        for c in p.get("calendars") or []:
            for sid in c.get("sourceIds") or []:
                if sid not in ids:
                    fail(where, f"calendar {c.get('code')} cites {sid}, which is not a source of the profile", "APP-011")
            val = c.get("validity") or {}
            seen = set()
            for h in c.get("holidays") or []:
                if h.get("sourceId") not in ids:
                    fail(where, f"holiday {h.get('date')} cites {h.get('sourceId')}, which is not a source of the profile", "APP-011")
                if not (val.get("start", "") <= h.get("date", "") < val.get("end", "9999")):
                    fail(where, f"holiday {h.get('date')} lies outside the validity of calendar {c.get('code')}", "APP-011")
                if h.get("date") in seen:
                    fail(where, f"holiday {h.get('date')} appears twice", "APP-011")
                seen.add(h.get("date"))
            if c.get("roll") == "next-working-day" and not c.get("nonWorkingWeekdays"):
                fail(where, f"calendar {c.get('code')} rolls to the next working day, so it names its non-working weekdays", "APP-055")
        for key in ("languageRules", "prefillBases"):
            for r in p.get(key) or []:
                if r.get("sourceId") not in ids:
                    fail(where, f"{key} {r.get('code')} cites {r.get('sourceId')}, which is not a source of the profile", "APP-011")
        for r in p.get("rules") or []:
            for sid in r.get("sourceIds") or []:
                if sid not in ids:
                    fail(where, f"rule {r.get('code')} cites {sid}, which is not a source of the profile", "APP-011")
    core = profiles.get("core")
    if not core or not core.get("defaults"):
        fail("profiles/core.yaml", "the core profile sets the defaults", "APP-014")
    elif core["defaults"].get("digestAlgorithm") != "sha-256":
        fail("profiles/core.yaml", "the only digest algorithm is sha-256", "APP-014, APP-062")
    return profiles


def check_forms(model, root, profiles):
    forms = {}
    for path in sorted(glob.glob(os.path.join(root, "examples", "forms", "*.json"))):
        where = os.path.relpath(path, root)
        f = load(path)
        model.check(f, "FormDefinition", where, "APP-020")
        key = f"{f.get('url')}|{f.get('version')}"
        if key in forms:
            fail(where, f"{key} names two form files", "APP-020")
        forms[key] = (f, open(path, "rb").read(), where)
        langs = set(f.get("languages") or [])
        for code in f.get("profiles") or []:
            if code not in profiles:
                fail(where, f"names profile {code}, which does not exist", "APP-010")
        if "core" not in (f.get("profiles") or []):
            fail(where, "each form follows the core profile", "APP-014")
        if {t.get("language") for t in f.get("title") or []} != langs:
            fail(where, "the title has one entry per language of the form", "APP-025")
        if {n.get("language") for n in f.get("collectionNotice") or []} != langs:
            fail(where, "the collection notice has one address per language of the form", "APP-023")
        schema = f.get("schema") or {}
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            fail(where, "the schema is a JSON Schema 2020-12 document", "APP-020")
        ids = [q.get("id") for q in f.get("questions") or []]
        if len(ids) != len(set(ids)):
            fail(where, "two questions share an id", "APP-020")
        if set(ids) != set((schema.get("properties") or {}).keys()):
            fail(where, "the properties of the schema are the question ids", "APP-020")
        required = {q.get("id") for q in f.get("questions") or [] if q.get("required")}
        if required != set(schema.get("required") or []):
            fail(where, "the schema requires exactly the questions marked required", "APP-023")
        for q in f.get("questions") or []:
            if {l.get("language") for l in q.get("labels") or []} != langs:
                fail(where, f"question {q.get('id')} has a label in each language of the form", "APP-025")
            if q.get("kind") == "answer" and ("allowedMediaTypes" in q or "maxBytes" in q):
                fail(where, f"question {q.get('id')} is an answer, so it declares no media type or size", "APP-060")
            pf = q.get("prefill")
            if pf:
                bases = {b["code"] for c in f.get("profiles") or [] for b in profiles.get(c, {}).get("prefillBases") or []}
                if pf.get("basis") not in bases:
                    fail(where, f"question {q.get('id')} fills from a basis that no profile of the form defines", "APP-024")
        if f.get("status") == "retired" and not f.get("retiredAt"):
            fail(where, "a retired version states when it was retired", "APP-021")
    return forms


def check_services(model, root, profiles, forms):
    services = {}
    core = profiles.get("core", {}).get("defaults") or {}
    for path in sorted(glob.glob(os.path.join(root, "examples", "services", "*.yaml"))):
        where = os.path.relpath(path, root)
        s = load(path)
        model.check(s, "ServiceDeclaration", where, "APP-012")
        services[s.get("code")] = s
        for code in s.get("profiles") or []:
            if code not in profiles:
                fail(where, f"names profile {code}, which does not exist", "APP-010")
        for key in s.get("forms") or []:
            if key not in forms:
                fail(where, f"names form {key}, which no form file holds", "APP-020")
        if (s.get("purgeNoticeDays") or core.get("purgeNoticeDays", 0)) < core.get("purgeNoticeDays", 0):
            fail(where, "the notice before a purge comes no later than the default of core", "APP-014, APP-034")
        channels = set(s.get("channels") or [])
        if channels <= {"digital", "email"}:
            sid = s.get("digitalOnlySourceId")
            known = {src["id"] for c in s.get("profiles") or [] for src in profiles.get(c, {}).get("sources") or []}
            if sid not in known:
                fail(where, "a service that offers only digital channels names the source of its profile that allows it", "APP-093")
        if "core" not in (s.get("profiles") or []):
            fail(where, "each service follows the core profile", "APP-014")
    return services


# ---------------------------------------------------------------------------------------------
# Calendars and deadlines


def calendar_of(profiles, code):
    for p in profiles.values():
        for c in p.get("calendars") or []:
            if c.get("code") == code:
                return p, c
    return None, None


def is_holiday(c, d):
    if WEEKDAYS[d.weekday()] in (c.get("weeklyHolidays") or []):
        return True
    return d.isoformat() in {h["date"] for h in c.get("holidays") or []}


def roll(c, d):
    """The date after the roll, and every day that the roll visits, the first included."""
    visited = []
    while True:
        visited.append(d)
        off = is_holiday(c, d)
        if c.get("roll") == "next-working-day" and WEEKDAYS[d.weekday()] in (c.get("nonWorkingWeekdays") or []):
            off = True
        if not off:
            return d, visited
        d += timedelta(days=1)


def covered(c, d):
    v = c.get("validity") or {}
    return v.get("start", "") <= d.isoformat() < v.get("end", "9999")


def end_of_day(d, tz):
    """The instant, in UTC, at which local day d ends in the time zone tz."""
    return datetime.combine(d + timedelta(days=1), datetime.min.time(), tzinfo=ZoneInfo(tz)).astimezone(timezone.utc)


def adverse(h, svc):
    """A move to decided is adverse unless its result kind is decided with a full grant (APP-032)."""
    return not (h.get("resultKind") == "decided" and h.get("outcome") in (svc.get("fullGrantOutcomes") or []))


# ---------------------------------------------------------------------------------------------
# Application files


def check_examples(model, root, profiles, forms, services):
    data = {"files": {}, "versions": {}, "receiptRecords": {}, "acknowledgments": {}, "requests": {},
            "attachments": {}, "notifications": {}, "contactAttempts": {}, "outages": {}, "draftEvents": {},
            "projections": {}}
    parties = set()
    for path in sorted(glob.glob(os.path.join(root, "examples", "*", "application.json"))):
        folder = os.path.dirname(path)
        where = os.path.relpath(path, root)
        doc = load(path)
        model.check(doc, "ApplicationsContainer", where, "APP-006")
        for p_, node in walk(doc):
            if isinstance(node, str) and WEAK_DIGEST.search(node):
                fail(where, f"{p_} names a weak digest: MD5 and SHA-1 are not used at all", "APP-062")
            if isinstance(node, dict):
                for k in node:
                    if WEAK_DIGEST.search(k):
                        fail(where, f"{p_}.{k} names a weak digest: MD5 and SHA-1 are not used at all", "APP-062")
        for key in data:
            for x in doc.get(key) or []:
                xid = x.get("id") or x.get("fileId")
                if xid in data[key]:
                    fail(where, f"{key} {xid} appears twice", "DMO-021")
                data[key][xid] = (x, where, folder)
    D = data

    def get(kind, xid):
        return D[kind].get(xid, (None, None, None))[0]

    # Attachments (APP-060 to APP-064)
    core = profiles.get("core", {}).get("defaults") or {}
    for aid, (a, where, folder) in D["attachments"].items():
        f = get("files", a.get("fileId"))
        if f is None:
            fail(where, f"attachment {aid} names a file that the examples do not hold", "APP-064")
            continue
        p = a.get("path")
        if p:
            full = os.path.join(folder, p)
            if not os.path.exists(full):
                fail(where, f"attachment {aid} points to {p}, which does not exist", "APP-064")
            else:
                b = open(full, "rb").read()
                check_digest(where, f"attachment {aid}", a.get("digest") or {}, b, "APP-062")
                if len(b) != a.get("byteSize"):
                    fail(where, f"attachment {aid} declares {a.get('byteSize')} bytes, but the file has {len(b)}", "APP-060")
                magic = MAGIC.get(a.get("detectedMediaType"))
                if magic is None or not b.startswith(magic):
                    fail(where, f"attachment {aid} is not a {a.get('detectedMediaType')} by its content", "APP-061")
        if a.get("scanState") != "pending" and not a.get("scannedAt"):
            fail(where, f"attachment {aid} has a scan state but no scan instant", "APP-063")
        prev = a.get("previousAttachmentId")
        if a.get("version", 1) > 1:
            pa = get("attachments", prev)
            if pa is None:
                fail(where, f"attachment {aid} is version {a.get('version')} and names no previous version", "APP-064")
            elif pa.get("questionId") != a.get("questionId") or pa.get("fileId") != a.get("fileId") or pa.get("version") != a.get("version") - 1:
                fail(where, f"attachment {aid} follows a version of another question, file or number", "APP-064")
        elif prev:
            fail(where, f"attachment {aid} is version 1 and names a previous version", "APP-064")

    # Files
    for fid, (f, where, folder) in D["files"].items():
        svc = services.get(f.get("service"))
        if svc is None:
            fail(where, f"file {fid} names service {f.get('service')}, which does not exist", "APP-012")
            continue
        fkey = f"{f.get('formUrl')}|{f.get('formVersion')}"
        if fkey not in forms:
            fail(where, f"file {fid} names form {fkey}, which no form file holds", "APP-033")
            continue
        form = forms[fkey][0]
        profs = [profiles[c] for c in svc.get("profiles") or [] if c in profiles]
        if f.get("reference") and not reference_ok(f["reference"]):
            fail(where, f"file {fid} has reference {f['reference']}, whose check character does not match", "APP-045, APP-046")
        hist = f.get("stateHistory") or []
        prev_state, prev_at, seen_submitted = None, None, False
        for i, h in enumerate(hist):
            if prev_state in FINAL:
                fail(where, f"file {fid} moves after the final state {prev_state}", "APP-030")
            if h.get("state") not in MOVES.get(prev_state, set()):
                fail(where, f"file {fid} moves from {prev_state} to {h.get('state')}, which APP-031 does not allow", "APP-031")
            if prev_at and h.get("at", "") < prev_at:
                fail(where, f"file {fid}: entry {i} of the history comes before the entry before it", "APP-031")
            prev_state, prev_at = h.get("state"), h.get("at")
            check_actor(where, f"file {fid} entry {i}", h.get("actor") or {}, f, svc, later=seen_submitted)
            if h.get("state") == "submitted":
                seen_submitted = True
            if h.get("state") == "decided":
                if not h.get("decisionRecordId") or not h.get("resultKind"):
                    fail(where, f"file {fid} moves to decided without its decision record and its result kind", "APP-032")
                elif h["resultKind"] == "referred":
                    fail(where, f"file {fid} moves to decided on a referred result, which is not a decision", "APP-032, DEC-024")
                elif h["resultKind"] == "decided" and not h.get("outcome"):
                    fail(where, f"file {fid} moves to decided without the outcome of its decision record", "APP-032, DEC-024")
            if h.get("state") == "information-requested" and get("requests", h.get("requestId")) is None:
                fail(where, f"file {fid} moves to information-requested without a request of the examples", "APP-051")
        if hist and hist[-1].get("state") != f.get("state"):
            fail(where, f"file {fid} is {f.get('state')}, but its history ends at {hist[-1].get('state')}", "APP-031")
        start = f.get("draftStartedAt", "")
        if form.get("retiredAt") and start >= form["retiredAt"]:
            fail(where, f"file {fid} starts a draft on {fkey} after it was retired", "APP-021")
        # Languages (APP-025)
        if f.get("correspondenceLanguage") not in (form.get("languages") or []):
            fail(where, f"file {fid} corresponds in {f.get('correspondenceLanguage')}, which its form does not offer", "APP-025")
        rules = [r for p in profs for r in p.get("languageRules") or []]
        basis = [r for r in rules if r.get("code") == f.get("languageBasis")]
        if not basis or basis[0].get("language") != f.get("correspondenceLanguage"):
            fail(where, f"file {fid} records a language basis that no profile gives for its language", "APP-025")
        for r in rules:
            if basis and basis[0].get("exceptionTo") == r.get("code"):
                continue
            if r.get("exclusive") and r.get("appliesTo") == svc.get("applicationKind"):
                if form.get("languages") != [r["language"]] or f.get("correspondenceLanguage") != r["language"] or f.get("languageBasis") != r["code"]:
                    fail(where, f"file {fid}: rule {r['code']} of the profile asks for {r['language']} only in this kind of application", "APP-025")
        if f.get("assurance") == "self-declared" and not svc.get("selfDeclaredSubmissions"):
            fail(where, f"file {fid} is self-declared, which its service does not allow", "APP-072")
        # Clocks (APP-054)
        clock_codes = {c["code"] for c in svc.get("clocks") or []}
        for c in f.get("clocks") or []:
            if c.get("code") not in clock_codes:
                fail(where, f"file {fid} has clock {c.get('code')}, which its service does not declare", "APP-054")
        for h in f.get("handoffs") or []:
            if not UUID.match(h.get("id", "")):
                fail(where, f"file {fid} hands off {h.get('kind')} with an id that is not a UUID", "APP-101")
        fvs = sorted([v for v, _, _ in D["versions"].values() if v.get("fileId") == fid], key=lambda v: v.get("number", 0))
        submitted = any(h.get("state") == "submitted" for h in hist)
        if submitted and not fvs:
            fail(where, f"file {fid} is submitted but has no file version", "APP-036")
        if submitted and not f.get("reference"):
            fail(where, f"file {fid} is submitted but has no reference number", "APP-045")
        if fvs and (fvs[-1].get("formUrl"), fvs[-1].get("formVersion")) != (f.get("formUrl"), f.get("formVersion")):
            fail(where, f"file {fid} names a form version that its last file version did not answer", "APP-037")
        check_requests(where, f, svc, profiles, forms, D, get)
        check_closing(where, f, svc, D, get)

    # File versions and receipt records (APP-036 to APP-041, APP-091, APP-092)
    for vid, (v, where, folder) in D["versions"].items():
        f = get("files", v.get("fileId"))
        if f is None:
            fail(where, f"version {vid} names a file that the examples do not hold", "APP-037")
            continue
        svc = services.get(f.get("service"), {})
        fkey = f"{v.get('formUrl')}|{v.get('formVersion')}"
        if fkey not in forms:
            fail(where, f"version {vid} answers {fkey}, which no form file holds", "APP-036")
            continue
        form, raw, _ = forms[fkey]
        check_digest(where, f"version {vid} formDigest", v.get("formDigest") or {}, raw, "APP-036")
        check_digest(where, f"version {vid} answersDigest", v.get("answersDigest") or {}, jcs(v.get("answers")), "APP-040")
        json_schema_check(v.get("answers"), form.get("schema") or {}, where, f"version {vid} answers", "APP-036, APP-037")
        check_actor(where, f"version {vid}", v.get("submittedBy") or {}, f, svc, later=(v.get("number") or 1) > 1)
        n = v.get("number")
        if n and n > 1:
            pv = get("versions", v.get("previousVersionId"))
            if pv is None or pv.get("number") != n - 1 or pv.get("fileId") != v.get("fileId"):
                fail(where, f"version {vid} is number {n} and does not name version {n - 1} of its file", "APP-037")
            if get("requests", v.get("requestId")) is None:
                fail(where, f"version {vid} is number {n} and names no request that it answers", "APP-053")
            if pv:
                old = set(pv.get("attachmentIds") or [])
                for aid in v.get("attachmentIds") or []:
                    a = get("attachments", aid)
                    if a and aid not in old and a.get("version", 1) == 1:
                        same_q = [get("attachments", o) for o in old]
                        if any(x and x.get("questionId") == a.get("questionId") for x in same_q):
                            fail(where, f"version {vid} replaces an attachment without a new attachment version", "APP-064")
        elif v.get("previousVersionId") or v.get("requestId"):
            fail(where, f"version {vid} is number 1 and names a previous version or a request", "APP-037")
        qkinds = {q["id"]: q for q in form.get("questions") or []}
        for aid in v.get("attachmentIds") or []:
            a = get("attachments", aid)
            if a is None or a.get("fileId") != v.get("fileId"):
                fail(where, f"version {vid} holds attachment {aid}, which is not an attachment of its file", "APP-064")
                continue
            if a.get("scanState") != "clean":
                fail(where, f"version {vid} holds attachment {aid}, whose scan state is {a.get('scanState')}", "APP-036, APP-063")
            q = qkinds.get(a.get("questionId"))
            if q is None or q.get("kind") != "attachment":
                fail(where, f"attachment {aid} answers {a.get('questionId')}, which is not an attachment question of the form", "APP-060")
                continue
            types = q.get("allowedMediaTypes") or core.get("allowedMediaTypes") or []
            limit = q.get("maxBytes") or core.get("maxAttachmentBytes") or 0
            if a.get("detectedMediaType") not in types:
                fail(where, f"attachment {aid} is {a.get('detectedMediaType')}, which question {q['id']} does not accept", "APP-060")
            if a.get("byteSize", 0) > limit:
                fail(where, f"attachment {aid} is larger than question {q['id']} accepts", "APP-060")
            if a.get("receivedAt", "") > v.get("submittedAt", "") and v.get("channel") not in ASSISTED:
                fail(where, f"attachment {aid} arrived after the submission that holds it", "APP-066")
        for qid, val in (v.get("answers") or {}).items():
            q = qkinds.get(qid)
            if q and q.get("kind") == "attachment" and val not in (v.get("attachmentIds") or []):
                fail(where, f"version {vid} answers {qid} with an attachment that it does not hold", "APP-064")
        ch = v.get("channel")
        if ch in ASSISTED:
            if not v.get("capturedBy"):
                fail(where, f"version {vid} came by {ch}, so it records in capturedBy who keyed it in", "APP-091")
            elif (v.get("submittedBy") or {}).get("role") != "staff" or (v.get("submittedBy") or {}).get("actorId") != v.get("capturedBy"):
                fail(where, f"version {vid}: the staff member who keyed it in is the actor, with the role staff", "APP-071, APP-091")
        if ch in {"paper", "counter"}:
            if not v.get("keyedAt"):
                fail(where, f"version {vid} came by {ch}, so it records keyedAt", "APP-092")
            elif v["keyedAt"] < v.get("submittedAt", ""):
                fail(where, f"version {vid} was keyed in before it arrived", "APP-092")
        recs = [r for r, _, _ in D["receiptRecords"].values() if r.get("fileVersionId") == vid]
        if len(recs) != 1:
            fail(where, f"version {vid} has {len(recs)} receipt records, and each submission creates one", "APP-040")
            continue
        r = recs[0]
        check_receipt(where, r, v, f, svc, profiles, D, get)

    # Requests and closed files are checked with their files. Projections and notifications:
    for fid, (pj, where, _) in D["projections"].items():
        f = get("files", fid)
        if f is None:
            fail(where, f"projection of {fid} names a file that the examples do not hold", "APP-080")
            continue
        if pj.get("label") != LABEL.get(f.get("state")):
            fail(where, f"file {fid} is {f.get('state')}, so its label is {LABEL.get(f.get('state'))}, not {pj.get('label')}", "APP-080")
        open_reqs = [q for q, _, _ in D["requests"].values() if q.get("fileId") == fid and q.get("status") == "open"]
        if pj.get("label") == "action-needed":
            an = pj.get("actionNeeded") or {}
            if not open_reqs or an.get("requestId") != open_reqs[0]["id"]:
                fail(where, f"file {fid} shows action-needed without its open request", "APP-081")
            elif sorted(an.get("items") or []) != sorted(i["questionId"] for i in open_reqs[0].get("items") or []) or an.get("deadline") != open_reqs[0]["deadline"]["date"]:
                fail(where, f"file {fid} shows other items or another deadline than its open request", "APP-081")
        elif pj.get("actionNeeded"):
            fail(where, f"file {fid} shows what to do while its label is {pj.get('label')}", "APP-081")
        if f.get("state") != "draft":
            for k in ("reference", "receivedAt", "handlingBodyPartyId"):
                if not pj.get(k):
                    fail(where, f"projection of {fid} lacks {k}", "APP-082")
            if not pj.get("expectedDecisionDate") and not pj.get("serviceStandard"):
                fail(where, f"projection of {fid} shows neither an expected date nor a service standard", "APP-082")
            first = min((v.get("submittedAt") for v, _, _ in D["versions"].values() if v.get("fileId") == fid), default=None)
            if pj.get("reference") != f.get("reference") or pj.get("receivedAt") != first:
                fail(where, f"projection of {fid} drifts from the file of record", "APP-083")
    for fid, (f, where, _) in D["files"].items():
        if f.get("state") != "draft" and fid not in D["projections"]:
            fail(where, f"file {fid} has no status projection", "APP-080")
    for nid, (n, where, _) in D["notifications"].items():
        f = get("files", n.get("fileId"))
        svc = services.get((f or {}).get("service"), {})
        for link in n.get("links") or []:
            m = re.match(r"^https://([^/?#]+)([^?#]*)(\?[^#]*)?", link)
            if not m or m.group(1) not in (svc.get("domains") or []):
                fail(where, f"notification {nid} links to {link}, which is not a domain of the body, in full, over HTTPS", "APP-086")
            elif m.group(3) or re.search(r"(?i)redirect|/r/|track|utm_", link):
                fail(where, f"notification {nid} links through a redirect or a tracking parameter", "APP-086")
        if (n.get("deliveryStatus") == "failed") != bool(n.get("failedAt")):
            fail(where, f"notification {nid} records a failure without its instant, or an instant without a failure", "APP-087")
    for rid, (r, where, _) in D["receiptRecords"].items():
        if not any(n.get("fileId") == r.get("fileId") and n.get("kind") == "receipt" and n.get("sentAt", "") >= r.get("receivedAt", "")
                   for n, _, _ in D["notifications"].values()):
            fail(where, f"receipt record {rid} has no notification of receipt", "APP-084")
    for fid, (f, where, _) in D["files"].items():
        acts = [h.get("actor") or {} for h in f.get("stateHistory") or []]
        if any(a.get("role") == "representative" for a in acts if a.get("subjectPartyId") == f.get("subjectPartyId")):
            if not any(n.get("fileId") == fid and n.get("recipientRole") == "represented-party" for n, _, _ in D["notifications"].values()):
                fail(where, f"file {fid} was submitted for another party, who received no notice", "APP-073")
    for nid, (n, where, _) in D["notifications"].items():
        f = get("files", n.get("fileId")) or {}
        if f.get("assurance") == "self-declared" and n.get("recipientRole") == "representative" and n.get("links"):
            fail(where, f"notification {nid} links the file to the declarant of a self-declared submission", "APP-072")
    # The other acts: uploads, requests and draft events (APP-070 to APP-072).
    for kind, key, when in (("attachments", "uploadedBy", "receivedAt"), ("requests", "openedBy", "openedAt"), ("draftEvents", "actor", "at")):
        for xid, (x, where, _) in D[kind].items():
            f = get("files", x.get("fileId"))
            if f is None:
                continue
            first = min((h.get("at", "") for h in f.get("stateHistory") or [] if h.get("state") == "submitted"), default=None)
            check_actor(where, f"{kind} {xid}", x.get(key) or {}, f, services.get(f.get("service"), {}),
                        later=bool(first) and x.get(when, "") > first)
    check_draft_events(D, get, forms)
    return D


def check_actor(where, label, a, f, svc, later=False):
    """later: the act comes after the submission, so it cannot be self-declared (APP-072)."""
    if a.get("subjectPartyId") != f.get("subjectPartyId"):
        fail(where, f"{label}: the subject of the act is not the party of the file", "APP-071")
    role = a.get("role")
    if role != "service" and not a.get("actingPartyId"):
        fail(where, f"{label}: the act names no acting party", "APP-071")
    if role in {"applicant", "representative", "staff"} and not a.get("authorityCheckedAt"):
        fail(where, f"{label}: an act of the role {role} without a check of its authority", "APP-070")
    if role == "representative" and a.get("assurance") != "self-declared" and not a.get("representationId"):
        fail(where, f"{label}: a representative acts on a representation that the service checked", "APP-070")
    if role == "representative" and a.get("assurance") == "self-declared" and not svc.get("selfDeclaredSubmissions"):
        fail(where, f"{label}: a self-declared act, which the service does not allow", "APP-072")
    if role == "applicant" and a.get("actingPartyId") != f.get("subjectPartyId"):
        fail(where, f"{label}: an applicant acts for their own file only", "APP-071")
    if later:
        if a.get("assurance") == "self-declared":
            fail(where, f"{label}: a self-declared act after the submission, which needs the subject or a representation", "APP-072")
    elif a.get("assurance") != f.get("assurance") and role in {"applicant", "representative"}:
        fail(where, f"{label}: the assurance of the submission differs from that of the file", "APP-072")


def check_receipt(where, r, v, f, svc, profiles, D, get):
    rid = r.get("id")
    if r.get("receivedAt") != v.get("submittedAt"):
        fail(where, f"receipt record {rid} has another received instant than its version", "APP-041")
    if r.get("reference") != f.get("reference") or r.get("fileId") != f.get("id"):
        fail(where, f"receipt record {rid} names another file or reference", "APP-040")
    if r.get("channel") != v.get("channel") or r.get("submitter") != v.get("submittedBy"):
        fail(where, f"receipt record {rid} records another channel or submitter than its version", "APP-040")
    if r.get("formDigest") != v.get("formDigest") or r.get("answersDigest") != v.get("answersDigest"):
        fail(where, f"receipt record {rid} records other digests than its version", "APP-040")
    expected = sorted((aid, (get("attachments", aid) or {}).get("digest", {}).get("value")) for aid in v.get("attachmentIds") or [])
    got = sorted((x.get("attachmentId"), (x.get("digest") or {}).get("value")) for x in r.get("attachmentDigests") or [])
    if expected != got:
        fail(where, f"receipt record {rid} does not hold the digest of each attachment of its version", "APP-040")
    if r.get("assurance") != (v.get("submittedBy") or {}).get("assurance"):
        fail(where, f"receipt record {rid} does not record the assurance of the submission", "APP-072")
    if r.get("sealProfile") not in SEAL_PROFILES:
        fail(where, f"receipt record {rid} is sealed under {r.get('sealProfile')}, below seal-log", "APP-042")
    tzs = {c["timeZone"] for c in svc.get("profiles") or [] for c in profiles.get(c, {}).get("calendars") or []}
    loc = r.get("receivedLocal") or {}
    prec = r.get("receivedPrecision")
    if prec != "second" and r.get("channel") not in {"paper", "counter"}:
        fail(where, f"receipt record {rid} came by {r.get('channel')}, so it holds its instant to the second", "APP-040")
    elif prec == "day" and not (loc.get("localDateTime") or "").endswith("T00:00:00"):
        fail(where, f"receipt record {rid} holds a date only, so it records the start of its local day", "APP-041, APP-092")
    elif prec == "minute" and not (loc.get("localDateTime") or "").endswith(":00"):
        fail(where, f"receipt record {rid} holds a minute, so it records the start of that minute", "APP-041, APP-092")
    if loc.get("timeZone") not in tzs:
        fail(where, f"receipt record {rid} uses a time zone that is not the legal time zone of its profile", "APP-040, APP-012")
    else:
        dt = instant(r["receivedAt"]).astimezone(ZoneInfo(loc["timeZone"]))
        if dt.strftime("%Y-%m-%dT%H:%M:%S") != loc.get("localDateTime"):
            fail(where, f"receipt record {rid}: the local time does not match the received instant in {loc['timeZone']}", "APP-040")
    acks = [a for a, _, _ in D["acknowledgments"].values() if a.get("receiptRecordId") == rid]
    full = [a for a in acks if a.get("kind") == "acknowledgment"]
    if len(full) != 1:
        fail(where, f"receipt record {rid} has {len(full)} acknowledgments, and each submission gets one", "APP-043")
    for a in acks:
        if a.get("receivedLocal") != loc or a.get("reference") != r.get("reference"):
            fail(where, f"acknowledgment {a.get('id')} shows another reference or received time than its receipt record", "APP-043")
        if a.get("language") != f.get("correspondenceLanguage"):
            fail(where, f"acknowledgment {a.get('id')} is not in the language of the file", "APP-043")
        if a.get("kind") == "acknowledgment":
            for k in ("handlingBodyPartyId", "handlingContact", "statusUri"):
                if not a.get(k):
                    fail(where, f"acknowledgment {a.get('id')} lacks {k}", "APP-043")
            if not a.get("expectedDecisionDate") and not a.get("serviceStandard"):
                fail(where, f"acknowledgment {a.get('id')} gives neither an expected date nor a service standard", "APP-043")
        if a.get("sentAt", "") < r.get("receivedAt", ""):
            fail(where, f"acknowledgment {a.get('id')} was sent before the receipt", "APP-043")
    notices = [a for a in acks if a.get("kind") == "registration-notice"]
    if full and notices and notices[0].get("sentAt", "") > full[0].get("sentAt", ""):
        fail(where, f"receipt record {rid}: the notice of registration comes after the acknowledgment", "APP-044")


def check_requests(where, f, svc, profiles, forms, D, get):
    fid = f.get("id")
    reqs = sorted([q for q, _, _ in D["requests"].values() if q.get("fileId") == fid], key=lambda q: q.get("openedAt", ""))
    if len([q for q in reqs if q.get("status") == "open"]) > 1:
        fail(where, f"file {fid} has more than one open request", "APP-051")
    for i, q in enumerate(reqs[1:], 1):
        before = reqs[i - 1]
        end = before.get("resolvedAt") or before.get("cancelledAt") or before.get("expiredAt")
        if not end or end > q.get("openedAt", ""):
            fail(where, f"file {fid}: request {q.get('id')} opens while request {before.get('id')} is still open", "APP-051")
    clocks = {c.get("code"): c.get("changes") or [] for c in f.get("clocks") or []}
    declared = {c["code"] for c in svc.get("clocks") or []}
    for q in reqs:
        qid = q.get("id")
        status = q.get("status")
        need = {"resolved": ("resolvedAt", "resolvedByVersionId"), "cancelled": ("cancelledAt", "cancelReason"), "expired": ("expiredAt",)}
        for k in need.get(status, ()):
            if not q.get(k):
                fail(where, f"request {qid} is {status} without {k}", "APP-051, APP-053")
        for k in ("resolvedAt", "cancelledAt", "expiredAt"):
            if q.get(k) and k[:-2] != status:
                fail(where, f"request {qid} is {status} and records {k}", "APP-051")
        if {e.get("clock") for e in q.get("clockEffects") or []} != declared:
            fail(where, f"request {qid} does not state its effect on each clock of the program", "APP-050, APP-054")
        v = get("versions", q.get("fileVersionId"))
        if v is None or v.get("fileId") != fid:
            fail(where, f"request {qid} concerns a version that is not a version of its file", "APP-050")
        for it in q.get("items") or []:
            if it.get("attachmentId") and get("attachments", it["attachmentId"]) is None:
                fail(where, f"request {qid} names an attachment that the examples do not hold", "APP-050")
            fkey = f"{(v or {}).get('formUrl')}|{(v or {}).get('formVersion')}"
            qids = {x["id"] for x in (forms.get(fkey, ({},))[0].get("questions") or [])}
            if it.get("questionId") not in qids:
                fail(where, f"request {qid} names question {it.get('questionId')}, which the form of its version does not hold", "APP-050")
        if status == "resolved":
            rv = get("versions", q.get("resolvedByVersionId"))
            if rv is None or rv.get("requestId") != qid or rv.get("submittedAt") != q.get("resolvedAt"):
                fail(where, f"request {qid} is resolved by a version that does not answer it at that instant", "APP-053")
        # Deadline (APP-055, APP-056, APP-013)
        deadline_end = None
        dl = q.get("deadline") or {}
        prof, cal = calendar_of(profiles, dl.get("calendar"))
        if cal is None or prof.get("code") not in (svc.get("profiles") or []):
            fail(where, f"request {qid} uses calendar {dl.get('calendar')}, which no profile of its service holds", "APP-055")
        else:
            if dl.get("calendarVersion") != prof.get("version"):
                fail(where, f"request {qid} names version {dl.get('calendarVersion')} of a profile at version {prof.get('version')}", "APP-055")
            start = instant(q["openedAt"]).astimezone(ZoneInfo(cal["timeZone"])).date()
            if dl.get("startDate") != start.isoformat():
                fail(where, f"request {qid} starts on {dl.get('startDate')}, but it opened on {start} in {cal['timeZone']}", "APP-055")
            raw = start + timedelta(days=dl.get("periodDays", 0))
            if dl.get("rawDate") != raw.isoformat():
                fail(where, f"request {qid}: the raw date must be {raw}", "APP-055")
            if not cal.get("complete"):
                fail(where, f"request {qid}: calendar {cal['code']} lacks days that its law counts for some places, so the deadline is a missing value", "APP-013")
            target = raw
            ext = dl.get("extension")
            if ext:
                o = get("outages", ext.get("outageId"))
                rule = svc.get("extensionRule") or {}
                if o is None or ext.get("rule") != rule.get("code"):
                    fail(where, f"request {qid} applies an extension without its outage or without the rule of its service", "APP-056")
                else:
                    tz = ZoneInfo(cal["timeZone"])
                    o_start = instant(o["start"]).astimezone(tz).date()
                    o_end = instant(o["end"]).astimezone(tz).date()
                    if not (o_start <= raw <= o_end):
                        fail(where, f"request {qid}: the deadline {raw} does not fall in outage {o['id']}", "APP-056")
                    if o.get("publishedAt", "") > o.get("end", ""):
                        fail(where, f"outage {o['id']} was published after it ended", "APP-056")
                    target = o_end + timedelta(days=rule.get("extendByDaysAfterOutageEnd", 0))
            expected, visited = roll(cal, target)
            for vd in [raw] + visited:
                if not covered(cal, vd):
                    fail(where, f"request {qid}: calendar {cal['code']} does not cover {vd}, a missing value", "APP-013")
                    break
            if dl.get("date") != expected.isoformat():
                fail(where, f"request {qid}: the deadline after the roll must be {expected}", "APP-055")
            if status == "expired" and instant(q["expiredAt"]) < end_of_day(day(dl["date"]), cal["timeZone"]):
                fail(where, f"request {qid} expired before the end of its deadline", "APP-057")
            deadline_end = end_of_day(day(dl["date"]), cal["timeZone"])
        # The notice of the request (APP-084), and no adverse decision that the applicant could not
        # answer (APP-052): not while the request is open and in time, not before the deadline of a
        # cancelled request ends, and after an expiry or a cancel only once the applicant was reached.
        notices = [n for n, _, _ in D["notifications"].values() if n.get("requestId") == qid and n.get("kind") == "action-needed"]
        if not any(n.get("fileId") == fid and n.get("sentAt", "") >= q.get("openedAt", "") for n in notices):
            fail(where, f"request {qid} has no notice of request sent to the applicant", "APP-084")
        attempts = [c for c, _, _ in D["contactAttempts"].values() if c.get("requestId") == qid]
        if status == "cancelled":
            end = max(q.get("cancelledAt", ""), utc(deadline_end)) if deadline_end else q.get("cancelledAt")
        else:
            end = q.get("resolvedAt") or q.get("expiredAt")
        for h in f.get("stateHistory") or []:
            at = h.get("at", "")
            if h.get("state") != "decided" or at < q.get("openedAt", ""):
                continue
            in_window = not end or at < end
            after_cancel = status == "cancelled" and at >= q.get("cancelledAt", "")
            heard = any(n.get("deliveryStatus") == "delivered" for n in notices) or any(
                not contact_problems(c, q, D, get, until=at) for c in attempts)
            if adverse(h, svc):
                if in_window and after_cancel:
                    fail(where, f"file {fid} is decided on an adverse outcome before the deadline of cancelled request {qid} ended", "APP-052, APP-053")
                elif in_window:
                    fail(where, f"file {fid} is decided on an adverse outcome while request {qid} is open and in time", "APP-052")
                elif status in {"expired", "cancelled"} and not heard:
                    fail(where, f"file {fid} is decided on an adverse outcome after request {qid}, with no delivered notice of it and no logged contact attempt", "APP-052")
            elif in_window and not after_cancel and not svc.get("favorableWhileOpenAllowed"):
                fail(where, f"file {fid} is decided while request {qid} is open, which its program does not allow", "APP-052")
        # Clock effects (APP-054)
        for e in q.get("clockEffects") or []:
            changes = clocks.get(e.get("clock"), [])
            if e.get("effect") == "suspend":
                if not any(c.get("change") == "suspended" and c.get("at") == q.get("openedAt") and c.get("requestId") == qid for c in changes):
                    fail(where, f"request {qid} suspends clock {e.get('clock')}, which records no suspension when it opened", "APP-054")
                if q.get("resolvedAt") and not any(c.get("change") == "resumed" and c.get("at") == q["resolvedAt"] for c in changes):
                    fail(where, f"request {qid} suspends clock {e.get('clock')}, which does not resume when the request is resolved", "APP-054")
            elif e.get("effect") == "start-on-completion":
                if q.get("resolvedAt") and not any(c.get("change") == "started" and c.get("at") == q["resolvedAt"] for c in changes):
                    fail(where, f"request {qid} starts clock {e.get('clock')} on completion, which does not start when the request is resolved", "APP-054")
                if any(c.get("change") == "started" and c.get("at", "") < q.get("openedAt", "") for c in changes):
                    fail(where, f"clock {e.get('clock')} starts on completion, but it started before request {qid}", "APP-054")


def contact_problems(ca, q, D, get, until=None):
    """Why a contact attempt does not count under APP-057: none, if the list is empty."""
    if ca is None or ca.get("requestId") != q.get("id") or ca.get("at", "") < q.get("openedAt", "") or (until and ca.get("at", "") > until):
        return [("without a logged contact attempt after the request opened", "APP-057")]
    n = get("notifications", ca.get("notificationId"))
    if n is None:
        return [("on a contact attempt without its notification", "APP-057, APP-087")]
    notices = [x for x, _, _ in D["notifications"].values() if x.get("requestId") == q.get("id") and x.get("kind") == "action-needed"]
    problems = []
    if any(n is x for x in notices):
        problems.append(("on a contact attempt that is not distinct from the notice of the request", "APP-057"))
    if n.get("deliveryStatus") == "failed":
        problems.append(("on a contact attempt through a channel that failed", "APP-057, APP-087"))
    elif n.get("deliveryStatus") != "delivered" and n.get("channel") in {x.get("channel") for x in notices if x is not n}:
        problems.append(("on a contact attempt that is neither delivered nor on another channel than the notice of the request", "APP-057, APP-087"))
    return problems


def check_closing(where, f, svc, D, get):
    fid = f.get("id")
    for h in f.get("stateHistory") or []:
        if h.get("state") != "closed":
            continue
        if not svc.get("closingForNoResponse"):
            fail(where, f"file {fid} is closed for no response, which its program does not allow", "APP-057")
        q = get("requests", h.get("requestId"))
        if q is None or q.get("status") != "expired" or q.get("expiredAt", "") > h.get("at", ""):
            fail(where, f"file {fid} is closed without a request that expired before", "APP-057")
            continue
        for message, rule in contact_problems(get("contactAttempts", h.get("contactAttemptId")), q, D, get, until=h.get("at", "")):
            fail(where, f"file {fid} is closed {message}", rule)


def check_draft_events(D, get, forms):
    for eid, (e, where, _) in D["draftEvents"].items():
        f = get("files", e.get("fileId"))
        if e.get("kind") != "migrated":
            continue
        if f is None:
            fail(where, f"draft event {eid} names a file that the examples do not hold", "APP-035")
            continue
        src = forms.get(f"{f.get('formUrl')}|{e.get('fromFormVersion')}", (None,))[0]
        dst = forms.get(f"{f.get('formUrl')}|{e.get('toFormVersion')}", (None,))[0]
        if src is None or dst is None:
            fail(where, f"draft event {eid} moves between versions that no form file holds", "APP-035")
            continue
        if dst.get("status") != "active" or (dst.get("publishedAt") or "") > e.get("at", ""):
            fail(where, f"draft event {eid} moves the draft to a version that was not active", "APP-035")
        a = {q["id"]: q for q in src.get("questions") or []}
        b = {q["id"]: q for q in dst.get("questions") or []}
        carried, changed = set(e.get("carriedQuestionIds") or []), set(e.get("changedQuestionIds") or [])
        new, dropped = set(e.get("newQuestionIds") or []), set(e.get("droppedQuestionIds") or [])
        if new != set(b) - set(a) or dropped != set(a) - set(b):
            fail(where, f"draft event {eid} lists other new or dropped questions than the two versions hold", "APP-035")
        if not carried <= set(a) & set(b):
            fail(where, f"draft event {eid} carries an answer to a question that one of the versions lacks", "APP-035")
        diff = {k for k in set(a) & set(b) if a[k] != b[k]}
        if changed != diff:
            fail(where, f"draft event {eid} shows other changed questions than the two versions differ on", "APP-035")
        if not e.get("shownToApplicantAt"):
            fail(where, f"draft event {eid} does not record when the front end showed the changes", "APP-035")
        fvs = [v for v, _, _ in D["versions"].values() if v.get("fileId") == f.get("id") and v.get("number") == 1]
        if fvs:
            v = fvs[0]
            if v.get("formVersion") != e.get("toFormVersion") or v.get("submittedAt", "") < (e.get("shownToApplicantAt") or ""):
                fail(where, f"draft event {eid}: the first version is not on the new form version, or came before the changes were shown", "APP-035")
        start = f.get("draftStartedAt", "")
        if start >= (src.get("retiredAt") or "9999"):
            fail(where, f"draft event {eid}: the draft started after its first version was retired", "APP-021")


# ---------------------------------------------------------------------------------------------
# Events and features


def check_events(root, D):
    schemas = {}
    for path in sorted(glob.glob(os.path.join(root, "registry", "events", "*.schema.json"))):
        s = load(path)
        name = os.path.basename(path)[: -len(".schema.json")]
        if s.get("title") != name or not re.fullmatch(r"org\.fpsot\.applications\.[a-z0-9-]+\.[a-z0-9-]+", name):
            fail(os.path.relpath(path, root), "an event type is org.fpsot.applications.<resource>.<event>, named like its file", "NAM-050, APP-088")
        if s.get("additionalProperties") is not False:
            fail(os.path.relpath(path, root), "the event schema must close its data", "APP-088")
        schemas[name] = s
    personal = set()
    for f, _, _ in D["files"].values():
        personal |= {f.get("subjectPartyId"), f.get("reference")}
        for h in f.get("stateHistory") or []:
            personal |= {(h.get("actor") or {}).get("actingPartyId"), (h.get("actor") or {}).get("actorId")}
    personal.discard(None)
    for path in sorted(glob.glob(os.path.join(root, "examples", "*", "events", "*.json"))):
        where = os.path.relpath(path, root)
        e = load(path)
        for k in ("specversion", "id", "source", "type", "time", "datacontenttype", "subject", "dataschema", "data"):
            if k not in e:
                fail(where, f"the event lacks the attribute {k}", "API-101")
        if e.get("specversion") != "1.0":
            fail(where, "the event must be a CloudEvents 1.0 event", "API-100")
        s = schemas.get(e.get("type"))
        if s is None:
            fail(where, f"the type {e.get('type')} has no schema in registry/events/", "API-103, APP-088")
            continue
        if e.get("dataschema") != s.get("$id"):
            fail(where, "dataschema must be the $id of the schema of its type", "API-103")
        json_schema_check(e.get("data"), s, where, "$.data", "API-103")
        for p_, node in walk(e):
            if isinstance(node, str) and node in personal:
                fail(where, f"{p_} holds a party id, an account or a reference number: events hold no personal value", "APP-088")
        if e.get("subject") not in D["files"]:
            fail(where, "the subject must be the id of a file of the examples", "APP-088")
        elif (e.get("data") or {}).get("fileId") != e.get("subject"):
            fail(where, "the subject must be the file that the data names", "APP-088")


def feature_shape(path):
    tags, steps = [], []
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        if s.startswith("@"):
            tags.append(s)
        elif re.match(r"^(Given|When|Then|And|But|Étant donné|Quand|Alors|Et|Mais)\b", s):
            steps.append(tuple(re.findall(r'"([^"]*)"', s)))
    return tags, steps


def check_features(root, D):
    states = set(MOVES) - {None}
    refs = {f.get("reference") for f, _, _ in D["files"].values()}
    for en in sorted(glob.glob(os.path.join(root, "examples", "features", "en", "*.feature"))):
        fr = en.replace(os.sep + "en" + os.sep, os.sep + "fr" + os.sep)
        where = os.path.relpath(fr, root)
        if not os.path.exists(fr):
            fail(where, "each feature exists in English and in French", "TST-030")
            continue
        for f, lang in ((en, "en"), (fr, "fr")):
            if open(f, encoding="utf-8").readline().strip() != f"# language: {lang}":
                fail(os.path.relpath(f, root), f"the first line must be # language: {lang}", "TST-031")
        if feature_shape(en) != feature_shape(fr):
            fail(where, "the English and French versions must have the same tags and steps, with the same quoted values", "TST-032")
        for line in open(en, encoding="utf-8"):
            for m in re.finditer(r'state "([^"]+)"', line):
                if m.group(1) not in states:
                    fail(os.path.relpath(en, root), f"names state {m.group(1)}, which APP-030 does not define", "APP-102")
            for m in re.finditer(r'reference "([^"]+)"', line):
                if m.group(1) not in refs or not reference_ok(m.group(1)):
                    fail(os.path.relpath(en, root), f"names reference {m.group(1)}, which no file of the examples holds", "APP-102")


def check_no_weak_digest(root):
    """MD5 and SHA-1 appear in no data file, schema or profile, not even as a transport checksum (APP-062)."""
    for pattern in ("profiles/*.yaml", "registry/events/*.json", "examples/forms/*.json", "examples/services/*.yaml", "model/applications.yaml"):
        for path in sorted(glob.glob(os.path.join(root, pattern))):
            text = open(path, encoding="utf-8").read()
            for line in text.splitlines():
                if line.lstrip().startswith("#"):
                    continue
                if WEAK_DIGEST.search(line) and "MD5 and SHA-1 are not" not in line:
                    fail(os.path.relpath(path, root), f"names a weak digest: {line.strip()[:60]}", "APP-062")


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), ".."))
    model = Model(os.path.join(root, "model", "applications.yaml"))
    profiles = check_profiles(model, root)
    forms = check_forms(model, root, profiles)
    services = check_services(model, root, profiles, forms)
    data = check_examples(model, root, profiles, forms, services)
    check_events(root, data)
    check_features(root, data)
    check_no_weak_digest(root)
    for f in failures:
        print(f)
    if failures:
        print(f"{len(failures)} failure(s)")
        return 1
    print("OK: the examples meet the checked rules")
    return 0


if __name__ == "__main__":
    sys.exit(main())
