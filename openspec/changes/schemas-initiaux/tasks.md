# Tasks

## 1. Décisions

- [x] 1.1 Écrire l'ADR « Règles d'évolution du schéma de persistance » via `/adr` (règles listées dans design.md, déclencheur d'un IDL, lien avec 0001 et 0002) ; vérifier qu'il apparaît dans l'index `docs/decisions/README.md`
- [x] 1.2 Écrire l'ADR « Photos des outils en `bytea` » via `/adr` (trois garde-fous, chemin *expand/backfill/contract* vers S3, déclencheurs, alternatives volume et S3) ; vérifier qu'il apparaît dans l'index
- [x] 1.3 Écrire l'ADR « Diagramme du schéma généré par paracelsus » via `/adr` (alternatives eralchemy et SchemaSpy) ; vérifier qu'il apparaît dans l'index

## 2. Fondations du schéma

- [x] 2.1 Ajouter la convention de nommage à `SQLAlchemy(metadata=MetaData(naming_convention=...))` dans `app/extensions.py` ; vérifier que `uv run pytest` passe toujours et que `user` reçoit `pk_user` et `uq_user_username` dans la base de test
- [x] 2.2 Créer `btree_gist` dans la fixture `mock_app` avant `db.create_all()` ; vérifier que `uv run pytest` passe toujours

## 3. Comptes : courriel unique et téléphone

- [x] 3.1 Modèle `User` : `phone` en `String(20)` et index unique `uq_user_email_lower` sur `lower(email)` ; vérifier par un test pytest que deux comptes `alice@example.com` et `Alice@Example.com` lèvent `IntegrityError`, et qu'un numéro de 20 caractères est conservé
- [x] 3.2 `/register` : refuser un courriel déjà utilisé sans égard à la casse avec le `flash` « Le courriel est déjà utilisé » ; vérifier par des tests pytest le scénario « Courriel déjà utilisé » de la spec `authentification` (aucun compte créé, message affiché)

## 4. Outils et photos

- [x] 4.1 Créer le modèle `Tool` et l'énumération `ToolCondition` (`StrEnum`, `VARCHAR` + `CHECK`, défauts Python et serveur) selon design.md ; vérifier par des tests pytest les scénarios des exigences « Outil rattaché à un propriétaire » et « État fonctionnel de l'outil », dont un `INSERT` SQL direct avec l'état `neuf` refusé par la base
- [x] 4.2 Ajouter `private_notes` (nullable) et `is_active` (NOT NULL, défauts Python et serveur `true`) ; vérifier par des tests pytest qu'un outil sans notes est conservé, et les scénarios « Nouvel outil en circulation » et « Outil retiré conservé »
- [x] 4.3 Créer le modèle `ToolPhoto` (PK `tool_id`, `ON DELETE CASCADE`) et la relation `Tool.photo` à chargement différé ; vérifier par des tests pytest les scénarios « Photo enregistrée », « Seconde photo refusée » et « Suppression de l'outil », et que charger un outil n'émet aucune requête sur `tool_photo`

## 5. Prêts

- [x] 5.1 Créer le modèle `Loan` et l'énumération `LoanStatus`, avec `ck_loan_end_after_start` et la propriété `lender` (propriétaire de l'outil) ; vérifier par des tests pytest les exigences « Prêt d'un outil à un emprunteur », « Dates du prêt » et « Statut du prêt », dont un `INSERT` SQL direct avec le statut `en_cours` refusé
- [x] 5.2 Ajouter la contrainte d'exclusion `excl_loan_tool_dates` (`ExcludeConstraint`, GiST, `WHERE status IN ('accepte', 'remis')`) ; vérifier par des tests pytest les six scénarios de « Aucun chevauchement des prêts engagés », dont l'acceptation d'une demande qui chevauche
- [x] 5.3 Vérifier par des tests pytest les scénarios de « Historique des prêts conservé » (suppression d'un outil prêté refusée)

## 6. Migration

- [x] 6.1 Générer la révision avec `uv run flask db migrate -m "Schémas initiaux : outils, photos et prêts"` puis la compléter à la main (`btree_gist`, exclusion, index sur `lower(email)`, `RENAME CONSTRAINT` de `user`, `CHECK` et `server_default`, `downgrade`) ; vérifier sur la base de développement `upgrade` → `downgrade a0989299c569` → `upgrade`, puis `uv run flask db check` sans écart
- [x] 6.2 Vérifier par `\d "user"`, `\d tool`, `\d tool_photo` et `\d loan` dans `psql` que chaque contrainte et index de la table des noms attendus de design.md existe sous ce nom exact, avec les défauts du design, après `flask db upgrade`
- [x] 6.3 Ajouter à `.github/workflows/ci.yml`, après les tests, l'étape `flask db upgrade`, `flask db downgrade base`, `flask db upgrade`, `flask db check` ; vérifier la commande en local sur une base vide

## 7. Diagramme

- [x] 7.1 `uv add --dev paracelsus`, configurer `[tool.paracelsus]` dans `pyproject.toml` (base `db.Model` ou alias `Base`, modules de modèles) et créer `docs/schema.md` avec ses balises ; vérifier que `uv run paracelsus inject ../docs/schema.md` produit un diagramme Mermaid des quatre tables et que `uv.lock` résout vers PyPI public
- [x] 7.2 Ajouter `paracelsus inject --check` au skill `/verifier` et à la CI ; vérifier que la commande échoue après l'ajout d'une colonne de test à un modèle, puis réussit une fois le diagramme régénéré

## 8. Corrections de relecture

- [x] 8.1 Photo : tester le remplacement par `tool.photo = ...` (scénario « Nouvelle photo ») et renommer le test d'ajout direct en « Jamais deux photos » ; vérifier que les tests passent
- [x] 8.2 `tests/test_schema.py` sur une base montée par `flask_migrate.upgrade()`, avec égalité stricte des noms ; `compare_server_default=True` sur `Migrate` ; vérifier que pytest échoue si un `CHECK` est retiré de la révision, et que `flask db check` reste vide
- [x] 8.3 CI : étape de migration avant les tests ; vérifier l'ordre dans `.github/workflows/ci.yml`
- [x] 8.4 `/register` compare `func.lower` des deux côtés ; vérifier que les tests d'inscription passent
- [x] 8.5 Test de retrait : vérifier aussi la photo, avec un emprunteur distinct du propriétaire ; vérifier que le test passe

## 9. Vérification

- [x] 9.1 Exécuter `/verifier` et obtenir « terminé » (lint, format, tests sur Postgres, `flask db check`, diagramme à jour, `openspec validate`)

## Workflow follow-up

- Archiver `fermeture-de-session` avant celui-ci : il crée la spec `authentification` que ce changement complète.
- Relecture par l'agent `relecteur` avant la PR, qui référence l'issue #15.
- À ajouter aux specs des changements des pages d'outil et des prêts, avec leurs tests : notes privées jamais présentées à un autre que le propriétaire ; aucune demande de prêt pour un outil retiré.
- Le changement de suppression de compte remplacera le blocage provisoire par les clés étrangères.
- Archiver le changement avec `/opsx:archive` une fois la PR mergée.
