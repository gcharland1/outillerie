# Tasks

## 1. Accueil réservé et healthcheck

- [x] 1.1 Vue `index` : redirection d'un visiteur vers `auth.login` (sans `?next=`, sans message) ; `index.html` minimal pour l'utilisateur connecté ; tests de `test_main.py`, `test_navigation.py` (navigation, feuille de style, `visitor_pages`, cache) déplacés de `/` vers `/login` ; `is_logged_in` (`test_csrf.py`), `test_session.py` et `test_auth.py` repèrent la connexion par le menu du compte, plus par « Rebonjour » ; vérifier par des tests pytest les scénarios « Utilisateur connecté » et « Visiteur » de « Tableau de bord de l'utilisateur connecté », et ceux de « Pages connectées non mises en cache »
- [x] 1.2 `compose.yaml` : healthcheck sur `/login` ; `README.md` (« page de connexion servie ») ; test « visiteur `GET /login` → 200 » ; vérifier `docker compose up --build` jusqu'à `healthy`

## 2. Tri de « Trouver un outil » et dernier emprunt

- [x] 2.1 Paramètre `sort` (valeurs énumérées, défaut `relevance`) lu hors de `filters` dans `catalog.tool_list` ; ordres `added-*` et `borrowed-*` dans `visible_tools`, sous-requête du dernier emprunt (`(*OUT, RETURNED)`, `max(start_date)`), départage par `Tool.id`, `nulls_last` / `nulls_first` ; vérifier par des tests pytest chaque scénario de « Ordre des outils »
- [x] 2.2 Menu « Trier par » dans le formulaire `tool-filters` (`<select name="sort">`, option sélectionnée) ; `sort` transmis par l'origine d'une demande d'emprunt (`_origin`, `_origin_url`, `loans/confirm.html`) ; vérifier par des tests pytest « Tri sur la page d'un contact », « Tri inconnu » et le retour trié de « Demande envoyée »
- [x] 2.3 Date du dernier emprunt lue en lot dans `tool_cards` ; carte extraite dans `tools/_card.html` avec « Dernier emprunt le <date> » seulement si elle existe ; vérifier par des tests pytest « Dernier emprunt », « Remise à confirmer comptée », « Jamais emprunté », et que les scénarios existants de « Carte d'un outil » passent

## 3. Retour à l'accueil après une action

- [x] 3.1 Origine `home` / `mine` pour les actions de prêt (`act`, tous les retours) et les réponses de contact (`accept`, `refuse`), défaut `mine` ; origine `home` pour une demande d'emprunt ; boutons de prêt extraits de `loans/mine.html` en macro avec l'origine en champ caché ; message de succès de chaque action (table de `design.md`) ; vérifier par des tests pytest les scénarios d'origine (accueil, inconnue, en double) de « Actions réservées aux parties », « Réponse du propriétaire », « Retrait d'une demande par l'emprunteur », « Demande qui n'existe plus » et « Envoi d'une demande », et ceux de « Messages de succès »

## 4. Sections du tableau de bord

- [x] 4.1 `loans.dashboard` (filtres SQL, rang de catégorie, date de fin, départage par id, 5 lignes plus une par groupe) et section « Gestion des prêts » avec « Voir tous mes prêts » sous chaque groupe qui dépasse ; vérifier par des tests pytest (date du site fixée) chaque scénario de « Contenu de « Gestion des prêts » », « Ordre de « Gestion des prêts » », « Tri dans une catégorie de « Gestion des prêts » » et « Lignes de « Gestion des prêts » limitées »
- [x] 4.2 Style de retard dans `site.css`, appliqué sur l'accueil et sur « Mes prêts » ; vérifier par des tests pytest « Ligne en retard » et « Retard en rouge »
- [x] 4.3 `contacts.received_requests` (extraite de `contacts.mine`) et `contacts.recent_contacts` (30 jours) ; section « Gestion des contacts » avec lien vers « Mes contacts » ; vérifier par des tests pytest chaque scénario de « Gestion des contacts »
- [x] 4.4 `catalog.recent_tools` (visibilité de `_visible`, `created_at` depuis 30 jours, plus récent d'abord, 7 lus) et section « Nouveaux outils » avec « Voir plus » vers `tools.find` trié `added-desc` ; vérifier par des tests pytest chaque scénario de « Nouveaux outils » et de « Date qui rend un outil nouveau »
- [x] 4.5 Messages des sections vides ; vérifier par des tests pytest « Nouveau compte » et « Contacts sans nouvel outil », et `/` dans `test_no_page_says_voisin`
- [x] 4.6 Vérifier par un test pytest le nombre de requêtes de `GET /` (constant quand le nombre de prêts, de contacts et d'outils augmente) et le scénario « Jeton manquant » de « Retour à l'accueil après une action »

## 5. Vérification

- [x] 5.1 QA manuelle dans `docker compose up --build`, avec trois comptes : accueil vide, demandes et prêts dans chaque catégorie, retard (date de fin passée en base), actions depuis l'accueil, contact noué, nouveaux outils et « Voir plus », tri de « Trouver un outil » ; y joindre la tâche 7.1 restée ouverte de `gestion-des-prets`
- [x] 5.2 Exécuter `/verifier` jusqu'à « terminé »
