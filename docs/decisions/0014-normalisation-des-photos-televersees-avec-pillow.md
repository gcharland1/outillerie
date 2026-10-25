---
status: accepted
date: 2026-10-25
decision-makers: Gabriel Charland
---

# Normalisation des photos téléversées avec Pillow

## Contexte et problème

Un voisin joint une photo à un outil (issue #20). L'ADR 0008 fixe où vivent les octets (`bytea`
dans `tool_photo`), mais pas ce qu'on accepte ni ce qu'on garde. Une photo de téléphone pèse 3 à
8 Mo, porte souvent la géolocalisation du domicile dans ses EXIF, et un fichier de quelques Ko
peut déclarer des dimensions qui épuisent la mémoire au décodage. L'ADR 0008 suppose une base de
quelques centaines de Mo. Servir l'image se heurte aussi au `Cache-Control: no-store` que l'application
pose sur toute réponse à un utilisateur connecté, pour qu'une page ne reste pas lisible sur un poste
partagé après la déconnexion (ADR 0006) : chaque liste d'outils retéléchargerait toutes ses
vignettes. Changement OpenSpec : `openspec/changes/photo-des-outils/`.

## Options considérées

* Pillow, normalisation : décodage, plafonds, réduction, réencodage JPEG, métadonnées retirées
* Pillow, format d'origine conservé (PNG, WebP), réduction et métadonnées retirées
* Pillow, vérification et retrait des métadonnées seulement, original conservé jusqu'à 10 Mo
* Aucune bibliothèque : vérification de la signature du fichier

Pour la mise en cache de l'image :

* `no-store` conservé, comme pour toute réponse à un utilisateur connecté
* `private, no-cache` avec un ETag calculé sur le contenu, revalidé à chaque affichage
* `private, max-age` avec une URL versionnée (`?v=<empreinte>`)

## Décision

Option retenue : « Pillow, normalisation », parce qu'un seul passage vérifie le contenu réel,
retire la géolocalisation, borne la mémoire et garde la base dans le budget de l'ADR 0008.

Règles :

* Formats acceptés : JPEG, PNG, WebP, reconnus par décodage, jamais par l'extension ni par le
  type annoncé par le navigateur.
* Fichier d'au plus 10 Mo, contrôlé par la vue ; `MAX_CONTENT_LENGTH` = 16 Mo en garde-fou pour
  toute requête (page 413).
* Image d'au plus 40 Mpx, contrôlé sur l'en-tête avant le décodage complet.
* Orientation EXIF appliquée, puis réduction à 1600 px sur le grand côté (jamais d'agrandissement),
  réencodage JPEG qualité 85, sans aucune métadonnée. La transparence est aplatie sur fond blanc.
* Le type de contenu enregistré est celui de la sortie (`image/jpeg`), et l'original n'est pas
  conservé.
* Ce traitement vit dans le module unique d'accès aux photos de l'ADR 0008.

Pour le cache, option retenue : « `private, no-cache` avec un ETag », parce qu'une image inchangée
n'est plus retransmise (réponse 304) et qu'une image remplacée s'affiche dès la page suivante, sans
toucher à l'URL stable de l'ADR 0008. Règles :

* Seule la route de l'image (`tools.photo`) est exemptée du `no-store` ; l'exemption est nommée
  dans le hook, pour qu'aucune autre vue n'en sorte sans le dire.
* L'image porte `Cache-Control: private, no-cache`, un ETag calculé sur son contenu et
  `X-Content-Type-Options: nosniff` ; elle n'est jamais `public`.

### Conséquences

* Bon, parce qu'un fichier piégé (polyglotte, SVG, bombe de décompression) n'est jamais stocké ni
  servi : seul ce que Pillow a décodé puis réencodé l'est.
* Bon, parce qu'une photo stockée pèse quelques centaines de Ko : l'hypothèse de taille de
  l'ADR 0008 tient.
* Bon, parce que la géolocalisation ne quitte jamais le poste du propriétaire.
* Mauvais, parce que l'original est perdu : un futur affichage plus grand que 1600 px, ou un
  autre format de sortie, ne pourra pas regénérer les photos existantes.
* Mauvais, parce que la transparence d'un PNG est perdue et qu'un dessin au trait subit les
  artefacts du JPEG.
* Bon, parce qu'afficher une liste ne coûte qu'une requête conditionnelle par vignette, et
  qu'aucun cache partagé (proxy) ne garde l'image.
* Mauvais, parce que l'image peut rester dans le cache du navigateur après la déconnexion, sur un
  poste partagé : c'est la seule exception à la règle de l'ADR 0006, acceptée pour une photo
  d'outil qui ne contient plus de métadonnées.
* Mauvais, parce que Pillow est une dépendance native de plus, à tenir à jour pour ses failles
  de sécurité, et que le décodage occupe la requête et la mémoire de Flask.
