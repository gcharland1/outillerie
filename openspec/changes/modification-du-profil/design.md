# Design

Décisions et sources : [questions.md](questions.md). Décision d'architecture : ADR 0023 (`proposed`).
Motivation : [proposal.md](proposal.md) ; comportement : les specs du changement.

## Context

- Aucune clé étrangère vers `user` n'a d'`ondelete` ; `tool_photo` seule cascade depuis `tool`.
- `load_user` (`app/__init__.py`) relit le compte à chaque requête ; la session est un cookie signé
  sans état serveur (ADR 0006).
- `catalog.OUT`, `cancel_unstarted_loans` et `cancel_notice` portent déjà la règle du retrait d'un
  contact ou d'un outil : un prêt `OUT` reste, les demandes et acceptations à venir sont annulées.
- Ordre d'implémentation dans la même branche : `retrait-du-nom-d-utilisateur` (#38, suppression de
  `user.username`), puis `couleurs-des-boutons-et-liens` (#49, ADR 0022, macro `user_name` de
  `templates/_user_name.html`), puis ce changement.

## Goals / Non-Goals

**Goals :**
- Une suppression atomique : tout est effacé ou rien, et aucun prêt ne devient `OUT` pendant qu'elle a lieu.
- Un compte supprimé n'est plus joignable par aucun chemin d'écriture (contact, emprunt, session).

**Non-Goals :**
- Purge des sauvegardes, limitation des essais de mot de passe, page d'un non-contact (proposal).
- Restauration d'un compte supprimé : la suppression est définitive.

## Decisions

### Blueprint `profile`

`app/profile.py` (ADR 0011), préfixe `/profile` : `GET`/`POST /profile` (page et enregistrement),
`GET`/`POST /profile/delete` (confirmation et suppression), tous `login_required`. Gabarits
`profile/show.html` et `profile/confirm_delete.html`. Dans `base.html`, l'entrée grisée « Mon profil »
devient le lien `url_for('profile.show')`, première entrée du menu.

### Adresse et téléphone

Longueurs lues sur les colonnes (`User.address.type.length`, `User.phone.type.length`), comme
`MESSAGE_MAX_LENGTH` de `loans.py`, comptées après `strip`. Téléphone : `fullmatch` de
`[0-9 +\-().]*` après `strip`, sans normalisation. Les deux champs sont vérifiés avant tout
enregistrement ; chaque erreur a son `flash` et le formulaire est réaffiché avec la saisie (règle des
gabarits). Une valeur vide devient `NULL`. Les champs prénom, nom ou courriel éventuellement envoyés
sont ignorés : la vue ne lit que `address` et `phone`.

L'enregistrement est un `UPDATE "user" SET address, phone WHERE id = :me AND deleted_at IS NULL`, et
non l'écriture de l'objet chargé par `load_user` : un envoi parti d'un autre onglet pendant une
suppression attend le verrou du compte, puis ne trouve plus de ligne à modifier, au lieu de réécrire
l'adresse et le téléphone du compte anonymisé. Aucune ligne modifiée : `logout_user()`, redirection
vers `/login`, sans message de succès, comme pour toute session d'un compte supprimé.

### Section de suppression et prêts bloquants

Une fonction de `profile.py` liste les prêts `Loan.status.in_(catalog.OUT)` où le compte est
emprunteur (`borrower_id`) ou prêteur (outil dont il est `owner_id`), avec outil et autre partie
chargés ; l'autre partie est rendue par la macro `user_name`. Le statut affiché reprend les libellés
de « Mes prêts » (`loans.STATUS_LABELS`, « En retard » par `catalog.overdue_loan`), sans réécrire la
règle. Bouton actif : `<a class="button error">` vers la
confirmation ; désactivé : `<button type="button" class="button" disabled>`, gris selon l'ADR 0022.
`GET /profile/delete` avec un prêt `OUT` redirige vers `/profile` avec le message de blocage.

### Confirmation et vérification

L'annonce reprend `catalog.cancel_notice(requests, acceptances)` (sans « entre vous ») sur la
condition « emprunteur ou prêteur ». Le nom est comparé en SQL :
`text_search.sort_key(literal(saisie)) == text_search.sort_key(first_name || ' ' || last_name)`, la
normalisation de l'ADR 0018 plus la casse ; un nom vide après normalisation échoue. Le mot de passe
passe par `check_password_hash`. Une seule erreur pour les deux cas ; le champ du nom est réaffiché,
jamais le mot de passe. Champ du nom `autocomplete="off"`, mot de passe
`autocomplete="current-password"`. « Annuler » est `<a class="button">` vers `/profile`, « Confirmer la
suppression » `<button type="submit" class="button error">`. Le jeton CSRF suit l'ADR 0012.

### Schéma et révision Alembic

Modèle : `deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)`, `email` passe à
`nullable=True`. Une révision (nom de fichier ASCII), chaînée après celle de
`retrait-du-nom-d-utilisateur` :

- `upgrade` : `add_column("user", deleted_at)`, `alter_column("user", "email", nullable=True)` ;
- `downgrade` : `UPDATE "user" SET email = 'supprime-' || id || '@invalid' WHERE email IS NULL`,
  `alter_column(..., nullable=False)`, `drop_column("user", "deleted_at")`.

Une seule révision et une seule PR suffisent : ADR 0007 n'impose *expand/contract* qu'à un
changement incompatible, et les deux opérations sont des relâchements (colonne nullable ajoutée,
`NOT NULL` retiré), sans passe *contract* à suivre. Cette livraison groupée ne permet pourtant pas de
revenir à l'image précédente sans `downgrade` (ADR 0017) : #38 supprime `user.username`, que cette
image mappe encore, et elle ne chargerait plus les comptes (risque de retour arrière de
`retrait-du-nom-d-utilisateur/design.md`, restauration par le `pg_dump` pris avant le déploiement).
Et l'image précédente, même ramenée à son schéma par `downgrade`, ignore `deleted_at` : son
`load_user` rendrait de nouveau valides les sessions encore ouvertes d'un compte supprimé, et les
comptes supprimés réapparaîtraient dans la recherche et les demandes de contact.
`uq_user_email_lower` reste : un index unique admet plusieurs NULL (comportement par défaut de
Postgres, `NULLS DISTINCT` ; vérifié par le scénario « Deux suppressions »). `flask db check` vide,
`docs/schema.md` régénéré (ADR 0009).

### Transaction de suppression

Dans `POST /profile/delete`, une seule transaction, dans cet ordre :

1. Vérifier nom et mot de passe ; en cas d'échec, réafficher sans rien verrouiller.
2. `SELECT … FROM "user" WHERE id = :me FOR UPDATE` : premier verrou, avant tout autre.
3. Verrouiller ses outils, puis ses prêts (emprunteur ou prêteur), `FOR UPDATE … ORDER BY id`.
4. Revérifier l'absence de prêt `OUT` sur les lignes verrouillées ; sinon `rollback` et redirection
   vers `/profile` avec le message de blocage.
5. `catalog.cancel_unstarted_loans(emprunteur ou prêteur)`.
6. `loan.message = NULL` où `borrower_id = :me`.
7. Pour chaque outil : `is_active = False`, `description = ''`, `private_notes = NULL`,
   `photos.remove_photo(tool)` (le module photo reste seul à supprimer une photo, ADR 0008).
8. Supprimer les `contact_request` et `contact_relation` où le compte figure, des deux côtés.
9. `email`, `address`, `phone` à NULL ; `password = generate_password_hash(secrets.token_urlsafe(32))` ;
   `deleted_at = now()`.
10. `commit`, puis `logout_user()`, `session.clear()`, redirection vers
    `/logged-out?reason=account-deleted`.

Le mot de passe inutilisable est le hachage d'un secret aléatoire jeté aussitôt : une valeur au format
attendu par `check_password_hash`, qu'aucune saisie ne vérifie. Une valeur hors format (« ! ») a été
écartée : son traitement par Werkzeug n'est pas vérifié dans ce dépôt.

### Verrouillage contre les écritures concurrentes

Sous `READ COMMITTED`, l'étape 4 relit l'état validé une fois les verrous obtenus : une déclaration de
remise validée avant reste visible et bloque ; une déclaration qui arrive après attend le verrou du
prêt, puis trouve le prêt annulé (« Ce prêt a déjà changé de statut »). `loans._loan_for` verrouille
déjà le prêt (`loans.py:409-411`).

Les écritures qui lient un compte à un autre verrouillent d'abord les lignes `user` concernées
`FOR SHARE`, triées par id :

- `contacts.send_request` : demandeur et destinataire ; 404 si l'un a `deleted_at` ;
- `contacts.accept` : demandeur et utilisateur, avant le verrou de la demande (lire d'abord
  `requester_id` sans verrou, puis verrouiller les comptes, puis relire la demande `FOR UPDATE`). La
  suppression du demandeur a effacé la demande dans sa transaction : la relecture ne la trouve plus et
  la réponse est celle du requirement « Demande qui n'existe plus » (« Cette demande n'est plus en
  attente »), pas un 404 ;
- `loans.create` : emprunteur et propriétaire, avant le verrou de l'outil ; 404 si l'un a `deleted_at`.

Une demande d'emprunt envoyée après la suppression, depuis une page restée ouverte, vers un outil du
compte supprimé reçoit déjà 404 sans ce verrou : la suppression a retiré l'outil et défait la relation
de contact, et `_requestable_tool` (`catalog.visible_tool`) refuse un outil retiré ou d'un non-contact
(requirement « Outil qu'on peut demander » de `demandes-d-emprunt`). Le verrou des comptes ne sert
qu'à l'envoi parti pendant la suppression.

`FOR SHARE` attend la fin d'un `FOR UPDATE` : une écriture qui commence pendant la suppression voit le
compte supprimé ; une écriture déjà engagée fait attendre la suppression, dont les étapes 5 et 8
(nouvelles instructions) voient alors la ligne ajoutée. Comptes d'abord, puis outils, prêts et
demandes : tous les chemins prennent les verrous dans le même ordre. Sans le verrou de compte,
`accept` (verrou de la demande, puis verrou de clé étrangère sur le compte) et la suppression (compte,
puis demande) s'attendraient l'un l'autre.

### Sessions, recherche, contacts, page de déconnexion

- `load_user` : `None` si le compte est absent ou a `deleted_at` ; Flask-Login traite alors la
  requête en visiteur (complète l'ADR 0006, voir ADR 0023).
- `search._matching_users` : `User.deleted_at.is_(None)`, avant la limite de 25.
- `contacts.show` : 404 si `deleted_at`, avant le test de contact.
- `auth.logged_out` : un motif lu dans une table (`inactivity`, `account-deleted`), défaut « Vous êtes
  déconnecté ».

### Nom d'un compte supprimé

Première branche de `user_name(user)` dans `_user_name.html` : si `user.deleted_at`, un
`<span class="user-deleted">Prénom Nom (supprimé)</span>`, sans lien ; la classe est grisée dans
`site.css` (pas d'attribut `style=`, règle des gabarits). Le texte reste échappé par Jinja.

## Risks / Trade-offs

- [Une requête sur des comptes oublie `deleted_at`] → les seuls chemins qui listent ou joignent un
  compte sans relation (recherche, demande de contact, page d'un contact, `load_user`) sont filtrés
  et testés ; les autres passent par des relations ou des prêts déjà défaits ou annulés.
- [Deux suppressions simultanées de comptes liés] → les prêts sont verrouillés `ORDER BY id`, et les
  deux transactions ne partagent ni ligne `user` ni outil ; un interblocage résiduel ferait échouer
  l'une, sans rien supprimer pour elle.
- [Données dans les sauvegardes `pg_dump`, 10 gardées (ADR 0017)] → accepté jusqu'à leur rotation,
  non annoncé à l'utilisateur (`questions.md` #17), consigné dans l'ADR 0023.
- [Retour à l'image précédente] → impossible sans `downgrade` dans cette livraison groupée, à cause
  de #38 (section du schéma) ; après un `downgrade`, l'ancienne image, dont `load_user` ignore
  `deleted_at`, rendrait de nouveau valides les sessions d'un compte supprimé.
- [`downgrade` : courriel `supprime-<id>@invalid` déjà pris] → aucune validation de format à
  l'inscription ne l'interdit ; l'`UPDATE` échouerait sur `uq_user_email_lower`, à corriger à la main.
  Improbable, accepté.
- [Essais répétés du mot de passe sur la confirmation] → exige une session ouverte ; limitation hors
  périmètre, comme à la connexion.

## Migration Plan

Déploiement ordinaire (ADR 0017) : `flask db upgrade` applique la révision, sans migration de
données. Retour arrière : celui de `retrait-du-nom-d-utilisateur` (risque de retour arrière de son
design), livré dans la même image : l'image précédente mappe encore `username` et ne tourne pas sur le
nouveau schéma ; restauration par le `pg_dump` pris avant le déploiement. Après un `downgrade`,
l'ancienne image, dont `load_user` ignore `deleted_at`, rendrait de nouveau valides les sessions d'un
compte supprimé.
