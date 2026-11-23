## MODIFIED Requirements

### Requirement: Cookie de session sécurisé hors développement
Hors de l'environnement `development`, le cookie de session et le cookie persistant de « Rester
connecté » MUST porter l'attribut `Secure`, pour que le navigateur ne les envoie qu'en HTTPS. En
`development`, ils MUST NOT le porter.

#### Scenario: Connexion en production
- **WHEN** un utilisateur se connecte et que l'environnement est `production`
- **THEN** le cookie de session posé porte l'attribut `Secure`

#### Scenario: Connexion en développement
- **WHEN** un utilisateur se connecte et que l'environnement est `development`
- **THEN** le cookie de session posé ne porte pas l'attribut `Secure`

#### Scenario: Cookie persistant en production
- **WHEN** un utilisateur se connecte case « Rester connecté » cochée et que l'environnement est `production`
- **THEN** le cookie persistant posé porte l'attribut `Secure`

#### Scenario: Cookie persistant en développement
- **WHEN** un utilisateur se connecte case « Rester connecté » cochée et que l'environnement est `development`
- **THEN** le cookie persistant posé ne porte pas l'attribut `Secure`
