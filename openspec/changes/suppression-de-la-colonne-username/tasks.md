## 1. Révision

- [x] 1.1 Retirer de `migrations/env.py` la fonction `include_object` et ses deux branchements (modes online et offline)
- [x] 1.2 `uv run flask db migrate -m "Utilisateurs : suppression de la colonne du nom d'utilisateur"` sur une base dédiée à jour ; relire la révision, la mettre au format du design (`batch_alter_table`, `downgrade` qui remplit `'user' || id` et recrée `uq_user_username`) et renommer le fichier en ASCII ; `down_revision` est `916cc286d588`
- [x] 1.3 Sur une base dédiée : `uv run flask db upgrade`, puis `uv run flask db check` est vide

## 2. Tests

- [x] 2.1 `tests/test_schema.py` : retirer `uq_user_username` des contraintes attendues ; le test de la colonne non mappée vérifie que la colonne `username` n'existe pas en base
- [x] 2.2 Test d'aller-retour : un compte actif et un compte supprimé, `downgrade` à `916cc286d588`, `username = 'user' || id` pour les deux et `uq_user_username` présente, puis `upgrade` et colonne absente ; `uv run pytest tests/test_schema.py` passe
- [x] 2.3 `git grep -n -i username -- application ':!application/migrations/versions'` ne trouve que `autocomplete="username"` (`login.html`, `sign_up.html`) et les tests qui prouvent l'absence du champ ou de la colonne

## 3. Fin

- [x] 3.1 `/verifier` rend « terminé »
