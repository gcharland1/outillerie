# Design

## Context

Voir `proposal.md` pour la motivation et `questions.md` pour chaque décision, sa source et qui l'a
prise. État utile :

- `Loan` : `start_date`, `end_date` non nulles, `CHECK end_date >= start_date`, exclusion GiST des
  prêts `accepted` / `lent` qui se chevauchent ; aucune colonne de message.
- `app/catalog.py` : `visible_tools`, `tool_cards`, `loan_statuses`, `_blocking_loan`,
  `site_today()` (America/Toronto), `tool_list` (filtres de l'URL).
- `app/contacts.py` : pastille des demandes de contact par un context processor ; réponses sous
  verrou (`with_for_update`) ; `_back_from_*` (flash + redirection) pour un second envoi.
- `base.html` affiche tout flash avec la classe `.flash` (rouge).

## Goals / Non-Goals

**Goals:**
- Une seule définition de « l'outil peut être demandé maintenant », partagée par la carte, la
  page de confirmation et l'envoi.
- Aucune adresse de retour fournie par le client : l'origine est énumérée.
- Nombre de requêtes de la liste d'outils inchangé (la vue de l'emprunteur passe par la requête
  de statuts existante).

**Non-Goals:**
- Contrainte en base « une demande ouverte par outil » : « ouverte » dépend de la date du jour,
  aucun index partiel ne peut l'exprimer. Garantie applicative sous verrou.
- Tâche planifiée : l'expiration se lit sur les dates.

## Decisions

### Règle de blocage

`_blocking_loan()` devient `blocking_loan()` : `lent`, OU `accepted` et `end_date >= today`, OU
`requested` et `start_date >= today` (demande non expirée, `pending_request()`). Une demande
expirée cesse ainsi de bloquer le lendemain de son premier jour. Même expression pour le filtre
« Disponible uniquement », la pastille et la vérification à l'envoi.

`_loan_states(tool_ids, viewer_id)`, derrière `loan_statuses(tool_ids)`, lit aussi `borrower_id`
(même requête) : une demande non expirée de `viewer_id` marque la carte `requested_by_viewer`.
`ToolCard` gagne `requested_by_viewer` et `borrow_url`.

### Origine et lien « Emprunter »

`catalog.tool_list(user_id, args, owner=None)` calcule, pour chaque carte disponible, l'URL
`url_for("loans.new", tool_id=…, origin="find"|"contact", q=…, available=…)`. La page de
confirmation renvoie `origin`, `q`, `available` en champs cachés. `loans._origin_url(form, tool)` :
`origin == "contact"` et le propriétaire est encore un contact ⇒ `contacts.show(tool.owner_id)` ;
sinon `tools.find`. `q` et `available` sont repassés à `url_for`, jamais concaténés.

### Blueprint `loans`

`app/loans.py`, `url_prefix="/loans"` (ADR 0011) :

| Route | Rôle |
|-------|------|
| `GET /loans/new/<tool_id>` | page de confirmation |
| `POST /loans/new/<tool_id>` | création, PRG vers l'origine |
| `GET /loans` | « Mes prêts » |
| `POST /loans/<loan_id>/accept` | propriétaire |
| `POST /loans/<loan_id>/refuse` | propriétaire |
| `POST /loans/<loan_id>/withdraw` | emprunteur → `canceled` |

- Outil demandable : `catalog.visible_tool(user_id, tool_id)` (mêmes conditions que
  `visible_tools`, par id) ou 404. Au POST : `SELECT … FOR UPDATE` sur la ligne `tool`, puis
  `catalog.is_available(tool_id)` (`NOT EXISTS` sur `blocking_loan()`) ; sinon flash « Cet outil
  n'est plus disponible » et retour à l'origine. Le verrou sérialise deux envois concurrents.
- Dates : `date.fromisoformat` ; règles dans l'ordre de la spec ; constantes `MAX_LEAD_DAYS = 14`,
  `MAX_LOAN_DAYS = 30` (bornes comprises : `(end - start).days + 1 <= 30`). `loans/confirm.html`
  reçoit les bornes `min` / `max` calculées par la route depuis `site_today()` et ces constantes :
  « Du » de `today` à `today + MAX_LEAD_DAYS`, « Au » de `today` à
  `today + MAX_LEAD_DAYS + MAX_LOAN_DAYS - 1`.
- Message : `strip()`, CRLF → LF, vide → `None`, `MESSAGE_MAX_LENGTH = Loan.message.type.length`,
  `maxlength` dans le gabarit. Rendu échappé, `white-space: pre-line` dans `site.css`.
- Transitions : la ligne `loan` est lue `with_for_update()` ; un autre acteur ⇒ 404 ; plus
  `requested` ou expirée ⇒ flash « Cette demande n'est plus en attente » et retour à « Mes
  prêts ». L'acceptation intercepte l'`IntegrityError` de `excl_loan_tool_dates` ⇒ rollback,
  flash « Ces dates ne sont plus libres ».
- « Mes prêts » : deux requêtes (`Loan` des outils de l'utilisateur, `Loan` dont il est
  l'emprunteur), avec `joinedload` de l'outil, du propriétaire et de l'emprunteur. Tri : d'abord
  les demandes sur lesquelles on peut agir (aujourd'hui, `requested` non expirée : `_is_pending`,
  forme Python de `catalog.pending_request()`), puis les autres, chaque groupe par `created_at`
  décroissante. Le jour où un prêt accepté ou prêté aura une action (changement suivant), il
  rejoint le premier groupe.
  Libellés : `requested` non expirée « En attente », expirée « Expirée », puis « Acceptée »,
  « Refusée », « Annulée », « Prêté », « Rendu ». « Accepter » prend la classe `button success`,
  « Refuser » `button error`, comme « Retirer ma demande ».

### Recherche

`base.html` choisit dans le menu du type de recherche la variable `search_type`, `tool` par
défaut. `search.results` la passe au gabarit : le type cherché, ou `tool` pour un type inconnu.
`search.py` garde `user` pour une URL sans `type` : le lien explicite `type=user` de
`tools/_cards.html` reste valide.

### Pastilles

Context processor de `loans` : `pending_loan_requests` = nombre de `requested`, `start_date >=
today`, sur un outil dont l'utilisateur est propriétaire. `base.html` : pastille sur « Mes prêts »,
et sur le nom d'utilisateur `pending_contact_requests + pending_loan_requests`. La macro
`pending_badge(count, label)` prend son libellé pour lecteur d'écran en paramètre.

### Annulations automatiques

`catalog.cancel_pending_requests(where)` met à `canceled` les `requested` non expirées
correspondantes, dans la transaction de l'appelant :
- `tools.retire` et `tools.edit` (passage à `out_of_order`) : celles de l'outil ;
- `contacts.remove` : celles d'un outil de l'un demandées par l'autre, dans les deux sens.
Les pages `confirm_retire` et `confirm_remove` reçoivent le nombre à annuler
(`catalog.count_pending_requests(where)`) et l'annoncent au singulier ou au pluriel.

### Messages de succès

`flash(message, "success")` ; `base.html` rend chaque message avec la classe `flash
flash-<catégorie>` ; `site.css` donne à `.flash-success` la couleur `--color-success`. Les flash
existants (catégorie par défaut `message`) gardent l'apparence d'erreur.

### Schéma

`loan.message = db.Column(db.String(500), nullable=True)` ; révision par `flask db migrate`, nom de
fichier ASCII ; `docs/schema.md` régénéré (paracelsus) ; `downgrade()` supprime la colonne.
Fixture `make_loan` dans `tests/factories.py`, qui remplace les trois `add_loan` des tests.

## Risks / Trade-offs

- [Une réservation future bloque l'outil jusqu'à sa fin] → règle reconfirmée par l'utilisateur ;
  borné par l'horizon de 14 jours et la durée de 30 jours.
- [Garantie « une demande ouverte » seulement applicative] → verrou de ligne `tool` sur chaque
  création ; test de deux envois successifs. Une écriture hors de la route (console, script)
  pourrait la contourner.
- [Demande expirée qui reste `requested` en base] → l'état se lit sur les dates partout
  (blocage, pastille, libellé, acceptation) par la même expression.
- [Changement d'apparence des flash existants] → seule la catégorie `success` change ; les autres
  restent identiques.

## Migration Plan

1. Déployer : `flask db upgrade` au démarrage ajoute `loan.message` (colonne nullable, sans
   rupture, ADR 0007).
2. Retour arrière : `downgrade` supprime la colonne ; les messages saisis sont perdus.
