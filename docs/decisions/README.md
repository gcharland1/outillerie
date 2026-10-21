# Décisions d'architecture (ADR)

Format [MADR 4.0](https://adr.github.io/madr/), gabarit minimal : [adr-template.md](adr-template.md).
Créer un ADR avec le skill `/adr <titre>`.

## Quand écrire un ADR

Quand un choix est coûteux à défaire ou contraint le code futur : dépendance, schéma de données,
structure de l'app, outil de dev, convention transverse. Un détail d'implémentation local n'en a pas besoin.

## Règles

* Fichier `NNNN-titre-en-kebab.md`, numéro croissant, jamais réutilisé.
* `status` : `proposed` → `accepted` ; plus tard `deprecated` ou `superseded by NNNN`.
* Un ADR `accepted` est immuable : pour changer d'avis, écrire un nouvel ADR qui le remplace
  et mettre à jour le `status` de l'ancien (seule modification permise).
* Un changement OpenSpec qui tranche un choix d'architecture crée ou cite un ADR.

## Index

| #    | Décision                                                                 | Statut   |
|------|--------------------------------------------------------------------------|----------|
| 0000 | [Consigner les décisions avec MADR](0000-consigner-les-decisions-avec-madr.md) | accepted |
| 0001 | [Flask, app factory et rendu serveur Jinja](0001-flask-app-factory-et-rendu-serveur.md) | accepted |
| 0002 | [PostgreSQL, SQLAlchemy et migrations Alembic](0002-postgresql-sqlalchemy-et-alembic.md) | accepted |
| 0003 | [uv et Docker Compose pour le développement](0003-uv-et-docker-compose.md) | accepted |
| 0004 | [OpenSpec pour le développement piloté par spec](0004-openspec.md) | accepted |
| 0005 | [Archiver les sessions Claude dans le dépôt](0005-archiver-les-sessions-claude.md) | accepted |
| 0006 | [Sessions dans le cookie signé de Flask, expiration d'inactivité](0006-sessions-dans-le-cookie-signe-de-flask.md) | accepted |
| 0007 | [Règles d'évolution du schéma de persistance](0007-regles-d-evolution-du-schema-de-persistance.md) | accepted |
| 0008 | [Photos des outils en `bytea`](0008-photos-des-outils-en-bytea.md) | accepted |
| 0009 | [Diagramme du schéma généré par paracelsus](0009-diagramme-du-schema-genere-par-paracelsus.md) | accepted |
