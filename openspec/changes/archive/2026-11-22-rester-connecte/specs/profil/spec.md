## MODIFIED Requirements

### Requirement: Fin de session après la suppression
Une suppression confirmée SHALL fermer la session, effacer le cookie persistant de « Rester
connecté » de l'appareil et mener l'utilisateur à `/logged-out?reason=account-deleted`, qui affiche
« Votre compte a été supprimé ».

#### Scenario: Déconnexion après la suppression
- **WHEN** Alice confirme la suppression de son compte
- **THEN** elle est redirigée vers `/logged-out?reason=account-deleted`, qui affiche « Votre compte a été supprimé »
- **AND** les requêtes suivantes la traitent comme une visiteuse

#### Scenario: Suppression d'un compte resté connecté
- **WHEN** Alice, connectée case « Rester connecté » cochée, confirme la suppression de son compte
- **THEN** la réponse efface le cookie persistant
