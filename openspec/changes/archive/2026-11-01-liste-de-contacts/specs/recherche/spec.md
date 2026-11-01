# Spec Delta

## Purpose

Permettre à un voisin connecté de trouver d'autres voisins sur la plateforme et de voir, pour
chacun, où en est leur relation de contact.

## ADDED Requirements

### Requirement: Barre de recherche dans la navigation
Pour un utilisateur connecté, la barre de navigation SHALL afficher au centre un champ de
recherche précédé d'un menu déroulant du type de recherche : « Utilisateur », choisi, et « Outil »,
affiché mais non sélectionnable. Sur la page de résultats, le champ garde le texte cherché. La
navigation d'un visiteur MUST NOT afficher la barre de recherche.

#### Scenario: Utilisateur connecté
- **WHEN** un utilisateur connecté ouvre une page du site
- **THEN** la navigation contient un champ de recherche et un menu déroulant offrant « Utilisateur » et « Outil »
- **AND** « Outil » n'est pas sélectionnable

#### Scenario: Visiteur
- **WHEN** un visiteur ouvre une page du site
- **THEN** la navigation ne contient pas de champ de recherche

#### Scenario: Texte cherché conservé
- **WHEN** Alice cherche « gagnon »
- **THEN** le champ de recherche de la page de résultats contient « gagnon »

### Requirement: Recherche réservée à un utilisateur connecté
La page de résultats MUST exiger une session ouverte : un visiteur est redirigé vers `/login`.

#### Scenario: Visiteur non connecté
- **WHEN** un visiteur demande la page de résultats de recherche
- **THEN** il est redirigé vers `/login`

### Requirement: Correspondance des utilisateurs
La recherche d'utilisateurs SHALL lister les autres comptes dont le nom d'utilisateur, le prénom,
le nom, ou le prénom suivi du nom contient le texte cherché, sans égard à la casse et aux espaces
qui l'entourent, triés par nom d'utilisateur sans égard à la casse. Le compte de l'utilisateur
n'y figure jamais. `%` et `_` sont cherchés tels quels.

#### Scenario: Par le nom
- **WHEN** Bob Gagnon a un compte et Alice cherche « GAGN »
- **THEN** le compte de Bob figure dans les résultats

#### Scenario: Par le prénom et le nom
- **WHEN** Bob Gagnon a un compte et Alice cherche «  bob gagnon  »
- **THEN** le compte de Bob figure dans les résultats

#### Scenario: Soi-même exclu
- **WHEN** Alice Tremblay cherche « tremblay »
- **THEN** son propre compte ne figure pas dans les résultats

#### Scenario: Caractère joker cherché tel quel
- **WHEN** aucun nom d'utilisateur, prénom ni nom ne contient « 50% » et Alice cherche « 50% »
- **THEN** aucun compte ne figure dans les résultats

#### Scenario: Ordre des résultats
- **WHEN** les comptes « carole », « Bob » et « albert » correspondent à la recherche
- **THEN** ils sont listés dans l'ordre « albert », « Bob », « carole »

### Requirement: Informations affichées
Chaque résultat SHALL afficher le nom d'utilisateur, le prénom et le nom du compte, et MUST NOT
afficher son courriel, son adresse ni son téléphone.

#### Scenario: Coordonnées cachées
- **WHEN** Bob a un courriel, une adresse et un téléphone et Alice le trouve par une recherche
- **THEN** la page de résultats affiche « bob », « Bob » et « Gagnon »
- **AND** elle n'affiche ni son courriel, ni son adresse, ni son téléphone

### Requirement: Recherche trop courte ou sans résultat
Un texte cherché de moins de 3 caractères, sans compter les espaces qui l'entourent, SHALL
afficher « Saisissez au moins 3 caractères » sans chercher ni lister de compte ; le champ de
recherche l'indique aussi avant l'envoi. Une recherche sans résultat SHALL afficher « Aucun
utilisateur ne correspond à « texte » ». Un type de recherche autre que « Utilisateur » SHALL
afficher « Ce type de recherche n'est pas encore disponible ».

#### Scenario: Texte trop court
- **WHEN** Bob Gagnon a un compte et Alice cherche «  bo  »
- **THEN** la page affiche « Saisissez au moins 3 caractères » et aucun compte

#### Scenario: Trois caractères
- **WHEN** Bob Gagnon a un compte et Alice cherche « bob »
- **THEN** le compte de Bob figure dans les résultats

#### Scenario: Texte vide
- **WHEN** Alice lance une recherche avec un texte fait d'espaces
- **THEN** la page affiche « Saisissez au moins 3 caractères » et aucun compte

#### Scenario: Aucun résultat
- **WHEN** aucun compte ne correspond à « zzz » et Alice cherche « zzz »
- **THEN** la page affiche « Aucun utilisateur ne correspond à « zzz » »

#### Scenario: Recherche d'outils
- **WHEN** Alice demande la page de résultats avec le type « Outil »
- **THEN** la page affiche « Ce type de recherche n'est pas encore disponible » et aucun compte

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
