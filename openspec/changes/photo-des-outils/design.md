# Design

## Context

Voir `proposal.md` pour le pourquoi et `specs/photo-outil/spec.md` pour le comportement. Les
questions tranchées pendant le cadrage, leur source et qui les a tranchées sont dans
`questions.md`.

État actuel :

- `tool_photo` existe : `tool_id` (PK, FK `ON DELETE CASCADE`), `content` (`bytea`),
  `content_type`, `created_at` ; `Tool.photo` est chargé à la demande (`application/models/tool.py:43-52`).
- `tools/form.html` sert à l'enregistrement et à la modification, sans `enctype`.
  `_read_tool_form` renvoie `(values, error)` ; la vue `flash` l'erreur et réaffiche `values`.
- Un `after_request` pose `Cache-Control: no-store` sur toute réponse à un utilisateur connecté et
  écrase ce que la vue a posé (`application/app/__init__.py:34-38`).
- `CSRFProtect` lit `request.form` dans un `before_request` : un dépassement de
  `MAX_CONTENT_LENGTH` lève 413 avant la vue (Flask-WTF 1.3.0, `csrf.py:231-244`).
- Flask 3.1.3 / Werkzeug 3.1.9 : `MAX_FORM_MEMORY_SIZE` (500 Ko) et `MAX_FORM_PARTS` (1000)
  lèvent aussi 413 ; un fichier téléversé au-delà de 500 Ko est mis sur disque
  (`SpooledTemporaryFile`).

## Goals / Non-Goals

**Goals:**

- Un seul module connaît le stockage et le traitement des photos (ADR 0008, ADR 0014).
- Une photo refusée ne laisse aucun état partiel : outil et photo écrits dans un seul `commit`.
- Charger une liste d'outils ne charge jamais les octets des photos.

**Non-Goals:**

- Traitement asynchrone des images : le décodage reste dans la requête, borné par le plafond de
  pixels.
- Colonne de version ou `updated_at` : l'ETag se calcule sur le contenu.

## Decisions

### Module `app/photos.py`, seul accès à `ToolPhoto`

Fonctions :

- `normalize(file_storage) -> bytes` : lève `PhotoRejected(message)` ;
- `save_photo(tool, jpeg_bytes)` ;
- `remove_photo(tool)` ;
- `load_photo(tool) -> StoredPhoto | None` (octets et type de contenu, jamais la ligne `ToolPhoto`) ;
- `tool_ids_with_photo(tool_ids) -> set[int]` ;
- `can_view_photo(user, tool) -> bool`.

Ni `save_photo` ni `remove_photo` ne font de `commit` : la vue commite l'outil et la photo
ensemble. Un test garde-fou échoue si `ToolPhoto` ou `.photo` est utilisé hors de `app/photos.py`,
`models/` et des tests.

Alternative écartée : méthodes sur le modèle `Tool`. Elles mêleraient le traitement d'image au
modèle, et la migration vers S3 de l'ADR 0008 toucherait `models/`.

### Normalisation (ADR 0014), dans `normalize`

1. Mesurer la taille par `stream.seek(0, SEEK_END)` / `tell()`, sans lire le fichier : plus de
   10 Mo ⇒ refus. Taille nulle ⇒ « La photo est illisible ».
2. `Image.open` lit l'en-tête : un format hors JPEG/PNG/WebP ⇒ refus de format ; une
   `UnidentifiedImageError` ⇒ refus de format ; `width × height` > 40 Mpx ⇒ refus de taille,
   avant tout décodage.
3. `load()` décode ; toute erreur de décodage (`OSError`, image tronquée) ⇒ « La photo est
   illisible ».
4. `ImageOps.exif_transpose`, puis aplatissement de la transparence sur fond blanc, conversion
   en RVB, `thumbnail((1600, 1600))` (qui n'agrandit jamais), enregistrement en JPEG qualité 85
   sans `exif=` ni `icc_profile=`.

`Image.MAX_IMAGE_PIXELS` est aligné sur 40 Mpx pour que Pillow refuse aussi tout ce qui
échapperait à l'étape 2.

### Formulaire et vues

- `tools/form.html` passe en `enctype="multipart/form-data"`. Sans photo (enregistrement, ou
  modification d'un outil sans photo) : champ « Ajouter une image »,
  `<input type="file" name="photo" accept="image/jpeg,image/png,image/webp">`. Avec une photo :
  aperçu `<img>`, puis deux cases : `replace_photo` « Modifier l'image », suivie du champ de
  fichier, et `remove_photo` « Retirer l'image (définitif) », décochées à l'ouverture. Après une
  erreur, les cases envoyées sont recochées et le message rappelle de choisir de nouveau la photo.
- Des cases plutôt que des boutons radio (retours de QA) : sans JavaScript, un bouton radio ne se
  décoche pas, et le propriétaire doit pouvoir renoncer à un choix tout en enregistrant le reste.
  L'exclusion vient de `site.css` (`:has()`), sans JavaScript (ADR 0001) :
  - une case cochée grise et rend inerte au pointeur l'autre case tant que celle-ci est décochée ;
  - le champ de fichier est grisé tant que « Modifier l'image » n'est pas cochée ;
  - un avertissement, caché par défaut, apparaît si les deux cases sont cochées (le clavier
    contourne le verrou au pointeur), et « Enregistrer » est alors grisé et inerte au pointeur ;
    la touche Entrée envoie quand même le formulaire, que le serveur refuse.
  - « Modifier l'image » sans fichier n'est pas détectable en CSS : seul le serveur le refuse.
  Un navigateur sans `:has()` ne verrouille rien et cache l'avertissement : la règle qui compte
  est côté serveur.
- `new` : le fichier compte s'il est nommé. `edit` : `_read_tool_form`, puis le choix d'image,
  décidé d'après le formulaire envoyé et non d'après la base, qu'un autre onglet a pu changer.
  Un champ caché `had_photo` dit si le formulaire montrait les cases. Le fichier ne compte qu'avec
  `replace_photo`, ou si le formulaire ne montrait pas de photo, et jamais avec `remove_photo`.
  Les deux cases ⇒ « Choisissez Modifier l'image ou Retirer l'image, pas les deux ».
  `replace_photo` sans fichier ⇒ « Choisissez la nouvelle image ». Fichier d'un formulaire sans
  photo pour un outil qui en a reçu une entre-temps ⇒ « Choisissez la nouvelle image » : le
  formulaire réaffiché montre alors les cases.
  Toute erreur ⇒ réaffichage, sans `db.session.add` ni modification de l'outil. Sinon, un seul
  `commit` : fichier retenu ⇒ `save_photo` ; `remove_photo` ⇒ `remove_photo()`, sans erreur si la
  photo est déjà absente.
- Pas d'aperçu de l'image choisie avant l'enregistrement : il exigerait du JavaScript. L'aperçu
  est celui de la photo enregistrée (formulaire de modification, listes).

### Route `GET /tools/<int:tool_id>/photo` (endpoint `tools.photo`)

- Dans la Blueprint `tools` (ADR 0011) ; outil inconnu, d'autrui ou sans photo ⇒ `abort(404)`.
- `can_view_photo(user, tool)` vaut aujourd'hui `tool.owner_id == user.id`. La page des outils
  d'un contact y ajoutera la relation de contact (ADR 0013) : c'est la seule ligne à changer.
- Un visiteur reçoit 404, pas la redirection habituelle vers `/login` : la spec demande la même
  réponse pour tous les refus. La route vérifie donc `current_user.is_authenticated` elle-même,
  sans `@login_required`.
- Réponse : `Response(content, mimetype=content_type)`, `set_etag(sha256(content))`,
  `cache_control.private = True`, `cache_control.no_cache = True`,
  `X-Content-Type-Options: nosniff`, puis `make_conditional(request)` pour le 304.
  `send_file` n'apporte rien : sans chemin, il ne calcule pas d'ETag et ne pose pas `private`.
- Le hook `no-store` saute `request.endpoint == "tools.photo"` (ADR 0014). Alternative écartée : ne pas
  écraser un `Cache-Control` déjà posé, qui laisserait n'importe quelle vue future sortir du
  `no-store` sans le dire.

### Limites de taille

- `MAX_CONTENT_LENGTH = 16 * 1024 * 1024` dans `_initialize_app()`, avant la branche
  `test_config`, pour que les tests en héritent ; un test la baisse pour provoquer le 413 sans
  envoyer 16 Mo.
- `@app.errorhandler(RequestEntityTooLarge)` rend `too_large.html`, calqué sur
  `csrf_error.html`, statut 413, avec un lien vers « Mes outils ». Le message est générique,
  puisque le 413 couvre aussi `MAX_FORM_MEMORY_SIZE` et `MAX_FORM_PARTS`.

### Listes

`mine` et `retired` passent `tool_ids_with_photo([t.id for t in tools])` au gabarit : une seule
requête `SELECT tool_id FROM tool_photo WHERE tool_id IN (...)`, sans charger `content`. La
vignette est `<img src="{{ url_for('tools.photo', tool_id=t.id) }}" alt="{{ t.name }}"
class="tool-thumb">`, dont la taille est fixée par `site.css`.

### Tests

Les images sont générées en mémoire par Pillow : JPEG, PNG transparent, WebP, GIF, PNG
10 000 × 5 000 (en-tête seulement, décodage non requis), JPEG tronqué, JPEG avec EXIF GPS et
orientation. Elles sont envoyées par `data={"photo": (BytesIO, "x.jpg"), ...}` dans
`tests/test_photos.py`, avec des fixtures partagées dans `tests/conftest.py`. Un test vérifie le
formulaire multipart avec le CSRF actif (`csrf_client`).

## Risks / Trade-offs

- [Deux onglets modifient la même photo] → dernier écrit gagne ; si deux onglets créent la
  première photo en même temps, la PK lève `IntegrityError` (500). C'est accepté à l'échelle d'un
  voisinage.
- [Derrière un proxy, un 413 renvoyé sans lire le corps peut apparaître comme une connexion
  coupée] → aucun déploiement n'est configuré (issue #5) ; il faudra poser la même limite au proxy
  (`client_max_body_size`).
- [Le décodage occupe la requête et la mémoire] → le plafond de 40 Mpx borne le pire cas à
  environ 160 Mo en RGBA ; à revoir si le serveur est petit.
- [L'image peut rester dans le cache du navigateur après la déconnexion, sur un poste partagé]
  → elle est privée et revalidée, et la route répond 404 sans session ; c'est accepté
  (ADR 0014).
- [Pillow est une dépendance native] → les wheels embarquent leurs bibliothèques ;
  `docker compose up --build` le confirme à la tâche 1.

## Migration Plan

Aucune migration de schéma. Déploiement : `uv sync` installe Pillow ; reconstruction de l'image
Docker. Retour arrière : revenir au commit précédent ; les photos déjà enregistrées restent en
base, sans écran pour les voir.
