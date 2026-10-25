---
status: accepted
date: 2026-10-25
decision-makers: Gabriel Charland
---

# Exposer la production par Cloudflare Tunnel, app en boucle locale

## Contexte et problème

En production, `cloudflared` (service systemd) relie le domaine à l'app servie par Docker Compose.
Cloudflare termine le TLS : l'app reçoit du HTTP et doit savoir qu'elle est servie en HTTPS. Il faut
fixer le seul chemin d'entrée de la production, les ports que Compose publie, et ce que Flask déduit
de son environnement. Issue #24, changement OpenSpec :
`openspec/changes/configuration-de-deploiement/`.

## Options considérées

* Cloudflare Tunnel seul point d'entrée : ports Compose liés à `127.0.0.1`, `ProxyFix` pour le
  schéma, cookies `Secure` hors développement
* `cloudflared` en service Compose, aucun port publié
* TLS sur le serveur (Caddy ou nginx avec certificat), ports 80 et 443 ouverts
* Ports publiés sur toutes les interfaces, filtrés par le pare-feu de l'hôte

## Décision

Option retenue : « Cloudflare Tunnel seul point d'entrée, ports liés à `127.0.0.1` », parce que le
tunnel n'exige aucun port entrant et que la boucle locale désigne le poste en développement et le
serveur en production : un seul `compose.yaml` sert aux deux, `localhost:8080` et `localhost:5430`
restent accessibles en développement.

* `compose.yaml` : `127.0.0.1:8080:5000` et `127.0.0.1:5430:5432` ; `FLASK_ENVIRONMENT` transmis
  au conteneur (`development` par défaut).
* Flask : `ProxyFix(x_for=0, x_proto=1)`, un seul proxy de confiance, schéma seulement, pour que `request.scheme` vaille `https`.
* Hors `development` : `SESSION_COOKIE_SECURE=True`.

`cloudflared` en Compose est écarté parce qu'il tourne déjà en systemd et qu'il ajouterait un jeton
de tunnel à gérer dans Compose. Le filtrage par pare-feu est écarté parce que Docker insère ses
règles iptables en amont de celles d'un pare-feu comme ufw : la liaison à `127.0.0.1` ne dépend
d'aucune règle. Un TLS sur le serveur dupliquerait ce que Cloudflare fournit déjà.

### Conséquences

* Bon, parce que tout trafic web passe par Cloudflare, chiffré, sans port entrant autre que SSH.
* Bon, parce que le développement ne change pas : mêmes ports, même fichier, aucun override.
* Mauvais, parce que `ProxyFix` croit l'en-tête `X-Forwarded-Proto` de tout processus local qui
  joint `127.0.0.1:8080`.
* Mauvais, parce qu'un appareil du réseau local ne joint plus l'app de développement sans un
  `compose.override.yaml` non versionné.
* Mauvais, parce que l'accès à la base de production passe par un tunnel SSH
  (`ssh -L 15430:127.0.0.1:5430 <serveur>`).
* Mauvais, parce que la production dépend de Cloudflare : sans tunnel, le site est injoignable.
