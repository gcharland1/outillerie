# authentification Specification

## Purpose
Permettre à un voisin de créer un compte, de s'y connecter et de fermer sa session, que ce soit
volontairement ou après une période d'inactivité, sans exposer son mot de passe.

## Requirements

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

### Requirement: Mot de passe jamais stocké en clair
Le système MUST conserver le mot de passe d'un compte uniquement sous forme de hachage salé ; le
mot de passe soumis ne SHALL jamais être enregistré ni affiché tel quel.

#### Scenario: Hachage à l'inscription
- **WHEN** un compte est créé avec le mot de passe `secret123`
- **THEN** la valeur enregistrée pour le mot de passe est différente de `secret123`
- **AND** elle permet de vérifier `secret123` à la connexion

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

### Requirement: Déconnexion
Le système SHALL fermer la session de l'utilisateur sur une requête `POST /logout`, puis le
rediriger vers la page de déconnexion avec le message « Vous êtes déconnecté ». La déconnexion
MUST NOT être possible par une requête `GET`.

#### Scenario: Déconnexion d'un utilisateur connecté
- **WHEN** un utilisateur connecté envoie `POST /logout`
- **THEN** il est redirigé vers `/logged-out`, qui affiche « Vous êtes déconnecté »
- **AND** les requêtes suivantes le traitent comme un visiteur

#### Scenario: Déconnexion sans session
- **WHEN** un visiteur non connecté envoie `POST /logout`
- **THEN** il est redirigé vers `/logged-out` sans erreur

#### Scenario: Requête GET refusée
- **WHEN** un client envoie `GET /logout`
- **THEN** le système répond 405
- **AND** une session ouverte reste ouverte

### Requirement: Page de déconnexion
Le système SHALL servir sur `GET /logged-out` une page qui confirme la fin de la session, avec un
lien vers la connexion. Message : « Vous êtes déconnecté » par défaut ; pour le motif `inactivity`,
« Votre session a expiré après N minutes d'inactivité », N étant la durée d'expiration en vigueur.
Un utilisateur encore connecté MUST y être redirigé vers `/` sans être déconnecté.

#### Scenario: Page après une déconnexion
- **WHEN** un visiteur ouvre `/logged-out`
- **THEN** la page affiche « Vous êtes déconnecté » et un lien vers `/login`

#### Scenario: Page après une expiration
- **WHEN** un visiteur ouvre `/logged-out?reason=inactivity`
- **THEN** la page affiche « Votre session a expiré après 30 minutes d'inactivité » et un lien vers `/login`

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

### Requirement: Expiration par inactivité
Le système SHALL fermer automatiquement une session restée 30 minutes sans requête. Chaque requête
d'un utilisateur connecté MUST repousser l'expiration de 30 minutes. L'expiration MUST être vérifiée
par le serveur, y compris pour un cookie de session réutilisé après ce délai.

#### Scenario: Session inactive expirée
- **WHEN** un utilisateur connecté envoie une requête plus de 30 minutes après sa dernière requête
- **THEN** il est traité comme un visiteur

#### Scenario: Activité qui prolonge la session
- **WHEN** un utilisateur connecté envoie une requête toutes les 20 minutes pendant une heure
- **THEN** il reste connecté à chaque requête

### Requirement: Avis d'expiration dans le navigateur
Une page servie à un utilisateur connecté SHALL, 30 minutes après son chargement sans autre
navigation, amener le navigateur sur `/logged-out?reason=inactivity` sans action de l'utilisateur.
Ce comportement MUST fonctionner sans JavaScript.

#### Scenario: Page laissée ouverte
- **WHEN** un utilisateur connecté laisse une page ouverte 30 minutes sans naviguer
- **THEN** le navigateur affiche la page de déconnexion avec « Votre session a expiré après 30 minutes d'inactivité »

#### Scenario: Activité dans un autre onglet
- **WHEN** une page reste ouverte 30 minutes dans un onglet pendant que l'utilisateur navigue dans un autre onglet
- **THEN** l'onglet inactif revient sur `/`
- **AND** l'utilisateur reste connecté

#### Scenario: Page servie à un visiteur
- **WHEN** un visiteur ouvre une page du site
- **THEN** la page ne déclenche aucune redirection d'expiration

### Requirement: Pages connectées non mises en cache
Toute réponse servie à un utilisateur connecté MUST interdire sa mise en cache par le navigateur,
pour qu'après une déconnexion ou une expiration, le retour arrière ne réaffiche aucun contenu
réservé à l'utilisateur connecté.

#### Scenario: En-tête pour un utilisateur connecté
- **WHEN** un utilisateur connecté ouvre une page du site
- **THEN** la réponse porte l'en-tête `Cache-Control: no-store`

#### Scenario: Pages de visiteur cachables
- **WHEN** un visiteur ouvre la page de connexion ou de création de compte
- **THEN** la réponse ne porte pas `Cache-Control: no-store`

#### Scenario: Retour arrière après déconnexion
- **WHEN** un utilisateur se déconnecte puis utilise le bouton « Précédent » du navigateur pour revenir à l'accueil
- **THEN** le navigateur redemande la page au serveur
- **AND** il est redirigé vers la page de connexion

### Requirement: Protection du cookie de session
Le cookie de session MUST être inaccessible au JavaScript de la page et MUST NOT être envoyé lors
d'une requête `POST` émise depuis un autre site.

#### Scenario: Attributs du cookie
- **WHEN** le système ouvre une session à la connexion
- **THEN** le cookie de session porte les attributs `HttpOnly` et `SameSite=Lax`

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
