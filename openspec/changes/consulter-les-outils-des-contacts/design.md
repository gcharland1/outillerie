# Design

## Context

Voir `proposal.md` pour la motivation et `questions.md` pour chaque décision, sa source et qui
l'a prise. État du code utile ici :

- Un contact est une ligne `contact_relation` (paire ordonnée `user_a_id < user_b_id`, ADR 0013) ;
  `app/contacts.py` a déjà `_my_contacts()` et `_contact_relation(user_id)`.
- `Tool` : `is_active`, `condition` (`functional`, `needs_repair`, `out_of_order`),
  `private_notes`. `Loan` : `status` (`requested`, `accepted`, `refused`, `canceled`, `lent`,
  `returned`), `start_date` et `end_date` non nulles. Aucune colonne de disponibilité.
- `app/photos.py` est le seul module qui décide de l'accès à une photo (`can_view_photo`, ADR 0008)
  et fournit `tool_ids_with_photo` pour un lot d'outils.
- La recherche d'utilisateurs (`app/search.py`) est un GET avec `icontains(autoescape=True)` ; le
  type « Outil » y répond aujourd'hui « pas encore disponible ».
- Aucun JavaScript (ADR 0001) ; aucune pagination dans le site.

## Goals / Non-Goals

**Goals:**
- Un nombre fixe de requêtes par page, quel que soit le nombre d'outils : outils, statuts et
  présence de photo chargés en lot.
- Une seule définition des « outils visibles par un utilisateur », partagée par les deux pages et
  par l'accès à la photo.
- Un état de filtre entièrement porté par l'URL (`q`, `available`).

**Non-Goals:**
- Index trigramme, fonction `unaccent` immuable : inutiles sans index (ADR 0016).
- Toute écriture en base : ce changement est en lecture seule (aucun POST, aucun jeton CSRF neuf).

## Decisions

### Module de catalogue partagé

Nouveau module `app/catalog.py`, importé par `tools` et `contacts` :

- `visible_tools_query(user, owner_id=None)` : `Tool` actif, `condition != out_of_order`,
  `owner_id` dans la sous-requête des ids de contacts de `user` (les deux sens de la paire),
  `owner_id != user.id`. `owner_id` restreint à un contact (page d'un contact).
- `loan_statuses(tool_ids)` : une requête groupée sur `loan` qui renvoie, par outil, le prêt
  `lent` le plus récent (pour sa `end_date`) ou la présence d'un `requested` / `accepted` dont
  `end_date >= today`. Calcul du libellé en Python, dans la vue.
- `is_contact(user_id, other_id)` : lecture de `contact_relation` par la paire ordonnée.

*Alternative écartée :* placer la requête dans `tools.py` et l'importer depuis `contacts.py` :
crée une dépendance entre Blueprints (ADR 0011). Une colonne de statut dénormalisée sur `tool` :
deux sources de vérité.

### Statut de prêt

Priorité : `lent` (quelles que soient les dates) → « Prêté jusqu'au <end_date> » ; sinon un
`requested` ou `accepted` non terminé (`end_date >= today`) → « En attente de prêt » ; sinon
« Disponible ». « Disponible uniquement » applique la même règle en SQL (`NOT EXISTS` sur les
prêts bloquants), pour ne pas filtrer après coup en Python. La date est formatée en Python par
`catalog.french_date` (mois en toutes lettres), dans le libellé : pas de Babel.

### Recherche floue (ADR 0016)

- Texte normalisé : `strip()`. Vide ⇒ aucun filtre, tri `lower(name), id`.
- Condition : `unaccent(name) ILIKE unaccent(:pattern)` OU même chose sur la description, OU
  `word_similarity(unaccent(:q), unaccent(name)) >= FUZZY_THRESHOLD`, OU même chose sur la
  description. `:pattern` = `%` + `q` échappé à la main (`\`, `%`, `_`) + `%`, avec
  `escape="\\"` : `icontains(autoescape=True)` n'accepte pas une expression `unaccent(...)`.
- Sous 3 caractères : sous-chaîne seulement (trigrammes peu fiables).
- `FUZZY_THRESHOLD = 0.5`, constante Python, calibrée par les tests de comportement de la spec
  (faute d'une lettre, accents, « tondeuse » ne trouve pas « perceuse »). Comparaison explicite
  plutôt que l'opérateur `<%` : pas de `SET` de session, fragile avec le pool.
- Tri : `name ILIKE pattern` desc, score nom desc, score description desc, `lower(name)`, `id`.
- `private_notes` n'apparaît jamais dans la requête.

### Routes et gabarits

- `GET /tools/find` (`tools.find`) : `q`, `available` ; `@login_required`.
- `GET /contacts/<int:user_id>` (`contacts.show`) : 404 si `user_id` n'est pas un contact, est
  l'utilisateur lui-même ou n'existe pas — même réponse dans tous les cas, comme `_owned_tool`.
- `search.results` avec `type=tool` : après le contrôle des 3 caractères, redirection vers
  `tools.find` avec `q` ; type inconnu : « Ce type de recherche n'est pas disponible ».
- `catalog.tool_list(user_id, args, owner=None)` lit les filtres de l'URL et prépare cartes et
  message de liste vide pour les deux vues.
- `CONDITION_LABELS` passe de `tools.py` à `catalog.py` : la page d'un contact, rendue par la
  Blueprint `contacts`, affiche aussi l'état.
- Gabarit inclus `tools/_cards.html` (formulaire de filtre + grille + messages de liste vide),
  utilisé par `tools/find.html` et `contacts/show.html`. Le formulaire de filtre renvoie vers
  l'URL de la page courante (`url_for` de l'endpoint courant), jamais vers une URL fournie par le
  client.
- Grille : classes CSS dans `site.css` (`.tool-cards`, `grid-template-columns` une colonne, trois
  à partir du point de rupture moyen), pas de `style=`.
- Description coupée dans la vue (`text[:125] + "…"` si plus longue), pas de `truncate` Jinja
  dont la tolérance par défaut dépasse la limite.
- Bouton « Emprunter » : `<button class="button" disabled>` + « Bientôt disponible ».
- Paramètres : `available` coché seulement pour la valeur `1`, toute autre valeur vaut décoché ;
  `q` est coupé de ses espaces autour. Un outil sans description n'affiche pas de description.
- `base.html` : option « Outil » sans `disabled` ; bouton « Trouver un outil » (`a.button`) dans
  la navigation, pas dans le menu du compte (`.claude/rules/templates.md`).
- `contacts/mine.html` : nom du contact en lien vers `contacts.show`.

### Accès à la photo

`can_view_photo(user, tool)` : propriétaire, ou (`tool.is_active` et `condition != out_of_order`
et une ligne `contact_relation` pour la paire). Lue directement dans `photos.py` : `catalog`
importe déjà `photos`, l'inverse créerait un import circulaire. Le cache `private, no-cache` + ETag existant
fait qu'un ancien contact reçoit 404 à la revalidation.

### Extensions PostgreSQL

Révision Alembic écrite à la main (`flask db revision`, nom de fichier ASCII) :
`CREATE EXTENSION IF NOT EXISTS pg_trgm` et `unaccent` ; `downgrade()` les laisse, comme
`btree_gist` (d'autres objets peuvent en dépendre). Tests : `mock_app` crée les deux extensions ;
`test_schema.drop_schema()` les supprime, et un test vérifie leur présence après migration.

## Risks / Trade-offs

- [Seuil de similarité mal calibré : faux positifs dans les longues descriptions ou faute non
  trouvée dans un nom court] → constante unique, tests de comportement, ajustement sans
  migration.
- [`unaccent(text)` dépend du `search_path`] → schéma `public` par défaut ; à revoir si le
  `search_path` change (ADR 0016).
- [Balayage complet des outils des contacts à chaque recherche] → borné aux contacts ; index
  GIN + fonction immuable si le volume l'exige (ADR 0016).
- [Statut affiché sans prêt réel tant que la demande d'emprunt n'existe pas] → la règle est
  couverte par des tests qui créent des prêts directement ; le second changement l'exercera.
- [Le type « Outil » de la barre garde le minimum de 3 caractères, la page n'en a pas] → assumé :
  la page filtre un ensemble déjà restreint aux contacts.

## Migration Plan

1. Déployer : le conteneur exécute `flask db upgrade` au démarrage, qui crée les extensions avec
   le rôle propriétaire de la base (même rôle que `btree_gist`).
2. Vérifier : `SELECT extname FROM pg_extension` contient `pg_trgm` et `unaccent`.
3. Retour arrière : redéployer la version précédente ; les extensions restent installées sans
   effet.
