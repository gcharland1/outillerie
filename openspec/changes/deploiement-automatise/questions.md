# Questions — deploiement-automatise (issue #5)

Issue #5 « Automatiser le déploiement sur mon serveur » : à chaque PR mergée sur `main`, le serveur
récupère le code, lance la suite de tests et, si elle passe à 100 %, redémarre le Docker Compose.

Quatre angles explorés (code, specs et ADR, cas limites, antériorité). `gh` = lecture de l'API GitHub
le 2026-11-04.

| #   | Question | Réponse | Source | Décidé par |
|-----|----------|---------|--------|------------|
| 1   | Déclencheur : merge sur `main`, release, `workflow_dispatch` ? | à trancher ; l'issue dit « PR mergée » et « Trigger git sur nouveau release » | texte de l'issue ; `ci.yml:3-5` | utilisateur |
| 2   | Comment le serveur apprend qu'il doit déployer (aucun port entrant hors SSH) ? | à trancher : sondage par le serveur, SSH depuis Actions, runner auto-hébergé | ADR 0015:44 ; dépôt public (`gh`) | utilisateur |
| 3   | Où tournent les tests ? | à trancher ; l'issue dit « sur le serveur », la CI les lance déjà sur les PR | `ci.yml:52-73` ; texte de l'issue | utilisateur |
| 4   | Base des tests | jamais la base de prod : `mock_app` fait `create_all` puis `drop_all` ; défaut `TEST_DATABASE_URL` sinon `localhost:5432` | `application/tests/conftest.py:17,22-29,51,55` | dépôt |
| 5   | Où se construit l'image ? | aujourd'hui sur le serveur (`build:`, pas d'`image:`, aucun registre) ; lié à 2 | `compose.yaml:2-5` | utilisateur (avec 2) |
| 6   | Sauvegarde avant migration, échec de migration | aucune sauvegarde ; `flask db upgrade` au démarrage ; migration en échec ⇒ app arrêtée ; downgrade testé sur base vide seulement | `Dockerfile:35` ; `ci.yml:58-65` | utilisateur |
| 7   | Retour arrière automatique ou manuel | précédent : manuel, « redéployer la révision précédente » ; pas d'`image:` étiquetée ni de healthcheck pour le détecter | archive `configuration-de-deploiement/design.md:82` ; `compose.yaml:2-16` | utilisateur |
| 8   | Coupure acceptable pendant le redémarrage | inconnue ; un seul conteneur `app`, coupure de quelques secondes inévitable | Inferred de `compose.yaml` | utilisateur |
| 9   | Notification | inconnue ; GitHub notifie par courriel l'échec d'un workflow (Training) | No basis | utilisateur |
| 10  | Secrets | le `.env` reste sur le serveur (ignoré par git et par le contexte Docker) ; secrets GitHub selon 2 | `.gitignore:43` ; `application/.dockerignore:1` | dépôt |
| 11  | Compte qui déploie | inconnu ; groupe `docker` ≈ root (Training) | No basis | utilisateur |
| 12  | Merges rapprochés | `concurrency` sans annulation du run en cours + verrou `flock` côté serveur ; jamais déployer un SHA qui n'est pas descendant du SHA déployé | Inferred (annuler en pleine migration est dangereux) | convention |
| 13  | Volet « *Blinder* côté sécurité » | #24 a couvert tunnel, ports, `ProxyFix`, cookie `Secure` ; pare-feu, SSH du serveur, réglages Cloudflare et HSTS exclus ⇒ hors périmètre ; seule la sécurité du mécanisme de déploiement entre ici | archive `configuration-de-deploiement/proposal.md:39-43` | convention |
| 14  | « Linker un repo git » sur Cloudflare | hors périmètre : Pages et Workers ne font pas tourner un Compose Flask + Postgres (Training) ; ADR 0015 fixe Compose derrière le tunnel | ADR 0015:11 | convention |
| 15  | Spec porteuse | nouvelle capacité `livraison-continue` ; `deploiement` décrit le comportement de l'app, pas le pipeline ; delta sur `deploiement` seulement si `compose.yaml` change | `openspec/specs/deploiement/spec.md:3-5` | convention |
| 16  | Chemin du checkout sur le serveur, `POSTGRES_DATA_PATH` | inconnu ; par défaut les données vivent dans le checkout (`./data/postgres`), un `git clean -x` les effacerait | `.env.example:6` ; `.gitignore:11` | utilisateur |
| N1  | Dépôt public : runner auto-hébergé exposé au code des forks ? | dépôt `PUBLIC` ; approbation des forks pour les nouveaux contributeurs seulement ; aucun runner enregistré | `gh repo view`, `gh api actions/permissions` | dépôt (contraint 2) |
| N2  | L'image de prod peut-elle lancer les tests ? | non : `UV_NO_DEV=1`, pytest dans le groupe `dev` | `Dockerfile:14` ; `pyproject.toml` | dépôt |
| N3  | Qu'est-ce qui empêche de déployer un `main` non testé ? | rien : `ci.yml` sur `pull_request` seulement ; le ruleset `main` n'exige aucun check | `ci.yml:3-5` ; `gh api rules/branches/main` | dépôt |
| N4  | Tests sur le commit mergé avant déploiement | relancer le job `tests` de `ci.yml` (lint, migrations, pytest, diagramme) sur `push: main` ; le déploiement en dépend | Inferred de N3 et de l'exigence « 100 % » | convention |
| N5  | Rendre les checks `tests` et `specs` obligatoires dans le ruleset `main` | réglage du dépôt, hors code | `gh api rules/branches/main` | utilisateur |
| N6  | Comment constater que le redéploiement a réussi ? | `app` n'a ni healthcheck ni route de santé ; ajouter un healthcheck (`python -c urllib…` sur `/`, pas de curl dans l'image slim, non vérifié) et `docker compose up -d --wait` | `compose.yaml:12-14,28-32` ; `app/__init__.py:305-310` | convention |
| N7  | Redémarrage après reboot ou plantage | aucune clé `restart:` ⇒ ajouter `restart: unless-stopped` à `app` et `db` | `compose.yaml` | convention |
| N8  | Mise à jour du checkout sans perte | `git fetch` + `git checkout --detach <sha>`, jamais `git clean -x` ; `docker compose build` avant `up` pour qu'un build raté laisse l'ancien conteneur | `.gitignore:11,43` | convention |
| N9  | Journaux publics (dépôt public) | côté Actions : succès ou échec et SHA seulement ; le détail dans journald sur le serveur ; jamais `docker compose config` dans un log | Inferred de la visibilité `PUBLIC` | convention |
| N10 | Chaîne d'approvisionnement du job qui détient un accès au serveur | actions épinglées par SHA, `permissions` minimales, `known_hosts` fourni (jamais `ssh-keyscan` ni `StrictHostKeyChecking=no`) | `gh api actions/permissions` ; `ci.yml:35,40,43` | convention |
| N11 | Interruption à mi-déploiement | script serveur détaché de la session (service `oneshot` ou `systemd-run`), idempotent pour un même SHA | Inferred de `Dockerfile:35` | convention |
| N12 | Serveur WSGI de production (le conteneur sert Werkzeug) | reporté par #24 sans destination | archive `configuration-de-deploiement/proposal.md:41` ; `main.py:3-6` | utilisateur |
| N13 | Refuser au démarrage la clé secrète de dev hors `development` | reporté explicitement « avec l'issue #5 » lors d'une relecture ; pas fait | `docs/sessions/2026-10-20-6a8271bb.md:10259-10260,10525` | dépôt |
| N14 | Limite de taille de corps au proxy (photos 16 Mo) | reportée à #5 ; sans nginx, c'est la limite de Cloudflare ⇒ vérification après déploiement | archive `photo-des-outils/design.md:152-153` | convention |
| N15 | Cookie `Secure` « à activer au déploiement HTTPS (#5) » | déjà fait par #24 ; vérification après déploiement | archive `fermeture-de-session/design.md:141-142` | dépôt |
| N16 | Extensions Postgres en production | vérifier `SELECT extname FROM pg_extension` après déploiement | Recalled `docs/sessions/2026-11-02-231a80d7.md:12211-12218` | convention |
| N17 | État actuel du serveur (app déjà en marche, base existante, RAM) | inconnu ; le plan manuel de #24 n'a pas de trace d'exécution | archive `configuration-de-deploiement/tasks.md:26` | utilisateur |
| N18 | Archive `configuration-de-deploiement` en double (2026-10-25 et 2026-11-01, identiques) | hors de ce changement ; à nettoyer dans un commit séparé | `diff -r` des deux dossiers | hors périmètre |

## Divergences entre angles

- Q2 : les angles specs et antériorité recommandaient un runner auto-hébergé ; l'angle cas limites a
  établi que le dépôt est public (N1), ce qui expose ce runner au code des forks.
- Q5 : GHCR imposerait `image:` en prod et `build:` en dev, donc un override, contraire à ADR 0015
  (un seul `compose.yaml`) ; build sur le serveur ne change pas `compose.yaml`.
- Q15 : deux angles sur trois pour une nouvelle capacité ; retenu par convention.

## Réponses de l'utilisateur

- Q2 + Q5 (2026-11-04) : **sondage par le serveur**. Un timer systemd interroge l'API GitHub publique
  (dernier commit de `main` et résultat de sa CI) ; s'il est nouveau et vert : sauvegarde, checkout,
  build sur le serveur, `up --wait`. Aucun port entrant, aucun secret GitHub, `compose.yaml` inchangé
  hors healthcheck et `restart:`. Conséquences : N1 et N10 (accès au serveur) sans objet ; N9 : le
  détail du déploiement vit dans journald.
- Q3 (2026-11-04) : **tests dans Actions seulement**. `ci.yml` tourne aussi sur `push` vers `main` ;
  le serveur ne déploie qu'un commit dont ce run est vert et ne lance jamais de tests. Écart assumé à
  la lettre de l'issue. Q4 et N2 sans objet.
- Q1 (2026-11-04) : **chaque commit de `main` dont la CI est verte**, pas les releases. Retour
  arrière par un revert mergé.
- Q6 (2026-11-04) : **`pg_dump -Fc` avant chaque déploiement**, sur le serveur, hors du checkout,
  dossier réservé à root, mode 600, les 10 derniers conservés. Dump en échec ⇒ pas de déploiement.
  Copie hors serveur : hors périmètre (issue de sauvegarde à part).
- Q7 (2026-11-04) : **retour automatique à l'image précédente, sans downgrade**. Image étiquetée par
  SHA (`compose.yaml` : `image:` paramétré en plus de `build:`) ; échec de `up --wait` ⇒ relance de
  l'image précédente, SHA marqué en échec et jamais retenté. Repose sur la transaction des migrations
  et l'expand/contract d'ADR 0007.
- Q11 (2026-11-04) : **le compte personnel de l'utilisateur** exécute le service et le timer
  (`User=` du service). Le compte doit déjà pouvoir lancer `docker` ; le dossier des dumps (Q6)
  appartient alors à ce compte, mode 700, au lieu de root.
- Q16 (2026-11-04) : le checkout de production **existe déjà sur le serveur** (chemin donné par
  l'utilisateur, volontairement absent du dépôt public). Emplacement des données Postgres : **déjà
  fixé par `POSTGRES_DATA_PATH` dans le `.env` du serveur** (valeur non communiquée, `.env` non lu).
  Le script ne touche ni à ce chemin ni au `.env`, et ne lance jamais `git clean -x`. Dossier des
  dumps : convention, `<checkout>-deploiement/sauvegardes/`, à côté de l'état et du jeton (design.md,
  Fichiers du serveur).
- N12 (2026-11-04) : **le serveur de développement reste en production**, avec
  `FLASK_ENVIRONMENT=production` dans le `.env` du serveur. Hors périmètre. Constat : cette variable
  ne règle que le cookie `Secure` (`app/__init__.py:64`) ; `main.py` lance `app.run` sans `debug`,
  donc sans débogueur interactif.
- Q9 (2026-11-04) : **statut de commit `deploiement`** (succès ou échec, sans détail) posé par le
  script via l'API GitHub. Jeton à grain fin limité aux statuts de commit de ce dépôt, dans un fichier
  du serveur hors du checkout, jamais dans le dépôt. Le détail reste dans journald (N9).
- Q8 (2026-11-04) : **coupure de quelques secondes acceptée, à toute heure**. Build avant l'arrêt.

## Conséquences des réponses (convention)

- N5 (checks requis dans le ruleset) : hors périmètre ; le serveur ne déploie qu'un commit vert (Q1, Q3).
- N10, N11 côté Actions : sans objet (Q2) ; le script reste détaché et idempotent côté serveur.
- N17 (état du serveur) : checkout et `.env` existent (Q16) ; premier déploiement sans image étiquetée
  précédente ⇒ en cas d'échec, pas de retour automatique possible : arrêt et statut d'échec.
- Intervalle du timer : 5 minutes.
- Nom de projet Compose de la production : **`outillerie-prod`** (`docker compose -p outillerie-prod`,
  conteneurs `outillerie-prod-app-1` et `outillerie-prod-db-1`). Donné par l'utilisateur le 2026-11-04 ;
  Recalled : transcript du 2026-10-25 (`docs/sessions/.local/2026-10-25-40f6145a.md:5685-5715`). Toutes
  les commandes Compose du script le passent : sans lui, Compose prendrait le nom du dossier
  (`outillerie`) et créerait une seconde pile qui entrerait en conflit sur les ports 8080 et 5430.

## Second passage (cas limites, 2026-11-04) — convention

Aucune décision utilisateur requise ; toutes appliquées, renversables.

| #   | Question | Réponse retenue | Source |
|-----|----------|-----------------|--------|
| S1  | Comment savoir qu'un SHA est vert ? | run de `ci.yml` filtré `event=push`, `branch=main`, `head_sha`, `status=completed`, `conclusion=success`, et jobs `tests` et `specs` tous deux `success` ; jamais le statut combiné `/status`, qui ignore les check-runs (`pending`, `total_count: 0` sur 5d3d48d dont les check-runs sont verts) et ne verrait que le statut `deploiement` | Sourced `gh api` ; Training pour les filtres |
| S2  | Run en cours, relancé, absent | en cours ⇒ attendre ; relance verte ⇒ déployable ; aucun run ⇒ pas vert (jamais une erreur). Le premier déploiement suit le premier push sur `main` après l'ajout de `push:` à `ci.yml` | Sourced `ci.yml:3-5` ; Training |
| S3  | Tête de `main` rouge, commit antérieur vert | déployer le plus récent commit vert descendant du SHA déployé (`git merge-base --is-ancestor`), conforme à Q1 | Inferred de Q1 |
| S4  | Quand marquer un SHA en échec | seulement si `up --wait` échoue ; fetch, API, dump, build, espace disque ⇒ échec transitoire, au plus 3 tentatives par SHA ; état (SHA déployé, échecs, tentatives) dans un fichier hors du checkout, effaçable à la main | Inferred de Q7 |
| S5  | `image:` dans le `compose.yaml` partagé | `image: outillerie-app:${APP_TAG:-dev}` ; dev inchangé ; retour arrière par `up -d --wait --no-build --pull never`, jamais `pull_policy: build` ; `APP_TAG` passé par l'environnement du script, jamais par le `.env` | Sourced `compose.yaml:2-5` ; Training |
| S6  | Retour arrière et `compose.yaml` modifié | retour arrière = `git checkout --detach <SHA précédent>` puis `up` avec l'étiquette précédente ; un changement de l'image `db` reste manuel (hors périmètre) | Sourced `compose.yaml:19,25` |
| S7  | Espace disque | après un succès, garder les images courante et précédente, supprimer les autres `outillerie-app:*`, puis `docker image prune -f` (jamais `-a`, `system prune` ni volumes) ; vérifier l'espace libre avant dump et build | Inferred de Q7 |
| S8  | Jeton et `.env` | jeton en fichier 600 du compte de service, passé à `curl` par `--config` ou stdin, jamais en argument ; pas de `set -x` ni `compose config` ; jeton aussi utilisé pour les lectures (60 req/h sans jeton, 5000 avec, Training) ; 403/429 ⇒ transitoire ; échec de pose du statut journalisé sans bloquer ; droit minimal « Commit statuses: write » sur ce dépôt, date d'expiration notée | Training |
| S9  | Checkout modifié à la main | `git status --porcelain --untracked-files=no` non vide ⇒ arrêt, journal, statut d'échec, SHA non marqué ; jamais `reset --hard` ni `clean` | Sourced `.gitignore:11` ; Training |
| S10 | Script modifié par le commit qu'il déploie | script et unités systemd installés hors du checkout, mis à jour à la main par une procédure documentée | Training |
| S11 | Premier déploiement | amorçage manuel documenté : étiqueter l'image en marche `outillerie-app:<HEAD du checkout>` et écrire le fichier d'état ; sans fichier d'état, le script refuse de tourner | Inferred |
| S12 | Concurrence et durée | `flock` ; `--wait-timeout 120` ; `start_period` sur le healthcheck de `app` ; force-push sur `main` déjà bloqué (`non_fast_forward`) | Sourced `gh api rules/branches/main` |
| S13 | Run de PR de fork pris pour vert | écarté par le filtre `event=push` sur `main` | Training |

Remplace la ligne N17 ci-dessus : le premier déploiement a désormais une cible de retour arrière (S11).

## Écarts d'implémentation

- S11 (amorçage) : remplacé par un premier déploiement du commit courant avec `APP_TAG`, fait par
  `installer.sh` (design.md, Migration Plan) ; l'image en marche, construite par l'ancien
  `compose.yaml`, n'est pas réétiquetée.
- S10 et Q16 (2026-11-04, demande de l'utilisateur) : aucun chemin du serveur dans le dépôt public.
  `deploiement/installer.sh`, idempotent, déduit tout de son emplacement (`<checkout>-deploiement/`),
  génère les unités depuis un gabarit et les lie par `systemctl link` ; ni le compte ni un chemin
  absolu n'est versionné.
- Jeton : « Actions: Read-only » ajouté à « Commit statuses: Read and write » pour la lecture des runs.
