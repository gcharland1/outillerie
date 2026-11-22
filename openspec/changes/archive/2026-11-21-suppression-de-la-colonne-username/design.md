# Design

Décisions et sources : [questions.md](questions.md). Décisions d'architecture : ADR 0020 et
ADR 0007. Motivation : [proposal.md](proposal.md).

## Ordre de livraison

Ce changement se livre seul, dans une première PR ; `confirmation-du-courriel` (#50) et
`tests-une-seule-fois-par-livraison` (#53) suivent ensemble dans une seconde PR, dont la révision se
chaîne après celle-ci (question 11).

Précondition : la PR #52, qui retire `username` du modèle, est déployée (question 1). Elle se relit
juste avant le merge par le statut de commit `deploiement` de `fdfbebe`, sans accès à la
production.

## Révision

Générée par `uv run flask db migrate` une fois le filtre de `env.py` retiré, puis relue et renommée en
ASCII (`.claude/rules/migrations.md`). Elle part de `916cc286d588`.

- `upgrade` : dans `batch_alter_table("user")`, `drop_constraint("uq_user_username", type_="unique")`
  puis `drop_column("username")`.
- `downgrade` : `add_column` `VARCHAR(250)` nullable, `UPDATE "user" SET username = 'user' || id`
  (comptes supprimés compris), puis `create_unique_constraint("uq_user_username", ["username"])`. La
  colonne recréée est vide : aucune collision possible (question 3). Pas de `NOT NULL` : l'état visé
  est celui de `916cc286d588`. Le nom de la contrainte doit rester exact, car le `downgrade` de
  `1f84fa116ada` le renomme plus bas dans la chaîne (`downgrade base` de la CI).

## Retour arrière

L'image précédente (PR #52 ou plus récente) ne mappe plus `username`, et un retour arrière redémarre
avec `SKIP_DB_UPGRADE=1` (ADR 0017) : elle tourne sans la colonne (question 6).

## Tests

- `test_schema.py` : `uq_user_username` sort de `EXPECTED_CONSTRAINT_NAMES` ; le test « colonne
  gardée mais non mappée » devient « la colonne `username` n'existe pas en base ».
- Aller-retour sur le modèle de `test_account_deletion_columns_round_trip` : avec un compte actif et
  un compte supprimé, `downgrade` à `916cc286d588`, vérifier `username = 'user' || id` et la
  contrainte, puis `upgrade` et vérifier l'absence de la colonne.
- La CI enchaîne aussi `upgrade`, `downgrade base`, `upgrade`, `check`.
