# Proposal

## Why

Un utilisateur connecté n'a aucun moyen de se déconnecter, et sa session reste valide jusqu'à
31 jours (valeur par défaut de Flask), même sur un ordinateur partagé laissé ouvert (issue #11).
L'inscription et la connexion livrées dans la PR #13 n'ont pas non plus de spec : ce changement
spécifie l'ensemble du cycle de session avant de fermer la PR.

## What Changes

- Bouton « Me déconnecter » dans la barre de navigation pour un utilisateur connecté ; il ferme
  la session par une requête `POST /logout`.
- Page de déconnexion `/logged-out`, qui confirme la fin de la session : « Vous êtes déconnecté »
  ou « Votre session a expiré après 30 minutes d'inactivité ».
- Expiration automatique de la session après 30 minutes sans requête, vérifiée côté serveur.
- Avis d'expiration : une page laissée ouverte se rafraîchit d'elle-même vers la page de
  déconnexion au terme du délai, sans JavaScript.
- Pages servies à un utilisateur connecté non mises en cache, pour que le retour arrière après
  une déconnexion ne réaffiche pas son contenu sur un ordinateur partagé.
- Barre de navigation selon l'état de connexion : « Connexion » et « Inscription » pour un
  visiteur, nom d'utilisateur et « Me déconnecter » pour un utilisateur connecté.
- Cookie de session `SameSite=Lax` et `HttpOnly`.
- Spec du comportement existant d'inscription et de connexion, avec deux corrections :
  le message « nom d'utilisateur déjà utilisé » s'affiche réellement sur la page d'inscription
  (il est aujourd'hui transmis au gabarit mais jamais rendu), et le message d'échec de connexion
  est corrigé.

## Capabilities

### New Capabilities
- `authentification`: comptes utilisateurs et cycle de session — inscription, connexion,
  déconnexion, page de déconnexion, expiration par inactivité et son avis dans le navigateur,
  pages connectées non mises en cache, état de connexion affiché.

### Modified Capabilities
_Aucune._

## Impact

- Code : `application/app/__init__.py` (routes `/logout` et `/logged-out`, configuration de
  session, en-tête de cache), `application/app/templates/base.html`, `sign_up.html`, `login.html`,
  nouveau gabarit de la page de déconnexion.
- Tests : nouveaux tests pytest pour l'inscription, la connexion, la déconnexion et l'expiration.
- Aucune dépendance ni migration : Flask et Flask-Login suffisent.
- ADR : nouvel ADR à écrire via `/adr` — sessions dans le cookie signé de Flask, sans révocation
  côté serveur, bornées par l'expiration d'inactivité. ADR concernés : 0001 (Flask, rendu serveur
  Jinja ; le changement n'introduit aucun JavaScript), 0002 (PostgreSQL ; tests sur Postgres).

**Hors périmètre**

- Validation des formulaires et jeton CSRF : issue #12 (WTForms). D'ici là, `SameSite=Lax`
  empêche un site tiers de déclencher la déconnexion par un `POST`, mais pas un CSRF de connexion
  sur `/login` (risque décrit dans le design).
- Cacher à l'inscription qu'un nom d'utilisateur est déjà pris.
- Vérification de la confirmation du mot de passe et règles de mot de passe : issue #12.
- Révocation côté serveur d'un cookie de session copié.
- Avertissement avant l'expiration (compte à rebours, bouton « Rester connecté ») : il
  demanderait du JavaScript et son propre ADR.
- Garder un onglet inactif sur sa page quand un autre onglet a gardé la session vivante (il est
  aujourd'hui renvoyé vers `/`) : à revoir avec le premier formulaire soumis par un utilisateur
  connecté, seul cas où la saisie en cours serait perdue.
- Message d'expiration sur un lien cliqué après l'expiration (page restée ouverte hors du
  rafraîchissement) : un cookie expiré est rejeté silencieusement par Flask et ne se distingue
  pas d'un visiteur jamais connecté.
- Fonction « Se souvenir de moi » et attribut `Secure` du cookie (HTTPS, issue #5 de déploiement).
