#!/usr/bin/env bash
# SessionEnd: exporte le transcript de la session en Markdown dans docs/sessions/.
# Détaché, car la conversion (~7 s) dépasse le budget SessionEnd.
set -euo pipefail

script_dir=$(cd "$(dirname "$0")" && pwd)

input=$(cat)
transcript=$(jq -r '.transcript_path // empty' <<<"$input")
session_id=$(jq -r '.session_id // empty' <<<"$input")
[[ -f "$transcript" && -n "$session_id" ]] || exit 0

project_dir=${CLAUDE_PROJECT_DIR:-$(pwd)}
out_dir="$project_dir/docs/sessions"
short_id=${session_id:0:8}
mkdir -p "$out_dir"

# Une session reprise un autre jour garde son fichier d'origine.
existing=$(compgen -G "$out_dir/*-$short_id.md" | head -n1 || true)
target=${existing:-"$out_dir/$(date +%F)-$short_id.md"}

(
  tmp=$(mktemp --suffix=.md)
  trap 'rm -f "$tmp"' EXIT
  uvx --quiet claude-code-log "$transcript" --format md --compact \
    --image-export-mode placeholder -o "$tmp" >/dev/null 2>&1 || exit 0
  terms="$project_dir/.claude/forbidden-terms.local"
  if [[ -s "$terms" ]] && grep -qiEf "$terms" "$tmp"; then
    mkdir -p "$out_dir/.local"
    target="$out_dir/.local/$(basename "$target")"
  fi
  sed -E -f "$script_dir/redact.sed" "$tmp" > "$target"
) </dev/null >/dev/null 2>&1 &
disown
