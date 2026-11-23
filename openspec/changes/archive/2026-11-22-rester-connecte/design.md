# Design

## Context

Voir [proposal.md](proposal.md) ; décisions et sources dans [questions.md](questions.md). La session
vit dans le cookie signé de Flask, permanent, 30 minutes glissantes (`PERMANENT_SESSION_LIFETIME`,
re-signé à chaque requête). Flask-Login 0.6.3 sait poser un cookie « remember » (`remember_token`)
qui rouvre la session quand celle-ci a disparu : sa valeur est `get_id()` signé par `SECRET_KEY`,
sans date ; seul l'attribut `Expires` le borne, côté navigateur.

## Goals / Non-Goals

**Goals:**
- Garder l'expiration de 30 minutes intacte pour qui ne coche pas la case.
- Préparer la révocation de toutes les sessions d'un compte (issue #61) sans l'offrir encore.

**Non-Goals:**
- Un terme vérifié par le serveur pour le cookie persistant (limite acceptée, question 5).
- Prolonger le jeton CSRF d'une session restée connectée (question 3).

## Decisions

### Cookie « remember » de Flask-Login (ADR 0028)
`login_user(user, remember=True)` si la case vaut `"1"`. Configuration dans `_initialize_app` :
`REMEMBER_COOKIE_DURATION = timedelta(days=30)`, `REMEMBER_COOKIE_SAMESITE = "Lax"`,
`REMEMBER_COOKIE_SECURE = environment != "development"`, `REMEMBER_COOKIE_HTTPONLY = True` (déjà le
défaut, écrit pour la spec). Sans ces valeurs, Flask-Login pose 365 jours, `SameSite=None`, sans
`Secure`. Écartés : une interface de session maison (allonge aussi les sessions de visiteur), une
table de jetons par appareil (schéma plus lourd pour un risque faible, question 2).

### Case décochée
`login_user(user)` puis `session["_remember"] = "clear"` : `login_user` sans `remember` laisse en
place le cookie persistant d'une connexion antérieure (navigateur partagé, question 9).

### Glissement de 30 jours
`REMEMBER_COOKIE_REFRESH_EACH_REQUEST` reste désactivé : il poserait le cookie pour toute session
qui porte `_user_id`, case décochée comprise. Un `after_app_request` du blueprint `auth`, enregistré
par `create_app` après `login_manager.init_app` donc exécuté avant celui de Flask-Login (ordre
inverse), décide quand `_remember` est absent de la session :
- cookie présent (`flask_login.login_remembered()`) et utilisateur authentifié : `"set"`, le cookie
  repart pour 30 jours ;
- cookie présent et utilisateur anonyme (cookie refusé par le chargeur : ancien format, autre
  version, compte supprimé) : `"clear"`, pour qu'il ne soit pas relu à chaque requête (question 20).
  Ce cas couvre aussi un cookie laissé après `logout_user()` si la marque de Flask-Login était perdue.

### Session rétablie par le cookie
Le signal `user_loaded_from_cookie` met `session.permanent = True`, comme la connexion : la session
rétablie est re-signée à chaque requête et expire comme une autre. Elle est neuve : son jeton CSRF
aussi, d'où le refus d'un formulaire ouvert avant (questions 3 et 25).

### Version de session
Colonne `user.session_version`, `Integer NOT NULL`, `server_default="0"` et `default=0` dans le
modèle (comme `models/tool.py`). `User.get_id()` renvoie `"<id>"` à la version 0 et
`"<id>:<version>"` au-delà ; il sert à la session et au cookie persistant. `load_user` lit `"<id>"`
comme la version 0 et renvoie `None` si le format est inattendu, si la version diffère ou si le
compte est supprimé (ADR 0023). Aucune fonction ne change encore la version (issue #61) : tout
identifiant émis reste `"<id>"`, que l'image précédente sait lire (question 16). Écarté :
`"<id>:<version>"` dès la version 0, qui faisait échouer en 500 l'image précédente sur chaque
session et chaque cookie persistant après un retour arrière automatique (ADR 0017).

### Avis d'expiration
Un context processor expose `expires_on_inactivity` : utilisateur authentifié et
`login_remembered()` faux. `base.html` n'émet la balise `refresh` que dans ce cas (pas de logique
métier dans les gabarits). Juste après une connexion case cochée, la redirection vers `/` porte déjà
le cookie : la balise est absente dès la première page.

### Déconnexion et suppression
`auth.logout` et `profile._logged_out_after_deletion` appellent `session.clear()` puis
`logout_user()`. L'ordre inverse, décidé par `fermeture-de-session` et `modification-du-profil`,
effaçait la marque `_remember = "clear"` que pose `logout_user()`, et le cookie persistant survivait
(question 18). Les appels de `logout_user()` seuls (`profile.py:76,93`, `tools.py:189`) restent
tels quels (question 19).

### Case dans le formulaire
`login.html` : case `name="remember" value="1"` sous le mot de passe, classe `.checkbox` du site ;
l'échec de connexion repasse son état au gabarit.

## Risks / Trade-offs

- [Copie volée du cookie persistant valide sans terme côté serveur] → limite acceptée (ADR 0028) ;
  la suppression du compte la coupe ; issue #61 pour la rotation de `session_version`.
- [Rotation de `FLASK_SECRET_KEY`] → invalide aussi tous les cookies persistants et les liens de
  confirmation (ADR 0027) ; à faire en connaissance de cause.
- [Première version non nulle, issue #61] → émettra `"<id>:<version>"`, illisible pour une image
  antérieure à ce changement : l'issue #61 devra le prendre en compte dans son retour arrière.
- [`SESSION_PROTECTION`] → défaut `basic`, sans effet ici ; pas une protection contre le vol
  (question 24).
- [Tests] → la fixture `clock` fige l'âge du cookie de session, pas l'`Expires` du cookie persistant,
  calculé avec l'heure réelle : les 30 jours se testent par les attributs du `Set-Cookie`, la reprise
  après 30 minutes avec `clock`.
- [`datetime.utcnow()` de Flask-Login] → `DeprecationWarning` sous Python 3.13, sans effet.

## Migration Plan

Révision Alembic « Utilisateurs : version de session », `down_revision = "8af64a316b37"`, qui ajoute
la colonne avec `server_default` (expansion seule, ADR 0007) ; `downgrade` la supprime.

Retour arrière d'image (ADR 0017) : l'ancien code ignore la colonne, et son chargeur
(`int(user_id)`) lit les identifiants `"<id>"` des sessions et des cookies persistants posés ;
Flask-Login lit ces cookies même sans configuration, donc un utilisateur resté connecté le reste,
avec l'expiration d'inactivité de l'ancien code dès que la session expire et que le cookie la rouvre.
