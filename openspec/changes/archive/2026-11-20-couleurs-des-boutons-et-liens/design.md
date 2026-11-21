# Design

## Context

Voir proposal.md pour la motivation. Les décisions de fond sont dans `questions.md` (1 à 10) et la
règle de couleur dans l'ADR 0022 (`proposed`), que ce design applique bouton par bouton.

Ordre d'implémentation dans la branche commune : `retrait-du-nom-d-utilisateur` (#38), puis ce
changement (#49), puis `modification-du-profil` (#46).

État actuel : `Button.style` vide donne un bouton gris, et `loans/_buttons.html` n'ajoute la classe que si
le style existe. `site.css:19` (`[type="submit"]:not(.primary)`) rend gris tout bouton d'envoi sans
`primary`, donc un `button error` d'envoi y perdrait son rouge. Chota 0.9.2 n'a pas de `warning` : le rouge
est `button error` (`--color-error`). Deux noms seulement sont des liens aujourd'hui
(`tools/_card.html:8`, `contacts/mine.html:19`), tous deux vers `/contacts/<id>`.

## Goals / Non-Goals

**Goals:**
- Chaque bouton porte la classe que lui donne l'ADR 0022 ; un test empêche un `error` hors d'un bouton
  destructeur et tout `success`.
- Une seule macro rend un nom d'utilisateur ; aucun gabarit ne compose plus `first_name last_name`
  à la main, hors des exceptions de la spec `interface`.

**Non-Goals:**
- La branche « compte supprimé » de la macro (voir Décisions).
- Toute autre couleur que celle des boutons : liens, états et logo sont inchangés.

## Decisions

### Classe de chaque bouton

Inventaire relu sur le code ; « = » : inchangé.

| Fichier:ligne | Texte | Avant | Après |
|---|---|---|---|
| `base.html:36` | Rechercher | `button` | `button primary` |
| `base.html:56` | Me déconnecter | `button` | = |
| `base.html:59` | Connexion | `button` | = |
| `base.html:60` | Inscription | `button primary` | = |
| `login.html:22` | Se connecter | `button primary` | = |
| `sign_up.html:40` | Créer mon compte | `button primary` | = |
| `logged_out.html:15` | Se reconnecter | `button primary` | = |
| `too_large.html:11` | Retour à mes outils | `button` | = |
| `index.html:28` | Voir tous mes prêts | `button` | `button primary` |
| `index.html:48` | Mes contacts | `button` | `button primary` |
| `index.html:61` | Voir plus | `button` | `button primary` |
| `tools/mine.html:6` | Enregistrer un outil | `button primary` | = |
| `tools/mine.html:7` | Voir mes outils retirés | `button` | = |
| `tools/mine.html:26` | Modifier | `button` | `button primary` |
| `tools/mine.html:27` | Retirer | `button` | `button error` |
| `tools/confirm_retire.html:22` | Annuler | `button` | = |
| `tools/confirm_retire.html:23` | Confirmer le retrait | `button primary` | `button error` |
| `tools/retired.html:6` | Retour à mes outils | `button` | = |
| `tools/retired.html:26` | Remettre en circulation | `button primary` | = |
| `tools/form.html:49` | Annuler | `button` | = |
| `tools/form.html:50` | Enregistrer | `button primary` | = |
| `tools/_cards.html:15` | Filtrer | `button` | `button primary` |
| `tools/_card.html:17` | Demande envoyée (désactivé) | `button` | = |
| `tools/_card.html:19` | Emprunter | `button primary` | = |
| `tools/_card.html:21` | Emprunter (désactivé) | `button` | = |
| `contacts/_requests.html:17` | Refuser | `button` | = |
| `contacts/_requests.html:24` | Accepter | `button primary` | = |
| `contacts/mine.html:22` | Retirer | `button` | `button error` |
| `contacts/confirm_remove.html:16` | Annuler | `button` | = |
| `contacts/confirm_remove.html:17` | Retirer | `button primary` | `button error` |
| `search/results.html:24` | Envoyer une demande | `button primary` | = |
| `search/results.html:27` | Demande envoyée (désactivé) | `button` | = |
| `search/results.html:29` | Répondre à sa demande | `button primary` | = |
| `search/results.html:31` | Déjà en contact (désactivé) | `button` | = |
| `loans/confirm.html:32` | Annuler | `button` | = |
| `loans/confirm.html:33` | Confirmer | `button primary` | = |
| `loans/confirm_cancel.html:13` | Retour à « Mes prêts » | `button` | = |
| `loans/confirm_cancel.html:14` | Annuler le prêt | `button primary` | `button error` |
| `loans.py:108` `refuse` | Refuser | `""` | = |
| `loans.py:109` `accept` | Accepter | `primary` | = |
| `loans.py:110` `withdraw` | Retirer ma demande | `""` | `error` |
| `loans.py:111` `cancel` | Annuler le prêt | `""` | `error` |
| `loans.py:112` `not-received` | Pas reçu | `""` | = |
| `loans.py:113-116` | J'ai remis / reçu / rendu l'outil, Confirmer la réception | `primary` | = |

Cas tranchés par la règle « au plus un bleu par groupe » : « Connexion » et « Inscription » avancent
tous deux ; « Inscription », déjà bleu, reste le principal. « Voir mes outils retirés » partage son groupe
avec « Enregistrer un outil » et reste gris. « Modifier » (bleu) et « Retirer » (rouge) partagent un
groupe sans enfreindre la règle.

`site.css` : le sélecteur devient `[type="submit"]:not(.primary):not(.error)` ; les commentaires qui
citent l'ADR 0019 citent 0022.

### Contrôle des couleurs dans les tests

`test_no_button_is_red_or_green` devient un test qui parcourt les gabarits : aucune classe `success` sur
un bouton ; une classe `error` seulement sur une ligne dont le libellé est l'un des boutons destructeurs
(« Retirer », « Confirmer le retrait », « Annuler le prêt »). Pour `loans.BUTTONS`, l'ensemble des actions
de style `error` vaut exactement `{"withdraw", "cancel"}` et aucun style n'est `success`. Une liste fermée
de libellés plutôt qu'une heuristique : un nouveau bouton rouge doit être ajouté sciemment au test.

### Macro du nom

`templates/_user_name.html` définit `user_name(user)`, qui rend :
- un contact : lien vers `url_for('contacts.show', user_id=user.id)` ;
- tout autre compte, l'utilisateur lui-même compris : le prénom et le nom en texte.

Le texte reste « Prénom Nom » dans tous les cas, échappé par Jinja ; un lien a la couleur des liens
(`--color-primary`), sans classe propre.

Pour savoir qui est un contact, un processeur de contexte de la Blueprint `contacts`
(`app_context_processor`, comme `inject_loan_actions` de `loans.py`) expose `contact_ids`, l'ensemble
des identifiants des contacts de l'utilisateur connecté (vide pour un visiteur), lu par une fonction
publique de `catalog.py` qui exécute la sous-requête existante `_contact_ids`. Les gabarits importent la
macro avec `{% from "_user_name.html" import user_name with context %}`, sans quoi une macro importée ne
voit ni `current_user` ni `contact_ids` ; `_card.html`, inclus par trois pages, l'importe lui-même. Une
macro qui appelle `user_name` doit elle aussi être importée `with context` : `contacts/_requests.html`,
importé sans contexte par `index.html:3` et `contacts/mine.html:2`, ne transmettrait à `user_name` qu'un
contexte sans `current_user`. Le test `current_user.id` sur un `current_user` indéfini lève alors
`UndefinedError` (vérifié avec Jinja seul, hors de Flask).

Alternatives écartées :
- un indicateur calculé par chaque vue et passé à la macro : huit vues à modifier, et autant d'occasions
  d'oublier ; la règle « pas de logique métier dans les gabarits » est tenue puisque la vue (le processeur
  de contexte) prépare l'ensemble et que la macro ne fait qu'un test d'appartenance ;
- un appel `catalog.is_contact` par nom affiché : une requête par nom au lieu d'une par page ;
- l'état `relation_states` de la recherche : il ne sert qu'à la page de résultats.

Gabarits où la macro remplace le nom composé à la main : `index.html:18` (autre partie d'un prêt) et
`:42` (contact noué), `loans/mine.html:14` (autre partie), `loans/confirm.html:12` (propriétaire),
`loans/confirm_cancel.html:7` (titre), `contacts/_requests.html:9` (demandeur, rendu en texte),
`contacts/mine.html:19`, `contacts/confirm_remove.html:7` (titre), `search/results.html:16`,
`tools/_card.html:8`.

Restent en texte, comme exceptions de la spec : `base.html:44` (déclencheur du menu du compte),
`contacts/show.html:4-5` (titre et sous-titre de la page du contact elle-même : un lien vers la page
affichée ne mène nulle part), `loans/confirm.html:28` (libellé du champ « Message pour … » : un lien dans un
`<label>` ferait quitter un formulaire en cours de saisie).

Aucune page ne montre aujourd'hui le nom de l'utilisateur à lui-même hors du menu du compte (la recherche
l'exclut, l'autre partie d'un prêt n'est jamais lui, les cartes ne montrent que des outils de contacts) :
le cas « soi-même » (texte) se teste en rendant la macro directement (`render_template_string` dans un
contexte de requête connecté).

### Compte supprimé : laissé à `modification-du-profil`

La macro n'a pas de branche « (supprimé) » dans ce changement. `deleted_at` n'existe pas encore ; une
branche écrite maintenant ne pourrait être ni exercée ni testée, du code mort jusqu'au changement
suivant. `modification-du-profil`, livré après celui-ci dans la même branche, ajoute la colonne, la
branche grisée « Prénom Nom (supprimé) » sans lien en tête de la macro, et le cas « supprimé » au
requirement « Nom d'un utilisateur » de la capacité `interface`.

### Capacité `interface`

Les deux règles valent pour toutes les pages (authentification, inventaire, contacts, recherche, prêts,
accueil) ; aucune capacité existante ne porte une règle d'affichage transverse. `contacts` aurait pu
recevoir « Nom d'un utilisateur », puisque le lien dépend de la relation de contact, mais le requirement
gouverne surtout les pages des prêts, de la recherche et de l'accueil. Les deux règles rejoignent donc
une capacité `interface`, comme elles sont réunies sous « Interface » dans `.claude/rules/templates.md`.

### ADR

L'ADR 0022 (`proposed`) remplace 0019. Son passage à `accepted`, et celui de 0019 à
`superseded by 0022`, se font à l'archivage (`/livrer`), pas pendant l'implémentation.

## Risks / Trade-offs

- [Une requête de plus par page rendue pour un utilisateur connecté] → une seule requête sur les
  relations de contact, à côté de celles des pastilles déjà faites à chaque page.
- [Un gabarit importe la macro, ou une macro qui l'appelle, sans `with context` : la page lève
  `UndefinedError` sur `current_user` et répond 500] → les tests de la spec rendent chaque page qui
  affiche un nom, dont l'accueil et « Mes contacts » avec une demande de contact reçue.
- [Des tests cherchent un nom dans le HTML brut (« Vous êtes maintenant en contact avec Bob Gagnon »,
  « Propriétaire : Bob Gagnon »), qu'une balise `<a>` coupe] → ces assertions passent à un texte sans
  balises ou à l'attribut `href` attendu.
- [Le rouge sert aux boutons et aux états] → accepté par l'ADR 0022 ; le bouton se distingue par sa forme
  pleine.

### Confirmation du retrait d'une demande

Décision de l'utilisateur (questions.md #11) : « Retirer ma demande », rouge selon l'ADR 0022, passe par une
page de confirmation, comme le veut `.claude/rules/templates.md`, avec un champ « Raison » facultatif.

- Le bouton « Retirer ma demande » de `loans/_buttons.html` devient un lien (comme « Annuler le prêt »,
  `loans.py:111`) vers `GET /loans/<id>/withdraw`, qui rend `loans/confirm_withdraw.html` sur le modèle
  de `loans/confirm_cancel.html` (`confirm_cancel`, `loans.py:275-281`) : outil, propriétaire (macro
  `user_name`), dates, `<textarea name="reason">`, « Retour » (`button`) et « Retirer ma demande »
  (`button error`). L'origine (« Mes prêts » ou accueil) est portée comme pour l'annulation.
- Le POST reste l'action `withdraw` existante (transition `REQUESTED → CANCELED`, `loans.py:79`), avec la
  raison lue, `strip()`ée. Raison vide : message inchangé. Sinon : `message = f"{message} — Raison du
  retrait : {raison}"`, ou `f"Raison du retrait : {raison}"` sans message. Le tiret long garde une seule
  ligne, que `loans/mine.html:16` affiche telle quelle.
- Longueur : `Loan.message` fait `MESSAGE_MAX_LENGTH` (500) caractères. Le reste disponible pour la raison
  est calculé côté serveur et donné en `maxlength` ; un dépassement réaffiche la page avec « La raison ne
  doit pas dépasser N caractères », sans changer la demande.
- Un GET sur une demande qui n'est plus en attente ramène à l'origine avec « Cette demande n'est plus en
  attente » ; la demande d'un autre répond 404, au GET comme au POST. CSRF : le formulaire porte
  `csrf_token()` (ADR 0012).
