# Proposal

## Why

La passe *expand* de l'issue #38 (PR #47, révision `43880597035b`) a rendu `user.username`
nullable et plus aucun code ne le lit ni ne l'écrit ; elle est déployée. Il reste la passe
*contract* prévue par l'ADR 0020 et l'ADR 0007 : supprimer la colonne et `uq_user_username`,
condition de fermeture de l'issue.

Les décisions et leur source sont dans [questions.md](questions.md). Décisions d'architecture :
ADR 0020 et ADR 0007 ; aucun nouvel ADR, ce changement applique la règle « supprimée après le
déploiement » de l'ADR 0020.

## What Changes

- Schéma : une révision Alembic supprime la contrainte `uq_user_username`, puis la colonne
  `user.username` ; le modèle `User` n'a plus de colonne `username`.
- Tests et documentation suivent : `test_schema.py` n'attend plus `uq_user_username`,
  `test_auth.py` ne lit plus `user.username`, `docs/schema.md` est régénéré (ADR 0009), la règle
  des gabarits parle du nom complet dans le menu du compte.
- Gardés : le jeton HTML `autocomplete="username"` des champs courriel (destiné aux gestionnaires
  de mots de passe) et les tests qui prouvent l'absence du champ nom d'utilisateur.

Aucun comportement visible ne change : la passe *expand* a déjà retiré le nom d'utilisateur de
l'inscription, de la connexion et de l'affichage. Le change déclare donc `skip_specs: true` ; les
scénarios « Nom d'utilisateur déjà pris » et « Nom d'utilisateur refusé » de `authentification`
restent vrais tels quels.

Hors périmètre : la limitation des essais de mot de passe, suivi à proposer dans le corps de la PR
(l'issue promise par la PR #47 n'a jamais été ouverte).

Closes #38

## Capabilities

### New Capabilities

### Modified Capabilities

## Impact

`application/models/user.py`, une nouvelle révision dans `application/migrations/versions/`,
`tests/test_schema.py`, `tests/test_auth.py`, `docs/schema.md`, `.claude/rules/templates.md`.
Retour arrière après déploiement (ADR 0017) : voir le design.
