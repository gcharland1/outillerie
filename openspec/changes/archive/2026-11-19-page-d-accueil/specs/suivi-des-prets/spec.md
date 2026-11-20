# Spec Delta

## MODIFIED Requirements

### Requirement: Actions réservées aux parties
Chaque action sur un prêt SHALL être réservée à la partie qui peut la faire selon le statut ; pour
toute autre personne, et pour un prêt inexistant, le système répond 404. Une action ramène à la page
d'où elle a été envoyée, « Mes prêts » ou l'accueil ; une origine inconnue ramène à « Mes prêts ».
Une action sur un prêt dont le statut ne la permet plus y ramène avec « Ce prêt a déjà changé de
statut », sans rien changer. Ces actions ne dépendent ni de la visibilité de l'outil ni du lien de
contact.

#### Scenario: Tiers
- **WHEN** Carole envoie « J'ai remis l'outil » pour le prêt de la perceuse de Bob à Alice
- **THEN** le système répond 404 et le prêt ne change pas

#### Scenario: Envoi en double
- **WHEN** Alice a déclaré avoir rendu la perceuse et envoie de nouveau « J'ai rendu l'outil » depuis « Mes prêts »
- **THEN** elle revient sur « Mes prêts » avec « Ce prêt a déjà changé de statut »

#### Scenario: Depuis l'accueil
- **WHEN** Bob clique « J'ai remis l'outil » sur l'accueil
- **THEN** le prêt est « Remise à confirmer » et Bob revient sur l'accueil

#### Scenario: Origine inconnue
- **WHEN** Bob envoie « J'ai remis l'outil » avec l'origine « https://exemple.com »
- **THEN** il revient sur « Mes prêts »

#### Scenario: Deux actions en même temps
- **WHEN** Alice déclare avoir rendu la perceuse pendant que Bob clique « J'ai reçu l'outil »
- **THEN** une seule des deux actions s'applique et l'autre ramène à sa page d'origine avec « Ce prêt a déjà changé de statut »

#### Scenario: Outil retiré pendant le prêt
- **WHEN** Alice a la perceuse de Bob et Bob retire la perceuse de la circulation
- **THEN** Alice peut encore déclarer « J'ai rendu l'outil » et Bob confirmer la réception

#### Scenario: Jeton manquant
- **WHEN** une action sur un prêt est envoyée sans jeton CSRF
- **THEN** le système répond 400 et le prêt ne change pas

#### Scenario: Visiteur
- **WHEN** un visiteur envoie une action sur un prêt
- **THEN** il est redirigé vers `/login` et le prêt ne change pas
