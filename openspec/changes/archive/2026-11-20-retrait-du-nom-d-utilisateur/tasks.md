## 1. Modèle (première PR de la passe *contract*)

- [x] 1.1 Retirer la colonne `username` de `models/user.py` ; aucune révision ne touche la colonne (question 9)
- [x] 1.2 `migrations/env.py` : `include_object` écarte `user.username` et `uq_user_username` de l'autogénération, en modes online et offline ; `uv run flask db upgrade` passe et `uv run flask db check` est vide
- [x] 1.3 `tests/test_schema.py` : `uq_user_username` reste dans les contraintes attendues de `user` ; un test vérifie que la colonne existe en base, n'est pas mappée et qu'un `User` s'insère ; `uv run pytest tests/test_schema.py` passe
- [x] 1.4 Régénérer `docs/schema.md` avec `uv run paracelsus inject ../docs/schema.md` (ADR 0009) ; `uv run paracelsus inject ../docs/schema.md --check` passe et le diagramme n'a plus `username`

## 2. Références restantes

- [x] 2.1 `tests/test_auth.py:40` : ne plus lire `user.username`, vérifier le prénom et le nom seulement ; `uv run pytest tests/test_auth.py` passe
- [x] 2.2 `.claude/rules/templates.md` : dans la ligne du menu du compte, « nom d'utilisateur » devient « nom complet », sans toucher au reste du fichier (la ligne Couleurs appartient au changement `couleurs-des-boutons-et-liens`) ; comparé au commit qui précède cette tâche, `git diff <commit> -- .claude/rules/templates.md` ne montre que ce mot
- [x] 2.3 `git grep -n -i username -- application ':!application/migrations/versions'` ne trouve que le jeton HTML `autocomplete="username"` des champs courriel, les tests qui prouvent l'absence du champ, le filtre de `migrations/env.py` et le test de la colonne non mappée

## 3. Fin

- [x] 3.1 `/verifier` rend « terminé »
