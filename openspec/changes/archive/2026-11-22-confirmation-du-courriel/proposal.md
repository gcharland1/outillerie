# Proposal

## Why

N'importe qui peut créer un compte avec une adresse qui n'est pas la sienne, puis emprunter ou prêter
sous cette identité : rien ne prouve que l'utilisateur reçoit les courriels de son adresse. L'issue
#50 demande un courriel de confirmation à l'inscription, et de réserver les prêts aux comptes
confirmés. L'app n'a jamais envoyé de courriel.

Les décisions et leur source sont dans [questions.md](questions.md). Décisions d'architecture :
ADR 0006 et 0012 (jetons signés, CSRF), ADR 0007 (colonnes ajoutées nullables), ADR 0017 (retour
arrière d'image), ADR 0020 (courriel identifiant, énumération acceptée), ADR 0022 (couleurs), ADR
0023 (compte supprimé) ; nouvel ADR 0027, « Confirmer le courriel par un lien signé envoyé en SMTP »,
`proposed`.

## What Changes

- Envoi de courriels par SMTP (`smtplib`), configuré par variables d'environnement ; hors
  `development`, l'app refuse de démarrer sans elles ; en développement sans SMTP, le courriel est
  écrit dans le journal ; en tests, il est gardé en mémoire.
- Colonnes `user.email_confirmed_at` et `user.email_confirmation_sent_at`, nullables ; les comptes
  existants restent non confirmés.
- À l'inscription, après la création du compte, un courriel contient un lien signé valide 30 jours.
  Le lien ouvre une page « Confirmer mon courriel » dont le bouton confirme le compte par un POST.
- Un compte non confirmé ne peut ni demander un emprunt ni accepter une demande : « Emprunter » et
  « Accepter » sont grisés, le serveur refuse un envoi forgé. Refuser, suivre un prêt en cours, gérer
  ses outils et ses contacts restent permis.
- Pastille sur « Mon profil », comptée dans celle du nom ; bandeau en tête de « Mon profil » avec
  « Renvoyer le courriel », au plus une fois toutes les 5 minutes.
- Le jeton est masqué dans les lignes de requête journalisées par l'app.

Hors périmètre : libérer l'adresse d'un compte jamais confirmé (issue de suivi, question 16) ; taire
« Le courriel est déjà utilisé » à l'inscription (question 17) ; limiter le débit des inscriptions
(question 18) ; changer de courriel ; le choix du fournisseur SMTP, le DNS (SPF, DKIM) et le `.env`
du serveur, faits par l'utilisateur avant le merge (question 1).

Closes #50.

## Capabilities

### New Capabilities
- `confirmation-du-courriel` : envoi du courriel de confirmation, lien et page de confirmation,
  renvoi, et actions réservées à un compte confirmé.

### Modified Capabilities
- `authentification` : « Création de compte » envoie le courriel de confirmation.
- `profil` : pastille de « Mon profil » ; bandeau et renvoi dans « Informations du profil ».
- `contacts` : la pastille du nom compte aussi celle de « Mon profil ».
- `outils-des-contacts` : « Emprunter » grisé pour un compte non confirmé.
- `deploiement` : configuration SMTP exigée hors développement.

## Impact

`application/app/` (nouveau module d'envoi, `auth.py`, `profile.py`, `loans.py`, `__init__.py`),
gabarits (`base.html`, `profile/show.html`, carte d'un outil, « Mes prêts », accueil, nouvelle page de
confirmation), `application/models/user.py`, une révision Alembic, `application/pyproject.toml`
(`itsdangerous` en dépendance directe), `compose.yaml`, `.env.example`, tests. Livré avec
`tests-une-seule-fois-par-livraison`, après `suppression-de-la-colonne-username` ; sa révision part
de celle de ce dernier.
