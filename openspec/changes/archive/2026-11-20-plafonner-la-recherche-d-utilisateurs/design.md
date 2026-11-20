# Design

Décisions et sources : [questions.md](questions.md).

## Coupe

`USER_RESULTS_MAX = 25` rejoint les réglages de `app/search.py`. `_matching_users` ajoute
`.limit(USER_RESULTS_MAX + 1)` après son `order_by` : le 26e compte ne sert qu'à savoir qu'il y en
a plus, comme `catalog.recent_tools` et `loans.dashboard`. La vue coupe à 25 avant
`relation_states`, qui ne lit donc que les comptes affichés. Le dernier critère de tri est
`User.id` : la coupe tombe toujours au même endroit.

## Message

Le message passe par l'emplacement `message` existant, au-dessus du tableau. Il ne coexiste
jamais avec « Aucun utilisateur ne correspond… » : l'un exige des résultats, l'autre leur absence.
Le texte cherché est échappé par Jinja, comme dans le message sans résultat.

## Non-objectifs

- Pagination ou « Voir plus » : aucune page complète vers laquelle mener, et la pagination
  rouvrirait l'énumération que le plafond réduit.
- Plafond de « Trouver un outil » : borné aux outils des contacts.
- Total des correspondances : un `COUNT` rebalaierait la table.

## Risques

- Le plafond ne réduit pas le coût SQL : PostgreSQL calcule le score de chaque compte avant de
  garder les 26 premiers. Le risque « Coût » de l'ADR 0018 reste entier.
- Le plafond limite chaque réponse, pas l'énumération : rien ne limite le nombre de recherches.
- L'ADR 0018 range « sans plafond » parmi ses conséquences ; c'est désormais faux pour les
  comptes. Un ADR accepté est immuable : le constat reste, ce design le corrige.
