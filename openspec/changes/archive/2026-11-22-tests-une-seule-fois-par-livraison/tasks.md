## 1. Preuve d'un arbre déjà testé

- [x] 1.1 `deploiement/already_tested.py` : fonction pure `proves_tested` selon les quatre conditions du design, en réutilisant `REPOSITORY`, `REQUIRED_JOBS` et le client `GitHub` de `deployer.py` ; `main()` lit `GITHUB_SHA` et `GITHUB_TOKEN`, écrit `tested=true|false` dans `$GITHUB_OUTPUT`, journalise la raison, et sort `tested=false` sur toute erreur
- [x] 1.2 `deploiement/tests/test_already_tested.py` : un cas par scénario de la spec (arbre déjà testé, arbre différent, tête qui ne contient pas le premier parent, commit à un parent, run absent, en échec, annulé, relancé avec succès, run d'un fork, job `tests` ou `specs` non réussi) et une erreur HTTP par un faux `opener` ; `uv run pytest ../deploiement/tests` passe

## 2. CI

- [x] 2.1 `.github/workflows/ci.yml` : job `already-tested` (permissions `actions: read`, `contents: read` ; `tested=false` sans appel hors `push`) ; `tests` et `specs` en `needs`, chaque étape après le checkout conditionnée par `needs.already-tested.outputs.tested != 'true'`, et les deux jobs en `if: ${{ !cancelled() }}` pour tourner même si `already-tested` échoue ; noms des jobs `tests` et `specs` inchangés
- [x] 2.2 `uv run ruff check . ../deploiement` et `uv run ruff format --check . ../deploiement` passent

## 3. Skill et ADR

- [x] 3.1 `.claude/skills/traiter-issue/SKILL.md` : étape 17 vérifie que le run `push` du commit de merge réussit avec `already-tested` à `tested=true` ; le paragraphe sur la CI exigée par GitHub décrit le ruleset (PR et checks `tests`, `specs` exigés, `strict: false`, contournement admin)

## 4. Fin

- [x] 4.1 `/verifier` rend « terminé »
