# Tasks

## 1. Barre de navigation

- [x] 1.1 `base.html` : champ « Rechercher… » et bouton « Rechercher », sans `select` ; `site.css` sans les règles du `select` de la barre ; tests de navigation réécrits (champ et bouton, aucun menu de type)

## 2. Section « Utilisateurs »

- [x] 2.1 `catalog.contact_ids_query` (ex-`_contact_ids`) ; `contacts.RELATION_FILTERS` et `read_relation_filter` ; `_matching_users` filtre par relation avant le `LIMIT 26` ; tests (« Mes contacts uniquement », « Pas en contact uniquement » avec demandes envoyée et reçue, valeur inconnue, filtre avant le plafond)
- [x] 2.2 `search.results` : `type` ignoré, moins de 3 caractères sans section, 5 comptes repliés et 25 dépliés (`more=1` seulement), compteur « X de Y » ou « X de plus de 25 », message de plafond seulement déplié, « Aucun résultat d'utilisateur » ; tests (anciennes adresses `type=tool` et `type=lieu`, 3, 12, 25 et 26 comptes, état déplié inconnu ou avec peu de comptes, comptes supprimés)
- [x] 2.3 `search/results.html` : formulaire GET de filtres (`q` et `more` cachés, relation, distance désactivée « Aucune limite » et « à venir », « Filtrer »), compteur, « Voir plus » ; tests (filtre affiché sans résultat et sélectionné, distance ignorée, filtre qui garde l'état déplié)

## 3. Section « Outils »

- [x] 3.1 `search.results` : outils visibles par pertinence, 6 cartes, « X de Y », « Voir plus » vers « Trouver un outil » avec le texte, « Aucun résultat d'outil » ; provenance `find` avec `q` ; tests (2 et 8 outils, outil d'un non-contact absent, sans contact, filtre de relation sans effet, « Annuler » d'un emprunt)

## 4. Retour après une demande

- [x] 4.1 Champs cachés `relation` et `more` dans chaque formulaire « Envoyer une demande » ; `send_request` les relit en liste blanche, sans `type` ; tests (retour filtré et déplié, valeurs falsifiées), tests de contacts mis à jour

## 5. Libellés

- [x] 5.1 `index.html` : « Voir tous mes prêts » devient « Voir plus » ; `index.html` et `tools/_cards.html` : « Cherchez un utilisateur avec la barre de recherche », sans lien ; tests de l'accueil, de « Trouver un outil » et des couleurs

## 6. Fin

- [x] 6.1 `/verifier` rend « terminé »
