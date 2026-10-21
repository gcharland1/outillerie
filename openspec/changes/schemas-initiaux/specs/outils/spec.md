# Spec Delta

## Purpose

Décrire les outils que les voisins proposent au prêt : à qui ils appartiennent, ce qu'on en montre
à tous, leur état de fonctionnement et ce que seul le propriétaire en voit.

## ADDED Requirements

### Requirement: Outil rattaché à un propriétaire
Le système SHALL enregistrer chaque outil avec exactement un propriétaire, qui est un compte
existant, ainsi qu'un nom et une description. La description est l'information publique de
l'outil.

#### Scenario: Outil complet enregistré
- **WHEN** un outil est enregistré avec un propriétaire existant, un nom et une description
- **THEN** l'outil est conservé avec ces informations

#### Scenario: Outil sans propriétaire refusé
- **WHEN** un outil est enregistré sans propriétaire, ou avec un propriétaire qui n'existe pas
- **THEN** l'enregistrement est refusé et aucun outil n'est créé

#### Scenario: Outil sans nom refusé
- **WHEN** un outil est enregistré sans nom ou sans description
- **THEN** l'enregistrement est refusé et aucun outil n'est créé

### Requirement: État fonctionnel de l'outil
Le système SHALL enregistrer l'état d'un outil parmi `fonctionnel`, `a_reparer` et `hors_service`,
et MUST refuser toute autre valeur. Un outil enregistré sans état est `fonctionnel`.

#### Scenario: État par défaut
- **WHEN** un outil est enregistré sans état
- **THEN** son état est `fonctionnel`

#### Scenario: État inconnu refusé
- **WHEN** un outil est enregistré avec l'état `neuf`
- **THEN** l'enregistrement est refusé

### Requirement: Notes privées du propriétaire
Le système SHALL permettre au propriétaire de joindre à un outil des notes privées facultatives,
destinées à lui seul, distinctes de la description publique.

#### Scenario: Outil sans notes
- **WHEN** un outil est enregistré sans notes privées
- **THEN** l'outil est conservé sans notes

### Requirement: Retrait d'un outil de la circulation
Le système SHALL indiquer pour chaque outil s'il est en circulation ; un nouvel outil l'est. Un
outil retiré reste enregistré avec sa photo et ses prêts.

#### Scenario: Nouvel outil en circulation
- **WHEN** un outil est enregistré sans indication de circulation
- **THEN** l'outil est en circulation

#### Scenario: Outil retiré conservé
- **WHEN** un outil qui a un prêt `rendu` est retiré de la circulation
- **THEN** l'outil et son prêt restent enregistrés

### Requirement: Photo de l'outil
Le système SHALL conserver au plus une photo par outil, avec son type de contenu. Une nouvelle
photo remplace celle que l'outil avait déjà. La photo d'un outil supprimé MUST être supprimée avec
lui.

#### Scenario: Photo enregistrée
- **WHEN** une photo JPEG est enregistrée pour un outil
- **THEN** son contenu et le type `image/jpeg` sont conservés pour cet outil

#### Scenario: Nouvelle photo
- **WHEN** une photo PNG est enregistrée pour un outil qui a déjà une photo JPEG
- **THEN** l'outil n'a plus que la photo PNG

#### Scenario: Jamais deux photos
- **WHEN** une seconde photo est ajoutée à côté de celle qu'un outil a déjà, sans la remplacer
- **THEN** l'ajout est refusé et la première photo est conservée

#### Scenario: Suppression de l'outil
- **WHEN** un outil qui a une photo et aucun prêt est supprimé
- **THEN** sa photo est supprimée aussi
