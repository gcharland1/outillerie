# livraison-continue Specification

## Purpose
Fixer comment un commit de `main` passe en production sur le serveur : quand il est déployable,
comment le déploiement se protège (sauvegarde, vérification, retour arrière) et comment son résultat
est publié.

## Requirements

### Requirement: Tests du commit mergé
La CI MUST lancer le job de tests (lint, vérification des migrations, pytest, diagramme du schéma)
et le job de validation des specs sur chaque `push` vers `main`, en plus des pull requests.

#### Scenario: Merge d'une PR
- **WHEN** une PR est mergée sur `main`
- **THEN** un run de la CI déclenché par `push` s'exécute sur le commit de `main` qui en résulte
- **AND** ce run comprend les jobs `tests` et `specs`

### Requirement: Commit déployable
Le serveur MUST considérer un commit comme vert seulement si un run de la CI déclenché par `push` sur
`main` pour ce commit est terminé avec succès et que ses jobs `tests` et `specs` ont tous deux réussi.
Un statut de commit, dont celui que pose le déploiement, MUST NOT compter comme résultat de CI.

#### Scenario: Run réussi
- **WHEN** le run `push` d'un commit de `main` est terminé, avec `tests` et `specs` réussis
- **THEN** le commit est vert

#### Scenario: Run en cours
- **WHEN** le run `push` d'un commit est en file ou en cours
- **THEN** le commit n'est pas vert et le serveur réessaie au passage suivant

#### Scenario: Aucun run
- **WHEN** un commit de `main` n'a aucun run `push`
- **THEN** le commit n'est pas vert, sans que ce soit une erreur

#### Scenario: Job sauté
- **WHEN** le run est réussi mais le job `tests` ou `specs` est sauté ou absent
- **THEN** le commit n'est pas vert

#### Scenario: Run de pull request
- **WHEN** seul un run déclenché par `pull_request` est réussi pour un commit
- **THEN** le commit n'est pas vert

#### Scenario: Run relancé
- **WHEN** un run en échec est relancé et sa dernière tentative réussit
- **THEN** le commit est vert

### Requirement: Choix du commit à déployer
Le serveur SHALL vérifier toutes les 5 minutes s'il existe un commit à déployer. Il MUST choisir le
plus récent commit vert de `main` qui descend du commit déployé, n'a pas déjà échoué au déploiement et
diffère du commit déployé.

#### Scenario: Nouveau commit vert
- **WHEN** le dernier commit de `main` est vert et descend du commit déployé
- **THEN** le serveur le déploie

#### Scenario: Tête de main rouge
- **WHEN** le dernier commit de `main` est rouge et qu'un commit antérieur, descendant du commit déployé, est vert
- **THEN** le serveur déploie ce commit antérieur

#### Scenario: Rien de nouveau
- **WHEN** aucun commit vert ne descend du commit déployé
- **THEN** le serveur ne fait rien

#### Scenario: Commit déjà en échec
- **WHEN** le seul commit vert candidat a déjà échoué au déploiement
- **THEN** le serveur ne le retente pas

### Requirement: Un seul déploiement à la fois
Le serveur MUST NOT exécuter deux déploiements en même temps.

#### Scenario: Lancement pendant un déploiement
- **WHEN** un déploiement démarre alors qu'un autre est en cours
- **THEN** le second s'arrête sans rien modifier

### Requirement: Sauvegarde avant déploiement
Avant de modifier quoi que ce soit, le serveur MUST sauvegarder la base de production dans un dossier
hors du checkout, lisible par le seul compte de service, et MUST conserver les 10 dernières
sauvegardes. Une sauvegarde en échec MUST empêcher le déploiement.

#### Scenario: Sauvegarde réussie
- **WHEN** un déploiement commence
- **THEN** une sauvegarde de la base est écrite avant le checkout du commit
- **AND** au plus 10 sauvegardes sont conservées

#### Scenario: Sauvegarde en échec
- **WHEN** la sauvegarde échoue
- **THEN** le serveur ne déploie pas et la version en marche continue de servir

### Requirement: Checkout intact
Le serveur MUST refuser de déployer quand un fichier suivi par git a été modifié dans le checkout de
production, et MUST NOT effacer de fichier non suivi ni ignoré.

#### Scenario: Fichier modifié à la main
- **WHEN** un fichier suivi du checkout de production a été modifié
- **THEN** le serveur ne déploie pas et publie un échec
- **AND** le commit visé n'est pas marqué en échec

#### Scenario: Fichiers ignorés
- **WHEN** un déploiement met à jour le checkout
- **THEN** le `.env` et les fichiers ignorés par git sont intacts

### Requirement: Build avant arrêt
Le serveur MUST construire l'image du commit avant d'arrêter la version en marche. Un build en échec
MUST laisser la version en marche intacte.

#### Scenario: Build en échec
- **WHEN** la construction de l'image échoue
- **THEN** la version en marche continue de servir

### Requirement: Vérification après démarrage
Le serveur MUST considérer un déploiement réussi seulement si l'app devient saine dans les 120
secondes qui suivent son démarrage.

#### Scenario: App saine
- **WHEN** l'app répond à son healthcheck dans le délai
- **THEN** le commit devient le commit déployé

#### Scenario: Migration en échec
- **WHEN** la migration Alembic échoue au démarrage
- **THEN** le déploiement est en échec

### Requirement: Retour à la version précédente
Quand la nouvelle version ne devient pas saine, le serveur MUST relancer la version précédente avec
son image et sa configuration, sans annuler ni appliquer de migration, et MUST marquer le commit en
échec.

#### Scenario: Nouvelle version malsaine
- **WHEN** l'app du nouveau commit ne devient pas saine
- **THEN** le serveur relance l'image et le checkout du commit déployé précédemment
- **AND** il n'annule aucune migration
- **AND** le commit est marqué en échec

#### Scenario: Migration appliquée puis app malsaine
- **WHEN** le nouveau commit applique une migration puis son app ne devient pas saine
- **THEN** la version précédente redémarre sans lancer de migration et devient saine
- **AND** la base garde la révision appliquée

#### Scenario: Retour arrière en échec
- **WHEN** la version précédente ne devient pas saine non plus
- **THEN** le serveur publie un échec, journalise l'état et ne tente plus rien jusqu'à une intervention manuelle

### Requirement: Échec transitoire
Un échec qui ne vient pas du code déployé (API GitHub, réseau, sauvegarde, build, espace disque)
MUST NOT marquer le commit en échec. Le serveur SHALL le retenter au plus 3 fois.

#### Scenario: API indisponible
- **WHEN** l'API GitHub répond une erreur ou une limite de débit
- **THEN** le serveur ne déploie pas, ne marque aucun commit en échec et réessaie au passage suivant

#### Scenario: Trois échecs de build
- **WHEN** le build d'un même commit a échoué 3 fois
- **THEN** le serveur ne le retente plus

### Requirement: Statut publié
Le serveur SHALL poser sur le commit déployé un statut `deploiement` qui indique seulement le succès
ou l'échec. Le statut MUST NOT contenir de détail d'erreur ; le détail va dans le journal du serveur.

#### Scenario: Déploiement réussi
- **WHEN** un déploiement réussit
- **THEN** le commit porte le statut `deploiement` à `success`

#### Scenario: Déploiement en échec
- **WHEN** un déploiement échoue
- **THEN** le commit porte le statut `deploiement` à `failure`, sans message d'erreur
- **AND** le détail est dans le journal du serveur

#### Scenario: Statut impossible à poser
- **WHEN** l'API refuse le statut (jeton expiré ou révoqué)
- **THEN** l'échec est journalisé et le résultat du déploiement n'en dépend pas

### Requirement: Secrets hors des journaux
Le serveur MUST NOT écrire dans ses journaux ni passer en argument de commande le jeton GitHub ou une
valeur du `.env`.

#### Scenario: Journal d'un déploiement
- **WHEN** un déploiement, réussi ou en échec, est journalisé
- **THEN** le journal ne contient ni le jeton ni une valeur du `.env`

### Requirement: Nettoyage des images
Après un déploiement réussi, le serveur SHALL conserver l'image du commit déployé et celle du
précédent, et MUST supprimer les autres images de l'app sans toucher aux volumes ni aux données.

#### Scenario: Troisième déploiement
- **WHEN** un troisième commit est déployé avec succès
- **THEN** seules les images des deux derniers commits déployés restent
