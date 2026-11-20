# Tasks

## 1. Module commun

- [x] 1.1 `app/text_search.py` : `normalized`, `contains` (échappement en SQL après normalisation, `ESCAPE '\'`), `similarity` ; vérifier par des tests pytest sur la base de test : « Fréd » et « FRÉD » contiennent « fred », « Jean-Pierre » contient « jean pierre », « bob    gagnon » se normalise en « bob gagnon », `％％％`, `＿＿＿` et `＼` ne correspondent qu'à un texte qui contient `%%%`, `___` ou `\`, et l'espace insécable (question ouverte du design)

## 2. Recherche d'outils

- [x] 2.1 `catalog._text_search` passe par `text_search` ; `_escape_like` supprimé ; constantes et tri inchangés ; vérifier par des tests pytest les nouveaux scénarios de « Filtre par texte » (« Accents du texte ignorés », « Tiret et espace équivalents », « Espaces multiples », « Joker pleine chasse cherché tel quel », « Joker présent dans une description ») et « Contenu normalisé en tête » d'« Ordre des outils » et que les tests existants de `test_catalog.py` et `test_tools_of_contacts.py` passent toujours

## 3. Recherche d'utilisateurs

- [x] 3.1 `search.results` compte le minimum de 3 caractères sur le texte normalisé en SQL, avant le choix du type ; vérifier par des tests pytest « Tirets seuls », « Tirets typographiques seuls », « Accents sans lettre », « Tirets seuls en type Outil » et les tests existants de texte trop court
- [x] 3.2 `search._matching_users` : `contains` et, dès `USER_FUZZY_MIN_LENGTH` (4, compté sur le texte normalisé), `similarity` au seuil `USER_FUZZY_THRESHOLD` (0.5) sur `username` et prénom + nom ; tri contient, `greatest` des scores, `lower(username)`, `id` ; docstring à jour ; vérifier par des tests pytest chaque scénario de « Correspondance des utilisateurs », dont « Contenu avant ressemblance », « Pas de ressemblance sous 4 caractères » et « Courriel non cherché »
- [x] 3.3 Garder le cas « b_b » de `test_wildcards_are_searched_literally` (3 caractères : le flou, qui commence à 4, ne s'applique pas), et étendre le commentaire de `tests/conftest.py` sur `unaccent` à la recherche d'utilisateurs ; vérifier que `uv run pytest tests/test_search.py` passe

## 4. Vérification

- [x] 4.1 Vérifier à la main dans `docker compose up --build` : « fred » trouve « Fréd » dans la recherche d'utilisateurs et « ％％％ » ne liste rien dans les deux recherches
- [x] 4.2 Lancer `/verifier` ; il doit rendre « terminé »

## Workflow follow-up

- Archiver le changement (`/opsx:archive`) une fois la PR mergée.
