---
paths:
  - "application/app/templates/**"
---

# Gabarits Jinja

- Chaque page étend `base.html` (`{% extends "base.html" %}`) dès qu'il existe.
- Tout texte affiché est en français.
- Aucun texte affiché n'emploie « voisin » : on parle d'utilisateur, ou de contact une fois la demande acceptée.
- Pas de logique métier dans les gabarits : préparer les données dans la vue.
- Les formulaires POST affichent les messages `flash` et conservent les champs saisis en cas d'erreur.

## Interface

Les styles vivent dans `app/static/site.css`, chargé après Chota ; pas d'attribut `style=` dans les gabarits.

- Un bouton a un contour et un fond (`class="button"`, ou `button primary`) ; jamais `button outline` ni un texte sur fond transparent.
- Couleurs (ADR 0022) : avancer en bleu (`button primary`, au plus un par groupe d'actions ou par formulaire) ; détruire (retirer, annuler, supprimer) en rouge (`button error`), y compris le bouton qui ouvre la confirmation et celui qui la confirme ; reculer, quitter, dire non et tout bouton désactivé en gris (`button`). Jamais `success` sur un bouton : le vert signale un état. Un lien, menu du compte compris, a le bleu des boutons (`--color-primary`).
- Le nom complet d'un utilisateur passe par la macro `user_name` (`_user_name.html`, importée `with context`).
- Dans un menu ou un contexte d'action, une action est un bouton, même quand elle mène à une page (`<a class="button">`). Un lien nu ne sert qu'au fil d'un texte, et dans le menu du compte (ci-dessous), dont chaque entrée est un simple texte.
- Une action dangereuse (retrait, suppression, effacement) passe par une page de confirmation.
- Deux éléments ne se touchent jamais : boutons groupés dans `<div class="actions">`, espacement `var(--gap)` ; une page commence sous la barre de navigation avec un écart.
- La barre de navigation reste délimitée (`.site-header`).
- Les pages de l'utilisateur connecté (« Gérer mes outils », « Mes contacts », « Mes prêts », « Mon profil », « Trouver un outil », plus tard « Préférences ») vont dans le menu du compte, ouvert en cliquant sur le nom complet (`<details class="account-menu">`, sans JavaScript, ADR 0001). Ses entrées sont de simples liens texte bleus, pas des boutons ; « Me déconnecter » reste visible à côté, en bouton.
