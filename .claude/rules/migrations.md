---
paths:
  - "application/migrations/**"
  - "application/models/**"
---

# Migrations Alembic

- Toute modification de schéma passe par `uv run flask db migrate -m "<message en français>"`, puis relecture de la révision générée, puis `uv run flask db upgrade`. Voir ADR 0002.
- Nom de fichier d'une révision : ASCII seulement, en minuscules, chiffres et `_` (`<rev>_<slug>.py`), sans accent (à, è, é, ê, ç…), espace ni autre caractère spécial, même si le message est en français. `flask db migrate` tire le nom du message : renommer aussitôt le fichier généré (ex. `1f84fa116ada_schemas_initiaux_outils_photos_et_prets.py`) ; la docstring garde ses accents. Alembic identifie une révision par sa variable `revision`, pas par son nom de fichier : le renommage ne la change pas.
- Ne jamais modifier une révision déjà commitée sur `main` : en créer une nouvelle.
- Une colonne non nulle ajoutée à une table existante a un `server_default`.
- Vérifier `upgrade()` **et** `downgrade()`.
- Pas de `db.create_all()` en dehors des tests.
