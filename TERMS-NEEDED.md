# Terms needed

Entries in the format of `termbase/terms.yaml` of fpsot-spec-writing, for a pull request to the term base.
The pages of this specification write these terms in plain text for now, and will use the term attributes once the term base has them.
The French forms marked "to confirm" have no record that the writer could check in the Grand dictionnaire terminologique or TERMIUM Plus during this work.
French forms that come from a French text of law that the research read say so in their source.

## Decisions for the lead (provisional French forms)

1. **application → « demande »** (used on every French page). It is the word that Québec and French law use, but it collides with two other terms of the FPSOT pages.
   - The fees specification renders *fee order* as « demande de paiement ».
   - This specification renders *request for information* as « demande de renseignements ».

   The French pages keep them apart this way: a bare « demande » always means the application; « demande de paiement » and « demande de renseignements » are always written in full, never shortened to « demande »; the record of an application is « dossier de demande », or « dossier » once the context is set. The lead may prefer another form for the request, such as « demande de complément » or « avis de pièces manquantes », which would remove one of the two collisions.
2. **receipt record → « constat de réception »** (provisional). The term base already holds *receipt* / « reçu » for the receipt of a fee (FEE-080), with a definition tied to a fee order. The English pages therefore never say a bare "receipt": they say "receipt record" for the proof of arrival, and the French pages say « constat de réception », never « reçu ». Alternatives: « preuve de réception », « enregistrement de réception ».
3. **applicant → « personne requérante »** (provisional, used on every French page). It is neutral in gender and current in Québec administrative writing. Alternatives: « demandeur ou demanderesse », « auteur de la demande ».
4. **clock → « décompte »** (provisional). « Délai » already renders *time limit*, and « compteur » sounds mechanical. A clock that a request suspends is then « un décompte suspendu ».
5. **front end → « interface utilisateur »** (provisional), kept apart from « interface de programmation » for an API.
6. **Spelling of our codes and class names.** English is US spelling, so the class is `Acknowledgment`, not `Acknowledgement` as the plan wrote it. The plan's `Receipt` class is `ReceiptRecord`, to keep it apart from the `Receipt` class of the fees model.
7. **submission → « dépôt »**, after the French *dépôt* of the federal law on electronic documents and of Démarche Numérique. To confirm.
8. **service declaration → « déclaration de service »** (provisional). The term base already renders *filing* (REG) as « déclaration », and Québec law has the *déclaration de services aux citoyens*. The French pages write « déclaration de service » in full for the file of a program, « déclaration » alone only for a filing of a register, and « dépôt sur simple déclaration » for a self-declared submission. Alternatives for the file of a program: « fiche de service », « paramétrage du service ».
9. **case → « affaire »** (provisional). The French pages write « dossier » for the application file, so the case that a later case specification holds, and a case of the Dutch APIs, is « affaire », and a case system is « système de traitement des affaires ».
10. **date stamp → « tampon dateur »**, and **received precision → « précision de la réception »**. To confirm.

```yaml
  - id: application
    kind: term
    en: {full: "application", definition: "A request to a public body for a decision about one party, such as a permit, a license, a benefit or a grant."}
    fr: {full: "demande", definition: "Requête adressée à un organisme public pour obtenir une décision sur une partie, comme un permis, une licence, une prestation ou une subvention."}
    source: {name: "Loi sur la justice administrative, RLRQ, c. J-3, articles 4 to 6 (French form of the act); French form provisional, see decision 1", url: "https://www.legisquebec.gouv.qc.ca/fr/document/lc/J-3", checked: "2026-11-23"}
  - id: application-file
    kind: term
    en: {full: "application file", definition: "The record of one application from its first draft to its end, with its states, its versions and the acts on it, whatever its channel."}
    fr: {full: "dossier de demande", definition: "Donnée d’une demande, de son premier brouillon jusqu’à sa fin, avec ses états, ses versions et les actes faits sur elle, quel que soit son canal."}
    source: {name: "FPSOT applications specification, APP-030; French form to confirm", url: "https://github.com/fpsot-org/fpsot-spec-applications", checked: "2026-11-26"}
  - id: applicant
    kind: term
    en: {full: "applicant", definition: "The party that an application is about and that applies, alone or through a representative."}
    fr: {full: "personne requérante", definition: "Partie que vise une demande et qui la présente, seule ou par une personne qui la représente."}
    source: {name: "FPSOT applications specification, APP-001; French form provisional, see decision 3", url: "https://github.com/fpsot-org/fpsot-spec-applications", checked: "2026-11-26"}
  - id: file-version
    kind: term
    en: {full: "file version", definition: "One submitted state of an application file, with the answers and attachments sent at that time, which never changes."}
    fr: {full: "version du dossier", definition: "État déposé d’un dossier de demande, avec les réponses et les pièces jointes transmises à ce moment, qui ne change jamais."}
    source: {name: "FPSOT applications specification, APP-036 and APP-037; French form to confirm", url: "https://github.com/fpsot-org/fpsot-spec-applications", checked: "2026-11-26"}
  - id: form-definition
    kind: term
    en: {full: "form definition", definition: "One version of a form: its canonical address, its business version, its status, its questions and the JSON Schema that its answers meet."}
    fr: {full: "définition de formulaire", definition: "Version d’un formulaire : son adresse canonique, sa version métier, son statut, ses questions et le schéma JSON que respectent ses réponses."}
    source: {name: "FPSOT applications specification, APP-020, after the Questionnaire of HL7 FHIR R5; French form to confirm", url: "https://hl7.org/fhir/R5/questionnaire.html", checked: "2026-11-23"}
  - id: receipt-record
    kind: term
    en: {full: "receipt record", definition: "The sealed record of when a submission became accessible to a public body, from whom, through which channel, with the digests of what arrived."}
    fr: {full: "constat de réception", definition: "Donnée cachetée du moment où un dépôt est devenu accessible à un organisme public, de qui, par quel canal, avec les condensés de ce qui est arrivé."}
    source: {name: "FPSOT applications specification, APP-040 to APP-042, after article 31 of the Loi concernant le cadre juridique des technologies de l'information; French form provisional, see decision 2", url: "https://www.legisquebec.gouv.qc.ca/fr/document/lc/C-1.1", checked: "2026-11-23"}
  - id: acknowledgment
    kind: term
    en: {full: "acknowledgment of receipt", definition: "The message that a public body sends for each submission, with the reference number, the received time, the body that handles it and what comes next."}
    fr: {full: "accusé de réception", definition: "Message qu’un organisme public envoie pour chaque dépôt, avec le numéro de référence, l’heure de réception, l’organisme qui le traite et la suite."}
    source: {name: "Loi concernant le cadre juridique des technologies de l'information, RLRQ, c. C-1.1, articles 28 and 31 (official French form)", url: "https://www.legisquebec.gouv.qc.ca/fr/document/lc/C-1.1", checked: "2026-11-23"}
  - id: reference-number
    kind: term
    en: {full: "reference number", definition: "The random number that an applicant quotes for an application file, with a check character, which tells nothing about the person or the matter."}
    fr: {full: "numéro de référence", definition: "Numéro aléatoire qu’une personne cite pour un dossier de demande, avec un caractère de contrôle, qui ne révèle rien de la personne ni de l’affaire."}
    source: {name: "FPSOT applications specification, APP-045; French form to confirm", url: "https://github.com/fpsot-org/fpsot-spec-applications", checked: "2026-11-26"}
  - id: request-for-information
    kind: term
    en: {full: "request for information", definition: "A message in which a public body asks the applicant for missing or corrected items, with its reason, its deadline and its effect on each clock."}
    fr: {full: "demande de renseignements", definition: "Message par lequel un organisme public demande à la personne des éléments manquants ou corrigés, avec son motif, son échéance et son effet sur chaque décompte."}
    source: {name: "FPSOT applications specification, APP-050; French form provisional, see decision 1", url: "https://github.com/fpsot-org/fpsot-spec-applications", checked: "2026-11-26"}
  - id: clock
    kind: term
    en: {full: "clock", definition: "A period that runs on an application file, such as a service standard or a statutory time limit, which a request can start or suspend."}
    fr: {full: "décompte", definition: "Période qui court sur un dossier de demande, comme une norme de service ou un délai légal, qu’une demande de renseignements peut faire partir ou suspendre."}
    source: {name: "FPSOT applications specification, APP-054; French form provisional, see decision 4", url: "https://github.com/fpsot-org/fpsot-spec-applications", checked: "2026-11-26"}
  - id: service-standard
    kind: term
    en: {full: "service standard", definition: "A published promise of how well or how fast a service performs in normal conditions, in a form that can be measured."}
    fr: {full: "norme de service", definition: "Promesse publiée sur la qualité ou la rapidité d’un service dans des conditions normales, sous une forme mesurable."}
    source: {name: "Policy on Service and Digital, Treasury Board of Canada Secretariat, definitions (official French form; definition in FPSOT wording)", url: "https://www.tbs-sct.canada.ca/pol/doc-eng.aspx?id=32603", checked: "2026-11-23"}
  - id: status-projection
    kind: term
    en: {full: "status projection", definition: "What an applicant sees of an application file: one label of a closed published list, mapped from its state, and what to do when action is needed."}
    fr: {full: "projection d’état", definition: "Ce qu’une personne voit d’un dossier de demande : une étiquette d’une liste fermée et publiée, tirée de son état, et ce qu’il faut faire quand une action est requise."}
    source: {name: "FPSOT applications specification, APP-080 and APP-081; French form to confirm", url: "https://github.com/fpsot-org/fpsot-spec-applications", checked: "2026-11-26"}
  - id: acting-party
    kind: term
    en: {full: "acting party", definition: "The party who does an act on an application file, recorded apart from the party whose file it is."}
    fr: {full: "partie agissante", definition: "Partie qui fait un acte sur un dossier de demande, consignée séparément de la partie à qui appartient le dossier."}
    source: {name: "FPSOT applications specification, APP-071; French form to confirm", url: "https://github.com/fpsot-org/fpsot-spec-applications", checked: "2026-11-26"}
  - id: service-declaration
    kind: term
    en: {full: "service declaration", definition: "The file in which a program states its forms, its clocks, its channels, its drafts and its rules on closing and self-declared submissions."}
    fr: {full: "déclaration de service", definition: "Fichier dans lequel un programme indique ses formulaires, ses décomptes, ses canaux, ses brouillons et ses règles sur la fermeture et le dépôt sur simple déclaration."}
    source: {name: "FPSOT applications specification, APP-012; French form to confirm; not to be confused with the déclaration de services aux citoyens of article 6 of the Loi sur l'administration publique", url: "https://github.com/fpsot-org/fpsot-spec-applications", checked: "2026-11-26"}
  - id: full-grant
    kind: term
    en: {full: "full grant", definition: "A decision outcome that gives the applicant all that the application asks; every other result of a decision is adverse to the applicant."}
    fr: {full: "octroi complet", definition: "Issue d’une décision qui accorde à la personne tout ce que sa demande sollicite; tout autre résultat d’une décision lui est défavorable."}
    source: {name: "FPSOT applications specification, APP-032 and APP-052, after the result kinds of DEC-024; French form to confirm", url: "https://github.com/fpsot-org/fpsot-spec-applications", checked: "2026-11-26"}
  - id: date-stamp
    kind: term
    en: {full: "date stamp", definition: "The mark that a body puts on a paper document when it arrives, which may hold a date only, or a time to the minute."}
    fr: {full: "tampon dateur", definition: "Marque qu’un organisme appose sur un document papier à son arrivée, qui peut ne porter qu’une date, ou une heure à la minute."}
    source: {name: "FPSOT applications specification, APP-041 and APP-092; French form to confirm, see decision 10", url: "https://github.com/fpsot-org/fpsot-spec-applications", checked: "2026-11-26"}
  - id: case
    kind: term
    en: {full: "case", definition: "The matter that a body works on after an application, which a later case specification will hold."}
    fr: {full: "affaire", definition: "Ce que traite un organisme à la suite d’une demande, que contiendra une future spécification sur le traitement des affaires."}
    source: {name: "FPSOT applications specification, APP-032; French form provisional, see decision 9", url: "https://github.com/fpsot-org/fpsot-spec-applications", checked: "2026-11-26"}
```
