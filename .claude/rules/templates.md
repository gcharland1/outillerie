---
paths:
  - "application/app/templates/**"
---

# Gabarits Jinja

- Chaque page étend `base.html` (`{% extends "base.html" %}`) dès qu'il existe.
- Tout texte affiché est en français.
- Pas de logique métier dans les gabarits : préparer les données dans la vue.
- Les formulaires POST affichent les messages `flash` et conservent les champs saisis en cas d'erreur.

## Interface

Les styles vivent dans `app/static/site.css`, chargé après Chota ; pas d'attribut `style=` dans les gabarits.

- Un bouton a un contour et un fond (`class="button"`, et `primary`, `error`…) ; jamais `button outline` ni un texte sur fond transparent.
- Dans un menu ou un contexte d'action, une action est un bouton, même quand elle mène à une page (`<a class="button">`). Un lien nu ne sert qu'au fil d'un texte, et dans le menu du compte (ci-dessous), dont chaque entrée est un simple texte.
- Une action dangereuse (retrait, suppression, effacement) est rouge : `class="button error"`.
- Deux éléments ne se touchent jamais : boutons groupés dans `<div class="actions">`, espacement `var(--gap)` ; une page commence sous la barre de navigation avec un écart.
- La barre de navigation reste délimitée (`.site-header`).
- Les pages personnelles (« Gérer mes outils », plus tard « Mon profil », « Préférences ») vont dans le menu du compte, ouvert en cliquant sur le nom d'utilisateur (`<details class="account-menu">`, sans JavaScript, ADR 0001). Ses entrées sont de simples liens texte, pas des boutons ; « Me déconnecter » reste visible à côté, en bouton.
