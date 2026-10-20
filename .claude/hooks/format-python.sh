#!/usr/bin/env bash
# PostToolUse (Edit|Write) : formate et corrige le fichier Python modifié avec ruff.
set -euo pipefail

file=$(jq -r '.tool_input.file_path // empty')
[[ "$file" == *.py && -f "$file" ]] || exit 0

app_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}/application"
[[ "$file" == "$app_dir"/* ]] || exit 0

cd "$app_dir"
uv run --quiet ruff format "$file"
# F401 non corrigé : un import ajouté avant son usage (édition suivante) serait supprimé.
uv run --quiet ruff check --fix --unfixable F401 --quiet "$file" || true
