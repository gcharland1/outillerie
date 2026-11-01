---
status: accepted
date: 2026-11-01
decision-makers: Gabriel Charland
---

# Recherche floue des outils avec pg_trgm et unaccent

## Contexte et problème

Un utilisateur filtre les outils de ses contacts par un texte, et les résultats doivent être
classés par qualité de correspondance, nom avant description (issue #29). Les noms d'outils sont
courts, souvent accentués (« Scie à métaux ») et mal orthographiés (« perseuse ») : une
sous-chaîne exacte en laisse passer beaucoup. La recherche d'utilisateurs a écarté `pg_trgm` et
`unaccent` comme non-objectifs, au profit d'une sous-chaîne sans égard à la casse
(`openspec/changes/archive/2026-11-01-liste-de-contacts/design.md`). La base n'a aujourd'hui que
l'extension `btree_gist`. Changement OpenSpec : `openspec/changes/consulter-les-outils-des-contacts/`
(`questions.md` #8, #32 à #37).

## Options considérées

* Sous-chaîne sans égard à la casse (`ILIKE`), tri nom puis description
* Extensions PostgreSQL `pg_trgm` et `unaccent` : ressemblance par trigrammes, accents ignorés
* `pg_trgm` seul : fautes tolérées, accents comptés comme des différences
* Comparaison en Python (`difflib`) sur les outils déjà chargés

Pour l'appliquer :

* Opérateur `<%` réglé par `SET pg_trgm.word_similarity_threshold`
* Fonction `word_similarity()` comparée à une constante de l'application

## Décision

Option retenue : « `pg_trgm` et `unaccent` », parce que c'est la seule qui trouve à la fois une
faute de frappe et un mot sans accent, en SQL, sans charger les outils en mémoire. Les deux
extensions sont livrées avec PostgreSQL (`contrib`) et sont présentes dans l'image `postgres:17`
utilisée en développement, en CI et en production.

Règles :

* Une révision Alembic écrite à la main crée les extensions (`CREATE EXTENSION IF NOT EXISTS`) ;
  son `downgrade()` les laisse en place, comme pour `btree_gist`. Les fixtures de test les créent
  aussi, et le test de schéma vérifie que les révisions les installent.
* Un outil correspond si `unaccent` de son nom ou de sa description contient le texte sans
  accents (`ILIKE`, jokers échappés), ou si `word_similarity(unaccent(texte), unaccent(champ))`
  atteint une constante `FUZZY_THRESHOLD` de l'application (0.5 au départ). Sous 3 caractères,
  seule la sous-chaîne compte.
* Tri : sous-chaîne exacte dans le nom, ressemblance du nom, ressemblance de la description, nom
  sans égard à la casse, identifiant.
* Pas d'index trigramme ni de fonction `unaccent` immuable : la recherche ne porte que sur les
  outils des contacts de l'utilisateur.

Pour le seuil, option retenue : « `word_similarity()` comparée à une constante », parce qu'un
`SET` de session se perd ou fuit d'une requête à l'autre avec le pool de connexions, et que
l'opérateur n'apporte rien sans index.

### Conséquences

* Bon, parce que « perseuse » trouve « Perceuse » et « scie a metaux » trouve « Scie à métaux ».
* Bon, parce que le seuil se règle dans le code, sans migration, et que les tests fixent le
  comportement attendu plutôt que des scores.
* Mauvais, parce que la recherche d'utilisateurs reste une sous-chaîne : deux règles de
  correspondance coexistent jusqu'à ce qu'elle suive.
* Mauvais, parce que deux extensions s'ajoutent au schéma, et le rôle de l'application doit
  pouvoir les créer (propriétaire de la base, comme pour `btree_gist`).
* Mauvais, parce que chaque recherche calcule `unaccent` et la ressemblance sur toutes les lignes
  visibles ; si le volume l'exige, il faudra un index GIN `gin_trgm_ops` et une fonction
  `unaccent` immuable, car la forme à un argument dépend du `search_path` et ne peut pas servir
  dans un index.
* Mauvais, parce qu'un seuil mal calibré donne des faux positifs dans les longues descriptions,
  ou manque une faute dans un nom très court.
