#!/usr/bin/env bash
# Installs or updates the automatic deployment of the checkout holding this script (ADR 0017).
# Idempotent: rerun it after pulling a change to deploiement/. See deploiement/README.md.
#
# Every path derives from this script's location, so none is written in the repository:
#   <checkout>              this repository's root, with its .env
#   <checkout>-deploiement  state, token, backups, installed script and units (mode 700)
set -euo pipefail

checkout=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
deploiement="$checkout-deploiement"
projet=outillerie-prod
compte=$(id -un)
groupe=$(id -gn)

echec() {
  echo "installer.sh : $*" >&2
  exit 1
}

compose() {
  docker compose --project-directory "$checkout" -p "$projet" "$@"
}

[[ $EUID -ne 0 ]] || echec "lancer sous le compte qui exécutera les déploiements, pas root"
docker info >/dev/null 2>&1 || echec "$compte ne peut pas lancer docker"
python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' || echec "python3 ≥ 3.10 requis"
[[ -f $checkout/.env ]] || echec "$checkout/.env absent"
# Written unquoted into the generated unit and through sed.
[[ $checkout =~ ^[A-Za-z0-9._/-]+$ ]] || echec "chemin du checkout refusé (espace ou caractère spécial)"

echo "Dossier de déploiement : $deploiement"
if [[ ! -d $deploiement ]]; then
  if [[ -w $(dirname -- "$checkout") ]]; then
    install -d -m 700 "$deploiement"
  else
    sudo install -d -o "$compte" -g "$groupe" -m 700 "$deploiement"
  fi
fi
install -d -m 700 "$deploiement/sauvegardes" "$deploiement/unites"
install -m 700 "$checkout/deploiement/deployer.py" "$deploiement/deployer.py"

if [[ ! -s $deploiement/jeton ]]; then
  read -rsp "Jeton GitHub (Commit statuses: write, Actions: read) : " jeton
  echo
  [[ -n $jeton ]] || echec "jeton vide"
  (umask 077 && printf '%s\n' "$jeton" >"$deploiement/jeton")
  unset jeton
fi
chmod 600 "$deploiement/jeton"

if [[ ! -f $deploiement/etat.json ]]; then
  git -C "$checkout" diff --quiet HEAD -- || echec "fichiers suivis modifiés dans $checkout"
  sha=$(git -C "$checkout" rev-parse HEAD)
  echo "Amorçage : déploiement manuel de $sha"
  services=$(compose ps --status running --services) || echec "état de la pile illisible"
  if grep -qx db <<<"$services"; then
    sauvegarde="$deploiement/sauvegardes/$(date -u +%Y%m%dT%H%M%SZ)-installation.dump"
    (umask 077 && compose exec -T db sh -c 'pg_dump -Fc -U "$POSTGRES_USER" "$POSTGRES_DB"' \
      >"$sauvegarde") || {
      rm -f -- "$sauvegarde"
      echec "sauvegarde en échec"
    }
    echo "Sauvegarde : $sauvegarde"
  elif [[ ${OUTILLERIE_SANS_SAUVEGARDE:-} == 1 ]]; then
    echo "Base arrêtée : amorçage sans sauvegarde (OUTILLERIE_SANS_SAUVEGARDE=1)"
  else
    echec "base arrêtée, rien à sauvegarder avant les migrations : la démarrer" \
      "(docker compose -p $projet up -d db), ou relancer avec OUTILLERIE_SANS_SAUVEGARDE=1" \
      "si elle ne contient aucune donnée"
  fi
  APP_TAG=$sha compose build app
  APP_TAG=$sha compose up -d --wait --wait-timeout 120
  (umask 077 && printf '{"deployed": "%s", "previous": null, "failed": [], "attempts": {}, "blocked": false}\n' \
    "$sha" >"$deploiement/etat.json")
fi

sed -e "s|@COMPTE@|$compte|g" \
  -e "s|@CHECKOUT@|$checkout|g" \
  -e "s|@DEPLOIEMENT@|$deploiement|g" \
  -e "s|@PYTHON@|$(command -v python3)|g" \
  "$checkout/deploiement/outillerie-deploiement.service.in" \
  >"$deploiement/unites/outillerie-deploiement.service"
chmod 644 "$deploiement/unites/outillerie-deploiement.service"
install -m 644 "$checkout/deploiement/outillerie-deploiement.timer" "$deploiement/unites/"
sudo systemctl link "$deploiement/unites/outillerie-deploiement.service" \
  "$deploiement/unites/outillerie-deploiement.timer"
sudo systemctl daemon-reload
sudo systemctl enable --now outillerie-deploiement.timer

echo "Installé. Journal : journalctl -u outillerie-deploiement"
