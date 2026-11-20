## MODIFIED Requirements

### Requirement: Ordre et couleurs de « Mes prêts »
Chaque liste de « Mes prêts » SHALL montrer d'abord les prêts en retard, de la date de fin la plus
ancienne à la plus récente, puis les lignes sur lesquelles l'utilisateur peut agir, puis les autres,
ces deux groupes de la plus récente à la plus ancienne selon la date d'envoi. Une ligne « En retard »
SHALL être mise en évidence en rouge. Les boutons suivent l'ADR 0019 : « Accepter », « J'ai remis
l'outil », « J'ai reçu l'outil », « J'ai rendu l'outil » et « Confirmer la réception » SHALL être
affichés en bleu ; « Refuser », « Retirer ma demande », « Annuler le prêt » et « Pas reçu » en
neutre. Aucun bouton n'est rouge.

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
- **THEN** « Accepter » est affiché en bleu et « Refuser » en neutre, comme sur une demande de contact

#### Scenario: Annulation en neutre
- **WHEN** Bob a accepté la demande d'Alice
- **THEN** « Annuler le prêt » est affiché en neutre et « J'ai remis l'outil » en bleu
