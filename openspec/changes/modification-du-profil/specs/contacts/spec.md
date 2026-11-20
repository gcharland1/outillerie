## MODIFIED Requirements

### Requirement: Envoi d'une demande de contact
Un utilisateur connecté SHALL pouvoir envoyer une demande de contact à un autre compte. Une
demande existe tant que le destinataire n'y a pas répondu. Entre deux voisins, il MUST exister au
plus une demande, dans un sens ou dans l'autre. Une demande à un compte supprimé (ADR 0023) MUST
être refusée par une réponse 404, sans rien enregistrer.

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

#### Scenario: Demande à un compte supprimé
- **WHEN** Bob a supprimé son compte
- **AND** Alice soumet une demande à Bob, par exemple depuis une page de résultats ouverte avant la suppression
- **THEN** le système répond 404
- **AND** aucune demande n'est enregistrée

### Requirement: Page d'un contact
La page d'un contact SHALL afficher en titre son prénom et son nom (« Bob Gagnon »), puis ses
outils. Elle MUST NOT afficher son courriel, son adresse ni son
téléphone. Elle exige une session ouverte ; pour un compte qui n'est pas un contact de
l'utilisateur, l'utilisateur lui-même, un compte supprimé ou un compte inexistant, le système MUST
répondre 404.

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

#### Scenario: Ancien contact supprimé
- **WHEN** Alice et Bob étaient en contact et Bob a supprimé son compte
- **AND** Alice demande la page de Bob
- **THEN** le système répond 404

#### Scenario: Visiteur
- **WHEN** un visiteur demande la page d'un compte
- **THEN** il est redirigé vers `/login`
