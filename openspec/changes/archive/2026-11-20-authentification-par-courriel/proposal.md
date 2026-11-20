# Proposal

## Why

On se connecte aujourd'hui avec un nom d'utilisateur choisi à l'inscription, qu'il faut retenir en
plus du courriel. L'issue #38 fait du courriel le seul identifiant de connexion et retire le nom
d'utilisateur de la base, du code et de l'affichage ; le menu du compte affiche le nom complet.

Les décisions et leur source sont dans [questions.md](questions.md). Décision d'architecture :
ADR 0020 (`proposed`).

## What Changes

- **BREAKING** `/login` demande le courriel et le mot de passe, plus le nom d'utilisateur. Le
  courriel est comparé sans égard à la casse ni aux espaces autour ; message d'échec « Le courriel
  ou le mot de passe est invalide ». La protection contre l'énumération (même réponse, même
  hachage) est gardée.
- **BREAKING** `/register` ne demande plus de nom d'utilisateur ; le courriel est enregistré sans
  espaces autour.
- Le nom d'utilisateur disparaît de l'affichage : le menu du compte montre « Prénom Nom », les
  colonnes « Nom d'utilisateur » de la recherche, de « Mes contacts » et de l'accueil sont retirées,
  la page d'un contact a pour titre « Bob Gagnon ».
- La recherche d'utilisateurs ne compare plus que le prénom suivi du nom ; le courriel reste hors
  recherche.
- « Mes contacts » et la recherche trient par prénom, puis nom, sans égard à la casse ni aux
  accents, puis par ancienneté du compte.
- Schéma, en deux passes (ADR 0007) : cette PR rend `user.username` nullable et le code ne le lit
  ni ne l'écrit plus ; une PR suivante, après le déploiement, supprime la colonne et
  `uq_user_username`.

Hors périmètre : suppression de la colonne (PR suivante), limitation des essais de mot de passe,
inscription par courriel vérifié, champ public de distinction des homonymes, propriété `full_name`.

## Capabilities

### New Capabilities

### Modified Capabilities
- `authentification`: « Courriel unique », « Création de compte », « Connexion », « État de connexion dans la navigation ».
- `recherche`: « Correspondance des utilisateurs », « Informations affichées ».
- `contacts`: « Demandes reçues », « Liste de mes contacts », « Pastille des demandes en attente », « Page d'un contact ».
- `inventaire`: « Accès depuis la navigation ».
- `outils-des-contacts`: « Page « Trouver un outil » ».

## Impact

`models/user.py`, une révision Alembic, `app/auth.py`, `app/search.py`, `app/contacts.py`,
`app/text_search.py` (clé de tri), gabarits `base.html`, `login.html`, `sign_up.html`,
`search/results.html`, `contacts/*`, `docs/schema.md` (ADR 0009) ; tests : fixtures et fabriques
par courriel. La production ne contient que des comptes de test : aucune migration de données.
