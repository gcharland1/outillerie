# Déploiement automatique

Toutes les 5 minutes, le serveur cherche le plus récent commit de `main` dont la CI est verte, le
sauvegarde, le construit et le démarre ; s'il ne devient pas sain, il relance la version précédente.
Décision : [ADR 0017](../docs/decisions/0017-deployer-la-production-par-sondage-du-serveur.md) ;
exigences : spec `livraison-continue`.

Aucun chemin du serveur n'est écrit dans ce dépôt public : `installer.sh` les déduit de son propre
emplacement. Pour un checkout `<checkout>` :

| Chemin | Contenu |
|--------|---------|
| `<checkout>/` | le dépôt, son `.env`, projet Compose `outillerie-prod` |
| `<checkout>-deploiement/deployer.py` | copie installée du script, jamais exécutée depuis le checkout |
| `<checkout>-deploiement/etat.json` | commit déployé, précédent, commits en échec, tentatives |
| `<checkout>-deploiement/jeton` | jeton GitHub (mode 600) |
| `<checkout>-deploiement/sauvegardes/` | les 10 dernières sauvegardes de la base |
| `<checkout>-deploiement/unites/` | unités systemd générées, liées par `systemctl link` |

Le service tourne sous le compte qui lance `installer.sh`.

## Prérequis

- Un compte qui peut lancer `docker` et `sudo` ; `python3` ≥ 3.10 ; Docker Compose ≥ 2.20.
- Le `.env` du checkout : `FLASK_ENVIRONMENT=production`, une vraie `FLASK_SECRET_KEY` (l'app
  refuse `dev-seulement`), `POSTGRES_DATA_PATH` hors du checkout.
- Un jeton GitHub à grain fin : *Settings › Developer settings › Fine-grained tokens*, ce dépôt
  seulement, permissions *Commit statuses: Read and write* et *Actions: Read-only*. Noter sa date
  d'expiration : à l'échéance, les lectures échouent et le journal le montre.

## Installation et mise à jour

Depuis le checkout, sur le commit à déployer en premier :

```sh
deploiement/installer.sh
```

Le script est idempotent ; chaque passage :

1. crée `<checkout>-deploiement/` (par `sudo` si le dossier parent n'est pas accessible en écriture) ;
2. copie `deployer.py` ;
3. demande le jeton s'il manque ;
4. au premier passage seulement (pas d'`etat.json`) : refuse un checkout modifié, sauvegarde la base
   si elle tourne, construit et démarre le commit courant avec `APP_TAG`, écrit `etat.json` ;
5. régénère les unités, les lie, recharge systemd et active le timer.

Le commit amorcé doit rester un ancêtre de `main` : amorcer sur une branche puis la fusionner par
*squash* ou *rebase* bloque les déploiements (le journal le signale). Dans ce cas, se placer sur
`main`, supprimer `etat.json` et relancer `installer.sh`.

Un commit qui modifie `deploiement/` est déployé comme les autres, mais le script installé ne change
pas seul : relancer `deploiement/installer.sh` une fois ce commit déployé.

## Exploitation

Depuis le checkout ; `etat.json` et `sauvegardes/` sont dans `<checkout>-deploiement/`.

- Journal : `journalctl -u outillerie-deploiement` ; le résultat de chaque déploiement est aussi le
  statut `deploiement` du commit sur GitHub.
- Prochain passage : `systemctl list-timers outillerie-deploiement.timer`.
- Forcer une nouvelle tentative d'un commit en échec : retirer son SHA de `failed` et de `attempts`
  dans `etat.json`.
- Déploiements bloqués (le retour arrière lui-même a échoué) : remettre la pile en état à la main,
  aligner `deployed` dans `etat.json` sur le commit en marche, puis remettre `"blocked": false`.
- Restaurer une sauvegarde :

  ```sh
  export APP_TAG=$(git rev-parse HEAD)
  docker compose -p outillerie-prod stop app
  docker compose -p outillerie-prod exec -T db \
    sh -c 'pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
    < "../$(basename "$PWD")-deploiement/sauvegardes/<fichier>.dump"
  docker compose -p outillerie-prod up -d --wait --no-build
  ```

- Désactiver : `sudo systemctl disable --now outillerie-deploiement.timer` ; la pile continue de
  tourner et se gère de nouveau à la main.

## À ne jamais faire en production

- `docker compose up` sans `APP_TAG` : la pile repasserait sur `outillerie-app:dev`.
- Modifier un fichier suivi du checkout : le script refuse alors de déployer.
- `git clean`, `git reset --hard` ou `docker system prune` sur le serveur.
