# Tasks

## 1. Schéma et fixtures

- [x] 1.1 `loan.message` (`String(500)`, nullable) ; révision `uv run flask db migrate`, fichier renommé en ASCII, `downgrade()` qui supprime la colonne ; `docs/schema.md` régénéré ; vérifier `flask db upgrade`, `downgrade base`, `upgrade`, `check` sur une base jetable et `paracelsus inject --check`
- [x] 1.2 `make_loan(tool_id, borrower_id, first_day, last_day, status=None, message=None)` dans `tests/factories.py`, qui remplace les `add_loan` de `test_loan_model.py`, `test_catalog.py` et `test_tools_of_contacts.py` ; vérifier que `uv run pytest` passe

## 2. Règle de blocage et carte

- [x] 2.1 `_blocking_loan` : `requested` bloque tant que `start_date >= site_today()` ; vérifier par des tests pytest les scénarios de « Statut de prêt » dont « Demande expirée », et « Disponible uniquement »
- [x] 2.2 `loan_statuses(…, viewer_id)` et `ToolCard.requested_by_viewer`, `borrow_url` (origine `find` ou `contact`, `q`, `available`) ; `_cards.html` : « Emprunter » en lien actif, grisé, ou « Demande envoyée » ; « Bientôt disponible » retiré ; vérifier par des tests pytest les scénarios de « Carte d'un outil » et que le nombre de requêtes reste fixe

## 3. Page de confirmation et envoi

- [x] 3.1 Blueprint `loans` enregistrée ; `catalog.visible_tool` ; `GET /loans/new/<tool_id>` et gabarit `loans/confirm.html` ; vérifier par des tests pytest « Contenu de la page », « Notes privées cachées », les 404 de « Outil qu'on peut demander », la redirection d'un visiteur, et qu'aucune demande n'est créée par le GET
- [x] 3.2 `POST /loans/new/<tool_id>` : dates, message, verrou de l'outil, disponibilité, création, PRG vers l'origine énumérée ; vérifier par des tests pytest chaque scénario de « Dates d'une demande », « Message au propriétaire » (longueur, espaces), « Envoi d'une demande » (origine `find` filtrée, `contact`, inconnue, « Annuler », CSRF avec `csrf_client`) et « Une demande à la fois par outil »
- [x] 3.3 Catégories de flash dans `base.html` et `.flash-success` dans `site.css` ; vérifier par des tests pytest que « Demande envoyée à Bob Gagnon » porte la classe de succès et qu'un message d'erreur existant garde la sienne

## 4. « Mes prêts » et réponses

- [x] 4.1 `GET /loans` et `loans/mine.html` (demandes reçues, mes demandes, libellés de statut, message en texte brut), entrée « Mes prêts » du menu du compte, règle `.claude/rules/templates.md` mise à jour ; vérifier par des tests pytest « Demandes reçues et envoyées », « Entrée du menu », « Balisage affiché tel quel », « Message privé », « Demande expirée », la redirection d'un visiteur, et `/loans` dans `test_no_page_says_voisin`
- [x] 4.2 `POST /loans/<id>/accept`, `/refuse`, `/withdraw` sous verrou ; vérifier par des tests pytest chaque scénario de « Réponse du propriétaire » et « Retrait d'une demande par l'emprunteur », l'acceptation d'une demande expirée refusée, et « Ces dates ne sont plus libres » sur un chevauchement

## 5. Pastilles

- [x] 5.1 Context processor `pending_loan_requests`, pastille sur « Mes prêts », total sur le nom d'utilisateur, `pending_badge(count, kind)` ; vérifier par des tests pytest « Une demande reçue », « Demande expirée hors de la pastille » et « Demandes de contact et d'emprunt », et mettre à jour les tests de pastille existants

## 6. Annulations automatiques

- [x] 6.1 `catalog.count_pending_requests` / `cancel_pending_requests` ; `tools.retire`, `tools.edit` (passage hors d'usage) et `contacts.remove` ; annonce dans `confirm_retire.html` et `confirm_remove.html` ; vérifier par des tests pytest « Demandes annulées par le retrait », « Demandes annulées par le passage hors d'usage » et « Demandes d'emprunt annulées », et qu'une demande déjà acceptée n'est pas touchée

## 7. Vérification

- [ ] 7.1 Vérifier à la main dans `docker compose up --build`, avec deux comptes en contact et un troisième : demander un outil depuis les deux listes, voir la pastille, accepter, refuser, retirer une demande, retirer un outil et un contact avec une demande en attente
- [x] 7.2 Lancer `/verifier` ; il doit rendre « terminé »

## Workflow follow-up

- Changement suivant : remise (`lent`), retour (`returned`) et annulation d'un prêt accepté.
- Archiver ce changement une fois validé (`/opsx:archive`).
