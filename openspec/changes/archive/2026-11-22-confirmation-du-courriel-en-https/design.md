# Design

Motivation : [proposal.md](proposal.md).

- `_render_confirm_email` (`app/auth.py`) pose `Referrer-Policy: same-origin` au lieu de `no-referrer`.
  Avec `same-origin`, le navigateur envoie le `Referer` complet vers le site lui-même et rien vers un
  autre site (Training) : le POST du bouton porte l'adresse de la page, de même origine, que Flask-WTF
  accepte en HTTPS.
- Ce `Referer` contient le jeton et arrive au serveur de l'app ; Werkzeug ne journalise pas cet en-tête,
  seulement la ligne de requête, déjà masquée.
- Test : requêtes relayées avec `X-Forwarded-Proto: https`, comme par Cloudflare Tunnel, CSRF actif ; le POST porte le `Referer` qu'un navigateur enverrait selon
  la politique lue dans la réponse de la page (aucun pour `no-referrer`). Il échoue avec `no-referrer`
  et passe avec `same-origin`.

## Limites

- Le test simule le navigateur ; le comportement réel se constate en production après le déploiement.
