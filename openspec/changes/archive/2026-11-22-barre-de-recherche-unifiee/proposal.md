# Proposal

## Why

La barre de recherche demande de choisir « Outil » ou « Utilisateur » avant de chercher ; chercher
« Mr Burn » en type « Outil » ne trouve rien. L'issue #57 demande une barre unique dont les
résultats montrent à la fois les utilisateurs et les outils, et des filtres pour trouver plus
facilement des utilisateurs.

Les décisions et leur source sont dans [questions.md](questions.md). Décisions d'architecture :
ADR 0001 (sans JavaScript), ADR 0011 (blueprint `search` étendue), ADR 0018 (règles des champs de
recherche), ADR 0022 (couleurs des boutons), ADR 0023 (comptes supprimés exclus). Aucun nouvel ADR.

## What Changes

- Barre de navigation : un champ « Rechercher… » et le bouton « Rechercher », sans menu de type.
- Page « Résultats de recherche » en deux sections :
  - « Utilisateurs » : 5 comptes et « X de Y » (« plus de 25 » au-delà), « Voir plus » qui déplie la
    même page jusqu'à 25 comptes, le message de plafond actuel seulement dans la vue dépliée ;
    filtre « Tous les utilisateurs » / « Mes contacts uniquement » / « Pas en contact uniquement »
    et sélecteur de distance grisé « à venir » ;
  - « Outils » : 6 cartes des outils visibles des contacts et « X de Y », « Voir plus » vers
    « Trouver un outil » filtré par le texte.
- Messages vides « Aucun résultat d'utilisateur » et « Aucun résultat d'outil ».
- Le paramètre `type` est ignoré ; la redirection vers « Trouver un outil » disparaît.
- Après « Envoyer une demande », retour aux résultats avec le texte, le filtre et l'état déplié.
- « Voir plus » partout : « Voir tous mes prêts » de l'accueil est renommé. Les liens « ouvrez la
  recherche d'utilisateurs » deviennent « Cherchez un utilisateur avec la barre de recherche ».
- Remplace la décision de l'issue #40 (plafonner la recherche d'utilisateurs) de n'offrir ni total
  ni « Voir plus » : un compteur et un « Voir plus » s'ajoutent, toujours sans pagination ni total
  exact au-delà de 25.

Hors périmètre : un vrai filtre de distance (issue future, avec un ADR : géocodage, schéma, vie
privée) ; pagination au-delà de 25 comptes.

Closes #57.

## Capabilities

### New Capabilities

### Modified Capabilities
- `recherche` : barre sans type, sections « Utilisateurs » et « Outils », compteurs, « Voir plus »,
  filtre de relation, sélecteur de distance, retour après une demande ; retrait de la recherche de
  type « Outil ».
- `accueil` : « Voir plus » sous un groupe de prêts ; texte vers la barre de recherche sans contact.
- `outils-des-contacts` : texte vers la barre de recherche sans contact.
- `interface` : scénarios des boutons bleus (« Voir plus », « Filtrer » des résultats).

## Impact

`application/app/search.py`, `application/app/contacts.py` (retour après une demande),
`application/app/catalog.py` (sous-requête des contacts rendue publique), gabarits `base.html`,
`search/results.html`, `index.html`, `tools/_cards.html`, `static/site.css`, tests. Aucun schéma,
aucune dépendance.
