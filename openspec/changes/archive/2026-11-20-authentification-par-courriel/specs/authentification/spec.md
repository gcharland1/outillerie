## MODIFIED Requirements

### Requirement: Courriel unique
Le système MUST refuser de créer un compte avec un courriel déjà utilisé par un autre compte, sans
égard à la casse ni aux espaces autour, et l'indiquer sur la page d'inscription. Le message révèle
qu'un compte utilise ce courriel : la protection contre l'énumération des comptes ne vaut que pour
la connexion (ADR 0020).

#### Scenario: Courriel déjà utilisé
- **WHEN** un compte existe avec le courriel `alice@example.com`
- **AND** un visiteur soumet le formulaire d'inscription avec le courriel `Alice@Example.com`
- **THEN** aucun compte n'est créé
- **AND** la page d'inscription affiche « Le courriel est déjà utilisé »

#### Scenario: Courriel avec espaces déjà utilisé
- **WHEN** un compte existe avec le courriel `alice@example.com`
- **AND** un visiteur soumet le formulaire d'inscription avec le courriel « ␠alice@example.com␠ »
- **THEN** aucun compte n'est créé
- **AND** la page d'inscription affiche « Le courriel est déjà utilisé »

### Requirement: Création de compte
Le système SHALL créer un compte à partir d'un courriel, d'un mot de passe, d'un prénom et d'un
nom soumis sur la page `/register`, puis rediriger vers la page de connexion. Le courriel est
enregistré sans les espaces autour. Le formulaire MUST NOT demander de nom d'utilisateur.

#### Scenario: Inscription réussie
- **WHEN** un visiteur soumet le formulaire d'inscription avec un courriel libre et tous les champs remplis
- **THEN** un compte est créé avec ces informations
- **AND** le visiteur est redirigé vers `/login`

#### Scenario: Nom d'utilisateur déjà pris
- **WHEN** un visiteur ouvre la page d'inscription
- **THEN** le formulaire ne demande aucun nom d'utilisateur, et aucun nom n'est donc jamais « déjà pris »

#### Scenario: Espaces retirés
- **WHEN** un visiteur s'inscrit avec le courriel « ␠bob@example.com␠ »
- **THEN** le compte est enregistré avec le courriel `bob@example.com`

### Requirement: Connexion
Le système SHALL ouvrir une session pour l'utilisateur qui soumet sur `/login` son courriel et un
mot de passe valides, puis le rediriger vers la page d'accueil. Le courriel est comparé sans égard
à la casse ni aux espaces autour. La réponse à des identifiants invalides MUST NOT révéler, ni par
son contenu ni par son délai, si le courriel a un compte ; elle réaffiche le courriel saisi, jamais
le mot de passe.

#### Scenario: Identifiants valides
- **WHEN** un utilisateur soumet son courriel et son mot de passe corrects
- **THEN** il est redirigé vers `/`
- **AND** les requêtes suivantes le reconnaissent comme connecté

#### Scenario: Casse et espaces du courriel
- **WHEN** Alice, inscrite avec `alice@example.com`, soumet « ␠Alice@Example.COM␠ » et son mot de passe
- **THEN** elle est connectée

#### Scenario: Identifiants invalides
- **WHEN** un visiteur soumet un courriel inconnu ou un mot de passe erroné
- **THEN** aucune session n'est ouverte
- **AND** la page de connexion affiche « Le courriel ou le mot de passe est invalide », sans préciser lequel
- **AND** le champ du courriel contient le courriel saisi et celui du mot de passe est vide

#### Scenario: Nom inconnu indiscernable d'un mauvais mot de passe
- **WHEN** un visiteur soumet un courriel inconnu, puis un courriel existant avec un mot de passe erroné
- **THEN** les deux réponses sont identiques, au courriel réaffiché près
- **AND** dans les deux cas, le mot de passe soumis passe par la même vérification de hachage

#### Scenario: Nom d'utilisateur refusé
- **WHEN** un visiteur soumet `alice` au lieu de son courriel
- **THEN** aucune session n'est ouverte et la page affiche « Le courriel ou le mot de passe est invalide »

### Requirement: État de connexion dans la navigation
La barre de navigation SHALL afficher les liens « Connexion » et « Inscription » à un visiteur, et
le prénom suivi du nom de l'utilisateur avec un bouton « Me déconnecter » à un utilisateur connecté.

#### Scenario: Navigation d'un visiteur
- **WHEN** un visiteur ouvre une page du site
- **THEN** la navigation affiche « Connexion » et « Inscription »
- **AND** elle n'affiche pas « Me déconnecter »

#### Scenario: Navigation d'un utilisateur connecté
- **WHEN** Alice Tremblay, connectée, ouvre une page du site
- **THEN** la navigation affiche « Alice Tremblay » et le bouton « Me déconnecter »
- **AND** elle n'affiche ni « Connexion » ni « Inscription »
