# Questions — issue #38 (S'authentifier par courriel)

Passe *contract* de l'ADR 0020 ; la passe *expand* (révision `43880597035b`) est livrée par la PR #47.

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 1 | Références restantes à `username` hors migrations ? | `models/user.py:10`, `tests/test_schema.py:11` (`uq_user_username`), `tests/test_auth.py:40` ; `docs/schema.md:57` (généré) ; `.claude/rules/templates.md` (« nom d'utilisateur » du menu). Gardés : `autocomplete="username"` (jeton HTML des gestionnaires de mots de passe) et les tests qui prouvent l'absence du champ. | Sourced grep | convention |
| 2 | La passe *expand* est-elle déployée ? | Oui : statut `deploiement` = `success` sur `f6a385b`, 2026-11-20 18:55Z. | Sourced `gh api …/statuses` | dépôt |
| 3 | Retour arrière (ADR 0017) après la suppression ? | L'image précédente mappe encore `username` : un retour arrière sans downgrade casserait le chargement des comptes. Évité par la coupure en deux PR (question 9). | Sourced `0017:38-40,65-66`, `0020:38-40` | convention |
| 4 | Que fera le `downgrade` de la révision de suppression (PR suivante, question 9) ? | Recrée `username VARCHAR(250)` nullable, la remplit `user<id>` suffixé de `_` (règle de 0020, sans effet ici), recrée `uq_user_username`. | Sourced `0020:39-40`, `43880597035b…py:24-43`, `0007:42-43` | convention |
| 5 | Menu du compte en nom complet ? | Déjà fait. | Sourced `base.html:44` | dépôt |
| 6 | `Closes` ou `Refs` ? | `Closes #38` : l'utilisateur ferme l'issue avec cette PR malgré la coupure (question 9) ; la suppression de la colonne est suivie par l'issue #51, ouverte le 2026-11-20. | Utilisateur, 2026-11-20 | utilisateur |
| 7 | Contrainte `uq_user_username` ? | Gardée en base avec la colonne, exclue de l'autogénération (question 9) ; la révision de la PR suivante fera un `drop_constraint` explicite avant `drop_column`. | Sourced `1f84fa116ada…py:55` | convention |
| 8 | Issue de suivi « Limiter les essais de mot de passe » promise par la PR #47 ? | Jamais ouverte. Hors périmètre : suivi à proposer dans le corps de PR. | Sourced `gh issue list` | convention |
| 9 | Supprimer la colonne dans la même PR que son retrait du modèle ? | Non : coupure en deux PR. Le relecteur a constaté que l'image déployée sur `main` mappe encore `username` (`origin/main:application/models/user.py:10`) ; avec la révision de suppression dans cette PR, un retour arrière sans `downgrade` (ADR 0017) casserait tout chargement de `User`. Cette PR démappe seulement, la colonne et `uq_user_username` restent en base, ignorées par l'autogénération ; la révision de suppression suit après le déploiement. | Relecture, décision 2026-11-20 | utilisateur |
