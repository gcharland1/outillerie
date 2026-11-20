# Proposal

## Why

La recherche d'utilisateurs liste chaque compte trouvé, sans limite. Depuis la recherche sans
accents (issue #39), elle tolère une faute de frappe dès 4 caractères et renvoie donc plus de
comptes. L'issue #40 demande de plafonner la liste et d'inviter à préciser la recherche au-delà.

Les décisions et leur source sont dans [questions.md](questions.md).

## What Changes

- La recherche d'utilisateurs liste au plus 25 comptes, les premiers dans son ordre de tri.
- Au-delà, la page affiche au-dessus du tableau « Plus de 25 utilisateurs correspondent à
  « texte » ; précisez votre recherche ». Ni total, ni pagination, ni « Voir plus ».

## Capabilities

### New Capabilities

### Modified Capabilities
- `recherche`: nouvelle exigence « Nombre de comptes listés ».

## Impact

`app/search.py` (constante `USER_RESULTS_MAX`, `LIMIT` sur la requête), `tests/test_search.py`.
Aucun schéma, aucune dépendance, aucun ADR : le tri et les réglages de chaque recherche relèvent
de sa spec (ADR 0018). Le tri par prénom puis nom vient du changement `authentification-par-courriel`,
dans la même branche ; ce changement n'ajoute que la coupe.
