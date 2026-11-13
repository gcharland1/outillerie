# Spec Delta

## Purpose

Suivre un prêt accepté jusqu'à sa fin : remise et retour de l'outil, chacun déclaré par celui qui le
donne et confirmé par celui qui le reçoit, annulation avant la remise, retard et expiration.

## ADDED Requirements

### Requirement: Remise déclarée par le propriétaire
Le propriétaire SHALL pouvoir déclarer « J'ai remis l'outil » sur un prêt accepté, dès
l'acceptation et jusqu'au dernier jour du prêt : le prêt passe à « Remise à confirmer ». Les dates
du prêt ne changent pas.

#### Scenario: Remise déclarée avant le premier jour
- **WHEN** Bob a accepté de prêter sa perceuse à Alice du 10 au 12 et déclare « J'ai remis l'outil » le 9
- **THEN** le prêt est « Remise à confirmer », toujours du 10 au 12

#### Scenario: Prêt accepté expiré
- **WHEN** le dernier jour d'un prêt accepté de la perceuse de Bob est passé
- **THEN** « Mes prêts » de Bob n'offre pas « J'ai remis l'outil » pour ce prêt

### Requirement: Réception de l'outil par l'emprunteur
L'emprunteur SHALL pouvoir confirmer une remise déclarée (« Confirmer la réception ») ou déclarer
lui-même « J'ai reçu l'outil » sur un prêt accepté non expiré : le prêt passe à « Prêté » et la date
de remise est enregistrée.

#### Scenario: Remise confirmée
- **WHEN** Bob a déclaré avoir remis sa perceuse à Alice et Alice clique « Confirmer la réception »
- **THEN** le prêt est « Prêté » et « Mes emprunts » d'Alice affiche la date de remise du jour

#### Scenario: Réception sans déclaration
- **WHEN** Bob a accepté de prêter sa perceuse à Alice, sans rien déclarer, et Alice clique « J'ai reçu l'outil »
- **THEN** le prêt est « Prêté »

#### Scenario: Le propriétaire ne marque pas lui-même « Prêté »
- **WHEN** Bob envoie la confirmation de réception du prêt de sa perceuse à Alice
- **THEN** le système répond 404 et le prêt ne change pas

### Requirement: Retour déclaré par l'emprunteur
L'emprunteur SHALL pouvoir déclarer « J'ai rendu l'outil » sur un prêt « Prêté », avant ou après sa
date de fin : le prêt passe à « Retour à confirmer ».

#### Scenario: Retour déclaré
- **WHEN** Alice a la perceuse de Bob et clique « J'ai rendu l'outil »
- **THEN** le prêt est « Retour à confirmer »

#### Scenario: Retour anticipé
- **WHEN** Alice a emprunté la perceuse de Bob jusqu'au 12 et déclare l'avoir rendue le 10
- **THEN** le prêt est « Retour à confirmer »

### Requirement: Réception du retour par le propriétaire
Le propriétaire SHALL pouvoir confirmer un retour déclaré (« Confirmer la réception ») ou déclarer
lui-même « J'ai reçu l'outil » sur un prêt « Prêté » : le prêt passe à « Complété », la date de retour
est enregistrée et l'outil redevient disponible.

#### Scenario: Retour confirmé
- **WHEN** Alice a déclaré avoir rendu la perceuse et Bob clique « Confirmer la réception »
- **THEN** le prêt est « Complété » et la perceuse redevient « Disponible »

#### Scenario: Retour sans déclaration
- **WHEN** Alice a la perceuse de Bob, sans rien déclarer, et Bob clique « J'ai reçu l'outil »
- **THEN** le prêt est « Complété »

#### Scenario: L'emprunteur ne complète pas lui-même
- **WHEN** Alice envoie la confirmation de réception du retour de la perceuse de Bob
- **THEN** le système répond 404 et le prêt ne change pas

### Requirement: Déclaration contestée
Celui qui doit recevoir l'outil SHALL pouvoir répondre « Pas reçu » à une déclaration : une remise à
confirmer redevient « Attente de récupération », un retour à confirmer redevient « Prêté ». L'autre
partie peut déclarer de nouveau. Une remise contestée MUST devenir « Annulée » si l'outil est retiré
ou « Hors d'usage », ou si les deux ne sont plus en contact.

#### Scenario: Remise contestée
- **WHEN** Bob a déclaré avoir remis sa perceuse et Alice clique « Pas reçu »
- **THEN** le prêt est « Attente de récupération » et Bob peut de nouveau déclarer « J'ai remis l'outil »

#### Scenario: Retour contesté
- **WHEN** Alice a déclaré avoir rendu la perceuse et Bob clique « Pas reçu »
- **THEN** le prêt est « Prêté »

#### Scenario: Remise contestée d'un outil retiré
- **WHEN** Bob a déclaré avoir remis sa perceuse à Alice, puis l'a retirée de la circulation, la passe « Hors d'usage » ou retire Alice de ses contacts
- **AND** Alice clique « Pas reçu »
- **THEN** le prêt est « Annulée »

### Requirement: Annulation d'un prêt accepté
Le propriétaire et l'emprunteur SHALL pouvoir annuler un prêt « Attente de récupération », par une
page de confirmation qui nomme l'outil et l'autre personne, avec
« Annuler le prêt » et un retour à « Mes prêts ». Le prêt devient « Annulée » et l'outil redevient
disponible. Un prêt « Remise à confirmer », « Prêté » ou « Retour à confirmer » MUST NOT être annulé.

#### Scenario: Annulation par l'emprunteur
- **WHEN** Alice ouvre l'annulation du prêt accepté de la perceuse de Bob et confirme
- **THEN** le prêt est « Annulée » et la perceuse redevient « Disponible »

#### Scenario: Page de confirmation sans effet
- **WHEN** Bob ouvre la page d'annulation du prêt de sa perceuse à Alice
- **THEN** la page nomme « Perceuse » et « Alice Tremblay » et le prêt est toujours accepté

#### Scenario: Remise à confirmer non annulable
- **WHEN** Bob a déclaré avoir remis sa perceuse à Alice
- **THEN** ni « Mes prêts » de Bob ni « Mes emprunts » d'Alice n'offrent « Annuler le prêt »

#### Scenario: Prêt en cours non annulable
- **WHEN** Bob envoie l'annulation du prêt de sa perceuse, que Alice a reçue
- **THEN** il revient sur « Mes prêts » avec « Ce prêt a déjà changé de statut » et le prêt reste « Prêté »

### Requirement: Prêt en retard
Un prêt « Prêté » ou « Remise à confirmer » SHALL être « En retard » à partir du lendemain de sa date
de fin, dans le fuseau du site, jusqu'à ce que l'outil soit déclaré rendu. Le retard se déduit des
dates : aucune action ni écriture ne le déclenche.

#### Scenario: Dernier jour
- **WHEN** Alice a la perceuse de Bob jusqu'à aujourd'hui
- **THEN** le prêt est « Prêté »

#### Scenario: Lendemain du dernier jour
- **WHEN** Alice a la perceuse de Bob jusqu'à hier
- **THEN** « Mes prêts » de Bob et « Mes emprunts » d'Alice affichent le prêt « En retard »

#### Scenario: Retour déclaré après la fin
- **WHEN** Alice a la perceuse de Bob jusqu'à hier et déclare l'avoir rendue
- **THEN** le prêt est « Retour à confirmer », pas « En retard »

#### Scenario: Retour contesté après la fin
- **WHEN** Bob répond « Pas reçu » au retour déclaré d'un prêt fini hier
- **THEN** le prêt est « En retard »

### Requirement: Prêt accepté expiré
Un prêt « Attente de récupération » dont la date de fin est passée SHALL être « Expirée » : il
n'offre plus aucune action et ne bloque plus l'outil.

#### Scenario: Outil jamais récupéré
- **WHEN** Bob a accepté de prêter sa perceuse à Alice jusqu'à hier et personne n'a déclaré de remise
- **THEN** « Mes prêts » de Bob affiche ce prêt « Expirée », sans action
- **AND** la perceuse est « Disponible »

### Requirement: Actions réservées aux parties
Chaque action sur un prêt SHALL être réservée à la partie qui peut la faire selon le statut ; pour
toute autre personne, et pour un prêt inexistant, le système répond 404. Une action sur un prêt dont
le statut ne la permet plus ramène à « Mes prêts » avec « Ce prêt a déjà changé de statut », sans
rien changer. Ces actions ne dépendent ni de la visibilité de l'outil ni du lien de contact.

#### Scenario: Tiers
- **WHEN** Carole envoie « J'ai remis l'outil » pour le prêt de la perceuse de Bob à Alice
- **THEN** le système répond 404 et le prêt ne change pas

#### Scenario: Envoi en double
- **WHEN** Alice a déclaré avoir rendu la perceuse et envoie de nouveau « J'ai rendu l'outil »
- **THEN** elle revient sur « Mes prêts » avec « Ce prêt a déjà changé de statut »

#### Scenario: Deux actions en même temps
- **WHEN** Alice déclare avoir rendu la perceuse pendant que Bob clique « J'ai reçu l'outil »
- **THEN** une seule des deux actions s'applique et l'autre ramène à « Mes prêts » avec « Ce prêt a déjà changé de statut »

#### Scenario: Outil retiré pendant le prêt
- **WHEN** Alice a la perceuse de Bob et Bob retire la perceuse de la circulation
- **THEN** Alice peut encore déclarer « J'ai rendu l'outil » et Bob confirmer la réception

#### Scenario: Jeton manquant
- **WHEN** une action sur un prêt est envoyée sans jeton CSRF
- **THEN** le système répond 400 et le prêt ne change pas

#### Scenario: Visiteur
- **WHEN** un visiteur envoie une action sur un prêt
- **THEN** il est redirigé vers `/login` et le prêt ne change pas
