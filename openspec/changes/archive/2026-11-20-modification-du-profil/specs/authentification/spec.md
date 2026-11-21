## MODIFIED Requirements

### Requirement: Courriel unique
Le système MUST refuser de créer un compte avec un courriel déjà utilisé par un autre compte, sans
égard à la casse ni aux espaces autour, et l'indiquer sur la page d'inscription. Le message révèle
qu'un compte utilise ce courriel : la protection contre l'énumération des comptes ne vaut que pour
la connexion (ADR 0020). Le courriel d'un compte supprimé est effacé (ADR 0023) : il est libre, et
le nouveau compte n'a aucun lien avec l'ancien.

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

#### Scenario: Courriel d'un compte supprimé
- **WHEN** Alice, inscrite avec `alice@example.com`, a supprimé son compte
- **AND** un visiteur s'inscrit avec `alice@example.com`
- **THEN** un nouveau compte est créé, sans les contacts, outils ni prêts de l'ancien

### Requirement: Connexion
Le système SHALL ouvrir une session pour l'utilisateur qui soumet sur `/login` son courriel et un
mot de passe valides, puis le rediriger vers la page d'accueil. Le courriel est comparé sans égard
à la casse ni aux espaces autour. La réponse à des identifiants invalides MUST NOT révéler, ni par
son contenu ni par son délai, si le courriel a un compte ; elle réaffiche le courriel saisi, jamais
le mot de passe. Un compte supprimé MUST NOT ouvrir de session.

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

#### Scenario: Compte supprimé
- **WHEN** Alice a supprimé son compte et soumet son ancien courriel et son ancien mot de passe
- **THEN** aucune session n'est ouverte
- **AND** la page affiche « Le courriel ou le mot de passe est invalide », comme pour un courriel inconnu

### Requirement: Page de déconnexion
Le système SHALL servir sur `GET /logged-out` une page qui confirme la fin de la session, avec un
lien vers la connexion. Message : « Vous êtes déconnecté » par défaut ; pour le motif `inactivity`,
« Votre session a expiré après N minutes d'inactivité », N étant la durée d'expiration en vigueur ;
pour le motif `account-deleted`, « Votre compte a été supprimé ».
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

## ADDED Requirements

### Requirement: Sessions d'un compte supprimé
Toute session ouverte d'un compte supprimé, dans n'importe quel navigateur, MUST être traitée comme
celle d'un visiteur dès sa requête suivante, sans attendre son expiration (ADR 0023).

#### Scenario: Session ouverte dans un autre navigateur
- **WHEN** Alice est connectée sur son ordinateur et sur son téléphone
- **AND** elle supprime son compte depuis son ordinateur
- **THEN** la requête suivante de son téléphone vers une page réservée la redirige vers `/login`

#### Scenario: Cookie copié
- **WHEN** une copie du cookie de session d'Alice est renvoyée après la suppression de son compte, avant 30 minutes
- **THEN** le système la traite comme un visiteur
