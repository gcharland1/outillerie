## 1. Schéma et modèle

- [ ] 1.1 `models/user.py` : `email_confirmed_at` et `email_confirmation_sent_at`, `DateTime(timezone=True)` nullables, et la propriété `email_confirmed`
- [ ] 1.2 Révision `uv run flask db migrate -m "Utilisateurs : confirmation du courriel"` sur une base dédiée, partant de la révision de `suppression-de-la-colonne-username` ; relire, renommer en ASCII ; `downgrade` supprime les deux colonnes ; `uv run flask db check` vide
- [ ] 1.3 Régénérer `docs/schema.md` (`uv run paracelsus inject ../docs/schema.md`) ; `--check` passe
- [ ] 1.4 `tests/test_schema.py` : colonnes nullables, comptes existants à `NULL` après l'`upgrade`, aller-retour `downgrade`/`upgrade`

## 2. Envoi

- [ ] 2.1 `uv add itsdangerous` ; `app/mail.py` : envoi selon le design (mémoire en tests, journal en développement sans `SMTP_HOST`, `smtplib` sinon) ; échec journalisé sans le lien
- [ ] 2.2 `_initialize_app` lit `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `MAIL_SENDER`, `SITE_URL` et refuse de démarrer hors `development` si l'une manque, en la nommant sans valeur ; `compose.yaml` et `.env.example` suivent
- [ ] 2.3 Tests : chaque variable manquante en `production` est nommée ; développement sans SMTP démarre et journalise le courriel ; envoi `smtplib` simulé (STARTTLS et SSL selon le port) ; échec SMTP journalisé sans le lien

## 3. Courriel, lien et confirmation

- [ ] 3.1 Courriel de confirmation (prénom, lien depuis `SITE_URL`, 30 jours, invitation à l'ignorer) et jeton signé `{id, email}` ; tests du contenu et de l'en-tête `Host` forgé
- [ ] 3.2 `register` : `email_confirmation_sent_at` à la création, envoi après le `commit`, message de succès ; tests, dont l'échec d'envoi
- [ ] 3.3 `GET /confirmer-courriel/<jeton>` et `confirm_email.html` : bouton, lien expiré, lien invalide (altéré, compte supprimé, courriel qui ne correspond plus), `Referrer-Policy: no-referrer`, aucune écriture ; tests
- [ ] 3.4 `POST /confirmer-courriel` : `UPDATE` conditionnel, redirection selon la session, jamais de `login_user`, message identique si déjà confirmé ; tests (sans session, session d'un autre compte, double envoi, jeton CSRF manquant avec `WTF_CSRF_ENABLED`, lien expiré entre l'ouverture et l'envoi)
- [ ] 3.5 Filtre du logger `werkzeug` qui masque le jeton ; test sur une ligne de requête

## 4. Profil, pastille, renvoi

- [ ] 4.1 Context processor du courriel à confirmer ; `base.html` : pastille sur « Mon profil » et total du nom ; tests de la pastille (compte confirmé, non confirmé, avec une demande de contact)
- [ ] 4.2 `profile/show.html` : bandeau et « Renvoyer le courriel » (`button primary`, POST avec `csrf_token`) ; tests (affiché ou non selon la confirmation)
- [ ] 4.3 `POST /profile/courriel/renvoyer` : verrou, compte déjà confirmé, délai de 5 minutes avec minutes restantes, envoi ; tests, dont deux renvois successifs sous le délai et l'ancien lien encore valide

## 5. Blocage des engagements

- [ ] 5.1 Fixtures de comptes confirmées par défaut, plus une fixture de compte non confirmé ; la suite existante passe
- [ ] 5.2 `loans.new` et `loans.create` : un compte non confirmé est ramené à la liste d'origine avec le message ; tests (page, envoi forgé, compte confirmé inchangé)
- [ ] 5.3 `loans.act` `accept` : refus avec le message pour un propriétaire non confirmé ; `refuse` et le suivi inchangés ; tests
- [ ] 5.4 `tools/_card.html` grise « Emprunter » et `loans/_buttons.html` grise « Accepter » pour un compte non confirmé (« Mes prêts » et accueil) ; tests

## 6. Fin

- [ ] 6.1 `/verifier` rend « terminé »
