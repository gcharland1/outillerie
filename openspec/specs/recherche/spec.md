# recherche Specification

## Purpose
Permettre à un voisin connecté de trouver d'autres voisins sur la plateforme et de voir, pour
chacun, où en est leur relation de contact.

## Requirements

### Requirement: Barre de recherche dans la navigation
Pour un utilisateur connecté, la barre de navigation SHALL afficher au centre un champ de
recherche précédé d'un menu déroulant du type de recherche : « Outil », choisi par défaut,
et « Utilisateur ». Sur la page de résultats, le champ garde le texte cherché et le menu le type
cherché, « Outil » pour un type inconnu. La navigation d'un visiteur MUST NOT afficher la barre
de recherche.

#### Scenario: Utilisateur connecté
- **WHEN** un utilisateur connecté ouvre une page du site
- **THEN** la navigation contient un champ de recherche et un menu déroulant offrant « Outil » et « Utilisateur »
- **AND** « Outil » est choisi et « Utilisateur » est sélectionnable

#### Scenario: Visiteur
- **WHEN** un visiteur ouvre une page du site
- **THEN** la navigation ne contient pas de champ de recherche

#### Scenario: Texte cherché conservé
- **WHEN** Alice choisit « Utilisateur » et cherche « gagnon »
- **THEN** le champ de recherche de la page de résultats contient « gagnon »
- **AND** le menu déroulant y a « Utilisateur » choisi

#### Scenario: Type inconnu
- **WHEN** Alice demande la page de résultats avec le type « lieu »
- **THEN** le menu déroulant y a « Outil » choisi

### Requirement: Recherche réservée à un utilisateur connecté
La page de résultats MUST exiger une session ouverte : un visiteur est redirigé vers `/login`.

#### Scenario: Visiteur non connecté
- **WHEN** un visiteur demande la page de résultats de recherche
- **THEN** il est redirigé vers `/login`

### Requirement: Correspondance des utilisateurs
La recherche d'utilisateurs SHALL lister les autres comptes dont le prénom suivi du nom
contient le texte ou, dès 4 caractères, lui ressemble malgré une faute
légère, sans égard à la casse, aux accents ni aux espaces autour ; un tiret vaut une espace,
plusieurs espaces une seule ; `%`, `_` et `\` sont cherchés tels quels. Tri : ceux qui
contiennent le texte, puis ressemblance décroissante, puis prénom, puis nom, sans égard à la
casse ni aux accents, puis du plus ancien compte au plus récent. Jamais son propre compte.

#### Scenario: Par le nom
- **WHEN** Bob Gagnon a un compte et Alice cherche « GAGN »
- **THEN** le compte de Bob figure dans les résultats

#### Scenario: Par le prénom et le nom
- **WHEN** Bob Gagnon a un compte et Alice cherche «  bob gagnon  »
- **THEN** le compte de Bob figure dans les résultats

#### Scenario: Accents du compte ignorés
- **WHEN** Fréd Côté a un compte et Alice cherche « fred cote »
- **THEN** le compte de Fréd figure dans les résultats

#### Scenario: Accents du texte ignorés
- **WHEN** Fred Cote a un compte et Alice cherche « FRÉD CÔTÉ »
- **THEN** le compte de Fred figure dans les résultats

#### Scenario: Tiret et espace équivalents
- **WHEN** Jean-Pierre Roy a un compte et Alice cherche « jean pierre »
- **THEN** le compte de Jean-Pierre figure dans les résultats

#### Scenario: Espaces multiples
- **WHEN** Bob Gagnon a un compte et Alice cherche « bob    gagnon »
- **THEN** le compte de Bob figure dans les résultats

#### Scenario: Faute de frappe
- **WHEN** Bob Gagnon a un compte et Alice cherche « gagnion »
- **THEN** le compte de Bob figure dans les résultats

#### Scenario: Nom avant prénom
- **WHEN** Bob Gagnon a un compte et Alice cherche « gagnon bob »
- **THEN** le compte de Bob figure dans les résultats

#### Scenario: Pas de ressemblance sous 4 caractères
- **WHEN** Bob Gagnon a un compte, aucun compte ne contient « gax » et Alice cherche « gax »
- **THEN** aucun compte ne figure dans les résultats

#### Scenario: Courriel non cherché
- **WHEN** seul le courriel de Bob contient « courrielbob » et Alice cherche « courrielbob »
- **THEN** le compte de Bob ne figure pas dans les résultats

#### Scenario: Soi-même exclu
- **WHEN** Alice Tremblay cherche « tremblay »
- **THEN** son propre compte ne figure pas dans les résultats

#### Scenario: Caractère joker cherché tel quel
- **WHEN** aucun prénom ni nom ne contient « 50% » et Alice cherche « 50% »
- **THEN** aucun compte ne figure dans les résultats

#### Scenario: Joker pleine chasse cherché tel quel
- **WHEN** aucun prénom ni nom ne contient « %%% » et Alice cherche « ％％％ »
- **THEN** aucun compte ne figure dans les résultats

#### Scenario: Joker présent dans un nom
- **WHEN** le nom de Bob est « Gagnon%%% », aucun autre compte ne contient « %%% », et Alice cherche « %%% »
- **THEN** seul le compte de Bob figure dans les résultats

#### Scenario: Ordre des résultats
- **WHEN** Carole, bob, Élise et Albert ont le nom « Leclerc » et Alice cherche « leclerc »
- **THEN** ils sont listés dans l'ordre Albert, bob, Carole, Élise

#### Scenario: Homonymes
- **WHEN** deux comptes s'appellent Bob Gagnon et Alice cherche « gagnon »
- **THEN** le plus ancien des deux comptes est listé en premier

#### Scenario: Contenu avant ressemblance
- **WHEN** Albert Gagnon et Zoé Gagné ont un compte et Alice cherche « gagne »
- **THEN** Zoé Gagné est listée avant Albert Gagnon

### Requirement: Informations affichées
Chaque résultat SHALL afficher le prénom et le nom du compte, et MUST NOT
afficher son courriel, son adresse ni son téléphone.

#### Scenario: Coordonnées cachées
- **WHEN** Bob a un courriel, une adresse et un téléphone et Alice le trouve par une recherche
- **THEN** la page de résultats affiche « Bob Gagnon »
- **AND** elle n'affiche ni son courriel, ni son adresse, ni son téléphone

### Requirement: Recherche trop courte ou sans résultat
Un texte cherché qui compte moins de 3 caractères une fois normalisé (sans accents, un tiret
valant une espace, espaces consécutives réduites à une, espaces des bords retirées) SHALL
afficher « Saisissez au moins 3 caractères » sans chercher ni lister de compte ; le champ de
recherche l'indique aussi avant l'envoi. Une recherche sans résultat SHALL afficher « Aucun
utilisateur ne correspond à « texte » ». Un type de recherche inconnu SHALL afficher « Ce type
de recherche n'est pas disponible ».

#### Scenario: Texte trop court
- **WHEN** Bob Gagnon a un compte et Alice cherche «  bo  »
- **THEN** la page affiche « Saisissez au moins 3 caractères » et aucun compte

#### Scenario: Trois caractères
- **WHEN** Bob Gagnon a un compte et Alice cherche « bob »
- **THEN** le compte de Bob figure dans les résultats

#### Scenario: Texte vide
- **WHEN** Alice lance une recherche avec un texte fait d'espaces
- **THEN** la page affiche « Saisissez au moins 3 caractères » et aucun compte

#### Scenario: Tirets seuls
- **WHEN** Bob Gagnon a un compte et Alice cherche « --- »
- **THEN** la page affiche « Saisissez au moins 3 caractères » et aucun compte

#### Scenario: Tirets typographiques seuls
- **WHEN** Bob Gagnon a un compte et Alice cherche « ––– »
- **THEN** la page affiche « Saisissez au moins 3 caractères » et aucun compte

#### Scenario: Accents sans lettre
- **WHEN** Bob Gagnon a un compte et Alice cherche « e » suivi de trois accents aigus combinants
- **THEN** la page affiche « Saisissez au moins 3 caractères » et aucun compte

#### Scenario: Aucun résultat
- **WHEN** aucun compte ne correspond à « zzz » et Alice cherche « zzz »
- **THEN** la page affiche « Aucun utilisateur ne correspond à « zzz » »

#### Scenario: Recherche d'outils
- **WHEN** Alice demande la page de résultats avec le type « Outil » et le texte « perceuse »
- **THEN** elle arrive sur la page « Trouver un outil » et aucun compte n'est listé

#### Scenario: Tirets seuls en type « Outil »
- **WHEN** Alice choisit « Outil » et cherche « --- »
- **THEN** la page affiche « Saisissez au moins 3 caractères » et elle n'est pas menée à « Trouver un outil »

#### Scenario: Type inconnu
- **WHEN** Alice demande la page de résultats avec le type « lieu »
- **THEN** la page affiche « Ce type de recherche n'est pas disponible » et aucun compte

### Requirement: Action selon la relation de contact
Chaque résultat SHALL offrir une action selon sa relation avec l'utilisateur : « Envoyer une
demande » sans relation ; « Demande envoyée », grisé, si sa demande attend une réponse ;
« Répondre à sa demande », vers « Mes contacts », si ce compte lui a envoyé une demande ; « Déjà en
contact », grisé, s'ils sont en contact.

#### Scenario: Envoi depuis les résultats
- **WHEN** Alice cherche « bob » et clique « Envoyer une demande » à côté de Bob
- **THEN** elle revient sur les résultats de la recherche « bob »
- **AND** le bouton à côté de Bob affiche « Demande envoyée » et est grisé

#### Scenario: Demande reçue
- **WHEN** Bob a envoyé une demande à Alice et Alice cherche « bob »
- **THEN** le résultat de Bob offre « Répondre à sa demande », qui mène à « Mes contacts »

#### Scenario: Contact existant
- **WHEN** Alice et Bob sont en contact et Alice cherche « bob »
- **THEN** le bouton à côté de Bob affiche « Déjà en contact » et est grisé

#### Scenario: Après un refus
- **WHEN** Bob a refusé la demande d'Alice et Alice cherche « bob »
- **THEN** le résultat de Bob offre « Envoyer une demande »

### Requirement: Recherche de type « Outil »
Une recherche de type « Outil » SHALL mener à la page « Trouver un outil », filtrée par le texte
cherché sans les espaces qui l'entourent, la case « Disponible uniquement » décochée. Le minimum
de 3 caractères de la barre de recherche s'applique.

#### Scenario: Recherche d'un outil
- **WHEN** Alice choisit « Outil » et cherche «  perceuse  »
- **THEN** elle arrive sur la page « Trouver un outil »
- **AND** le champ de texte de la page contient « perceuse » et la liste est filtrée par ce texte

#### Scenario: Texte trop court
- **WHEN** Alice choisit « Outil » et cherche « pe »
- **THEN** la page affiche « Saisissez au moins 3 caractères »

### Requirement: Nombre de comptes listés
La recherche d'utilisateurs SHALL lister au plus 25 comptes : les 25 premiers dans l'ordre de
« Correspondance des utilisateurs ». Quand plus de 25 comptes correspondent, la page SHALL afficher
au-dessus des résultats « Plus de 25 utilisateurs correspondent à « texte » ; précisez votre
recherche », avec le texte cherché tel que saisi, sans nombre total. Avec 25 comptes ou moins,
aucun message n'est affiché.

#### Scenario: Plus de 25 comptes
- **WHEN** 26 autres comptes s'appellent Gagnon et Alice cherche « gagnon »
- **THEN** la page liste 25 comptes, les 25 premiers dans l'ordre de tri
- **AND** elle affiche « Plus de 25 utilisateurs correspondent à « gagnon » ; précisez votre recherche »

#### Scenario: Exactement 25 comptes
- **WHEN** 25 autres comptes s'appellent Gagnon et Alice cherche « gagnon »
- **THEN** la page liste les 25 comptes, sans message

#### Scenario: Correspondances exactes gardées
- **WHEN** 25 comptes ressemblent à « gagnon » sans le contenir, un compte contient « gagnon » et Alice cherche « gagnon »
- **THEN** le compte qui contient « gagnon » figure parmi les 25 comptes listés

### Requirement: Comptes supprimés exclus
La recherche d'utilisateurs MUST NOT lister un compte supprimé (ADR 0023), même quand son prénom et
son nom correspondent au texte cherché, et il ne compte pas dans le plafond de 25 comptes.

#### Scenario: Compte supprimé absent des résultats
- **WHEN** Bob Gagnon a supprimé son compte et Alice cherche « gagnon »
- **THEN** le compte de Bob ne figure pas dans les résultats
- **AND** la page affiche « Aucun utilisateur ne correspond à « gagnon » » si aucun autre compte ne correspond

#### Scenario: Plafond sans les comptes supprimés
- **WHEN** 25 autres comptes actifs et 1 compte supprimé s'appellent Gagnon et Alice cherche « gagnon »
- **THEN** la page liste les 25 comptes actifs, sans message de plafond
