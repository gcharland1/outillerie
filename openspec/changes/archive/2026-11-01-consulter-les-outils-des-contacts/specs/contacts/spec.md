# Spec Delta

## MODIFIED Requirements

### Requirement: Liste de mes contacts
La page « Mes contacts » SHALL lister les contacts de l'utilisateur, triés par nom d'utilisateur
sans égard à la casse, avec leur nom d'utilisateur, leur prénom, leur nom et l'action « Retirer ».
Le nom d'un contact mène à sa page. Sans contact, elle affiche « Vous n'avez encore aucun
contact ».

#### Scenario: Contacts listés
- **WHEN** Bob est en contact avec « carole » et « Alice »
- **THEN** sa page « Mes contacts » les liste dans l'ordre « Alice », « carole »

#### Scenario: Lien vers la page d'un contact
- **WHEN** Bob est en contact avec Alice et clique sur son nom dans « Mes contacts »
- **THEN** il arrive sur la page d'Alice

#### Scenario: Aucun contact
- **WHEN** Bob n'a aucun contact
- **THEN** sa page « Mes contacts » affiche « Vous n'avez encore aucun contact »

## ADDED Requirements

### Requirement: Page d'un contact
La page d'un contact SHALL afficher en titre son prénom, son nom et son nom d'utilisateur
(« Bob Gagnon (@bob) »), puis ses outils. Elle MUST NOT afficher son courriel, son adresse ni son
téléphone. Elle exige une session ouverte ; pour un compte qui n'est pas un contact de
l'utilisateur, l'utilisateur lui-même ou un compte inexistant, le système MUST répondre 404.

#### Scenario: Page d'un contact
- **WHEN** Alice et Bob Gagnon (« bob ») sont en contact et Alice ouvre la page de Bob
- **THEN** la page a pour titre « Bob Gagnon (@bob) »
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
