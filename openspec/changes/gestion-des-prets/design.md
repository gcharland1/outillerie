# Design

## Context

Voir `proposal.md` pour la motivation et `questions.md` pour chaque décision, sa source et qui l'a
prise. État utile :

- `Loan.status` : `VARCHAR(20)` + `CHECK ck_loan_loan_status` (`requested`, `accepted`, `refused`,
  `canceled`, `lent`, `returned`) ; exclusion GiST `excl_loan_tool_dates` `WHERE status IN
  ('accepted', 'lent')` ; seul horodatage : `created_at`. Dernière révision : `13db5eeed32b`.
- `app/catalog.py` : `site_today()` (America/Toronto), `pending_request()`, `blocking_loan()`,
  `cancel_pending_requests()`, `cancel_notice()`, `requests_for_tool()`, `requests_between()`,
  `_loan_states()` (statut de la carte).
- `app/loans.py` : `_pending_loan()` (verrou `FOR UPDATE`, 404 pour un inconnu ou un non-acteur),
  `_rows()` / `_row()` (libellé, « Expirée » calculée, actionnables d'abord), pastille par
  `inject_pending_loan_requests`.
- Aucune route n'écrit `lent` ni `returned` aujourd'hui.

## Goals / Non-Goals

**Goals:**
- Une table de transitions unique, lue par les routes et par « Mes prêts » : qui peut faire quoi
  depuis quel statut ne s'écrit qu'une fois.
- Une expression SQL par état calculé (`overdue_loan()`, `pending_request()`, prêt accepté expiré),
  partagée par la pastille, le tri, le libellé et le blocage.
- Aucune requête de plus par ligne de « Mes prêts ».

**Non-Goals:**
- Statut stocké « en retard » ou « expiré », tâche planifiée : ces états se lisent sur les dates
  (session 2026-10-21 : un statut stocké enregistre un évènement).
- Historique complet des transitions : seules `lent_at` et `returned_at` (questions.md #8).

## Decisions

### Statuts et horodatages

`LoanStatus` gagne `HANDOVER_CLAIMED = "handover_claimed"` et `RETURN_CLAIMED = "return_claimed"`
(16 et 14 caractères, sous la longueur 20). « Remis » n'est pas employé : il a désigné la prise de
l'outil le 2026-10-21. `Loan` gagne `lent_at` et `returned_at`, `DateTime(timezone=True)` nullables,
affichés en date du fuseau du site (`french_date`).

Alternative écartée : un seul statut `claimed` avec une colonne « qui a déclaré » ; deux valeurs
lisibles dans le `CHECK` et l'exclusion valent mieux qu'une colonne de plus à garder cohérente.

### Transitions

Une table dans `app/loans.py`, une entrée par action :

| Action (route `POST /loans/<id>/<action>`) | Acteur | Depuis | Vers | Écrit |
|---|---|---|---|---|
| `hand-over` « J'ai remis l'outil » | propriétaire | `accepted` non expiré | `handover_claimed` | |
| `receive` « J'ai reçu l'outil » / « Confirmer la réception » | emprunteur | `accepted` non expiré, `handover_claimed` | `lent` | `lent_at` |
| `give-back` « J'ai rendu l'outil » | emprunteur | `lent` | `return_claimed` | |
| `take-back` « J'ai reçu l'outil » / « Confirmer la réception » | propriétaire | `lent`, `return_claimed` | `returned` | `returned_at` |
| `not-received` « Pas reçu » | emprunteur | `handover_claimed` | `accepted` | |
| `not-received` « Pas reçu » | propriétaire | `return_claimed` | `lent` | |
| `cancel` « Annuler le prêt » (`GET` = confirmation) | l'un ou l'autre | `accepted` non expiré | `canceled` | |

`not-received` a deux entrées : l'acteur se déduit du statut. Une remise contestée dont l'outil est retiré ou
« Hors d'usage », ou dont les deux ne sont plus en contact, passe à `canceled` au lieu de `accepted` :
la cascade l'avait épargnée parce qu'elle était déclarée remise (`_still_lendable`). Le libellé du bouton dépend du statut
de départ (« Confirmer la réception » si une déclaration attend, « J'ai reçu l'outil » sinon).

`_pending_loan(loan_id, owner)` se généralise en `_loan_for(loan_id, action)` : verrou `FOR UPDATE`,
404 si le prêt n'existe pas ou si l'utilisateur n'est l'acteur d'aucune entrée de l'action, `None`
si le statut ne permet plus l'action. Les routes existantes (`accept`, `refuse`, `withdraw`) gardent
leur message « Cette demande n'est plus en attente » ; les nouvelles disent « Ce prêt a déjà changé
de statut » (`STATUS_CHANGED`). Aucun contrôle de visibilité de l'outil ni de relation de contact
(questions.md #11). Toutes les réponses : PRG vers `loans.mine`.

`receive` et `not-received` sur `handover_claimed` ne touchent pas aux dates : l'exclusion ne peut
pas se déclencher (même ensemble de jours, statut toujours engagé).

### États calculés

Dans `app/catalog.py`, à côté de `pending_request()` :

- `expired_acceptance()` : `accepted` et `end_date < today`.
- `overdue_loan()` : statut `lent` ou `handover_claimed` et `end_date < today`.
- `blocking_loan()` : `lent`, `handover_claimed`, `return_claimed` sans borne ; `accepted` et
  `end_date >= today` ; `pending_request()`.

Côté Python, `_row()` applique les mêmes règles pour le libellé : `overdue` l'emporte sur le statut
(« En retard »), puis « Expirée » pour `requested` ou `accepted` passés, sinon `STATUS_LABELS`.

### « Mes prêts »

`LoanRow` remplace `pending: bool` par `actions` (liste de `(action, libellé, classe)` permises pour
l'utilisateur et ce prêt, tirée de la table) et `overdue: bool`, plus `lent_on` / `returned_on`
formatés. Tri : clé `(not overdue, end_date si overdue, not actions, -created_at, -id)`, sur les
lignes déjà chargées (pas de requête de plus). Gabarit : macro unique, boucle sur `row.actions`, un
`<form method="post">` avec jeton CSRF par action ; « Annuler le prêt » est un `<a class="button
error">` vers la page de confirmation. Titres « Mes prêts » / « Mes emprunts ». Classes : `success`
pour « Accepter », `error` pour « Refuser », « Annuler le prêt », « Pas reçu », `primary` sinon
(`.claude/rules/templates.md`).

### Pastille

`inject_pending_loan_requests` devient `inject_loan_actions` → `loan_actions` : une requête
`count(*)` avec une condition `OR` :

- outil de l'utilisateur et (`pending_request()` OU `return_claimed` OU `overdue_loan()`) ;
- emprunteur = l'utilisateur et (`handover_claimed` OU `overdue_loan()`).

Un `handover_claimed` en retard ne compte qu'une fois par personne (une ligne, une condition `OR`).
La macro `pending_badge` prend son texte caché en paramètre : « prêt(s) qui attend(ent) votre
action » pour « Mes prêts ».

### Annulation en cascade

`cancel_pending_requests(*conditions)` devient `cancel_unstarted_loans(*conditions)` : `UPDATE …
SET status = 'canceled'` sur `pending_request()` OU `upcoming_acceptance()` (`accepted` non expiré).
Un `handover_claimed` est traité comme une remise faite et n'est jamais annulé (questions.md, #3 et
#10 révisés) ; un `accepted` expiré reste « Expirée », comme une demande expirée. Les pages de
confirmation comptent séparément demandes et prêts : `cancel_notice(requests, acceptances, between)` →
« 1 demande d'emprunt en attente et 1 prêt accepté seront annulés », ou chacun seul comme dans les
scénarios.

### Carte de l'outil

`_loan_states()` traite `handover_claimed` et `return_claimed` comme `lent` (« Prêté jusqu'au
<date> ») ; un `accepted` expiré ne sort plus de `blocking_loan()`, donc « Disponible ». Aucun
libellé de retard sur la carte (vie privée, questions.md #17).

### Migration

Une révision `flask db migrate -m "Prêts : remise, retour et horodatages"`, renommée en ASCII, après
`13db5eeed32b` :

- `add_column` `lent_at`, `returned_at` (autogénérées) ;
- à la main : `DROP` puis `CREATE` de `ck_loan_loan_status` avec les huit valeurs, et de
  `excl_loan_tool_dates` avec `status IN ('accepted', 'handover_claimed', 'lent', 'return_claimed')` ;
- `downgrade` : `handover_claimed → accepted`, `return_claimed → lent` par `UPDATE`, puis
  contraintes d'origine et `drop_column`.

`flask db check` vide ensuite ; `docs/schema.md` régénéré (ADR 0009) ; `test_schema` vérifie le
nouveau `where` de l'exclusion.

## Risks / Trade-offs

- [Retour arrière manuel vers une version antérieure sans downgrade (ADR 0017) : l'ancien code lit
  `handover_claimed` et lève une erreur (Training : `Enum` non natif refuse une valeur inconnue à la
  lecture)] → Le retour automatique ne se produit que si le déploiement échoue avant de servir, donc
  avant toute écriture des nouvelles valeurs ; un retour manuel passe par `flask db downgrade`.
- [« Pas reçu » sur une remise et retrait de l'outil, « Hors d'usage » ou retrait du contact au même
  instant : la cascade ne voit pas encore `accepted`, « Pas reçu » ne voit pas encore le retrait, un
  prêt accepté reste sur l'outil retiré] → Fenêtre de quelques millisecondes ; le prêt reste annulable
  à la main. Accepté plutôt que verrouiller l'outil et la relation dans chaque route.
- [Pastille sans courriel : un utilisateur qui ne se connecte pas ignore un retard] → Accepté
  (questions.md #5).
- [Deux personnes agissent en même temps sur un prêt] → Verrou `FOR UPDATE` ; le second reçoit
  « Ce prêt a déjà changé de statut ».
- [Prêts `accepted` déjà en production pour un outil réellement prêté] → Ils restent actionnables
  jusqu'à leur fin (« J'ai reçu l'outil »), puis « Expirée » ; aucune migration de données.

## Migration Plan

1. Merge sur `main` ; le déploiement par sondage applique `flask db upgrade` (ADR 0017).
2. Aucune donnée à migrer.
3. Retour arrière : `flask db downgrade 13db5eeed32b` puis version précédente, ou restauration de la
   sauvegarde `pg_dump` prise avant le déploiement.
