## ADDED Requirements

### Requirement: Rester connecté sur un appareil
La page de connexion SHALL offrir la case « Rester connecté sur cet appareil », décochée par défaut,
sous le mot de passe. Une connexion réussie case cochée MUST poser un cookie persistant qui reconnaît
l'utilisateur 30 jours après sa dernière requête, au-delà de l'expiration par inactivité ; chaque
requête de l'utilisateur ainsi reconnu repousse ce terme de 30 jours. Toute autre valeur du champ
vaut décochée. Le terme est appliqué par le navigateur seulement (ADR 0028).

#### Scenario: Case affichée décochée
- **WHEN** un visiteur ouvre `/login`
- **THEN** la page affiche la case « Rester connecté sur cet appareil », décochée

#### Scenario: Connexion case cochée
- **WHEN** Alice se connecte avec la case cochée
- **THEN** la réponse pose un cookie persistant qui expire dans 30 jours

#### Scenario: Reconnue après l'expiration de la session
- **WHEN** Alice s'est connectée case cochée et envoie une requête 31 minutes après sa dernière requête
- **THEN** elle est reconnue comme connectée
- **AND** la réponse repousse le terme du cookie persistant à 30 jours

#### Scenario: Activité qui prolonge le cookie persistant
- **WHEN** Alice, connectée case cochée, ouvre une page
- **THEN** la réponse renouvelle le cookie persistant pour 30 jours

#### Scenario: Connexion case décochée
- **WHEN** Alice se connecte sans cocher la case, puis ouvre plusieurs pages
- **THEN** aucune réponse ne pose de cookie persistant
- **AND** sa session expire après 30 minutes d'inactivité

#### Scenario: Navigateur partagé
- **WHEN** Bob s'est connecté case cochée dans un navigateur, puis Alice s'y connecte sans cocher la case
- **THEN** la réponse efface le cookie persistant de Bob
- **AND** 31 minutes plus tard, le navigateur est traité comme un visiteur, jamais comme Bob

#### Scenario: Valeur de case inattendue
- **WHEN** un visiteur soumet la connexion avec une valeur inattendue pour la case
- **THEN** il est connecté comme si la case était décochée

#### Scenario: Échec de connexion case cochée
- **WHEN** un visiteur soumet un mot de passe erroné avec la case cochée
- **THEN** aucun cookie persistant n'est posé
- **AND** la page de connexion réaffiche la case cochée

#### Scenario: Cookie persistant expiré
- **WHEN** le navigateur d'Alice n'envoie plus le cookie persistant, expiré, et que sa session a expiré
- **THEN** elle est traitée comme une visiteuse, sans message particulier

#### Scenario: Session ouverte avant le déploiement
- **WHEN** une session ouverte avant le déploiement de ce changement envoie une requête
- **THEN** elle reste ouverte

#### Scenario: Identifiant de session altéré
- **WHEN** une session porte un identifiant de compte d'un format inattendu
- **THEN** elle est traitée comme celle d'un visiteur, sans erreur

## MODIFIED Requirements

### Requirement: Déconnexion
Le système SHALL fermer la session de l'utilisateur sur une requête `POST /logout`, effacer le cookie
persistant de cet appareil, puis le rediriger vers la page de déconnexion avec le message « Vous êtes
déconnecté ». La déconnexion MUST NOT être possible par une requête `GET`.

#### Scenario: Déconnexion d'un utilisateur connecté
- **WHEN** un utilisateur connecté envoie `POST /logout`
- **THEN** il est redirigé vers `/logged-out`, qui affiche « Vous êtes déconnecté »
- **AND** les requêtes suivantes le traitent comme un visiteur

#### Scenario: Déconnexion d'un utilisateur resté connecté
- **WHEN** Alice, connectée case cochée, envoie `POST /logout`
- **THEN** la réponse efface le cookie persistant
- **AND** 31 minutes plus tard, le navigateur est traité comme un visiteur

#### Scenario: Déconnexion sans session
- **WHEN** un visiteur non connecté envoie `POST /logout`
- **THEN** il est redirigé vers `/logged-out` sans erreur

#### Scenario: Requête GET refusée
- **WHEN** un client envoie `GET /logout`
- **THEN** le système répond 405
- **AND** une session ouverte reste ouverte

### Requirement: Expiration par inactivité
Le système SHALL fermer automatiquement une session restée 30 minutes sans requête. Chaque requête
d'un utilisateur connecté MUST repousser l'expiration de 30 minutes. L'expiration MUST être vérifiée
par le serveur, y compris pour un cookie de session réutilisé après ce délai. Un appareil qui porte
le cookie persistant de « Rester connecté » rouvre une session sans nouvelle connexion.

#### Scenario: Session inactive expirée
- **WHEN** un utilisateur connecté sans cocher « Rester connecté » envoie une requête plus de 30 minutes après sa dernière requête
- **THEN** il est traité comme un visiteur

#### Scenario: Activité qui prolonge la session
- **WHEN** un utilisateur connecté envoie une requête toutes les 20 minutes pendant une heure
- **THEN** il reste connecté à chaque requête

### Requirement: Avis d'expiration dans le navigateur
Une page servie à un utilisateur connecté sans cookie persistant SHALL, 30 minutes après son
chargement sans autre navigation, amener le navigateur sur `/logged-out?reason=inactivity` sans
action de l'utilisateur. Une page servie à un utilisateur resté connecté MUST NOT le faire. Ce
comportement MUST fonctionner sans JavaScript.

#### Scenario: Page laissée ouverte
- **WHEN** un utilisateur connecté sans cocher « Rester connecté » laisse une page ouverte 30 minutes sans naviguer
- **THEN** le navigateur affiche la page de déconnexion avec « Votre session a expiré après 30 minutes d'inactivité »

#### Scenario: Activité dans un autre onglet
- **WHEN** une page reste ouverte 30 minutes dans un onglet pendant que l'utilisateur navigue dans un autre onglet
- **THEN** l'onglet inactif revient sur `/`
- **AND** l'utilisateur reste connecté

#### Scenario: Page servie à un utilisateur resté connecté
- **WHEN** Alice, connectée case cochée, ouvre une page du site
- **THEN** la page ne déclenche aucune redirection d'expiration

#### Scenario: Page servie à un visiteur
- **WHEN** un visiteur ouvre une page du site
- **THEN** la page ne déclenche aucune redirection d'expiration

### Requirement: Protection du cookie de session
Le cookie de session et le cookie persistant de « Rester connecté » MUST être inaccessibles au
JavaScript de la page et MUST NOT être envoyés lors d'une requête `POST` émise depuis un autre site.

#### Scenario: Attributs du cookie
- **WHEN** le système ouvre une session à la connexion
- **THEN** le cookie de session porte les attributs `HttpOnly` et `SameSite=Lax`

#### Scenario: Attributs du cookie persistant
- **WHEN** un utilisateur se connecte case cochée
- **THEN** le cookie persistant porte les attributs `HttpOnly` et `SameSite=Lax`

### Requirement: Sessions d'un compte supprimé
Toute session ouverte d'un compte supprimé, dans n'importe quel navigateur, MUST être traitée comme
celle d'un visiteur dès sa requête suivante, sans attendre son expiration (ADR 0023). Il en va de
même d'un cookie persistant de ce compte. Hors suppression du compte, une copie du cookie persistant
reste valide jusqu'à son terme : aucune fonction ne la révoque encore (ADR 0028, issue #61).

#### Scenario: Session ouverte dans un autre navigateur
- **WHEN** Alice est connectée sur son ordinateur et sur son téléphone
- **AND** elle supprime son compte depuis son ordinateur
- **THEN** la requête suivante de son téléphone vers une page réservée la redirige vers `/login`

#### Scenario: Cookie copié
- **WHEN** une copie du cookie de session d'Alice est renvoyée après la suppression de son compte, avant 30 minutes
- **THEN** le système la traite comme un visiteur

#### Scenario: Cookie persistant copié
- **WHEN** une copie du cookie persistant d'Alice est renvoyée après la suppression de son compte
- **THEN** le système la traite comme un visiteur
