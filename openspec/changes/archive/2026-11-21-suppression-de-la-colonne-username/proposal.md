# Proposal

## Why

La passe *contract* du retrait du nom d'utilisateur (ADR 0020, ADR 0007) a été coupée en deux PR. La
PR #52 a retiré `username` du modèle `User` ; elle est déployée (statut `deploiement` = `success` sur
`fdfbebe`, question 1). Reste la seconde : supprimer de la base la colonne `user.username` et sa
contrainte `uq_user_username`, dernières traces du nom d'utilisateur, et retirer le filtre qui les
cachait à l'autogénération Alembic.

Les décisions et leur source sont dans [questions.md](questions.md). Décisions d'architecture :
ADR 0020 et ADR 0007 ; aucun nouvel ADR, ce changement applique la règle « supprimée après le
déploiement » de l'ADR 0020.

## What Changes

- Révision Alembic : `upgrade` supprime `uq_user_username` puis `user.username` ; `downgrade` recrée
  la colonne nullable, la remplit `user<id>` et recrée `uq_user_username`.
- `migrations/env.py` : le filtre `include_object` et ses deux branchements disparaissent ;
  `flask db check` est vide sans lui.
- `tests/test_schema.py` : `uq_user_username` sort des contraintes attendues ; le test de la colonne
  non mappée devient une preuve d'absence ; un test d'aller-retour couvre la révision.

Aucun comportement visible ne change : le change déclare `skip_specs: true`.

Hors périmètre : les mentions historiques de `username` (ADR 0020, `docs/sessions/`, archives
OpenSpec), qui restent ; le jeton HTML `autocomplete="username"` et les tests qui prouvent l'absence
du champ, gardés.

Closes #51.

## Capabilities

### New Capabilities

### Modified Capabilities

## Impact

`application/migrations/versions/` (nouvelle révision), `application/migrations/env.py`,
`application/tests/test_schema.py`. Livrée seule, dans une PR qui précède celle de #50 et #53
(question 11).
