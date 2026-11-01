# outils-des-contacts Specification

## Purpose
Permettre à un utilisateur de voir les outils que ses contacts proposent, de savoir lesquels il
pourrait emprunter dès maintenant et de les retrouver par leur nom ou leur description.

## Requirements

### Requirement: Outils visibles par un contact
Les outils montrés à un utilisateur SHALL être ceux de ses contacts, en circulation et dont l'état
n'est pas « Hors d'usage ». Ses propres outils, les outils retirés, hors d'usage, ou ceux d'un
compte avec qui il n'est pas en contact, y compris s'il lui a seulement envoyé une demande,
MUST NOT y figurer.

#### Scenario: Outil d'un contact
- **WHEN** Alice et Bob sont en contact et Bob a une perceuse en circulation
- **THEN** la page « Trouver un outil » d'Alice montre la perceuse de Bob

#### Scenario: Ses propres outils exclus
- **WHEN** Alice a une scie en circulation
- **THEN** la page « Trouver un outil » d'Alice ne montre pas sa scie

#### Scenario: Non-contact
- **WHEN** Carole n'est pas en contact avec Alice et a une ponceuse en circulation
- **THEN** la page « Trouver un outil » d'Alice ne montre pas la ponceuse

#### Scenario: Demande de contact en attente
- **WHEN** Alice a envoyé à Carole une demande de contact qui attend une réponse
- **THEN** la page « Trouver un outil » d'Alice ne montre aucun outil de Carole

#### Scenario: Outil retiré
- **WHEN** Bob, contact d'Alice, a retiré sa perceuse
- **THEN** la page « Trouver un outil » d'Alice ne montre pas la perceuse

#### Scenario: Outil hors d'usage
- **WHEN** Bob, contact d'Alice, a une perceuse à l'état « Hors d'usage »
- **THEN** la page « Trouver un outil » d'Alice ne montre pas la perceuse

#### Scenario: Outil à réparer
- **WHEN** Bob, contact d'Alice, a une perceuse à l'état « À réparer »
- **THEN** la page « Trouver un outil » d'Alice montre la perceuse avec l'état « À réparer »

### Requirement: Page « Trouver un outil »
Pour un utilisateur connecté, le menu du compte SHALL offrir l'entrée « Trouver un outil » vers
la page du même nom, qui liste tous les outils visibles de ses contacts. La page MUST exiger
une session ouverte : un visiteur est redirigé vers `/login`.

#### Scenario: Entrée du menu du compte
- **WHEN** un utilisateur connecté ouvre une page du site
- **THEN** son nom d'utilisateur ouvre un menu qui contient « Trouver un outil », qui mène à la page « Trouver un outil »

#### Scenario: Visiteur
- **WHEN** un visiteur demande la page « Trouver un outil »
- **THEN** il est redirigé vers `/login`
- **AND** la navigation d'un visiteur ne contient pas « Trouver un outil »

### Requirement: Outils d'un contact sur sa page
La page d'un contact SHALL contenir une section « Outils de <prénom> <nom> » qui liste seulement
les outils visibles de ce contact, avec les mêmes cartes et les mêmes filtres que la page
« Trouver un outil ».

#### Scenario: Seuls les outils du contact
- **WHEN** Bob et Carole sont contacts d'Alice et ont chacun un outil en circulation
- **AND** Alice ouvre la page de Bob
- **THEN** la section « Outils de Bob Gagnon » montre l'outil de Bob et pas celui de Carole

### Requirement: Carte d'un outil
Chaque outil SHALL être présenté par une carte qui affiche son nom, sa photo, le prénom et le nom
de son propriétaire, menant à sa page, sa description, son état et son statut de prêt, ainsi qu'un bouton « Emprunter » grisé portant « Bientôt
disponible ». Les cartes sont disposées sur trois colonnes à partir d'un écran moyen, sur une
seule sur un petit écran. Les notes privées du propriétaire MUST NOT être affichées.

#### Scenario: Contenu de la carte
- **WHEN** Bob, contact d'Alice, a une perceuse fonctionnelle avec photo et description
- **THEN** la carte de la perceuse affiche son nom, sa photo, « Bob Gagnon », sa description, « Fonctionnel » et son statut
- **AND** « Bob Gagnon » mène à la page de Bob
- **AND** elle affiche un bouton « Emprunter » désactivé et « Bientôt disponible »

#### Scenario: Notes privées cachées
- **WHEN** la perceuse de Bob a les notes privées « code du cadenas 1234 »
- **THEN** aucune page d'Alice n'affiche « code du cadenas 1234 »

#### Scenario: Outil sans photo
- **WHEN** la perceuse de Bob n'a pas de photo
- **THEN** sa carte affiche un espace réservé à la place de la photo, à la même taille

### Requirement: Description abrégée
La carte SHALL afficher la description entière si elle compte au plus 125 caractères ; sinon, ses
125 premiers caractères suivis de « … ».

#### Scenario: Description courte
- **WHEN** la description d'un outil compte 125 caractères
- **THEN** la carte l'affiche en entier, sans « … »

#### Scenario: Description longue
- **WHEN** la description d'un outil compte 200 caractères
- **THEN** la carte affiche ses 125 premiers caractères suivis de « … »

### Requirement: Statut de prêt
Le statut d'un outil SHALL être écrit en clair sur sa carte : « Prêté jusqu'au <date> » s'il est
prêté, même après la date prévue ; sinon « En attente de prêt » si une demande attend une réponse
ou si un prêt accepté n'est pas terminé, même pour des dates à venir ; sinon « Disponible ». La
date est écrite en français, par exemple « 3 novembre 2026 ».

#### Scenario: Outil prêté
- **WHEN** la perceuse de Bob est prêtée jusqu'au 3 novembre 2026
- **THEN** sa carte affiche « Prêté jusqu'au 3 novembre 2026 »

#### Scenario: Prêt en retard
- **WHEN** la perceuse de Bob est encore prêtée et la date de fin prévue est passée
- **THEN** sa carte affiche « Prêté jusqu'au » suivi de cette date

#### Scenario: Demande en attente
- **WHEN** une demande d'emprunt de la perceuse de Bob attend sa réponse
- **THEN** sa carte affiche « En attente de prêt »

#### Scenario: Prêt accepté à venir
- **WHEN** Bob a accepté de prêter sa perceuse du 10 au 12 du mois prochain
- **THEN** sa carte affiche « En attente de prêt »

#### Scenario: Prêts terminés
- **WHEN** tous les prêts de la perceuse de Bob sont rendus, refusés ou annulés
- **THEN** sa carte affiche « Disponible »

### Requirement: Filtre « Disponible uniquement »
Les pages qui listent des outils SHALL offrir une case « Disponible uniquement » et un bouton
« Filtrer ». Cochée, seuls les outils au statut « Disponible » sont listés ; décochée, tous les
outils visibles le sont. Le filtre MUST fonctionner sans JavaScript et rester dans l'adresse de la
page.

#### Scenario: Case cochée
- **WHEN** Bob a une perceuse disponible et une scie prêtée
- **AND** Alice coche « Disponible uniquement » et clique « Filtrer »
- **THEN** la page montre la perceuse et pas la scie
- **AND** la case reste cochée

#### Scenario: Case décochée
- **WHEN** Bob a une perceuse disponible, une scie prêtée et une ponceuse en attente de prêt
- **AND** Alice filtre sans cocher « Disponible uniquement »
- **THEN** la page montre les trois outils avec leur statut

### Requirement: Filtre par texte
Les pages qui listent des outils SHALL offrir un champ de texte : seuls les outils dont le nom ou
la description ressemble au texte sont listés, sans égard à la casse, aux accents ni à une faute
de frappe légère ; `%` et `_` sont cherchés tels quels. Un texte vide ne filtre pas. Le champ
garde le texte cherché.

#### Scenario: Faute de frappe
- **WHEN** Bob a une « Perceuse » et Alice cherche « perseuse »
- **THEN** la perceuse figure dans les résultats

#### Scenario: Accents ignorés
- **WHEN** Bob a une « Scie à métaux » et Alice cherche « scie a metaux »
- **THEN** la scie figure dans les résultats

#### Scenario: Dans la description
- **WHEN** Bob a un « Coffret » décrit « embouts de vissage » et Alice cherche « vissage »
- **THEN** le coffret figure dans les résultats

#### Scenario: Sans rapport
- **WHEN** Bob a une « Perceuse » sans description et Alice cherche « tondeuse »
- **THEN** la perceuse ne figure pas dans les résultats

#### Scenario: Caractère joker cherché tel quel
- **WHEN** aucun outil ne contient « 50% » et Alice cherche « 50% »
- **THEN** aucun outil n'est listé

#### Scenario: Notes privées non cherchées
- **WHEN** seules les notes privées de la perceuse de Bob contiennent « cadenas » et Alice cherche « cadenas »
- **THEN** la perceuse ne figure pas dans les résultats

### Requirement: Ordre des outils
Avec un texte cherché, les outils SHALL être listés dans cet ordre : ceux dont le nom contient le
texte tel quel, puis par ressemblance décroissante du nom, puis de la description, puis par nom
sans égard à la casse. Sans texte, ils sont triés par nom sans égard à la casse.

#### Scenario: Correspondance exacte en tête
- **WHEN** Bob a un « Robot culinaire » et un « Rabot électrique » et Alice cherche « rabot »
- **THEN** le rabot électrique est listé en premier

#### Scenario: Nom avant description
- **WHEN** Bob a une « Scie sauteuse » et un « Établi » décrit « idéal pour la scie »
- **AND** Alice cherche « scie »
- **THEN** la scie sauteuse est listée avant l'établi

#### Scenario: Sans texte
- **WHEN** Bob a « carotteuse », « Bêche » et « agrafeuse » et Alice ouvre « Trouver un outil » sans texte
- **THEN** ils sont listés dans l'ordre « agrafeuse », « Bêche », « carotteuse »

### Requirement: Listes vides
Une liste d'outils vide SHALL afficher un message selon le cas. Sur « Trouver un outil » :
« Vous n'avez encore aucun contact » avec un lien vers la recherche d'utilisateurs, sans contact ;
« Vos contacts n'ont encore aucun outil à prêter » sans outil visible. Sur la page d'un contact :
« <prénom> <nom> n'a encore aucun outil à prêter ». Partout : « Aucun outil ne correspond à ces
filtres » quand les filtres écartent tous les outils.

#### Scenario: Aucun contact
- **WHEN** Alice n'a aucun contact et ouvre « Trouver un outil »
- **THEN** la page affiche « Vous n'avez encore aucun contact »

#### Scenario: Contacts sans outil
- **WHEN** Bob, seul contact d'Alice, n'a aucun outil visible
- **THEN** la page « Trouver un outil » d'Alice affiche « Vos contacts n'ont encore aucun outil à prêter »

#### Scenario: Contact sans outil
- **WHEN** Bob Gagnon, contact d'Alice, n'a aucun outil visible et Alice ouvre sa page
- **THEN** la section de ses outils affiche « Bob Gagnon n'a encore aucun outil à prêter »

#### Scenario: Filtres sans résultat
- **WHEN** Bob a une perceuse et Alice cherche « tondeuse »
- **THEN** la page affiche « Aucun outil ne correspond à ces filtres »
