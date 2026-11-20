## MODIFIED Requirements

### Requirement: Page « Trouver un outil »
Pour un utilisateur connecté, le menu du compte SHALL offrir l'entrée « Trouver un outil » vers
la page du même nom, qui liste tous les outils visibles de ses contacts. La page MUST exiger
une session ouverte : un visiteur est redirigé vers `/login`.

#### Scenario: Entrée du menu du compte
- **WHEN** un utilisateur connecté ouvre une page du site
- **THEN** son prénom et son nom ouvrent un menu qui contient « Trouver un outil », qui mène à la page « Trouver un outil »

#### Scenario: Visiteur
- **WHEN** un visiteur demande la page « Trouver un outil »
- **THEN** il est redirigé vers `/login`
- **AND** la navigation d'un visiteur ne contient pas « Trouver un outil »
