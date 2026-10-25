---
status: accepted
date: 2026-10-24
decision-makers: Gabriel Charland
---

# Une Blueprint par fonctionnalité

## Contexte et problème

Toutes les routes vivent dans `create_app()` (`app/__init__.py`), ce qui suffisait à
l'authentification. La gestion des outils (issue #17) en ajoute six ou sept, et chaque
fonctionnalité suivante (prêts, photos) en ajoutera d'autres : la fabrique grossirait sans
limite. Complète 0001 sans le remplacer. Changement OpenSpec : `openspec/changes/gestion-des-outils/`.

## Options considérées

* Une Blueprint Flask par fonctionnalité, enregistrée par `create_app()`
* Routes dans `create_app()`, comme aujourd'hui
* Modules de vues importés par la fabrique, sans Blueprint (`app.add_url_rule`)

## Décision

Option retenue : « une Blueprint par fonctionnalité », parce qu'elle donne à chaque
fonctionnalité son module, son préfixe d'URL et son espace de noms d'`url_for`, et que
`create_app()` se réduit à configurer et enregistrer. Règles :

* Un module `app/<fonctionnalite>.py` par Blueprint, nommé en anglais (`auth`, `tools`) ;
  un paquet seulement quand le module devient trop gros.
* `create_app()` garde la configuration, les extensions, les hooks globaux (`after_request`,
  `user_loader`) et `index`, puis enregistre les Blueprints.
* Les routes d'authentification passent dans la Blueprint `auth` ; leurs URL ne changent pas,
  leurs noms deviennent `auth.login`, `auth.register`, etc.

### Conséquences

* Bon, parce qu'une fonctionnalité se lit et se teste dans un seul module.
* Bon, parce que le préfixe d'URL et l'espace de noms évitent les collisions de routes.
* Mauvais, parce que chaque `url_for` et `login_manager.login_view` doivent nommer la Blueprint ;
  un nom oublié lève `BuildError` à l'exécution, que seuls les tests attrapent.
* Mauvais, parce que le déplacement de l'authentification touche des routes qui marchent, sans
  gain fonctionnel.
