# Proposal

## Why

L'application ne connaît aujourd'hui que des comptes : rien ne décrit un outil à prêter ni un prêt
entre voisins (issue #15). Avant d'écrire les écrans, il faut un premier schéma de données et des
règles pour le faire évoluer, puisqu'il changera à chaque fonctionnalité. L'issue évoque un langage
de description d'interface (Protobuf, Avro, Thrift) pour des contrats entre services, mais
l'application est un monolithe Flask à rendu serveur (ADR 0001) sans API ni second service : le
schéma de persistance est le seul contrat, et c'est lui qu'il faut encadrer.

## What Changes

- Table `tool` : propriétaire, nom, description publique, état fonctionnel (`fonctionnel`,
  `a_reparer`, `hors_service`), notes privées réservées au propriétaire et indicateur `is_active`
  pour retirer un outil de la circulation sans le supprimer.
- Table `tool_photo` : au plus une photo par outil, stockée en `bytea` avec son type de contenu.
- Table `loan` : outil, emprunteur, dates de début et de fin, statut (`demande`, `accepte`,
  `refuse`, `annule`, `remis`, `rendu`). Le prêteur est le propriétaire de l'outil, sans colonne
  à part. Postgres refuse deux prêts `accepte` ou `remis` qui se chevauchent sur un même outil.
- Table `user` : courriel unique sans égard à la casse ; téléphone élargi à 20 caractères.
  L'inscription refuse un courriel déjà utilisé avec un message au lieu d'une erreur 500.
- Convention de nommage des contraintes SQLAlchemy, et renommage des contraintes existantes de
  `user` pour s'y conformer.
- Diagramme entité-relation Mermaid généré depuis les modèles par paracelsus dans `docs/`,
  vérifié à jour par `/verifier`.
- Trois ADR : schéma de persistance comme source de vérité et règles d'évolution ; photos en
  `bytea` avec un chemin de migration vers S3 ; paracelsus pour le diagramme.

## Capabilities

### New Capabilities
- `outils`: outils proposés au prêt — propriétaire, description publique, état fonctionnel,
  notes privées, photo.
- `prets`: prêts d'un outil à un voisin — dates, cycle de vie par statut, absence de
  chevauchement des prêts engagés.

### Modified Capabilities
- `authentification`: un courriel ne sert qu'à un seul compte, sans égard à la casse. La
  capacité est introduite par le changement `fermeture-de-session`, à archiver avant celui-ci.

## Impact

- Code : `application/app/extensions.py` (convention de nommage), `application/models/`
  (`user.py` modifié ; nouveaux modèles outil, photo, prêt), route `/register` dans
  `application/app/__init__.py`.
- Migrations : une révision Alembic, en partie écrite à la main (extension `btree_gist`,
  contrainte d'exclusion, index unique sur `lower(email)`, renommage des contraintes). Aucune base
  de production : la révision suppose une table `user` sans doublons de courriel.
- Tests : fixtures (`btree_gist` créé avant `db.create_all()`), tests pytest des contraintes et
  de l'inscription.
- Dépendance de développement : `paracelsus` (`uv add --dev`).
- Outillage : nouvelle étape de `/verifier` et de la CI (`paracelsus inject --check`) ; la CI
  applique aussi les migrations sur une base vide (`upgrade`, `downgrade`, `check`).
- ADR concernés : 0001 (monolithe à rendu serveur, d'où l'absence d'IDL), 0002 (Alembic seule
  source du schéma ; les nouveaux ADR le complètent sans le remplacer), 0003 (`uv add`).
- Nouveaux ADR via `/adr` : règles d'évolution du schéma, stockage des photos, diagramme.

**Hors périmètre**

- Téléversement, validation, service (`/tools/<id>/photo`) et module d'accès des photos : le
  changement crée la table et l'ADR qui les encadrent.
- Pages des outils, formulaires de prêt, transitions de statut et leurs règles (qui peut accepter,
  remettre, annuler ; un propriétaire n'emprunte pas son propre outil ; dates passées ; prêt d'un
  outil `hors_service`) : changements suivants.
- Notes privées jamais présentées à un autre que le propriétaire : exigence et test avec les pages
  d'outil.
- Commentaires et avis des emprunteurs.
- Normalisation du numéro de téléphone (format E.164) et champ téléphone à l'inscription.
- Plusieurs photos par outil.
- L'action de retrait d'un outil et ses règles (prêts `accepte` ou `remis` en cours, demandes
  refusées pour un outil retiré) : exigences et tests avec les pages d'outil et les prêts.
- Suppression de compte : bloquée par les clés étrangères tant qu'un compte possède un outil ou
  figure dans un prêt. Provisoire : le changement de suppression de compte décidera du sort des
  outils et des prêts.
- Tout IDL ou contrat d'API (Protobuf, Avro, OpenAPI) : à reconsidérer par un nouvel ADR à
  l'arrivée d'un second consommateur des données.
