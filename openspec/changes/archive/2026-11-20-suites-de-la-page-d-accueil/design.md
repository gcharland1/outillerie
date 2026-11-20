# Design

## Couleurs des boutons

Choix de l'utilisateur (issue #44, « À décider ») : boutons positifs bleus et négatifs neutres
sur tout le site, règle consignée dans l'ADR 0019 et dans `.claude/rules/templates.md`.
`Button.style` vide donne un bouton neutre ; `_buttons.html` n'ajoute la classe que si le style
existe. Les liens qui ouvrent une confirmation de retrait ou d'annulation sont neutres ; le
bouton qui confirme sur cette page est bleu. Le rouge reste aux messages d'erreur et aux retards.

`site.css` redéfinit `--color-primary` en bleu (`#1a5fb4`, texte blanc lisible) : Chota 0.9.2 le
fixe à `#14854f`, un vert, et l'applique aux liens, aux boutons `primary` et à tout
`[type=submit]`. Une règle `[type="submit"]:not(.primary)` rend neutres les autres boutons d'envoi
(« Refuser », « Rechercher », « Me déconnecter »), que Chota remplissait. Les entrées du menu du
compte, gris foncé par `.nav a`, passent au bleu.

## Partiel des demandes de contact

`contacts/_requests.html` expose `received_requests(requests, origin=None)`, sur le modèle de
`loans/_buttons.html` ; `origin="home"` ajoute le champ caché qui ramène à l'accueil.

## Notes archivées

Les écarts relevés dans `2026-11-19-page-d-accueil` sont corrigés dans l'archive elle-même : ce
sont des notes, pas des specs. « Mes emprunts » et « Mes prêts » restent lues sans `LIMIT` et
triées en Python ; l'écart est noté (question 21) plutôt que corrigé.
