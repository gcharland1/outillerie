# Design

Décisions et sources : [questions.md](questions.md). Décisions d'architecture : ADR 0020 et
ADR 0007. Motivation : [proposal.md](proposal.md).

## Ordre de livraison

Dans la branche commune, les trois changements s'implémentent dans cet ordre : ce changement (#38),
puis `couleurs-des-boutons-et-liens` (#49), puis `modification-du-profil` (#46). La révision de #46 se
chaîne après `43880597035b`, et #46 modifie la macro et la capacité `interface` créées par #49.

La passe *contract* se livre en deux PR (question 9) :

1. Cette PR : `User` ne mappe plus `username` ; aucune révision ne touche la colonne.
2. PR suivante, après le déploiement de celle-ci : une révision supprime `uq_user_username` puis
   `user.username`, et retire le filtre de `env.py` ; elle est suivie par l'issue #51, et cette PR-ci
   ferme #38 (décision de l'utilisateur).

Entre les deux, l'image précédente (qui mappe `username`) et celle-ci tournent toutes deux sur le
même schéma : un retour arrière sans `downgrade` (ADR 0017) ne casse rien.

## Colonne gardée, exclue de l'autogénération

`migrations/env.py` passe un `include_object` à `context.configure` (modes online et offline) qui
écarte la colonne `user.username` et la contrainte `uq_user_username` ; sans lui, `flask db check`
détecterait leur suppression. La colonne est nullable depuis `43880597035b` : un `User` inséré par
l'ORM la laisse à `NULL`, ce que `uq_user_username` accepte.

`docs/schema.md` est régénéré par paracelsus depuis les modèles (ADR 0009, `[tool.paracelsus]` de
`pyproject.toml`) : le diagramme n'a plus `username`, alors que la base la garde jusqu'à la PR
suivante. La CI le vérifie avec `--check`.

Révision de la PR suivante (question 4) : `upgrade` = `drop_constraint("uq_user_username")` puis
`drop_column("username")` ; `downgrade` = colonne `VARCHAR(250)` nullable, remplie `'user' || id`,
puis `uq_user_username` recréée.

## Tests

- `test_schema.py` : `uq_user_username` reste dans les contraintes attendues de `user` ; un test
  vérifie que la colonne `username` existe en base, que `User` ne la mappe pas et qu'un `User`
  s'insère par l'ORM (colonne à `NULL`).
- `test_auth.py` : l'inscription ne vérifie plus `user.username`, seulement le prénom et le nom.
- Gardés : les tests qui prouvent l'absence du champ (`test_register_form_asks_no_username`, le
  cas `username` de la connexion refusée, « Nom d'utilisateur » absent des contacts).

## Suivis

Hors des tâches, à proposer dans le corps de la PR : la révision de suppression de la colonne
(ci-dessus), après le déploiement ; l'issue « Connexion - Limiter les essais de mot de passe »
(question 8), ouverte après accord de l'utilisateur sur son texte.
