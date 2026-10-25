# Tasks

## 1. Décisions

- [x] 1.1 Faire accepter par l'utilisateur l'ADR 0013 « Relation de contact symétrique en une ligne » ; vérifier que son `status` et l'index `docs/decisions/README.md` indiquent `accepted`

## 2. Schéma

- [x] 2.1 Créer `models/contact.py` (`ContactRequest`, `ContactRelation` avec `between(first_id, second_id)`) selon le design, et l'exporter dans `models/__init__.py` ; ajouter `make_contact_request` et `make_contact_relation` à `tests/factories.py` et une fixture `carole` à `tests/conftest.py` ; écrire `tests/test_contact_model.py` : demande à soi-même refusée, second envoi refusé, demande croisée refusée, nouvelle demande acceptée après suppression de la précédente, `between` range la paire dans les deux sens, paire non rangée refusée par le `CHECK`, relation en double refusée ; vérifier que `uv run pytest` passe
- [x] 2.2 `uv run flask db migrate -m "Contacts : demandes et relations"`, renommer la révision en `<rev>_contacts_demandes_et_relations.py`, relire et compléter à la main l'index `uq_contact_request_pair` et les deux `CHECK` ; vérifier `uv run flask db upgrade`, `downgrade -1`, `upgrade`, puis `uv run flask db check` vide (ou l'avertissement sur l'index d'expression noté dans la révision)
- [x] 2.3 Régénérer `docs/schema.md` avec `uv run paracelsus inject ../docs/schema.md` ; vérifier que `--check` passe

## 3. Blueprint `contacts` et navigation

- [x] 3.1 Créer `app/contacts.py` (Blueprint `contacts`, préfixe `/contacts`, `@login_required` sur chaque route) et l'enregistrer dans `create_app()` ; route `GET /contacts` et gabarit `contacts/mine.html` (demandes reçues de la plus ancienne à la plus récente avec « Accepter » et « Refuser », puis contacts triés par nom d'utilisateur sans égard à la casse avec « Retirer » en rouge, message « Vous n'avez encore aucun contact ») ; vérifier par des tests pytest (`tests/test_contacts.py`) la redirection d'un visiteur vers `/login` avec le message, la demande reçue affichée, la demande envoyée absente, l'ordre des contacts et la liste vide
- [x] 3.2 Ajouter « Mes contacts » au menu du compte de `base.html` (lien texte, `.claude/rules/templates.md`) ; vérifier par des tests pytest (`tests/test_navigation.py`) sa présence pour un utilisateur connecté et son absence pour un visiteur
- [x] 3.3 Context processor `pending_contact_requests` et pastille `.badge` (avec `aria-label`) à côté du nom d'utilisateur et de « Mes contacts », style dans `app/static/site.css` ; vérifier par des tests pytest la pastille « 2 » pour deux demandes reçues, son absence sans demande en attente, son absence après acceptation ou refus, et son absence pour le demandeur

## 4. Réponse aux demandes

- [x] 4.1 Écrire `_received_request(request_id)` (`with_for_update()`, 404 pour la demande d'un autre, `flash` et redirection pour une demande qui n'existe plus) et les routes `POST /contacts/requests/<id>/accept` et `/refuse` ; vérifier par des tests pytest l'acceptation (demande supprimée, contact des deux côtés), le refus (demande supprimée, pas de relation), le 404 pour une demande adressée à un autre et pour le demandeur lui-même, et « Cette demande n'est plus en attente » sur un refus après acceptation, relation intacte

## 5. Envoi d'une demande

- [x] 5.1 Route `POST /contacts/requests` (champs `recipient_id` et `q`) selon l'ordre du design, `IntegrityError` absorbé, redirection vers `search.results` avec `q` ou vers `contacts.mine` pour une demande croisée ; écrire `relation_states(user_ids)` ; vérifier par des tests pytest la demande enregistrée, le second envoi sans doublon, la demande à un contact ignorée, le 404 à soi-même et à un compte inconnu, la demande croisée redirigée vers « Mes contacts », la nouvelle demande après un refus, et chaque état de `relation_states`

## 6. Retrait d'un contact

- [x] 6.1 Routes `GET` et `POST /contacts/<user_id>/remove` et gabarit `contacts/confirm_remove.html` (nom du contact, « Annuler », « Retirer » en rouge) ; vérifier par des tests pytest la page de confirmation sans effet, le retrait des deux côtés, « Cette personne ne fait pas partie de vos contacts » sur un second envoi et pour un non-contact, et le 404 pour un compte inconnu

## 7. Recherche

- [x] 7.1 Créer `app/search.py` (Blueprint `search`, `@login_required`) et l'enregistrer ; route `GET /search` et gabarit `search/results.html` (nom d'utilisateur, prénom, nom, bouton selon l'état, formulaire d'envoi avec `recipient_id`, `q` et jeton CSRF) ; vérifier par des tests pytest (`tests/test_search.py`) la redirection d'un visiteur, le minimum de 3 caractères après `strip()` (« bo » refusé, « bob » accepté, texte vide), la correspondance par nom, par prénom et nom avec espaces autour, sans égard à la casse, soi-même exclu, `%` cherché tel quel, l'ordre, les coordonnées absentes, les messages de l'absence de résultat et du type « Outil »
- [x] 7.2 Barre de recherche dans `.nav-center` de `base.html` (menu « Utilisateur » choisi, « Outil » `disabled`, champ `minlength="3"` prérempli par `search_text`, bouton « Rechercher »), style `.search-bar` dans `app/static/site.css` ; vérifier par des tests pytest sa présence connectée avec « Outil » désactivé, son absence pour un visiteur, et le texte conservé sur la page de résultats
- [x] 7.3 Vérifier par des tests pytest les scénarios d'action de la spec `recherche` : envoi depuis les résultats qui revient sur la même recherche avec « Demande envoyée » grisé, « Répondre à sa demande » vers « Mes contacts », « Déjà en contact » grisé, « Envoyer une demande » après un refus

## 8. Protection CSRF

- [x] 8.1 Vérifier par un test pytest que chaque `<form method="post">` de « Mes contacts », de la confirmation de retrait et des résultats de recherche contient le champ `csrf_token`, et que le formulaire de recherche est en `GET`

## 9. Vérification

- [ ] 9.1 Parcourir dans l'app (`uv run main.py`, CSRF actif) avec deux comptes : recherche → envoyer une demande → pastille chez l'autre compte → accepter → contact des deux côtés → retirer avec confirmation → nouvelle demande → refuser → « Envoyer une demande » de nouveau ; vérifier à l'œil la barre centrée, la pastille et les boutons grisés
- [x] 9.2 Exécuter `/verifier` et obtenir « terminé »

## Workflow follow-up

- Relecture par l'agent `relecteur` avant la PR, qui ferme #22.
- Archiver avec `/opsx:archive` une fois la PR mergée.
