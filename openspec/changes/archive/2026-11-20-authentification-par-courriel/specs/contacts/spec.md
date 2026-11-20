## MODIFIED Requirements

### Requirement: Demandes reçues
La page « Mes contacts » SHALL lister les demandes reçues de l'utilisateur, de la plus
ancienne à la plus récente, avec pour chacune le prénom et le nom du demandeur, et les actions « Accepter » et « Refuser ». Une demande envoyée par l'utilisateur n'y
figure pas.

#### Scenario: Demande reçue affichée
- **WHEN** Alice a envoyé une demande à Bob
- **AND** Bob ouvre « Mes contacts »
- **THEN** il voit la demande d'Alice, avec « Accepter » et « Refuser »

#### Scenario: Demande envoyée absente
- **WHEN** Alice a envoyé une demande à Bob
- **AND** Alice ouvre « Mes contacts »
- **THEN** la demande à Bob n'y figure pas

### Requirement: Liste de mes contacts
La page « Mes contacts » SHALL lister les contacts de l'utilisateur, triés par prénom, puis nom,
sans égard à la casse ni aux accents, puis du plus ancien compte au plus récent, avec leur prénom,
leur nom et l'action « Retirer ».
Le nom d'un contact mène à sa page. Sans contact, elle affiche « Vous n'avez encore aucun
contact ».

#### Scenario: Contacts listés
- **WHEN** Bob est en contact avec Élise Roy, carole Roy et Alice Tremblay
- **THEN** sa page « Mes contacts » les liste dans l'ordre Alice Tremblay, carole Roy, Élise Roy

#### Scenario: Lien vers la page d'un contact
- **WHEN** Bob est en contact avec Alice et clique sur son nom dans « Mes contacts »
- **THEN** il arrive sur la page d'Alice

#### Scenario: Aucun contact
- **WHEN** Bob n'a aucun contact
- **THEN** sa page « Mes contacts » affiche « Vous n'avez encore aucun contact »

### Requirement: Pastille des demandes en attente
Quand un utilisateur connecté a des demandes reçues en attente, chaque page SHALL afficher une
pastille portant leur nombre à côté de « Mes contacts » dans le menu du compte, et une pastille
portant le total de ses demandes de contact en attente et du nombre de la pastille de « Mes prêts »
à côté de son nom. Sans rien en attente, aucune pastille n'est affichée.

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

#### Scenario: Aucune demande en attente
- **WHEN** Bob a accepté ou refusé toutes ses demandes reçues et aucun prêt n'attend son action
- **THEN** aucune pastille n'est affichée

#### Scenario: Demande envoyée sans pastille
- **WHEN** Alice a envoyé une demande à Bob
- **AND** Alice ouvre une page du site
- **THEN** aucune pastille n'est affichée pour Alice

### Requirement: Page d'un contact
La page d'un contact SHALL afficher en titre son prénom et son nom (« Bob Gagnon »), puis ses
outils. Elle MUST NOT afficher son courriel, son adresse ni son
téléphone. Elle exige une session ouverte ; pour un compte qui n'est pas un contact de
l'utilisateur, l'utilisateur lui-même ou un compte inexistant, le système MUST répondre 404.

#### Scenario: Page d'un contact
- **WHEN** Alice et Bob Gagnon sont en contact et Alice ouvre la page de Bob
- **THEN** la page a pour titre « Bob Gagnon »
- **AND** elle n'affiche ni son courriel, ni son adresse, ni son téléphone

#### Scenario: Non-contact
- **WHEN** Alice n'est pas en contact avec Carole et demande la page de Carole
- **THEN** le système répond 404

#### Scenario: Demande en attente
- **WHEN** Alice a envoyé à Carole une demande de contact qui attend une réponse
- **AND** Alice demande la page de Carole
- **THEN** le système répond 404

#### Scenario: Sa propre page
- **WHEN** Alice demande la page de contact de son propre compte
- **THEN** le système répond 404

#### Scenario: Visiteur
- **WHEN** un visiteur demande la page d'un compte
- **THEN** il est redirigé vers `/login`
