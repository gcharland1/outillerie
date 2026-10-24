# Tasks

## 1. Décisions

- [x] 1.1 Faire accepter par l'utilisateur les ADR 0010 « Protection CSRF par Flask-WTF » et 0011 « Une Blueprint par fonctionnalité » ; vérifier que leur `status` et l'index `docs/decisions/README.md` indiquent `accepted`

## 2. Blueprint `auth` (déplacement sans changement de comportement)

- [x] 2.1 Créer `app/auth.py` (Blueprint `auth`, sans préfixe) et y déplacer `register`, `login`, `logout`, `logged_out` et `_DUMMY_PASSWORD_HASH` ; `logged_out` lit `current_app.permanent_session_lifetime` ; enregistrer la Blueprint dans `create_app()` ; renommer les `url_for` en `auth.*` et `login_view` en `"auth.login"` ; vérifier que `uv run flask routes` liste `auth.register`, `auth.login`, `auth.logout` et `auth.logged_out` aux mêmes URL qu'avant
- [x] 2.2 Faire espionner `app.auth.check_password_hash` par `tests/test_auth.py` ; vérifier que `uv run pytest` passe sans autre modification des tests existants

## 3. Protection CSRF

- [x] 3.1 `uv add flask-wtf` ; créer `csrf = CSRFProtect()` dans `app/extensions.py` et l'initialiser dans `create_app()` ; poser `WTF_CSRF_TIME_LIMIT = None` dans `_initialize_app()` et `WTF_CSRF_ENABLED: False` dans `app_config()` de `tests/conftest.py` ; vérifier que `uv.lock` est modifié et que `uv run pytest` passe
- [x] 3.2 Ajouter le champ caché `csrf_token` aux formulaires de `login.html`, `sign_up.html` et au bouton de déconnexion de `base.html` ; ajouter `@app.errorhandler(CSRFError)` qui rend `csrf_error.html` avec le message de la spec et le statut 400 ; vérifier par des tests pytest que `/login`, `/register` et une page connectée contiennent un champ `csrf_token`
- [x] 3.3 Écrire `tests/test_csrf.py` (app créée avec `WTF_CSRF_ENABLED: True`) pour les scénarios de la spec `protection-csrf` hors outils : connexion et déconnexion sans jeton refusées sans effet, message affiché, connexion acceptée avec le jeton extrait de la page `/login`, acceptée 20 minutes plus tard et refusée avec le message 31 minutes plus tard (fixture `clock` déplacée dans `tests/conftest.py`) ; vérifier que les tests passent

## 4. Blueprint `tools` et navigation

- [x] 4.1 Créer `app/tools.py` (Blueprint `tools`, préfixe `/tools`, `@login_required` sur chaque route), `CONDITION_LABELS` et `_owned_tool(tool_id)` ; l'enregistrer dans `create_app()` ; poser `login_manager.login_message` en français dans `app/extensions.py` ; vérifier que `uv run pytest` passe avec la Blueprint enregistrée
- [x] 4.2 Déplacer `logged_in_client` de `tests/test_navigation.py` vers `tests/conftest.py` et ajouter une fixture pour un second compte `bob` ; vérifier que `uv run pytest` passe
- [x] 4.3 Ajouter le lien « Gérer mes outils » dans `base.html` pour un utilisateur connecté ; vérifier par des tests pytest sa présence connectée et son absence pour un visiteur

## 5. Liste de mes outils

- [x] 5.1 Route `GET /tools/mine` et gabarit `tools/mine.html` (nom, libellé d'état, « Modifier », « Retirer », « Enregistrer un outil », « Voir mes outils retirés », message d'inventaire vide), tri `func.lower(Tool.name), Tool.id` ; vérifier par des tests pytest les scénarios de la spec : redirection d'un visiteur vers `/login` avec « Veuillez vous connecter pour accéder à cette page », outils en circulation seulement, outils des autres absents, ordre alphabétique sans égard à la casse, inventaire vide, libellé « À réparer »

## 6. Enregistrement et modification

- [x] 6.1 Écrire `_read_tool_form(form)` (nettoyage, trois messages d'erreur de la spec, notes vides → `None`) et le gabarit partagé `tools/form.html` (nom, description, `<select>` des états tiré de `CONDITION_LABELS`, notes privées, jeton CSRF) ; vérifier par des tests pytest de `_read_tool_form` chaque message d'erreur, le nom de 250 caractères accepté et les notes faites d'espaces ramenées à `None`
- [x] 6.2 Route `GET, POST /tools/new` ; vérifier par des tests pytest l'outil enregistré (propriétaire, champs, en circulation, redirection, présent dans la liste), l'état `functional` par défaut, les notes vides, et chaque refus de validation (aucun outil créé, message affiché, valeur saisie conservée)
- [x] 6.3 Route `GET, POST /tools/<id>/edit` ; vérifier par des tests pytest le formulaire prérempli, la modification enregistrée et redirigée, l'effacement des notes, la modification invalide qui laisse l'outil intact, le 404 pour un outil de `bob`, un identifiant inconnu et un outil retiré

## 7. Retrait et remise en circulation

- [x] 7.1 Routes `GET /tools/<id>/retire` (gabarit `tools/confirm_retire.html` : nom de l'outil, phrase « L'outil restera enregistré ; vous pourrez le remettre en circulation depuis « Mes outils retirés ». », « Confirmer le retrait » en `POST`, lien d'annulation) et `POST /tools/<id>/retire` ; vérifier par des tests pytest que la page de confirmation affiche la phrase et ne change rien, que la confirmation retire l'outil sans l'effacer de la base et redirige vers une liste qui ne le montre plus, et le 404 avec l'outil de `bob` resté en circulation
- [x] 7.2 Case `erase_private_notes` sur la page de confirmation, affichée seulement si l'outil a des notes ; effacement des notes dans le même `commit` que le retrait ; vérifier par des tests pytest les notes effacées case cochée (nom, description et état conservés), conservées case décochée, et l'absence de la case pour un outil sans notes
- [x] 7.3 Outil du propriétaire déjà retiré : `GET` et `POST /tools/<id>/retire` posent « Cet outil est déjà retiré » et redirigent vers `tools.mine` ; vérifier par des tests pytest le retour sur la page de confirmation après un retrait et le second envoi case cochée, qui laisse l'outil retiré avec ses notes
- [x] 7.4 Route `GET /tools/mine/retired` (gabarit `tools/retired.html`) et `POST /tools/<id>/restore` ; vérifier par des tests pytest la liste des outils retirés seulement, le message « Aucun outil retiré », la remise en circulation qui garde l'état et redirige vers `tools.retired`, l'outil remis en circulation sans notes après un effacement, et le 404 pour l'outil retiré de `bob`
- [x] 7.5 Vérifier par un test pytest que chaque `<form method="post">` des pages d'outils contient le champ `csrf_token`
- [x] 7.6 Ajouter à `tests/test_csrf.py` le scénario « Enregistrement d'outil avec un jeton invalide » : un `POST /tools/new` avec un jeton altéré répond 400 et n'enregistre aucun outil ; vérifier que le test passe

## 8. Vérification

- [x] 8.1 Parcourir dans l'app (`uv run main.py`, CSRF actif) : connexion → « Gérer mes outils » → enregistrer → modifier → retirer en effaçant les notes → « Précédent » ramène à « Mes outils » → « Voir mes outils retirés » → remettre en circulation → déconnexion ; vérifier qu'aucun envoi n'est refusé pour le jeton
- [x] 8.2 Exécuter `/verifier` et obtenir « terminé »

## Workflow follow-up

- Relecture par l'agent `relecteur` avant la PR, qui ferme #17 (pas #20) ; la PR signale que les libellés « Retirer » et « Mes outils retirés » remplacent ceux de l'issue.
- Archiver avec `/opsx:archive` une fois la PR mergée, après l'archivage de `schemas-initiaux` et `fermeture-de-session`.
