## MODIFIED Requirements

### Requirement: Listes vides
Une liste d'outils vide SHALL afficher un message selon le cas. Sur « Trouver un outil » :
« Vous n'avez encore aucun contact » et « Cherchez un utilisateur avec la barre de recherche », sans
contact ; « Vos contacts n'ont encore aucun outil à prêter » sans outil visible. Sur la page d'un
contact : « <prénom> <nom> n'a encore aucun outil à prêter ». Partout : « Aucun outil ne correspond
à ces filtres » quand les filtres écartent tous les outils.

#### Scenario: Aucun contact
- **WHEN** Alice n'a aucun contact et ouvre « Trouver un outil »
- **THEN** la page affiche « Vous n'avez encore aucun contact » et « Cherchez un utilisateur avec la barre de recherche »

#### Scenario: Contacts sans outil
- **WHEN** Bob, seul contact d'Alice, n'a aucun outil visible
- **THEN** la page « Trouver un outil » d'Alice affiche « Vos contacts n'ont encore aucun outil à prêter »

#### Scenario: Contact sans outil
- **WHEN** Bob Gagnon, contact d'Alice, n'a aucun outil visible et Alice ouvre sa page
- **THEN** la section de ses outils affiche « Bob Gagnon n'a encore aucun outil à prêter »

#### Scenario: Filtres sans résultat
- **WHEN** Bob a une perceuse et Alice cherche « tondeuse »
- **THEN** la page affiche « Aucun outil ne correspond à ces filtres »
