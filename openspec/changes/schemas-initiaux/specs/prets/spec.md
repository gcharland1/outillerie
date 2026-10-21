# Spec Delta

## Purpose

Encadrer le prêt d'un outil à un voisin : qui emprunte, pour quelles dates, où en est le prêt, et
la garantie qu'un même outil n'est jamais promis à deux emprunteurs en même temps.

## ADDED Requirements

### Requirement: Prêt d'un outil à un emprunteur
Le système SHALL enregistrer chaque prêt avec un outil existant, un emprunteur qui est un compte
existant, une date de début et une date de fin. Le prêteur d'un prêt est le propriétaire de
l'outil prêté.

#### Scenario: Prêt enregistré
- **WHEN** un prêt est enregistré pour un outil, un emprunteur, du 3 au 5 novembre
- **THEN** le prêt est conservé avec ces informations
- **AND** son prêteur est le propriétaire de l'outil

#### Scenario: Outil ou emprunteur inexistant
- **WHEN** un prêt est enregistré pour un outil ou un emprunteur qui n'existe pas
- **THEN** l'enregistrement est refusé et aucun prêt n'est créé

### Requirement: Dates du prêt
Le système MUST refuser un prêt dont la date de fin précède la date de début. Les dates sont des
jours entiers, et les deux bornes font partie du prêt : un prêt peut commencer et finir le même jour.

#### Scenario: Prêt d'une journée
- **WHEN** un prêt est enregistré du 3 au 3 novembre
- **THEN** le prêt est conservé

#### Scenario: Fin avant le début
- **WHEN** un prêt est enregistré du 5 au 3 novembre
- **THEN** l'enregistrement est refusé

### Requirement: Statut du prêt
Le système SHALL enregistrer le statut d'un prêt parmi `demande`, `accepte`, `refuse`, `annule`,
`remis` et `rendu`, et MUST refuser toute autre valeur. Un prêt enregistré sans statut est une
`demande`.

#### Scenario: Statut par défaut
- **WHEN** un prêt est enregistré sans statut
- **THEN** son statut est `demande`

#### Scenario: Statut inconnu refusé
- **WHEN** un prêt est enregistré avec le statut `en_cours`
- **THEN** l'enregistrement est refusé

### Requirement: Aucun chevauchement des prêts engagés
Le système MUST refuser que deux prêts d'un même outil aux statuts `accepte` ou `remis` partagent un
jour, même quand deux enregistrements arrivent en même temps. Les demandes peuvent se chevaucher
entre elles et avec un prêt engagé ; les prêts refusés, annulés ou rendus ne bloquent aucune date.

#### Scenario: Prêts engagés qui se chevauchent
- **WHEN** un outil a un prêt `accepte` du 3 au 5 novembre
- **AND** un second prêt `accepte` du 5 au 7 novembre est enregistré pour cet outil
- **THEN** l'enregistrement du second prêt est refusé

#### Scenario: Prêts engagés consécutifs
- **WHEN** un outil a un prêt `remis` du 3 au 5 novembre
- **AND** un prêt `accepte` du 6 au 8 novembre est enregistré pour cet outil
- **THEN** le second prêt est conservé

#### Scenario: Demandes concurrentes
- **WHEN** un outil a un prêt `accepte` du 3 au 5 novembre
- **AND** deux prêts `demande` du 4 au 6 novembre sont enregistrés pour cet outil
- **THEN** les deux demandes sont conservées

#### Scenario: Acceptation d'une demande qui chevauche
- **WHEN** un outil a un prêt `accepte` du 3 au 5 novembre et une `demande` du 4 au 6 novembre
- **AND** la demande passe au statut `accepte`
- **THEN** le changement de statut est refusé

#### Scenario: Prêt rendu libère ses dates
- **WHEN** un outil a un prêt `rendu` du 3 au 5 novembre
- **AND** un prêt `accepte` du 3 au 5 novembre est enregistré pour cet outil
- **THEN** le second prêt est conservé

#### Scenario: Outils différents
- **WHEN** deux outils ont chacun un prêt `accepte` du 3 au 5 novembre
- **THEN** les deux prêts sont conservés

### Requirement: Historique des prêts conservé
Le système MUST refuser la suppression d'un outil qui figure dans au moins un prêt, quel que soit
son statut, pour que l'historique des prêts reste complet. Le retrait de la circulation remplace
alors la suppression.

#### Scenario: Outil déjà prêté
- **WHEN** la suppression d'un outil qui a un prêt `rendu` est demandée
- **THEN** la suppression est refusée et l'outil et son prêt sont conservés
