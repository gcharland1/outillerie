# deploiement Specification

## Purpose
Fixer comment l'app se comporte selon son environnement d'exécution et derrière le proxy qui termine
le TLS : schéma des requêtes, attributs du cookie de session et ports publiés par Docker Compose.

## Requirements

### Requirement: Environnement d'exécution
Le système SHALL lire son environnement dans la variable `FLASK_ENVIRONMENT` et MUST le considérer
comme `development` quand la variable est absente. Docker Compose SHALL transmettre cette variable
au conteneur de l'app, avec `development` comme valeur par défaut.

#### Scenario: Variable absente
- **WHEN** l'app démarre sans `FLASK_ENVIRONMENT`
- **THEN** elle se comporte en environnement `development`

#### Scenario: Variable transmise par Compose
- **WHEN** le `.env` lu par Compose définit `FLASK_ENVIRONMENT=production`
- **THEN** le conteneur de l'app reçoit `FLASK_ENVIRONMENT=production`

### Requirement: Schéma relayé par le proxy
Le système SHALL traiter une requête comme reçue en HTTPS quand l'unique proxy devant lui l'indique
par l'en-tête `X-Forwarded-Proto: https`. Les URL absolues qu'il génère MUST alors utiliser `https`.

#### Scenario: Requête relayée en HTTPS
- **WHEN** une requête arrive en HTTP avec l'en-tête `X-Forwarded-Proto: https`
- **THEN** l'app la considère comme sécurisée
- **AND** une URL absolue générée pendant cette requête commence par `https://`

#### Scenario: Requête directe
- **WHEN** une requête arrive en HTTP sans en-tête `X-Forwarded-Proto`
- **THEN** l'app la considère comme non sécurisée
- **AND** une URL absolue générée pendant cette requête commence par `http://`

### Requirement: Cookie de session sécurisé hors développement
Hors de l'environnement `development`, le cookie de session MUST porter l'attribut `Secure`, pour
que le navigateur ne l'envoie qu'en HTTPS. En `development`, il MUST NOT le porter.

#### Scenario: Connexion en production
- **WHEN** un utilisateur se connecte et que l'environnement est `production`
- **THEN** le cookie de session posé porte l'attribut `Secure`

#### Scenario: Connexion en développement
- **WHEN** un utilisateur se connecte et que l'environnement est `development`
- **THEN** le cookie de session posé ne porte pas l'attribut `Secure`

### Requirement: Ports publiés sur la boucle locale
Docker Compose MUST publier les ports de l'app et de la base sur `127.0.0.1` seulement : l'app sur
le port 8080, la base sur le port 5430. Les services SHALL rester joignables entre eux par le réseau
interne de Compose.

#### Scenario: Accès depuis l'hôte
- **WHEN** un processus de l'hôte se connecte à `127.0.0.1:8080` ou à `127.0.0.1:5430`
- **THEN** il joint respectivement l'app et la base

#### Scenario: Accès depuis une autre machine
- **WHEN** une autre machine se connecte au port 8080 ou 5430 d'une adresse de l'hôte
- **THEN** la connexion est refusée

#### Scenario: Accès de l'app à la base
- **WHEN** l'app démarre dans Compose
- **THEN** elle joint la base à `db:5432`

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
