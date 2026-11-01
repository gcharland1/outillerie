# Tasks

## 1. Décision et extensions

- [x] 1.1 Faire accepter par l'utilisateur l'ADR 0016 « Recherche floue des outils avec pg_trgm et unaccent » ; vérifier que son `status` et l'index `docs/decisions/README.md` indiquent `accepted`
- [x] 1.2 Révision Alembic écrite à la main (`uv run flask db revision -m "..."`, nom de fichier ASCII) : `CREATE EXTENSION IF NOT EXISTS pg_trgm` et `unaccent`, `downgrade()` qui les laisse ; `mock_app` (`tests/conftest.py`) crée les deux extensions ; `test_schema.drop_schema()` les supprime ; vérifier par un test pytest qu'après migration `pg_extension` contient `btree_gist`, `pg_trgm` et `unaccent`, et que `uv run flask db upgrade`, `downgrade base`, `upgrade` et `check` passent

## 2. Module `app/catalog.py`

- [x] 2.1 `is_contact` et `visible_tools_query(user, owner_id=None)` selon le design ; vérifier par des tests pytest chaque scénario de « Outils visibles par un contact » (contact, soi-même, non-contact, demande en attente, retiré, hors d'usage, à réparer) au niveau de la requête
- [x] 2.2 `loan_statuses(tool_ids)` en une requête groupée et libellé dérivé (« Prêté jusqu'au <date> », « En attente de prêt », « Disponible ») ; date en français (`catalog.french_date`) ; vérifier par des tests pytest, avec des prêts créés directement en base, chaque scénario de « Statut de prêt » (prêté, en retard, demande, accepté à venir, terminés) et « 3 novembre 2026 »
- [x] 2.3 Filtre « Disponible uniquement » en SQL (`NOT EXISTS` sur les prêts bloquants) ; vérifier par des tests pytest les scénarios « Case cochée » et « Case décochée » au niveau de la requête
- [x] 2.4 Filtre texte (sous-chaîne `unaccent` + `ILIKE` échappé, `word_similarity` ≥ `FUZZY_THRESHOLD`, sous-chaîne seule sous 3 caractères) et tri selon le design ; vérifier par des tests pytest chaque scénario de « Filtre par texte » et « Ordre des outils », et ajuster `FUZZY_THRESHOLD` si un scénario échoue
- [x] 2.5 Vérifier par un test pytest que le nombre de requêtes SQL d'une liste de 1 et de 10 outils est le même (outils, statuts, photos)

## 3. Page « Trouver un outil »

- [x] 3.1 `GET /tools/find` (`tools.find`, `@login_required`), gabarits `tools/find.html` et `tools/_cards.html` (formulaire GET `q` + `available` + « Filtrer », grille, cartes, messages de liste vide), styles `.tool-cards` dans `site.css` ; vérifier par des tests pytest le contenu d'une carte (nom, photo, description, état, statut, « Emprunter » désactivé, « Bientôt disponible »), l'espace réservé sans photo, les notes privées absentes, la description à 125 et à 200 caractères, les quatre messages de liste vide, la case et le texte conservés, et la redirection d'un visiteur
- [x] 3.2 Entrée « Trouver un outil » dans le menu du compte de `base.html` pour un utilisateur connecté ; vérifier par des tests pytest sa présence et son absence pour un visiteur (`tests/test_navigation.py`)

## 4. Page d'un contact

- [x] 4.1 `GET /contacts/<int:user_id>` (`contacts.show`), gabarit `contacts/show.html` (titre « Prénom Nom (@nom) », section « Outils de Prénom Nom » qui inclut `tools/_cards.html`) ; vérifier par des tests pytest chaque scénario de « Page d'un contact » (404 identique pour non-contact, demande en attente, soi-même, inexistant ; coordonnées absentes ; visiteur redirigé) et « Seuls les outils du contact » et « Contact sans outil »
- [x] 4.2 Nom de chaque contact en lien vers sa page dans `contacts/mine.html` ; vérifier par un test pytest le lien « Lien vers la page d'un contact »

## 5. Recherche de type « Outil »

- [x] 5.1 `base.html` : option « Outil » sélectionnable ; `search.results` redirige `type=tool` vers `tools.find` avec `q` sans espaces autour, après le contrôle des 3 caractères ; type inconnu : « Ce type de recherche n'est pas disponible » ; vérifier par des tests pytest les scénarios modifiés de `recherche` et mettre à jour les tests existants qui attendaient « pas encore disponible » et « Outil » non sélectionnable

## 6. Accès à la photo

- [x] 6.1 `can_view_photo` : propriétaire, ou contact pour un outil en circulation et non hors d'usage (relation de contact lue dans `photos.py`) ; vérifier par des tests pytest chaque scénario de « Accès à l'image » (contact, contact et outil retiré, contact et hors d'usage, ancien contact avec l'ancienne étiquette, non-contact, visiteur, sans photo)

## 7. Vérification

- [x] 7.1 Vérifier à la main dans `docker compose up --build`, avec deux comptes en contact et un troisième sans lien : « Trouver un outil », page du contact, filtres et faute de frappe, recherche « Outil » depuis la barre, photo visible, grille sur écran étroit et large
- [x] 7.2 Lancer `/verifier` ; il doit rendre « terminé »

## Workflow follow-up

- Second changement « demande d'emprunt » : page de confirmation, dates, message, création du prêt, notification et page du propriétaire ; active le bouton « Emprunter ».
- Archiver ce changement une fois mergé (`/opsx:archive`).
