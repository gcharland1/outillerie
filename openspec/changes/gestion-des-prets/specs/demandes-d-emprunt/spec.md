# Spec Delta

## MODIFIED Requirements

### Requirement: Page « Mes prêts »
Le menu du compte SHALL offrir « Mes prêts », une page à deux listes : « Mes prêts », les prêts et
demandes des outils de l'utilisateur, et « Mes emprunts », les siens. Chaque ligne montre l'outil,
l'autre personne, les dates, le message, les dates de remise et de retour connues et le statut :
« En attente », « Expirée », « Attente de récupération », « Remise à confirmer », « Prêté »,
« En retard », « Retour à confirmer », « Complété », « Refusée » ou « Annulée ». Session requise.

#### Scenario: Demandes reçues et envoyées
- **WHEN** Alice a demandé la perceuse de Bob et Bob a demandé la scie d'Alice
- **THEN** la liste « Mes emprunts » d'Alice montre sa demande de la perceuse
- **AND** sa liste « Mes prêts » montre la demande de Bob pour sa scie

#### Scenario: Entrée du menu
- **WHEN** un utilisateur connecté ouvre une page du site
- **THEN** son menu du compte contient « Mes prêts »

#### Scenario: Dates de remise et de retour
- **WHEN** Alice a reçu la perceuse de Bob le 3 novembre 2026 et Bob a reçu son retour le 5 novembre 2026
- **THEN** la ligne affiche « Prêté le 3 novembre 2026 » et « Complété le 5 novembre 2026 »

### Requirement: Ordre et couleurs de « Mes prêts »
Chaque liste de « Mes prêts » SHALL montrer d'abord les prêts en retard, de la date de fin la plus
ancienne à la plus récente, puis les lignes sur lesquelles l'utilisateur peut agir, puis les autres,
ces deux groupes de la plus récente à la plus ancienne selon la date d'envoi. « Accepter » SHALL
être affiché en vert, et « Refuser », « Annuler le prêt » et « Pas reçu » en rouge.

#### Scenario: Ordre des demandes
- **WHEN** Bob a reçu, dans cet ordre, des demandes de la scie, de la perceuse, de la ponceuse et du rabot
- **AND** il a refusé celle de la scie et celle de la ponceuse est « Complété »
- **THEN** sa liste « Mes prêts » est dans l'ordre : rabot, perceuse, ponceuse, scie

#### Scenario: Retards d'abord
- **WHEN** Bob a une demande en attente pour son rabot, et sa scie et sa perceuse sont en retard, la scie depuis plus longtemps
- **THEN** sa liste « Mes prêts » est dans l'ordre : scie, perceuse, rabot

#### Scenario: Couleur des réponses
- **WHEN** Bob a une demande reçue en attente
- **THEN** « Accepter » est affiché en vert et « Refuser » en rouge

### Requirement: Pastille des demandes d'emprunt
Quand un utilisateur a des prêts qui attendent son action, chaque page SHALL afficher leur nombre
dans une pastille à côté de « Mes prêts » dans le menu du compte. Comptent : pour le propriétaire,
les demandes reçues en attente non expirées, les retours à confirmer et les prêts de ses outils en
retard ; pour l'emprunteur, les remises à confirmer et ses prêts en retard.

#### Scenario: Une demande reçue
- **WHEN** Alice a demandé la perceuse de Bob et Bob ouvre une page du site
- **THEN** une pastille « 1 » est affichée à côté de « Mes prêts »

#### Scenario: Demande expirée hors de la pastille
- **WHEN** la seule demande reçue par Bob est expirée
- **THEN** aucune pastille n'est affichée à côté de « Mes prêts »

#### Scenario: Retour à confirmer
- **WHEN** Alice a déclaré avoir rendu la perceuse de Bob
- **THEN** Bob voit une pastille « 1 » à côté de « Mes prêts » et Alice n'en voit aucune

#### Scenario: Remise à confirmer
- **WHEN** Bob a déclaré avoir remis sa perceuse à Alice
- **THEN** Alice voit une pastille « 1 » à côté de « Mes prêts » et Bob n'en voit aucune

#### Scenario: Prêt en retard
- **WHEN** Alice a la perceuse de Bob et sa date de fin était hier
- **THEN** Alice et Bob voient chacun une pastille « 1 » à côté de « Mes prêts »
