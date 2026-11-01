# Design

## Context

Voir proposal.md pour la motivation et specs/ pour les exigences. État actuel :

- `application/app/__init__.py` : toutes les routes (`index`, `register`, `login`, `logout`,
  `logged_out`) sont définies dans `create_app()`, avec le hook `after_request` et le
  `user_loader`. `login_manager.login_view = "login"` (`app/extensions.py`).
- `tests/test_auth.py` espionne `app.check_password_hash` par `monkeypatch.setattr(app_module, ...)` ;
  ce nom vit aujourd'hui dans `app/__init__.py`.
- Les gabarits écrivent les URL en dur (`href="/login"`, `action="/logout"`), sans `url_for`.
- `models/tool.py` porte déjà tout ce qu'il faut : `name` (`String(250)`), `description`,
  `condition` (`ToolCondition`), `private_notes`, `is_active`, `owner_id` indexé. Aucune révision
  Alembic n'est nécessaire.
- `base.html` affiche chaque message `flash` comme une erreur, en rouge.
- Aucun formulaire ne porte de jeton CSRF ; le cookie de session est `SameSite=Lax` (ADR 0006).

## Goals / Non-Goals

**Goals:**
- Un module par fonctionnalité (ADR 0011) : `create_app()` ne fait plus que configurer et
  enregistrer.
- Une seule requête par page, filtrée par propriétaire en SQL : aucun outil d'un autre compte
  n'est chargé puis rejeté en Python.
- Protection CSRF active par défaut pour toute route `POST`, présente et future (ADR 0012).

**Non-Goals:**
- Classes de formulaire WTForms : la validation reste écrite dans la route (issue #12).
- Pagination des listes : un inventaire de voisin tient sur une page.
- Remplacer les URL en dur des gabarits existants par `url_for` : elles restent valides, le
  déplacement ne change aucune URL.

## Decisions

### Blueprints `auth` et `tools`

`app/auth.py` définit `bp = Blueprint("auth", __name__)`, sans préfixe : `register`, `login`,
`logout` et `logged_out` y passent tels quels, avec `_DUMMY_PASSWORD_HASH` et les imports de
`werkzeug.security`. `logged_out` lit la durée par `current_app.permanent_session_lifetime`.
Les `url_for("login")` deviennent `url_for("auth.login")`, `login_view` devient `"auth.login"`.
`index`, le hook `after_request` et le `user_loader` restent dans `create_app()` (ADR 0011).
`tests/test_auth.py` importe `app.auth` et espionne `app.auth.check_password_hash`.

`app/tools.py` définit `bp = Blueprint("tools", __name__, url_prefix="/tools")`. Chaque route
porte `@login_required` ; Flask-Login redirige le visiteur vers `login_view`.

Alternative écartée : un paquet par Blueprint (`app/tools/__init__.py`, `routes.py`) : trop de
fichiers pour sept routes ; l'ADR 0011 prévoit le passage au paquet quand un module grossit.

### Routes

| Méthode | URL | Endpoint | Effet |
|---|---|---|---|
| GET | `/tools/mine` | `tools.mine` | « Mes outils » : outils en circulation |
| GET | `/tools/mine/retired` | `tools.retired` | « Mes outils retirés » |
| GET, POST | `/tools/new` | `tools.new` | formulaire vide ; `POST` crée puis redirige vers `tools.mine` |
| GET, POST | `/tools/<id>/edit` | `tools.edit` | formulaire prérempli ; `POST` modifie puis redirige vers `tools.mine` |
| GET | `/tools/<id>/retire` | `tools.confirm_retire` | page de confirmation |
| POST | `/tools/<id>/retire` | `tools.retire` | `is_active = False`, redirige vers `tools.mine` |
| POST | `/tools/<id>/restore` | `tools.restore` | `is_active = True`, redirige vers `tools.retired` |

`/tools` et `/tools/<id>` restent libres pour le futur catalogue public et la page d'un outil ;
`/tools/<id>/photo` est réservée par l'ADR 0008. Le code et les libellés disent la même chose :
*retire* et `is_active` dans le code, « Retirer » et « Mes outils retirés » à l'écran.
« Supprimer », le mot de l'issue #17, laisserait croire que l'outil et ses notes privées sont
effacés.

Alternative écartée : `DELETE` réel avec `ON DELETE CASCADE` sur les prêts : il effacerait
l'historique des prêts, et la spec `prets` de `schemas-initiaux` interdit de supprimer un outil
qui figure dans un prêt.

### Un outil se cherche par propriétaire et par état

Une fonction du module, `_owned_tool(tool_id)`, exécute
`select(Tool).where(Tool.id == tool_id, Tool.owner_id == current_user.id)` et appelle
`abort(404)` si rien ne revient : un outil d'un autre compte ou inexistant répond 404 de la même
façon, sans révéler qu'il existe. Chaque route vérifie ensuite l'état :

| Route | Outil en circulation | Outil retiré |
|---|---|---|
| `edit` | formulaire | 404 |
| `confirm_retire`, `retire` | confirmation, retrait | `flash` « Cet outil est déjà retiré », redirection vers `tools.mine` |
| `restore` | 404 | remise en circulation |

Le retrait d'un outil déjà retiré redirige parce que c'est le chemin du retour arrière : les pages
connectées portent `Cache-Control: no-store`, donc « Précédent » après un retrait redemande
`GET /tools/<id>/retire` au serveur, qui renvoie l'utilisateur à « Mes outils », d'où il a ouvert
le formulaire. Un second envoi de « Confirmer le retrait » suit le même chemin et ne modifie rien,
pas même les notes privées si la case est cochée.

Alternatives écartées : garder le 404 (le retour arrière mène à une page d'erreur) ; transmettre
le contexte d'origine dans un paramètre `next` validé comme chemin local (inutile tant que
« Retirer » n'a qu'un point d'entrée, à reprendre avec le premier formulaire qui en aura deux) ;
un jeton à usage unique par formulaire, gardé dans la session (code, taille du cookie et ADR en
plus pour un cas que la redirection couvre).

Les listes trient par `func.lower(Tool.name), Tool.id`. L'index `ix_tool_owner_id` sert le filtre ;
aucun index ne s'ajoute pour le tri à cette échelle.

### Validation écrite dans le module, formulaire partagé

`_read_tool_form(form)` renvoie les valeurs nettoyées et un message d'erreur ou `None` :

- `name` et `description` passés par `strip()` ; l'un des deux vide → « Le nom et la description
  sont obligatoires ».
- `name` de plus de 250 caractères après `strip()` → « Le nom ne doit pas dépasser 250
  caractères » (la colonne est un `String(250)` : sans ce contrôle, Postgres lèverait une erreur 500).
- `condition` absente de `ToolCondition` → « L'état choisi est invalide ».
- `private_notes` passé par `strip()` ; vide → `None`.

En cas d'erreur, la route `flash` le message et rend le formulaire avec les valeurs saisies,
statut 200 comme `/register` ; rien n'est écrit en base. Un seul gabarit `tools/form.html` sert
`new` et `edit`, avec un titre et une action reçus de la route.

Les libellés des états vivent dans un dictionnaire `CONDITION_LABELS` de `app/tools.py`
(`ToolCondition` → libellé), passé aux gabarits ; le `<select>` de l'état en est tiré, dans l'ordre
de `ToolCondition`.

### Effacement des notes privées au retrait

`tools/confirm_retire.html` affiche la case `erase_private_notes` seulement si
`tool.private_notes` n'est pas vide. `retire` pose `is_active = False` et, si la case est cochée,
`private_notes = None`, dans le même `commit`. Le chemin « déjà retiré » ignore la case. Une
remise en circulation ne restaure rien : les notes effacées sont perdues.

Alternative écartée : une action « Effacer mes notes » séparée sur la liste des outils retirés.
Le moment du retrait est celui où le propriétaire décide de ce qu'il laisse derrière lui ; une
seconde action ajouterait une route et une confirmation.

### CSRF : `CSRFProtect` global, message dans la mise en page

`csrf = CSRFProtect()` dans `app/extensions.py`, `csrf.init_app(app)` dans `create_app()`. Chaque
formulaire `POST` ajoute `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` :
`login.html`, `sign_up.html`, le bouton de déconnexion de `base.html` et les gabarits d'outils. Le
jeton est signé avec `SECRET_KEY` et sa valeur brute vit dans la session de Flask (ADR 0006) ; un
visiteur reçoit donc un cookie de session dès qu'une page affiche un formulaire.

`@app.errorhandler(CSRFError)` rend `csrf_error.html` (hérite de `base.html`) avec le message de
la spec et le statut 400.

`_initialize_app()` pose `WTF_CSRF_TIME_LIMIT = None` : le jeton vaut autant que la session qui
le porte. Flask refuse tout cookie de session signé depuis plus de `PERMANENT_SESSION_LIFETIME`,
permanent ou non (`flask/sessions.py`, `open_session`) : 30 minutes d'inactivité pour un
utilisateur connecté (ADR 0006), dont le cookie est re-signé à chaque requête, et 30 minutes depuis
l'ouverture de `/login` ou `/register` pour un visiteur, dont le cookie n'est signé qu'à la création
du jeton. Sans limite propre, le jeton d'une page rendue il y a plus d'une heure reste valable
quand un autre onglet a gardé la session ouverte ; la durée par défaut de Flask-WTF (une heure) le
refuserait. Le jeton disparaît avec la session, à la déconnexion (`session.clear()`) ou à
l'expiration.

Alternative écartée : une interface de session propre aux visiteurs, à durée plus longue, pour
qu'une page de connexion reste valable au-delà de 30 minutes. Du code et un ADR pour un cas que le
message de refus (« Rechargez la page ») couvre.

Tests : `app_config()` de `tests/conftest.py` pose `WTF_CSRF_ENABLED: False`, pour que les tests
existants continuent d'envoyer leurs formulaires sans jeton. La fixture `csrf_client` de
`tests/test_csrf.py` pose `WTF_CSRF_ENABLED = True` sur l'app de test (Flask-WTF relit le drapeau
à chaque requête), vérifie les refus de la spec et soumet un formulaire avec le jeton
extrait de la page servie ; les scénarios du formulaire ouvert 20 et 31 minutes avancent
l'horloge de signature avec la fixture `clock`, déplacée de `tests/test_session.py` vers
`tests/conftest.py`.

Alternative écartée : désactiver le CSRF pour `/login` et `/register`. Un CSRF de connexion
ouvrirait la session de l'attaquant dans le navigateur de la victime, qui enregistrerait alors ses
outils dans le mauvais compte.

### Navigation et interface

Pour un utilisateur connecté, le nom d'utilisateur de `base.html` est le `<summary>` d'un
`<details class="account-menu">` qui contient « Gérer mes outils » (`url_for('tools.mine')`), en
simple lien texte : un bouton serait trop lourd dans une liste de menu. « Mon profil » et
« Préférences » l'entourent, grisés et sans lien (`<span aria-disabled="true">`), pour annoncer
les pages à venir sans mener à une erreur 404 ;
« Me déconnecter » reste à côté, hors du menu. `<details>` s'ouvre et se ferme au clic sans
JavaScript (ADR 0001) ; il ne se ferme ni sur un clic ailleurs ni sur Échap, ce qui demanderait un
script et un ADR.

Les règles d'interface vivent dans `.claude/rules/templates.md` (section « Interface ») et leurs
styles dans `app/static/site.css`, chargé après Chota, épinglé à la version `0.9.2` que servait
`@latest` : `site.css` s'appuie sur ses classes. Les attributs `style=` des gabarits y passent.

- Boutons : contour ajouté aux boutons de Chota (transparent par défaut) ; plus de `button outline`,
  qui rendait « Remettre en circulation » blanc sur blanc (texte blanc des `submit` sur fond
  transparent). Actions de page et de ligne en boutons ; « Retirer » et « Confirmer le retrait » en
  `button error`.
- Espacement : `.actions` (flex, `gap: var(--gap)`, marge au-dessus) pour chaque groupe de boutons ;
  la barre `.site-header` est bordée et laisse un écart avant le contenu.

Alternative écartée : un menu avec JavaScript, qui se fermerait sur un clic ailleurs. Il
demanderait un ADR qui complète 0001 pour un seul menu.

`app/extensions.py` pose `login_manager.login_message = "Veuillez vous connecter pour accéder à
cette page."` : sans lui, `@login_required` affiche le message anglais de Flask-Login
(« Please log in to access this page. »).

### Tests

- `tests/conftest.py` reçoit `logged_in_client` (aujourd'hui dans `test_navigation.py`) et un
  second compte, `bob`, pour les scénarios d'accès croisé ; `tests/factories.py` garde `make_tool`.
- `tests/test_tools.py` couvre chaque scénario de la spec `inventaire` par le client de test, et
  vérifie l'état en base après chaque `POST`.

## Risks / Trade-offs

- [Un `url_for` d'une route déplacée garde l'ancien nom] → `BuildError` à l'exécution ; les tests
  existants de l'authentification parcourent chaque route et l'attrapent.
- [Un formulaire `POST` futur oublie le champ caché] → il est refusé (400) dès son premier test :
  l'erreur se voit, elle n'ouvre pas de faille.
- [Les tests désactivent le CSRF] → un gabarit sans jeton passerait les tests d'outils ;
  `test_csrf.py` soumet le formulaire de connexion avec le jeton de sa page, et une vérification
  par gabarit (présence de `csrf_token` dans chaque `<form method="post">`) s'ajoute aux tests des
  outils.
- [Retrait d'un outil qui a une demande ou un prêt en cours] → aucun écran de prêt n'existe ;
  le retrait ne touche pas aux prêts, et le changement des demandes décidera de la règle.
- [Un formulaire d'outil laissé ouvert perd sa saisie] → `base.html` rafraîchit toute page
  connectée vers `/logged-out?reason=inactivity` 30 minutes et 5 secondes après son chargement,
  sans voir la saisie en cours ni un autre onglet qui garde la session ouverte (dans ce cas, la
  page revient sur `/`). Accepté : le rafraîchissement cache les notes privées d'un formulaire de
  modification laissé ouvert sur un ordinateur partagé. Le changement `fermeture-de-session`
  reportait ce point au premier formulaire d'un utilisateur connecté ; il est tranché ici.
- [Des notes « effacées définitivement » subsistent quelque temps] → l'`UPDATE` laisse l'ancienne
  version de la ligne dans la table jusqu'au passage de `VACUUM` (autovacuum), et les sauvegardes
  antérieures la gardent. Accepté à l'échelle d'un voisinage ; la case promet l'effacement des
  notes dans l'application, pas sur le disque.
- [Le `GET` de `/register` ou `/login` crée maintenant un cookie de session pour un visiteur] →
  sans effet sur la connexion : `session.permanent` n'est posé qu'à la connexion.

## Migration Plan

Aucune révision Alembic. `uv add flask-wtf` puis `uv sync` ; `docker compose up --build` reconstruit
l'image. Retour arrière : revenir au commit précédent ; aucune donnée n'est transformée.
