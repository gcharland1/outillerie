## MODIFIED Requirements

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
- **THEN** les deux « Voir plus » et « Mes contacts » sont bleus

#### Scenario: Voir plus et Filtrer des résultats en bleu
- **WHEN** Alice cherche un texte qui correspond à plus de 5 comptes et plus de 6 outils
- **THEN** « Filtrer » et les deux « Voir plus » de la page de résultats sont bleus, chacun dans son propre groupe

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
