# Design

## Context

Voir proposal.md pour la motivation. État actuel, dans `application/app/__init__.py` :

- Flask-Login gère la connexion (`login_user`) ; aucune route ne fait `logout_user`.
- La session vit dans le cookie signé de Flask. Flask refuse à la lecture un cookie dont la
  signature est plus vieille que `PERMANENT_SESSION_LIFETIME` (`flask/sessions.py`, `open_session`),
  par défaut 31 jours. La session n'est pas marquée permanente : le cookie disparaît à la fermeture
  du navigateur, mais une copie reste valide 31 jours.
- `SESSION_COOKIE_SAMESITE` vaut `None` (défaut Flask) ; `HttpOnly` est déjà actif par défaut.
- Il n'y a pas encore de jeton CSRF (issue #12).
- Les erreurs passent tantôt par `flash` (connexion), tantôt par une variable `error` que
  `sign_up.html` n'affiche pas (inscription).

## Goals / Non-Goals

**Goals:**
- Couvrir la spec `authentification` sans nouvelle dépendance ni migration.
- Rendre la durée d'inactivité configurable pour la tester sans attendre 30 minutes.
- Ne pas introduire de JavaScript : le rendu serveur de l'ADR 0001 suffit.

**Non-Goals:**
- Toucher au modèle `User` ou au stockage des sessions.
- Refondre les formulaires : WTForms et la validation viennent avec l'issue #12.

## Decisions

### Sessions dans le cookie signé, expiration glissante de 30 minutes

`PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)`, `session.permanent = True` à la connexion,
et `SESSION_REFRESH_EACH_REQUEST` laissé à sa valeur par défaut (`True`) : chaque requête
re-signe le cookie et repousse l'échéance. Comme Flask vérifie l'âge de la signature, un cookie
copié puis réutilisé après 30 minutes d'inactivité est rejeté par le serveur.

Alternative écartée : sessions côté serveur (table de sessions ou jeton par utilisateur) pour
révoquer une copie du cookie dès la déconnexion. Cela ajoute un schéma ou une dépendance pour
un risque déjà borné à 30 minutes ; décision prise avec l'utilisateur. Elle sera consignée dans
un ADR (`/adr`), puisqu'elle contraint toute future fonction de révocation.

### Déconnexion par `POST /logout` et `session.clear()`

La route appelle `logout_user()` puis vide la session et redirige vers `/logged-out`. Le bouton
est un petit formulaire `POST` dans la navigation. Elle n'exige pas d'être connecté : un visiteur
qui l'appelle est simplement redirigé.

Pourquoi `POST` : un lien `GET` peut être déclenché par une image ou un préchargement d'un site
tiers. Sans jeton CSRF, c'est `SameSite=Lax` qui empêche un `POST` intersite de porter le cookie.

### Page `/logged-out` commune à la déconnexion et à l'expiration

Une seule page, dont le message dépend du paramètre `reason` (`inactivity`, sinon le message de
déconnexion par défaut ; toute autre valeur est ignorée). Le paramètre ne choisit qu'un texte
parmi deux : il n'est jamais réaffiché tel quel. Si l'utilisateur est encore connecté, la page
redirige vers `/` : c'est ce qui gère le cas de plusieurs onglets.

Alternative écartée : un message `flash` sur `/`. Le rafraîchissement automatique ne peut pas
poser de `flash` lui-même, et la session expirée ne peut plus le transporter.

Le message d'expiration calcule ses minutes depuis `PERMANENT_SESSION_LIFETIME`, comme le délai
du rafraîchissement, pour rester juste si la durée change.

### Rafraîchissement automatique par `<meta http-equiv="refresh">`

`base.html` émet, dans sa branche « utilisateur connecté » seulement,
`<meta http-equiv="refresh" content="<durée + 5>;url=/logged-out?reason=inactivity">`, la durée
étant lue depuis `PERMANENT_SESSION_LIFETIME` : une seule source pour le serveur et la page.

- Délai relatif au chargement de la page : aucune dépendance aux horloges du client et du
  serveur. La page est chargée juste après la signature du cookie ; les 5 secondes de marge
  garantissent que le serveur considère la session expirée quand la redirection arrive.
- Fonctionne sans JavaScript ; le navigateur gère lui-même le délai.
- Plusieurs onglets : un onglet inactif est rafraîchi vers `/logged-out` ; si un autre onglet a
  gardé la session vivante, la page renvoie vers `/`.

Alternative écartée : minuteur JavaScript (fichier sous `static/js/`, durée passée par un
attribut `data-`). Son seul avantage est d'accueillir plus tard un avertissement, un bouton
« Rester connecté » ou une vérification de la session avant de quitter la page, tous hors
périmètre. Il introduirait le premier JavaScript du site, donc un ADR, sans gain aujourd'hui ;
ce choix sera fait avec son besoin réel.

### Pages connectées en `Cache-Control: no-store`

Un hook `after_request` ajoute `Cache-Control: no-store` à toute réponse quand l'utilisateur est
connecté. `no-store` empêche aussi la restauration de la page depuis le cache d'historique
(bfcache) : après une déconnexion, « Précédent » redemande la page au serveur, qui sert la
version visiteur.

Alternative écartée : `no-store` sur toutes les réponses. Plus simple, mais prive inutilement
les pages de visiteur du cache.

### Durée lue depuis la configuration

La factory fixe `PERMANENT_SESSION_LIFETIME` à 30 minutes ; la config de test peut la remplacer
(par exemple 1 seconde) pour tester l'expiration. Les tests d'expiration contrôlent l'horloge
utilisée pour signer le cookie plutôt que d'attendre réellement.

### Messages d'erreur par `flash`

L'inscription passe au même mécanisme que la connexion : `flash` puis rendu par `base.html`.
Les textes sont harmonisés : « Le nom d'utilisateur est déjà utilisé » (au lieu de « nom
d'usager ») et « Le nom d'utilisateur ou le mot de passe est invalide » (accord corrigé).

### Vérification de hachage factice à la connexion

Quand le nom d'utilisateur est inconnu, la route vérifie quand même le mot de passe soumis contre
un hachage factice calculé une fois au démarrage, avec la même méthode que les vrais. Les deux
échecs prennent alors un temps comparable et rendent la même réponse.
Les confirmations (déconnexion, expiration) passent par la page `/logged-out`, pas par `flash`.

## Risks / Trade-offs

- [Une copie volée du cookie reste valide jusqu'à 30 minutes après la dernière requête, même
  après la déconnexion] → acceptée et consignée dans l'ADR ; à revoir si le site stocke des
  données sensibles.
- [Sans jeton CSRF, la protection du `POST /logout` repose sur `SameSite=Lax`, que tous les
  navigateurs récents appliquent] → le jeton CSRF arrive avec l'issue #12.
- [Le rafraîchissement peut arriver en retard (onglet en arrière-plan, ordinateur en veille)] →
  sans conséquence : la redirection arrive plus tard, et le serveur a déjà fermé la session.
- [Un onglet inactif est renvoyé vers `/` même quand un autre onglet a gardé la session vivante :
  il quitte sa page et perd toute saisie non soumise] → sans effet tant qu'aucun formulaire
  n'exige d'être connecté ; à revoir avec le premier, par exemple en vérifiant la session avant
  de quitter la page (hors périmètre).
- [La redirection d'un onglet inactif est une requête : si un autre onglet a gardé la session
  vivante, elle la prolonge une fois de 30 minutes] → pas de prolongation sans fin : au tour
  suivant, sans autre activité, la session est expirée et l'avis s'affiche.
- [Le rafraîchissement n'a pas de test automatisé de bout en bout] → pytest vérifie la balise et
  son délai ; le déclenchement se vérifie à la main avec une durée courte.
- [Un navigateur peut être configuré pour ignorer `meta refresh`] → la page reste affichée ;
  l'expiration côté serveur s'applique quand même au clic suivant.
- [Le cookie n'a pas l'attribut `Secure` tant que le site est servi en HTTP] → à activer au
  déploiement HTTPS (issue #5).
- [Les sessions ouvertes avant le déploiement ne sont pas permanentes, donc pas re-signées à
  chaque requête : Flask les rejette 30 minutes après leur dernière écriture, même en activité]
  → l'utilisateur se reconnecte une fois ; rien à migrer.
