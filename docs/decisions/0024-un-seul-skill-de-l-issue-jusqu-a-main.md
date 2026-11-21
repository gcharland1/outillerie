---
status: accepted
date: 2026-11-21
decision-makers: Gabriel Charland
---

# Un seul skill, de l'issue jusqu'à `main`, derrière des gates

## Contexte et problème

0021 confiait la livraison après l'accord sur la spec au skill `/livrer`, que `/traiter-issue` appelait à
sa dernière étape. Deux skills pour un seul parcours : l'utilisateur veut un skill unique, de l'issue au
merge. Les règles de livraison de 0021 ne changent pas ; seul change le skill qui les porte.

## Options considérées

* `/traiter-issue` contient la livraison ; `/livrer` disparaît
* `/traiter-issue` contient la livraison ; `/livrer` reste comme alias pour un changement créé hors issue
* Deux skills, `/traiter-issue` appelant `/livrer` (0021)

## Décision

Option retenue : « `/traiter-issue` contient la livraison », parce que le parcours se lit d'un bout à
l'autre dans un seul fichier, sans texte dupliqué ni renvoi entre skills.

Règles, mises en œuvre par le skill `/traiter-issue` :

* Seul un accord explicite de l'utilisateur sur la spec des changements livrés ouvre la livraison. Cet accord
  vaut aussi pour les ADR `proposed` que la spec cite, nommés dans le récapitulatif qui le demande, et pour
  la fermeture, par `Closes`, des issues que la spec résout entièrement.
* Gates, dans l'ordre : `/verifier` « terminé » ; relecture par l'agent `relecteur` des commits, deux
  passages, aucun constat bloquant au second, une révision qui contredit *expand/contract* (0007) étant
  bloquante ; CI verte sur le dernier commit ; PR `MERGEABLE` et `CLEAN`.
* Une gate qui échoue arrête tout et rend la main ; aucun contournement (test sauté, `--no-verify`,
  `--admin`, force push sur `main`).
* Les tâches d'un changement sont menées par un agent seul : une vérification qui exige un humain est
  notée comme limite dans le design et dans la PR, pas comme tâche.
* Ouvrir une issue, en fermer une autrement, ou toucher la production, reste soumis à l'accord de
  l'utilisateur.
* GitHub n'exige pas la CI pour merger `main` : seule la gate CI du skill l'impose.

### Conséquences

* Bon, parce que l'utilisateur ne tranche que ce qui lui revient : les décisions et la spec.
* Bon, parce que chaque livraison passe les mêmes gates, notées dans la PR.
* Bon, parce qu'un seul fichier porte le parcours : une gate modifiée ne l'est qu'à un endroit.
* Mauvais, parce qu'un changement créé hors issue (`/opsx:propose`) n'a plus de livraison automatique :
  il suit les étapes 4 à 6 du workflow de `CLAUDE.md` à la main.
* Mauvais, parce qu'un défaut que ni les tests, ni la relecture, ni la CI ne voient part en production sans
  regard humain ; la QA à la main disparaît des tâches.
* Mauvais, parce qu'un `downgrade` n'est jamais exécuté en production : un retour arrière (0017) repose sur
  la rigueur de l'*expand/contract*, sans autre filet.
