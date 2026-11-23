## MODIFIED Requirements

### Requirement: Lignes de « Gestion des prêts » limitées
Chaque groupe de la section SHALL afficher au plus 5 lignes, dans son ordre ; sous un groupe qui en
a davantage, un bouton « Voir plus » mène à « Mes prêts ».

#### Scenario: Plus de 5 lignes dans un groupe
- **WHEN** Alice a reçu 6 demandes d'emprunt
- **THEN** le groupe « Demandes reçues » affiche les 5 premières et un bouton « Voir plus » qui mène à « Mes prêts »

#### Scenario: 5 lignes ou moins
- **WHEN** Alice a reçu 5 demandes d'emprunt
- **THEN** le groupe « Demandes reçues » affiche les 5 et pas de bouton « Voir plus »

#### Scenario: Bouton par groupe
- **WHEN** Alice a 6 emprunts en cours et prête 2 outils
- **THEN** seul le groupe « Mes emprunts » a un bouton « Voir plus »

### Requirement: Sections vides
Une section sans ligne SHALL rester affichée avec un message : « Aucun prêt en cours »,
« Aucune demande de contact » et « Aucun nouvel outil depuis 30 jours ». Sans contact, « Nouveaux
outils » affiche « Vous n'avez encore aucun contact » et « Cherchez un utilisateur avec la barre de
recherche ».

#### Scenario: Nouveau compte
- **WHEN** Alice vient de créer son compte et ouvre `/`
- **THEN** la page répond 200 et affiche « Aucun prêt en cours », « Aucune demande de contact » et « Vous n'avez encore aucun contact »
- **AND** elle affiche « Cherchez un utilisateur avec la barre de recherche »

#### Scenario: Contacts sans nouvel outil
- **WHEN** Alice a des contacts qui n'ont ajouté aucun outil depuis 30 jours
- **THEN** la section « Nouveaux outils » affiche « Aucun nouvel outil depuis 30 jours »
