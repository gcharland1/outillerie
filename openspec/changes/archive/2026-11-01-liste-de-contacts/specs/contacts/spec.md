# Spec Delta

## Purpose

Permettre à deux voisins de se lier comme contacts, par une demande que l'un envoie et que
l'autre accepte ou refuse, et à chacun de gérer sa liste de contacts.

## ADDED Requirements

### Requirement: Contacts réservés à un utilisateur connecté
Les pages et actions de contact MUST exiger une session ouverte : un visiteur est redirigé vers
`/login`. Un utilisateur SHALL n'agir que sur les demandes qu'il a reçues ; une demande adressée
à un autre compte répond 404 et n'est pas modifiée.

#### Scenario: Visiteur non connecté
- **WHEN** un visiteur demande la page « Mes contacts »
- **THEN** il est redirigé vers `/login`
- **AND** la page de connexion affiche « Veuillez vous connecter pour accéder à cette page »

#### Scenario: Demande adressée à un autre voisin
- **WHEN** Alice a envoyé une demande à Bob
- **AND** Carole soumet l'acceptation de cette demande
- **THEN** le système répond 404
- **AND** la demande reste en attente et aucune relation n'est créée

#### Scenario: Le demandeur ne peut pas accepter sa propre demande
- **WHEN** Alice a envoyé une demande à Bob
- **AND** Alice soumet l'acceptation de cette demande
- **THEN** le système répond 404
- **AND** Alice et Bob ne sont pas en contact

### Requirement: Envoi d'une demande de contact
Un utilisateur connecté SHALL pouvoir envoyer une demande de contact à un autre compte. Une
demande existe tant que le destinataire n'y a pas répondu. Entre deux voisins, il MUST exister au
plus une demande, dans un sens ou dans l'autre.

#### Scenario: Demande envoyée
- **WHEN** Alice envoie une demande à Bob
- **THEN** une demande d'Alice à Bob est enregistrée

#### Scenario: Second envoi
- **WHEN** Alice a une demande envoyée à Bob
- **AND** Alice soumet de nouveau une demande à Bob
- **THEN** il n'existe toujours qu'une demande d'Alice à Bob

#### Scenario: Demande à un contact
- **WHEN** Alice et Bob sont en contact
- **AND** Alice soumet une demande à Bob
- **THEN** aucune demande n'est enregistrée

#### Scenario: Demande à soi-même
- **WHEN** Alice soumet une demande à son propre compte
- **THEN** le système répond 404
- **AND** aucune demande n'est enregistrée

#### Scenario: Demande croisée
- **WHEN** Bob a une demande envoyée à Alice
- **AND** Alice soumet une demande à Bob
- **THEN** aucune nouvelle demande n'est enregistrée
- **AND** Alice est redirigée vers « Mes contacts », où la demande de Bob attend sa réponse

### Requirement: Demandes reçues
La page « Mes contacts » SHALL lister les demandes reçues de l'utilisateur, de la plus
ancienne à la plus récente, avec pour chacune le nom d'utilisateur, le prénom et le nom du
demandeur, et les actions « Accepter » et « Refuser ». Une demande envoyée par l'utilisateur n'y
figure pas.

#### Scenario: Demande reçue affichée
- **WHEN** Alice a envoyé une demande à Bob
- **AND** Bob ouvre « Mes contacts »
- **THEN** il voit la demande d'Alice, avec « Accepter » et « Refuser »

#### Scenario: Demande envoyée absente
- **WHEN** Alice a envoyé une demande à Bob
- **AND** Alice ouvre « Mes contacts »
- **THEN** la demande à Bob n'y figure pas

### Requirement: Acceptation d'une demande
Accepter une demande reçue SHALL supprimer la demande et lier les deux voisins comme contacts,
l'un pour l'autre.

#### Scenario: Demande acceptée
- **WHEN** Alice a envoyé une demande à Bob
- **AND** Bob clique « Accepter » à côté de la demande d'Alice
- **THEN** la demande n'existe plus et ne figure plus parmi les demandes reçues de Bob
- **AND** Alice figure dans la liste de contacts de Bob
- **AND** Bob figure dans la liste de contacts d'Alice

### Requirement: Refus d'une demande
Refuser une demande reçue SHALL supprimer la demande sans lier les deux voisins. Le demandeur
n'en est pas informé et peut envoyer une nouvelle demande.

#### Scenario: Demande refusée
- **WHEN** Alice a envoyé une demande à Bob
- **AND** Bob clique « Refuser » à côté de la demande d'Alice
- **THEN** la demande n'existe plus et ne figure plus parmi les demandes reçues de Bob
- **AND** Alice et Bob ne sont pas en contact

#### Scenario: Nouvelle demande après un refus
- **WHEN** Bob a refusé la demande d'Alice
- **AND** Alice envoie une nouvelle demande à Bob
- **THEN** une demande d'Alice à Bob est enregistrée

### Requirement: Demande qui n'existe plus
Répondre à une demande qui n'existe plus, parce qu'on y a déjà répondu (retour arrière, second
envoi), MUST laisser tout inchangé : l'utilisateur est redirigé vers « Mes contacts » avec le
message « Cette demande n'est plus en attente ».

#### Scenario: Refus après acceptation
- **WHEN** Bob a accepté la demande d'Alice
- **AND** Bob soumet le refus de la même demande
- **THEN** il est redirigé vers « Mes contacts », qui affiche « Cette demande n'est plus en attente »
- **AND** Alice et Bob restent en contact

### Requirement: Liste de mes contacts
La page « Mes contacts » SHALL lister les contacts de l'utilisateur, triés par nom d'utilisateur
sans égard à la casse, avec leur nom d'utilisateur, leur prénom, leur nom et l'action « Retirer ».
Sans contact, elle affiche « Vous n'avez encore aucun contact ».

#### Scenario: Contacts listés
- **WHEN** Bob est en contact avec « carole » et « Alice »
- **THEN** sa page « Mes contacts » les liste dans l'ordre « Alice », « carole »

#### Scenario: Aucun contact
- **WHEN** Bob n'a aucun contact
- **THEN** sa page « Mes contacts » affiche « Vous n'avez encore aucun contact »

### Requirement: Retrait d'un contact
« Retirer » SHALL mener à une page de confirmation qui nomme le contact, avec « Retirer » et
« Annuler ». La confirmation défait la relation pour les deux voisins, sans les informer. Retirer
quelqu'un qui n'est pas ou plus un contact MUST laisser tout inchangé : redirection vers « Mes
contacts » avec « Cette personne ne fait pas partie de vos contacts ».

#### Scenario: Page de confirmation
- **WHEN** Bob clique « Retirer » à côté d'Alice
- **THEN** une page lui demande de confirmer le retrait d'Alice
- **AND** Alice et Bob sont toujours en contact

#### Scenario: Retrait confirmé
- **WHEN** Bob confirme le retrait d'Alice
- **THEN** Alice ne figure plus dans la liste de contacts de Bob
- **AND** Bob ne figure plus dans la liste de contacts d'Alice

#### Scenario: Retrait déjà fait
- **WHEN** Bob a retiré Alice de ses contacts
- **AND** Bob soumet de nouveau la confirmation du retrait d'Alice
- **THEN** il est redirigé vers « Mes contacts », qui affiche « Cette personne ne fait pas partie de vos contacts »

### Requirement: Accès depuis le menu du compte
Le menu du compte d'un utilisateur connecté SHALL contenir « Mes contacts », qui mène à la page
« Mes contacts ». La navigation d'un visiteur MUST NOT l'offrir.

#### Scenario: Utilisateur connecté
- **WHEN** un utilisateur connecté ouvre son menu du compte
- **THEN** il contient « Mes contacts »

#### Scenario: Visiteur
- **WHEN** un visiteur ouvre une page du site
- **THEN** la navigation ne contient pas « Mes contacts »

### Requirement: Pastille des demandes en attente
Quand un utilisateur connecté a des demandes reçues en attente, chaque page SHALL afficher une
pastille portant leur nombre à côté de son nom d'utilisateur et à côté de « Mes contacts » dans le
menu du compte. Sans demande en attente, aucune pastille n'est affichée.

#### Scenario: Deux demandes en attente
- **WHEN** Alice et Carole ont chacune envoyé une demande à Bob
- **AND** Bob ouvre une page du site
- **THEN** une pastille « 2 » est affichée à côté de son nom d'utilisateur et à côté de « Mes contacts »

#### Scenario: Aucune demande en attente
- **WHEN** Bob a accepté ou refusé toutes ses demandes reçues
- **THEN** aucune pastille n'est affichée

#### Scenario: Demande envoyée sans pastille
- **WHEN** Alice a envoyé une demande à Bob
- **AND** Alice ouvre une page du site
- **THEN** aucune pastille n'est affichée pour Alice
