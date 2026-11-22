# Proposal

## Why

Chaque livraison attend deux fois la suite de tests pour un même code : une fois sur la PR, puis
aussitôt sur `main`, car le serveur ne déploie qu'un commit dont le run `push` a réussi (ADR 0017).
La gate de merge exige déjà que la branche contienne `main` : le commit de merge a alors l'arbre que
la PR a testé (vérifié sur `fdfbebe` et `61a07d5`). Exemple : PR #52, `tests` 6 min 7 s sur la PR,
puis de nouveau sur `main` avant tout déploiement.

Les décisions et leur source sont dans [questions.md](questions.md). Décisions d'architecture :
ADR 0017 (complété), ADR 0025 (gates inchangées) ; nouvel ADR 0026, « Ne pas rejouer les tests d'un
arbre déjà testé par sa PR », `proposed`.

## What Changes

- CI : sur un `push` vers `main`, un job `already-tested` cherche la preuve que l'arbre du commit a
  déjà été testé par un run `pull_request` réussi de ce dépôt. Les jobs `tests` et `specs` en
  dépendent : avec la preuve, ils réussissent sans rejouer leurs étapes ; sans elle, ou si la
  recherche échoue, ils rejouent tout.
- Script `deploiement/already_tested.py`, bibliothèque standard seulement, testé comme
  `deployer.py`. `ci.yml` gagne la permission `actions: read`.
- Serveur inchangé : `is_green` exige toujours un run `push` réussi avec `tests` et `specs` réussis ;
  aucune réinstallation sur le serveur.
- Skill `/traiter-issue` : l'étape 17 vérifie que le run `push` du commit de merge réussit sans
  rejouer les tests, et le texte « GitHub n'exige pas la CI pour merger » est corrigé (ruleset du
  2026-11-20, consigné dans l'ADR 0026).

Hors périmètre : la piste 2 de l'issue (merge sans commit de merge), écartée (question 1) ; restreindre
les méthodes de merge du dépôt à `merge`, réglage GitHub laissé à l'utilisateur (question 12) ; le
déployeur et la règle du commit vert.

Closes #53.

## Capabilities

### New Capabilities

### Modified Capabilities
- `livraison-continue` : « Tests du commit mergé » admet qu'un commit de merge dont l'arbre a déjà été
  testé par sa PR réussisse sans rejouer les tests.

## Impact

`.github/workflows/ci.yml`, nouveau `deploiement/already_tested.py` et ses tests,
`.claude/skills/traiter-issue/SKILL.md`, `docs/decisions/` (ADR 0026, index). Livré avec
`confirmation-du-courriel`, après `suppression-de-la-colonne-username` (question 11 de ce dernier).
