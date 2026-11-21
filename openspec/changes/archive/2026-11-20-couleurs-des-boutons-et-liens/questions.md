# Questions — issue #49 (Uniformisation des couleurs au frontend)

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 1 | Remplacer l'ADR 0019 ? | Oui : ADR 0022 (`proposed`), demandé par l'utilisateur ; 0019 passe `superseded by 0022` à l'acceptation. | Utilisateur, 2026-11-20 | utilisateur |
| 2 | Bleu : quels boutons ? Plusieurs par groupe ? | Au plus un bleu par groupe ; « Retour » gris, « Voir plus » bleu. Règle proposée : avancer en bleu, reculer ou dire non en gris (ADR 0022) ; confirmé le 2026-11-20. | Utilisateur, 2026-11-20 | utilisateur |
| 3 | Rouge : « Refuser », « Retirer ma demande », « Pas reçu » ? | Rouge strict : « Refuser » n'est pas destructif, gris ; « Pas reçu » gris ; « Retirer ma demande » rouge (retire) ; confirmé le 2026-11-20. | Utilisateur, 2026-11-20 | utilisateur |
| 4 | Lien vers le profil pour un non-contact (recherche, demandes, ex-contact) ? | Le nom pointe vers ses outils, comme la carte d'un outil : un contact → `/contacts/<id>` ; soi-même → texte, jamais de lien (2026-11-20) ; un non-contact (recherche, demandes reçues, ex-contact) reste en texte, sa page répondant 404 ; un compte supprimé : grisé « (supprimé) ». Utilisateur, 2026-11-20 (non-contact : lecture retenue). | Sourced `tools/_card.html:8`, `contacts.py:68-76` | utilisateur |
| 5 | `warning` ou `error` ? | Chota n'a pas de `warning` : `button error` (`--color-error`). `site.css:19` rend gris tout submit sans `primary` : ajouter `:not(.error)`. | Sourced unpkg chota@0.9.2, `site.css:19` | dépôt |
| 6 | Tests à adapter ? | `test_navigation.py:144-157` (`test_no_button_is_red_or_green`) et les assertions de classes dans `test_loans`, `test_home`, `test_contacts`, `test_tools`, `test_search`, `test_tools_of_contacts`. | Sourced grep | dépôt |
| 7 | Specs et règles touchées ? | `demandes-d-emprunt/spec.md:160-188` (renvoie à 0019, « Aucun bouton n'est rouge ») ; `.claude/rules/templates.md` (Couleurs). | Sourced | dépôt |
| 8 | Rouge des états (« En retard ») ? | Inchangé ; un bouton rouge se distingue par sa forme pleine. Noté dans l'ADR. | Inferred de `accueil/spec.md:100-101`, `templates.md` | convention |
| 9 | Un nom est rendu comment ? | Une macro Jinja unique (lien, texte, ou grisé « (supprimé) »), partagée avec #46. | Inferred de l'inventaire des noms | convention |
| 10 | Nom d'un compte supprimé : lien ? | Jamais : il n'a plus de page. | Inferred | convention |
| 11 | « Retirer ma demande » (rouge) sans confirmation, contre `.claude/rules/templates.md` ? | Page de confirmation ajoutée, avec un champ « Raison » dont le texte s'ajoute au message de la demande. Utilisateur, 2026-11-20. Facultatif, format « — Raison du retrait : … » et borne de longueur : convention (motif de `confirm_cancel` et `MESSAGE_MAX_LENGTH`). | Sourced `loans.py:79,110-111,275-281`, `models/loan.py:41` | utilisateur |
