# Questions — recherche-sans-accents (issue #39)

Issue : « Une recherche pour "Fred" ne trouve pas "Fréd" » ; la recherche d'outil ou d'utilisateur
doit ignorer accents et majuscules. Réponses fusionnées de quatre angles d'exploration (code, specs
et ADR, cas limites, antériorité). Chemins de code relatifs à `application/`. « Base de dev » :
`SELECT` en lecture seule dans `outillerie-db-1` (PostgreSQL 17.11, `en_US.utf8`).

## Décidé par le dépôt ou la convention

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 1 | Où « Fred » échoue-t-il ? | Recherche d'utilisateurs seulement : `icontains` sans `unaccent` sur nom d'utilisateur, prénom, nom, prénom + nom. La recherche d'outils applique déjà `unaccent` au champ et au motif | Sourced `app/search.py:38-52`, `app/catalog.py:312-331` ; base de dev `unaccent('Fréd') ILIKE unaccent('%fred%')` = vrai | dépôt |
| 2 | Champs de recherche dans le périmètre | Barre de navigation en type « Utilisateur ». Le type « Outil » et le filtre de « Trouver un outil » / page d'un contact sont déjà conformes (test du sens inverse à ajouter). « Mes contacts » et « Gérer mes outils » n'ont pas de filtre texte. Connexion et unicité des noms d'utilisateur hors périmètre (ce ne sont pas des recherches ; « fred » ≡ « fréd » y ouvrirait l'usurpation) | Sourced `templates/base.html:35`, `templates/tools/_cards.html:2`, `app/contacts.py:171`, `app/tools.py:194`, `app/auth.py:33-38` | dépôt |
| 3 | Accents ignorés dans les deux sens | Oui : `unaccent` des deux côtés, majuscules accentuées comprises (« FRÉD ») ; un scénario par sens | Sourced `app/catalog.py:314-322` ; base de dev | convention |
| 6 | Tri des utilisateurs | Inchangé (`lower(username)`, `id`) ; la collation `en_US.utf8` range déjà « Émile » près de « emma ». Pas de scénario de tri accentué, qui dépendrait de la collation | Sourced `app/search.py:51` ; base de dev. Partial : collation de prod et CI non vérifiée | convention |
| 7 | Mécanisme | `unaccent` en SQL, comme les outils ; ILIKE à jokers échappés ; extension déjà installée (`9654b00a97c3`) ; ni migration, ni index (la sous-chaîne `%x%` n'utilise pas d'index B-tree, et le balayage complet de `user` est déjà accepté par liste-de-contacts). Normalisation Python écartée : NFKD ne traite ni ß ni œ, règles différentes des outils | Sourced ADR 0016:44-51,66-69, `migrations/versions/9654b00a97c3_extensions_de_recherche_floue.py:20-21`, `openspec/changes/archive/2026-11-01-liste-de-contacts/design.md:31` | convention |
| 8 | Nouvel ADR | Remplacé par la décision #11 : ADR 0018 qui remplace l'ADR 0016 (règles de tous les champs de recherche). Il lève aussi le non-objectif de liste-de-contacts, posé par l'agent sans question à l'utilisateur, et justifie l'absence d'index pour une recherche qui balaie toute la table `user` (la raison « outils des contacts seulement » de l'ADR 0016 ne vaut pas ici) | Sourced ADR 0016:50-51,62-69, `docs/decisions/README.md` (ADR `accepted` immuable), `liste-de-contacts/design.md:29-30`, `docs/sessions/2026-10-25-f7afc990.md:1883,1907` | utilisateur |
| 9 | Minimum de 3 caractères | Remplacé par la grille : compté sur le texte normalisé en SQL, car « --- » se normalisait en une espace et listait tous les comptes ; ferme aussi les accents combinants empilés. Décidé par l'utilisateur | Sourced `app/search.py:9,24`, `templates/base.html:35` ; base de dev | convention |
| 10 | `unaccent` en test | Déjà créé par `mock_app` et vérifié par `test_schema.py` ; commentaire de `conftest.py:48` à étendre aux utilisateurs | Sourced `tests/conftest.py:44-50`, `tests/test_schema.py:43` | dépôt |
| 13 | Prénom + nom | `unaccent` sur les quatre expressions (dont la concaténation) et sur le motif, même forme `or_` | Sourced `app/search.py:44-49` | convention |
| 14 | Courriel hors recherche | Confirmé par le code, sans scénario ni test : en ajouter un | Sourced `app/search.py:44-49`, `tests/test_search.py` | convention |
| 15 | Message « Aucun utilisateur ne correspond » | Affiche le texte saisi, accents compris ; inchangé | Sourced `app/search.py:18,33` | dépôt |
| 16 | Emoji, `™`, `½` | Passent par `unaccent` sans règle particulière ; aucun scénario | Sourced base de dev | convention |
| 17 | Spec des outils, « contient le texte tel quel » | Remplacé par la grille : delta MODIFIED « Ordre des outils », qui renvoie aux règles du filtre. Décidé par l'utilisateur | Sourced `openspec/specs/outils-des-contacts/spec.md:187-190`, `app/catalog.py:317` | convention |
| 19 | Champs comparés et tri des utilisateurs (flou) | Deux expressions : nom d'utilisateur et prénom + nom (couvre prénom seul, nom seul et « gagnon bob »). Tri : sous-chaîne dans l'une d'elles, puis meilleur des deux scores, puis nom d'utilisateur sans égard à la casse, puis id ; aucun champ ne prime. Le scénario « Ordre des résultats » vaut pour des correspondances égales ; scénarios « gagne » → Gagné avant Gagnon, « fred » → Fred avant Alfred | Sourced `app/search.py:44-51`, `app/catalog.py:312-331` ; sortie psql | convention |
| 20 | Module commun | `app/text_search.py`, sans Blueprint (comme `catalog.py`, `photos.py`) : normalisation, échappement en SQL après `unaccent`, sous-chaîne et score ; `catalog._text_search` migre dessus. ADR 0011 ne règle qu'un module par Blueprint | Sourced ADR 0011:28-31, `app/search.py:5` ; sortie psql (échappement après `unaccent` vérifié) | convention |
| 21 | Tests cassés | Aucun : « b_b » fait 3 caractères et le flou des utilisateurs commence à 4 (décision B/F), le cas reste | Sourced `tests/test_search.py:59-68` ; sortie psql | convention |
| 22 | Spec « Correspondance des utilisateurs » | Delta MODIFIED : « contient le texte ou lui ressemble », sans égard à la casse, aux accents, aux tirets ni aux espaces multiples, formulé comme la spec outils-des-contacts ; « Ordre des résultats » en MODIFIED | Sourced `openspec/specs/recherche/spec.md:41-65` | convention |
| 18 | Chevauchement avec `page-d-accueil` (issue #3) | Ce changement ne touche ni `recherche/spec.md` ni `search.py` d'après son `questions.md` | Sourced `openspec/changes/page-d-accueil/questions.md` (poste principal, non commité) | dépôt |

## Décidé par l'utilisateur

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 5 | Sous-chaîne sans accents seulement, ou aussi la ressemblance floue de l'ADR 0016 ? | Aussi la ressemblance floue : même règle que les outils, fautes de frappe comprises ; tri et seuil à revoir pour des noms de personnes (second passage) | Sourced ADR 0016:62-63 ; base de dev `word_similarity('fred','alfred')` = 0.6 > `FUZZY_THRESHOLD` 0.5 | utilisateur |
| 11 | Jokers pleine chasse : `unaccent` change `％ ＿ ＼` en `% _ \` après l'échappement Python, donc `％` correspond à tout (déjà vrai pour les outils) | Corriger outils et utilisateurs par une fonction commune qui échappe après `unaccent` : « %%% » (ASCII ou pleine chasse) ne trouve que les outils ou comptes qui contiennent ces caractères. Les règles valent pour tout champ de recherche et vont dans un ADR ; l'ADR 0016 étant immuable, un nouvel ADR 0018 le remplace (`superseded by 0018`) | Sourced `app/catalog.py:316,334-335` ; base de dev `'abcdef' ILIKE unaccent('%％%')` = vrai | utilisateur |
| 4 | Tiret ≡ espace, espaces internes multiples | Oui, les deux, pour tout champ de recherche : la fonction commune remplace les tirets par une espace et réduit les espaces multiples, des deux côtés, après `unaccent`. Le flou en couvrait déjà une partie (`word_similarity('jean pierre','jean-pierre')` = 1.0) sans garantie pour la sous-chaîne | Sourced base de dev (`unaccent` ne les touche pas), `app/search.py:18` | utilisateur |

| B/F | Seuil et longueur minimale du flou pour des noms de personnes | Constantes propres aux utilisateurs : flou dès 4 caractères, seuil 0.5 ; à 3 caractères, sous-chaîne normalisée seule. Outils inchangés (3 caractères, 0.5) | Sourced sortie psql : à 3 caractères, 2 trigrammes sur 4 suffisent (« gax » → Gagnon = 0.5) ; faux positifs martin/martel 0.571, marie/mario 0.667, roy/leroy 0.5 ; vrais positifs gagnion/gagnon 0.5, tremblai/tremblay 0.778 ; `FUZZY_MIN_LENGTH` = 3 (`app/catalog.py:26`) | utilisateur |
| N1 | Plafond du nombre de comptes listés (aucun aujourd'hui, `.all()`) | Non dans ce changement ; risque noté dans le design, issue #40 (plafonner le nombre de comptes listés) | Sourced `app/search.py:40-52` | utilisateur |

## Suivi hors périmètre

- Plafond du nombre de comptes listés par la recherche d'utilisateurs (N1) : issue #40 (plafonner le nombre de comptes listés).

- Unicité des noms d'utilisateur exacte, sans normalisation NFC : « Fréd » en NFC et en NFD peuvent être deux comptes distincts (Sourced `app/auth.py:27-33`, `models/user.py:10`).
