# Spec Delta

## MODIFIED Requirements

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
