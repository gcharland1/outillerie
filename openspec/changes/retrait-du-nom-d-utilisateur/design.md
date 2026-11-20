# Design

Décisions et sources : [questions.md](questions.md). Décisions d'architecture : ADR 0020 et
ADR 0007. Motivation : [proposal.md](proposal.md).

## Ordre de livraison

Dans la branche commune, les trois changements s'implémentent dans cet ordre : ce changement (#38),
puis `couleurs-des-boutons-et-liens` (#49), puis `modification-du-profil` (#46). La révision de #46 se
chaîne après celle-ci, et #46 modifie la macro et la capacité `interface` créées par #49.

## Révision *contract*

La révision suit la révision `43880597035b` (*expand*), générée par `uv run flask db migrate`
puis relue à la main (ADR 0007), fichier renommé en ASCII (`.claude/rules/migrations.md`).

- `upgrade` : `drop_constraint("uq_user_username")` explicite, puis `drop_column("username")`.
  Supprimer la colonne emporterait la contrainte dans Postgres, mais le nom explicite garde la
  révision lisible et symétrique au `downgrade` (question 7).
- `downgrade` : recrée `username VARCHAR(250)` nullable, l'état laissé par `43880597035b` ; la
  remplit avec `'user' || id` ; recrée `uq_user_username`. La règle de l'ADR 0020 (suffixer `_`
  tant qu'un ancien nom occupe la valeur) n'a pas d'effet ici : après la suppression, aucun ancien
  nom ne subsiste (question 4). Revenir ensuite sous `43880597035b` repasse par son propre
  `downgrade`, qui remet `NOT NULL`.

Ensuite `flask db check` est vide et `docs/schema.md` est régénéré par paracelsus depuis les
modèles (ADR 0009, `[tool.paracelsus]` de `pyproject.toml`) ; la CI le vérifie avec `--check`.

## Tests

- `test_schema.py` : `uq_user_username` retirée des contraintes attendues de `user`.
- `test_auth.py` : l'inscription ne vérifie plus `user.username`, seulement le prénom et le nom.
- Un test aller-retour de la révision : à la tête, un compte existe ; `downgrade` vers
  `43880597035b` lui donne `username = 'user<id>'` et recrée `uq_user_username` ; `upgrade`
  revient à la tête sans la colonne. La fixture `migrated_app` ne fait qu'aller-retour à vide.
- Gardés : les tests qui prouvent l'absence du champ (`test_register_form_asks_no_username`, le
  cas `username` de la connexion refusée, « Nom d'utilisateur » absent des contacts).

## Risques

- Retour arrière (ADR 0017) : si le déploiement de cette version échoue après la révision, le
  serveur revient à l'image précédente sans `downgrade` ; cette image mappe encore `username` et
  ne chargerait plus les comptes. Restauration par le `pg_dump` pris juste avant le déploiement.
  Risque prévu par l'ADR 0020 (colonne « supprimée après le déploiement ») ; la passe *expand*
  est déployée (question 2).

## Suivis

Hors des tâches : proposer dans le corps de la PR l'issue « Connexion - Limiter les essais de mot
de passe » (question 8), ouverte après accord de l'utilisateur sur son texte.
