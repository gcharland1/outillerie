# Proposal

## Why

En production, Cloudflare Tunnel termine le TLS et relaie les requêtes en HTTP vers l'app : Flask
doit reconnaître qu'il est servi en HTTPS et marquer le cookie de session `Secure`. L'ADR 0015 fixe
le tunnel comme seul point d'entrée et les ports publiés sur la boucle locale ; ce changement
l'applique (issue #24).

## What Changes

- `compose.yaml` lie les ports publiés à la boucle locale : `127.0.0.1:8080:5000` (app) et
  `127.0.0.1:5430:5432` (db). Le développement garde `localhost:8080` et `localhost:5430`.
- `compose.yaml` transmet `FLASK_ENVIRONMENT` au conteneur de l'app, `development` par défaut ;
  `.env.example` documente la variable.
- La factory enveloppe l'app dans `ProxyFix(x_for=0, x_proto=1)` : derrière un proxy, `request.scheme` et les
  URL externes suivent `X-Forwarded-Proto`.
- Hors `development`, le cookie de session porte l'attribut `Secure`.

## Capabilities

### New Capabilities
- `deploiement`: comportement de l'app selon son environnement d'exécution et derrière le proxy
  qui termine le TLS (schéma des requêtes, attributs du cookie de session, ports publiés).

### Modified Capabilities

Aucune.

## Impact

- `compose.yaml`, `.env.example`, `application/app/__init__.py`, nouveaux tests pytest.
- Aucune dépendance ajoutée : `ProxyFix` vient de Werkzeug, déjà installé avec Flask.
- Aucun schéma ni migration.
- ADR concernés : 0015 (appliqué ici), 0001 (app factory), 0003 (Docker Compose), 0006 (attributs
  du cookie de session, complétés par `Secure`).
- Mise en production : le `.env` du serveur doit définir `FLASK_ENVIRONMENT=production`.

## Hors périmètre

- Remplacer le serveur de développement Flask (`app.run`) par un serveur WSGI de production.
- Configuration hors dépôt : tunnel et réglages Cloudflare, pare-feu et SSH du serveur.
- En-tête HSTS émis par l'app.
