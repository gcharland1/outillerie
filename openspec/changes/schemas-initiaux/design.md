# Design

## Context

Voir proposal.md pour la motivation. État actuel :

- `application/app/extensions.py` crée `db = SQLAlchemy()` sans convention de nommage : les
  contraintes de `user` portent les noms par défaut de Postgres (`user_pkey`, `user_username_key`).
- `application/models/user.py` : `email` sans contrainte d'unicité, `phone` en `String(11)`,
  trop court pour un numéro international (E.164 : jusqu'à 15 chiffres plus `+`).
- Une seule révision Alembic (`a0989299c569`, création de `user`). Aucune base de production.
- Les tests créent le schéma par `db.create_all()` (`tests/conftest.py`) ; la CI n'exécute aucune
  migration, donc rien ne vérifie aujourd'hui qu'une révision s'applique.
- `/register` vérifie l'unicité du nom d'utilisateur avant l'insertion, pas celle du courriel.

## Goals / Non-Goals

**Goals:**
- Garantir les règles des specs dans Postgres (contraintes), pas seulement dans le code Python :
  plusieurs écrans écriront ces tables plus tard.
- Une révision qui s'applique et se défait sur une base vide, vérifiée en CI.
- Un diagramme du schéma qui ne peut pas diverger des modèles.

**Non-Goals:**
- Passer les modèles à la syntaxe `Mapped[]` de SQLAlchemy 2 : on garde le style `db.Column` de
  `user.py`.
- Règles de transition entre statuts d'un prêt : seule la cohérence des données est garantie ici.

## Decisions

### Le schéma de persistance est le contrat ; pas d'IDL

Les modèles SQLAlchemy et les révisions Alembic restent la seule définition des données
(ADR 0002). Un IDL (Protobuf, Avro, Thrift) ou un contrat d'API (OpenAPI) n'aurait aucun
consommateur dans un monolithe à rendu serveur (ADR 0001) et dériverait des modèles.

Nouvel ADR « Règles d'évolution du schéma de persistance » (complète 0002 sans le remplacer) :

- Toute modification passe par `flask db migrate`, relue et complétée à la main quand
  l'autogénération ne voit pas l'objet (voir plus bas) ; `flask db check` doit être vide ensuite.
- Une révision mergée sur `main` est immuable : on la corrige par une nouvelle révision.
- Changement incompatible en *expand/contract* : ajouter (colonne nullable, nouvelle table),
  migrer les données, puis retirer ou resserrer dans une révision suivante. Un renommage est un
  ajout, une copie et une suppression.
- Chaque révision a un `downgrade` qui fonctionne.
- Valeurs énumérées en `VARCHAR` + `CHECK`, jamais en type `ENUM` natif.
- Toute contrainte a un nom stable, donné par la convention de nommage.
- Une migration de données qui touche un système externe (ex. copie vers S3) est une commande
  `flask`, pas une révision Alembic : elle n'est pas transactionnelle.
- Le diagramme `docs/schema.md` est régénéré avec chaque modification de modèle.
- Un IDL sera choisi par un nouvel ADR à l'arrivée d'un second consommateur des données (API
  publique, application mobile, second service, évènements).

### Convention de nommage des contraintes

`SQLAlchemy(metadata=MetaData(naming_convention=...))` avec les gabarits usuels : `pk_%(table_name)s`,
`fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s`, `uq_%(table_name)s_%(column_0_name)s`,
`ix_%(column_0_label)s`, `ck_%(table_name)s_%(constraint_name)s`. Sans noms stables, une révision
future ne peut pas supprimer une contrainte de façon portable, et Alembic ne peut pas nommer les
`CHECK` des énumérations. La révision renomme `user_pkey` en `pk_user` et `user_username_key` en
`uq_user_username` (`ALTER TABLE ... RENAME CONSTRAINT`) : c'est le moment le moins coûteux, sans
base de production. Le renommage est conditionnel : Alembic applique la convention en
rejouant `a0989299c569`, si bien qu'une base neuve reçoit déjà `pk_user` et `uq_user_username` ;
seules les bases créées avant ce changement portent les anciens noms.

Le gabarit `ck` exige un nom explicite (`name=`) : SQLAlchemy lève une erreur pour un `CHECK`
sans nom quand la convention contient `%(constraint_name)s`. Les objets que la convention ne couvre
pas (exclusion, index d'expression) sont nommés explicitement aussi. Noms attendus après la
révision :

| Table | Contraintes et index |
|---|---|
| `user` | `pk_user`, `uq_user_username`, `uq_user_email_lower` |
| `tool` | `pk_tool`, `fk_tool_owner_id_user`, `ix_tool_owner_id`, `ck_tool_tool_condition` |
| `tool_photo` | `pk_tool_photo`, `fk_tool_photo_tool_id_tool` |
| `loan` | `pk_loan`, `fk_loan_tool_id_tool`, `fk_loan_borrower_id_user`, `ix_loan_tool_id`, `ix_loan_borrower_id`, `ck_loan_loan_status`, `ck_loan_end_after_start`, `excl_loan_tool_dates` |

Alternative écartée : garder les noms par défaut de Postgres. Ils dépendent du moteur et
l'autogénération ne sait pas nommer un `CHECK` sans convention.

### Énumérations : `StrEnum` Python stocké en `VARCHAR` + `CHECK`

`ToolCondition` (`fonctionnel`, `a_reparer`, `hors_service`) et `LoanStatus` (`demande`, `accepte`,
`refuse`, `annule`, `remis`, `rendu`) sont des `enum.StrEnum`, mappés par
`db.Enum(..., name="tool_condition" | "loan_status", native_enum=False, create_constraint=True,
values_callable=...)` : la base stocke la
valeur (`a_reparer`), pas le nom du membre Python, et un `CHECK` nommé refuse le reste. La colonne
est un `VARCHAR(20)` plutôt que la longueur de la plus longue valeur : ajouter une valeur ne
modifie que le `CHECK`, pas le type. Défaut en
Python et côté serveur (`server_default`), pour qu'un `INSERT` SQL direct obtienne aussi
`fonctionnel` ou `demande`.

Alternative écartée : type `ENUM` natif de Postgres. Retirer ou renommer une valeur demande de
recréer le type, et l'autogénération d'Alembic ne détecte pas les changements de valeurs.

### `user` : courriel unique sans égard à la casse, téléphone élargi

Index unique `uq_user_email_lower` sur `lower(email)`, déclaré dans le modèle (`db.Index`).
Alembic 1.20 compare les index d'expression sur Postgres : l'autogénération devrait le produire, à
vérifier dans la révision. Le courriel reste
enregistré tel que saisi. `phone` passe à `String(20)`.

`/register` cherche un compte dont `lower(email)` égale le courriel soumis en minuscules, après la
vérification du nom d'utilisateur, et affiche « Le courriel est déjà utilisé » par `flash`.

Alternative écartée : extension `citext`. Elle change le type de la colonne pour un seul besoin
qu'un index d'expression couvre.

### `tool`

| Colonne | Type | Contraintes |
|---|---|---|
| `id` | `Integer` | PK |
| `owner_id` | `Integer` | FK `user.id`, NOT NULL, indexée |
| `name` | `String(250)` | NOT NULL |
| `description` | `Text` | NOT NULL |
| `condition` | `VARCHAR` + `CHECK` | NOT NULL, défaut `fonctionnel` |
| `private_notes` | `Text` | nullable |
| `is_active` | `Boolean` | NOT NULL, défaut `true` |
| `created_at` | `DateTime(timezone=True)` | NOT NULL, défaut `now()` |

`created_at` n'a pas été discuté : ajouté parce qu'il sert à trier les outils récents et coûte
plus cher à remplir après coup. Les clés étrangères n'ont pas d'`ON DELETE` (comportement
`NO ACTION`) : un compte qui possède un outil ou figure dans un prêt ne peut pas être supprimé.
Ce blocage est provisoire et volontairement absent des specs : un utilisateur doit pouvoir
supprimer son compte, et le changement qui ajoutera cette fonction décidera du sort de ses outils
et de ses prêts (retrait, anonymisation). Postgres n'indexe pas les clés étrangères de lui-même, d'où les index.

`is_active` retire un outil de la circulation sans le supprimer, ce que les clés étrangères des
prêts interdisent. Booléen choisi pour sa simplicité ; un horodatage `retired_at` dirait aussi
*quand*, et pourra le remplacer en *expand/contract*. L'état `condition` reste indépendant : un
outil `fonctionnel` peut être retiré et revenir sans perdre son état. Refuser une demande pour un
outil retiré est une règle applicative (un `CHECK` ne lit pas une autre table), portée par le
changement qui crée les demandes.

Le nom `private_notes` signale dans le code que la colonne ne doit pas être rendue à un autre que
le propriétaire ; l'exigence et son test viennent avec les pages d'outil.

### `tool_photo` : `bytea` dans une table à part

| Colonne | Type | Contraintes |
|---|---|---|
| `tool_id` | `Integer` | PK, FK `tool.id` `ON DELETE CASCADE` |
| `content` | `LargeBinary` (`bytea`) | NOT NULL |
| `content_type` | `String(100)` | NOT NULL |
| `created_at` | `DateTime(timezone=True)` | NOT NULL, défaut `now()` |

La clé primaire sur `tool_id` garantit au plus une photo par outil. Affecter `tool.photo` à un outil
qui en a une remplace l'ancienne (l'ORM émet un `UPDATE` de la même ligne) ; `created_at` garde la
date de la première photo. La relation `Tool.photo`
(`uselist=False`, `passive_deletes=True`) se charge à la demande : lire un outil ne lit jamais les
octets. Les formats acceptés et la taille maximale relèvent du téléversement, hors périmètre.

Nouvel ADR « Photos des outils en `bytea` » : une sauvegarde unique, suppression transactionnelle
(aucun fichier orphelin), aucun service ajouté. Il fixe trois garde-fous pour la suite — table
séparée, URL stable `/tools/<id>/photo` (jamais une URL de stockage dans un gabarit), un seul module
d'accès — et le chemin vers S3 :

1. *expand* : colonne `storage_key` nullable ; le module lit S3 si la clé existe, sinon `content` ;
   les nouvelles photos vont dans S3.
2. *backfill* : commande `flask` par lots, idempotente, qui copie chaque `content` et pose la clé.
3. *contract* : `content` supprimée, puis `VACUUM FULL` (ou `pg_repack`) pour rendre l'espace.

Déclencheurs : taille de la base, hébergement sans stockage Postgres adapté, besoin d'un CDN.

Alternatives écartées : fichiers sur un volume (sauvegarde séparée, fichiers orphelins possibles),
MinIO/S3 dès maintenant (service, dépendance et secrets en plus pour quelques centaines de Mo).

### `loan` et contrainte d'exclusion

| Colonne | Type | Contraintes |
|---|---|---|
| `id` | `Integer` | PK |
| `tool_id` | `Integer` | FK `tool.id`, NOT NULL, indexée |
| `borrower_id` | `Integer` | FK `user.id`, NOT NULL, indexée |
| `start_date`, `end_date` | `Date` | NOT NULL, `ck_loan_end_after_start` : `end_date >= start_date` |
| `status` | `VARCHAR` + `CHECK` | NOT NULL, défaut `demande` |
| `created_at` | `DateTime(timezone=True)` | NOT NULL, défaut `now()` |

Pas de `lender_id` : le prêteur est `tool.owner_id`, une seule source. Le jour où un outil peut
changer de propriétaire, une colonne figée s'ajoute en *expand/backfill*. Les clés étrangères sans
`ON DELETE` empêchent de supprimer un outil qui figure dans un prêt (spec `prets`) ; pour les
comptes, voir le blocage provisoire décrit sous `tool`.

Le non-chevauchement est une contrainte d'exclusion Postgres, déclarée dans le modèle avec
`ExcludeConstraint` :

```sql
CONSTRAINT excl_loan_tool_dates EXCLUDE USING gist
  (tool_id WITH =, daterange(start_date, end_date, '[]') WITH &&)
  WHERE (status IN ('accepte', 'remis'))
```

Elle exige l'extension `btree_gist` (égalité sur un entier dans un index GiST). Postgres la vérifie
à chaque `INSERT` et `UPDATE`, y compris le passage d'une `demande` à `accepte`, sans condition de
course entre deux acceptations simultanées. La borne `'[]'` inclut le jour de fin : un outil rendu
le 5 ne peut être promis à un autre que le 6.

Alternative écartée : vérification dans l'application avant l'acceptation. Deux requêtes
simultanées passeraient toutes les deux.

### Révision Alembic : autogénérée puis complétée

Une seule révision, `flask db migrate -m "Schémas initiaux : outils, photos et prêts"`, puis à la
main :

- `CREATE EXTENSION IF NOT EXISTS btree_gist` en tête de l'`upgrade` ; le `downgrade` ne la
  supprime pas (d'autres objets pourraient en dépendre).
- Les deux `RENAME CONSTRAINT` de `user`, que l'autogénération ne détecte pas ; la contrainte
  d'exclusion et l'index `uq_user_email_lower` si elle ne les a pas produits.
- Comparer chaque nom de la révision à la table des noms attendus.
- Vérifier que les `CHECK` des énumérations, `ck_loan_end_after_start` et les `server_default`
  figurent dans la révision : l'autogénération ne compare pas les `CHECK`, donc `flask db check`
  ne signalerait pas leur absence.

La CI gagne une étape après les tests : `flask db upgrade`, `flask db downgrade base`,
`flask db upgrade`, `flask db check`, sur sa base Postgres vide.

### Tests : `btree_gist` avant `db.create_all()`, noms vérifiés sur la base migrée

La fixture `mock_app` exécute `CREATE EXTENSION IF NOT EXISTS btree_gist` avant `db.create_all()`.
Les tests des contraintes passent par l'ORM et attendent `IntegrityError` ; pour les énumérations,
un `INSERT` SQL direct prouve que le `CHECK` existe en base et pas seulement la validation Python.

Ces tests ne voient que ce que déclarent les modèles. `tests/test_schema.py` monte donc sa base par
les révisions Alembic (`flask_migrate.upgrade()`) et exige, table par table, exactement les noms de
contraintes et d'index attendus : un `CHECK`, une exclusion ou un index oublié dans une révision,
ou une contrainte en double sous un nom par défaut, fait échouer pytest. `Migrate` reçoit
`compare_server_default=True`, pour que `flask db check` compare aussi les valeurs par défaut.

### Diagramme : paracelsus vers `docs/schema.md`

`paracelsus` en dépendance de développement, configuré dans `[tool.paracelsus]` de `pyproject.toml`
(base `db.Model`, modules de modèles importés). `paracelsus inject ../docs/schema.md` écrit le
diagramme Mermaid entre ses balises ; `--check` échoue s'il n'est plus à jour. L'étape s'ajoute à
`/verifier` et à la CI. Si paracelsus n'accepte pas `db.Model` comme base, `models/__init__.py`
expose un alias `Base = db.Model`.

Nouvel ADR « Diagramme du schéma généré par paracelsus ». Alternatives écartées : eralchemy
(images binaires, Graphviz requis), SchemaSpy ou l'ERD de DBeaver (lisent la base migrée, pas les
modèles).

## Risks / Trade-offs

- [Une contrainte écrite à la main manque dans la révision ou dans le modèle, et les tests passent
  quand même parce qu'ils utilisent `db.create_all()`] → `test_schema.py` compare les noms sur la
  base migrée, `flask db check` compare les défauts ; reste non comparé le texte d'un `CHECK` (une
  condition fausse sous le bon nom passerait).
- [Un hébergeur géré interdit `btree_gist`] → l'extension est disponible chez les principaux
  hébergeurs Postgres ; sinon, un nouvel ADR remplace l'exclusion par un verrou applicatif.
- [Deux inscriptions simultanées avec le même courriel] → la seconde lève `IntegrityError` (erreur
  500) au lieu du message ; l'index garantit tout de même l'unicité. Accepté.
- [La base grossit avec les photos] → chemin vers S3 décrit dans l'ADR ; redimensionner au
  téléversement.
- [Des doublons de courriel existent dans une base de développement] → la révision échoue à la
  création de l'index ; supprimer les doublons à la main, aucune base de production n'existant.

## Migration Plan

`flask db upgrade` sur les bases de développement. Retour arrière : `flask db downgrade` vers
`a0989299c569` supprime `loan`, `tool_photo` et `tool`, l'index du courriel, remet `phone` en
`String(11)` (échoue si un numéro plus long a été saisi entre-temps) et les anciens noms de
contraintes.
