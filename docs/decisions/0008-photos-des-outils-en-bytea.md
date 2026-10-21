---
status: accepted
date: 2026-10-21
decision-makers: Gabriel Charland
---

# Photos des outils en `bytea`

## Contexte et problème

Chaque outil peut avoir une photo (issue #15). Il faut choisir où vivent les octets : le choix
décide de la sauvegarde, des fichiers orphelins possibles et des services à opérer. L'application
tourne en Docker Compose, sans hébergement cible ni stockage objet. Changement OpenSpec :
`openspec/changes/schemas-initiaux/`.

## Options considérées

* `bytea` dans Postgres, dans une table `tool_photo` séparée
* Fichiers sur un volume Docker, chemin dans une colonne
* Stockage objet (S3, MinIO), clé dans une colonne

## Décision

Option retenue : « `bytea` dans `tool_photo` », parce qu'elle n'ajoute aucun service, qu'un seul
`pg_dump` sauvegarde tout et que la suppression d'un outil supprime sa photo dans la même
transaction. À l'échelle d'un voisinage (quelques centaines de Mo), Postgres suffit.

Trois garde-fous gardent la migration vers S3 peu coûteuse :

* Les octets vivent dans `tool_photo`, jamais dans `tool` : lire un outil ne lit pas sa photo.
* La photo est servie par une URL stable, `/tools/<id>/photo` ; aucun gabarit ne contient d'URL
  de stockage.
* Un seul module lit, écrit et supprime les photos ; c'est le seul code qui sait où elles vivent.

Chemin vers S3, selon 0007 :

1. *expand* : colonne `storage_key` nullable ; le module lit S3 si la clé existe, sinon `content` ;
   les nouvelles photos vont dans S3.
2. *backfill* : commande `flask` par lots, idempotente, qui copie chaque `content` et pose la clé.
3. *contract* : suppression de `content`, puis `VACUUM FULL` (ou `pg_repack`) pour rendre l'espace.

Déclencheurs d'un nouvel ADR : taille de la base qui pèse sur les sauvegardes, hébergement sans
stockage Postgres adapté, besoin d'un CDN.

### Conséquences

* Bon, parce qu'aucune photo ne peut devenir orpheline et qu'une seule sauvegarde suffit.
* Bon, parce que la migration vers S3 tient en une commande et deux révisions, sans toucher aux
  gabarits.
* Mauvais, parce que la base et ses sauvegardes grossissent avec chaque photo ; les JPEG ne se
  compressent pas davantage.
* Mauvais, parce que chaque image passe par Flask et par la mémoire de l'application.
