# Spec Delta

## MODIFIED Requirements

### Requirement: Barre de recherche dans la navigation
Pour un utilisateur connecté, la barre de navigation SHALL afficher au centre un champ de
recherche précédé d'un menu déroulant du type de recherche : « Utilisateur », choisi par défaut,
et « Outil ». Sur la page de résultats, le champ garde le texte cherché. La navigation d'un
visiteur MUST NOT afficher la barre de recherche.

#### Scenario: Utilisateur connecté
- **WHEN** un utilisateur connecté ouvre une page du site
- **THEN** la navigation contient un champ de recherche et un menu déroulant offrant « Utilisateur » et « Outil »
- **AND** « Utilisateur » est choisi et « Outil » est sélectionnable

#### Scenario: Visiteur
- **WHEN** un visiteur ouvre une page du site
- **THEN** la navigation ne contient pas de champ de recherche

#### Scenario: Texte cherché conservé
- **WHEN** Alice cherche « gagnon »
- **THEN** le champ de recherche de la page de résultats contient « gagnon »

### Requirement: Recherche trop courte ou sans résultat
Un texte cherché de moins de 3 caractères, sans compter les espaces qui l'entourent, SHALL
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

#### Scenario: Aucun résultat
- **WHEN** aucun compte ne correspond à « zzz » et Alice cherche « zzz »
- **THEN** la page affiche « Aucun utilisateur ne correspond à « zzz » »

#### Scenario: Recherche d'outils
- **WHEN** Alice demande la page de résultats avec le type « Outil » et le texte « perceuse »
- **THEN** elle arrive sur la page « Trouver un outil » et aucun compte n'est listé

#### Scenario: Type inconnu
- **WHEN** Alice demande la page de résultats avec le type « lieu »
- **THEN** la page affiche « Ce type de recherche n'est pas disponible » et aucun compte

## ADDED Requirements

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
