---
status: superseded by 0012
date: 2026-10-24
decision-makers: Gabriel Charland
---

# Protection CSRF par Flask-WTF

## Contexte et problème

La gestion des outils (issue #17) ajoute les premiers formulaires qui modifient des données
au-delà de la déconnexion : créer, modifier, retirer et remettre en circulation un outil.
Aucun formulaire ne porte de jeton CSRF ; seul `SameSite=Lax` (0006) empêche un site tiers
d'envoyer un `POST` avec le cookie de session, et il ne protège ni d'un sous-domaine du même
site ni d'un navigateur qui l'ignore. Changement OpenSpec : `openspec/changes/gestion-des-outils/`.

## Options considérées

* `CSRFProtect` de Flask-WTF, actif pour toute l'application
* `SameSite=Lax` seul, sans jeton
* Jeton écrit à la main (stocké dans la session, vérifié dans un `before_request`)

## Décision

Option retenue : « `CSRFProtect` de Flask-WTF », parce qu'il vérifie toute requête `POST`
sans code par route, qu'une route oubliée est protégée par défaut, et que son jeton signé vit
dans la session de Flask (0006) sans table ajoutée. Chaque formulaire `POST`, déconnexion
comprise, inclut `{{ csrf_token() }}` dans un champ caché. Seule la protection CSRF est
adoptée : les formulaires restent écrits en HTML dans les gabarits, sans classes WTForms ;
la validation des formulaires par WTForms reste à trancher par l'issue #12.

### Conséquences

* Bon, parce qu'une nouvelle route `POST` est protégée sans y penser.
* Bon, parce qu'un jeton écrit à la main (comparaison en temps constant, expiration, rotation) n'est
  pas à maintenir.
* Mauvais, parce qu'une dépendance s'ajoute (Flask-WTF et WTForms) pour une seule fonction.
* Mauvais, parce que les tests doivent fournir un jeton ou désactiver la protection
  (`WTF_CSRF_ENABLED = False`) ; un test dédié doit alors prouver qu'un `POST` sans jeton est refusé.
* Mauvais, parce qu'un formulaire envoyé après la fin de la session (30 minutes d'inactivité, ou
  fermeture du navigateur pour un visiteur) est refusé (400) : son jeton a disparu avec la
  session, sa durée propre étant désactivée (`WTF_CSRF_TIME_LIMIT = None`).
