## 1. Schéma (passe *contract*)

- [x] 1.1 Retirer la colonne `username` de `models/user.py` ; générer la révision avec `UV_NO_CONFIG=1 uv run flask db migrate -m "Utilisateurs : suppression du nom d'utilisateur"`, renommer aussitôt le fichier en ASCII (`<rev>_utilisateurs_suppression_du_nom_d_utilisateur.py`) ; vérifier que `down_revision` vaut `43880597035b`
- [x] 1.2 Compléter la révision à la main selon le design : `upgrade` = `drop_constraint("uq_user_username")` puis `drop_column("username")` ; `downgrade` = colonne `VARCHAR(250)` nullable, remplie `'user' || id`, puis `uq_user_username` recréée ; `uv run flask db upgrade` passe et `uv run flask db check` est vide
- [x] 1.3 `tests/test_schema.py` : retirer `uq_user_username` des contraintes attendues de `user` ; ajouter un test aller-retour (compte créé à la tête, `downgrade` vers `43880597035b` lui donne `username = 'user<id>'` et recrée `uq_user_username`, `upgrade` revient sans la colonne) ; `uv run pytest tests/test_schema.py` passe
- [x] 1.4 Régénérer `docs/schema.md` avec `uv run paracelsus inject ../docs/schema.md` (ADR 0009) ; `uv run paracelsus inject ../docs/schema.md --check` passe et le diagramme n'a plus `username`

## 2. Références restantes

- [x] 2.1 `tests/test_auth.py:40` : ne plus lire `user.username`, vérifier le prénom et le nom seulement ; `uv run pytest tests/test_auth.py` passe
- [x] 2.2 `.claude/rules/templates.md` : dans la ligne du menu du compte, « nom d'utilisateur » devient « nom complet », sans toucher au reste du fichier (la ligne Couleurs appartient au changement `couleurs-des-boutons-et-liens`) ; comparé au commit qui précède cette tâche, `git diff <commit> -- .claude/rules/templates.md` ne montre que ce mot
- [x] 2.3 `git grep -n -i username -- application ':!application/migrations'` ne trouve que le jeton HTML `autocomplete="username"` des champs courriel et les tests qui prouvent l'absence du champ

## 3. Fin

- [x] 3.1 `/verifier` rend « terminé »
