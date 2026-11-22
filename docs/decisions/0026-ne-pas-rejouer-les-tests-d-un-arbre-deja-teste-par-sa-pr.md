---
status: proposed
date: 2026-11-21
decision-makers: Gabriel Charland
---

# Ne pas rejouer les tests d'un arbre déjà testé par sa PR

## Contexte et problème

L'ADR 0017 ne déploie un commit de `main` qu'après un run `push` réussi avec les jobs `tests` et
`specs`. La gate de merge de l'ADR 0025 exige une branche qui contient `main` : le commit de merge a
donc l'arbre que la PR vient de tester, et chaque livraison attend deux fois la même suite (issue
#53). Changement OpenSpec : `openspec/changes/tests-une-seule-fois-par-livraison/` (décisions et
sources dans `questions.md`).

Depuis le 2026-11-20, le ruleset « main no push » de GitHub exige une PR et les checks `tests` et
`specs` pour merger `main`, sans branche à jour (`strict: false`), et un admin peut le contourner.
L'ADR 0025 dit encore que GitHub n'exige pas la CI pour merger : cet ADR consigne le ruleset, voulu
et durable.

## Options considérées

* Le run `push` réutilise le résultat du run `pull_request` quand l'arbre du commit de merge est celui
  de la tête de PR testée
* Merger sans commit de merge (fast-forward), le serveur acceptant un run `pull_request` réussi sur le
  même SHA
* Garder les deux runs complets

## Décision

Option retenue : « réutiliser le run de la PR », parce qu'elle garde le merge, l'historique, la
règle du commit vert de l'ADR 0017 et le serveur tels quels. Le fast-forward est écarté : GitHub n'en
fait jamais depuis une PR (« Rebase and merge » et « Squash » créent de nouveaux SHA), et le seul
fast-forward possible est un `git push` vers `main` en contournement admin, interdit par l'ADR 0025.

* Sur un `push` vers `main`, les jobs `tests` et `specs` réussissent sans rejouer leurs étapes
  seulement si le commit est un commit de merge dont le second parent contient le premier, dont
  l'arbre égale celui du second parent, et pour lequel un run `pull_request` de ce dépôt (pas d'un
  fork), sur ce second parent, a réussi avec `tests` et `specs` à sa dernière tentative.
* Dans tout autre cas, y compris une erreur de l'API GitHub, ils rejouent toutes leurs étapes.
* La preuve se cherche dans la CI, par un job qui lit l'API avec `actions: read`. Les jobs `tests`
  et `specs` gardent leur nom et réussissent : le serveur ne change pas.
* Cet ADR complète l'ADR 0017 sans le remplacer : sa règle (run `push` réussi, `tests` et `specs`
  réussis) reste vraie.

### Conséquences

* Bon, parce qu'une livraison n'attend la suite de tests qu'une fois, et qu'aucun commit n'arrive en
  production sans une CI verte sur son contenu exact.
* Bon, parce qu'un commit poussé sur `main` sans PR reste testé avant tout déploiement.
* Mauvais, parce qu'un merge en squash, en rebase ou sans branche à jour rejoue la suite tant que le
  dépôt permet ces méthodes.
* Mauvais, parce que le statut d'un commit de `main` dépend aussi d'un run de PR : sa lecture
  demande de suivre le lien vers ce run.
