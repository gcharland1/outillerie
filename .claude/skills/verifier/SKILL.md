---
name: verifier
description: Définition de « terminé » pour L'Outillerie — lint, format, tests, migrations et specs. Lancer avant de déclarer une tâche finie ou de proposer un commit, ou sur "/verifier".
allowed-tools: Bash(uv run:*), Bash(uv sync:*), Bash(openspec:*), Bash(git status:*), Bash(git diff:*), Bash(git ls-files:*), Bash(test:*), Bash(docker compose ps:*)
---

# Vérifier

Depuis `application/` :

1. `uv sync --locked`
2. `uv run ruff check .`
3. `uv run ruff format --check .`
4. `uv run pytest -q`
5. Si `application/migrations/` existe : `uv run flask db check` (aucune migration manquante). Requiert Postgres (`docker compose up -d db`) et `DATABASE_URL` ; si la base est indisponible, marquer l'étape « non vérifiée », pas « OK ».
6. `uv run paracelsus inject ../docs/schema.md --check` : le diagramme du schéma est à jour (ADR 0009).
7. `git ls-files migrations/versions | LC_ALL=C grep -v '^migrations/versions/[a-z0-9_]*\.py$'` doit être vide : noms de révision en ASCII, sans accent (`.claude/rules/migrations.md`).

Depuis la racine :

8. `openspec validate --all --no-interactive`
9. `git status --short` : signaler les fichiers non suivis inattendus.
10. Si `.claude/forbidden-terms.local` existe : `git grep -inEf .claude/forbidden-terms.local` sur les fichiers suivis et `git log main..HEAD --format=%B%n%ae | grep -iEf .claude/forbidden-terms.local` doivent être vides. Ne jamais citer les termes trouvés dans un fichier suivi.

Ne rien corriger pendant la vérification. Rendre un tableau :

| Étape | Résultat | Détail |
|-------|----------|--------|

Puis une ligne de verdict : **terminé** seulement si toutes les étapes sont OK ; sinon lister ce qui bloque.
