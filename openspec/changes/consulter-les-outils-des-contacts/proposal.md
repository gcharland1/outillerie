# Proposal

## Why

Pour prêter des outils, il faut d'abord savoir lesquels nos contacts proposent et s'ils sont
libres (issue #29). Aujourd'hui, un utilisateur ne voit que ses propres outils : aucune page ne
montre ceux de ses contacts, la photo d'un outil n'est servie qu'à son propriétaire, et l'option
« Outil » de la barre de recherche est grisée.

## What Changes

- Page « Trouver un outil » (`/tools/find`), atteinte par une entrée du menu du compte :
  tous les outils en circulation des contacts de l'utilisateur, en cartes (une colonne sur mobile,
  trois à partir d'un écran moyen) avec photo, nom, propriétaire, description coupée à 125 caractères, état et
  statut de prêt.
- Page d'un contact (`/contacts/<id>`) : « Prénom Nom (@nom d'utilisateur) », puis la section
  « Outils de <Prénom Nom> » avec les mêmes cartes ; le nom d'un contact devient un lien dans
  « Mes contacts ».
- Statut dérivé des prêts : « Prêté jusqu'au <date> », « En attente de prêt » ou « Disponible »,
  écrit en clair sur la carte. Un outil « Hors d'usage » n'est jamais montré aux contacts.
- Filtres en GET sur les deux pages : case « Disponible uniquement » et texte cherché.
  Recherche tolérante aux fautes de frappe et aux accents (extensions PostgreSQL `pg_trgm` et
  `unaccent`), triée : sous-chaîne exacte dans le nom, ressemblance du nom, ressemblance de la
  description, puis nom.
- Option « Outil » de la barre de recherche activée : elle mène à « Trouver un outil » filtré par
  le texte saisi.
- Bouton « Emprunter » affiché grisé sur chaque carte, « Bientôt disponible ».
- Photo d'un outil servie aussi aux contacts de son propriétaire, tant que l'outil est en
  circulation et n'est pas hors d'usage.

## Capabilities

### New Capabilities
- `outils-des-contacts`: consultation des outils des contacts — page « Trouver un outil »,
  section d'outils d'un contact, cartes, statut de prêt, filtres de disponibilité et de texte.

### Modified Capabilities
- `recherche`: l'option « Outil » devient sélectionnable et mène à « Trouver un outil » ; le
  message « Ce type de recherche n'est pas encore disponible » disparaît.
- `photo-outil`: l'image est servie aussi aux contacts du propriétaire pour un outil en
  circulation et non hors d'usage.
- `contacts`: le nom d'un contact mène à sa page ; nouvelle page d'un contact.

## Impact

- Code : `app/tools.py` (route `find`), `app/contacts.py` (route `show`), `app/search.py`
  (redirection du type outil), `app/photos.py` (`can_view_photo`), nouveau module de requête
  partagé pour la liste d'outils visibles et leur statut ; gabarits `base.html`,
  `contacts/mine.html`, nouveaux `tools/find.html`, `contacts/show.html` et une inclusion de
  cartes commune ; `app/static/site.css`.
- Schéma : une révision Alembic écrite à la main crée les extensions `pg_trgm` et `unaccent` ;
  aucune table ni colonne. Fixtures de test (`conftest.py`, `test_schema.py`) mises à jour.
- Dépendance Python : aucune.
- ADR : nouveau 0016 « Recherche floue des outils avec pg_trgm et unaccent » (`accepted`).
  ADR concernés : 0001 (rendu serveur, filtres sans JavaScript), 0002 et 0007 (révision
  Alembic, extensions écrites à la main), 0008 (route photo stable, seul `photos.py` décide de
  l'accès), 0011 (routes dans les Blueprints `tools` et `contacts`), 0012 (aucun POST nouveau),
  0013 (relation de contact en une ligne, paire ordonnée).
- Décisions : `questions.md`.

**Hors périmètre**

- Demande d'emprunt : page de confirmation, dates, message au propriétaire, création du prêt,
  notification, page du propriétaire pour accepter ou refuser. Second changement à venir ;
  « Emprunter » reste grisé d'ici là.
- Recherche floue des utilisateurs : la recherche d'utilisateurs reste une sous-chaîne.
- Index trigramme ; pagination ; filtrage pendant la frappe (JavaScript).
- Coordonnées ou autres informations de profil sur la page d'un contact.
