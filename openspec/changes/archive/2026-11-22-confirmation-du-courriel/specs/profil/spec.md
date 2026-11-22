## MODIFIED Requirements

### Requirement: Accès depuis le menu du compte
Le menu du compte d'un utilisateur connecté SHALL avoir « Mon profil » pour première entrée, un lien
texte vers `/profile` comme les autres entrées du menu, et non plus une entrée grisée. Pour un compte
non confirmé, « Mon profil » SHALL porter une pastille « 1 », annoncée « courriel à confirmer » aux
lecteurs d'écran. La navigation d'un visiteur MUST NOT l'offrir.

#### Scenario: Première entrée du menu
- **WHEN** un utilisateur connecté ouvre son menu du compte
- **THEN** sa première entrée est le lien « Mon profil », vers `/profile`, avant « Gérer mes outils »

#### Scenario: Compte non confirmé
- **WHEN** Alice, non confirmée, ouvre une page du site
- **THEN** « Mon profil » porte une pastille « 1 » dans son menu du compte

#### Scenario: Compte confirmé
- **WHEN** Alice, confirmée, ouvre une page du site
- **THEN** « Mon profil » ne porte aucune pastille

#### Scenario: Visiteur
- **WHEN** un visiteur ouvre une page du site
- **THEN** la navigation ne contient pas « Mon profil »

### Requirement: Informations du profil
La page « Mon profil » SHALL afficher le prénom, le nom et le courriel de l'utilisateur en texte, sans
champ pour les modifier, et un formulaire avec son adresse et son téléphone actuels, vides s'il n'en a
pas, et le bouton « Enregistrer ». Pour un compte non confirmé, elle SHALL commencer par un bandeau
« Votre courriel n'est pas confirmé. Confirmez-le avec le lien reçu à <courriel> pour emprunter et
accepter des demandes. » suivi du bouton « Renvoyer le courriel ».

#### Scenario: Page du profil
- **WHEN** Alice Tremblay, inscrite avec `alice@example.com`, adresse « 12 rue des Érables » et sans téléphone, ouvre « Mon profil »
- **THEN** la page affiche « Alice Tremblay » et `alice@example.com`, sans champ pour les modifier
- **AND** le champ de l'adresse contient « 12 rue des Érables » et celui du téléphone est vide

#### Scenario: Bandeau d'un compte non confirmé
- **WHEN** Alice, non confirmée, ouvre « Mon profil »
- **THEN** la page commence par « Votre courriel n'est pas confirmé. Confirmez-le avec le lien reçu à alice@example.com pour emprunter et accepter des demandes. » et le bouton « Renvoyer le courriel »

#### Scenario: Compte confirmé
- **WHEN** Alice, confirmée, ouvre « Mon profil »
- **THEN** la page n'affiche ni le bandeau ni « Renvoyer le courriel »

#### Scenario: Nom et courriel non modifiables
- **WHEN** Alice envoie le formulaire du profil avec en plus un prénom, un nom et un courriel différents
- **THEN** son prénom, son nom et son courriel ne changent pas
