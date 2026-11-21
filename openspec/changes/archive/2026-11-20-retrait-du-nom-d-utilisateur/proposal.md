# Proposal

## Why

La passe *expand* de l'issue #38 (PR #47, révision `43880597035b`) a rendu `user.username`
nullable et plus aucun code ne le lit ni ne l'écrit ; elle est déployée. Il reste la passe
*contract* prévue par l'ADR 0020 et l'ADR 0007, coupée en deux PR (question 9) : celle-ci retire
`username` du modèle `User` ; la suppression de la colonne et de `uq_user_username` suit dans une PR
suivante, une fois celle-ci déployée. Ainsi l'image précédente tourne toujours sur le schéma de
cette version et un retour arrière sans `downgrade` (ADR 0017) reste sûr.

Les décisions et leur source sont dans [questions.md](questions.md). Décisions d'architecture :
ADR 0020 et ADR 0007 ; aucun nouvel ADR, ce changement applique la règle « supprimée après le
déploiement » de l'ADR 0020.

## What Changes

- Modèle : `User` n'a plus de colonne `username`. Aucune révision : la colonne et
  `uq_user_username` restent en base, exclues de l'autogénération par `migrations/env.py`.
- Tests et documentation suivent : `test_schema.py` vérifie que la colonne existe encore en base
  sans être mappée, `test_auth.py` ne lit plus `user.username`, `docs/schema.md` est régénéré depuis
  les modèles (ADR 0009), la règle des gabarits parle du nom complet dans le menu du compte.
- Gardés : le jeton HTML `autocomplete="username"` des champs courriel (destiné aux gestionnaires
  de mots de passe) et les tests qui prouvent l'absence du champ nom d'utilisateur.

Aucun comportement visible ne change : la passe *expand* a déjà retiré le nom d'utilisateur de
l'inscription, de la connexion et de l'affichage. Le change déclare donc `skip_specs: true` ; les
scénarios « Nom d'utilisateur déjà pris » et « Nom d'utilisateur refusé » de `authentification`
restent vrais tels quels.

Hors périmètre : la révision qui supprime la colonne et `uq_user_username` et retire le filtre de
`env.py`, après le déploiement de celle-ci, suivie par l'issue #51 ; en suivi à proposer dans le corps
de la PR, la limitation des essais de mot de passe (l'issue promise par la PR #47 n'a jamais été
ouverte).

Closes #38 : l'utilisateur ferme l'issue avec cette PR, la suppression de la colonne étant suivie par l'issue #51.

## Capabilities

### New Capabilities

### Modified Capabilities

## Impact

`application/models/user.py`, `application/migrations/env.py`, `tests/test_schema.py`,
`tests/test_auth.py`, `docs/schema.md`, `.claude/rules/templates.md`. Ordre des deux PR : voir le
design.
