# Proposal

## Why

Une recherche d'utilisateurs pour « Fred » ne trouve pas « Fréd » (issue #39) : elle compare une
sous-chaîne sans égard à la casse, mais avec égard aux accents, alors que la recherche d'outils les
ignore déjà et tolère les fautes de frappe (ADR 0016). Deux règles de correspondance coexistent, et
la recherche d'outils laisse passer des jokers : `unaccent` change `％ ＿ ＼` en `% _ \` après
l'échappement, si bien que « ％％％ » liste tous les outils visibles.

## What Changes

- Une seule règle de normalisation pour tout champ de recherche, appliquée au texte cherché et aux
  champs comparés : sans égard à la casse ni aux accents, un tiret vaut une espace, plusieurs
  espaces n'en valent qu'une.
- Les caractères `%`, `_` et `\`, y compris leurs formes pleine chasse, sont cherchés tels quels
  dans toutes les recherches : « %%% » ne trouve que ce qui contient ces caractères.
- Recherche d'utilisateurs : un compte correspond si son nom d'utilisateur, ou son prénom suivi de
  son nom, contient le texte ou, à partir de 4 caractères, lui ressemble (faute de frappe légère,
  ordre « nom prénom »). Résultats triés par qualité de correspondance, puis par nom
  d'utilisateur sans égard à la casse.
- Le minimum de 3 caractères de la barre de recherche se compte sur le texte normalisé : « --- »
  n'est plus une recherche.
- Recherche d'outils : mêmes règles qu'aujourd'hui, plus la normalisation des tirets et des
  espaces et l'échappement corrigé.

## Capabilities

### New Capabilities

Aucune.

### Modified Capabilities

- `recherche` : « Correspondance des utilisateurs » ignore les accents, les tirets et les espaces
  multiples, tolère les fautes à partir de 4 caractères et trie par qualité de correspondance ;
  « Recherche trop courte ou sans résultat » compte le minimum sur le texte normalisé.
- `outils-des-contacts` : « Filtre par texte » ajoute la normalisation des tirets et des espaces et
  les jokers pleine chasse cherchés tels quels ; « Ordre des outils » renvoie aux règles du filtre
  au lieu de « tel quel ».

## Hors périmètre

- Connexion et unicité des noms d'utilisateur : comparaisons exactes, inchangées (rendre « fred »
  et « fréd » équivalents y ouvrirait l'usurpation).
- Plafond du nombre de comptes listés par la recherche d'utilisateurs : issue séparée.
- Normalisation Unicode (NFC) des noms d'utilisateur à l'inscription.
- Index trigramme et fonction `unaccent` immuable.
- Tri sans recherche (« Mes contacts », « Gérer mes outils ») : inchangé.

## Impact

- Code : nouveau module `app/text_search.py` (normalisation, sous-chaîne échappée, score) ;
  `app/catalog.py` (`_text_search` l'utilise, `_escape_like` disparaît) ; `app/search.py`
  (`_matching_users`, tri) ; tests `test_search.py`, `test_catalog.py` ; commentaire de
  `tests/conftest.py`.
- Schéma : aucun changement ; `pg_trgm` et `unaccent` sont déjà installés (révision
  `9654b00a97c3`).
- Dépendance : aucune.
- ADR : nouveau 0018 « Règles communes des champs de recherche » (`accepted`), qui remplace
  l'ADR 0016. ADR concernés : 0002 (SQLAlchemy), 0011 (module partagé sans Blueprint).
- Décisions : `questions.md`.
