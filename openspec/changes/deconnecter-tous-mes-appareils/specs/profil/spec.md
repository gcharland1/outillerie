## ADDED Requirements

### Requirement: Section « Déconnecter tous mes appareils »
« Mon profil » SHALL afficher, juste avant « Supprimer mon compte », une section « Déconnecter tous
mes appareils » avec le texte « Ferme votre session sur tous vos appareils, celui-ci compris. » et le
bouton rouge « Déconnecter tous mes appareils », qui mène à la page de confirmation. La section
s'affiche aussi pour un compte au courriel non confirmé.

#### Scenario: Section affichée
- **WHEN** Alice ouvre « Mon profil »
- **THEN** la section « Déconnecter tous mes appareils » précède « Supprimer mon compte »
- **AND** son bouton rouge « Déconnecter tous mes appareils » mène à la page de confirmation

### Requirement: Page de confirmation de la déconnexion de tous les appareils
`GET /profile/logout-all` SHALL afficher « Tous vos appareils, celui-ci compris, seront déconnectés.
Vous devrez vous reconnecter. », avec « Annuler », gris, vers « Mon profil », et « Déconnecter tous
mes appareils », rouge, qui envoie la confirmation en POST. L'ouvrir ne déconnecte rien. Un visiteur
non connecté est mené à la connexion.

#### Scenario: Page de confirmation
- **WHEN** Alice clique « Déconnecter tous mes appareils » sur « Mon profil »
- **THEN** la page de confirmation s'affiche avec « Annuler » gris et « Déconnecter tous mes appareils » rouge
- **AND** les autres appareils d'Alice restent connectés

#### Scenario: Annuler
- **WHEN** Alice clique « Annuler » sur la page de confirmation
- **THEN** elle revient sur « Mon profil », toujours connectée

#### Scenario: Visiteur
- **WHEN** un visiteur ouvre `/profile/logout-all`
- **THEN** il est redirigé vers `/login`

### Requirement: Effet de la déconnexion de tous les appareils
`POST /profile/logout-all`, avec un jeton CSRF valide, SHALL changer la version de session du compte
connecté : toutes ses sessions et tous ses cookies persistants, sur tous les appareils, MUST être
traités comme ceux d'un visiteur dès leur requête suivante (ADR 0028). L'appareil courant MUST être
déconnecté, son cookie persistant effacé, et mené à `/logged-out?reason=all-devices`. Le mot de passe
n'est pas redemandé. Un compte supprimé entre-temps n'est pas modifié : la requête mène à `/login`.

#### Scenario: Autre appareil déconnecté
- **WHEN** Alice est connectée sur son ordinateur et sur son téléphone
- **AND** elle confirme « Déconnecter tous mes appareils » depuis son ordinateur
- **THEN** la requête suivante de son téléphone vers une page réservée la redirige vers `/login`

#### Scenario: Cookie persistant révoqué
- **WHEN** Alice s'est connectée case « Rester connecté » cochée sur son téléphone
- **AND** elle confirme « Déconnecter tous mes appareils » depuis son ordinateur
- **THEN** le cookie persistant de son téléphone ne la reconnecte plus

#### Scenario: Appareil courant
- **WHEN** Alice confirme « Déconnecter tous mes appareils »
- **THEN** elle est redirigée vers `/logged-out?reason=all-devices`, qui affiche « Tous vos appareils ont été déconnectés »
- **AND** la réponse efface le cookie persistant de l'appareil
- **AND** elle peut se reconnecter avec son mot de passe

#### Scenario: Envoi sans jeton CSRF
- **WHEN** Alice envoie `POST /profile/logout-all` sans jeton CSRF
- **THEN** le système répond 400 et aucune session n'est révoquée

#### Scenario: Envoi sans session
- **WHEN** un visiteur envoie `POST /profile/logout-all`
- **THEN** il est redirigé vers `/login` et aucun compte n'est modifié

### Requirement: Avis de la déconnexion de tous les appareils
Après la révocation, le système SHALL envoyer à l'adresse du compte, si elle est confirmée, un
courriel en texte brut, objet « Vos appareils ont été déconnectés », qui salue l'utilisateur par son
prénom et dit que tous les appareils connectés à son compte ont été déconnectés. Il MUST NOT contenir
de lien, d'adresse ni de téléphone. Un échec d'envoi MUST NOT empêcher la révocation ni la
déconnexion. Un compte au courriel non confirmé ne reçoit rien.

#### Scenario: Avis envoyé
- **WHEN** Alice, au courriel confirmé, confirme « Déconnecter tous mes appareils »
- **THEN** un courriel « Vos appareils ont été déconnectés » part à son adresse, avec son prénom et sans lien

#### Scenario: Échec d'envoi
- **WHEN** l'envoi du courriel échoue
- **THEN** les sessions d'Alice sont quand même révoquées et elle arrive sur `/logged-out?reason=all-devices`

#### Scenario: Courriel non confirmé
- **WHEN** Denis, au courriel non confirmé, confirme « Déconnecter tous mes appareils »
- **THEN** ses sessions sont révoquées et aucun courriel ne part
