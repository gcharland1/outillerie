# Proposal

## Why

Le cookie persistant de « Rester connecté » ne porte pas de date : une copie volée reste valide
jusqu'à la suppression du compte ou une rotation de `user.session_version`, qu'aucune fonction ne fait
encore (ADR 0028). L'issue #61 demande une action « Déconnecter tous mes appareils ».

Décisions et sources dans [questions.md](questions.md). ADR suivis : 0001, 0012, 0017, 0022, 0027,
0028. Aucun nouvel ADR.

## What Changes

- Carte « Déconnecter tous mes appareils » sur « Mon profil », avant « Supprimer mon compte », qui
  mène à une page de confirmation.
- La confirmation fait tourner `session_version` : toutes les sessions et tous les cookies persistants
  du compte deviennent invalides, appareil courant compris, qui arrive sur
  `/logged-out?reason=all-devices`.
- Un avis sans lien part à l'adresse du compte, si elle est confirmée ; un échec d'envoi ne bloque rien.
- Règle des gabarits : toute action irréversible ou dangereuse passe par une page de confirmation.

Hors périmètre : changement et réinitialisation du mot de passe (issue à ouvrir à part).

Closes #61.

## Capabilities

### New Capabilities

### Modified Capabilities
- `authentification` : motif `all-devices` de la page de déconnexion ; révocation de toutes les sessions.
- `profil` : carte, page de confirmation et effet de « Déconnecter tous mes appareils ».

## Impact

`app/profile.py`, `app/auth.py`, gabarits `profile/show.html` et `profile/confirm_logout_all.html`,
`.claude/rules/templates.md`, tests. Aucune migration.
