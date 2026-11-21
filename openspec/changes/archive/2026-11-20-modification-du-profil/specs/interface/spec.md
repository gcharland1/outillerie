## MODIFIED Requirements

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
