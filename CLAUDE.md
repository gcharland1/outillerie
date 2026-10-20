# L'Outillerie

Site communautaire de partage d'outils entre voisins. Python 3.13, Flask (app factory), Jinja,
PostgreSQL 17, uv, Docker Compose. Le code vit dans `application/`.

## Commandes

Depuis `application/` :

```sh
uv sync                                   # dépendances (groupe dev inclus)
uv run main.py                            # app sur :5000
uv run pytest                             # tests
uv run ruff check . && uv run ruff format .
uv run flask db migrate -m "<message>"    # nouvelle révision Alembic
uv run flask db upgrade
```

Depuis la racine : `docker compose up --build` (app sur :8080, Postgres sur :5430).
Les variables à fournir sont dans `.env.example` ; ne jamais lire ni afficher `.env`.

## Workflow

1. Explorer : `/opsx:explore` pour réfléchir, lire `openspec/specs/` et les ADR.
2. Décision d'architecture (dépendance, schéma, structure, outil) : `/adr` **avant** de coder.
3. Spec : `/opsx:propose "<idée>"` crée `openspec/changes/<changement>/` ; la faire valider par l'utilisateur.
4. Implémenter : `/opsx:apply`, une tâche à la fois, tests compris.
5. Vérifier : `/verifier` doit rendre « terminé » ; relecture par l'agent `relecteur` avant une PR.
6. Archiver : `/opsx:archive` une fois le changement mergé ou validé.

Les ADR `accepted` dans `docs/decisions/` sont des contraintes : ne pas les contourner,
en écrire un nouveau qui les remplace. Index : @docs/decisions/README.md

## Conventions

- Contraintes du poste, non versionnées et prioritaires : `CLAUDE.local.md` (chargé automatiquement s'il existe).

- Commits en français, format `Thème - Description` (ex. `Login - Finaliser la création de compte`).
  Ajouter le trailer `Session: <8 premiers caractères du session_id>` ; l'ID est le nom du `.jsonl`
  le plus récent de `~/.claude/projects/<chemin du projet, / remplacés par ->/`.
- Identifiants et docstrings en anglais ; textes affichés, docs, specs et ADR en français.
- Ruff formate chaque fichier `.py` modifié (hook `PostToolUse`) ; ne pas lutter contre le formatage.
- Dépendance ajoutée ⇒ `uv add` (ou `uv add --dev`) et commit de `uv.lock`.
- Les transcripts de session s'exportent seuls dans `docs/sessions/` (hook `SessionEnd`).
