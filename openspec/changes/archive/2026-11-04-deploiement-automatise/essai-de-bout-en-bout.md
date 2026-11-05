# Essai de bout en bout (tâche 6.1, 2026-11-04)

`deployer.main()` exécuté pour de vrai (git, Docker Compose, `pg_dump`, verrou, état) sur un poste
de développement, avec :

- un dépôt d'origine local tenant lieu de GitHub, et un clone détaché tenant lieu du checkout de
  production ;
- projet Compose `outillerie-e2e` (au lieu de `outillerie-prod`), ports 18080 et 15430 par un
  `compose.override.yaml` non suivi, `.env` d'essai en `production` ;
- l'API GitHub remplacée par un faux qui déclare verts les commits listés et affiche le statut au
  lieu de le poser. La détection d'un commit vert sur la vraie API reste à observer en production.

Historique de `main` : `base` → `vert` → `casse` (migration qui lève une exception) → `correctif`
(retire la migration).

| # | Situation | Sortie | Constat |
|---|-----------|--------|---------|
| 1 | Pas de `etat.json` | `etat.json absent : amorcer le déploiement`, code 1 | rien modifié |
| 2 | Amorçage manuel à `base` (`APP_TAG=<sha>`, `build`, `up --wait`), aucun commit vert | `Aucun commit à déployer`, code 0 | |
| 3 | `vert` vert | `Sauvegarde : …-f74dc08c9ad9.dump`, `déployé`, statut `success`, code 0 | dump en 600 ; état : déployé `vert`, précédent `base` ; seules les images `base` et `vert` restent ; app `healthy` |
| 4 | `casse` vert | `ne devient pas sain : retour à f74dc08…`, statut `failure`, code 1 | checkout sur `vert`, image `vert` `healthy`, `alembic_version` = `9654b00a97c3` (aucun downgrade), `casse` dans `failed` |
| 4b | Passage suivant | `Aucun commit à déployer`, code 0 | `casse` non retenté |
| 5 | `correctif` vert, `compose.yaml` modifié à la main | `Checkout modifié à la main, déploiement refusé : M compose.yaml`, statut `failure`, code 1 | `correctif` non marqué en échec |
| 5b | Fichier restauré | `a4d95f5… déployé`, statut `success`, code 0 | images `vert` et `correctif` seules ; app `healthy` |
| 6 | Verrou tenu par un autre processus | `Un déploiement est déjà en cours`, code 0 | |

Effet de bord constaté : `docker image prune -f` supprime aussi les images orphelines des autres
projets de l'hôte. Voulu sur le serveur, à savoir sur un poste.

Non couvert ici : unités systemd réelles (vérifiées par `systemd-analyze verify` seulement), jeton
et API GitHub réels, restauration d'une sauvegarde, échec du retour arrière (`blocked`).

## Installateur (2026-11-04)

`deploiement/installer.sh` lancé depuis un clone d'essai, `sudo` remplacé par une cale qui affiche
la commande au lieu de l'exécuter :

| # | Situation | Constat |
|---|-----------|---------|
| 1 | Premier passage, jeton fourni sur l'entrée standard | `<checkout>-deploiement/` créé (700), `deployer.py` (700), `jeton` et `etat.json` (600) ; commit courant construit et démarré `healthy` ; base arrêtée, donc pas de sauvegarde ; `systemctl link`, `daemon-reload`, `enable --now` demandés |
| 2 | Unités générées | `systemd-analyze verify` sans erreur ; compte, checkout, dossier et `python3` remplis |
| 3 | Second passage, entrée vide | aucune question, aucun amorçage ; script et unités réinstallés, code 0 |
| 4 | Script installé lancé comme l'unité (`OUTILLERIE_CHECKOUT` seul) | trouve son état à côté de lui ; vraie API GitHub avec un faux jeton : `HTTP 401`, échec transitoire, jeton absent de la sortie |
| 5 | Script installé sans `OUTILLERIE_CHECKOUT` | refus, code 1 |

Non couvert : `sudo` et systemd réels, sauvegarde de l'amorçage sur une base en marche.

## Retour arrière après une migration appliquée (relecture, 2026-11-04)

Constat bloquant de la relecture : l'ancienne image relancée exécutait `flask db upgrade` sur une
base portant une révision qu'elle ignore. Essai, après le correctif `SKIP_DB_UPGRADE` :

| # | Situation | Constat |
|---|-----------|---------|
| 7 | Commit `relecture` (correctifs) vert | déployé, statut `success` |
| 8 | Commit `app-cassee` vert : migration valide (`e55a10000001`, crée une table), puis `main.py` qui s'arrête | `up --wait` échoue ; retour à `relecture` avec `SKIP_DB_UPGRADE=1`, `healthy` ; `alembic_version` = `e55a10000001`, table présente ; commit en échec, statut `failure`, code 1, pas de blocage |
| 8b | Contre-épreuve : même relance sans `SKIP_DB_UPGRADE` | `unhealthy`, journal : `Can't locate revision identified by 'e55a10000001'` |

## Mise en production (rapportée par l'utilisateur, 2026-11-05)

- `installer.sh` lancé sur le serveur après le merge de #32 (commit de merge `9d9ff35`) : installation
  et amorçage réussis ; le journal du service affiche `Aucun commit à déployer` toutes les 5 minutes.
- Second passage d'`installer.sh` : sans effet (tâche 5.3).
- Boucle complète constatée : un commit de `main` à la CI `push` verte a été redéployé seul (tâche 3.1).
- Affichage du journal : les accents apparaissent échappés (`<C3><A0>`) sous `LANG=C` ; le journal
  contient bien de l'UTF-8, rien à changer dans le script.
