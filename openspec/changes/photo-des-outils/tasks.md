# Tasks

## 1. Décision et dépendance

- [x] 1.1 Faire accepter par l'utilisateur l'ADR 0014 « Normalisation des photos téléversées avec Pillow » ; vérifier que son `status` et l'index `docs/decisions/README.md` indiquent `accepted`
- [x] 1.2 `uv add pillow` ; vérifier que `uv.lock` est modifié, que `uv run pytest` passe et que `docker compose up --build` démarre l'application

## 2. Module `app/photos.py`

- [x] 2.1 Fixtures d'images générées en mémoire dans `tests/conftest.py` (JPEG, PNG transparent, WebP, GIF, PNG 10 000 × 5 000, JPEG tronqué, JPEG 4000 × 3000 avec EXIF GPS, JPEG 3000 × 4000 couché avec orientation 6) ; vérifier que `uv run pytest --collect-only` les trouve
- [x] 2.2 `normalize()` et `PhotoRejected` selon le design (taille mesurée sans lecture, en-tête avant décodage, plafond 40 Mpx, `exif_transpose`, fond blanc, `thumbnail` 1600, JPEG 85 sans métadonnées) ; vérifier par des tests pytest chaque message de refus de la spec, la réduction 4000 × 3000 → 1600 × 1200, la petite image non agrandie, l'absence d'EXIF, l'orientation en portrait, le PNG transparent devenu JPEG
- [x] 2.3 `save_photo`, `remove_photo` (idempotent), `load_photo`, `tool_ids_with_photo`, `can_view_photo` ; vérifier par des tests pytest le remplacement, le retrait d'une photo absente sans erreur, `tool_ids_with_photo` sans chargement de `content`, `can_view_photo` vrai pour le propriétaire seulement
- [x] 2.4 Test garde-fou : `ToolPhoto` et `.photo` n'apparaissent dans `application/app/` que dans `photos.py` ; vérifier qu'il passe, et qu'il échoue si on ajoute un usage dans `tools.py`

## 3. Formulaire d'outil

- [x] 3.1 `tools/form.html` : `enctype="multipart/form-data"`, champ de photo avec `accept`, aperçu et case « Retirer la photo » en modification si une photo existe (case remplacée par 8.3), styles dans `site.css` ; vérifier par des tests pytest la présence du champ dans les deux formulaires, de l'aperçu et de la case seulement s'il y a une photo
- [x] 3.2 `new` : photo validée avant `db.session.add`, outil et photo dans un seul `commit` ; vérifier par des tests pytest l'outil créé avec sa photo, l'outil créé sans fichier, et le refus (GIF) qui ne crée aucun outil, réaffiche le nom saisi et « Choisissez de nouveau la photo »
- [x] 3.3 `edit` : photo ajoutée, remplacée, inchangée sans fichier, retirée par la case, fichier prioritaire sur la case (règle remplacée par 8.3 : un fichier ne compte qu'avec « Modifier l'image »), retrait déjà fait sans erreur ; refus qui laisse nom et photo intacts et réaffiche la saisie ; vérifier chaque scénario de la spec par un test pytest, et le 404 pour l'outil de `bob`
- [x] 3.4 Vérifier par un test pytest (`csrf_client`) qu'un envoi multipart avec le jeton est accepté et qu'un envoi sans jeton est refusé sans modifier la photo

## 4. Limites de taille

- [x] 4.1 `MAX_CONTENT_LENGTH = 16 Mo` dans `_initialize_app()` avant la branche `test_config` ; `@app.errorhandler(RequestEntityTooLarge)` et gabarit `too_large.html` (« Envoi trop volumineux », lien vers « Mes outils »), statut 413 ; vérifier par un test pytest, limite abaissée, le 413, la page en français et l'outil inchangé

## 5. Route de l'image

- [x] 5.1 `GET /tools/<int:tool_id>/photo` (`tools.photo`) : 404 pour visiteur, autre compte, outil inconnu ou sans photo ; photo servie pour un outil en circulation ou retiré ; vérifier chaque scénario « Accès à l'image » par un test pytest
- [x] 5.2 En-têtes : `private, no-cache`, `ETag` sur le contenu, `nosniff`, 304 sur `If-None-Match` ; hook `no-store` qui saute `tools.photo` ; vérifier par des tests pytest les en-têtes, le 304, la nouvelle photo après remplacement avec l'ancienne étiquette, et que les autres pages gardent `no-store` (`tests/test_navigation.py`)

## 6. Affichage dans l'inventaire

- [x] 6.1 `mine` et `retired` passent `tool_ids_with_photo` ; vignette `<img class="tool-thumb" alt="<nom>">` dans `tools/mine.html` et `tools/retired.html`, rien sans photo ; vérifier par des tests pytest la vignette et son `alt`, l'absence d'image sans photo, et la vignette d'un outil retiré

## 7. Vérification

- [x] 7.1 Vérifier à la main dans `docker compose up --build` : joindre une vraie photo de téléphone, la voir dans « Mes outils », la remplacer, la retirer, essayer un fichier de plus de 16 Mo
- [x] 7.2 Lancer `/verifier` ; il doit rendre « terminé »

## 8. Retours de QA

- [x] 8.1 (Boutons radio remplacés par les cases de 8.3.) Formulaire de modification d'un outil qui a une photo : boutons radio `photo_action` « Modifier l'image » (champ de fichier grisé par CSS tant qu'il n'est pas coché) et « Retirer l'image » (retrait définitif annoncé), aucun coché à l'ouverture, choix recoché après une erreur ; « Ajouter une image » sinon ; vérifier par des tests pytest chaque scénario de l'exigence « Modifier ou retirer l'image » et le libellé « Ajouter une image »
- [x] 8.2 Vérifier à la main, sans JavaScript à activer : le champ grisé tant que « Modifier l'image » n'est pas choisi, actif ensuite ; « Retirer l'image » décoche « Modifier l'image » ; puis relancer `/verifier`

- [x] 8.3 Remplacer les boutons radio par deux cases décochables `replace_photo` et `remove_photo` : verrou mutuel et avertissement « les deux cochées » en CSS (`:has()`), refus côté serveur des deux cases cochées ; vérifier par des tests pytest chaque scénario de l'exigence « Modifier ou retirer l'image »
- [x] 8.4 Vérifier à la main : une case cochée verrouille l'autre, la décocher la libère, le champ de fichier suit « Modifier l'image », l'avertissement apparaît et « Enregistrer » est grisé si les deux sont cochées au clavier ; enregistrer une description après avoir décoché ; puis relancer `/verifier`

## 9. Seconde relecture

- [x] 9.1 Décider d'après le formulaire envoyé, pas d'après la base : champ caché `had_photo` ; « Retirer l'image » ignore tout fichier ; les deux cases refusées même si la photo a disparu entre-temps ; fichier envoyé depuis un formulaire sans photo, alors que l'outil en a reçu une, refusé (« Choisissez la nouvelle image ») ; `aria-label` du champ de fichier ; vérifier par des tests pytest les cas d'onglet périmé

## Workflow follow-up

- Relecture par l'agent `relecteur` avant la PR ; la PR ferme #20.
- `/opsx:archive` une fois mergé.
- Numéro d'ADR : `configuration-de-deploiement` a aussi un ADR 0014, non commité ; si cette PR est mergée la première, il devient 0015.
