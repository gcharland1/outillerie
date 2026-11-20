## MODIFIED Requirements

### Requirement: Accès depuis la navigation
Pour un utilisateur connecté, la barre de navigation SHALL offrir un menu du compte, ouvert en
cliquant sur son prénom et son nom, qui contient « Gérer mes outils » vers la page « Mes outils ».
« Me déconnecter » reste visible hors du menu. La navigation MUST NOT offrir « Gérer mes outils »
à un visiteur.

#### Scenario: Utilisateur connecté
- **WHEN** un utilisateur connecté ouvre une page du site
- **THEN** son prénom et son nom ouvrent un menu qui contient « Gérer mes outils »
- **AND** « Me déconnecter » est affiché hors de ce menu

#### Scenario: Visiteur
- **WHEN** un visiteur ouvre une page du site
- **THEN** la navigation ne contient pas « Gérer mes outils »
