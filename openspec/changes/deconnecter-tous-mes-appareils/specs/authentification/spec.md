## MODIFIED Requirements

### Requirement: Page de déconnexion
Le système SHALL servir sur `GET /logged-out` une page qui confirme la fin de la session, avec un
lien vers la connexion. Message : « Vous êtes déconnecté » par défaut ; pour le motif `inactivity`,
« Votre session a expiré après N minutes d'inactivité », N étant la durée d'expiration en vigueur ;
pour le motif `account-deleted`, « Votre compte a été supprimé » ; pour le motif `all-devices`,
« Tous vos appareils ont été déconnectés ».
Un utilisateur encore connecté MUST y être redirigé vers `/` sans être déconnecté.

#### Scenario: Page après une déconnexion
- **WHEN** un visiteur ouvre `/logged-out`
- **THEN** la page affiche « Vous êtes déconnecté » et un lien vers `/login`

#### Scenario: Page après une expiration
- **WHEN** un visiteur ouvre `/logged-out?reason=inactivity`
- **THEN** la page affiche « Votre session a expiré après 30 minutes d'inactivité » et un lien vers `/login`

#### Scenario: Page après la suppression du compte
- **WHEN** un visiteur ouvre `/logged-out?reason=account-deleted`
- **THEN** la page affiche « Votre compte a été supprimé » et un lien vers `/login`
- **AND** elle n'affiche pas « Vous êtes déconnecté »

#### Scenario: Page après la déconnexion de tous les appareils
- **WHEN** un visiteur ouvre `/logged-out?reason=all-devices`
- **THEN** la page affiche « Tous vos appareils ont été déconnectés » et un lien vers `/login`

#### Scenario: Durée affichée selon la configuration
- **WHEN** la durée d'expiration est configurée à 15 minutes et un visiteur ouvre `/logged-out?reason=inactivity`
- **THEN** la page affiche « Votre session a expiré après 15 minutes d'inactivité »

#### Scenario: Motif inconnu
- **WHEN** un visiteur ouvre `/logged-out?reason=autre`
- **THEN** la page affiche « Vous êtes déconnecté »

#### Scenario: Utilisateur encore connecté
- **WHEN** un utilisateur connecté ouvre `/logged-out?reason=inactivity`
- **THEN** il est redirigé vers `/`
- **AND** il reste connecté

### Requirement: Sessions d'un compte supprimé
Toute session ouverte d'un compte supprimé, dans n'importe quel navigateur, MUST être traitée comme
celle d'un visiteur dès sa requête suivante, sans attendre son expiration (ADR 0023). Il en va de
même d'un cookie persistant de ce compte. Hors suppression du compte, seule « Déconnecter tous mes
appareils » révoque les sessions et les cookies persistants d'un compte (ADR 0028) ; une future
fonction de changement ou de réinitialisation du mot de passe MUST les révoquer de la même façon.

#### Scenario: Session ouverte dans un autre navigateur
- **WHEN** Alice est connectée sur son ordinateur et sur son téléphone
- **AND** elle supprime son compte depuis son ordinateur
- **THEN** la requête suivante de son téléphone vers une page réservée la redirige vers `/login`

#### Scenario: Cookie copié
- **WHEN** une copie du cookie de session d'Alice est renvoyée après la suppression de son compte, avant 30 minutes
- **THEN** le système la traite comme un visiteur

#### Scenario: Cookie persistant copié
- **WHEN** une copie du cookie persistant d'Alice est renvoyée après la suppression de son compte
- **THEN** le système la traite comme un visiteur
