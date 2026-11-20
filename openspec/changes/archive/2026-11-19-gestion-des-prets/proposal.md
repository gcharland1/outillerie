# Proposal

## Why

Depuis la PR #31, un emprunteur demande un outil et le propriétaire accepte ou refuse, mais rien
ne suit : aucune action ne marque l'outil remis ni rendu, un prêt accepté reste « Acceptée » pour
toujours et un retard passe inaperçu (issue #35). La remise, le retour et l'annulation d'un prêt
accepté, reportés par `demande-d-emprunt`, sont fixés ici.

## What Changes

- Remise de l'outil : le propriétaire déclare « J'ai remis l'outil » et l'emprunteur confirme, ou
  l'emprunteur déclare lui-même l'avoir reçu. Permise dès l'acceptation, jusqu'au dernier jour.
- Retour de l'outil : l'emprunteur déclare « J'ai rendu l'outil » et le propriétaire confirme, ou le
  propriétaire déclare lui-même l'avoir reçu. Retour anticipé permis.
- Celui qui reçoit l'outil peut répondre « Pas reçu » à une déclaration : le prêt revient à l'étape
  précédente.
- Annulation d'un prêt accepté, par l'une ou l'autre partie, avec une page de confirmation, tant
  qu'aucune remise n'est déclarée. Une remise à confirmer se conteste (« Pas reçu ») ; un prêt en
  cours ne s'annule pas, il se termine par un retour.
- Prêt « En retard » le lendemain de sa date de fin tant que l'outil n'est pas rendu ou déclaré rendu ;
  calculé à l'affichage, sans tâche planifiée.
- Un prêt accepté dont la date de fin est passée sans remise devient « Expirée » et ne bloque plus
  l'outil.
- « Mes prêts » : deux listes, « Mes prêts » et « Mes emprunts » ; les retards d'abord, puis les
  lignes où l'utilisateur a une action, puis le reste. Statuts : En attente, Expirée, Attente de
  récupération, Remise à confirmer, Prêté, En retard, Retour à confirmer, Complété, Refusée, Annulée ;
  dates de remise et de retour affichées.
- La pastille de « Mes prêts » compte aussi les remises et retours à confirmer et les prêts en
  retard ; le total du nom d'utilisateur suit.
- Retirer un outil, le passer « Hors d'usage » ou retirer un contact annule aussi les prêts acceptés
  non expirés, sans remise déclarée ; une remise à confirmer et un prêt en cours ne sont jamais
  annulés et restent clôturables. Une remise à confirmer contestée (« Pas reçu ») après une de ces
  actions devient « Annulée ».
- Les contacts voient « Prêté jusqu'au <date> » pendant une remise ou un retour à confirmer ; jamais
  le retard ni l'emprunteur.

## Capabilities

### New Capabilities
- `suivi-des-prets`: remise et retour de l'outil (déclaration, confirmation, « Pas reçu »),
  annulation d'un prêt accepté, retard, expiration d'un prêt accepté, actions selon le rôle.

### Modified Capabilities
- `prets`: « Statut du prêt » (deux statuts « à confirmer ») ; « Aucun chevauchement des prêts
  engagés » (ils engagent les dates).
- `demandes-d-emprunt`: « Page « Mes prêts » » (listes, libellés, dates) ; « Ordre et couleurs de
  « Mes prêts » » (retards d'abord) ; « Pastille des demandes d'emprunt » (prêts qui attendent une
  action).
- `contacts`: « Pastille des demandes en attente » (total) ; « Retrait d'un contact » (annule les
  prêts acceptés pas encore remis).
- `inventaire`: « Modification d'un outil » et « Retrait avec confirmation » (idem).
- `outils-des-contacts`: « Statut de prêt » (remise ou retour à confirmer, prêt accepté expiré).

## Impact

- Code : `app/loans.py` (transitions, page d'annulation, lignes de « Mes prêts », pastille) ;
  `app/catalog.py` (règles de blocage, de retard et d'annulation en cascade, statut de la carte) ;
  `app/tools.py` et `app/contacts.py` (annulation en cascade, avis de confirmation) ; gabarits
  `loans/mine.html`, nouveau `loans/confirm_cancel.html`, `base.html` (texte de la pastille),
  `tools/confirm_retire.html`, `contacts/confirm_remove.html` ; `app/static/site.css` si besoin.
- Schéma : statuts `handover_claimed` et `return_claimed` (CHECK élargi), exclusion des dates
  élargie, colonnes nullables `loan.lent_at` et `loan.returned_at` ; une révision Alembic ;
  `docs/schema.md` régénéré.
- Dépendance : aucune.
- ADR concernés : 0001 (sans JavaScript), 0002 et 0007 (révision expand, CHECK écrit à la main),
  0011 (Blueprint `loans`), 0012 (jeton CSRF sur chaque POST), 0013 (relation de contact), 0017
  (retour arrière sans downgrade). Aucun nouvel ADR : pas de courriel, de tâche planifiée, de table de
  notifications ni de JavaScript.
- Décisions : `questions.md`.

**Hors périmètre**

- Courriel ou autre notification hors du site : la pastille seule prévient.
- Prolongation d'un prêt et modification de ses dates.
- Suivi d'un litige ou d'un outil rendu endommagé : le propriétaire passe l'outil « Hors d'usage » à
  part.
- File d'attente : une seule demande ou un seul prêt ouvert à la fois par outil (règle inchangée).
- Horodatage des autres étapes (acceptation, déclarations, annulation).
