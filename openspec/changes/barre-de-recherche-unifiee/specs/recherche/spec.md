## ADDED Requirements

### Requirement: Sections de la page de résultats
Une recherche d'au moins 3 caractères SHALL mener à la page « Résultats de recherche », qui affiche
la section « Utilisateurs » puis la section « Outils ». Le paramètre `type` d'une ancienne adresse
MUST être ignoré, sans erreur.

#### Scenario: Deux sections
- **WHEN** Alice cherche « gagnon »
- **THEN** la page « Résultats de recherche » affiche une section « Utilisateurs » et une section « Outils »

### Requirement: Section « Outils »
La section « Outils » SHALL montrer, en cartes et par pertinence, les outils visibles des contacts
qui correspondent au texte, comme « Trouver un outil ». Elle affiche les 6 premiers et « X de Y »,
Y étant le total ; au-delà de 6, un bouton « Voir plus » mène à « Trouver un outil » filtré par le
texte, « Disponible uniquement » décochée, triée par pertinence. Sans outil : « Aucun résultat
d'outil », avec ou sans contact.

#### Scenario: Six outils ou moins
- **WHEN** 2 outils des contacts d'Alice correspondent à « perceuse » et Alice cherche « perceuse »
- **THEN** la section « Outils » affiche les 2 cartes et « 2 de 2 », sans « Voir plus »

#### Scenario: Plus de six outils
- **WHEN** 8 outils des contacts d'Alice correspondent à « perceuse » et Alice cherche « perceuse »
- **THEN** la section « Outils » affiche les 6 premières cartes par pertinence et « 6 de 8 »
- **AND** son bouton « Voir plus » mène à « Trouver un outil » dont le champ contient « perceuse »

#### Scenario: Outils hors d'atteinte
- **WHEN** Bob, qui n'est pas contact d'Alice, a une perceuse et Alice cherche « perceuse »
- **THEN** la section « Outils » ne montre pas la perceuse de Bob

#### Scenario: Aucun outil
- **WHEN** aucun outil des contacts d'Alice ne correspond à « zzz » et Alice cherche « zzz »
- **THEN** la section « Outils » affiche « Aucun résultat d'outil »

#### Scenario: Sans contact
- **WHEN** Alice n'a aucun contact et cherche « perceuse »
- **THEN** la section « Outils » affiche « Aucun résultat d'outil »

#### Scenario: Retour d'un emprunt annulé
- **WHEN** Alice clique « Emprunter » sur une carte de la section, puis « Annuler »
- **THEN** elle arrive sur « Trouver un outil » dont le champ contient le texte cherché

### Requirement: Filtre de relation
En tête de la section « Utilisateurs », dès qu'un texte valide est cherché, la page SHALL offrir un
filtre « Tous les utilisateurs » (par défaut), « Mes contacts uniquement » ou « Pas en contact
uniquement », appliqué par un bouton « Filtrer », sans effet sur la section « Outils ». Une demande
en attente, envoyée ou reçue, est « Pas en contact ». Le filtre précède le plafond de 25 et les
compteurs. Une valeur inconnue vaut « Tous les utilisateurs ».

#### Scenario: Mes contacts uniquement
- **WHEN** Bob Gagnon est contact d'Alice, Carole Gagnon ne l'est pas, et Alice cherche « gagnon » avec « Mes contacts uniquement »
- **THEN** seul Bob est listé, avec « 1 de 1 »

#### Scenario: Pas en contact uniquement
- **WHEN** Bob Gagnon est contact d'Alice, Alice a envoyé une demande à Carole Gagnon, et Alice cherche « gagnon » avec « Pas en contact uniquement »
- **THEN** seule Carole est listée

#### Scenario: Filtre sans résultat
- **WHEN** Alice n'a aucun contact et cherche « gagnon » avec « Mes contacts uniquement »
- **THEN** la section affiche « Aucun résultat d'utilisateur »
- **AND** le filtre reste affiché avec « Mes contacts uniquement » choisi

#### Scenario: Filtre sur la section « Outils »
- **WHEN** Alice cherche « perceuse » avec « Pas en contact uniquement »
- **THEN** la section « Outils » est la même qu'avec « Tous les utilisateurs »

#### Scenario: Filtre avant le plafond
- **WHEN** 26 comptes Gagnon ne sont pas contacts d'Alice, Bob Gagnon l'est, et Alice cherche « gagnon » avec « Mes contacts uniquement »
- **THEN** Bob est listé, avec « 1 de 1 »

#### Scenario: Valeur inconnue
- **WHEN** l'adresse des résultats porte un filtre de relation « amis »
- **THEN** la page répond 200 et liste comme « Tous les utilisateurs »

### Requirement: Sélecteur de distance à venir
En tête de la section « Utilisateurs », la page SHALL afficher un sélecteur « Dans un rayon de »
offrant « 1km », « 3km », « 5km », « 10km » et « Aucune limite », grisé, « Aucune limite » choisi,
avec la mention « à venir ». Il MUST rester sans effet sur les résultats.

#### Scenario: Sélecteur grisé
- **WHEN** Alice cherche « gagnon »
- **THEN** la section « Utilisateurs » affiche le sélecteur « Dans un rayon de » désactivé, « Aucune limite » choisi, et « à venir »

#### Scenario: Distance dans l'adresse ignorée
- **WHEN** l'adresse des résultats porte une distance « 1km »
- **THEN** les résultats sont les mêmes que sans distance

## MODIFIED Requirements

### Requirement: Barre de recherche dans la navigation
Pour un utilisateur connecté, la barre de navigation SHALL afficher au centre un champ « Rechercher… »
et un bouton « Rechercher », sans menu de type de recherche. Sur la page de résultats, le champ garde
le texte cherché. La navigation d'un visiteur MUST NOT afficher la barre de recherche.

#### Scenario: Utilisateur connecté
- **WHEN** un utilisateur connecté ouvre une page du site
- **THEN** la navigation contient le champ « Rechercher… » et le bouton « Rechercher »
- **AND** elle ne contient pas de menu « Outil / Utilisateur »

#### Scenario: Visiteur
- **WHEN** un visiteur ouvre une page du site
- **THEN** la navigation ne contient pas de champ de recherche

#### Scenario: Texte cherché conservé
- **WHEN** Alice cherche « gagnon »
- **THEN** le champ de recherche de la page de résultats contient « gagnon »

#### Scenario: Type inconnu
- **WHEN** Alice demande la page de résultats avec le type « lieu »
- **THEN** la navigation n'affiche aucun menu de type de recherche

### Requirement: Recherche trop courte ou sans résultat
Un texte cherché qui compte moins de 3 caractères une fois normalisé (sans accents, un tiret
valant une espace, espaces consécutives réduites à une, espaces des bords retirées) SHALL
afficher seulement « Saisissez au moins 3 caractères », sans section ni recherche ; le champ de
recherche l'indique aussi avant l'envoi. Une section « Utilisateurs » sans compte SHALL afficher
« Aucun résultat d'utilisateur ».

#### Scenario: Texte trop court
- **WHEN** Bob Gagnon a un compte et Alice cherche «  bo  »
- **THEN** la page affiche « Saisissez au moins 3 caractères », sans section « Utilisateurs » ni « Outils »

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
- **THEN** la section « Utilisateurs » affiche « Aucun résultat d'utilisateur »

#### Scenario: Recherche d'outils
- **WHEN** Alice demande la page de résultats avec le type « Outil » et le texte « perceuse »
- **THEN** elle reste sur la page « Résultats de recherche », qui affiche les sections « Utilisateurs » et « Outils »

#### Scenario: Tirets seuls en type « Outil »
- **WHEN** Alice demande la page de résultats avec le type « Outil » et le texte « --- »
- **THEN** la page affiche « Saisissez au moins 3 caractères » et elle n'est pas menée à « Trouver un outil »

#### Scenario: Type inconnu
- **WHEN** Alice demande la page de résultats avec le type « lieu » et le texte « gagnon »
- **THEN** la page n'affiche pas « Ce type de recherche n'est pas disponible » et affiche les deux sections

### Requirement: Action selon la relation de contact
Chaque résultat SHALL offrir une action selon sa relation avec l'utilisateur : « Envoyer une
demande » sans relation ; « Demande envoyée », grisé, si sa demande attend une réponse ;
« Répondre à sa demande », vers « Mes contacts », si ce compte lui a envoyé une demande ; « Déjà en
contact », grisé, s'ils sont en contact. Après l'envoi d'une demande, les résultats reviennent avec
le texte, le filtre et l'état déplié d'avant.

#### Scenario: Envoi depuis les résultats
- **WHEN** Alice cherche « bob » et clique « Envoyer une demande » à côté de Bob
- **THEN** elle revient sur les résultats de la recherche « bob »
- **AND** le bouton à côté de Bob affiche « Demande envoyée » et est grisé

#### Scenario: Envoi depuis une vue filtrée et dépliée
- **WHEN** Alice cherche « gagnon » avec « Pas en contact uniquement », clique « Voir plus », puis « Envoyer une demande » à côté de Bob
- **THEN** elle revient sur les résultats de « gagnon », filtrés par « Pas en contact uniquement » et dépliés

#### Scenario: Retour falsifié
- **WHEN** l'envoi d'une demande porte un filtre « amis » et un état déplié « oui »
- **THEN** les résultats reviennent avec « Tous les utilisateurs » et repliés

#### Scenario: Demande reçue
- **WHEN** Bob a envoyé une demande à Alice et Alice cherche « bob »
- **THEN** le résultat de Bob offre « Répondre à sa demande », qui mène à « Mes contacts »

#### Scenario: Contact existant
- **WHEN** Alice et Bob sont en contact et Alice cherche « bob »
- **THEN** le bouton à côté de Bob affiche « Déjà en contact » et est grisé

#### Scenario: Après un refus
- **WHEN** Bob a refusé la demande d'Alice et Alice cherche « bob »
- **THEN** le résultat de Bob offre « Envoyer une demande »

### Requirement: Nombre de comptes listés
La section « Utilisateurs » SHALL lister les 5 premiers comptes dans l'ordre de « Correspondance des
utilisateurs » et « X de Y », Y étant le total, ou « plus de 25 » au-delà de 25, sans le compter.
Au-delà de 5, un bouton « Voir plus » déplie la même page jusqu'à 25 comptes ; au-delà de 25, la
vue dépliée seule affiche « Plus de 25 utilisateurs correspondent à « texte » ; précisez votre
recherche ».

#### Scenario: Cinq comptes ou moins
- **WHEN** 3 autres comptes s'appellent Gagnon et Alice cherche « gagnon »
- **THEN** la section liste les 3 comptes et « 3 de 3 », sans « Voir plus »

#### Scenario: Plus de cinq comptes
- **WHEN** 12 autres comptes s'appellent Gagnon et Alice cherche « gagnon »
- **THEN** la section liste les 5 premiers comptes dans l'ordre de tri et « 5 de 12 », avec « Voir plus »
- **AND** « Voir plus » affiche la même page avec les 12 comptes et « 12 de 12 », sans « Voir plus »

#### Scenario: Plus de 25 comptes
- **WHEN** 26 autres comptes s'appellent Gagnon et Alice cherche « gagnon »
- **THEN** la section liste 5 comptes et « 5 de plus de 25 », sans le message de plafond
- **AND** après « Voir plus », elle liste les 25 premiers, « 25 de plus de 25 » et « Plus de 25 utilisateurs correspondent à « gagnon » ; précisez votre recherche »

#### Scenario: Exactement 25 comptes
- **WHEN** 25 autres comptes s'appellent Gagnon et Alice cherche « gagnon » puis clique « Voir plus »
- **THEN** la section liste les 25 comptes et « 25 de 25 », sans message

#### Scenario: Vue dépliée demandée avec peu de comptes
- **WHEN** 3 autres comptes s'appellent Gagnon et l'adresse des résultats de « gagnon » demande la vue dépliée
- **THEN** la section liste les 3 comptes et « 3 de 3 », sans « Voir plus »

#### Scenario: État déplié inconnu
- **WHEN** 12 autres comptes s'appellent Gagnon et l'adresse des résultats de « gagnon » porte un état déplié « tout »
- **THEN** la section liste 5 comptes, comme repliée

#### Scenario: Correspondances exactes gardées
- **WHEN** 25 comptes ressemblent à « gagnon » sans le contenir, un compte contient « gagnon » et Alice cherche « gagnon » puis clique « Voir plus »
- **THEN** le compte qui contient « gagnon » figure parmi les 25 comptes listés

### Requirement: Comptes supprimés exclus
La recherche d'utilisateurs MUST NOT lister un compte supprimé (ADR 0023), même quand son prénom et
son nom correspondent au texte cherché, et il ne compte ni dans le plafond de 25 comptes ni dans
les compteurs.

#### Scenario: Compte supprimé absent des résultats
- **WHEN** Bob Gagnon a supprimé son compte et Alice cherche « gagnon »
- **THEN** le compte de Bob ne figure pas dans les résultats
- **AND** la section « Utilisateurs » affiche « Aucun résultat d'utilisateur » si aucun autre compte ne correspond

#### Scenario: Plafond sans les comptes supprimés
- **WHEN** 25 autres comptes actifs et 1 compte supprimé s'appellent Gagnon et Alice cherche « gagnon » puis clique « Voir plus »
- **THEN** la section liste les 25 comptes actifs et « 25 de 25 », sans message de plafond

## REMOVED Requirements

### Requirement: Recherche de type « Outil »
**Reason**: la barre n'a plus de type ; les outils sont une section de la page de résultats.
**Migration**: le paramètre `type` est ignoré ; « Voir plus » de la section « Outils » mène à
« Trouver un outil » filtré par le texte.
