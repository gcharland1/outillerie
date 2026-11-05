# Spec Delta

## MODIFIED Requirements

### Requirement: Carte d'un outil
Chaque outil SHALL être présenté par une carte qui affiche son nom, sa photo, le prénom et le nom
de son propriétaire, menant à sa page, sa description, son état et son statut de prêt, ainsi qu'un
bouton « Emprunter » : actif s'il est « Disponible », grisé sinon, ou « Demande envoyée » grisé sur
l'outil que l'utilisateur a lui-même demandé. Les cartes sont disposées sur trois colonnes à partir
d'un écran moyen, sur une seule sur un petit écran. Les notes privées du propriétaire MUST NOT être
affichées.

#### Scenario: Contenu de la carte
- **WHEN** Bob, contact d'Alice, a une perceuse fonctionnelle avec photo et description
- **THEN** la carte de la perceuse affiche son nom, sa photo, « Bob Gagnon », sa description, « Fonctionnel » et son statut
- **AND** « Bob Gagnon » mène à la page de Bob
- **AND** elle affiche un bouton « Emprunter » actif, qui mène à la page de confirmation de la demande

#### Scenario: Outil indisponible
- **WHEN** la perceuse de Bob est prêtée ou en attente de prêt pour Carole
- **THEN** la carte de la perceuse affiche, pour Alice, un bouton « Emprunter » grisé

#### Scenario: Sa propre demande
- **WHEN** Alice a demandé la perceuse de Bob et la demande attend sa réponse
- **THEN** la carte de la perceuse affiche, pour Alice, « Demande envoyée » grisé
- **AND** elle affiche, pour Carole, « En attente de prêt » et « Emprunter » grisé

#### Scenario: Notes privées cachées
- **WHEN** la perceuse de Bob a les notes privées « code du cadenas 1234 »
- **THEN** aucune page d'Alice n'affiche « code du cadenas 1234 »

#### Scenario: Outil sans photo
- **WHEN** la perceuse de Bob n'a pas de photo
- **THEN** sa carte affiche un espace réservé à la place de la photo, à la même taille

### Requirement: Statut de prêt
Le statut d'un outil SHALL être écrit en clair sur sa carte : « Prêté jusqu'au <date> » s'il est
prêté, même après la date prévue ; sinon « En attente de prêt » si une demande attend une réponse
et n'est pas expirée, ou si un prêt accepté n'est pas terminé, même pour des dates à venir ; sinon
« Disponible ». La date est écrite en français, par exemple « 3 novembre 2026 ».

#### Scenario: Outil prêté
- **WHEN** la perceuse de Bob est prêtée jusqu'au 3 novembre 2026
- **THEN** sa carte affiche « Prêté jusqu'au 3 novembre 2026 »

#### Scenario: Prêt en retard
- **WHEN** la perceuse de Bob est encore prêtée et la date de fin prévue est passée
- **THEN** sa carte affiche « Prêté jusqu'au » suivi de cette date

#### Scenario: Demande en attente
- **WHEN** une demande d'emprunt de la perceuse de Bob attend sa réponse
- **THEN** sa carte affiche « En attente de prêt »

#### Scenario: Demande expirée
- **WHEN** une demande d'emprunt de la perceuse de Bob, commencée hier, n'a pas reçu de réponse
- **THEN** sa carte affiche « Disponible »

#### Scenario: Prêt accepté à venir
- **WHEN** Bob a accepté de prêter sa perceuse du 10 au 12 du mois prochain
- **THEN** sa carte affiche « En attente de prêt »

#### Scenario: Prêts terminés
- **WHEN** tous les prêts de la perceuse de Bob sont rendus, refusés ou annulés
- **THEN** sa carte affiche « Disponible »
