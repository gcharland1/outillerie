# Questions — suppression de la colonne `username`

Issue traitée : #51 (Supprimer la colonne du nom d'utilisateur).

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 1 | La PR #52 (étape 2) est-elle déployée ? | Oui : `fdfbebe` porte le statut `deploiement` = `success` (2026-11-21T01:45:25Z), lu par `gh api …/commits/<sha>/statuses`, sans accès à la production. À relire juste avant le merge. | Sourced `gh api` ; `deploiement/deployer.py:153-162` | dépôt |
| 2 | Ordre et nom de la contrainte | `drop_constraint("uq_user_username")` puis `drop_column("username")` dans `batch_alter_table`, comme `916cc286d588`. Nom fixé par la convention et par `1f84fa116ada`. | Sourced `app/extensions.py:13`, `1f84fa116ada…py:55`, `tests/test_schema.py:12` | dépôt |
| 3 | `downgrade` : collision de `user<id>` ? | Non : la colonne recréée est vide. `add_column` nullable, `UPDATE "user" SET username = 'user' \|\| id` (comptes supprimés compris), `create_unique_constraint("uq_user_username")`. Pas de `NOT NULL` : l'état visé est celui de `916cc286d588`. | Sourced `43880597035b…py:24-43`, ADR 0020:38-40 ; issue #51 | dépôt |
| 4 | Filtre de `env.py` | `include_object` ne filtre que `username` et `uq_user_username` : retirer la fonction et ses deux branchements (l. 74 et 102). | Sourced `migrations/env.py:52-57,74,102` | dépôt |
| 5 | Références restantes à `username` | À changer : `env.py`, `test_schema.py:12` et `:95-105` (test inversé en preuve d'absence). À garder : `autocomplete="username"` (`login.html:14`, `sign_up.html:15`), tests d'absence `test_auth.py:43-48,99`, révisions. Historiques hors critère : ADR 0020, `docs/sessions/`, archives OpenSpec. | Sourced grep | convention |
| 6 | L'image précédente marche-t-elle sans la colonne ? | Oui : elle ne mappe plus `username`, et le retour arrière relance avec `SKIP_DB_UPGRADE=1`. | Sourced `models/user.py:7-21`, `deployer.py:283-291` | dépôt |
| 7 | `docs/schema.md` à jour ? | Oui, généré depuis les modèles ; `paracelsus inject --check` en CI. | Sourced `docs/schema.md:55-64` | dépôt |
| 8 | Test d'aller-retour | Sur le modèle de `test_account_deletion_columns_round_trip` : `downgrade("916cc286d588")`, vérifier `user<id>` (compte supprimé compris) et la contrainte, `upgrade()`, vérifier l'absence. La CI fait aussi `upgrade`/`downgrade base`/`upgrade`. | Sourced `tests/test_schema.py:55-66,108-130`, `ci.yml:61-68` | dépôt |
| 9 | Nouvel ADR ? | Non : *contract* prévu par ADR 0007 et 0020. | Sourced ADR 0020:38-40 | convention |
| 10 | `Closes` | `Closes #51` seulement ; #38 est déjà fermée. | Sourced archive `retrait-du-nom-d-utilisateur/questions.md:110` | dépôt |
| 11 | Même PR que #50 et #53, ou PR séparée ? | Deux révisions partant de `916cc286d588` feraient deux têtes : à chaîner si même branche. L'ADR 0025 (`proposed`, autre worktree) isole une révision qui retire du schéma. | Sourced `916cc286d588…py:13-14` ; ADR 0025 non commité | utilisateur |

## Réponses de l'utilisateur

- **Q11 (2026-11-21)** : deux PR à la suite, après un seul accord sur les trois specs : d'abord #51 seule, puis #50 et #53 ensemble. La révision de #50 part de celle de #51.
