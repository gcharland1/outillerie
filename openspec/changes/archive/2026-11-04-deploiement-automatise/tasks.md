# Tasks

## 1. Clé secrète hors développement

- [x] 1.1 Dans `_initialize_app`, refuser hors `development` une `FLASK_SECRET_KEY` absente, vide ou égale à `dev-seulement`, par une `RuntimeError` qui nomme la variable sans sa valeur ; vérifier par des tests pytest les trois scénarios de la spec `deploiement` (Clé secrète hors développement), et que le message ne contient pas la valeur
- [x] 1.2 Vérifier que les tests existants passent toujours (`uv run pytest`)

## 2. Docker Compose

- [x] 2.1 Dans `compose.yaml`, ajouter à `app` `image: outillerie-app:${APP_TAG:-dev}`, le healthcheck du design et `restart: unless-stopped`, et `restart: unless-stopped` à `db` ; vérifier que `python -c "import urllib.request"` tourne dans l'image (`docker build ./application` puis `docker run --rm <image> python -c ...`) et que l'image n'a pas `curl` ou en a un, pour confirmer le choix
- [x] 2.2 Vérifier sur une pile jetable (`docker compose -p outillerie-essai`, ports libres via un override non versionné) : sans `APP_TAG` l'image est `outillerie-app:dev` ; `up -d --wait` réussit ; avec une migration volontairement cassée, `up -d --wait --wait-timeout 120` échoue et le conteneur ne devient jamais sain
- [x] 2.3 Mettre à jour `README.md` (développement inchangé, `APP_TAG`, healthcheck) ; vérifier que les commandes documentées fonctionnent telles qu'écrites

## 3. CI sur main

- [x] 3.1 Ajouter `push: branches: [main]` aux déclencheurs de `ci.yml` ; vérifier avec `actionlint` ou une lecture de la syntaxe, puis, après le merge, qu'un run `push` existe pour le commit de merge avec les jobs `tests` et `specs`

## 4. Logique de choix du commit

- [x] 4.1 Créer `deploiement/deployer.py` avec la fonction pure de choix du commit (runs réussis, jobs `tests` et `specs`, ascendance, commits en échec, commit déployé) ; vérifier par `deploiement/tests/` chaque scénario de la spec `livraison-continue` (Commit déployable, Choix du commit à déployer), avec des réponses d'API et une ascendance simulées
- [x] 4.2 Ajouter à `ci.yml` l'étape `uv run --locked pytest ../deploiement/tests` depuis `application/` ; vérifier qu'elle tourne en local et que ruff couvre `deploiement/`

## 5. Exécution du déploiement

- [x] 5.1 Implémenter dans `deployer.py` : verrou, lecture et écriture de `etat.json` (refus sans fichier), appels API avec le jeton en en-tête, `git fetch`, contrôle du checkout, espace libre, sauvegarde et rotation, build, `up --wait`, retour arrière, statut, nettoyage des images, compteur d'échecs transitoires ; vérifier par des tests pytest les parties sans effet de bord (rotation des sauvegardes, transitions de `etat.json`, classement transitoire ou définitif d'un échec, absence du jeton dans la sortie)
- [x] 5.2 Écrire le gabarit `deploiement/outillerie-deploiement.service.in` et `outillerie-deploiement.timer`, sans aucun chemin du serveur ; vérifier avec `systemd-analyze verify` l'unité générée
- [x] 5.3 Écrire `deploiement/installer.sh`, idempotent, chemins déduits de son emplacement (dossier, script, jeton, amorçage, unités liées et activées), et `deploiement/README.md` (jeton : droits et expiration ; installation et mise à jour ; réamorçage ; journal ; nouvelle tentative ; déblocage ; restauration ; désactivation ; ne jamais lancer `compose up` à la main en production) ; vérifier en lançant `installer.sh` une fois sur le serveur, puis une seconde fois sans effet

## 6. Vérification de bout en bout

- [x] 6.1 Sur une pile jetable avec un clone du dépôt : amorçage, déploiement d'un commit vert, retour arrière sur un commit dont l'app ne devient pas saine (aucun downgrade, image et checkout précédents, commit marqué en échec), refus sur checkout modifié, refus sans `etat.json` ; consigner les sorties
- [x] 6.2 Exécuter `/verifier` et obtenir « terminé » (lint, format, tests sur Postgres, `flask db check`, `openspec validate`)

## Workflow follow-up

- Relecture par l'agent `relecteur` avant la PR.
- Mise en production selon le Migration Plan de `design.md` (`installer.sh` sur la branche, puis merge par un commit de merge), puis un premier déploiement observé dans `journalctl -u outillerie-deploiement`.
- Archiver le changement avec `/opsx:archive`.
