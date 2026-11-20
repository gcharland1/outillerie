# Design

## Context

Voir `proposal.md` (Why) et les décisions de `questions.md`. Chemins relatifs à `application/`.

- Recherche d'utilisateurs : `search._matching_users` (`app/search.py:38-52`), `icontains` avec
  `autoescape` sur quatre expressions, tri `lower(username), id`, balayage de toute la table `user`.
- Recherche d'outils : `catalog._text_search` (`app/catalog.py:312-331`) applique `unaccent` au
  champ et au motif, puis `word_similarity` dès `FUZZY_MIN_LENGTH` (3) au seuil
  `FUZZY_THRESHOLD` (0.5). Le motif est échappé en Python (`_escape_like`) **avant** `unaccent`,
  qui change ensuite `％ ＿ ＼` en `% _ \` : vérifié en base de dev, `'abcdef' ILIKE
  unaccent('%％%')` est vrai.
- `pg_trgm` et `unaccent` sont installés par la révision `9654b00a97c3` et par la fixture
  `mock_app`.

## Goals / Non-Goals

**Goals:**

- Une seule fonction de normalisation et d'échappement, côté SQL, partagée par les deux recherches.
- Constantes de flou propres à chaque recherche, sans toucher au réglage des outils.

**Non-Goals:**

- Index GIN `gin_trgm_ops` et `unaccent` immuable (voir Risques).
- Normalisation Python (NFC/NFKD) du texte ou des données stockées.
- Plafond du nombre de résultats.

## Decisions

### Module `app/text_search.py`, sans Blueprint

Expose, en expressions SQLAlchemy :

- `normalized(expression)` : `unaccent`, puis tiret → espace, puis
  `regexp_replace(…, '\s+', ' ', 'g')`. S'applique aux colonnes comme au texte cherché (paramètre
  lié), pour que les deux côtés suivent la même règle.
- `contains(column, text)` : `normalized(column) ILIKE '%' || échappé(normalized(text)) || '%'`
  avec `ESCAPE '\'`, l'échappement (`\`, `%`, `_`) étant fait en SQL par `replace` **sur le
  résultat** de la normalisation.
- `similarity(column, text)` : `word_similarity(normalized(text), normalized(column))`.

`catalog._text_search` et `search._matching_users` l'utilisent ; `_escape_like` disparaît.
Comme `catalog.py` et `photos.py`, c'est un module partagé sans Blueprint : l'ADR 0011 ne règle que
les Blueprints.

Alternatives écartées : échapper en Python après un `unaccent` Python (aucune implémentation
Python ne reproduit `unaccent.rules`, NFKD ignore ß, œ, ø) ; garder `icontains(autoescape=True)`
(ne peut pas envelopper le motif dans `unaccent`).

### Correspondance et tri des utilisateurs

Deux expressions comparées : `username` et `first_name || ' ' || last_name`. La concaténation
couvre le prénom seul et le nom seul en sous-chaîne, et le même score que chaque champ en
ressemblance, puisque `word_similarity` cherche la meilleure étendue (mesuré :
`word_similarity('gagne','Bob Gagnon')` = `word_similarity('gagne','gagnon')` = 0.667) ; elle
trouve aussi « gagnon bob » (1.0).

Tri : `contains` sur l'une des deux (desc), puis `greatest` des deux scores (desc), puis
`lower(username)`, puis `id`. Aucun champ ne prime : un compte se reconnaît autant par son nom
d'utilisateur que par son nom.

Sous `USER_FUZZY_MIN_LENGTH` (4) caractères, seule `contains` compte, et le score ne sert pas au
tri. Seuil `USER_FUZZY_THRESHOLD` = 0.5. Constantes dans `app/search.py`. Raison : à 3 caractères,
2 trigrammes sur 4 suffisent, donc « gax » trouve Gagnon (0.5) ; à 4, les fautes mesurées restent
trouvées (gagnion/gagnon 0.5, tremblai/tremblay 0.778, frederik/frédéric 0.778).

### Minimum de longueur

`search.results` normalise d'abord le texte par un `SELECT` sur le texte seul (`normalized`, puis
`btrim`), et compare la longueur du résultat à `SEARCH_MIN_LENGTH`, avant de choisir la branche
« Outil » ou « Utilisateur ». `USER_FUZZY_MIN_LENGTH` se compte sur ce même texte normalisé.
Raison : compté sur le texte saisi, « --- » ou « e » suivi d'accents combinants passe le minimum
puis se normalise en une espace ou une lettre, et le motif trouve alors presque tous les comptes.
Alternative écartée : normaliser en Python, qui ne reproduit ni les tirets typographiques ni les
règles de `unaccent`.

### Outils

`_text_search` garde son tri et ses constantes ; seules la normalisation et l'échappement passent
par `text_search`. La spec « Ordre des outils » disait « contient le texte tel quel » ; un delta
la fait renvoyer aux règles du filtre par texte, puisque « tire bouchon » est désormais contenu
dans « Tire-bouchon ».

### ADR

ADR 0018 « Règles communes des champs de recherche » (`accepted`) remplace l'ADR 0016 : il en
reprend `pg_trgm` et `unaccent`, et ajoute la normalisation, l'échappement après normalisation, la
recherche d'utilisateurs et l'absence d'index pour une recherche qui balaie toute la table `user`.

## Risks / Trade-offs

- [Faux positifs du flou sur des noms courts : martin/Martel 0.571, marie/Mario 0.667,
  roy/Leroy 0.5, fred/Alfred 0.6] → seuil réglable par constante, flou dès 4 caractères ; les
  résultats n'affichent que nom d'utilisateur, prénom et nom.
- [Énumération : la recherche parcourt tous les comptes, sans plafond, et le flou en renvoie plus
  par requête] → aucune donnée nouvelle exposée ; plafond suivi dans l'issue #40 (plafonner le nombre de comptes listés).
- [Coût : 2 normalisations et jusqu'à 2 `word_similarity` par compte, sans index] → balayage déjà
  accepté à l'échelle d'un voisinage (`archive/2026-11-01-liste-de-contacts/design.md:31`) ; si le
  volume l'exige, index GIN et fonction `unaccent` immuable (ADR 0018).
- [La collation de la base de production n'a pas été vérifiée ; elle règle `lower()` sur les
  majuscules accentuées et l'ordre alphabétique] → les tests tournent sur la même image
  `postgres:17` ; aucun scénario ne dépend de l'ordre de lettres accentuées.
- [Une requête de plus par recherche, pour normaliser le texte avant de compter] → requête sur un
  littéral, sans table.

## Migration Plan

Aucune migration : ni table, ni colonne, ni extension nouvelle. Retour arrière par revert du code.

## Espaces Unicode

`\s` ne couvre pas l'espace insécable (U+00A0) dans la base de test : la normalisation réduit aussi
U+00A0, U+2000 à U+200A, U+202F, U+205F et U+3000 (`text_search.SPACES`), fixé par un test.
