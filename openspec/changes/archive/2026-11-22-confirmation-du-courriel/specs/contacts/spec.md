## MODIFIED Requirements

### Requirement: Pastille des demandes en attente
Quand un utilisateur connecté a des demandes reçues en attente, chaque page SHALL afficher une
pastille portant leur nombre à côté de « Mes contacts » dans le menu du compte, et une pastille
portant le total de ses demandes de contact en attente, du nombre de la pastille de « Mes prêts » et
de celui de la pastille de « Mon profil » à côté de son nom. Sans rien en attente, aucune pastille
n'est affichée.

#### Scenario: Deux demandes en attente
- **WHEN** Alice et Carole ont chacune envoyé une demande à Bob
- **AND** Bob ouvre une page du site
- **THEN** une pastille « 2 » est affichée à côté de son nom et à côté de « Mes contacts »

#### Scenario: Demandes de contact et d'emprunt
- **WHEN** Carole a envoyé une demande de contact à Bob et Alice a demandé la perceuse de Bob
- **AND** Bob ouvre une page du site
- **THEN** une pastille « 2 » est affichée à côté de son nom
- **AND** une pastille « 1 » à côté de « Mes contacts » et une pastille « 1 » à côté de « Mes prêts »

#### Scenario: Demande de contact et retour à confirmer
- **WHEN** Carole a envoyé une demande de contact à Bob et Alice a déclaré avoir rendu la perceuse de Bob
- **AND** Bob ouvre une page du site
- **THEN** une pastille « 2 » est affichée à côté de son nom

#### Scenario: Courriel à confirmer
- **WHEN** Bob, non confirmé, a une demande de contact de Carole en attente
- **AND** Bob ouvre une page du site
- **THEN** une pastille « 2 » est affichée à côté de son nom

#### Scenario: Aucune demande en attente
- **WHEN** Bob, confirmé, a accepté ou refusé toutes ses demandes reçues et aucun prêt n'attend son action
- **THEN** aucune pastille n'est affichée

#### Scenario: Demande envoyée sans pastille
- **WHEN** Alice, confirmée, a envoyé une demande à Bob
- **AND** Alice ouvre une page du site
- **THEN** aucune pastille n'est affichée pour Alice
