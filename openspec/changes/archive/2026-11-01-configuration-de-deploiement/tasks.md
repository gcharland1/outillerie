# Tasks

## 1. Environnement et cookie de session

- [x] 1.1 Lire `FLASK_ENVIRONMENT` une fois au début de `_initialize_app` (`development` par défaut), en déduire `SESSION_COOKIE_SECURE`, avant d'appliquer `test_config` ; réutiliser la valeur pour `load_dotenv()` ; vérifier par des tests pytest (`monkeypatch.setenv`/`delenv`) que le cookie posé à la connexion porte `Secure` en `production` et ne le porte pas en `development` ni sans la variable
- [x] 1.2 Vérifier que les tests existants passent toujours (`uv run pytest`), en particulier `tests/test_session.py`

## 2. Schéma relayé par le proxy

- [x] 2.1 Envelopper `app.wsgi_app` dans `ProxyFix(x_for=0, x_proto=1)` dans `create_app` ; vérifier par des tests pytest qu'avec `X-Forwarded-Proto: https` la requête est sécurisée et qu'une URL absolue générée commence par `https://`, et que sans l'en-tête elle commence par `http://`
- [x] 2.2 Ajouter un test CSRF (jeton activé) : un `POST` relayé avec `X-Forwarded-Proto: https` et un `Referer` de même origine est accepté, et le même `POST` sans `Referer` est refusé ; vérifier que les tests passent

## 3. Docker Compose

- [x] 3.1 Dans `compose.yaml`, lier les ports à `127.0.0.1` (`127.0.0.1:8080:5000`, `127.0.0.1:5430:5432`) et transmettre `FLASK_ENVIRONMENT: ${FLASK_ENVIRONMENT:-development}` au service `app` ; ajouter `FLASK_ENVIRONMENT=development` à `.env.example` ; vérifier avec `docker compose config` les liaisons et la valeur par défaut
- [x] 3.2 Vérifier en local que `docker compose up --build` sert l'app sur `http://localhost:8080`, que la connexion fonctionne (cookie sans `Secure`) et que `localhost:5430` joint la base
- [x] 3.3 Mettre à jour `README.md` et `CLAUDE.md` : ports liés à la boucle locale, rôle de `FLASK_ENVIRONMENT` ; vérifier que les commandes documentées fonctionnent telles qu'écrites

## 4. Vérification

- [x] 4.1 Exécuter `/verifier` et obtenir « terminé » (lint, format, tests sur Postgres, `flask db check`, `openspec validate`)

## Workflow follow-up

- Relecture par l'agent `relecteur` avant la PR.
- Mise en production selon le plan de `design.md` (Migration Plan), avant de pousser la branche.
- Archiver le changement avec `/opsx:archive` une fois la PR mergée.
