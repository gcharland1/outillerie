# Questions — rester connecté

Issue traitée : #56 « Donner l'option aux utilisateurs de rester connecté », livrée en lot (`/traiter-issue lots`,
ADR 0025). Entrées : l'issue et son dernier commentaire de tri (`understood`), qui tranche les questions
`utilisateur`.

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 1 | Durée de « rester connecté » ? | 30 jours glissants, prolongés à chaque visite | Commentaire de l'utilisateur sur #56 | utilisateur |
| 2 | Mécanisme et révocation ? | Cookie « remember » de Flask-Login et colonne `user.session_version` renvoyée par `get_id` | Commentaire de l'utilisateur sur #56 | utilisateur |
| 3 | Formulaire ouvert plus de 30 minutes ? | Le refus CSRF (« Rechargez la page ») est accepté ; ADR 0012 intact | Commentaire de l'utilisateur sur #56 | utilisateur |
| 4 | « Déconnecter tous mes appareils » ? | Hors périmètre : issue #61 | Commentaire de l'utilisateur sur #56 | utilisateur |
| 5 | Terme des 30 jours côté serveur ? | Aucun : le cookie Flask-Login n'a pas de date ; une copie volée reste valide jusqu'à la suppression du compte ou une rotation de `session_version` (#61). Limite écrite dans l'ADR et la spec | Commentaire de l'utilisateur sur #56 | utilisateur |
| 6 | Case décochée ? | Expiration actuelle de 30 minutes d'inactivité, aucun cookie persistant émis | ADR 0006 ; tri de #56 | convention |
| 7 | Libellé et place de la case ? | « Rester connecté sur cet appareil », décochée, sous le mot de passe, conservée après un échec | `.claude/rules/templates.md` ; tri de #56 | convention |
| 8 | Prolonger le cookie persistant ? | Seulement s'il est déjà présent et que l'utilisateur est connecté ; `REMEMBER_COOKIE_REFRESH_EACH_REQUEST` le poserait aussi pour une case décochée | `flask_login/login_manager.py:448-462` | convention |
| 9 | Connexion case décochée sur un appareil qui porte un cookie persistant ? | Le cookie est effacé (navigateur partagé) | `flask_login/utils.py` (`login_user` sans `remember` ne l'efface pas) ; tri de #56 | convention |
| 10 | Attributs du cookie persistant ? | `HttpOnly`, `SameSite=Lax`, `Secure` hors développement | Spec authentification « Protection du cookie de session » ; `app/__init__.py` | convention |
| 11 | Avis d'expiration pour une session restée connectée ? | Aucun : pas de balise `refresh` | Issue (« aucune déconnexion automatique ») | convention |
| 12 | « Me déconnecter » et suppression du compte ? | Effacent le cookie persistant : `session.clear()` avant `logout_user()` | `app/auth.py:122-123`, `app/profile.py:184-185`, `flask_login/utils.py` | convention |
| 13 | Compte supprimé sur un appareil resté connecté ? | Visiteur : le chargeur refuse un compte supprimé | ADR 0023 ; `app/__init__.py:87-91` | dépôt |
| 14 | Cookie persistant expiré ? | Retour à la connexion, sans message | ADR 0006 | convention |
| 15 | `session_version` ? | Entier `NOT NULL`, `server_default` 0, colonne ajoutée seule | ADR 0007 ; `.claude/rules/migrations.md` | convention |
| 16 | Ancien format d'identifiant de session au déploiement ? | Visiteur, jamais d'erreur ; les sessions en cours (30 minutes au plus) sont coupées une fois | Tri de #56 | convention |
| 17 | Session rétablie par le cookie persistant ? | Marquée permanente, pour qu'elle soit re-signée à chaque requête comme une session ouverte à la connexion | `flask/sessions.py` ; `flask_login/login_manager.py:413-425` | convention |
| 18 | Ordre `logout_user()` / `session.clear()` ? | `session.clear()` d'abord : l'ordre inverse, décidé par `fermeture-de-session` et `modification-du-profil`, effaçait la marque qui supprime le cookie persistant | `openspec/changes/archive/2026-11-01-fermeture-de-session/design.md:42-44` ; `flask_login/utils.py:224-228` | convention |
| 19 | Autres appels de `logout_user()` (compte supprimé en cours de requête) ? | Inchangés : sans `session.clear()` après, ils effacent déjà le cookie persistant | `app/profile.py:76,93`, `app/tools.py:189` | dépôt |
| 20 | Cookie persistant refusé par le chargeur (ancien format, autre version, compte supprimé) ? | Effacé par la réponse, pour ne pas être relu à chaque requête | `flask_login/login_manager.py:413-425` | convention |
| 21 | Valeur de case falsifiée ou absente ? | Toute valeur autre que celle de la case vaut décochée, sans erreur | grill-spec §3 | convention |
| 22 | Connexion par-dessus une session ouverte, `/login` ouvert par un utilisateur connecté ? | Inchangé, hors périmètre | `app/auth.py:59-74` | convention |
| 23 | Compte non confirmé (issue #50) ? | Peut rester connecté comme tout compte | `app/auth.py:68` ; ADR 0027 | convention |
| 24 | `SESSION_PROTECTION` ? | Défaut `basic`, sans effet ici (aucune route `fresh_login_required`) ; ce n'est pas une protection contre un cookie volé | `flask_login/login_manager.py:385-411` | dépôt |
| 25 | Onglet restauré par le navigateur après expiration de la session ? | Son POST est refusé (« Rechargez la page »), comme à la question 3 | ADR 0012 ; `app/__init__.py` (`WTF_CSRF_TIME_LIMIT`) | convention |
| 26 | Specs touchées ? | `authentification` ; `deploiement` (`Secure`) ; `profil` (fin de session après la suppression) | `openspec/specs/deploiement/spec.md:36-46`, `openspec/specs/profil/spec.md:251-258` | dépôt |
