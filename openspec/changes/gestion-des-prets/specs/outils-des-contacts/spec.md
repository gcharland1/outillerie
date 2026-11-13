# Spec Delta

## MODIFIED Requirements

### Requirement: Statut de prêt
Le statut d'un outil SHALL être écrit en clair sur sa carte : « Prêté jusqu'au <date> » s'il est
prêté, ou si une remise ou un retour attend sa confirmation, même après la date prévue ; sinon
« En attente de prêt » si une demande attend une réponse et n'est pas expirée, ou si un prêt
accepté n'est pas terminé, même pour des dates à venir ; sinon « Disponible ». La carte ne dit
jamais qu'un prêt est en retard. La date est écrite en français, par exemple « 3 novembre 2026 ».

#### Scenario: Outil prêté
- **WHEN** la perceuse de Bob est prêtée jusqu'au 3 novembre 2026
- **THEN** sa carte affiche « Prêté jusqu'au 3 novembre 2026 »

#### Scenario: Prêt en retard
- **WHEN** la perceuse de Bob est encore prêtée et la date de fin prévue est passée
- **THEN** sa carte affiche « Prêté jusqu'au » suivi de cette date, sans « En retard »

#### Scenario: Remise ou retour à confirmer
- **WHEN** Bob a déclaré avoir remis sa perceuse, prêtée jusqu'au 3 novembre 2026, ou l'emprunteur a déclaré l'avoir rendue
- **THEN** sa carte affiche « Prêté jusqu'au 3 novembre 2026 »

#### Scenario: Demande en attente
- **WHEN** une demande d'emprunt de la perceuse de Bob attend sa réponse
- **THEN** sa carte affiche « En attente de prêt »

#### Scenario: Demande expirée
- **WHEN** une demande d'emprunt de la perceuse de Bob, commencée hier, n'a pas reçu de réponse
- **THEN** sa carte affiche « Disponible »

#### Scenario: Prêt accepté à venir
- **WHEN** Bob a accepté de prêter sa perceuse du 10 au 12 du mois prochain
- **THEN** sa carte affiche « En attente de prêt »

#### Scenario: Prêt accepté expiré
- **WHEN** Bob a accepté de prêter sa perceuse jusqu'à hier et personne n'a déclaré de remise
- **THEN** sa carte affiche « Disponible »

#### Scenario: Prêts terminés
- **WHEN** tous les prêts de la perceuse de Bob sont complétés, refusés ou annulés
- **THEN** sa carte affiche « Disponible »
