---
status: accepted
date: 2026-10-20
decision-makers: Gabriel Charland
---

# PostgreSQL, SQLAlchemy et migrations Alembic

## Contexte et problème

Les comptes et les outils partagés doivent persister. Le schéma va évoluer souvent ;
chaque évolution doit être reproductible en dev, en CI et en production.

## Options considérées

* PostgreSQL 17 + SQLAlchemy 2 (Flask-SQLAlchemy) + Flask-Migrate (Alembic)
* SQLite + SQLAlchemy
* PostgreSQL avec SQL écrit à la main

## Décision

Option retenue : « PostgreSQL + SQLAlchemy + Alembic », parce que Postgres est déjà le service
`db` de `compose.yaml`, et que les révisions Alembic versionnent le schéma avec le code.

Les révisions Alembic sont la seule source du schéma : pas de `db.create_all()` hors des tests.

### Conséquences

* Bon, parce que dev, CI et production partagent le même moteur.
* Mauvais, parce que les tests qui touchent la base exigent un Postgres (service dans la CI).
