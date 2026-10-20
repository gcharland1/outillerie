---
status: accepted
date: 2026-10-20
decision-makers: Gabriel Charland
---

# Flask, app factory et rendu serveur Jinja

## Contexte et problème

L'Outillerie est un site communautaire simple : formulaires, listes d'outils, comptes.
Il faut un framework web Python léger, testable, sans SPA à maintenir.

## Options considérées

* Flask avec app factory (`create_app`) et gabarits Jinja
* Django
* FastAPI + front JavaScript

## Décision

Option retenue : « Flask + app factory + Jinja », parce que la surface est petite, l'app factory
permet d'instancier l'app par test, et le rendu serveur évite un second projet front.

### Conséquences

* Bon, parce que les tests créent une app isolée via `create_app()`.
* Bon, parce que les gabarits héritent d'un `base.html` commun.
* Mauvais, parce que l'authentification, les formulaires et l'admin s'assemblent à la main (extensions Flask).
