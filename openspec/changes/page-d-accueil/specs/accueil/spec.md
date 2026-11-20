# Spec Delta

## REMOVED Requirements

### Requirement: Page d'accueil
**Reason**: `/` n'est plus une page publique de bienvenue : elle devient le tableau de bord de
l'utilisateur connecté, et un visiteur est redirigé vers `/login`.
**Migration**: remplacée par « Tableau de bord de l'utilisateur connecté » ; les vérifications de
visiteur visent `/login`.

## ADDED Requirements

### Requirement: Tableau de bord de l'utilisateur connecté
Le système SHALL servir à la racine `/` le tableau de bord de l'utilisateur connecté, rendu à partir
du gabarit `index.html`, avec trois sections dans cet ordre : « Gestion des prêts », « Gestion des
contacts », « Nouveaux outils ». Un visiteur MUST être redirigé vers `/login`, sans message ; la
page fonctionne sans JavaScript.

#### Scenario: Sans script
- **WHEN** Alice ouvre `/` dans un navigateur sans JavaScript
- **THEN** chaque action de la page est un formulaire ou un lien qui fonctionne sans script

#### Scenario: Utilisateur connecté
- **WHEN** Alice, connectée, demande `GET /`
- **THEN** le système répond 200 avec le gabarit `index.html`
- **AND** la page affiche « Gestion des prêts », « Gestion des contacts » et « Nouveaux outils », dans cet ordre

#### Scenario: Visiteur
- **WHEN** un visiteur demande `GET /`
- **THEN** il est redirigé vers `/login`
- **AND** la page de connexion n'affiche aucun message

### Requirement: Contenu de « Gestion des prêts »
La section « Gestion des prêts » SHALL lister les prêts de l'utilisateur sur lesquels un échange est
en cours, chaque ligne avec l'outil, l'autre personne, les dates, le statut et les mêmes actions
que « Mes prêts ». Les lignes « Complété », « Refusée », « Annulée » et « Expirée » MUST NOT y
figurer. Un prêt en cours avec un ancien contact y reste.

#### Scenario: Prêts terminés absents
- **WHEN** Alice a un prêt « Complété », une demande « Refusée », une demande « Annulée » et une demande « Expirée »
- **THEN** aucune de ces lignes n'apparaît dans la section

#### Scenario: Ancien contact
- **WHEN** Alice a la perceuse de Bob et Bob l'a retirée de ses contacts
- **THEN** la perceuse est toujours dans la section, avec « J'ai rendu l'outil »

#### Scenario: Prêts des autres
- **WHEN** Bob prête sa perceuse à Carole
- **THEN** la section d'Alice ne montre ni ce prêt ni son message

### Requirement: Ordre de « Gestion des prêts »
La section SHALL ranger ses lignes en trois groupes : « Demandes reçues » (demandes en attente non
expirées de ses outils), « Mes emprunts » (« En retard », « Remise à confirmer », « Retour à
confirmer », puis les autres) et « Mes prêts » (« En retard », « Attente de récupération »,
« Retour à confirmer », puis les autres).

#### Scenario: Ordre des groupes
- **WHEN** Alice a reçu une demande de Carole pour sa scie, emprunte la perceuse de Bob et son rabot est « Prêté » à Bob
- **THEN** la section liste la demande de la scie, puis la perceuse, puis le rabot

#### Scenario: Retard d'abord
- **WHEN** Alice a la perceuse de Bob jusqu'à hier et la ponceuse de Carole jusqu'à demain
- **THEN** la perceuse est listée avant la ponceuse, avec « En retard »

#### Scenario: Remise à confirmer en retard
- **WHEN** Bob a déclaré avoir remis sa perceuse à Alice et la date de fin du prêt était hier
- **THEN** la ligne de la perceuse est dans la catégorie « En retard » d'Alice, avec « Confirmer la réception » et « Pas reçu »

#### Scenario: Catégories du prêteur
- **WHEN** Alice prête sa scie à Bob (« Prêté »), a accepté de prêter son rabot à Carole et Carole a déclaré lui avoir rendu sa ponceuse
- **THEN** la section liste, dans ses prêts, le rabot, puis la ponceuse, puis la scie

#### Scenario: Catégories de l'emprunteur
- **WHEN** Alice a la scie de Bob (« Prêté »), Carole a déclaré lui avoir remis sa ponceuse et Alice a déclaré avoir rendu la perceuse de Bob, tous jusqu'à demain ou plus tard
- **THEN** ses emprunts sont listés dans l'ordre ponceuse, perceuse, scie

### Requirement: Tri dans une catégorie de « Gestion des prêts »
Dans chaque catégorie, les lignes SHALL aller de la date de fin la plus proche à la plus lointaine ;
les demandes reçues, de la date de début la plus proche. À date égale, l'ordre reste stable.

#### Scenario: Date de fin dans une catégorie
- **WHEN** Alice a accepté de prêter son rabot à Bob jusqu'au 20 et sa scie à Carole jusqu'au 15
- **THEN** la scie est listée avant le rabot

#### Scenario: Demandes reçues par date de début
- **WHEN** Alice a reçu une demande de Bob pour sa scie à partir du 25 et une de Carole pour son rabot à partir du 21
- **THEN** la demande du rabot est listée avant celle de la scie

### Requirement: Lignes de « Gestion des prêts » limitées
Chaque groupe de la section SHALL afficher au plus 5 lignes, dans son ordre ; sous un groupe qui en
a davantage, un bouton « Voir tous mes prêts » mène à « Mes prêts ».

#### Scenario: Plus de 5 lignes dans un groupe
- **WHEN** Alice a reçu 6 demandes d'emprunt
- **THEN** le groupe « Demandes reçues » affiche les 5 premières et un bouton « Voir tous mes prêts » qui mène à « Mes prêts »

#### Scenario: 5 lignes ou moins
- **WHEN** Alice a reçu 5 demandes d'emprunt
- **THEN** le groupe « Demandes reçues » affiche les 5 et pas de bouton « Voir tous mes prêts »

#### Scenario: Bouton par groupe
- **WHEN** Alice a 6 emprunts en cours et prête 2 outils
- **THEN** seul le groupe « Mes emprunts » a un bouton « Voir tous mes prêts »

### Requirement: Retard mis en évidence
Une ligne « En retard » de la section « Gestion des prêts » SHALL être mise en évidence en rouge,
par le libellé « En retard » et par le même style que sur « Mes prêts ».

#### Scenario: Ligne en retard
- **WHEN** Alice a la perceuse de Bob jusqu'à hier
- **THEN** la ligne de la perceuse sur l'accueil porte « En retard » et le style de retard

### Requirement: Gestion des contacts
La section « Gestion des contacts » SHALL lister les demandes de contact reçues, de la plus ancienne
à la plus récente, avec « Accepter » et « Refuser », puis les contacts noués depuis 30 jours, du plus
récent au plus ancien, sous la forme « Vous êtes maintenant en contact avec <prénom> <nom> », pour
les deux personnes. Un refus MUST NOT y apparaître, ni rien qui permette de le déduire. Un bouton mène
à « Mes contacts ».

#### Scenario: Demande reçue
- **WHEN** Carole a envoyé une demande de contact à Alice
- **THEN** la section d'Alice affiche la demande de Carole avec « Accepter » et « Refuser »

#### Scenario: Contact noué, des deux côtés
- **WHEN** Bob a accepté la demande d'Alice il y a 3 jours
- **THEN** la section d'Alice affiche « Vous êtes maintenant en contact avec Bob Gagnon »
- **AND** la section de Bob affiche « Vous êtes maintenant en contact avec Alice Tremblay »

#### Scenario: Contact ancien
- **WHEN** Alice et Bob sont en contact depuis 31 jours
- **THEN** la section d'Alice n'affiche pas « Vous êtes maintenant en contact avec Bob Gagnon »

#### Scenario: Refus discret
- **WHEN** Bob a refusé la demande d'Alice
- **THEN** la section d'Alice n'affiche rien sur Bob

#### Scenario: Contact retiré
- **WHEN** Bob a accepté la demande d'Alice hier, puis l'a retirée de ses contacts
- **THEN** la section d'Alice n'affiche rien sur Bob

### Requirement: Nouveaux outils
La section « Nouveaux outils » SHALL afficher, avec les cartes de « Trouver un outil », au plus 6
outils visibles de l'utilisateur ajoutés depuis 30 jours, du plus récent au plus ancien, dans un
ordre stable à date égale. Au-delà de 6, un bouton « Voir plus » mène à « Trouver un outil » trié
par date d'ajout, du plus récent au plus ancien.

#### Scenario: Outils récents
- **WHEN** Bob, contact d'Alice, a ajouté une perceuse il y a 2 jours et une scie il y a 5 jours
- **THEN** la section d'Alice affiche la perceuse puis la scie

#### Scenario: Borne des 30 jours
- **WHEN** Bob a ajouté une scie il y a 30 jours, en fin de soirée à l'heure du site
- **THEN** la section d'Alice affiche la scie

#### Scenario: Outil trop ancien
- **WHEN** Bob a ajouté une ponceuse il y a 31 jours
- **THEN** la section d'Alice n'affiche pas la ponceuse

#### Scenario: Outils non visibles
- **WHEN** dans les 30 derniers jours, Alice a ajouté un rabot, Bob a ajouté une scie qu'il a retirée de la circulation et une tondeuse « Hors d'usage », et Dave, qui n'est pas son contact, a ajouté une perceuse
- **THEN** la section d'Alice n'affiche aucun de ces outils

#### Scenario: Outil prêté
- **WHEN** la perceuse ajoutée par Bob il y a 2 jours est prêtée à Carole
- **THEN** la section d'Alice affiche la perceuse avec son statut de prêt et « Emprunter » grisé

#### Scenario: Exactement 6
- **WHEN** les contacts d'Alice ont ajouté 6 outils depuis 30 jours
- **THEN** la section affiche les 6 et pas de bouton « Voir plus »

#### Scenario: Plus de 6
- **WHEN** les contacts d'Alice ont ajouté 7 outils depuis 30 jours
- **THEN** la section affiche les 6 plus récents et un bouton « Voir plus »
- **AND** « Voir plus » mène à « Trouver un outil » trié par date d'ajout, du plus récent au plus ancien

### Requirement: Date qui rend un outil nouveau
Seule la date d'ajout de l'outil SHALL compter : ni une remise en circulation, ni un retour d'un
état « Hors d'usage », ni la date du lien de contact ne rendent un outil nouveau.

#### Scenario: Remise en circulation
- **WHEN** Bob remet en circulation une scie ajoutée il y a 3 mois
- **THEN** la section d'Alice n'affiche pas la scie

#### Scenario: Nouveau contact
- **WHEN** Bob, devenu contact d'Alice hier, a ajouté une perceuse il y a 3 mois
- **THEN** la section d'Alice n'affiche pas la perceuse

### Requirement: Sections vides
Une section sans ligne SHALL rester affichée avec un message : « Aucun prêt en cours »,
« Aucune demande de contact » et « Aucun nouvel outil depuis 30 jours ». Sans contact, « Nouveaux
outils » affiche « Vous n'avez encore aucun contact » avec un lien vers la recherche d'utilisateurs.

#### Scenario: Nouveau compte
- **WHEN** Alice vient de créer son compte et ouvre `/`
- **THEN** la page répond 200 et affiche « Aucun prêt en cours », « Aucune demande de contact » et « Vous n'avez encore aucun contact »

#### Scenario: Contacts sans nouvel outil
- **WHEN** Alice a des contacts qui n'ont ajouté aucun outil depuis 30 jours
- **THEN** la section « Nouveaux outils » affiche « Aucun nouvel outil depuis 30 jours »

### Requirement: Retour à l'accueil après une action
Une action lancée depuis l'accueil (réponse à une demande d'emprunt ou de contact, action sur un
prêt, demande d'emprunt depuis une carte) SHALL ramener à l'accueil avec son message, de succès
comme d'erreur. Le retour est désigné par une valeur fixe, jamais par une adresse. « Annuler le
prêt » mène à sa page de confirmation, qui ramène à « Mes prêts ».

#### Scenario: Acceptation depuis l'accueil
- **WHEN** Alice clique « Accepter » sur la demande de Carole pour sa scie, sur l'accueil
- **THEN** elle revient sur l'accueil, la demande est acceptée et « Demande de Carole Roy acceptée » est affiché comme un message de succès

#### Scenario: Envoi en double depuis l'accueil
- **WHEN** Alice a déclaré avoir rendu la perceuse depuis l'accueil, revient en arrière et envoie de nouveau « J'ai rendu l'outil »
- **THEN** elle revient sur l'accueil avec « Ce prêt a déjà changé de statut »

#### Scenario: Demande de contact déjà traitée
- **WHEN** Alice a accepté la demande de Carole depuis l'accueil, revient en arrière et clique « Refuser »
- **THEN** elle revient sur l'accueil avec « Cette demande n'est plus en attente » et reste en contact avec Carole

#### Scenario: Emprunter depuis l'accueil
- **WHEN** Alice clique « Emprunter » sur la perceuse de Bob dans « Nouveaux outils » et confirme
- **THEN** elle revient sur l'accueil avec « Demande envoyée à Bob Gagnon »

#### Scenario: Jeton manquant
- **WHEN** une action de l'accueil est envoyée sans jeton CSRF
- **THEN** le système répond 400 et rien ne change
