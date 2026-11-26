# language: en
# SPDX-License-Identifier: Community-Spec-1.0
# Scenarios of the FPSOT applications specification (APP-102), on the synthetic files of examples/.
# Each scenario states its dates, its states and its references, and the French version holds the
# same steps with the same quoted values (TST-032).
Feature: Take in an application and prove what arrived

  @APP-040 @APP-041 @APP-101
  Scenario: A pleasure craft license application starts a fee order and a filing
    Given the service "pleasure-craft-licensing" under the profile "ca-federal"
    And a draft on the form version "2.0.0" with a clean attachment of type "application/pdf"
    When the applicant submits it on "2026-03-10T14:58:30Z"
    Then the file has the reference "7HQ3-MZ4K-4" and the state "submitted"
    And its receipt record shows "2026-03-10T10:58:30" in the time zone "America/Toronto"
    And the file hands off a "fee-order" and a "filing"
    And a decision record moves the file to the state "decided" on "2026-03-10T15:05:00Z"

  @APP-025 @APP-070
  Scenario: A business applies for a permit in French only
    Given the service "example-operating-permit" whose kind of application is "legal-person-permit-or-grant"
    And the profile "ca-qc" whose language rule "charter-21-9" asks for "fr" only
    When a representative of the business submits on "2026-06-15T13:42:07Z" on the representation "rel-qc-7f3a21"
    Then the file has the reference "Q2X8-PR5D-X", the language "fr" and the basis "charter-21-9"
    And the business receives a notice of type "on-behalf-submitted"

  @APP-052 @APP-054 @APP-055
  Scenario: A request for information suspends a clock and its deadline rolls past a holiday
    Given the file with the reference "4WD7-KT9N-E" in the state "in-review"
    When staff open a request with the reason "outdated" on "2026-05-25T15:00:00Z" for "30" days
    Then the raw deadline is "2026-06-24" and the deadline after the roll is "2026-06-25"
    And the clock "service-standard" is "suspended" and the file is in the state "information-requested"
    And the status label is "action-needed"
    When the applicant replies on "2026-06-10T16:30:00Z" with a new attachment version
    Then the file is in the state "in-review" with a second file version and a second receipt record
    And the clock "service-standard" is "resumed" and the clock "review-time-limit" is "started"

  @APP-056 @APP-057 @APP-087
  Scenario: A file closes after an expired request and a logged contact attempt
    Given the file with the reference "JN6V-3F8C-2" and a request opened on "2026-08-10T14:00:00Z"
    And a text message that "failed" and an email that was "delivered" on "2026-08-11T13:00:00Z"
    And an outage of the channel "digital" that moves the deadline from "2026-09-09" to "2026-09-15"
    When the request expires on "2026-09-16T04:00:00Z"
    Then staff may move the file to the state "closed"

  @APP-070 @APP-072 @APP-073
  Scenario: A representative and a self-declared helper submit for others
    Given the file with the reference "RB4T-6WXA-=" submitted by a "representative" on the representation "rel-5b2e90"
    And the file with the reference "M9C2-HV7E-H" submitted with the assurance "self-declared"
    Then each act records the acting party apart from the subject
    And each represented party receives a notice of type "on-behalf-submitted"

  @APP-041 @APP-091 @APP-092
  Scenario: Staff key in a paper application five days after it arrived
    Given a paper application with a date stamp of "2026-04-02" on arrival
    When the staff member "staff-2c71d0" keys it in on "2026-04-07T14:05:00Z"
    Then the file has the reference "2KF9-XA3P-X" and the channel "paper"
    And its received instant is "2026-04-02T04:00:00Z", the start of that local day, with the precision "day"
    And the instant of keying is recorded apart in "keyedAt"

  @APP-035
  Scenario: A draft moves to a new form version before its submission
    Given a draft started on "2026-08-20T22:15:00Z" on the form version "1.0.0"
    And the form version "1.1.0" became active on "2026-09-01T13:00:00Z"
    When the applicant accepts the move on "2026-09-03T14:12:00Z"
    Then the answers to "fullName" and "mailingAddress" carry over by question id
    And the question "mailingAddress" shows again, since its label changed
    And the answer to "householdIncome" is dropped and listed in the draft event
    And the file has the reference "V8NQ-4C2M-U" on the form version "1.1.0"
