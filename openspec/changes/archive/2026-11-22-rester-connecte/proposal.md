# Proposal

## Why

Toute session se ferme après 30 minutes d'inactivité (ADR 0006) : un utilisateur qui revient sur son
propre appareil doit se reconnecter à chaque visite. L'issue #56 demande une case « Rester connecté
sur cet appareil » qui supprime la déconnexion automatique sur l'appareil où elle est cochée.

Les décisions et leur source sont dans [questions.md](questions.md). Décisions d'architecture :
ADR 0006 (remplacé), ADR 0007 (colonne ajoutée seule), ADR 0012 (jeton CSRF lié à la session,
inchangé), ADR 0015 (`Secure` hors développement), ADR 0023 (compte supprimé) ; nouvel ADR 0028,
« Rester connecté par le cookie remember de Flask-Login et une version de session », `proposed`,
qui remplace l'ADR 0006.

## What Changes

- Case « Rester connecté sur cet appareil », décochée par défaut, sur la page de connexion.
- Cochée : un cookie persistant garde l'utilisateur connecté 30 jours après sa dernière visite,
  au-delà de l'expiration de 30 minutes ; aucune redirection d'expiration dans ses pages.
- Décochée : comportement actuel (30 minutes d'inactivité), et un cookie persistant laissé sur
  l'appareil par une connexion antérieure est effacé.
- « Me déconnecter » et la suppression du compte effacent le cookie persistant de l'appareil.
- Colonne `user.session_version` (entier, 0 par défaut), portée par l'identifiant de session : la
  faire changer invalidera toutes les sessions du compte (issue #61). À la version 0, l'identifiant
  reste celui d'aujourd'hui : les sessions en cours survivent au déploiement et à un retour arrière.
- Limite acceptée : le serveur n'impose pas les 30 jours ; une copie volée du cookie persistant reste
  valide jusqu'à la suppression du compte ou un changement de `session_version`.

Hors périmètre : « Déconnecter tous mes appareils » (issue #61) ; prolonger le jeton CSRF d'une
session restée connectée (un formulaire ouvert plus de 30 minutes reste refusé, question 3) ;
changement ou réinitialisation du mot de passe.

Closes #56.

## Capabilities

### New Capabilities

### Modified Capabilities
- `authentification` : case « Rester connecté » à la connexion ; déconnexion qui efface le cookie
  persistant ; expiration par inactivité et avis d'expiration réservés aux sessions sans cookie
  persistant ; protection du cookie persistant ; sessions d'un compte supprimé.
- `deploiement` : le cookie persistant porte `Secure` hors développement.
- `profil` : la suppression du compte efface le cookie persistant.

## Impact

`application/app/auth.py`, `application/app/__init__.py` (configuration du cookie persistant,
chargeur d'utilisateur, prolongation), `application/app/profile.py`, `application/models/user.py`,
une révision Alembic, gabarits `login.html` et `base.html`, `docs/schema.md`, `docs/decisions/`
(ADR 0028, statut de l'ADR 0006), tests. Aucune dépendance ajoutée : Flask-Login est déjà déclaré.
