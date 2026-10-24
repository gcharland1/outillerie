# Proposal

## Why

Le schéma des outils existe (changement `schemas-initiaux`), mais aucun écran ne permet à un
voisin d'enregistrer les outils qu'il veut prêter : sans inventaire, il n'y a rien à emprunter
(issue #17). Ces écrans sont aussi les premiers formulaires qui modifient des données au-delà de
la déconnexion, ce qui rend nécessaire une protection CSRF et une structure de routes qui
supporte les fonctionnalités suivantes.

## What Changes

- Lien « Gérer mes outils » dans la barre de navigation d'un utilisateur connecté. L'issue parle
  du profil, mais aucune page de profil n'existe : la barre de navigation en tient lieu.
- Page « Mes outils » : la liste des outils en circulation de l'utilisateur, avec « Modifier » et
  « Retirer » pour chacun, et les liens « Enregistrer un outil » et « Voir mes outils retirés ».
- Formulaire d'enregistrement et de modification : nom, description, état (`functional`,
  `needs_repair`, `out_of_order`, avec des libellés français) et notes privées.
- Retrait en deux temps : une page de confirmation, puis « Confirmer le retrait ». Le retrait sort
  l'outil de la circulation (`is_active = false`) sans l'effacer de la base, parce que les prêts y
  font référence ; la page le dit, et une case permet d'effacer définitivement les notes privées.
- Libellés « Retirer » et « Mes outils retirés » plutôt que « Supprimer » et « Mes outils
  supprimés » (issue #17) : l'outil n'est pas effacé, le mot ne doit pas le laisser croire.
- Page « Mes outils retirés », avec « Remettre en circulation » pour chaque outil ; un retrait
  déjà fait (retour arrière, second envoi) ramène à « Mes outils » au lieu d'une erreur.
- Accès réservé au propriétaire connecté : le visiteur est renvoyé vers la connexion, avec un
  message en français ; l'outil d'un autre compte répond 404.
- Jeton CSRF (Flask-WTF) exigé sur tout formulaire `POST` de l'application, connexion,
  inscription et déconnexion comprises ; un jeton absent ou invalide est refusé (400) avec un
  message.
- Routes regroupées en Blueprints : `tools` (nouvelle) et `auth` (inscription, connexion,
  déconnexion, page de déconnexion, déplacées sans changement d'URL ni de comportement).

## Capabilities

### New Capabilities
- `inventaire`: gestion par un voisin de ses propres outils : liste, enregistrement,
  modification, retrait avec confirmation et effacement facultatif des notes privées, liste des
  outils retirés et remise en circulation, accès réservé au propriétaire.
- `protection-csrf`: refus de toute requête `POST` qui ne porte pas un jeton valide émis par le
  site.

### Modified Capabilities
_Aucune._ La spec `authentification` vit encore dans les changements `fermeture-de-session` et
`schemas-initiaux`, non archivés ; le déplacement des routes dans la Blueprint `auth` ne change
aucune de ses exigences.

## Impact

- Code : `application/app/__init__.py` (enregistrement des Blueprints, `CSRFProtect`,
  `WTF_CSRF_TIME_LIMIT`), nouveaux modules `app/auth.py` et `app/tools.py`, `app/extensions.py`
  (`login_view = "auth.login"`, `login_message`), `base.html` (lien de navigation, jeton du formulaire de
  déconnexion), `login.html`, `sign_up.html`, nouveaux gabarits dans `templates/tools/`.
- Dépendance : `flask-wtf` (`uv add`, `uv.lock` commité).
- Schéma : aucune migration ; les colonnes `name`, `description`, `condition`, `private_notes` et
  `is_active` de `tool` suffisent.
- Tests : nouveaux tests pytest des pages d'outils et du CSRF ; `tests/test_auth.py` vise
  `app.auth.check_password_hash` au lieu de `app.check_password_hash` ; la configuration de test
  désactive le CSRF, sauf dans les tests qui le vérifient.
- ADR : nouveaux 0010 « Protection CSRF par Flask-WTF » et 0011 « Une Blueprint par
  fonctionnalité » (`proposed`, à accepter avant l'implémentation). ADR concernés : 0001 (rendu
  serveur Jinja, sans JavaScript), 0006 (le jeton CSRF vit dans le cookie de session), 0007
  (aucune révision requise), 0008 (photo hors périmètre).

**Hors périmètre**

- Photo de l'outil : téléversement, formats, taille et route `/tools/<id>/photo` (issue #20).
- Validation des formulaires par WTForms (issue #12) : seul `CSRFProtect` de Flask-WTF est adopté
  ici ; la validation des outils reste écrite à la main dans la route.
- Catalogue public des outils et pages d'outil vues par les voisins.
- Effet d'un retrait sur les demandes et prêts en cours : aucun écran de prêt n'existe ; le
  changement qui les crée décidera s'il faut bloquer le retrait ou annuler les demandes.
- Suppression définitive d'un outil et de sa photo ; seules les notes privées peuvent être
  effacées, au retrait.
- Saisie conservée quand une page se rafraîchit vers `/logged-out` après 30 minutes : un
  formulaire laissé ouvert perd sa saisie, même si un autre onglet garde la session ouverte
  (voir design).
- Retour vers la page demandée après la connexion (paramètre `next` de Flask-Login), et plus
  largement trace du contexte d'où un formulaire a été ouvert : à prévoir quand un formulaire
  aura un second point d'entrée.
- Messages de succès : `base.html` affiche tous les messages `flash` comme des erreurs.
