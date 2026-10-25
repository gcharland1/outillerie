# Proposal

## Why

Un voisin peut tenir son inventaire (issue #17), mais rien ne le relie aux autres voisins : il
ne peut ni les trouver ni choisir avec qui partager ses outils. L'issue #22 demande une
recherche d'utilisateurs et des demandes de contact, première étape avant l'accès à la liste
d'outils d'un contact.

## What Changes

- Barre de recherche centrée dans la barre de navigation d'un utilisateur connecté, avec à sa
  gauche un menu déroulant du type de recherche : « Utilisateur », et « Outil » affiché mais
  grisé tant que la recherche d'outils n'existe pas.
- Page « Résultats de recherche » : les autres comptes dont le nom d'utilisateur, le prénom ou le
  nom contient le texte cherché (au moins 3 caractères), sans égard à la casse ; pour chacun, son nom d'utilisateur, son
  prénom et son nom (jamais courriel, adresse ni téléphone) et une action selon la relation :
  « Envoyer une demande », « Demande envoyée » (grisé), « Répondre à sa demande » ou « Déjà en
  contact » (grisé).
- Demande de contact : envoyée par un utilisateur à un autre, elle existe tant que le
  destinataire n'y a pas répondu ; son existence est son statut. Accepter crée la relation de
  contact, refuser n'en crée pas ; les deux suppriment la demande. Le refus est discret : le
  demandeur voit de nouveau « Envoyer une demande ».
- Page « Mes contacts », dans le menu du compte : les demandes reçues en attente, avec
  « Accepter » et « Refuser », puis la liste des contacts, avec « Retirer ». Le retrait passe
  par une page de confirmation et retire le contact des deux côtés.
- Pastille de notification, avec le nombre de demandes reçues en attente, à côté du nom
  d'utilisateur et de « Mes contacts » dans le menu du compte.
- Schéma : tables `contact_request` et `contact_relation`. Une relation est une seule ligne par
  paire de voisins, symétrique, comme le propose l'issue (point « À ANALYSER » tranché par un
  nouvel ADR).
- Blueprints `search` et `contacts` (ADR 0011).

## Capabilities

### New Capabilities
- `contacts`: demandes de contact entre voisins (envoi, acceptation, refus), liste « Mes
  contacts », retrait d'un contact avec confirmation, pastille des demandes en attente.
- `recherche`: barre de recherche de la navigation et page de résultats des utilisateurs, avec
  l'état de la relation de contact pour chaque résultat.

### Modified Capabilities
_Aucune._ L'entrée « Mes contacts » s'ajoute au menu du compte sans changer les exigences de la
spec `inventaire` (changement `gestion-des-outils`, non archivé).

## Impact

- Code : nouveaux modules `app/search.py` et `app/contacts.py`, enregistrés dans
  `create_app()` ; nouveaux gabarits `search/results.html`, `contacts/mine.html`,
  `contacts/confirm_remove.html` ; `base.html` (barre de recherche, entrée « Mes contacts »,
  pastilles) ; `app/static/site.css`.
- Schéma : modèles `ContactRequest` et `ContactRelation` (`models/contact.py`), une révision
  Alembic, `docs/schema.md` régénéré (ADR 0009).
- Tests : nouveaux tests pytest des modèles, de la recherche, des demandes, de « Mes contacts »
  et de la navigation ; fabriques dans `tests/factories.py`.
- Dépendance : aucune.
- ADR : nouveau 0013 « Relation de contact symétrique en une ligne ». ADR concernés : 0001
  (rendu serveur sans JavaScript : menu déroulant et pastille en HTML et CSS), 0002 et 0007
  (révision Alembic, contraintes nommées), 0009 (diagramme),
  0011 (Blueprints), 0012 (jeton CSRF sur chaque formulaire `POST` ; la recherche est un `GET`).

**Hors périmètre**

- Recherche d'outils : le choix « Outil » est grisé.
- Liste d'outils d'un contact : cliquer sur un contact ne fait rien (issue #22).
- Annulation par le demandeur d'une demande envoyée.
- Blocage d'un voisin, délai avant une nouvelle demande après un refus, limite du nombre de
  demandes.
- Notification hors du site (courriel) et historique des demandes : une demande traitée est
  supprimée.
- Pagination des résultats de recherche et de la liste de contacts.
- Visibilité configurable du profil : tout utilisateur connecté peut trouver tout autre compte
  par son nom.
