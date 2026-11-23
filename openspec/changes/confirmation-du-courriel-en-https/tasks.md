## 1. Correctif

- [x] 1.1 Test : confirmation envoyée en HTTPS avec CSRF, `Referer` selon la politique de la page ; il échoue avant le correctif ; le test de l'en-tête attend `same-origin`
- [x] 1.2 `app/auth.py` : `Referrer-Policy: same-origin` sur la page de confirmation

## 2. Fin

- [x] 2.1 `/verifier` rend « terminé »
