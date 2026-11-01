# Spec Delta

## MODIFIED Requirements

### Requirement: Accès à l'image
L'image d'un outil SHALL être servie à une adresse stable propre à l'outil : à son propriétaire,
que l'outil soit en circulation ou retiré, et aux contacts du propriétaire tant que l'outil est en
circulation et n'est pas « Hors d'usage ». Tout autre compte, un visiteur, un outil sans photo ou
inexistant MUST recevoir la même réponse 404.

#### Scenario: Propriétaire
- **WHEN** Alice demande l'image de sa perceuse
- **THEN** elle reçoit la photo, de type `image/jpeg`

#### Scenario: Outil retiré
- **WHEN** Alice a retiré sa perceuse et demande son image
- **THEN** elle reçoit la photo

#### Scenario: Contact du propriétaire
- **WHEN** Bob est en contact avec Alice et demande l'image de sa perceuse en circulation
- **THEN** il reçoit la photo

#### Scenario: Contact et outil retiré
- **WHEN** Bob est en contact avec Alice, qui a retiré sa perceuse
- **AND** Bob demande l'image de la perceuse
- **THEN** le système répond 404

#### Scenario: Contact et outil hors d'usage
- **WHEN** Bob est en contact avec Alice, dont la perceuse est « Hors d'usage »
- **AND** Bob demande l'image de la perceuse
- **THEN** le système répond 404

#### Scenario: Ancien contact
- **WHEN** Bob a vu la perceuse d'Alice, puis Alice l'a retiré de ses contacts
- **AND** Bob redemande l'image de la perceuse, avec l'étiquette reçue la première fois
- **THEN** le système répond 404

#### Scenario: Autre voisin
- **WHEN** Carole, qui n'est pas en contact avec Alice, demande l'image de la perceuse d'Alice
- **THEN** le système répond 404

#### Scenario: Visiteur
- **WHEN** un visiteur demande l'image de la perceuse d'Alice
- **THEN** le système répond 404

#### Scenario: Outil sans photo
- **WHEN** Alice demande l'image d'un de ses outils sans photo
- **THEN** le système répond 404
