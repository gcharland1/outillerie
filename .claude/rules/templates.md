---
paths:
  - "application/app/templates/**"
---

# Gabarits Jinja

- Chaque page étend `base.html` (`{% extends "base.html" %}`) dès qu'il existe.
- Tout texte affiché est en français.
- Pas de logique métier dans les gabarits : préparer les données dans la vue.
- Les formulaires POST affichent les messages `flash` et conservent les champs saisis en cas d'erreur.
