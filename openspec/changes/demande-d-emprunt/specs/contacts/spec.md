# Spec Delta

## MODIFIED Requirements

### Requirement: Pastille des demandes en attente
Quand un utilisateur connecté a des demandes reçues en attente, chaque page SHALL afficher une
pastille portant leur nombre à côté de « Mes contacts » dans le menu du compte, et une pastille
portant le total de ses demandes de contact et d'emprunt en attente à côté de son nom
d'utilisateur. Sans demande en attente, aucune pastille n'est affichée.

#### Scenario: Deux demandes en attente
- **WHEN** Alice et Carole ont chacune envoyé une demande à Bob
- **AND** Bob ouvre une page du site
- **THEN** une pastille « 2 » est affichée à côté de son nom d'utilisateur et à côté de « Mes contacts »

#### Scenario: Demandes de contact et d'emprunt
- **WHEN** Carole a envoyé une demande de contact à Bob et Alice a demandé la perceuse de Bob
- **AND** Bob ouvre une page du site
- **THEN** une pastille « 2 » est affichée à côté de son nom d'utilisateur
- **AND** une pastille « 1 » à côté de « Mes contacts » et une pastille « 1 » à côté de « Mes prêts »

#### Scenario: Aucune demande en attente
- **WHEN** Bob a accepté ou refusé toutes ses demandes reçues
- **THEN** aucune pastille n'est affichée

#### Scenario: Demande envoyée sans pastille
- **WHEN** Alice a envoyé une demande à Bob
- **AND** Alice ouvre une page du site
- **THEN** aucune pastille n'est affichée pour Alice

### Requirement: Retrait d'un contact
« Retirer » SHALL mener à une page de confirmation qui nomme le contact, avec « Retirer » et
« Annuler ». La confirmation défait la relation pour les deux voisins, sans les informer, et annule
les demandes d'emprunt en attente de l'un pour un outil de l'autre ; la page de confirmation
annonce leur nombre. Retirer quelqu'un qui n'est pas ou plus un contact MUST laisser tout
inchangé : redirection vers « Mes contacts » avec « Cette personne ne fait pas partie de vos
contacts ».

#### Scenario: Page de confirmation
- **WHEN** Bob clique « Retirer » à côté d'Alice
- **THEN** une page lui demande de confirmer le retrait d'Alice
- **AND** Alice et Bob sont toujours en contact

#### Scenario: Retrait confirmé
- **WHEN** Bob confirme le retrait d'Alice
- **THEN** Alice ne figure plus dans la liste de contacts de Bob
- **AND** Bob ne figure plus dans la liste de contacts d'Alice

#### Scenario: Demandes d'emprunt annulées
- **WHEN** Alice a demandé la perceuse de Bob et Bob a demandé la scie d'Alice, sans réponse
- **AND** Bob ouvre la confirmation du retrait d'Alice
- **THEN** la page annonce « 2 demandes d'emprunt en attente entre vous seront annulées »
- **AND** une fois le retrait confirmé, les deux demandes sont annulées

#### Scenario: Retrait déjà fait
- **WHEN** Bob a retiré Alice de ses contacts
- **AND** Bob soumet de nouveau la confirmation du retrait d'Alice
- **THEN** il est redirigé vers « Mes contacts », qui affiche « Cette personne ne fait pas partie de vos contacts »
