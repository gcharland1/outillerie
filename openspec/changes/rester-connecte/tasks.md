# Tasks

## 1. Schéma et modèle

- [x] 1.1 `models/user.py` : `session_version`, `Integer NOT NULL`, `default=0`, `server_default="0"` ; `get_id()` renvoie `"<id>:<version>"` ; test dans `tests/test_user_model.py`
- [x] 1.2 Révision `uv run flask db migrate -m "Utilisateurs : version de session"` sur une base dédiée, `down_revision = "8af64a316b37"` ; relire, renommer en ASCII ; `downgrade` supprime la colonne ; `uv run flask db check` vide
- [x] 1.3 Régénérer `docs/schema.md` (`uv run paracelsus inject ../docs/schema.md`) ; `--check` passe
- [x] 1.4 `tests/test_schema.py` : comptes existants à 0 après l'`upgrade`, aller-retour `downgrade`/`upgrade`

## 2. Chargeur et cookie persistant

- [x] 2.1 `load_user` : découpe `"<id>:<version>"`, `None` pour un format inattendu (dont l'ancien `"<id>"`), une autre version ou un compte supprimé ; tests (ancienne session traitée en visiteur sans erreur, version changée en base, compte supprimé)
- [x] 2.2 `_initialize_app` : `REMEMBER_COOKIE_DURATION` 30 jours, `REMEMBER_COOKIE_SAMESITE` `Lax`, `REMEMBER_COOKIE_SECURE` hors `development`, `REMEMBER_COOKIE_HTTPONLY` ; tests des attributs en `production` et en `development`
- [x] 2.3 `after_request` (prolonge un cookie présent pour un utilisateur authentifié, efface un cookie refusé) et signal `user_loaded_from_cookie` (session permanente) ; tests : reprise après 31 minutes avec `clock`, cookie renouvelé pour 30 jours à chaque page, cookie refusé effacé

## 3. Connexion et déconnexion

- [x] 3.1 `login.html` : case « Rester connecté sur cet appareil » (`name="remember" value="1"`, classe `.checkbox`), sous le mot de passe ; `auth.login` : `remember` si la valeur est `"1"`, sinon `_remember = "clear"` ; état repassé au gabarit après un échec ; tests (case décochée par défaut, cochée pose le cookie, décochée n'en pose aucun et efface celui d'un autre compte, valeur inattendue, échec case cochée)
- [x] 3.2 `auth.logout` et `profile._logged_out_after_deletion` : `session.clear()` puis `logout_user()` ; tests : déconnexion et suppression d'un compte resté connecté effacent le cookie, cookie persistant copié d'un compte supprimé traité en visiteur

## 4. Avis d'expiration

- [x] 4.1 Context processor `expires_on_inactivity` ; `base.html` n'émet la balise `refresh` que s'il est vrai ; tests (session sans case : balise ; resté connecté : aucune, dès la page qui suit la connexion ; visiteur : aucune)

## 5. Fin

- [x] 5.1 `/verifier` rend « terminé »
