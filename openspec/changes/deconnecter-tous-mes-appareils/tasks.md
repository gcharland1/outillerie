# Tasks

## 1. Action

- [x] 1.1 `profile.py` : `GET /profile/logout-all` (page de confirmation) et `POST /profile/logout-all` (rotation atomique, `end_session()`, redirection `/logged-out?reason=all-devices`, avis si le courriel est confirmé) ; `auth.logged_out` : motif `all-devices`
- [x] 1.2 Gabarits : carte sur `profile/show.html` avant « Supprimer mon compte », `profile/confirm_logout_all.html`
- [x] 1.3 Tests : carte, page de confirmation sans effet, rotation (autre client et cookie persistant refusés, appareil courant mené à la page de déconnexion), compte supprimé entre-temps, CSRF, GET sans effet, avis envoyé ou non selon la confirmation du courriel, contenu de l'avis

## 2. Règle

- [x] 2.1 `.claude/rules/templates.md` : toute action irréversible ou dangereuse passe par une page de confirmation

## 3. Fin

- [x] 3.1 `/verifier` rend « terminé »
