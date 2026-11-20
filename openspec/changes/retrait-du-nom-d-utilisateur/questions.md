# Questions — issue #38 (S'authentifier par courriel)

Passe *contract* de l'ADR 0020 ; la passe *expand* (révision `43880597035b`) est livrée par la PR #47.

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 1 | Références restantes à `username` hors migrations ? | `models/user.py:10`, `tests/test_schema.py:11` (`uq_user_username`), `tests/test_auth.py:40` ; `docs/schema.md:57` (généré) ; `.claude/rules/templates.md` (« nom d'utilisateur » du menu). Gardés : `autocomplete="username"` (jeton HTML des gestionnaires de mots de passe) et les tests qui prouvent l'absence du champ. | Sourced grep | convention |
| 2 | La passe *expand* est-elle déployée ? | Oui : statut `deploiement` = `success` sur `f6a385b`, 2026-11-20 18:55Z. | Sourced `gh api …/statuses` | dépôt |
| 3 | Retour arrière (ADR 0017) après la suppression ? | L'image précédente mappe encore `username` : un retour arrière sans downgrade casserait le chargement des comptes ; restauration par le `pg_dump` pris avant le déploiement. Risque prévu par 0020 (« supprimée après le déploiement »), consigné dans le design. | Sourced `0017:38-40,65-66`, `0020:38-40` | convention |
| 4 | Que fait le `downgrade` ? | Recrée `username VARCHAR(250)` nullable, la remplit `user<id>` suffixé de `_` (règle de 0020, sans effet ici), recrée `uq_user_username`. | Sourced `0020:39-40`, `43880597035b…py:24-43`, `0007:42-43` | convention |
| 5 | Menu du compte en nom complet ? | Déjà fait. | Sourced `base.html:44` | dépôt |
| 6 | `Closes` ou `Refs` ? | `Closes #38` : la passe *contract* était la condition de fermeture. | Sourced `archive/2026-11-20-authentification-par-courriel/design.md:20` | dépôt |
| 7 | Contrainte `uq_user_username` ? | `drop_constraint` explicite avant `drop_column` ; retirée de `test_schema.py`. | Sourced `1f84fa116ada…py:55` | convention |
| 8 | Issue de suivi « Limiter les essais de mot de passe » promise par la PR #47 ? | Jamais ouverte. Hors périmètre : suivi à proposer dans le corps de PR. | Sourced `gh issue list` | convention |
