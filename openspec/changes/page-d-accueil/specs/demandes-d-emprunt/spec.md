# Spec Delta

## MODIFIED Requirements

### Requirement: Envoi d'une demande
« Confirmer » SHALL créer une demande en attente pour l'outil, l'utilisateur et les dates, puis
ramener l'utilisateur à la liste d'où il est venu, avec ses filtres et son tri, et afficher
« Demande envoyée à <prénom> <nom> » comme un message de succès. « Annuler » ramène à cette liste
sans rien créer. La liste d'origine est « Trouver un outil », la page du propriétaire ou l'accueil ;
aucune autre adresse n'est acceptée.

#### Scenario: Demande envoyée
- **WHEN** Alice confirme une demande de la perceuse de Bob du 3 au 5, depuis « Trouver un outil » filtré par « perc » et trié par « Ajout : plus récents »
- **THEN** une demande en attente du 3 au 5 est enregistrée pour Alice
- **AND** Alice revient sur « Trouver un outil » filtré par « perc » et trié par « Ajout : plus récents », qui affiche « Demande envoyée à Bob Gagnon » en message de succès

#### Scenario: Depuis la page du contact
- **WHEN** Alice confirme une demande depuis la page de Bob
- **THEN** elle revient sur la page de Bob

#### Scenario: Depuis l'accueil
- **WHEN** Alice confirme une demande depuis « Nouveaux outils » de l'accueil
- **THEN** elle revient sur l'accueil

#### Scenario: Annuler
- **WHEN** Alice clique « Annuler » sur la page de confirmation
- **THEN** elle revient à la liste d'origine et aucune demande n'est créée

#### Scenario: Origine inconnue
- **WHEN** l'origine envoyée avec la demande est « https://exemple.com »
- **THEN** Alice revient sur « Trouver un outil »

#### Scenario: Jeton manquant
- **WHEN** la confirmation est envoyée sans jeton CSRF
- **THEN** le système répond 400 et aucune demande n'est créée

### Requirement: Ordre et couleurs de « Mes prêts »
Chaque liste de « Mes prêts » SHALL montrer d'abord les prêts en retard, de la date de fin la plus
ancienne à la plus récente, puis les lignes sur lesquelles l'utilisateur peut agir, puis les autres,
ces deux groupes de la plus récente à la plus ancienne selon la date d'envoi. Une ligne « En retard »
SHALL être mise en évidence en rouge. « Accepter » SHALL être affiché en vert, et « Refuser »,
« Annuler le prêt » et « Pas reçu » en rouge.

#### Scenario: Ordre des demandes
- **WHEN** Bob a reçu, dans cet ordre, des demandes de la scie, de la perceuse, de la ponceuse et du rabot
- **AND** il a refusé celle de la scie et celle de la ponceuse est « Complété »
- **THEN** sa liste « Mes prêts » est dans l'ordre : rabot, perceuse, ponceuse, scie

#### Scenario: Retards d'abord
- **WHEN** Bob a une demande en attente pour son rabot, et sa scie et sa perceuse sont en retard, la scie depuis plus longtemps
- **THEN** sa liste « Mes prêts » est dans l'ordre : scie, perceuse, rabot

#### Scenario: Retard en rouge
- **WHEN** la scie de Bob est en retard
- **THEN** sa ligne porte « En retard » et le style de retard

#### Scenario: Couleur des réponses
- **WHEN** Bob a une demande reçue en attente
- **THEN** « Accepter » est affiché en vert et « Refuser » en rouge

### Requirement: Réponse du propriétaire
Le propriétaire SHALL pouvoir accepter ou refuser une demande en attente de son outil ; seul lui
le peut, sinon le système répond 404. La réponse ramène à la page d'où elle a été envoyée,
« Mes prêts » ou l'accueil. Une demande qui n'est plus en attente, ou expirée, y ramène avec
« Cette demande n'est plus en attente », sans rien changer. Une acceptation dont les dates
chevauchent un prêt accepté ou en cours est refusée avec « Ces dates ne sont plus libres ». Une
origine inconnue ramène à « Mes prêts ».

#### Scenario: Acceptation
- **WHEN** Bob accepte la demande d'Alice pour sa perceuse
- **THEN** la demande est acceptée et la carte de la perceuse affiche « En attente de prêt »

#### Scenario: Refus
- **WHEN** Bob refuse la demande d'Alice
- **THEN** la demande est refusée et la perceuse redevient « Disponible »

#### Scenario: Autre que le propriétaire
- **WHEN** Alice ou Carole envoie l'acceptation de la demande d'Alice pour la perceuse de Bob
- **THEN** le système répond 404 et la demande reste en attente

#### Scenario: Réponse en double
- **WHEN** Bob a refusé la demande d'Alice et envoie de nouveau l'acceptation depuis « Mes prêts »
- **THEN** il revient sur « Mes prêts » avec « Cette demande n'est plus en attente »

#### Scenario: Demande expirée depuis l'accueil
- **WHEN** la demande d'Alice a expiré à minuit et Bob clique « Accepter » sur l'accueil resté ouvert
- **THEN** il revient sur l'accueil avec « Cette demande n'est plus en attente »

#### Scenario: Origine inconnue
- **WHEN** Bob accepte la demande d'Alice avec l'origine « https://exemple.com »
- **THEN** il revient sur « Mes prêts »

### Requirement: Retrait d'une demande par l'emprunteur
L'emprunteur SHALL pouvoir retirer sa demande tant qu'elle est en attente : elle devient annulée et
l'outil redevient disponible. Seul lui le peut, sinon le système répond 404. Le retrait ramène à la
page d'où il a été envoyé, « Mes prêts » ou l'accueil ; une demande qui n'est plus en attente y
ramène avec « Cette demande n'est plus en attente ».

#### Scenario: Retrait
- **WHEN** Alice retire sa demande pour la perceuse de Bob
- **THEN** la demande est annulée et la perceuse redevient « Disponible »

#### Scenario: Autre que l'emprunteur
- **WHEN** Bob envoie le retrait de la demande d'Alice
- **THEN** le système répond 404 et la demande reste en attente

#### Scenario: Retrait en double
- **WHEN** Alice a retiré sa demande et envoie de nouveau le retrait depuis « Mes prêts »
- **THEN** elle revient sur « Mes prêts » avec « Cette demande n'est plus en attente »

#### Scenario: Retrait depuis l'accueil
- **WHEN** Alice retire sa demande depuis l'accueil
- **THEN** elle revient sur l'accueil

### Requirement: Messages de succès
Un message qui confirme une action SHALL être affiché distinctement d'un message d'erreur. Chaque
action réussie sur une demande ou un prêt (envoi, réponse, retrait, remise, réception, retour,
« Pas reçu », annulation) SHALL afficher un message de succès sur la page où elle ramène.

#### Scenario: Succès et erreur
- **WHEN** Alice envoie une demande avec succès
- **THEN** « Demande envoyée à Bob Gagnon » est affiché comme un message de succès, pas comme une erreur

#### Scenario: Demande acceptée
- **WHEN** Bob accepte la demande d'Alice depuis « Mes prêts »
- **THEN** il revient sur « Mes prêts », qui affiche « Demande de Alice Tremblay acceptée » comme un message de succès

#### Scenario: Remise déclarée
- **WHEN** Bob clique « J'ai remis l'outil » pour le prêt de sa perceuse à Alice
- **THEN** « Remise déclarée, Alice Tremblay doit la confirmer » est affiché comme un message de succès

#### Scenario: Retour confirmé
- **WHEN** Bob confirme la réception du retour de sa perceuse depuis l'accueil
- **THEN** il revient sur l'accueil, la ligne n'y est plus et « Outil reçu, prêt complété » est affiché comme un message de succès
