---
name: adr
description: Crée un ADR (MADR) numéroté dans docs/decisions/ et met l'index à jour. Utiliser quand une décision d'architecture est prise (dépendance, schéma, structure, outil, convention transverse) ou sur "/adr <titre>".
argument-hint: <titre de la décision>
allowed-tools: Read, Write, Edit, Glob, Bash(git log:*)
---

# Nouvel ADR

1. Lire `docs/decisions/README.md` (règles, index) et `docs/decisions/adr-template.md`.
2. Numéro = plus grand `NNNN` existant + 1, sur 4 chiffres. Nom de fichier : `NNNN-<titre-en-kebab-sans-accents>.md`.
3. Si `$ARGUMENTS` est vide ou si le contexte, les options ou la justification manquent, poser les questions à l'utilisateur. Ne rien inventer.
4. Copier le gabarit, `status: proposed`, `date:` du jour, rédiger en français : contexte, au moins deux options réellement considérées, décision et conséquences (bonnes **et** mauvaises).
5. Lier le changement OpenSpec ou l'ADR d'origine s'il y en a un.
6. Si l'ADR remplace un ADR existant : mettre le `status` de l'ancien à `superseded by NNNN` (seule modification permise sur un ADR accepté).
7. Ajouter la ligne dans le tableau d'index de `docs/decisions/README.md`.
8. Montrer l'ADR à l'utilisateur ; passer à `accepted` seulement sur son accord.
