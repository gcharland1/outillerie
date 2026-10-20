---
status: accepted
date: 2026-10-20
decision-makers: Gabriel Charland
---

# Archiver les sessions Claude dans le dépôt

## Contexte et problème

Le raisonnement derrière un changement vit dans la session Claude qui l'a produit.
Les transcripts restent dans `~/.claude/projects/`, hors du dépôt, et finissent par disparaître.

## Options considérées

* Hook `SessionEnd` → `claude-code-log` en Markdown dans `docs/sessions/`, commité
* `claude-code-transcripts` en HTML, commité
* Transcripts locaux seulement, publiés à la main au besoin

## Décision

Option retenue : « Markdown commité via claude-code-log », parce que le Markdown se lit et se
compare dans une PR, et que le hook ne demande aucun geste manuel.

Les secrets connus (mots de passe, `FLASK_SECRET_KEY`, URL de connexion) sont masqués à l'export,
et Claude n'a pas le droit de lire `.env`.

### Conséquences

* Bon, parce que chaque commit peut citer sa session (trailer `Session:`).
* Mauvais, parce que le dépôt grossit, et que le masquage n'attrape que les motifs connus : relire avant de commiter.
