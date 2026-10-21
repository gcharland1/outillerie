# Sessions Claude

Transcripts des sessions Claude Code, exportés en Markdown à la fin de chaque session
par le hook `SessionEnd` (`.claude/hooks/export-transcript.sh`, via `claude-code-log`). Voir ADR 0005.

## Convention

* Fichier `AAAA-MM-JJ-<8 premiers caractères du session_id>.md`. Une session reprise réécrit son fichier d'origine.
* L'export tourne en arrière-plan : le fichier apparaît quelques secondes après la fin de la session.
* Les motifs de secrets connus (`PASSWORD=`, `SECRET…=`, `TOKEN=`, `user:pass@` dans une URL) sont
  masqués par `.claude/hooks/redact.sed`, puis chaque regex de `.claude/forbidden-terms.local`
  (non versionné, facultatif) est remplacée par `[masqué]`. Si un terme subsiste, le fichier va
  dans `docs/sessions/.local/` (ignoré par git). **Relire le fichier avant de le commiter.**

## Lier une session au travail

* Commit : trailer `Session: <session_id court>` dans le message.
* Changement OpenSpec : citer le fichier de session dans `proposal.md` ou `design.md`.
* ADR : citer la session dans « Contexte et problème » si la décision y a été prise.

## Exporter à la main

```sh
uvx claude-code-log ~/.claude/projects/<chemin du projet, / remplacés par ->/<session_id>.jsonl --format md --compact -o docs/sessions/<fichier>.md
```
