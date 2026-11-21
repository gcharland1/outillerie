---
status: accepted
date: 2026-11-21
decision-makers: Gabriel Charland
---

# Trier les issues par étiquettes et livrer les lots approuvés

## Contexte et problème

0024 n'ouvre la livraison que sur un accord donné dans une session de `/traiter-issue`, issue par issue :
l'utilisateur doit être présent pour chaque question et chaque spec. Il veut deux workflows qu'il lance à la
main : l'un trie toutes les issues ouvertes et pose ses questions dans l'issue, l'autre livre, sans lui, les
issues qu'il a approuvées, regroupées par lots. Le dépôt est public : le texte d'une issue peut venir de
n'importe qui. Cet ADR remplace 0024, dont il reprend les règles en y ajoutant ce second mode.

## Options considérées

* L'agent trie (`clarification-required` ou `understood`), l'utilisateur pose `ready-to-implement`, l'agent livre les issues qui portent les deux
* L'agent trie et pose lui-même `ready-to-implement` quand il ne reste aucune question pour l'utilisateur
* Comme la précédente, la livraison attendant N heures sans commentaire de l'utilisateur
* Garder 0024 seul : une session `/traiter-issue` par issue ou groupe d'issues

## Décision

Option retenue : « l'utilisateur pose `ready-to-implement` », parce que rien ne part en production sans
qu'il ait lu les décisions de l'agent, tout en n'exigeant de lui que des réponses dans l'issue et une
étiquette.

### Accord

* Mode interactif (`/traiter-issue <n>`) : seul un accord explicite de l'utilisateur sur la spec des
  changements livrés ouvre la livraison. Il vaut aussi pour les ADR `proposed` que la spec cite, nommés dans
  le récapitulatif qui le demande, et pour la fermeture, par `Closes`, des issues que la spec résout
  entièrement.
* Mode lots (`/traiter-issue lots`) : l'accord est `ready-to-implement`, posée par l'utilisateur sur une issue
  `understood`, après le dernier commentaire de tri, sans nouveau commentaire ni modification du corps depuis. Il
  vaut pour les décisions de ce commentaire, les ADR qu'il annonce et la fermeture de l'issue par `Closes`.
  Il est revérifié avant l'implémentation et avant le merge.

### Tri

* `/trier-issues` trie les issues ouvertes sans commentaire de tri ou sans étiquette de tri, et celles qu'un
  commentaire ou une modification du corps par l'utilisateur a changées depuis le dernier tri. Il n'écrit que
  sur GitHub : un commentaire et une étiquette par issue ; un nouveau tri retire `ready-to-implement`.
* Le commentaire de tri liste les questions qui reviennent à l'utilisateur (options, recommandation), les
  réponses qu'il a déjà données, les décisions prises par convention et les ADR à écrire. Sans question
  restante : `understood` ; sinon `clarification-required`.
* Les deux workflows ne lisent que les issues et commentaires écrits par le propriétaire du dépôt.

### Livraison

* Gates, dans l'ordre : `/verifier` « terminé » ; relecture par l'agent `relecteur` des commits, deux
  passages, aucun constat bloquant au second, une révision qui contredit *expand/contract* (0007) étant
  bloquante ; CI verte sur le dernier commit ; PR `MERGEABLE` et `CLEAN`.
* Aucun contournement : ni test sauté, ni `--no-verify`, ni `--admin`, ni force push sur `main`.
* Les tâches d'un changement sont menées par un agent seul : une vérification qui exige un humain est notée
  comme limite dans le design et dans la PR, pas comme tâche.
* Mode lots : les issues approuvées qui touchent le même code forment un lot, livré dans sa propre branche,
  un lot après l'autre ; une issue qui retire ou resserre le schéma forme un lot seul, arrêté si sa spec
  modifie aussi le code applicatif (0007). La spec de chaque lot s'écrit sans question ; une question pour
  l'utilisateur ou un ADR que le commentaire de tri ne couvrait pas arrête le lot ; une nouvelle décision
  par convention est appliquée et listée dans le corps de PR.
* Une gate qui échoue arrête la livraison. En mode interactif, la main revient à l'utilisateur. En mode lots,
  chaque issue du lot reçoit `delivery-blocked` et un commentaire court (gate et raison, lien vers
  `blocage.md`, poussé sur la branche du lot) ; les lots qui en dépendent sont sautés, les autres continuent.
  L'utilisateur retire l'étiquette pour relancer.
* Ouvrir une issue, en fermer une autrement que par `Closes`, ou toucher la production, reste soumis à
  l'accord de l'utilisateur.
* GitHub n'exige pas la CI pour merger `main` : seule la gate CI du skill l'impose.
* `/traiter-issue` porte les deux modes de livraison, pour qu'une gate modifiée ne le soit qu'à un endroit.

### Conséquences

* Bon, parce que l'utilisateur répond aux questions et approuve quand il veut, sans session ouverte.
* Bon, parce que chaque livraison, interactive ou par lots, passe les mêmes gates, notées dans la PR.
* Bon, parce qu'une issue ou un commentaire d'un tiers ne pilote aucun agent.
* Mauvais, parce qu'en mode lots l'utilisateur approuve un commentaire de tri, pas la spec écrite ensuite :
  une spec qui s'en écarte sans soulever de question part en production sans regard humain.
* Mauvais, parce qu'un défaut que ni les tests, ni la relecture, ni la CI ne voient part en production sans
  regard humain ; la QA à la main disparaît des tâches.
* Mauvais, parce qu'un `downgrade` n'est jamais exécuté en production : un retour arrière (0017) repose sur
  la rigueur de l'*expand/contract*, sans autre filet.
* Mauvais, parce qu'un lot arrêté laisse une branche poussée et parfois une PR ouverte, à reprendre par
  `/traiter-issue livrer` ou à fermer à la main.
* Mauvais, parce que l'agent écrit sur un dépôt public (commentaires, étiquettes) à chaque tri.
* Mauvais, parce que l'agent publie avec le compte du propriétaire : la vérification de l'auteur de
  `ready-to-implement` écarte les tiers, mais ne prouve pas que l'étiquette a été posée à la main.
* Mauvais, parce qu'un titre modifié ou un commentaire édité n'est pas détecté : l'utilisateur commente
  pour relancer le tri.
* Mauvais, parce qu'un changement créé hors issue (`/opsx:propose`) n'a pas de livraison automatique :
  il suit les étapes 4 à 6 du workflow de `CLAUDE.md` à la main.
