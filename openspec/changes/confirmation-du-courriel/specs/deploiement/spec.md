## ADDED Requirements

### Requirement: Envoi de courriels configuré hors développement
Hors de l'environnement `development`, l'app MUST refuser de démarrer quand l'une des variables
`SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `MAIL_SENDER` ou `SITE_URL` est absente ou
vide, avec un message qui nomme la variable sans afficher sa valeur. En `development`, sans
`SMTP_HOST`, l'app SHALL démarrer et écrire les courriels dans son journal au lieu de les envoyer.

#### Scenario: Variable absente en production
- **WHEN** l'app démarre en `production` sans `SMTP_PASSWORD`
- **THEN** elle refuse de démarrer avec un message qui nomme `SMTP_PASSWORD`

#### Scenario: Développement sans SMTP
- **WHEN** l'app démarre en `development` sans `SMTP_HOST`
- **THEN** elle démarre, et un courriel de confirmation est écrit dans son journal au lieu d'être envoyé
