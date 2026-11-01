# Proposal

## Why

Un voisin décrit ses outils par du texte seulement : rien ne montre à quoi ressemble un outil
(issue #20, sous-tâche de #17). Le schéma garde déjà une photo par outil (`tool_photo`, ADR 0008),
mais aucun écran ne permet d'en joindre une, et les règles d'image (formats, tailles,
métadonnées) restaient à fixer.

## What Changes

- Champ « Ajouter une image » dans le formulaire d'enregistrement, et dans celui de modification
  d'un outil sans photo : JPEG, PNG ou WebP, au plus 10 Mo.
- Pour un outil qui a une photo, deux cases décochables dans la modification : « Modifier
  l'image » (active le champ de fichier) et « Retirer l'image (définitif) » ; chacune verrouille
  l'autre tant qu'elle est cochée, et les deux cochées sont refusées. Un fichier n'est enregistré
  qu'avec « Modifier l'image ».
- Normalisation au téléversement : contenu vérifié par décodage, image d'au plus 40 Mpx,
  réduite à 1600 px sur son grand côté, réencodée en JPEG, sans métadonnées (dont la
  géolocalisation), orientation appliquée.
- Erreurs : photo refusée (format, fichier illisible, trop grande) ⇒ formulaire réaffiché avec
  la saisie et un message, rien n'est enregistré, la photo existante reste. Un envoi de plus de
  16 Mo reçoit une page « Envoi trop volumineux » en français.
- Route `GET /tools/<id>/photo`, réservée au propriétaire de l'outil (en circulation ou retiré) ;
  tout autre compte ou un visiteur reçoit 404. Mise en cache privée, revalidée à chaque affichage.
- Vignette dans « Mes outils » et « Mes outils retirés », photo actuelle dans le formulaire de
  modification ; sans photo, rien n'est affiché.

## Capabilities

### New Capabilities
- `photo-outil`: téléversement, normalisation, remplacement, retrait et affichage de la photo
  d'un outil par son propriétaire, et règle d'accès à l'image.

### Modified Capabilities
_Aucune._ Les specs `outils` (changement `schemas-initiaux`) et `inventaire` (changement
`gestion-des-outils`) ne sont pas archivées ; leurs exigences restent vraies : une photo par
outil, remplacement, accès réservé au propriétaire.

## Impact

- Code : nouveau module d'accès aux photos `app/photos.py` (seul à lire, écrire et retirer une
  photo, ADR 0008) ; `app/tools.py` (lecture du fichier, route photo) ; `app/__init__.py`
  (`MAX_CONTENT_LENGTH`, page 413, exemption du `no-store` pour la route photo) ;
  gabarits `tools/form.html`, `tools/mine.html`, `tools/retired.html`, nouvelle page d'erreur
  413 ; `app/static/site.css`.
- Dépendance : `pillow` (`uv add`, `uv.lock` commité).
- Schéma : aucune migration ; `tool_photo` suffit.
- Tests : nouveaux tests pytest du téléversement, de la normalisation, de la route photo, du
  cache et des erreurs ; images de test générées en mémoire.
- ADR : nouveau 0014 « Normalisation des photos téléversées avec Pillow », qui complète 0008 et
  exempte l'image du `no-store` de l'ADR 0006. ADR concernés : 0001 (sans JavaScript), 0006 (exemption du `no-store` pour l'image), 0008
  (route stable, module unique), 0011 (route dans la Blueprint `tools`), 0012 (jeton CSRF sur le
  formulaire multipart).

**Hors périmètre**

- Accès des contacts à la photo (issue #22, ADR 0013) : la règle cible est « le propriétaire et
  ses contacts » ; elle s'ouvrira avec la page qui montre les outils d'un contact.
- Catalogue public et accès anonyme aux photos.
- Plusieurs photos par outil ; recadrage ou rotation manuels ; aperçu avant envoi.
- Formats HEIC, GIF, SVG ; conservation du fichier original.
- Retrait de la photo d'un outil retiré : la modification d'un outil retiré répond 404 ; il faut
  le remettre en circulation d'abord.
