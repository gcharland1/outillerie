# Design

## Context

Voir proposal.md (Why), l'ADR 0017 et `questions.md`, qui consigne chaque décision et sa source.
État actuel :

- La production tourne à la main dans un checkout du serveur, projet Compose `outillerie-prod`
  (`docker compose -p outillerie-prod up -d --build`). Son `.env` fixe `FLASK_ENVIRONMENT=production`
  et `POSTGRES_DATA_PATH` ; il n'est jamais lu ici.
- `ci.yml` ne tourne que sur `pull_request` ; le HEAD de `main` n'a aucun run.
- `compose.yaml` : `app` construit sans `image:`, sans healthcheck ni `restart:` ; le `CMD` de
  l'image lance `flask db upgrade` puis `main.py`.
- Le dépôt est public : tout ce que la CI journalise est lisible par tous.
- `_initialize_app` lit `FLASK_SECRET_KEY` après le retour anticipé de `test_config` ; aucune valeur
  n'est refusée.

## Goals / Non-Goals

**Goals:**
- Aucun port entrant, aucun secret dans GitHub, un seul `compose.yaml` (ADR 0015).
- La logique de choix du commit testée par pytest en CI, sans réseau ni Docker.

**Non-Goals:**
- Mettre à jour automatiquement le script ou les unités systemd : ils sont installés à la main.
- Gérer plusieurs serveurs ou environnements.

## Decisions

### Script en Python, bibliothèque standard seulement

`deploiement/deployer.py` utilise `urllib`, `json`, `subprocess`, `fcntl` et `shutil` du `python3`
du serveur. Le jeton passe dans l'en-tête d'une requête `urllib` : jamais en argument de commande,
donc invisible pour `ps` (spec : Secrets hors des journaux). La logique de choix du commit est une
fonction pure, testée par `deploiement/tests/`, lancée en CI avec le pytest du projet
(`uv run --locked pytest ../deploiement/tests` depuis `application/`).

Alternative écartée : Bash avec `curl` et `jq`. Le jeton finirait en argument de `curl` ou demanderait
un fichier de config temporaire, `jq` serait à installer, et la sélection ne serait pas testable.

### Détection d'un commit vert

1. `git fetch origin main` dans le checkout.
2. `GET /repos/gcharland1/outillerie/actions/workflows/ci.yml/runs?branch=main&event=push&status=success`
   donne les runs réussis récents, les plus récents d'abord.
3. Pour chaque run candidat : `GET .../actions/runs/{id}/jobs` ; le commit est vert si `tests` et
   `specs` y sont `success`.
4. Le candidat retenu est le premier qui descend du commit déployé
   (`git merge-base --is-ancestor`), en diffère et n'est pas marqué en échec.

Le statut combiné `/commits/{sha}/status` n'est jamais lu : il ignore les check-runs et ne verrait
que le statut `deploiement` du script (`questions.md` S1).

### Séquence de déploiement

Toutes les commandes Compose s'exécutent dans le checkout avec `-p outillerie-prod` ; `APP_TAG`
passe par l'environnement du sous-processus, jamais par le `.env`.

1. Verrou `fcntl.flock` sur `verrou`, à côté de l'état ; s'il est pris, sortie.
2. Choix du commit (ci-dessus). Rien à faire ⇒ sortie.
3. `git status --porcelain --untracked-files=no` vide, sinon échec sans marquer le commit.
4. Espace libre ≥ 2 Gio sur le disque de Docker et celui des sauvegardes, sinon échec transitoire.
5. Sauvegarde : `docker compose exec -T db sh -c 'pg_dump -Fc -U "$POSTGRES_USER" "$POSTGRES_DB"'`
   vers `sauvegardes/<horodatage>-<sha court>.dump`, mode 600 ; les 10 plus récentes gardées. Les
   identifiants restent dans le conteneur.
6. `git checkout --detach <sha>` puis `docker compose build app` avec `APP_TAG=<sha>`.
7. `docker compose up -d --wait --wait-timeout 120` avec `APP_TAG=<sha>`.
8. Succès : état mis à jour (commit déployé, précédent), statut `success`, nettoyage des images.
9. Échec de 7 : `git checkout --detach <précédent>`, `APP_TAG=<précédent> SKIP_DB_UPGRADE=1
   docker compose up -d --wait --no-build --pull never`, commit marqué en échec, statut `failure`.
   `SKIP_DB_UPGRADE=1` est indispensable : si le commit en échec a appliqué une migration, le
   `flask db upgrade` de l'ancienne image échouerait sur une révision inconnue (`Can't locate
   revision`), et l'ancienne version ne redémarrerait jamais. Toutes les images déployées par le
   script sont construites après ce changement et lisent cette variable.

Un échec de commande hors de ces étapes (`rev-list`, retour du checkout après un échec transitoire)
devient un échec transitoire ou un blocage, jamais une exception non rattrapée ; le nettoyage des
images ne fait jamais échouer un déploiement réussi. Un checkout modifié ne publie `failure` qu'une
fois par commit.

`--no-build --pull never` empêche Compose de rebâtir l'ancienne étiquette avec le nouveau code
(`questions.md` S5). Si le retour arrière échoue aussi, le script publie un échec, écrit
`"blocked": true` dans `etat.json` et ne tente plus rien tant que l'utilisateur n'a pas retiré ce
drapeau : intervention manuelle avec la dernière sauvegarde.

### Fichiers du serveur

Aucun chemin du serveur n'est écrit dans le dépôt, qui est public : `deploiement/installer.sh`
déduit tout de son propre emplacement. Pour un checkout `<checkout>`, le reste vit dans le dossier
voisin `<checkout>-deploiement/`, au compte de l'utilisateur, mode 700 :

- `deployer.py` : copie installée du script (jamais exécutée depuis le checkout, qu'elle modifie) ;
  elle trouve l'état à côté d'elle et le checkout dans `OUTILLERIE_CHECKOUT`, posé par l'unité ;
- `etat.json` : commit déployé, précédent, commits en échec, tentatives transitoires par commit ;
- `jeton` : jeton GitHub, mode 600 ;
- `sauvegardes/` ;
- `unites/` : unités systemd générées.

Sans `etat.json`, le script refuse de tourner : `installer.sh` l'écrit à l'amorçage. Effacer une
entrée « en échec » de `etat.json` force une nouvelle tentative. Si le commit déployé n'est plus un
ancêtre de `main` (amorçage sur une branche fusionnée par *squash*), le script le signale et ne
déploie rien.

### Installation

`deploiement/installer.sh`, idempotent, lancé depuis le checkout sous le compte qui déploiera : crée
le dossier, copie le script, demande le jeton s'il manque, amorce au premier passage (sauvegarde,
build et `up --wait` du commit courant avec `APP_TAG`, `etat.json`), génère les unités et les active.
Le relancer met à jour le script et les unités installés. Base arrêtée à l'amorçage : refus, sauf
`OUTILLERIE_SANS_SAUVEGARDE=1` explicite. Un chemin de checkout hors `[A-Za-z0-9._/-]` est refusé,
car il est écrit dans l'unité et passe par `sed`.

Alternative écartée : une procédure manuelle dans le README, qui obligeait à y écrire les chemins.

### Unités systemd

`outillerie-deploiement.service.in` est un gabarit : `installer.sh` y remplace `@COMPTE@`,
`@CHECKOUT@`, `@DEPLOIEMENT@` et `@PYTHON@` (`command -v python3`), écrit le résultat dans
`<checkout>-deploiement/unites/` avec `outillerie-deploiement.timer` (`OnCalendar=*:0/5`,
`Persistent=true`), puis `sudo systemctl link` les deux unités et active le timer. Ni le compte ni un
chemin du serveur, pas même celui des unités de systemd, n'apparaît dans le dépôt. La sortie
standard va dans journald (`journalctl -u outillerie-deploiement`). Un `oneshot` actif n'est pas
relancé par son timer ; le verrou couvre un lancement manuel simultané.

### Compose

```yaml
app:
  build: ...
  image: outillerie-app:${APP_TAG:-dev}
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/', timeout=3)"]
    interval: 10s
    timeout: 5s
    retries: 3
    start_period: 60s
db:
  restart: unless-stopped
```

L'image `python:3.13-slim` n'a pas `curl` (Training, à vérifier à l'implémentation) ; Python y est.
`/` répond 200 sans connexion (`tests/test_main.py`).

### Statut GitHub

`POST /repos/gcharland1/outillerie/statuses/{sha}` avec `state` et `context: deploiement`, sans
`description` ni `target_url`. Jeton à grain fin, dépôt unique, « Commit statuses: Read and write »
et « Actions: Read-only » (lecture des runs ; sans effet de bord, et évite de dépendre de la lecture
anonyme d'un dépôt public). Un échec de cet appel est journalisé et n'altère pas le résultat.

### Clé secrète hors développement

`_initialize_app` refuse, hors `development`, une `FLASK_SECRET_KEY` absente, vide ou égale à
`dev-seulement`, par une `RuntimeError` qui nomme la variable sans sa valeur. Le contrôle est une
fonction appelée avec l'environnement et la clé, testable sans démarrer l'app.

### CI

`ci.yml` ajoute `push: branches: [main]` à ses déclencheurs ; jobs inchangés, plus l'étape des tests
du script. Rien d'autre côté GitHub : aucun job de déploiement, aucun secret.

## Risks / Trade-offs

- [Le compte de l'utilisateur est dans le groupe `docker`, donc équivalent root, et tout commit de
  `main` déployé l'exerce par `compose.yaml`] → accepté (Q11) ; le ruleset impose une PR mergée par
  le mainteneur.
- [Retour arrière sans downgrade après une migration appliquée] → expand/contract de l'ADR 0007 ;
  la sauvegarde du déploiement permet une restauration manuelle.
- [Délai jusqu'à 5 minutes plus la durée de la CI] → accepté.
- [Le jeton expire] → l'échec de pose du statut se voit dans journald ; date d'expiration notée dans
  la procédure.
- [Un `docker compose up` lancé à la main sans `APP_TAG` repasse sur `outillerie-app:dev`] → la
  procédure le proscrit en production ; le passage suivant du script ne le corrige pas, car le commit
  déployé n'a pas changé.
- [La logique d'exécution (Docker, git, API) n'est pas couverte par pytest] → vérification manuelle
  sur le serveur, scénarios listés dans tasks.md.

## Migration Plan

1. Sur le serveur, checkout sur la branche du changement : `deploiement/installer.sh`. L'amorçage
   sauvegarde la base et déploie ce commit avec `APP_TAG` : la pile passe sur l'image étiquetée et le
   nouveau `compose.yaml`. Plus simple et plus sûr que de réétiqueter l'image en marche, construite
   par l'ancien `compose.yaml`.
2. Merger la PR par un commit de merge, pour que le commit amorcé reste un ancêtre de `main` ; sinon
   réamorcer sur `main` (`deploiement/README.md`). Le commit de merge a un run `push` vert et devient
   le premier déploiement automatique.
3. Retour arrière du changement : `sudo systemctl disable --now outillerie-deploiement.timer` ; la
   pile continue de tourner et se gère de nouveau à la main.

La procédure vit dans `deploiement/README.md`.
