# Design

## Context

Voir proposal.md pour la motivation et specs/ pour les exigences. État actuel :

- `models/user.py` : `User` avec `username` (unique), `first_name`, `last_name` non nuls ;
  `email`, `address`, `phone` ne doivent pas sortir de la recherche.
- `models/loan.py` montre les conventions du schéma : `created_at` avec
  `server_default=func.now()`, contraintes nommées par la convention de `app/extensions.py`
  (ADR 0007).
- `app/tools.py` montre les conventions des routes : Blueprint à préfixe, `@login_required`,
  recherche filtrée en SQL par l'utilisateur courant puis `abort(404)`, `flash` puis redirection
  pour une action déjà faite (retour arrière, second envoi).
- `base.html` : `.nav-left` (logo) et `.nav-right` (menu du compte `<details class="account-menu">`,
  déconnexion). Chota offre `.nav-center`. Tous les messages `flash` s'affichent comme des erreurs.
- Les tests créent le schéma par `db.create_all()` ; les fixtures `user` (alice) et `bob` existent
  dans `tests/conftest.py`.

## Goals / Non-Goals

**Goals:**
- Garantir en base les invariants des specs : pas de demande à soi-même, au plus une demande
  par paire de voisins dans un sens ou dans l'autre, une seule relation par paire.
- Un nombre fixe de requêtes par page, quel que soit le nombre de résultats ou de contacts.
- Aucun JavaScript (ADR 0001) : menu du type de recherche, envoi et pastille en HTML et CSS.

**Non-Goals:**
- Recherche plein texte, tolérance aux accents ou aux fautes (`unaccent`, `pg_trgm`) : une
  sous-chaîne sans égard à la casse suffit à l'échelle d'un voisinage.
- Index pour la recherche : un balayage de `user` reste rapide à cette échelle.
- Messages de succès : le changement d'état du bouton ou de la liste en tient lieu, puisque
  `base.html` affiche tout message `flash` en rouge.

## Decisions

### Schéma : `contact_request` et `contact_relation` (ADR 0013)

`models/contact.py`, exporté par `models/__init__.py` :

```
contact_request
  id            integer PK
  requester_id  FK user.id, NOT NULL, indexé      -- qui envoie
  recipient_id  FK user.id, NOT NULL, indexé      -- qui reçoit
  created_at    timestamptz, défaut now()
  CHECK requester_id <> recipient_id                          (ck_contact_request_not_self)
  UNIQUE (LEAST(requester_id, recipient_id), GREATEST(...))   (uq_contact_request_pair)

contact_relation
  user_a_id   FK user.id, PK
  user_b_id   FK user.id, PK, indexé
  created_at  timestamptz, défaut now()
  CHECK user_a_id < user_b_id                                 (ck_contact_relation_ordered_pair)
```

Les noms de l'issue changent pour suivre le code existant (`owner_id`, `borrower_id`) :
`user_id` devient `recipient_id`, `user_a`/`user_b` deviennent `user_a_id`/`user_b_id`.

Une relation est une seule ligne : la paire est rangée (`user_a_id` le plus petit), le `CHECK`
interdit l'autre ordre et la clé primaire composite interdit le doublon. Une méthode de classe
`ContactRelation.between(first_id, second_id)` construit la ligne dans le bon ordre ; tout code
passe par elle. La clé primaire sert la recherche par `user_a_id`, l'index `ix_contact_relation_user_b_id`
celle par `user_b_id`.

L'index unique sur la paire non ordonnée porte deux invariants de la spec `contacts` : pas de
second envoi, pas de demande croisée. Son nom est explicite : la convention `ix` ne s'applique
pas à une expression.

Une demande existe tant qu'elle attend une réponse : son existence est son statut. Accepter ou
refuser la supprime ; aucune colonne `status`. Aucun parcours ne relit une demande traitée :
l'acceptation laisse la relation, le refus est discret (spec `contacts`), et la suppression libère
la paire pour une nouvelle demande après un refus, sans index partiel.

Les clés étrangères vers `user` ne portent pas d'`ON DELETE` : aucun compte ne se supprime
aujourd'hui, comme pour `tool` et `loan`.

Alternatives écartées (détail dans l'ADR 0013) : deux lignes dirigées par relation (doublon à
tenir synchrone) ; statut « acceptée » sur la demande au lieu d'une table de relations (mêle
historique et état, que l'issue veut séparer) ; demandes traitées conservées avec un statut
`sent`/`completed` (lignes que rien ne lit, index partiel pour permettre une nouvelle demande).

### Blueprints `search` et `contacts`

| Méthode | URL | Endpoint | Effet |
|---|---|---|---|
| GET | `/search?type=user&q=…` | `search.results` | résultats de recherche |
| GET | `/contacts` | `contacts.mine` | demandes reçues en attente et contacts |
| POST | `/contacts/requests` | `contacts.send_request` | envoie une demande (champs `recipient_id`, `q`) |
| POST | `/contacts/requests/<id>/accept` | `contacts.accept` | accepte, redirige vers `contacts.mine` |
| POST | `/contacts/requests/<id>/refuse` | `contacts.refuse` | refuse, redirige vers `contacts.mine` |
| GET | `/contacts/<user_id>/remove` | `contacts.confirm_remove` | page de confirmation |
| POST | `/contacts/<user_id>/remove` | `contacts.remove` | défait la relation, redirige vers `contacts.mine` |

La recherche a sa Blueprint (ADR 0011) parce qu'elle servira aussi les outils ; elle ne fait que
lire. Toutes les routes portent `@login_required`. La recherche est un `GET` : pas de jeton CSRF,
URL partageable et rechargeable ; chaque `POST` porte le jeton (ADR 0012).

`/contacts/<user_id>` reste libre pour la future page d'un contact et de ses outils.

### Recherche

`app/search.py` lit `type` (défaut `user`) et `q` passé par `strip()`. Pour `type` autre que
`user`, ou `q` de moins de `SEARCH_MIN_LENGTH = 3` caractères, la page rend le message de la spec
sans requête. Le champ porte `minlength="3"` : le navigateur prévient avant l'envoi, sans
JavaScript ; il compte les espaces, d'où le contrôle du serveur après `strip()`. Sinon :

```
select(User).where(
    User.id != current_user.id,
    or_(User.username.icontains(q, autoescape=True),
        User.first_name.icontains(q, autoescape=True),
        User.last_name.icontains(q, autoescape=True),
        (User.first_name + " " + User.last_name).icontains(q, autoescape=True)),
).order_by(func.lower(User.username), User.id)
```

`autoescape=True` échappe `%` et `_`. L'état de chaque résultat vient de trois requêtes, quel que
soit le nombre de résultats : identifiants des destinataires de mes demandes envoyées, des
demandeurs de mes demandes reçues, et de mes contacts. La vue passe au gabarit une
liste de paires (compte, état) avec l'état parmi `none`, `sent`, `received`, `contact` ; le
gabarit associe chaque état à son bouton. Ces trois requêtes vivent dans `app/contacts.py`
(`relation_states(user_ids)`), que la recherche importe.

La vue passe aussi `search_text` ; `base.html` remplit le champ avec `search_text|default("")`.

### Envoi d'une demande

`send_request` charge le destinataire par `db.session.get(User, recipient_id)` ; inconnu ou
soi-même → 404. Puis, dans l'ordre :

1. Déjà en contact, ou demande d'Alice à Bob déjà envoyée → rien.
2. Demande de Bob à Alice → redirection vers `contacts.mine`.
3. Sinon, insertion. Un `IntegrityError` sur `uq_contact_request_pair` (deux envois
   simultanés) est absorbé par `rollback` : l'invariant tient, la page suivante montre l'état réel.

Les cas 1 et 3 redirigent vers `url_for("search.results", type="user", q=q)`, avec le `q` du
champ caché du formulaire : `url_for` construit une URL locale, le texte n'est qu'un paramètre.

### Réponse à une demande

`_received_request(request_id)` charge la demande par `id` avec `with_for_update()` : deux
réponses simultanées s'exécutent l'une après l'autre, la seconde ne trouve plus la ligne.

- Demande adressée à un autre compte → 404.
- Aucune demande → `flash` « Cette demande n'est plus en attente » et redirection vers
  `contacts.mine`, comme le retrait d'un outil déjà retiré. Une demande traitée et un
  identifiant qui n'a jamais existé se confondent, ce qui ne révèle rien.

`accept` supprime la demande et ajoute `ContactRelation.between(...)` dans le même `commit`.
`refuse` ne fait que supprimer. Une relation et une demande ne coexistent pas : l'envoi est
refusé entre contacts et une relation ne naît que d'une acceptation.

### Retrait d'un contact

`confirm_remove` et `remove` chargent le compte par `user_id` (inconnu → 404), puis la relation
par `db.session.get(ContactRelation, pair)`. Sans relation → `flash` « Cette personne ne fait pas
partie de vos contacts » et redirection vers `contacts.mine`. Un identifiant de compte n'est pas
secret (la recherche les expose) : répondre autrement qu'un 404 ne révèle rien.

### Listes de « Mes contacts »

Deux requêtes : les demandes reçues avec leur demandeur (`joinedload`), triées par
`created_at, id` ; les contacts par jointure de `User` sur `contact_relation` où l'utilisateur
est `user_a_id` ou `user_b_id`, triés par `func.lower(User.username), User.id`. Le nom d'un
contact est un texte simple, sans lien (hors périmètre).

### Pastille

`@bp.app_context_processor` dans `app/contacts.py` injecte `pending_contact_requests` : un
`COUNT` des demandes dont `recipient_id` est l'utilisateur, servi par
`ix_contact_request_recipient_id`, et 0 pour un visiteur sans requête. `base.html` affiche
`<span class="badge" aria-label="N demandes de contact en attente">N</span>` dans le `<summary>`
et à côté de « Mes contacts » quand N > 0. Le compte fait une requête de plus par page connectée.

Alternative écartée : compter dans la session (cookie, ADR 0006) : périmé dès qu'un autre voisin
envoie une demande.

### Barre de recherche

Dans `base.html`, pour un utilisateur connecté, une `.nav-center` contient
`<form class="search-bar" method="get" action="/search">` : `<select name="type">` avec
`<option value="user" selected>Utilisateur</option>` et `<option value="tool" disabled>Outil</option>`,
`<input type="search" name="q" minlength="3">` avec un `aria-label`, et un bouton « Rechercher ». Le style
(`.search-bar`, `.badge`) va dans `app/static/site.css`, sans attribut `style=`.

### Migration

Une révision `flask db migrate -m "Contacts : demandes et relations"`, renommée en ASCII
(`<rev>_contacts_demandes_et_relations.py`). À relire : l'index d'expression et les deux
`CHECK` ; les compléter à la main si l'autogénération les omet. `flask db check` doit être vide
ensuite ; si Alembic ne sait pas comparer l'index d'expression, il l'ignore avec un avertissement,
à noter dans la révision. `downgrade` supprime les deux tables. `docs/schema.md` est régénéré.

## Risks / Trade-offs

- [Tout utilisateur connecté peut énumérer les comptes, une lettre à la fois] → seuls nom
  d'utilisateur, prénom et nom sont affichés ; visibilité configurable hors périmètre.
- [Un refus discret laisse un voisin insister] → accepté (choix de l'utilisateur) ; blocage et
  délai hors périmètre.
- [Les tests créent le schéma par `db.create_all()` et ne vérifient pas la révision] → l'index
  d'expression et les `CHECK` sont testés sur le schéma des modèles ; `flask db upgrade`,
  `downgrade` et `check` sont vérifiés à la main et par la CI (ADR 0007).
- [Une requête de plus par page connectée pour la pastille] → `COUNT` sur un index, négligeable.

## Migration Plan

`flask db upgrade` crée deux tables vides ; aucune donnée existante n'est touchée. Retour
arrière : `flask db downgrade` supprime les tables et les contacts créés depuis.
