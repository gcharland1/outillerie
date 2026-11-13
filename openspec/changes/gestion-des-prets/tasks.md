# Tasks

## 1. Schéma et fixtures

- [x] 1.1 `LoanStatus.HANDOVER_CLAIMED` et `RETURN_CLAIMED`, colonnes nullables `lent_at` et `returned_at`, exclusion du modèle élargie aux quatre statuts engagés ; révision `uv run flask db migrate`, renommée en ASCII, complétée à la main (`CHECK` et exclusion recréés, `downgrade` qui ramène `handover_claimed → accepted`, `return_claimed → lent`) ; `docs/schema.md` régénéré ; vérifier `flask db upgrade`, `downgrade base`, `upgrade`, `check` sur une base jetable et `paracelsus inject --check`
- [x] 1.2 Tests de `test_loan_model.py` et `test_schema.py` : « Statuts à confirmer », « Statut inconnu refusé », « Prêt à confirmer engagé » ; `make_loan` accepte `lent_at` / `returned_at` ; vérifier que `uv run pytest` passe

## 2. États calculés, blocage et carte

- [x] 2.1 `catalog.expired_acceptance()`, `overdue_loan()`, `blocking_loan()` élargi ; `_loan_states()` traite les deux statuts « à confirmer » comme `lent` ; vérifier par des tests pytest (date du site fixée) les scénarios de « Statut de prêt » dont « Remise ou retour à confirmer », « Prêt accepté expiré », « Prêt en retard », et le filtre « Disponible uniquement »

## 3. Transitions

- [x] 3.1 Table des transitions et `_loan_for(loan_id, action)` dans `app/loans.py` (verrou, 404, `STATUS_CHANGED`), `accept` / `refuse` / `withdraw` réécrits dessus sans changer leur comportement ; vérifier que les tests existants de `test_loans.py` passent
- [x] 3.2 Routes `hand-over`, `receive`, `give-back`, `take-back`, `not-received` (PRG, `lent_at` / `returned_at`) ; vérifier par des tests pytest chaque scénario de « Remise déclarée par le propriétaire », « Réception de l'outil par l'emprunteur », « Retour déclaré par l'emprunteur », « Réception du retour par le propriétaire », « Déclaration contestée »
- [x] 3.3 `GET` / `POST /loans/<id>/cancel` et gabarit `loans/confirm_cancel.html` ; vérifier par des tests pytest les scénarios de « Annulation d'un prêt accepté »
- [x] 3.4 Vérifier par des tests pytest les scénarios de « Actions réservées aux parties » : tiers et prêt inexistant 404, mauvais rôle 404, envoi en double, outil retiré et ancien contact, jeton CSRF absent (`csrf_client`), visiteur

## 4. « Mes prêts »

- [x] 4.1 `LoanRow` (`actions`, `overdue`, dates de remise et de retour), libellés de statut, tri en trois groupes ; `loans/mine.html` : listes « Mes prêts » / « Mes emprunts », boutons par action avec leurs classes ; vérifier par des tests pytest les scénarios de « Page « Mes prêts » », « Ordre et couleurs de « Mes prêts » », « Prêt en retard » (dernier jour, lendemain, retour déclaré, retour contesté) et « Prêt accepté expiré », et `/loans` dans `test_no_page_says_voisin`

## 5. Pastilles

- [x] 5.1 Context processor `loan_actions`, texte caché de `pending_badge` en paramètre, total du nom d'utilisateur ; vérifier par des tests pytest les scénarios de « Pastille des demandes d'emprunt » et de « Pastille des demandes en attente », dont « Demande de contact et retour à confirmer »

## 6. Annulations en cascade

- [x] 6.1 `cancel_unstarted_loans()` et `cancel_notice(requests, loans, between)` ; `tools.edit` (hors d'usage), `tools.retire`, `contacts.remove` et leurs pages de confirmation ; vérifier par des tests pytest « Prêt accepté annulé par le passage hors d'usage », « Prêt en cours gardé », « Prêt accepté annulé par le retrait », « Prêt en cours gardé au retrait », « Prêts acceptés annulés, prêt en cours gardé », et que les scénarios existants d'annulation de demandes passent toujours

## 7. Vérification

- [ ] 7.1 Vérifier à la main dans `docker compose up --build`, avec deux comptes en contact et un troisième : remise déclarée puis confirmée, réception directe, retour déclaré puis contesté puis confirmé, annulation, prêt en retard (date de fin passée en base), pastilles, retrait d'un outil prêté
- [x] 7.2 Lancer `/verifier` ; il doit rendre « terminé »

## Workflow follow-up

- Relecture par l'agent `relecteur` avant la PR.
- Archiver ce changement une fois mergé (`/opsx:archive`).
