# Questions — consulter-les-outils-des-contacts (issue #29)

Réponses fusionnées des agents Code, Specs et ADR, Cas limites, Antériorité (2026-11-01).

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 1 | La demande d'emprunt (Confirmer, « En attente de prêt », notification) fait-elle partie de ce changement ? | En suspens. `loan.start_date`/`end_date` NOT NULL, aucune colonne de message, aucune page propriétaire pour traiter une demande ; règles de prêt reportées à « des changements suivants ». | Sourced `application/models/loan.py:23-24` ; `openspec/changes/schemas-initiaux/proposal.md:63-65` | utilisateur |
| 2 | Quels outils sont visibles ? | Outils `is_active` des contacts acceptés (`contact_relation`, ADR 0013) ; une demande de contact en attente ne donne aucun accès. | Sourced `openspec/changes/photo-des-outils/questions.md:9` ; `application/models/contact.py:29-47` | dépôt |
| 3 | Mes propres outils sont-ils listés ? | Non : « Gérer mes outils » les montre, et un propriétaire n'emprunte pas son propre outil. | Inferred de `schemas-initiaux/proposal.md:64` | convention |
| 4 | Les outils retirés sont-ils listés ? | Non, ni leur photo pour un contact. | Inferred de `models/tool.py:39`, `schemas-initiaux/design.md:130-135` | convention |
| 5 | Comment traduire `loan.status` en Disponible / En attente de prêt / Prêté ? (`accepted` futur, `lent` dont `end_date` est dépassée, un `requested` bloque-t-il les autres ?) | En suspens. Statut dérivé, sans colonne. | Sourced `models/loan.py:10-16, 46-52` ; `schemas-initiaux/specs/prets/spec.md:49-52` | utilisateur |
| 6 | Notification au propriétaire : laquelle ? | Seul précédent : pastille calculée par un context processor ; courriel exclu. Dépend de #1. | Sourced `application/app/contacts.py:17-26` ; `liste-de-contacts/proposal.md:69-70` | utilisateur (si #1 inclut la demande) |
| 7 | Filtres côté serveur ou client ? | Formulaire GET `q` + `available=1`, bouton « Filtrer » ; pas de filtrage pendant la frappe. | Inferred de ADR 0001, `liste-de-contacts/design.md:26`, aucun `<script>` | convention |
| 8 | Fuzzy-match : technique ? | En suspens. Aujourd'hui `icontains(autoescape=True)` ; pg_trgm écarté pour la recherche d'utilisateurs ; pg_trgm = extension + ADR 0016. | Sourced `application/app/search.py:42-45` ; `liste-de-contacts/design.md:29-31` | utilisateur |
| 9 | Barre de recherche principale de l'accueil ? | C'est la barre de navigation ; activer « Outil », `type=tool&q=…` mène à « Trouver un outil » pré-filtré (delta MODIFIED de `recherche`). | Inferred de `templates/index.html:1-11`, `base.html:29-37` | convention |
| 10 | Où placer l'entrée « Trouver un outil » (issue : « menu déroulant ») ? | En suspens. Le menu du compte est réservé aux pages personnelles. | Sourced `.claude/rules/templates.md:23` | utilisateur |
| 11 | Titre « Emprunter un outil » ou « Trouver un outil » ? | « Trouver un outil » ; « Emprunter » reste le bouton. | Inferred de l'issue (deux libellés) et de #9 | convention |
| 12 | Grille 3 cartes sur mobile ? | Une colonne sur mobile, trois à partir de `md` (`col-12 col-4-md` ou grille dans `site.css`). | Inferred de `templates/login.html:4-5` ; `style=` interdit | convention |
| 13 | Troncature 125 caractères ? | Dans la vue, « … » ajouté seulement si coupé, 125 caractères avant « … ». | Inferred de `.claude/rules/templates.md:11` | convention |
| 14 | Détail du statut au survol ? | Statut écrit en clair (« En attente de prêt », « Prêté jusqu'au <date> »), `title` en plus ; le survol seul est invisible au tactile. | Inferred de ADR 0001 (pas de JS) | convention |
| 15 | Page d'un contact ? | `GET /contacts/<user_id>` dans `contacts`, section « Outils de <nom> » ; nom cliquable dans « Mes contacts ». | Sourced `liste-de-contacts/design.md:99, 166` | dépôt |
| 16 | Contenu de la page d'un contact hors outils ? | En suspens. Pas de coordonnées (comme la recherche). | Sourced `liste-de-contacts/specs/recherche/spec.md:62-69` | utilisateur |
| 17 | Accès d'un non-contact, outil retiré, inconnu ou à soi par URL ? | Même 404 sur toutes les routes (page de contact incluse ? voir #16), comme `_owned_tool` et la photo. | Inferred de `application/app/tools.py:169-176` | convention |
| 18 | Photo pour un contact ? | `can_view_photo` = propriétaire, ou contact et outil actif ; ex-contact → 404 (delta MODIFIED `photo-outil`). | Sourced `application/app/photos.py:98-100` ; `photo-des-outils/design.md:108-111` | dépôt |
| 19 | Notes privées ? | Jamais affichées ni cherchées par le filtre texte ; exigence + test. | Sourced `schemas-initiaux/tasks.md:58`, `proposal.md:66-67` | dépôt |
| 20 | CSRF ? | `CSRFProtect` global ; jeton sur tout POST ; GET sans jeton. | Sourced `application/app/__init__.py:23` ; ADR 0012 | dépôt |
| 21 | Pagination ? | Aucune (non-objectif) ; nombre fixe de requêtes par page (statuts et photos en lot). | Sourced `liste-de-contacts/proposal.md:71`, `design.md:24-25` | convention |
| 22 | Retour à la liste d'origine ? | Origine énumérée (`find` ou `contact`+id, avec `q`, `available`), URL reconstruite par `url_for` ; jamais d'URL brute. | Sourced `gestion-des-outils/proposal.md:79-81` ; `contacts.py:47` | convention |
| 23 | « Annuler » sur la confirmation ? | Lien-bouton vers la liste d'origine ; rien n'est écrit. | Sourced `templates/tools/confirm_retire.html:19` | convention |
| 24 | Minimum de 3 caractères ? | Gardé dans la barre de navigation ; le filtre de la page accepte un texte vide (tout afficher). | Sourced `application/app/search.py:9`, `base.html:34` | convention |
| 25 | Listes vides ? | Trois messages : aucun contact (lien vers la recherche), contacts sans outil, aucun résultat. | Inferred de `templates/tools/mine.html:34-36` | convention |
| 26 | Outil sans photo ? | Espace réservé neutre pour garder la grille. | Inferred de `photo-outil/spec.md:204` | convention |
| 27 | Outils `needs_repair` / `out_of_order` ? | En suspens. Règle reportée. | Sourced `schemas-initiaux/proposal.md:64-65` | utilisateur |
| 28 | Specs à modifier (`recherche`, `photo-outil`, `contacts`) encore en delta non archivé ? | En suspens. `openspec/specs/` ne contient que `accueil`. | Sourced `openspec list --specs` ; `liste-de-contacts/tasks.md:43` | utilisateur |
| 29 | Blueprints et routes ? | `GET /tools/find` dans `tools` ; `GET /contacts/<id>` dans `contacts` ; requête et statut dans un module partagé. | Inferred de ADR 0011, `application/app/__init__.py:25-31` | convention |
| 30 | ADR requis ? | Seulement pour pg_trgm (#8), une table de notifications (#6) ou du JavaScript. Prochain numéro : 0016. | Sourced `docs/decisions/README.md` ; aucune autre branche n'a d'ADR > 0015 | dépôt |

## Second passage — pg_trgm + unaccent (angle Code)

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 32 | Où installer les extensions ? | Révision écrite à la main : `CREATE EXTENSION IF NOT EXISTS pg_trgm` et `unaccent`, laissées au `downgrade()` comme `btree_gist` ; `mock_app` les crée ; `test_schema.drop_schema()` les supprime et le test vérifie leur présence après migration. | Sourced `migrations/versions/1f84fa116ada_…py:51,171` ; `tests/conftest.py:45-48` ; `tests/test_schema.py:42-46,82-86` | convention |
| 33 | Droit de CREATE EXTENSION en dev, CI et production ? | Même rôle `POSTGRES_USER` qui crée déjà `btree_gist` ; image `postgres:17` partout ; la production exécute `flask db upgrade` au démarrage. Vérification après déploiement : `SELECT extname FROM pg_extension`. Partial : `.env` de production non vu ; superutilisateur et extensions « trusted » = Training. | Sourced `compose.yaml:7,19-23` ; `application/Dockerfile:35` ; `.github/workflows/ci.yml:16` | convention |
| 34 | Index trigramme et wrapper immuable de `unaccent` ? | Aucun : balayage des seuls outils des contacts, échelle d'un voisinage. Piste notée dans l'ADR 0016. | Sourced `liste-de-contacts/design.md:29-31` ; Training pour la volatilité de `unaccent` | convention |
| 35 | Forme de la requête ? | `word_similarity(unaccent(q), unaccent(champ))` comparé à une constante `FUZZY_THRESHOLD` (0.5, calibrée par tests), OU ILIKE sur le texte sans accents (jokers échappés à la main) ; sous 3 caractères, ILIKE seul ; tri `name_score desc, desc_score desc, lower(name), id`. | Inferred de `application/app/search.py:35-49` ; Training pour pg_trgm | convention |
| 36 | La recherche d'utilisateurs suit-elle ? | Non, inchangée dans ce changement ; incohérence notée dans l'ADR 0016. | Sourced `application/app/search.py:9,35-49` | convention |

## Si la demande d'emprunt est incluse (#1)

Dates de la demande (champs « Du / Au » ou dates nullables), colonne `loan.message` et longueur maximale,
page propriétaire pour accepter ou refuser, demandes concurrentes sur un même outil, verrou `with_for_update`,
ce que voit l'emprunteur après l'envoi, sort des demandes au retrait d'un contact ou d'un outil.

## Réponses de l'utilisateur

- #1 : scinder. Ce changement couvre la consultation seulement ; la demande d'emprunt (dates, message,
  notification, page du propriétaire) va dans un second changement. #6 et la section ci-dessus passent à ce second changement.
- #5 : tout prêt ouvert bloque. `lent` → « Prêté jusqu'au <end_date> », même en retard ; sinon `requested` ou
  `accepted` non terminé → « En attente de prêt », même pour des dates futures ; sinon « Disponible ».
- #8 : pg_trgm + unaccent. Tolérance aux fautes de frappe et aux accents ; tri par score sur le nom puis la
  description. Deux extensions PostgreSQL par migration et fixture de test ; ADR 0016 (`accepted`).
- #28 : archiver avant. L'utilisateur archive (`/opsx:archive`) les changements terminés et liste-de-contacts ;
  les deltas MODIFIED de `recherche`, `photo-outil` et `contacts` s'écrivent ensuite contre `openspec/specs/`.
- #31 (nouvelle) Bouton « Emprunter » dans ce changement : affiché grisé sur toutes les cartes, avec
  « Bientôt disponible » ; le second changement l'active.
- #27 : les outils `out_of_order` n'apparaissent pas chez les contacts (ni leur photo) ; `needs_repair` est
  listé avec son état et reste disponible.
- #10 : bouton « Trouver un outil » dans la barre de navigation, pour un utilisateur connecté.
- #16 : en-tête minimal « Prénom Nom (@nom d'utilisateur) », puis la section des outils ; aucune coordonnée.
- #37 (second passage) : sous-chaîne exacte dans le nom d'abord. Tri : exact dans le nom, score nom,
  score description, `lower(name)`, `id` (remplace le tri de #35).

## Ajouts à la rédaction et à la grille (step 6-7)

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 38 | Message d'un type de recherche inconnu, maintenant que « Outil » existe ? | « Ce type de recherche n'est pas disponible » (sans « encore »). | Inferred de `openspec/specs/recherche/spec.md` (exigence « Recherche trop courte ou sans résultat ») | convention |
| 39 | Liste vide sur la page d'un contact ? | « <prénom> <nom> n'a encore aucun outil à prêter » ; « Aucun outil ne correspond à ces filtres » partout. | Inferred de #25 | convention |
| 40 | Valeur invalide de `available`, outil sans description ? | `available` coché seulement pour `1` ; pas de description affichée. | Inferred de #7 | convention |
| 41 | Retour à la liste d'origine (#22) ? | Sans objet dans ce changement (aucun formulaire d'emprunt) ; le filtre renvoie vers l'endpoint courant. Reporté au second changement. | Inferred de #1, #31 | convention |
