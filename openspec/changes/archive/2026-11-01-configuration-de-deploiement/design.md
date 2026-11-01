# Design

## Context

Voir proposal.md (Why) et l'ADR 0015. État actuel du code :

- `_initialize_app` (`application/app/__init__.py`) fixe les attributs du cookie de session, puis
  retourne tôt quand une `test_config` est fournie ; `FLASK_ENVIRONMENT` n'est lu qu'après ce retour,
  pour décider de `load_dotenv()`.
- Les tests créent l'app par `create_app(app_config())` (`tests/conftest.py`) : tout réglage placé
  après le retour anticipé n'est pas testable.
- Flask-WTF, quand `request.is_secure` est vrai, exige un en-tête `Referer` de même origine que
  `https://<host>/` sur les requêtes protégées (`WTF_CSRF_SSL_STRICT`, vrai par défaut). Aujourd'hui
  la vérification ne s'active jamais, puisque Flask ne voit que du HTTP.

## Goals / Non-Goals

**Goals:**
- Un seul `compose.yaml` pour le développement et la production.
- Rendre le schéma et le cookie `Secure` testables par pytest, sans Docker.

**Non-Goals:**
- Croire `X-Forwarded-For`, `X-Forwarded-Host` ou `X-Forwarded-Prefix` : aucun code n'utilise
  l'adresse du client, et `cloudflared` conserve l'en-tête `Host`.
- Tester les ports de Compose par pytest.

## Decisions

### `ProxyFix(x_for=0, x_proto=1)` appliqué dans `create_app`, tests compris

`ProxyFix` croit `X-Forwarded-For` par défaut (`x_for=1`) ; le mettre explicitement à 0 limite la
confiance au schéma, comme le décide l'ADR 0015. L'envelopper dans `create_app`, après la
configuration, l'applique aussi aux apps de test : un test peut envoyer `X-Forwarded-Proto: https`
au client de test.

Alternative écartée : ne l'activer que hors `development`. Le comportement testé différerait de
celui de la production, et un proxy local de développement ne gagnerait rien à l'absence.

### Environnement lu avant le retour anticipé de `test_config`

`_initialize_app` lit `FLASK_ENVIRONMENT` une fois, au début, et en déduit
`SESSION_COOKIE_SECURE = environment != "development"`, avant d'appliquer `test_config`. Un test
choisit l'environnement par `monkeypatch.setenv`, et `test_config` reste libre de surcharger la valeur.

Alternative écartée : passer `SESSION_COOKIE_SECURE` dans `test_config`. Le test vérifierait sa
propre configuration, pas la déduction tirée de l'environnement.

### Compose : adresse d'hôte explicite et variable transmise

`ports` devient `"127.0.0.1:8080:5000"` et `"127.0.0.1:5430:5432"`. Le service `app` reçoit
`FLASK_ENVIRONMENT: ${FLASK_ENVIRONMENT:-development}`, sur le modèle des variables déjà
transmises. `.env.example` ajoute `FLASK_ENVIRONMENT=development`.

### Vérification stricte du `Referer` conservée

Derrière le proxy, `request.is_secure` devient vrai et Flask-WTF exige un `Referer` de même origine.
Les navigateurs l'envoient pour un formulaire soumis depuis le site (politique par défaut
`strict-origin-when-cross-origin`) et l'app ne pose aucune `Referrer-Policy`. La vérification
s'ajoute au jeton CSRF (ADR 0012) sans le remplacer ; un test couvre un `POST` relayé en HTTPS.

Alternative écartée : `WTF_CSRF_SSL_STRICT = False`. Elle retirerait une défense gratuite.

## Risks / Trade-offs

- [Un navigateur ou une extension qui retire le `Referer` voit ses formulaires refusés en production]
  → La page d'erreur CSRF existante invite à recharger ; à revoir si des cas réels apparaissent.
- [`ProxyFix` croit `X-Forwarded-Proto` de tout processus local qui joint `127.0.0.1:8080`]
  → Accepté par l'ADR 0015 ; l'en-tête ne change que le schéma perçu.
- [Le `.env` de production sans `FLASK_ENVIRONMENT=production` laisse le cookie sans `Secure`]
  → Étape explicite du plan de mise en production.
- [Les URL `http://localhost:8080` de développement : le cookie sans `Secure` y reste nécessaire]
  → Garanti par la valeur par défaut `development`.

## Migration Plan

1. Ajouter `FLASK_ENVIRONMENT=production` au `.env` du serveur.
2. Déployer la branche, puis `docker compose up -d --build` : Compose recrée les conteneurs avec les
   nouvelles liaisons de ports.
3. Vérifier : le site répond par le domaine ; une connexion pose un cookie `Secure` ; les ports 8080
   et 5430 ne répondent pas depuis une autre machine.

Retour arrière : redéployer la révision précédente de `compose.yaml` et de l'app.
