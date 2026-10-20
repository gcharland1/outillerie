# accueil Specification

## Purpose
Page d'accueil publique de L'Outillerie : premier point d'entrée du site communautaire de partage d'outils entre voisins.

## Requirements

### Requirement: Page d'accueil
Le système SHALL servir la page d'accueil à la racine `/`, rendue à partir du gabarit `index.html`.

#### Scenario: Visite de la racine
- **WHEN** un visiteur demande `GET /`
- **THEN** le système répond 200
- **AND** la page est rendue avec le gabarit `index.html`

#### Scenario: Message de bienvenue
- **WHEN** un visiteur ouvre la page d'accueil
- **THEN** la page affiche « Bienvenue sur l'outillerie »
