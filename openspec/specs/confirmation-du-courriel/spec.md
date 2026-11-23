# confirmation-du-courriel Specification

## Purpose
Prouver qu'un utilisateur reçoit les courriels de son adresse avant qu'il emprunte ou accepte une
demande : courriel de confirmation à lien signé, page de confirmation et renvoi (ADR 0027).

## Requirements

### Requirement: Contenu du courriel de confirmation
Le courriel de confirmation SHALL contenir le prénom du compte, un lien de confirmation valide 30
jours, cette durée, et une phrase qui invite à l'ignorer si on n'a pas créé ce compte. Il MUST NOT
contenir d'autre donnée du compte. Le lien MUST être construit à partir de l'adresse publique du site
configurée, jamais de l'en-tête `Host` de la requête.

#### Scenario: Contenu du courriel
- **WHEN** un courriel de confirmation est envoyé à Alice
- **THEN** il est adressé à son courriel, contient « Alice », un lien vers l'adresse publique du site, la mention de 30 jours et l'invitation à l'ignorer
- **AND** il ne contient ni son nom, ni son adresse, ni son téléphone

#### Scenario: En-tête Host forgé
- **WHEN** l'inscription d'Alice arrive avec l'en-tête `Host: exemple.com`
- **THEN** le lien du courriel pointe vers l'adresse publique configurée du site

### Requirement: Envoi du courriel de confirmation
Chaque envoi d'un courriel de confirmation MUST enregistrer son heure sur le compte. Un échec d'envoi
MUST être journalisé sans le lien et MUST NOT annuler l'opération qui l'a demandé.

#### Scenario: Échec d'envoi
- **WHEN** le serveur SMTP refuse le courriel de confirmation d'Alice
- **THEN** l'échec est journalisé sans le lien et l'opération qui l'a demandé réussit quand même

### Requirement: Page de confirmation
Le lien de confirmation SHALL ouvrir, sans exiger de session, une page « Confirmer mon courriel » avec
un bouton « Confirmer mon courriel ». Ouvrir la page MUST NOT confirmer le compte. La réponse MUST
porter l'en-tête `Referrer-Policy: same-origin`, pour que l'adresse de la page, qui contient le jeton,
ne parte vers aucun autre site, tout en laissant le bouton passer la protection CSRF en HTTPS.

#### Scenario: Ouverture du lien
- **WHEN** Alice ouvre le lien de son courriel de confirmation
- **THEN** la page affiche le bouton « Confirmer mon courriel »
- **AND** son compte n'est pas encore confirmé

#### Scenario: En-tête Referer
- **WHEN** la page de confirmation est servie
- **THEN** sa réponse porte `Referrer-Policy: same-origin`

#### Scenario: Confirmation en HTTPS
- **WHEN** Alice, sur le site servi en HTTPS, clique « Confirmer mon courriel » depuis la page du lien
- **THEN** son compte est confirmé

### Requirement: Lien expiré ou invalide
Un lien expiré SHALL afficher « Ce lien a expiré. Connectez-vous pour recevoir un nouveau courriel
depuis « Mon profil ». », et un lien altéré, ou celui d'un compte supprimé ou dont le courriel ne
correspond plus, « Ce lien n'est pas valide. », dans les deux cas sans bouton.

#### Scenario: Lien expiré
- **WHEN** Alice ouvre un lien envoyé il y a 31 jours
- **THEN** la page affiche « Ce lien a expiré. Connectez-vous pour recevoir un nouveau courriel depuis « Mon profil ». » sans bouton

#### Scenario: Lien altéré ou compte supprimé
- **WHEN** Alice ouvre un lien dont le jeton a été modifié, ou le lien d'un compte supprimé depuis
- **THEN** la page affiche « Ce lien n'est pas valide. » sans bouton

### Requirement: Confirmation du compte
Le bouton « Confirmer mon courriel » SHALL confirmer le compte du lien, et non celui de la session
ouverte dans le navigateur, puis rediriger vers « Mon profil » si une session est ouverte, sinon vers
la page de connexion, avec « Votre courriel est confirmé. » comme message de succès. La confirmation
MUST NOT ouvrir de session.

#### Scenario: Confirmation sans session
- **WHEN** Alice, sans session ouverte, clique « Confirmer mon courriel »
- **THEN** son compte est confirmé
- **AND** elle arrive sur la page de connexion avec « Votre courriel est confirmé. », sans session ouverte

#### Scenario: Session d'un autre compte
- **WHEN** Bob est connecté dans le navigateur et clique « Confirmer mon courriel » sur le lien d'Alice
- **THEN** le compte d'Alice est confirmé et celui de Bob ne change pas

### Requirement: Confirmation répétée ou refusée
Un compte déjà confirmé SHALL recevoir « Votre courriel est confirmé. » sans changement. Un lien
devenu expiré ou invalide au moment de l'envoi ramène à la page de confirmation avec son message. Le
formulaire exige le jeton CSRF.

#### Scenario: Double clic
- **WHEN** Alice clique deux fois « Confirmer mon courriel », ou dans deux onglets
- **THEN** son compte est confirmé une fois, et chaque réponse affiche « Votre courriel est confirmé. »

#### Scenario: Jeton CSRF manquant
- **WHEN** la confirmation est envoyée sans jeton CSRF
- **THEN** le système répond 400 et le compte n'est pas confirmé

### Requirement: Renvoi du courriel de confirmation
« Renvoyer le courriel » SHALL envoyer un nouveau courriel de confirmation à l'utilisateur connecté et
non confirmé, puis le ramener sur « Mon profil » avec « Courriel de confirmation envoyé à
<courriel>. ». Un compte déjà confirmé n'envoie rien et affiche « Votre courriel est déjà confirmé. ».
Les liens déjà envoyés restent valides jusqu'à leur expiration. Le formulaire exige le jeton CSRF.

#### Scenario: Renvoi
- **WHEN** Alice, non confirmée, dont le dernier courriel date de 6 minutes, clique « Renvoyer le courriel »
- **THEN** un courriel de confirmation lui est envoyé
- **AND** « Mon profil » affiche « Courriel de confirmation envoyé à alice@example.com. »

#### Scenario: Ancien lien après un renvoi
- **WHEN** Alice a reçu un lien il y a 10 jours, puis en redemande un, et ouvre l'ancien
- **THEN** l'ancien lien confirme son compte

### Requirement: Délai entre deux courriels de confirmation
Un compte MUST NOT recevoir plus d'un courriel de confirmation par période de 5 minutes. Pendant ce
délai, une demande de renvoi n'envoie rien et affiche « Un courriel vous a été envoyé il y a moins de
5 minutes. Réessayez dans <n> minute(s). ».

#### Scenario: Renvoi trop tôt
- **WHEN** le dernier courriel d'Alice date de 2 minutes et elle clique « Renvoyer le courriel »
- **THEN** aucun courriel n'est envoyé
- **AND** « Mon profil » affiche « Un courriel vous a été envoyé il y a moins de 5 minutes. Réessayez dans 3 minute(s). »

#### Scenario: Deux renvois simultanés
- **WHEN** Alice envoie deux demandes de renvoi au même moment
- **THEN** un seul courriel est envoyé

### Requirement: Emprunt réservé à un compte confirmé
Un compte non confirmé MUST NOT pouvoir demander un emprunt : la page de confirmation d'une demande et
son envoi le ramènent à la liste d'où il est venu avec « Confirmez votre courriel depuis « Mon
profil » pour emprunter. », sans rien créer. Cette règle s'applique après celles de « Outil qu'on
peut demander ».

#### Scenario: Demande forgée
- **WHEN** Alice, non confirmée, envoie directement une demande de la perceuse de Bob
- **THEN** aucune demande n'est créée
- **AND** Alice revient sur la liste d'origine avec « Confirmez votre courriel depuis « Mon profil » pour emprunter. »

#### Scenario: Compte confirmé
- **WHEN** Alice, confirmée, confirme une demande de la perceuse de Bob
- **THEN** la demande est créée comme avant

### Requirement: Acceptation réservée à un compte confirmé
Un propriétaire non confirmé MUST NOT pouvoir accepter une demande : « Accepter » est grisé sur
« Mes prêts » et sur l'accueil, et une acceptation envoyée quand même ramène à la page d'origine avec
« Confirmez votre courriel depuis « Mon profil » pour accepter une demande. », sans rien changer. Il
SHALL pouvoir refuser une demande et suivre ses prêts déjà acceptés ou en cours.

#### Scenario: Acceptation grisée
- **WHEN** Bob, non confirmé, a une demande d'Alice en attente
- **THEN** « Mes prêts » affiche « Accepter » grisé et « Refuser » actif

#### Scenario: Acceptation forgée
- **WHEN** Bob, non confirmé, envoie quand même l'acceptation de la demande d'Alice
- **THEN** la demande reste en attente
- **AND** Bob revient sur « Mes prêts » avec « Confirmez votre courriel depuis « Mon profil » pour accepter une demande. »

#### Scenario: Prêt en cours
- **WHEN** Bob, non confirmé, a un prêt accepté pour Alice et déclare avoir remis la perceuse
- **THEN** la remise est enregistrée comme avant

### Requirement: Jeton absent des journaux de l'app
Les lignes de requête que l'app journalise MUST NOT contenir le jeton d'un lien de confirmation.

#### Scenario: Ligne de requête masquée
- **WHEN** Alice ouvre le lien de confirmation
- **THEN** la ligne de requête journalisée par l'app contient le chemin de la page de confirmation sans le jeton
