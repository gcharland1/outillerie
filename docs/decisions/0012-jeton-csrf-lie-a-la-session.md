---
status: accepted
date: 2026-10-24
decision-makers: Gabriel Charland
---

# Protection CSRF par Flask-WTF, jeton lié à la session

## Contexte et problème

La gestion des outils (issue #17) ajoute les premiers formulaires qui modifient des données
au-delà de la déconnexion : créer, modifier, retirer et remettre en circulation un outil.
`SameSite=Lax` (0006) empêche un site tiers d'envoyer un `POST` avec le cookie de session, mais
ne protège ni d'un sous-domaine du même site ni d'un navigateur qui l'ignore. Remplace 0010, dont
la décision tient toujours mais qui annonçait à tort qu'un jeton de visiteur vit jusqu'à la
fermeture du navigateur : Flask refuse tout cookie de session signé depuis plus de
`PERMANENT_SESSION_LIFETIME`, permanent ou non (`flask/sessions.py`, `open_session`).
Changement OpenSpec : `openspec/changes/gestion-des-outils/`.

## Options considérées

* `CSRFProtect` de Flask-WTF, jeton valable autant que la session (`WTF_CSRF_TIME_LIMIT = None`)
* `CSRFProtect` de Flask-WTF, durée de jeton par défaut (une heure après le rendu de la page)
* `SameSite=Lax` seul, sans jeton
* Jeton écrit à la main (stocké dans la session, vérifié dans un `before_request`)

## Décision

Option retenue : « `CSRFProtect` de Flask-WTF, jeton valable autant que la session », parce
qu'il vérifie toute requête `POST` sans code par route, qu'une route oubliée est protégée par
défaut, et que son jeton signé vit dans la session de Flask (0006) sans table ajoutée. Chaque
formulaire `POST`, déconnexion comprise, inclut `{{ csrf_token() }}` dans un champ caché. Seule
la protection CSRF est adoptée : les formulaires restent écrits en HTML dans les gabarits, sans
classes WTForms ; la validation des formulaires par WTForms reste à trancher par l'issue #12.

Le jeton n'a pas de durée propre : il vaut tant que la session qui le porte, soit 30 minutes
d'inactivité pour un utilisateur connecté, dont le cookie est re-signé à chaque requête, et
30 minutes depuis l'ouverture de `/login` ou `/register` pour un visiteur, dont le cookie n'est
signé qu'à la création du jeton. La durée par défaut refuserait une page rendue il y a plus d'une
heure dans un onglet, alors qu'un autre onglet a gardé la session ouverte.

### Conséquences

* Bon, parce qu'une nouvelle route `POST` est protégée sans y penser.
* Bon, parce qu'un jeton écrit à la main (comparaison en temps constant, expiration, rotation)
  n'est pas à maintenir.
* Bon, parce que la validité du jeton suit une seule durée, `PERMANENT_SESSION_LIFETIME`.
* Mauvais, parce qu'une dépendance s'ajoute (Flask-WTF et WTForms) pour une seule fonction.
* Mauvais, parce que les tests doivent fournir un jeton ou désactiver la protection
  (`WTF_CSRF_ENABLED = False`) ; un test dédié doit alors prouver qu'un `POST` sans jeton est refusé.
* Mauvais, parce qu'une page de connexion ou d'inscription ouverte plus de 30 minutes est refusée
  à l'envoi (400, « Rechargez la page et réessayez ») : la prolonger demanderait une interface de
  session propre aux visiteurs et un nouvel ADR.
