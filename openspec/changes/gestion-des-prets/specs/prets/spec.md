# Spec Delta

## MODIFIED Requirements

### Requirement: Statut du prêt
Le système SHALL enregistrer le statut d'un prêt parmi `requested`, `accepted`, `refused`, `canceled`,
`handover_claimed`, `lent`, `return_claimed` et `returned`, et MUST refuser toute autre valeur. Un prêt
enregistré sans statut a le statut `requested`.

#### Scenario: Statut par défaut
- **WHEN** un prêt est enregistré sans statut
- **THEN** son statut est `requested`

#### Scenario: Statut inconnu refusé
- **WHEN** un prêt est enregistré avec le statut `in_progress`
- **THEN** l'enregistrement est refusé

#### Scenario: Statuts à confirmer
- **WHEN** un prêt est enregistré avec le statut `handover_claimed` ou `return_claimed`
- **THEN** le prêt est conservé

### Requirement: Aucun chevauchement des prêts engagés
Le système MUST refuser que deux prêts d'un même outil aux statuts `accepted`, `handover_claimed`,
`lent` ou `return_claimed` partagent un jour, même quand deux enregistrements arrivent en même temps.
Les demandes peuvent se chevaucher entre elles et avec un prêt engagé ; les prêts refusés, annulés ou
rendus ne bloquent aucune date.

#### Scenario: Prêts engagés qui se chevauchent
- **WHEN** un outil a un prêt `accepted` du 3 au 5 novembre
- **AND** un second prêt `accepted` du 5 au 7 novembre est enregistré pour cet outil
- **THEN** l'enregistrement du second prêt est refusé

#### Scenario: Prêts engagés consécutifs
- **WHEN** un outil a un prêt `lent` du 3 au 5 novembre
- **AND** un prêt `accepted` du 6 au 8 novembre est enregistré pour cet outil
- **THEN** le second prêt est conservé

#### Scenario: Demandes concurrentes
- **WHEN** un outil a un prêt `accepted` du 3 au 5 novembre
- **AND** deux prêts `requested` du 4 au 6 novembre sont enregistrés pour cet outil
- **THEN** les deux demandes sont conservées

#### Scenario: Acceptation d'une demande qui chevauche
- **WHEN** un outil a un prêt `accepted` du 3 au 5 novembre et un prêt `requested` du 4 au 6 novembre
- **AND** ce prêt passe au statut `accepted`
- **THEN** le changement de statut est refusé

#### Scenario: Prêt à confirmer engagé
- **WHEN** un outil a un prêt `return_claimed` du 3 au 5 novembre
- **AND** un prêt `accepted` du 4 au 6 novembre est enregistré pour cet outil
- **THEN** l'enregistrement est refusé

#### Scenario: Prêt rendu libère ses dates
- **WHEN** un outil a un prêt `returned` du 3 au 5 novembre
- **AND** un prêt `accepted` du 3 au 5 novembre est enregistré pour cet outil
- **THEN** le second prêt est conservé

#### Scenario: Outils différents
- **WHEN** deux outils ont chacun un prêt `accepted` du 3 au 5 novembre
- **THEN** les deux prêts sont conservés
