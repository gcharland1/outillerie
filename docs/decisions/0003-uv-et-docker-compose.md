---
status: accepted
date: 2026-10-20
decision-makers: Gabriel Charland
---

# uv et Docker Compose pour le développement

## Contexte et problème

Il faut des dépendances reproductibles et un moyen simple de lancer l'app avec sa base.

## Options considérées

* uv (`pyproject.toml` + `uv.lock` commité) et Docker Compose (`app` + `db`)
* pip + `requirements.txt`
* Poetry

## Décision

Option retenue : « uv + Docker Compose », parce que `uv sync --locked` donne le même
environnement en local, en CI et dans l'image Docker, et que Compose démarre l'app et Postgres ensemble.

Python 3.13, fixé par `application/.python-version`. Les outils de dev (pytest, ruff) vivent
dans le groupe `dev`, exclu de l'image (`UV_NO_DEV=1`).

### Conséquences

* Bon, parce que `uv.lock` rend chaque build reproductible.
* Mauvais, parce que toute modification de dépendance exige `uv lock` et le commit du lock.
