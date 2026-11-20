---
status: accepted
date: 2026-11-20
decision-makers: Gabriel Charland
---

# Livrer jusqu'à `main` derrière des gates, après l'accord sur la spec

## Contexte et problème

`/traiter-issue` s'arrêtait à la spec ; l'implémentation, la vérification, la relecture, l'archivage, la PR
et le merge demandaient chacun une relance de l'utilisateur. L'utilisateur veut n'intervenir que pour les
décisions et l'accord sur la spec, et que le code arrive ensuite dans `main` seul, de manière sûre. Or merger
`main` déploie la production (0017).

## Options considérées

* Livraison automatique après l'accord sur la spec, chaque étape gardée par une gate qui arrête tout en cas d'échec
* Livraison automatique jusqu'à la PR, merge par l'utilisateur
* Workflow actuel : une relance de l'utilisateur à chaque étape

## Décision

Option retenue : « livraison automatique derrière des gates », parce que l'accord porte sur la spec, qui
fixe le comportement, et que les gates vérifient que le code la respecte mieux qu'une relance sans relecture.

Règles, mises en œuvre par le skill `/livrer` :

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
* Mauvais, parce qu'un défaut que ni les tests, ni la relecture, ni la CI ne voient part en production sans
  regard humain ; la QA à la main disparaît des tâches.
* Mauvais, parce qu'un `downgrade` n'est jamais exécuté en production : un retour arrière (0017) repose sur
  la rigueur de l'*expand/contract*, sans autre filet.
