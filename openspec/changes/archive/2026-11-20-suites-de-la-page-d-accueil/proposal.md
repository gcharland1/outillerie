# Proposal

## Why

La relecture de la PR #43 (page d'accueil, tri de « Trouver un outil ») a laissé des suites dans
l'issue #44 : des scénarios sans test, des tests qui ne peuvent pas échouer, des notes archivées
qui ne décrivent plus le code, et deux jeux de couleurs pour « Accepter » / « Refuser ».

## What Changes

- Une règle de couleurs pour tous les boutons du site (ADR 0019, `proposed`) : action positive en
  bleu, action négative, navigation et outils de page en neutre ; sur une page de confirmation, le
  bouton qui confirme est bleu. Plus aucun bouton rouge ni vert. Le bleu remplace le vert primaire
  de Chota, et les liens, menu du compte compris, prennent ce bleu. « Accepter » / « Refuser » sont
  donc bleu / neutre pour les contacts comme pour les prêts ; « Se connecter » et « Créer mon
  compte » deviennent bleus.
- Les demandes de contact reçues de l'accueil et de « Mes contacts » partagent un partiel.
- Tests ajoutés : « Remise en circulation » et « Sans script » de l'accueil, message de succès
  d'« Acceptation depuis l'accueil », lien « Annuler le prêt » de l'accueil sans `origin=home`,
  ce que voit celui qui refuse une demande de contact, ordre « Pertinence » d'un tri inconnu.
- Notes de l'archive `2026-11-19-page-d-accueil` alignées sur le code (`loans.dashboard(user_id)`,
  `<label>` « Trier par », écart des lectures sans `LIMIT`).

## Capabilities

### New Capabilities

### Modified Capabilities
- `demandes-d-emprunt`: couleurs des boutons dans « Ordre et couleurs de « Mes prêts » ».

## Impact

ADR 0019, `.claude/rules/templates.md` (règle « Interface »), `app/static/site.css`, `app/loans.py` (`BUTTONS`),
`templates/loans/_buttons.html`, les boutons de retrait et de confirmation (`tools/`, `contacts/`,
`loans/confirm_cancel.html`), `login.html`, `sign_up.html`, nouveau `templates/contacts/_requests.html`
utilisé par `index.html` et `contacts/mine.html`, tests `test_home.py`, `test_loans.py`,
`test_tools_of_contacts.py`. Aucun schéma, aucune dépendance.
