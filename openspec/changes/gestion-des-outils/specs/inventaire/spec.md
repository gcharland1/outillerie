# Spec Delta

## Purpose

Permettre à un voisin connecté de tenir l'inventaire des outils qu'il propose au prêt : les
enregistrer, les décrire, les retirer de la circulation et les y remettre.

## ADDED Requirements

### Requirement: Inventaire réservé à son propriétaire
Les pages de l'inventaire MUST exiger une session ouverte : un visiteur est redirigé vers
`/login`. Un utilisateur connecté SHALL n'y voir et n'y agir que sur ses propres outils ; l'outil
d'un autre compte, ou un outil inexistant, répond 404 et n'est pas modifié.

#### Scenario: Visiteur non connecté
- **WHEN** un visiteur demande la page « Mes outils »
- **THEN** il est redirigé vers `/login`
- **AND** la page de connexion affiche « Veuillez vous connecter pour accéder à cette page »

#### Scenario: Outil d'un autre voisin
- **WHEN** Alice demande la page de modification d'un outil de Bob
- **THEN** le système répond 404

#### Scenario: Action sur l'outil d'un autre voisin
- **WHEN** Alice soumet le retrait d'un outil de Bob
- **THEN** le système répond 404
- **AND** l'outil de Bob reste en circulation

### Requirement: Accès depuis la navigation
Pour un utilisateur connecté, la barre de navigation SHALL offrir un menu du compte, ouvert en
cliquant sur son nom d'utilisateur, qui contient « Gérer mes outils » vers la page « Mes outils ».
« Me déconnecter » reste visible hors du menu. La navigation MUST NOT offrir « Gérer mes outils »
à un visiteur.

#### Scenario: Utilisateur connecté
- **WHEN** un utilisateur connecté ouvre une page du site
- **THEN** son nom d'utilisateur ouvre un menu qui contient « Gérer mes outils »
- **AND** « Me déconnecter » est affiché hors de ce menu

#### Scenario: Visiteur
- **WHEN** un visiteur ouvre une page du site
- **THEN** la navigation ne contient pas « Gérer mes outils »

### Requirement: Liste de mes outils
La page « Mes outils » SHALL lister les outils en circulation de l'utilisateur connecté, triés par
nom sans égard à la casse, avec pour chacun son nom, son état et les actions « Modifier » et
« Retirer ». Elle SHALL offrir « Enregistrer un outil » et « Voir mes outils retirés ».

#### Scenario: Outils en circulation seulement
- **WHEN** Alice a une perceuse et une scie en circulation et une ponceuse retirée
- **THEN** sa page « Mes outils » liste la perceuse et la scie, pas la ponceuse

#### Scenario: Outils des autres absents
- **WHEN** Bob a un outil en circulation et Alice ouvre sa page « Mes outils »
- **THEN** l'outil de Bob n'y figure pas

#### Scenario: Ordre alphabétique
- **WHEN** Alice a les outils « scie », « Perceuse » et « marteau »
- **THEN** ils sont listés dans l'ordre « marteau », « Perceuse », « scie »

#### Scenario: Inventaire vide
- **WHEN** Alice n'a aucun outil en circulation
- **THEN** la page affiche « Vous n'avez encore enregistré aucun outil »
- **AND** elle offre « Enregistrer un outil »

### Requirement: États affichés en français
Le système SHALL afficher l'état d'un outil par un libellé français : `functional` « Fonctionnel »,
`needs_repair` « À réparer », `out_of_order` « Hors d'usage ».

#### Scenario: Outil à réparer
- **WHEN** Alice a un outil à l'état `needs_repair`
- **THEN** sa page « Mes outils » affiche « À réparer » pour cet outil

### Requirement: Enregistrement d'un outil
Le système SHALL enregistrer, depuis « Enregistrer un outil », un outil dont l'utilisateur
connecté est le propriétaire, à partir d'un nom, d'une description, d'un état (`functional` par
défaut) et de notes privées facultatives. Le nouvel outil est en circulation ; l'utilisateur est
ramené à « Mes outils ».

#### Scenario: Outil enregistré
- **WHEN** Alice soumet le nom « Perceuse », la description « Perceuse sans fil 18 V » et l'état « À réparer »
- **THEN** un outil appartenant à Alice est enregistré avec ces informations et en circulation
- **AND** Alice est redirigée vers « Mes outils », qui liste la perceuse

#### Scenario: Notes privées laissées vides
- **WHEN** Alice enregistre un outil sans remplir les notes privées
- **THEN** l'outil est enregistré sans notes privées

### Requirement: Validation du formulaire d'outil
Le système MUST refuser un outil sans nom, sans description (espaces seuls compris), au nom de
plus de 250 caractères ou à l'état inconnu. Il SHALL réafficher le formulaire avec les valeurs
saisies et le message de l'erreur, sans rien enregistrer ni modifier.

#### Scenario: Nom manquant
- **WHEN** Alice soumet un outil dont le nom ne contient que des espaces
- **THEN** aucun outil n'est enregistré
- **AND** le formulaire affiche « Le nom et la description sont obligatoires » et garde la description saisie

#### Scenario: Nom trop long
- **WHEN** Alice soumet un outil dont le nom compte 251 caractères
- **THEN** aucun outil n'est enregistré
- **AND** le formulaire affiche « Le nom ne doit pas dépasser 250 caractères »

#### Scenario: État inconnu
- **WHEN** Alice soumet un outil à l'état `new`
- **THEN** aucun outil n'est enregistré
- **AND** le formulaire affiche « L'état choisi est invalide »

#### Scenario: Modification invalide
- **WHEN** Alice efface la description d'un outil existant et enregistre
- **THEN** l'outil garde sa description d'origine
- **AND** le formulaire affiche « Le nom et la description sont obligatoires »

### Requirement: Modification d'un outil
Le système SHALL permettre au propriétaire de modifier le nom, la description, l'état et les
notes privées d'un outil en circulation, depuis un formulaire prérempli avec les valeurs
actuelles, puis le ramener à « Mes outils ». Vider les notes privées les supprime.

#### Scenario: Formulaire prérempli
- **WHEN** Alice ouvre « Modifier » pour sa perceuse
- **THEN** le formulaire affiche le nom, la description, l'état et les notes privées actuels

#### Scenario: Outil modifié
- **WHEN** Alice remplace l'état de sa perceuse par « Hors d'usage » et enregistre
- **THEN** la perceuse est à l'état `out_of_order`
- **AND** Alice est redirigée vers « Mes outils »

#### Scenario: Outil retiré non modifiable
- **WHEN** Alice demande la modification d'un de ses outils retirés
- **THEN** le système répond 404

### Requirement: Retrait avec confirmation
« Retirer » SHALL mener à une page de confirmation qui nomme l'outil, indique qu'il restera
enregistré et pourra être remis en circulation, et offre « Confirmer le retrait » et un lien
d'annulation vers « Mes outils ». Seule la confirmation, par un envoi de formulaire, retire
l'outil de la circulation ; il reste enregistré.

#### Scenario: Page de confirmation
- **WHEN** Alice clique « Retirer » pour sa perceuse
- **THEN** une page lui demande de confirmer le retrait de « Perceuse »
- **AND** elle affiche « L'outil restera enregistré ; vous pourrez le remettre en circulation depuis « Mes outils retirés ». »
- **AND** la perceuse est toujours en circulation

#### Scenario: Retrait confirmé
- **WHEN** Alice clique « Confirmer le retrait » pour sa perceuse
- **THEN** la perceuse n'est plus en circulation et reste enregistrée avec ses informations
- **AND** Alice est redirigée vers « Mes outils », qui ne liste plus la perceuse

#### Scenario: Pas de retrait par un lien
- **WHEN** le retrait d'un outil est demandé sans envoi de formulaire (`GET`)
- **THEN** l'outil reste en circulation

### Requirement: Effacement des notes privées au retrait
Quand l'outil a des notes privées, la page de confirmation du retrait SHALL offrir la case
« Effacer définitivement mes notes privées », décochée par défaut. Cochée, la confirmation MUST
effacer les notes de l'outil ; décochée, elle les conserve.

#### Scenario: Notes effacées
- **WHEN** Alice coche « Effacer définitivement mes notes privées » et confirme le retrait de sa perceuse
- **THEN** la perceuse n'est plus en circulation et n'a plus de notes privées
- **AND** son nom, sa description et son état sont conservés

#### Scenario: Notes conservées
- **WHEN** Alice confirme le retrait de sa perceuse sans cocher la case
- **THEN** la perceuse garde ses notes privées

#### Scenario: Outil sans notes
- **WHEN** Alice clique « Retirer » pour un outil sans notes privées
- **THEN** la page de confirmation n'affiche pas la case

#### Scenario: Remise en circulation après effacement
- **WHEN** Alice remet en circulation une perceuse retirée avec ses notes effacées
- **THEN** la perceuse est en circulation, sans notes privées

### Requirement: Outil déjà retiré
Une demande de retrait, page de confirmation ou envoi, pour un outil du propriétaire déjà retiré
SHALL le ramener à « Mes outils » avec le message « Cet outil est déjà retiré », sans rien
modifier.

#### Scenario: Retour arrière après un retrait
- **WHEN** Alice confirme le retrait de sa perceuse puis revient en arrière jusqu'à la page de confirmation
- **THEN** elle est redirigée vers « Mes outils »
- **AND** la page affiche « Cet outil est déjà retiré »

#### Scenario: Second envoi
- **WHEN** Alice envoie de nouveau « Confirmer le retrait », case cochée, pour sa perceuse déjà retirée avec ses notes
- **THEN** elle est redirigée vers « Mes outils » avec « Cet outil est déjà retiré »
- **AND** la perceuse reste retirée et garde ses notes privées

### Requirement: Liste de mes outils retirés
La page « Mes outils retirés » SHALL lister les outils de l'utilisateur connecté retirés de la
circulation, triés par nom sans égard à la casse, avec « Remettre en circulation » pour chacun,
et un lien de retour vers « Mes outils ».

#### Scenario: Outils retirés listés
- **WHEN** Alice a retiré sa ponceuse et garde sa perceuse en circulation
- **THEN** « Mes outils retirés » liste la ponceuse, pas la perceuse

#### Scenario: Aucun outil retiré
- **WHEN** Alice n'a retiré aucun outil
- **THEN** la page affiche « Aucun outil retiré »

### Requirement: Remise en circulation
« Remettre en circulation », par un envoi de formulaire, SHALL remettre un outil retiré du
propriétaire en circulation, avec les informations qu'il avait, et ramener l'utilisateur à
« Mes outils retirés ».

#### Scenario: Outil remis en circulation
- **WHEN** Alice clique « Remettre en circulation » pour sa ponceuse retirée à l'état « À réparer »
- **THEN** la ponceuse est de nouveau en circulation, toujours à l'état `needs_repair`
- **AND** elle figure de nouveau dans « Mes outils »
