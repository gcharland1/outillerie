## REMOVED Requirements

### Requirement: Ordre et couleurs de « Mes prêts »
**Reason**: Ses couleurs de boutons suivaient l'ADR 0019, remplacé par l'ADR 0022, et son scénario
« Annulation en neutre » devient faux. Le requirement est scindé en deux, l'ordre d'un côté et les
couleurs de l'autre.
**Migration**: L'ordre et le retard en rouge passent, inchangés, dans « Ordre de « Mes prêts » » ; les
couleurs des boutons, selon l'ADR 0022, dans « Couleurs des boutons de « Mes prêts » ».

## ADDED Requirements

### Requirement: Ordre de « Mes prêts »
Chaque liste de « Mes prêts » SHALL montrer d'abord les prêts en retard, de la date de fin la plus
ancienne à la plus récente, puis les lignes sur lesquelles l'utilisateur peut agir, puis les autres,
ces deux groupes de la plus récente à la plus ancienne selon la date d'envoi. Une ligne « En retard »
SHALL être mise en évidence en rouge.

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

### Requirement: Couleurs des boutons de « Mes prêts »
Les boutons de « Mes prêts » et de l'accueil SHALL suivre l'ADR 0022 : « Accepter », « J'ai remis
l'outil », « J'ai reçu l'outil », « J'ai rendu l'outil » et « Confirmer la réception » en bleu ;
« Retirer ma demande » et « Annuler le prêt » en rouge ; « Refuser » et « Pas reçu » en gris.

#### Scenario: Couleur des réponses
- **WHEN** Bob a une demande reçue en attente
- **THEN** « Accepter » est affiché en bleu et « Refuser » en gris, comme sur une demande de contact

#### Scenario: Annulation en rouge
- **WHEN** Bob a accepté la demande d'Alice
- **THEN** « Annuler le prêt » est affiché en rouge et « J'ai remis l'outil » en bleu

#### Scenario: Retrait d'une demande en rouge
- **WHEN** Alice a une demande d'emprunt en attente
- **THEN** « Retirer ma demande » est affiché en rouge dans ses emprunts

#### Scenario: Pas reçu en gris
- **WHEN** Bob a déclaré avoir remis la perceuse à Alice
- **THEN** « Pas reçu » est affiché en gris et « Confirmer la réception » en bleu dans les emprunts d'Alice

## MODIFIED Requirements

### Requirement: Retrait d'une demande par l'emprunteur
L'emprunteur SHALL pouvoir retirer sa demande tant qu'elle est en attente, en passant par une page de
confirmation qui offre un champ « Raison » facultatif : la demande devient annulée, l'outil redevient
disponible et une raison saisie s'ajoute au message de la demande. Seul lui le peut, sinon le système
répond 404. Le retrait ramène à la page d'où il est parti, « Mes prêts » ou l'accueil ; une demande
qui n'est plus en attente y ramène avec « Cette demande n'est plus en attente ».

#### Scenario: Page de confirmation
- **WHEN** Alice clique « Retirer ma demande » pour la perceuse de Bob
- **THEN** une page affiche l'outil, Bob et les dates, un champ « Raison » facultatif, « Retour » en gris et « Retirer ma demande » en rouge
- **AND** la demande reste en attente

#### Scenario: Retrait
- **WHEN** Alice confirme le retrait sans raison
- **THEN** la demande est annulée, la perceuse redevient « Disponible » et le message de la demande est inchangé

#### Scenario: Retrait avec une raison
- **WHEN** la demande d'Alice porte le message « Pour samedi » et Alice confirme le retrait avec la raison « J'en ai trouvé une »
- **THEN** le message de la demande devient « Pour samedi — Raison du retrait : J'en ai trouvé une »

#### Scenario: Retrait avec une raison, sans message
- **WHEN** la demande d'Alice n'a pas de message et Alice confirme le retrait avec la raison « J'en ai trouvé une »
- **THEN** le message de la demande devient « Raison du retrait : J'en ai trouvé une »

#### Scenario: Raison trop longue
- **WHEN** le message et la raison réunis dépasseraient la longueur permise d'un message
- **THEN** la page de confirmation est réaffichée avec la raison saisie et « La raison ne doit pas dépasser N caractères », N étant la place qui reste, et la demande reste en attente

#### Scenario: Retour
- **WHEN** Alice clique « Retour » sur la page de confirmation
- **THEN** elle revient à la page d'où elle est partie et la demande reste en attente

#### Scenario: Autre que l'emprunteur
- **WHEN** Bob ouvre la confirmation ou envoie le retrait de la demande d'Alice
- **THEN** le système répond 404 et la demande reste en attente

#### Scenario: Retrait en double
- **WHEN** Alice a retiré sa demande et envoie de nouveau le retrait depuis « Mes prêts »
- **THEN** elle revient sur « Mes prêts » avec « Cette demande n'est plus en attente »

#### Scenario: Retrait depuis l'accueil
- **WHEN** Alice retire sa demande depuis l'accueil
- **THEN** elle revient sur l'accueil
