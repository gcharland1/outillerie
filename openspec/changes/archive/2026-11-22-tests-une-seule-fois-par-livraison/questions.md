# Questions — tests une seule fois par livraison

Issue traitée : #53 (Ne pas rejouer les tests sur main après le merge).

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 1 | Piste 1 (réutiliser le run de la PR) ou piste 2 (sans commit de merge) ? | La piste 2 n'a pas de forme propre : `--rebase` et `--squash` créent de nouveaux SHA ; un vrai fast-forward exige un push direct, possible seulement en contournement admin du ruleset, interdit par l'ADR 0024 et le skill. La piste 1 est vérifiée sur un cas réel : l'arbre de `fdfbebe` égale celui de `61a07d5`. | Sourced ruleset 25512319, ADR 0024:34-35, `git log --format=%T` ; Training pour `--rebase` | utilisateur |
| 2 | Forme de la piste 1 | Le run `push` garde les jobs `tests` et `specs`. Un premier pas vérifie : commit de merge à deux parents, arbre de `HEAD` = arbre de `HEAD^2`, `HEAD^2` contient `HEAD^1`, run `pull_request` réussi (dernière tentative, `tests` et `specs`) pour `head_sha = HEAD^2` venant du dépôt lui-même. Si oui, les pas suivants sont sautés **dans** le job, qui reste `success` ; sinon toute la suite tourne. Un job sauté rendrait le commit non vert. | Inferred du ruleset (`non_fast_forward`), `SKILL.md` gate 17, `deployer.py:51-60`, spec `livraison-continue` « Job sauté » | convention |
| 3 | Serveur | Inchangé avec la piste 1 (`is_green`, `push_runs`) : pas de réinstallation de `installer.sh` sur le serveur. | Sourced `deployer.py:51-59,145-148`, `deploiement/README.md:68-70` | convention |
| 4 | Le run de PR teste le merge virtuel | La condition « `HEAD^2` contient `HEAD^1` » plus l'égalité des arbres garantit que l'arbre testé est celui livré. | Inferred ; Training pour `refs/pull/<n>/merge` | convention |
| 5 | Push direct sur `main` sans PR | Pas de second parent ni de run de PR : toute la suite tourne. Le déclencheur `push` reste. | Inferred de la piste 1 | convention |
| 6 | Historique, `Closes` | Inchangés avec la piste 1. | Sourced grep, `export-transcript.sh` | convention |
| 7 | ADR | ADR 0026 qui complète 0017 sans le remplacer : sa lettre reste vraie (run `push`, jobs `tests` et `specs` réussis) ; il ajoute que ces jobs ne rejouent pas un arbre déjà testé par sa PR. Ne remplace pas 0024. | Sourced ADR 0017:32-34 | convention |
| 8 | Spec `livraison-continue` | Modifier « Tests du commit mergé » ; scénarios : arbre déjà testé, push sans PR, arbre différent, run de PR échoué, relancé ou d'un fork. « Commit déployable » inchangée. | Sourced spec `livraison-continue:10-46` | convention |
| 9 | Tests | Le pas de vérification est un script Python pur dans `deploiement/`, testé comme `test_deployer.py` (faux `opener`), lancé et linté par la CI. `ci.yml` gagne `actions: read`. | Sourced `test_deployer.py:22-43,262-272`, `ci.yml:10-11,58-59,74-76` | convention |
| 10 | Skill `/traiter-issue` | Étape 17 : vérifier que le run `push` de `main` réussit sans rejouer les tests. L'autre worktree (ADR 0025) ne modifie pas encore le skill. | Sourced `SKILL.md:207-220`, `git status` du worktree | convention |
| 11 | Phrase périmée « GitHub n'exige pas la CI pour merger » (ADR 0024:40, `SKILL.md:118`) | Le ruleset exige une PR et `tests`/`specs` depuis le 2026-11-20 (contournement admin possible, `strict: false`). Consigné dans le nouvel ADR ; `SKILL.md` corrigé. | Sourced ruleset 25512319 | utilisateur (ruleset voulu et durable ?) |
| 12 | Restreindre les méthodes de merge à `merge` | Un squash ou rebase manuel casse la comparaison (le run `push` rejoue alors tout : sûr, mais en double). Réglage GitHub hors dépôt. | Sourced ruleset `allowed_merge_methods` | utilisateur |
| 13 | PR de fork | La vérification exige `head_repository` = ce dépôt ; un run de fork ne compte jamais. | Sourced `gh api` (fork approval, permissions) ; Training | convention |
| 14 | `already-tested` en échec sur une PR | `tests` et `specs` seraient sautés, et un check requis sauté compte comme réussi : ils portent `if: ${{ !cancelled() }}` et une sortie absente vaut « rejouer ». | Training (checks requis sautés) ; trouvé à l'étape 7 | convention |

## Réponses de l'utilisateur

- **Q1 (2026-11-21)** : piste 1, réutiliser le run de la PR par comparaison d'arbre (forme de Q2) ; la piste 2 exige un contournement admin ou dégénère en piste 1.
- **Q11 et Q12 (2026-11-21)** : le ruleset du 2026-11-20 est voulu et durable ; le nouvel ADR le consigne et `SKILL.md` est corrigé. Restreindre `allowed_merge_methods` à `merge` est un réglage GitHub hors dépôt : fait par l'utilisateur, ou par l'agent seulement sur sa demande explicite ; pas une tâche du changement.
