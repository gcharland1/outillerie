# Spec Delta

## ADDED Requirements

### Requirement: Image de l'app étiquetée
Docker Compose SHALL nommer l'image de l'app `outillerie-app` et l'étiqueter avec la variable
d'environnement `APP_TAG`, `dev` par défaut.

#### Scenario: Développement
- **WHEN** `docker compose up --build` est lancé sans `APP_TAG`
- **THEN** l'image construite est `outillerie-app:dev`

#### Scenario: Étiquette fournie
- **WHEN** `APP_TAG` vaut un SHA de commit
- **THEN** l'image construite ou démarrée est `outillerie-app:<SHA>`

### Requirement: Healthcheck de l'app
Docker Compose MUST déclarer un healthcheck pour l'app : elle est saine quand sa page d'accueil
répond avec succès depuis l'intérieur du conteneur, après un délai de démarrage qui couvre les
migrations.

#### Scenario: App démarrée
- **WHEN** les migrations sont appliquées et l'app répond sur sa page d'accueil
- **THEN** le conteneur de l'app est sain

#### Scenario: Migration en échec
- **WHEN** la migration échoue au démarrage
- **THEN** le conteneur de l'app ne devient jamais sain

### Requirement: Migrations au démarrage désactivables
Le conteneur de l'app SHALL appliquer les migrations à son démarrage, sauf quand la variable
`SKIP_DB_UPGRADE` vaut `1`, transmise par Docker Compose avec `0` par défaut.

#### Scenario: Démarrage ordinaire
- **WHEN** l'app démarre sans `SKIP_DB_UPGRADE`
- **THEN** les migrations en attente sont appliquées avant que l'app serve

#### Scenario: Migrations désactivées
- **WHEN** l'app démarre avec `SKIP_DB_UPGRADE=1` sur une base dont la révision lui est inconnue
- **THEN** elle démarre sans lancer de migration et devient saine

### Requirement: Redémarrage automatique des services
Docker Compose SHALL redémarrer l'app et la base après un plantage ou un redémarrage de l'hôte, sauf
si elles ont été arrêtées volontairement.

#### Scenario: Redémarrage de l'hôte
- **WHEN** l'hôte redémarre alors que la pile était en marche
- **THEN** l'app et la base redémarrent sans intervention

### Requirement: Clé secrète hors développement
Hors de l'environnement `development`, l'app MUST refuser de démarrer quand `FLASK_SECRET_KEY` est
absente, vide ou égale à la valeur d'exemple `dev-seulement`.

#### Scenario: Clé d'exemple en production
- **WHEN** l'app démarre en `production` avec `FLASK_SECRET_KEY=dev-seulement`
- **THEN** elle refuse de démarrer avec un message qui nomme la variable, sans afficher sa valeur

#### Scenario: Clé absente en production
- **WHEN** l'app démarre en `production` sans `FLASK_SECRET_KEY`
- **THEN** elle refuse de démarrer avec un message qui nomme la variable

#### Scenario: Clé d'exemple en développement
- **WHEN** l'app démarre en `development` avec `FLASK_SECRET_KEY=dev-seulement`
- **THEN** elle démarre
