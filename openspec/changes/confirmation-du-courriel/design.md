# Design

Décisions et sources : [questions.md](questions.md). Décision d'architecture : ADR 0027.
Motivation : [proposal.md](proposal.md).

## Ordre de livraison

Livré dans la seconde PR, avec `tests-une-seule-fois-par-livraison`, après
`suppression-de-la-colonne-username` (sa question 11). La révision de ce changement part de celle qui
supprime `username`.

Précondition de merge, hors des tâches : l'utilisateur a choisi le fournisseur SMTP, réglé SPF et
DKIM du domaine d'envoi et rempli le `.env` du serveur (`SMTP_*`, `MAIL_SENDER`, `SITE_URL`) ; il le
confirme avec son accord sur la spec (question 1). Sans ces variables, l'app refuse de démarrer en
production : le déploiement échouerait et reviendrait à l'image précédente (ADR 0017).

## Envoi

Module `app/mail.py` :

- `send(app, message)` choisit l'envoi selon la configuration : en `TESTING`, le message va dans
  `app.extensions["mail_outbox"]` (liste) ; en développement sans `SMTP_HOST`, il est écrit dans le
  journal de l'app, au niveau `WARNING` pour passer le niveau par défaut ; sinon `smtplib.SMTP(host, port)` avec `starttls()` puis `login`, ou
  `smtplib.SMTP_SSL` quand le port est 465.
- Configuration lue dans `_initialize_app`, comme `_secret_key` : hors `development`, une variable
  `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `MAIL_SENDER` ou `SITE_URL` absente ou
  vide lève une erreur qui la nomme, sans valeur. Les tests passent la leur par `app_config()`.
- `compose.yaml` passe ces variables à l'app ; `.env.example` les liste vides, avec un commentaire.
- Un échec, quelle que soit l'exception, est journalisé par son type, sans le corps ni le lien ;
  l'appelant continue.

## Jeton

`URLSafeTimedSerializer(SECRET_KEY, salt="confirmation-courriel")` sur `{"id": <id>, "email": <courriel>}`,
vérifié par `loads(max_age=30 jours)`. `itsdangerous` est déclaré en dépendance directe (`uv add`),
car l'app l'importe ; il est déjà installé par Flask. Pas d'usage unique : confirmer est idempotent.
Changer `FLASK_SECRET_KEY` invalide tous les liens en circulation (ADR 0027).

Le compte du jeton est valide si `id` existe, `deleted_at IS NULL` et son courriel égale celui du
jeton sans tenir compte de la casse. Sinon : « Ce lien n'est pas valide. ».

## Schéma

Révision `Utilisateurs : confirmation du courriel` : `user.email_confirmed_at` et
`user.email_confirmation_sent_at`, `timestamptz` nullables, sans `server_default` ; les comptes
existants restent `NULL`, donc non confirmés (question 5). `downgrade` supprime les deux colonnes.
Passe *expand* seule (ADR 0007) : l'image précédente les ignore.

## Routes

- `GET /confirmer-courriel/<jeton>` (blueprint `auth`) : vérifie le jeton, rend
  `confirm_email.html` (étend `base.html`) avec le bouton ou le message d'erreur ; en-tête
  `Referrer-Policy: no-referrer` sur la réponse. Aucune écriture.
- `POST /confirmer-courriel` : champ caché `token` plus `csrf_token` (ADR 0012 ; la page crée la
  session qui le porte). `UPDATE "user" SET email_confirmed_at = now() WHERE id = :id AND
  lower(email) = lower(:email) AND deleted_at IS NULL AND email_confirmed_at IS NULL` ; zéro ligne
  touchée sur un compte déjà confirmé donne le même message. Redirection vers `profile.show` si
  `current_user` est authentifié, sinon `auth.login`, avec le message de succès. N'appelle jamais
  `login_user`.
- `POST /profile/courriel/renvoyer` (blueprint `profile`, `login_required`) : `SELECT … FOR UPDATE`
  sur le compte, refus si confirmé ou si `email_confirmation_sent_at` date de moins de 5 minutes
  (minutes restantes arrondies vers le haut), sinon pose `email_confirmation_sent_at = now()`,
  `commit`, puis envoi. Le verrou fait qu'un seul de deux renvois simultanés envoie.
- `register` : `email_confirmation_sent_at = now()` à la création, `commit`, puis envoi hors
  transaction ; message de succès dans tous les cas.

## Blocage

Propriété `User.email_confirmed` (`email_confirmed_at is not None`).

- `loans.new` et `loans.create` : après les vérifications de « Outil qu'on peut demander », un compte
  non confirmé est ramené à la liste d'origine (même calcul que « Annuler ») avec le message.
- `loans.act` avec `accept` : après le verrou et les vérifications existantes, un propriétaire non
  confirmé est ramené à l'origine avec le message, sans transition. `refuse` et le suivi ne changent
  pas.
- Gabarits : `tools/_card.html` grise « Emprunter » (`button` désactivé) ; `loans/_buttons.html` grise
  « Accepter » sur « Mes prêts » et l'accueil, avec le même rendu qu'un bouton désactivé (ADR 0022 :
  gris).

## Pastille et bandeau

- Context processor `inject_email_to_confirm` (blueprint `profile`) : `1` pour un compte connecté non
  confirmé, `0` sinon. `base.html` l'ajoute au total du `summary` et met `pending_badge(...,
  "courriel à confirmer", ...)` sur « Mon profil ».
- `profile/show.html` : première `section.card` du bandeau, texte de la spec, formulaire POST
  « Renvoyer le courriel » en `button primary` dans `<div class="actions">`.

## Journal

Un filtre `logging.Filter` sur le logger `werkzeug` remplace le segment après `/confirmer-courriel/`
par `…` dans le message formaté, installé par `create_app`. Les journaux de Cloudflare Tunnel peuvent
garder l'URL : risque accepté dans l'ADR 0027.

## Tests

- Fixture `mail_outbox` ; `app_config()` gagne les variables SMTP factices.
- Les fixtures `user`, `bob`, `carole`, `make_user` créent des comptes confirmés ; une fixture crée un
  compte non confirmé.
- Expiration testée avec la fixture `clock` (`TimestampSigner.get_timestamp`), en gardant en tête
  qu'elle fige aussi la signature du cookie de session.

## Limites connues

- Comptes existants non confirmés au déploiement : ils doivent se faire renvoyer le courriel avant
  d'emprunter ou d'accepter ; leurs demandes reçues en attente ne peuvent qu'être refusées ou
  expirer en attendant (question 5).
- Squat d'adresse par un compte jamais confirmé : accepté, issue de suivi (question 16).
- Inscriptions en masse vers des adresses de tiers : aucune limite de débit (question 18).
- Retour à l'image précédente : la confirmation n'est plus exigée et les inscriptions n'envoient
  rien jusqu'au redéploiement (question 19).
- La livraison ne vérifie pas un vrai envoi SMTP : la réception d'un courriel réel se constate après
  le déploiement.
