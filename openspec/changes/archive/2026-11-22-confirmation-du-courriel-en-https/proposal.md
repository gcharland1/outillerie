# Proposal

## Why

En production, « Confirmer mon courriel » répond « Formulaire refusé » : aucun compte ne peut
confirmer son courriel, donc ni emprunter ni accepter une demande. La page de confirmation porte
`Referrer-Policy: no-referrer` ; le navigateur n'envoie alors aucun `Referer` avec le POST du bouton,
et Flask-WTF refuse toute requête HTTPS sans `Referer` de même origine (`WTF_CSRF_SSL_STRICT`, vrai par
défaut, `flask_wtf/csrf.py:291-293`). Derrière Cloudflare Tunnel, `ProxyFix` rend chaque requête HTTPS
(ADR 0015). Les tests passaient en HTTP, où ce contrôle ne s'applique pas.

## What Changes

- La page de confirmation porte `Referrer-Policy: same-origin` : le `Referer`, qui contient le jeton,
  part seulement vers le site lui-même, jamais vers un autre site, et le POST passe le contrôle de
  Flask-WTF.
- Un test envoie la confirmation en HTTPS avec CSRF, comme un navigateur qui suit la politique de la page.

Hors périmètre : désactiver `WTF_CSRF_SSL_STRICT`, qui affaiblirait la protection CSRF de tout le site
(ADR 0012).

## Capabilities

### Modified Capabilities
- `confirmation-du-courriel` : « Page de confirmation » exige `Referrer-Policy: same-origin`.

## Impact

`application/app/auth.py`, `application/tests/test_email_confirmation.py`. Aucun schéma, aucune
dépendance ; l'ADR 0027 ne cite pas l'en-tête.
