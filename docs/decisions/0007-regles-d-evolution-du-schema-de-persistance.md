---
status: accepted
date: 2026-10-21
decision-makers: Gabriel Charland
---

# Règles d'évolution du schéma de persistance

## Contexte et problème

L'issue #15 demande un standard pour définir les schémas de données (Protobuf, Avro, Thrift) et
des règles pour les faire évoluer. L'application est un monolithe Flask à rendu serveur (0001),
sans API ni second service : aucune donnée ne circule entre services. Le schéma changera à chaque
fonctionnalité ; il faut des règles pour que chaque changement reste sûr. Complète 0002 sans le
remplacer. Changement OpenSpec : `openspec/changes/schemas-initiaux/`.

## Options considérées

* Modèles SQLAlchemy et révisions Alembic comme seul contrat, encadrés par des règles d'évolution
* Contrat d'API HTTP (OpenAPI, JSON Schema) à côté des modèles
* Langage de description d'interface (Protobuf, Avro, Thrift) comme source des schémas

## Décision

Option retenue : « modèles SQLAlchemy et révisions Alembic, avec des règles d'évolution »,
parce qu'un contrat d'API ou un IDL n'aurait aucun consommateur et dériverait des modèles qui
définissent réellement les données.

Règles :

* Toute modification passe par `flask db migrate`, relue et complétée à la main quand
  l'autogénération ne voit pas l'objet (renommage de contrainte, extension, `CHECK`) ;
  `flask db check` doit être vide ensuite.
* Une révision mergée sur `main` est immuable : on la corrige par une nouvelle révision.
* Un changement incompatible suit *expand/contract* : ajouter (colonne nullable, nouvelle table),
  migrer les données, puis retirer ou resserrer dans une révision suivante. Un renommage est un
  ajout, une copie et une suppression.
* Chaque révision a un `downgrade` qui fonctionne ; la CI applique `upgrade`, `downgrade base`
  et `upgrade` sur une base vide.
* Les valeurs énumérées sont des `VARCHAR` avec un `CHECK`, jamais un type `ENUM` natif de
  Postgres (difficile à modifier, changements de valeurs invisibles pour l'autogénération).
* Toute contrainte et tout index a un nom stable, donné par la convention de nommage de
  `app/extensions.py` ou explicitement quand elle ne s'applique pas.
* Une migration de données qui touche un système externe est une commande `flask`, pas une
  révision Alembic : elle n'est pas transactionnelle.
* Le diagramme `docs/schema.md` est régénéré avec chaque modification de modèle.
* Un IDL ou un contrat d'API sera choisi par un nouvel ADR à l'arrivée d'un second consommateur
  des données : API publique, application mobile, second service ou évènements.

### Conséquences

* Bon, parce qu'il n'y a qu'une définition des données, versionnée avec le code.
* Bon, parce que les contraintes nommées et le *downgrade* testé rendent chaque révision
  réversible et modifiable plus tard.
* Mauvais, parce qu'une révision demande souvent des retouches à la main que les tests, qui
  créent le schéma par `db.create_all()`, ne vérifient pas : seule l'étape de migration de la CI
  les attrape.
* Mauvais, parce qu'*expand/contract* coûte deux révisions là où une suffirait sans base de
  production.
