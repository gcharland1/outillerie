# Spec Delta

## MODIFIED Requirements

### Requirement: Modification d'un outil
Le système SHALL permettre au propriétaire de modifier le nom, la description, l'état et les
notes privées d'un outil en circulation, depuis un formulaire prérempli avec les valeurs
actuelles, puis le ramener à « Mes outils ». Vider les notes privées les supprime. Passer l'outil
à l'état « Hors d'usage » annule ses demandes d'emprunt en attente et ses prêts acceptés non
expirés, sans remise déclarée ; une remise à confirmer et un prêt en cours restent intacts.

#### Scenario: Formulaire prérempli
- **WHEN** Alice ouvre « Modifier » pour sa perceuse
- **THEN** le formulaire affiche le nom, la description, l'état et les notes privées actuels

#### Scenario: Outil modifié
- **WHEN** Alice remplace l'état de sa perceuse par « Hors d'usage » et enregistre
- **THEN** la perceuse est à l'état `out_of_order`
- **AND** Alice est redirigée vers « Mes outils »

#### Scenario: Demandes annulées par le passage hors d'usage
- **WHEN** Bob a demandé la perceuse d'Alice, sans réponse
- **AND** Alice passe sa perceuse à l'état « Hors d'usage »
- **THEN** la demande de Bob est annulée

#### Scenario: Prêt accepté annulé par le passage hors d'usage
- **WHEN** Alice a accepté de prêter sa perceuse à Bob, sans remise déclarée
- **AND** Alice passe sa perceuse à l'état « Hors d'usage »
- **THEN** le prêt est « Annulée »

#### Scenario: Prêt en cours gardé
- **WHEN** Bob a la perceuse d'Alice, ou Alice a déclaré la lui avoir remise
- **AND** Alice passe sa perceuse à l'état « Hors d'usage »
- **THEN** le prêt garde son statut et reste clôturable depuis « Mes prêts »

#### Scenario: Outil retiré non modifiable
- **WHEN** Alice demande la modification d'un de ses outils retirés
- **THEN** le système répond 404

### Requirement: Retrait avec confirmation
« Retirer » SHALL mener à une page de confirmation qui nomme l'outil, indique qu'il restera
enregistré et pourra être remis en circulation, annonce le nombre de demandes d'emprunt en attente
et de prêts acceptés non expirés, sans remise déclarée, qui seront annulés s'il y en a, et offre « Confirmer le
retrait » et un lien d'annulation vers « Mes outils ». Seule la confirmation, par un envoi de
formulaire, retire l'outil et annule ces demandes et prêts ; il reste enregistré.

#### Scenario: Page de confirmation
- **WHEN** Alice clique « Retirer » pour sa perceuse
- **THEN** une page lui demande de confirmer le retrait de « Perceuse »
- **AND** elle affiche « L'outil restera enregistré ; vous pourrez le remettre en circulation depuis « Mes outils retirés ». »
- **AND** la perceuse est toujours en circulation

#### Scenario: Retrait confirmé
- **WHEN** Alice clique « Confirmer le retrait » pour sa perceuse
- **THEN** la perceuse n'est plus en circulation et reste enregistrée avec ses informations
- **AND** Alice est redirigée vers « Mes outils », qui ne liste plus la perceuse

#### Scenario: Demandes annulées par le retrait
- **WHEN** Bob a demandé la perceuse d'Alice, sans réponse
- **AND** Alice ouvre la confirmation du retrait de la perceuse
- **THEN** la page annonce « 1 demande d'emprunt en attente sera annulée »
- **AND** une fois le retrait confirmé, la demande de Bob est annulée

#### Scenario: Prêt accepté annulé par le retrait
- **WHEN** Alice a accepté de prêter sa perceuse à Bob, sans remise déclarée
- **AND** Alice ouvre la confirmation du retrait de la perceuse
- **THEN** la page annonce « 1 prêt accepté sera annulé »
- **AND** une fois le retrait confirmé, le prêt est « Annulée »

#### Scenario: Prêt en cours gardé au retrait
- **WHEN** Bob a la perceuse d'Alice et Alice confirme son retrait
- **THEN** le prêt reste « Prêté » dans « Mes prêts » d'Alice et « Mes emprunts » de Bob

#### Scenario: Pas de retrait par un lien
- **WHEN** le retrait d'un outil est demandé sans envoi de formulaire (`GET`)
- **THEN** l'outil reste en circulation
