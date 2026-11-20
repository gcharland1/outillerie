# Spec Delta

## MODIFIED Requirements

### Requirement: Healthcheck de l'app
Docker Compose MUST déclarer un healthcheck pour l'app : elle est saine quand sa page de connexion
répond avec succès depuis l'intérieur du conteneur, sans session, après un délai de démarrage qui
couvre les migrations.

#### Scenario: App démarrée
- **WHEN** les migrations sont appliquées et l'app répond sur sa page de connexion
- **THEN** le conteneur de l'app est sain

#### Scenario: Migration en échec
- **WHEN** la migration échoue au démarrage
- **THEN** le conteneur de l'app ne devient jamais sain
