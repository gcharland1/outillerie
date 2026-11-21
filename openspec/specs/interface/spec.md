# interface Specification

## Purpose
Fixer les règles d'affichage communes à toutes les pages du site : la couleur d'un bouton selon le sens
de son action, la couleur des liens, et la façon dont le nom d'un utilisateur est rendu.

## Requirements

### Requirement: Couleurs des boutons
Chaque bouton SHALL suivre l'ADR 0022 : bleu pour avancer, vers la suite d'une tâche ou vers plus de
contenu ; rouge pour retirer, annuler ou supprimer ce qui existe, ainsi que pour le bouton qui ouvre la
confirmation d'une telle action et celui qui la confirme ; gris pour reculer, quitter, dire non, et pour
tout bouton désactivé. Un groupe d'actions ou un formulaire MUST NOT avoir plus d'un bouton bleu. Un
bouton MUST NOT être vert. Un lien SHALL avoir le bleu des boutons.

#### Scenario: Rechercher et filtrer en bleu
- **WHEN** Alice ouvre « Trouver un outil »
- **THEN** « Rechercher » dans la barre de navigation et « Filtrer » sont bleus

#### Scenario: Voir plus en bleu
- **WHEN** l'accueil d'Alice a plus de nouveaux outils qu'il n'en montre et plus de prêts qu'un groupe n'en montre
- **THEN** « Voir plus », « Voir tous mes prêts » et « Mes contacts » sont bleus

#### Scenario: Retrait d'un outil en rouge
- **WHEN** Alice ouvre « Mes outils » puis clique « Retirer » sur sa perceuse
- **THEN** « Modifier » est bleu et « Retirer » rouge sur « Mes outils »
- **AND** sur la page de confirmation, « Confirmer le retrait » est rouge et « Annuler » gris

#### Scenario: Retrait d'un contact en rouge
- **WHEN** Alice ouvre « Mes contacts » puis clique « Retirer » à côté de Bob
- **THEN** « Retirer » est rouge sur « Mes contacts » et sur la page de confirmation, où « Annuler » est gris

#### Scenario: Annulation d'un prêt en rouge
- **WHEN** Alice ouvre la confirmation d'annulation d'un prêt accepté
- **THEN** « Annuler le prêt » est rouge et « Retour à « Mes prêts » » gris

#### Scenario: Dire non en gris
- **WHEN** Alice a reçu une demande de contact de Carole
- **THEN** « Accepter » est bleu et « Refuser » gris

#### Scenario: Un seul bleu par groupe
- **WHEN** un visiteur ouvre la page de connexion
- **THEN** « Inscription » est bleu et « Connexion » gris dans la barre de navigation, et « Se connecter » est bleu

#### Scenario: Bouton désactivé en gris
- **WHEN** Alice a déjà demandé la perceuse de Bob
- **THEN** « Demande envoyée », désactivé, est gris sur la carte de la perceuse

#### Scenario: Bouton d'envoi rouge
- **WHEN** un bouton d'envoi d'un formulaire est rouge, comme « Confirmer le retrait »
- **THEN** il garde le rouge et n'est pas rendu gris comme les autres boutons d'envoi

#### Scenario: Jamais de vert
- **WHEN** n'importe quelle page du site est affichée
- **THEN** aucun bouton n'est vert, et aucun bouton n'est rouge sauf ceux qui retirent, annulent ou suppriment

### Requirement: Nom d'un utilisateur
Le nom complet d'un autre utilisateur SHALL mener à ses outils, sur la page du contact, quand
c'est un contact. Le nom d'un compte qui n'est pas un contact, comme le sien propre, MUST être
affiché en texte, sans lien ; celui d'un compte
supprimé, grisé et suivi de « (supprimé) ».
Font exception le nom du menu du compte, le titre de la page d'un contact, le libellé « Message
pour <prénom> <nom> » de la demande d'emprunt et les messages de succès.

#### Scenario: Contact dans les prêts
- **WHEN** Bob, contact d'Alice, a accepté sa demande d'emprunt de la perceuse
- **THEN** « Bob Gagnon » mène à la page de Bob sur l'accueil d'Alice, dans « Mes prêts » et sur la page de confirmation d'annulation

#### Scenario: Ex-contact dans les prêts
- **WHEN** Alice a la perceuse de Bob et a retiré Bob de ses contacts
- **THEN** « Bob Gagnon » est affiché sans lien sur l'accueil d'Alice et dans « Mes prêts »

#### Scenario: Propriétaire d'un outil à emprunter
- **WHEN** Alice clique « Emprunter » sur la perceuse de Bob, son contact
- **THEN** « Propriétaire : Bob Gagnon » mène à la page de Bob
- **AND** le libellé « Message pour Bob Gagnon (facultatif) » n'est pas un lien

#### Scenario: Demande de contact reçue
- **WHEN** Carole, qui n'est pas contact d'Alice, lui a envoyé une demande de contact
- **THEN** « Carole Roy » est affiché sans lien sur l'accueil d'Alice et dans « Mes contacts »

#### Scenario: Contact noué
- **WHEN** Alice et Bob sont devenus contacts il y a 3 jours
- **THEN** dans « Vous êtes maintenant en contact avec Bob Gagnon » de l'accueil d'Alice, « Bob Gagnon » mène à la page de Bob

#### Scenario: Résultats de recherche
- **WHEN** Bob est contact d'Alice, Carole ne l'est pas, et Alice cherche un nom qui les trouve tous deux
- **THEN** « Bob Gagnon » mène à la page de Bob et « Carole Roy » est affiché sans lien

#### Scenario: Confirmation du retrait d'un contact
- **WHEN** Alice ouvre la confirmation du retrait de Bob
- **THEN** « Bob Gagnon » dans la question mène à la page de Bob

#### Scenario: Son propre nom
- **WHEN** Alice ouvre « Mon profil »
- **THEN** « Alice Tremblay » est affiché sans lien

#### Scenario: Menu du compte
- **WHEN** Alice est connectée
- **THEN** son prénom et son nom dans la barre de navigation ouvrent le menu du compte et ne sont pas un lien

#### Scenario: Titre de la page d'un contact
- **WHEN** Alice ouvre la page de Bob, son contact
- **THEN** le titre « Bob Gagnon » et « Outils de Bob Gagnon » ne sont pas des liens

#### Scenario: Compte supprimé
- **WHEN** Bob Gagnon a emprunté la scie d'Alice, le prêt est « Complété », et Bob supprime son compte
- **AND** Alice ouvre « Mes prêts »
- **THEN** la ligne de la scie affiche « Bob Gagnon (supprimé) », grisé et sans lien
