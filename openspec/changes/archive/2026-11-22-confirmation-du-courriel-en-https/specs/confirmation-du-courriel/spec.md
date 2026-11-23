## MODIFIED Requirements

### Requirement: Page de confirmation
Le lien de confirmation SHALL ouvrir, sans exiger de session, une page « Confirmer mon courriel » avec
un bouton « Confirmer mon courriel ». Ouvrir la page MUST NOT confirmer le compte. La réponse MUST
porter l'en-tête `Referrer-Policy: same-origin`, pour que l'adresse de la page, qui contient le jeton,
ne parte vers aucun autre site, tout en laissant le bouton passer la protection CSRF en HTTPS.

#### Scenario: Ouverture du lien
- **WHEN** Alice ouvre le lien de son courriel de confirmation
- **THEN** la page affiche le bouton « Confirmer mon courriel »
- **AND** son compte n'est pas encore confirmé

#### Scenario: En-tête Referer
- **WHEN** la page de confirmation est servie
- **THEN** sa réponse porte `Referrer-Policy: same-origin`

#### Scenario: Confirmation en HTTPS
- **WHEN** Alice, sur le site servi en HTTPS, clique « Confirmer mon courriel » depuis la page du lien
- **THEN** son compte est confirmé
