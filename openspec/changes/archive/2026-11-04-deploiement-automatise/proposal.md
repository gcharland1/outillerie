# Proposal

## Why

Chaque mise en production se fait à la main sur le serveur (`docker compose -p outillerie-prod up -d
--build`), sans tests sur le commit mergé, sans sauvegarde ni retour arrière. L'issue #5 demande que
chaque PR mergée sur `main` dont la suite de tests passe soit déployée seule. Décisions consignées
dans `questions.md` et l'ADR 0017.

## What Changes

- `ci.yml` tourne aussi sur `push` vers `main` : le commit mergé est testé (lint, migrations, pytest,
  diagramme, specs).
- Un timer systemd sur le serveur, toutes les 5 minutes, cherche par l'API GitHub le plus récent
  commit de `main` dont la CI est verte et qui descend du commit déployé. S'il en trouve un : sauvegarde
  `pg_dump`, checkout du commit, build d'une image étiquetée par son SHA, `up --wait`.
- Si la nouvelle version ne devient pas saine, le script relance la version précédente, sans
  downgrade Alembic, et ne retente plus ce SHA.
- Le script pose sur le commit un statut GitHub `deploiement` (succès ou échec, sans détail) ; le
  détail va dans journald.
- `compose.yaml` : l'image de l'app est nommée et étiquetée (`outillerie-app:${APP_TAG:-dev}`), l'app
  a un healthcheck, `app` et `db` redémarrent seuls (`restart: unless-stopped`).
- Hors `development`, l'app refuse de démarrer sans `FLASK_SECRET_KEY` ou avec la clé d'exemple
  `dev-seulement` (report vers l'issue #5 d'une relecture du 2026-10-20).
- Nouveau dossier `deploiement/` : script de déploiement, unités systemd, procédure d'installation et
  d'amorçage.

## Capabilities

### New Capabilities
- `livraison-continue`: comment un commit de `main` passe en production — conditions pour le
  déployer, sauvegarde, vérification, retour arrière, statut publié, garde-fous du serveur.

### Modified Capabilities
- `deploiement`: image de l'app étiquetée, healthcheck de l'app, redémarrage automatique des
  services, refus de la clé secrète d'exemple hors `development`.

## Impact

- `.github/workflows/ci.yml`, `compose.yaml`, `application/app/__init__.py`, nouveau dossier
  `deploiement/`, nouveaux tests pytest (clé secrète, logique de sélection du commit).
- Aucune dépendance Python ajoutée à l'app ; le script n'utilise que la bibliothèque standard du
  `python3` du serveur.
- Aucun schéma ni migration.
- Serveur : jeton GitHub à grain fin (« Commit statuses: write » sur ce dépôt) dans un fichier du
  serveur ; installation manuelle du script et des unités ; amorçage du premier déploiement.
- ADR concernés : 0017 (nouveau, déploiement par sondage du serveur), 0015 (aucun port entrant
  ajouté, un seul `compose.yaml`), 0003 (Docker Compose, `uv sync --locked`), 0007 (expand/contract,
  sur lequel repose le retour arrière sans downgrade).

## Hors périmètre

- Serveur WSGI de production : le serveur de développement reste en production (décision du
  2026-11-04).
- Durcissement de la VM (sshd, pare-feu, mises à jour), réglages Cloudflare, HSTS : déjà exclus par #24.
- Copie des sauvegardes hors du serveur.
- Lier le dépôt à Cloudflare : Cloudflare n'héberge pas l'app.
- Changement de l'image `db` (version majeure de PostgreSQL) : reste une opération manuelle.
- Checks obligatoires dans le ruleset de `main` : le serveur ne déploie qu'un commit vert.
- Déploiement sans coupure : quelques secondes de coupure acceptées.
- Doublon de l'archive `configuration-de-deploiement` : nettoyage dans un commit séparé.
