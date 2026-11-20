## 1. Schéma (passe *expand*)

- [x] 1.1 `username` nullable dans le modèle ; révision Alembic (nom de fichier ASCII) avec `downgrade` qui remplit `'user' || id` puis remet `NOT NULL` ; `flask db check` vide ; `docs/schema.md` régénéré ; `test_schema.py` adapté

## 2. Tests par courriel

- [x] 2.1 Fixtures `user`, `bob`, `carole` et fabriques (`make_user`, `user_id`, `user_id_in`) par courriel ; un seul `login` commun dans `conftest` ; connexions des tests par `email`

## 3. Connexion et inscription

- [x] 3.1 `/login` par courriel (casse et espaces ignorés, hachage factice gardé, courriel réaffiché) ; tests de chaque scénario de « Connexion »
- [x] 3.2 `/register` sans nom d'utilisateur, courriel enregistré sans espaces ; tests de « Création de compte » et « Courriel unique »

## 4. Affichage et tri

- [x] 4.1 Menu du compte « Prénom Nom », coupé s'il est trop long ; tests de « État de connexion dans la navigation » et des menus (`inventaire`, `outils-des-contacts`, pastille)
- [x] 4.2 `text_search.sort_key` ; « Mes contacts » et recherche triées par prénom, nom, id ; recherche sur le prénom suivi du nom seulement ; tests de « Correspondance des utilisateurs » et « Liste de mes contacts »
- [x] 4.3 Colonnes « Nom d'utilisateur » retirées (recherche, `contacts/_requests.html`, « Mes contacts ») ; titres de la page d'un contact et de sa confirmation de retrait ; tests de « Informations affichées », « Demandes reçues », « Page d'un contact »

## 5. Fin

- [x] 5.1 `git grep -i username` hors `migrations/` ne trouve que la colonne du modèle, `uq_user_username` dans `test_schema.py`, le jeton HTML `autocomplete="username"` du champ courriel et les tests qui vérifient son absence
- [x] 5.2 `/verifier` rend « terminé »
