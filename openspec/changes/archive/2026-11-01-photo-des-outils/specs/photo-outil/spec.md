# Spec Delta

## Purpose

Permettre au propriétaire d'un outil d'y joindre une photo, de la remplacer ou de la retirer,
et de la voir dans son inventaire, sans exposer ses métadonnées ni l'image à d'autres comptes.

## ADDED Requirements

### Requirement: Photo jointe au formulaire d'un outil
Le formulaire d'enregistrement, et celui de modification d'un outil sans photo, SHALL offrir un
champ « Ajouter une image ». Une photo acceptée est enregistrée avec l'outil, dans le même envoi.
Un envoi sans fichier ni choix MUST laisser la photo existante inchangée.

#### Scenario: Outil enregistré avec une photo
- **WHEN** Alice enregistre l'outil « perceuse » avec une photo JPEG
- **THEN** la perceuse est enregistrée et a une photo

#### Scenario: Photo ajoutée à la modification
- **WHEN** Alice modifie sa perceuse sans photo et y joint une photo PNG
- **THEN** la perceuse a une photo

#### Scenario: Modification sans fichier
- **WHEN** la perceuse d'Alice a une photo et Alice change sa description sans choisir de fichier
- **THEN** la description est modifiée et la photo est inchangée

### Requirement: Modifier ou retirer l'image
Le formulaire de modification d'un outil qui a une photo SHALL offrir deux cases, « Modifier
l'image » et « Retirer l'image (définitif) », décochées à l'ouverture et décochables. Un fichier
envoyé MUST être ignoré sans « Modifier l'image ». « Modifier l'image » sans fichier, ou les deux
cases cochées, MUST être refusés sans rien modifier.

#### Scenario: Photo remplacée
- **WHEN** la perceuse d'Alice a une photo et Alice coche « Modifier l'image » avec une autre photo
- **THEN** la perceuse n'a que la nouvelle photo

#### Scenario: Photo retirée
- **WHEN** la perceuse d'Alice a une photo et Alice coche « Retirer l'image »
- **THEN** la perceuse n'a plus de photo

#### Scenario: Changement d'avis
- **WHEN** Alice coche « Modifier l'image », sélectionne une photo, décoche « Modifier l'image » et change la description
- **THEN** la description est modifiée et la perceuse garde sa photo

#### Scenario: Fichier sans choix
- **WHEN** la perceuse d'Alice a une photo et Alice envoie un fichier sans cocher « Modifier l'image »
- **THEN** la perceuse garde sa photo

#### Scenario: Retrait avec un fichier sélectionné
- **WHEN** Alice sélectionne une photo, puis coche seulement « Retirer l'image »
- **THEN** la perceuse n'a plus de photo et la photo sélectionnée n'est pas enregistrée

#### Scenario: Modifier sans fichier
- **WHEN** la perceuse d'Alice a une photo et Alice coche « Modifier l'image » sans sélectionner de fichier
- **THEN** le formulaire affiche « Choisissez la nouvelle image » et la perceuse garde sa photo

#### Scenario: Les deux cases cochées
- **WHEN** la perceuse d'Alice a une photo et Alice coche « Modifier l'image » et « Retirer l'image » avec une autre photo
- **THEN** le formulaire affiche « Choisissez Modifier l'image ou Retirer l'image, pas les deux »
- **AND** la perceuse garde sa photo et ses autres champs

#### Scenario: Cases à l'ouverture
- **WHEN** Alice ouvre la modification de sa perceuse qui a une photo
- **THEN** le formulaire offre « Modifier l'image » et « Retirer l'image (définitif) », décochées

#### Scenario: Choix absents sans photo
- **WHEN** Alice ouvre la modification d'un outil sans photo
- **THEN** le formulaire offre « Ajouter une image » et n'offre ni « Modifier l'image » ni « Retirer l'image »

#### Scenario: Retrait d'une photo déjà retirée
- **WHEN** Alice soumet « Retirer l'image » avec une photo sélectionnée, pour une perceuse qui n'a plus de photo (second onglet, retour arrière)
- **THEN** l'enregistrement réussit, la perceuse n'a pas de photo et la photo sélectionnée n'est pas enregistrée

#### Scenario: Photo ajoutée dans un autre onglet
- **WHEN** Alice a ouvert la modification de sa perceuse sans photo, en a ajouté une dans un autre onglet, puis envoie une photo depuis le premier
- **THEN** le formulaire affiche « Choisissez la nouvelle image », offre « Modifier l'image » et la perceuse garde la photo de l'autre onglet

### Requirement: Formats et tailles acceptés
Une photo SHALL être acceptée seulement si son contenu est une image JPEG, PNG ou WebP lisible,
quel que soit le nom ou le type annoncé du fichier, d'au plus 10 Mo et d'au plus 40 millions de
pixels.

#### Scenario: Format refusé
- **WHEN** Alice joint un fichier GIF à sa perceuse
- **THEN** le formulaire affiche « La photo doit être une image JPEG, PNG ou WebP »

#### Scenario: Extension trompeuse
- **WHEN** Alice joint un fichier texte nommé « perceuse.jpg »
- **THEN** le formulaire affiche « La photo doit être une image JPEG, PNG ou WebP »

#### Scenario: Image tronquée
- **WHEN** Alice joint un fichier JPEG coupé en son milieu
- **THEN** le formulaire affiche « La photo est illisible »

#### Scenario: Fichier vide
- **WHEN** Alice joint un fichier de 0 octet
- **THEN** le formulaire affiche « La photo est illisible »

#### Scenario: Fichier trop lourd
- **WHEN** Alice joint une photo de 11 Mo
- **THEN** le formulaire affiche « La photo ne doit pas dépasser 10 Mo »

#### Scenario: Image trop grande
- **WHEN** Alice joint un PNG de 10 000 × 5 000 pixels
- **THEN** le formulaire affiche « La photo ne doit pas dépasser 40 millions de pixels »

### Requirement: Photo refusée sans effet
Une photo refusée MUST laisser l'outil et sa photo existante inchangés, et un outil en cours
d'enregistrement n'est pas créé. Le formulaire SHALL être réaffiché avec les autres champs saisis
et demander de choisir de nouveau la photo.

#### Scenario: Enregistrement refusé
- **WHEN** Alice enregistre l'outil « scie » avec un fichier GIF
- **THEN** aucun outil « scie » n'est enregistré
- **AND** le formulaire affiche « scie » dans le champ du nom
- **AND** le formulaire affiche « Choisissez de nouveau la photo »

#### Scenario: Modification refusée
- **WHEN** la perceuse d'Alice a une photo et Alice la modifie avec un nouveau nom et un fichier GIF
- **THEN** la perceuse garde son nom et sa photo
- **AND** le formulaire affiche le nouveau nom saisi

### Requirement: Image normalisée
Une photo acceptée SHALL être enregistrée en JPEG, orientée selon ses métadonnées d'origine,
réduite à au plus 1600 pixels sur son grand côté sans jamais être agrandie, et MUST NOT
conserver aucune métadonnée, dont la géolocalisation.

#### Scenario: Grande photo réduite
- **WHEN** Alice joint une photo de 4000 × 3000 pixels
- **THEN** la photo servie mesure 1600 × 1200 pixels, au format JPEG

#### Scenario: Petite photo conservée
- **WHEN** Alice joint un PNG de 800 × 600 pixels
- **THEN** la photo servie mesure 800 × 600 pixels, au format JPEG

#### Scenario: Géolocalisation retirée
- **WHEN** Alice joint une photo dont les métadonnées contiennent une position GPS
- **THEN** la photo servie ne contient aucune métadonnée EXIF

#### Scenario: Orientation appliquée
- **WHEN** Alice joint une photo de 3000 × 4000 pixels enregistrée couchée avec une orientation « pivoter de 90° »
- **THEN** la photo servie est en portrait

### Requirement: Envoi trop volumineux
Un envoi de formulaire de plus de 16 Mo MUST être refusé sans rien enregistrer, par une page en
français « Envoi trop volumineux » qui ramène à « Mes outils ».

#### Scenario: Envoi de 20 Mo
- **WHEN** Alice soumet le formulaire de sa perceuse avec un fichier de 20 Mo
- **THEN** le système répond 413 avec la page « Envoi trop volumineux »
- **AND** la perceuse est inchangée

### Requirement: Accès à l'image
L'image d'un outil SHALL être servie à une adresse stable propre à l'outil, à son propriétaire
seul, que l'outil soit en circulation ou retiré. Un autre compte, un visiteur, un outil sans
photo ou inexistant MUST recevoir la même réponse 404.

#### Scenario: Propriétaire
- **WHEN** Alice demande l'image de sa perceuse
- **THEN** elle reçoit la photo, de type `image/jpeg`

#### Scenario: Outil retiré
- **WHEN** Alice a retiré sa perceuse et demande son image
- **THEN** elle reçoit la photo

#### Scenario: Autre voisin
- **WHEN** Bob demande l'image de la perceuse d'Alice
- **THEN** le système répond 404

#### Scenario: Visiteur
- **WHEN** un visiteur demande l'image de la perceuse d'Alice
- **THEN** le système répond 404

#### Scenario: Outil sans photo
- **WHEN** Alice demande l'image d'un de ses outils sans photo
- **THEN** le système répond 404

### Requirement: Image privée et à jour dans le navigateur
L'image MUST être servie avec un type de contenu que le navigateur ne réinterprète pas, et sa
mise en cache MUST rester privée au navigateur et revalidée à chaque affichage : une image
remplacée s'affiche dès la page suivante, une image inchangée n'est pas retransmise.

#### Scenario: Cache privé
- **WHEN** Alice demande l'image de sa perceuse
- **THEN** la réponse porte `Cache-Control: private, no-cache` et `X-Content-Type-Options: nosniff`

#### Scenario: Image inchangée
- **WHEN** Alice redemande l'image de sa perceuse avec l'étiquette reçue la première fois
- **THEN** le système répond 304 sans contenu

#### Scenario: Image remplacée
- **WHEN** Alice a remplacé la photo de sa perceuse et redemande l'image avec l'ancienne étiquette
- **THEN** elle reçoit la nouvelle photo

### Requirement: Photo affichée dans l'inventaire
Les pages « Mes outils » et « Mes outils retirés » SHALL afficher une vignette de la photo de
chaque outil qui en a une, et le formulaire de modification la photo actuelle. Un outil sans photo
MUST n'afficher aucune image. Le texte de remplacement de l'image est le nom de l'outil.

#### Scenario: Vignette dans la liste
- **WHEN** la perceuse d'Alice a une photo et Alice ouvre « Mes outils »
- **THEN** la ligne de la perceuse affiche son image, avec le texte de remplacement « perceuse »

#### Scenario: Outil sans photo
- **WHEN** la scie d'Alice n'a pas de photo et Alice ouvre « Mes outils »
- **THEN** la ligne de la scie n'affiche aucune image

#### Scenario: Photo actuelle à la modification
- **WHEN** la perceuse d'Alice a une photo et Alice ouvre sa modification
- **THEN** le formulaire affiche la photo actuelle
