# Spec Delta

## Purpose

Permettre à un utilisateur de demander l'outil d'un contact pour des dates précises, et au
propriétaire d'en être prévenu et d'accepter ou de refuser, sans qu'un outil soit promis deux fois.

## ADDED Requirements

### Requirement: Page de confirmation d'une demande
« Emprunter » SHALL mener à une page qui affiche le nom, la photo, la description entière, l'état
et le prénom et le nom du propriétaire de l'outil, les champs « Du » et « Au », le champ
« Message pour <prénom> <nom> (facultatif) », et les boutons « Confirmer » et « Annuler ». « Du »
est prérempli avec la date du jour. Les notes privées MUST NOT y figurer. Ouvrir la page ne crée
aucune demande.

#### Scenario: Contenu de la page
- **WHEN** Bob Gagnon, contact d'Alice, a une perceuse disponible et Alice clique « Emprunter »
- **THEN** la page affiche « Perceuse », sa photo, sa description entière, son état et « Bob Gagnon »
- **AND** elle affiche les champs « Du », prérempli à aujourd'hui, « Au » et « Message pour Bob Gagnon (facultatif) »
- **AND** aucune demande n'est créée

#### Scenario: Notes privées cachées
- **WHEN** la perceuse de Bob a les notes privées « code du cadenas 1234 »
- **THEN** la page de confirmation n'affiche pas « code du cadenas 1234 »

### Requirement: Outil qu'on peut demander
La page de confirmation et son envoi MUST répondre 404, de la même façon, pour un outil inexistant,
retiré, « Hors d'usage », appartenant à l'utilisateur ou à un compte qui n'est pas son contact. Un
visiteur est redirigé vers `/login`.

#### Scenario: Outils refusés
- **WHEN** Alice demande la page de confirmation de son propre outil, d'un outil de Carole qui n'est pas son contact, d'un outil retiré ou hors d'usage de Bob, ou d'un outil inexistant
- **THEN** le système répond 404 dans chaque cas

#### Scenario: Visiteur
- **WHEN** un visiteur demande la page de confirmation d'un outil
- **THEN** il est redirigé vers `/login`

### Requirement: Dates d'une demande
Le système MUST refuser une demande dont « Du » ou « Au » est vide ou n'est pas une date, dont
« Du » précède aujourd'hui ou le dépasse de plus de 14 jours, dont « Au » précède « Du », ou qui
dure plus de 30 jours, bornes comprises. Le refus réaffiche la page avec un message et les champs
saisis, et ne crée aucune demande. Aujourd'hui est la date dans le fuseau du site.

#### Scenario: Date passée
- **WHEN** Alice envoie une demande dont « Du » est hier
- **THEN** la page affiche « La date de début ne peut pas être passée » et aucune demande n'est créée

#### Scenario: Trop loin
- **WHEN** Alice envoie une demande dont « Du » est dans 15 jours
- **THEN** la page affiche « La date de début doit être dans les 14 prochains jours »

#### Scenario: Fin avant le début
- **WHEN** Alice envoie une demande du 10 au 8
- **THEN** la page affiche « La date de fin ne peut pas précéder la date de début »

#### Scenario: Trop long
- **WHEN** Alice envoie une demande de 31 jours
- **THEN** la page affiche « Un prêt dure au plus 30 jours »

#### Scenario: Date invalide
- **WHEN** Alice envoie une demande dont « Au » est vide ou vaut « demain »
- **THEN** la page affiche « Indiquez des dates valides »
- **AND** le message saisi est conservé

### Requirement: Message au propriétaire
Le message est facultatif, au plus 500 caractères sans les espaces qui l'entourent ; un message
fait d'espaces vaut l'absence de message. Il SHALL n'être montré qu'au propriétaire et à
l'emprunteur, en texte brut avec ses retours à la ligne.

#### Scenario: Message trop long
- **WHEN** Alice envoie une demande avec un message de 501 caractères
- **THEN** la page affiche « Le message ne doit pas dépasser 500 caractères » et aucune demande n'est créée

#### Scenario: Balisage affiché tel quel
- **WHEN** Alice envoie le message « <b>merci</b> »
- **THEN** la page « Mes prêts » de Bob affiche « <b>merci</b> » comme du texte

#### Scenario: Message privé
- **WHEN** Alice a envoyé le message « je passe samedi » à Bob et Carole, contact de Bob, ouvre « Trouver un outil »
- **THEN** aucune page de Carole n'affiche « je passe samedi »

### Requirement: Envoi d'une demande
« Confirmer » SHALL créer une demande en attente pour l'outil, l'utilisateur et les dates, puis
ramener l'utilisateur à la liste d'où il est venu, avec ses filtres, et afficher « Demande envoyée
à <prénom> <nom> » comme un message de succès. « Annuler » ramène à cette liste sans rien créer.
La liste d'origine est « Trouver un outil » ou la page du propriétaire ; aucune autre adresse
n'est acceptée.

#### Scenario: Demande envoyée
- **WHEN** Alice confirme une demande de la perceuse de Bob du 3 au 5, depuis « Trouver un outil » filtré par « perc »
- **THEN** une demande en attente du 3 au 5 est enregistrée pour Alice
- **AND** Alice revient sur « Trouver un outil » filtré par « perc », qui affiche « Demande envoyée à Bob Gagnon » en message de succès

#### Scenario: Depuis la page du contact
- **WHEN** Alice confirme une demande depuis la page de Bob
- **THEN** elle revient sur la page de Bob

#### Scenario: Annuler
- **WHEN** Alice clique « Annuler » sur la page de confirmation
- **THEN** elle revient à la liste d'origine et aucune demande n'est créée

#### Scenario: Origine inconnue
- **WHEN** l'origine envoyée avec la demande est « https://exemple.com »
- **THEN** Alice revient sur « Trouver un outil »

#### Scenario: Jeton manquant
- **WHEN** la confirmation est envoyée sans jeton CSRF
- **THEN** le système répond 400 et aucune demande n'est créée

### Requirement: Une demande à la fois par outil
Le système MUST refuser une demande pour un outil qui n'est plus « Disponible » au moment de
l'envoi, même quand deux envois arrivent en même temps : la page de confirmation et l'envoi
ramènent alors à la liste d'origine avec « Cet outil n'est plus disponible », sans rien créer.

#### Scenario: Deuxième onglet
- **WHEN** Alice a confirmé une demande de la perceuse de Bob dans un onglet
- **AND** elle confirme de nouveau depuis un autre onglet
- **THEN** elle revient à la liste d'origine avec « Cet outil n'est plus disponible »
- **AND** une seule demande existe

#### Scenario: Deux emprunteurs
- **WHEN** Alice et Carole confirment chacune une demande de la perceuse de Bob en même temps
- **THEN** une seule demande est créée

### Requirement: Page « Mes prêts »
Le menu du compte SHALL offrir « Mes prêts », une page qui liste les demandes reçues pour les
outils de l'utilisateur et ses propres demandes, avec l'outil, l'autre personne, les dates, le
message et le statut : « En attente », « Expirée », « Acceptée », « Refusée », « Annulée »,
« Prêté » ou « Rendu ». La page exige une session ouverte.

#### Scenario: Demandes reçues et envoyées
- **WHEN** Alice a demandé la perceuse de Bob et Bob a demandé la scie d'Alice
- **THEN** la page « Mes prêts » d'Alice montre sa demande de la perceuse et la demande de Bob pour sa scie

#### Scenario: Entrée du menu
- **WHEN** un utilisateur connecté ouvre une page du site
- **THEN** son menu du compte contient « Mes prêts »

### Requirement: Réponse du propriétaire
Le propriétaire SHALL pouvoir accepter ou refuser une demande en attente de son outil ; seul lui
le peut, sinon le système répond 404. Une demande qui n'est plus en attente, ou expirée, ramène à
« Mes prêts » avec « Cette demande n'est plus en attente », sans rien changer. Une acceptation
dont les dates chevauchent un prêt accepté ou en cours est refusée avec « Ces dates ne sont plus
libres ».

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
- **WHEN** Bob a refusé la demande d'Alice et envoie de nouveau l'acceptation
- **THEN** il revient sur « Mes prêts » avec « Cette demande n'est plus en attente »

### Requirement: Retrait d'une demande par l'emprunteur
L'emprunteur SHALL pouvoir retirer sa demande tant qu'elle est en attente : elle devient annulée et
l'outil redevient disponible. Seul lui le peut, sinon le système répond 404 ; une demande qui
n'est plus en attente ramène à « Mes prêts » avec « Cette demande n'est plus en attente ».

#### Scenario: Retrait
- **WHEN** Alice retire sa demande pour la perceuse de Bob
- **THEN** la demande est annulée et la perceuse redevient « Disponible »

#### Scenario: Autre que l'emprunteur
- **WHEN** Bob envoie le retrait de la demande d'Alice
- **THEN** le système répond 404 et la demande reste en attente

#### Scenario: Retrait en double
- **WHEN** Alice a retiré sa demande et envoie de nouveau le retrait
- **THEN** elle revient sur « Mes prêts » avec « Cette demande n'est plus en attente »

### Requirement: Expiration d'une demande
Une demande restée en attente après son premier jour SHALL être expirée : elle n'apparaît plus
dans la pastille, ne peut plus être acceptée ni retirée, et apparaît comme « Expirée » dans
« Mes prêts ».

#### Scenario: Demande expirée
- **WHEN** Alice a demandé la perceuse de Bob à partir d'hier et Bob n'a pas répondu
- **THEN** la page « Mes prêts » de Bob montre la demande « Expirée », sans « Accepter » ni « Refuser »

### Requirement: Pastille des demandes d'emprunt
Quand un utilisateur a des demandes d'emprunt reçues en attente, non expirées, chaque page SHALL
afficher leur nombre dans une pastille à côté de « Mes prêts » dans le menu du compte.

#### Scenario: Une demande reçue
- **WHEN** Alice a demandé la perceuse de Bob et Bob ouvre une page du site
- **THEN** une pastille « 1 » est affichée à côté de « Mes prêts »

#### Scenario: Demande expirée hors de la pastille
- **WHEN** la seule demande reçue par Bob est expirée
- **THEN** aucune pastille n'est affichée à côté de « Mes prêts »

### Requirement: Messages de succès
Un message qui confirme une action SHALL être affiché distinctement d'un message d'erreur.

#### Scenario: Succès et erreur
- **WHEN** Alice envoie une demande avec succès
- **THEN** « Demande envoyée à Bob Gagnon » est affiché comme un message de succès, pas comme une erreur
