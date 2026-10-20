---
paths:
  - "application/migrations/**"
  - "application/models/**"
---

# Migrations Alembic

- Toute modification de schéma passe par `uv run flask db migrate -m "<message en français>"`, puis relecture de la révision générée, puis `uv run flask db upgrade`. Voir ADR 0002.
- Ne jamais modifier une révision déjà commitée sur `main` : en créer une nouvelle.
- Une colonne non nulle ajoutée à une table existante a un `server_default`.
- Vérifier `upgrade()` **et** `downgrade()`.
- Pas de `db.create_all()` en dehors des tests.
