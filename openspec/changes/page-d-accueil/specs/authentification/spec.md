# Spec Delta

## MODIFIED Requirements

### Requirement: Pages connectées non mises en cache
Toute réponse servie à un utilisateur connecté MUST interdire sa mise en cache par le navigateur,
pour qu'après une déconnexion ou une expiration, le retour arrière ne réaffiche aucun contenu
réservé à l'utilisateur connecté.

#### Scenario: En-tête pour un utilisateur connecté
- **WHEN** un utilisateur connecté ouvre une page du site
- **THEN** la réponse porte l'en-tête `Cache-Control: no-store`

#### Scenario: Pages de visiteur cachables
- **WHEN** un visiteur ouvre la page de connexion ou de création de compte
- **THEN** la réponse ne porte pas `Cache-Control: no-store`

#### Scenario: Retour arrière après déconnexion
- **WHEN** un utilisateur se déconnecte puis utilise le bouton « Précédent » du navigateur pour revenir à l'accueil
- **THEN** le navigateur redemande la page au serveur
- **AND** il est redirigé vers la page de connexion
