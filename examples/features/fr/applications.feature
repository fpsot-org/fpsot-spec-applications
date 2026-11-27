# language: fr
# SPDX-License-Identifier: Community-Spec-1.0
# Scénarios de la spécification FPSOT sur les demandes (APP-102), sur les fichiers synthétiques de
# examples/. Chaque scénario indique ses dates, ses états et ses numéros de référence, et la version
# anglaise contient les mêmes étapes avec les mêmes valeurs entre guillemets (TST-032).
Fonctionnalité: Recevoir une demande et prouver ce qui est arrivé

  @APP-040 @APP-041 @APP-101
  Scénario: Une demande de permis d’embarcation de plaisance amorce une demande de paiement et une déclaration
    Étant donné le service "pleasure-craft-licensing" sous le profil "ca-federal"
    Et un brouillon sur la version de formulaire "2.0.0" avec une pièce jointe saine du type "application/pdf"
    Quand la personne requérante le dépose le "2026-03-10T14:58:30Z"
    Alors le dossier a le numéro de référence "7HQ3-MZ4K-4" et l’état "submitted"
    Et son constat de réception indique "2026-03-10T10:58:30" dans le fuseau horaire "America/Toronto"
    Et le dossier transmet une "fee-order" et une "filing"
    Et un enregistrement de décision fait passer le dossier à l’état "decided" le "2026-03-10T15:05:00Z"

  @APP-025 @APP-070
  Scénario: Une entreprise demande un permis en français seulement
    Étant donné le service "example-operating-permit" dont le genre de demande est "legal-person-permit-or-grant"
    Et le profil "ca-qc" dont la règle de langue "charter-21-9" exige "fr" seulement
    Quand une personne qui représente l’entreprise dépose le "2026-06-15T13:42:07Z" selon la représentation "rel-qc-7f3a21"
    Alors le dossier a le numéro de référence "Q2X8-PR5D-X", la langue "fr" et la base "charter-21-9"
    Et l’entreprise reçoit un avis du genre "on-behalf-submitted"

  @APP-052 @APP-054 @APP-055
  Scénario: Une demande de renseignements suspend un décompte et son échéance passe un jour férié
    Étant donné le dossier au numéro de référence "4WD7-KT9N-E" à l’état "in-review"
    Quand le personnel ouvre une demande de renseignements au motif "outdated" le "2026-05-25T15:00:00Z" pour "30" jours
    Alors l’échéance brute est le "2026-06-24" et l’échéance après report est le "2026-06-25"
    Et le décompte "service-standard" est "suspended" et le dossier est à l’état "information-requested"
    Et l’étiquette d’état est "action-needed"
    Quand la personne répond le "2026-06-10T16:30:00Z" avec une nouvelle version de pièce jointe
    Alors le dossier est à l’état "in-review" avec une deuxième version et un deuxième constat de réception
    Et le décompte "service-standard" est "resumed" et le décompte "review-time-limit" est "started"

  @APP-056 @APP-057 @APP-087
  Scénario: Un dossier se ferme après l’échéance d’une demande de renseignements et une tentative de contact consignée
    Étant donné le dossier au numéro de référence "JN6V-3F8C-2" et une demande de renseignements ouverte le "2026-08-10T14:00:00Z"
    Et un texto dont la livraison a "failed" et un courriel qui a été "delivered" le "2026-08-11T13:00:00Z"
    Et une interruption du canal "digital" qui reporte l’échéance du "2026-09-09" au "2026-09-15"
    Quand la demande de renseignements échoit le "2026-09-16T04:00:00Z"
    Alors le personnel peut faire passer le dossier à l’état "closed"

  @APP-070 @APP-072 @APP-073
  Scénario: Une personne qui représente et une personne qui aide sur simple déclaration déposent pour autrui
    Étant donné le dossier au numéro de référence "RB4T-6WXA-=" déposé par un "representative" selon la représentation "rel-5b2e90"
    Et le dossier au numéro de référence "M9C2-HV7E-H" déposé avec l’assurance "self-declared"
    Alors chaque acte consigne la partie agissante séparément de la partie visée
    Et chaque partie représentée reçoit un avis du genre "on-behalf-submitted"

  @APP-041 @APP-091 @APP-092
  Scénario: Le personnel saisit une demande papier cinq jours après son arrivée
    Étant donné une demande papier dont le tampon dateur porte le "2026-04-02" à son arrivée
    Quand le membre du personnel "staff-2c71d0" la saisit le "2026-04-07T14:05:00Z"
    Alors le dossier a le numéro de référence "2KF9-XA3P-X" et le canal "paper"
    Et son instant de réception est le "2026-04-02T04:00:00Z", début de ce jour local, avec la précision "day"
    Et l’instant de la saisie est consigné séparément dans "keyedAt"

  @APP-035
  Scénario: Un brouillon passe à une nouvelle version du formulaire avant son dépôt
    Étant donné un brouillon commencé le "2026-08-20T22:15:00Z" sur la version de formulaire "1.0.0"
    Et la version de formulaire "1.1.0" est devenue active le "2026-09-01T13:00:00Z"
    Quand la personne accepte le passage le "2026-09-03T14:12:00Z"
    Alors les réponses à "fullName" et à "mailingAddress" sont reportées selon l’id de question
    Et la question "mailingAddress" s’affiche de nouveau, car son étiquette a changé
    Et la réponse à "householdIncome" n’est pas reportée, et l’événement du brouillon l’énumère
    Et le dossier a le numéro de référence "V8NQ-4C2M-U" sur la version de formulaire "1.1.0"
