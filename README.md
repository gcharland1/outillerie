# L'Outillerie - Partage d'outils Communaitaire

L'outillerie est un site web communaitaire gratuit favorisant le partage d'outils
entre voisins. Que ce soit pour des raisons financières ou environnementales, avoir 
12 tondeuses dans 12 remises qui ne servent chacunes moins d'une fois par semaine 
n'est pas logique. Avec L'Outillerie, on peut partager ses outils entre voisins, 
de la tondeuse au compresseur en passant par l'échelle et la machine à coudre.

## À qui s'adresse L'Outillerie?

L'Outillerie s'adresse à toi! Toi, qui a besoin d'une grande échelle pour nettoyer 
tes goutières. Toi, qui a besoin d'un souffleur à feuilles une seule fois par automne.
Toi, qui doit ajuster un bord de pantalon, mais n'a pas de machine à coudre. Toi,
qui doit couper des 2x4 à 45 degrés, mais n'as pas de scie à onglet.


## Notre vision

Le partage d'outils entre voisine n'a pas seulement des avantages financiers. Ce 
système de partage est également une solution au sur-enconbrement de nos domiciles 
et également un geste concret pour contrer la surconsommation.



## Développement

Prérequis : [uv](https://docs.astral.sh/uv/) et Docker Compose. La base est PostgreSQL 17
([ADR 0002](docs/decisions/0002-postgresql-sqlalchemy-et-alembic.md)), lancée par Docker Compose.

```sh
cp .env.example .env              # valeurs de dev, à adapter au besoin
docker compose up -d db           # Postgres sur localhost:5430, données dans ./data/postgres
cd application
uv sync
uv run flask db upgrade           # applique les migrations Alembic
uv run main.py                    # app sur :5000
```

Ou tout dans Docker : `docker compose up --build` (app sur :8080, migrations appliquées au démarrage).

### Base existante

Le schéma vient uniquement des migrations Alembic. Après un `git pull`, `uv run flask db upgrade`
amène une base existante à la dernière révision.

Si `flask db upgrade` échoue avec `Can't locate revision` (révision supprimée d'une branche) ou
`relation "user" already exists` (base créée avant les migrations), la base n'est plus alignée
sur l'historique Alembic. Deux options :

* **Repartir à neuf** (données de dev perdues) :

  ```sh
  docker compose down
  rm -rf data/postgres              # ou le chemin de POSTGRES_DATA_PATH
  docker compose up -d db
  cd application && uv run flask db upgrade
  ```

* **Garder les données**, si le schéma correspond déjà au code : marquer la base à la dernière
  révision sans rien exécuter, puis vérifier qu'il ne reste aucun écart.

  ```sh
  cd application
  uv run flask db stamp --purge head
  uv run flask db check             # doit afficher « No new upgrade operations detected. »
  ```

  Si `flask db check` détecte des écarts, repartir à neuf.

### Tests

Les tests ont besoin d'un Postgres, comme dans la CI, et créent puis suppriment leurs tables :
ils utilisent une base à part, jamais celle de dev. Ils lisent `TEST_DATABASE_URL` et, à défaut,
la base de la CI (`localhost:5432`).

```sh
docker compose exec db createdb -U outillerie outillerie_test   # une seule fois
cd application
TEST_DATABASE_URL=postgresql+psycopg://outillerie:outillerie@localhost:5430/outillerie_test uv run pytest
```
