# profil Specification

## Purpose
Permettre à un utilisateur connecté de consulter ses informations, de modifier son adresse et son
téléphone, et de supprimer son compte en effaçant ses données personnelles sans casser l'historique
des prêts de ses anciens partenaires (ADR 0023).

## Requirements

### Requirement: Profil réservé à un utilisateur connecté
La page « Mon profil » (`/profile`), la page de confirmation de la suppression et leurs envois MUST
exiger une session ouverte : un visiteur est redirigé vers `/login`. Un utilisateur SHALL n'y voir et
n'y modifier que son propre compte : aucune de ces adresses ne désigne un autre compte.

#### Scenario: Visiteur non connecté
- **WHEN** un visiteur demande `/profile`
- **THEN** il est redirigé vers `/login`
- **AND** la page de connexion affiche « Veuillez vous connecter pour accéder à cette page »

#### Scenario: Envoi sans session
- **WHEN** un visiteur envoie le formulaire de suppression du compte, avec un jeton CSRF valide de sa session de visiteur
- **THEN** il est redirigé vers `/login` et aucun compte n'est modifié

### Requirement: Accès depuis le menu du compte
Le menu du compte d'un utilisateur connecté SHALL avoir « Mon profil » pour première entrée, un lien
texte vers `/profile` comme les autres entrées du menu, et non plus une entrée grisée. Pour un compte
non confirmé, « Mon profil » SHALL porter une pastille « 1 », annoncée « courriel à confirmer » aux
lecteurs d'écran. La navigation d'un visiteur MUST NOT l'offrir.

#### Scenario: Première entrée du menu
- **WHEN** un utilisateur connecté ouvre son menu du compte
- **THEN** sa première entrée est le lien « Mon profil », vers `/profile`, avant « Gérer mes outils »

#### Scenario: Compte non confirmé
- **WHEN** Alice, non confirmée, ouvre une page du site
- **THEN** « Mon profil » porte une pastille « 1 » dans son menu du compte

#### Scenario: Compte confirmé
- **WHEN** Alice, confirmée, ouvre une page du site
- **THEN** « Mon profil » ne porte aucune pastille

#### Scenario: Visiteur
- **WHEN** un visiteur ouvre une page du site
- **THEN** la navigation ne contient pas « Mon profil »

### Requirement: Informations du profil
La page « Mon profil » SHALL afficher le prénom, le nom et le courriel de l'utilisateur en texte, sans
champ pour les modifier, et un formulaire avec son adresse et son téléphone actuels, vides s'il n'en a
pas, et le bouton « Enregistrer ». Pour un compte non confirmé, elle SHALL commencer par un bandeau
« Votre courriel n'est pas confirmé. Confirmez-le avec le lien reçu à <courriel> pour emprunter et
accepter des demandes. » suivi du bouton « Renvoyer le courriel ».

#### Scenario: Page du profil
- **WHEN** Alice Tremblay, inscrite avec `alice@example.com`, adresse « 12 rue des Érables » et sans téléphone, ouvre « Mon profil »
- **THEN** la page affiche « Alice Tremblay » et `alice@example.com`, sans champ pour les modifier
- **AND** le champ de l'adresse contient « 12 rue des Érables » et celui du téléphone est vide

#### Scenario: Bandeau d'un compte non confirmé
- **WHEN** Alice, non confirmée, ouvre « Mon profil »
- **THEN** la page commence par « Votre courriel n'est pas confirmé. Confirmez-le avec le lien reçu à alice@example.com pour emprunter et accepter des demandes. » et le bouton « Renvoyer le courriel »

#### Scenario: Compte confirmé
- **WHEN** Alice, confirmée, ouvre « Mon profil »
- **THEN** la page n'affiche ni le bandeau ni « Renvoyer le courriel »

#### Scenario: Nom et courriel non modifiables
- **WHEN** Alice envoie le formulaire du profil avec en plus un prénom, un nom et un courriel différents
- **THEN** son prénom, son nom et son courriel ne changent pas

### Requirement: Modification de l'adresse et du téléphone
L'envoi du formulaire du profil SHALL enregistrer l'adresse et le téléphone sans les espaces autour ;
un champ vide, ou fait d'espaces, retire l'information. Le téléphone est gardé tel que saisi, sans
normalisation. Après l'enregistrement, l'utilisateur revient sur « Mon profil » avec le message de
succès « Votre profil a été enregistré ».

#### Scenario: Ajout du téléphone
- **WHEN** Alice, sans téléphone, envoie « ␠(418) 555-0123␠ » comme téléphone
- **THEN** son téléphone est « (418) 555-0123 »
- **AND** elle revient sur « Mon profil », qui affiche « Votre profil a été enregistré » comme un message de succès

#### Scenario: Modification de l'adresse
- **WHEN** Alice remplace « 12 rue des Érables » par « 8 avenue du Parc »
- **THEN** son adresse est « 8 avenue du Parc »

#### Scenario: Retrait de l'adresse
- **WHEN** Alice vide le champ de l'adresse, ou n'y laisse que des espaces, et envoie le formulaire
- **THEN** elle n'a plus d'adresse

### Requirement: Validation de l'adresse et du téléphone
Une adresse de plus de 250 caractères ou un téléphone de plus de 20 caractères, comptés sans les
espaces autour, ou un téléphone qui contient autre chose que des chiffres de 0 à 9, des espaces et
`+ - ( ) .`, MUST être refusé : rien n'est enregistré et le formulaire est réaffiché avec les valeurs
saisies et le message de chaque erreur.

#### Scenario: Adresse trop longue
- **WHEN** Alice envoie une adresse de 251 caractères et un téléphone valide
- **THEN** ni son adresse ni son téléphone ne changent
- **AND** la page affiche « L'adresse ne doit pas dépasser 250 caractères » et ses champs contiennent les valeurs saisies

#### Scenario: Longueurs limites acceptées
- **WHEN** Alice envoie une adresse de 250 caractères et un téléphone de 20 caractères permis
- **THEN** les deux sont enregistrés

#### Scenario: Téléphone trop long
- **WHEN** Alice envoie un téléphone de 21 chiffres
- **THEN** son téléphone ne change pas et la page affiche « Le téléphone ne doit pas dépasser 20 caractères »

#### Scenario: Caractère refusé dans le téléphone
- **WHEN** Alice envoie « 418-555-0123 poste 4 » comme téléphone
- **THEN** son téléphone ne change pas
- **AND** la page affiche « Le téléphone ne peut contenir que des chiffres, des espaces et les caractères + - ( ) . »

#### Scenario: Texte affiché tel quel
- **WHEN** Alice enregistre l'adresse `<script>alert(1)</script>`
- **THEN** « Mon profil » affiche ce texte tel quel, sans l'exécuter ni l'interpréter comme du HTML

### Requirement: Section « Supprimer mon compte »
Au bas de « Mon profil », une section « Supprimer mon compte » SHALL afficher « La suppression de
votre compte est irréversible. » et le bouton rouge « Supprimer mon compte », qui mène à la page de
confirmation.

#### Scenario: Section sans prêt en cours
- **WHEN** Alice n'a aucun prêt en cours et ouvre « Mon profil »
- **THEN** la section « Supprimer mon compte » est la dernière de la page
- **AND** elle affiche « La suppression de votre compte est irréversible. » et le bouton rouge « Supprimer mon compte », qui mène à la page de confirmation

### Requirement: Suppression bloquée par un prêt en cours
Tant que l'utilisateur a, comme emprunteur ou comme prêteur, un prêt « Remise à confirmer »,
« Prêté » ou « Retour à confirmer », retards compris, la section SHALL désactiver le bouton (grisé),
afficher « Tous vos prêts en cours doivent être complétés avant de supprimer votre compte », lister
ces prêts (outil, autre personne, statut) et offrir un lien vers « Mes prêts ».

#### Scenario: Emprunt en cours
- **WHEN** Alice a la perceuse de Bob et ouvre « Mon profil »
- **THEN** le bouton « Supprimer mon compte » est désactivé et grisé
- **AND** la section affiche « Tous vos prêts en cours doivent être complétés avant de supprimer votre compte », liste la perceuse avec Bob Gagnon et « Prêté », et un lien vers « Mes prêts »

#### Scenario: Prêt en retard
- **WHEN** Bob a la scie d'Alice depuis une date de fin passée
- **THEN** la section de « Mon profil » d'Alice liste la scie avec « En retard » et le bouton est désactivé

#### Scenario: Remise ou retour déclarés
- **WHEN** Alice a déclaré avoir remis son rabot à Bob, et Carole a déclaré lui avoir rendu sa ponceuse
- **THEN** la section liste le rabot et la ponceuse et le bouton est désactivé

#### Scenario: Demandes et prêts acceptés ne bloquent pas
- **WHEN** Alice n'a qu'une demande d'emprunt en attente et un prêt accepté sans remise déclarée
- **THEN** le bouton « Supprimer mon compte » est actif

#### Scenario: Confirmation demandée malgré un prêt en cours
- **WHEN** Alice a la perceuse de Bob et demande la page de confirmation de la suppression
- **THEN** elle est redirigée vers « Mon profil », qui affiche « Tous vos prêts en cours doivent être complétés avant de supprimer votre compte »

### Requirement: Page de confirmation de la suppression
La page de confirmation SHALL afficher « La suppression de votre compte est irréversible. », annoncer
les demandes d'emprunt en attente et les prêts acceptés sans remise déclarée qui seront annulés, s'il
y en a, et demander le nom complet et le mot de passe actuel, avec « Annuler », gris, vers « Mon
profil », et « Confirmer la suppression », rouge. L'ouvrir ne supprime rien.

#### Scenario: Page sans annulation
- **WHEN** Alice n'a ni demande d'emprunt ni prêt accepté et clique « Supprimer mon compte »
- **THEN** la page demande son nom complet et son mot de passe, avec « Annuler » gris et « Confirmer la suppression » rouge
- **AND** elle n'annonce aucune annulation et le compte d'Alice existe toujours

#### Scenario: Annulations annoncées
- **WHEN** Alice a demandé la perceuse de Bob, sans réponse, et a accepté de prêter sa scie à Carole, sans remise déclarée
- **AND** Alice ouvre la confirmation de la suppression
- **THEN** la page annonce « 1 demande d'emprunt en attente et 1 prêt accepté seront annulés »

#### Scenario: Annuler
- **WHEN** Alice clique « Annuler » sur la page de confirmation
- **THEN** elle revient sur « Mon profil » et son compte n'est pas supprimé

### Requirement: Vérification avant la suppression
L'envoi de la confirmation SHALL supprimer le compte seulement si le nom saisi égale le prénom suivi
du nom, sans égard à la casse, aux accents ni aux espaces autour, un tiret valant une espace et
plusieurs espaces une seule, et si le mot de passe est celui du compte. Sinon, MUST rien supprimer et
réafficher la page avec « Le nom ou le mot de passe ne correspond pas », le nom saisi et un mot de
passe vide.

#### Scenario: Nom saisi sans accents ni majuscules
- **WHEN** Élise Côté-Roy saisit « elise cote roy » et son mot de passe, puis confirme
- **THEN** son compte est supprimé

#### Scenario: Mauvais nom
- **WHEN** Alice Tremblay saisit « Alice » et son mot de passe, puis confirme
- **THEN** son compte n'est pas supprimé
- **AND** la page affiche « Le nom ou le mot de passe ne correspond pas », le champ du nom contient « Alice » et celui du mot de passe est vide

#### Scenario: Mauvais mot de passe
- **WHEN** Alice saisit « Alice Tremblay » et un mot de passe erroné, puis confirme
- **THEN** son compte n'est pas supprimé et la page affiche « Le nom ou le mot de passe ne correspond pas »

#### Scenario: Champs vides
- **WHEN** Alice confirme sans rien saisir
- **THEN** son compte n'est pas supprimé et la page affiche « Le nom ou le mot de passe ne correspond pas »

#### Scenario: Prêt en cours au moment de l'envoi
- **WHEN** Alice a ouvert la confirmation, puis Bob a déclaré lui avoir remis sa perceuse
- **AND** Alice confirme avec son nom et son mot de passe
- **THEN** son compte n'est pas supprimé
- **AND** elle est redirigée vers « Mon profil », qui affiche « Tous vos prêts en cours doivent être complétés avant de supprimer votre compte »

#### Scenario: Envoi forgé malgré un prêt en cours
- **WHEN** Alice a la perceuse de Bob et envoie directement le formulaire de suppression avec son nom et son mot de passe
- **THEN** son compte n'est pas supprimé et la perceuse reste « Prêté »

#### Scenario: Envoi sans jeton CSRF
- **WHEN** le formulaire de suppression est envoyé sans jeton CSRF valide
- **THEN** le système répond 400 et le compte n'est pas supprimé

#### Scenario: Pas de suppression par un lien
- **WHEN** la suppression est demandée sans envoi de formulaire (`GET`)
- **THEN** le compte n'est pas supprimé

### Requirement: Effet de la suppression
Une suppression confirmée SHALL effacer le courriel, l'adresse et le téléphone, rendre le mot de passe
inutilisable, supprimer les demandes et relations de contact du compte dans les deux sens, retirer ses
outils en effaçant photo, description et notes privées, effacer le message des prêts qu'il a demandés
et annuler ses demandes d'emprunt en attente et prêts acceptés sans remise déclarée, des deux côtés.

#### Scenario: Données personnelles effacées
- **WHEN** Alice, avec une adresse et un téléphone, supprime son compte
- **THEN** son compte n'a plus ni courriel, ni adresse, ni téléphone
- **AND** son prénom et son nom sont gardés

#### Scenario: Contacts défaits
- **WHEN** Alice est en contact avec Bob, a reçu une demande de Carole et en a envoyé une à Denis
- **AND** Alice supprime son compte
- **THEN** Bob ne la voit plus dans « Mes contacts », la demande de Carole et celle à Denis n'existent plus

#### Scenario: Outils retirés et vidés
- **WHEN** Alice a une perceuse avec photo, description et notes privées, et supprime son compte
- **THEN** la perceuse n'est plus en circulation, n'a plus ni photo, ni description, ni notes privées
- **AND** elle garde son nom et son état

#### Scenario: Demandes et prêts à venir annulés
- **WHEN** Alice a demandé la perceuse de Bob, sans réponse, et Carole a une acceptation à venir pour la scie d'Alice
- **AND** Alice supprime son compte
- **THEN** les deux sont « Annulée »

#### Scenario: Messages d'Alice effacés, ceux des autres gardés
- **WHEN** Alice a emprunté la perceuse de Bob avec le message « Pour la terrasse », et Bob a emprunté la scie d'Alice avec le message « Merci »
- **AND** les deux prêts sont « Complété » et Alice supprime son compte
- **THEN** les deux prêts sont gardés, le premier sans message et le second avec « Merci »

#### Scenario: Deux suppressions
- **WHEN** Alice puis Bob suppriment leur compte
- **THEN** les deux comptes sont supprimés sans erreur

### Requirement: Fin de session après la suppression
Une suppression confirmée SHALL fermer la session et mener l'utilisateur à
`/logged-out?reason=account-deleted`, qui affiche « Votre compte a été supprimé ».

#### Scenario: Déconnexion après la suppression
- **WHEN** Alice confirme la suppression de son compte
- **THEN** elle est redirigée vers `/logged-out?reason=account-deleted`, qui affiche « Votre compte a été supprimé »
- **AND** les requêtes suivantes la traitent comme une visiteuse
