# Spec Delta

## Purpose

Empêcher un autre site, ou une page piégée, de soumettre un formulaire de L'Outillerie au nom
d'un voisin à son insu.

## ADDED Requirements

### Requirement: Jeton exigé sur toute requête POST
Le système MUST refuser, par une réponse 400 et sans effet, toute requête `POST` qui ne porte pas
un jeton anti-CSRF valide émis par le site pour la même session de navigateur. Cela vaut pour
tous les formulaires, y compris l'inscription, la connexion et la déconnexion.

#### Scenario: Connexion sans jeton
- **WHEN** un visiteur soumet des identifiants valides à `/login` sans jeton
- **THEN** le système répond 400
- **AND** aucune session n'est ouverte

#### Scenario: Déconnexion sans jeton
- **WHEN** un utilisateur connecté envoie `POST /logout` sans jeton
- **THEN** le système répond 400
- **AND** il reste connecté

#### Scenario: Enregistrement d'outil avec un jeton invalide
- **WHEN** un utilisateur connecté soumet le formulaire d'enregistrement d'un outil avec un jeton altéré
- **THEN** le système répond 400
- **AND** aucun outil n'est enregistré

### Requirement: Formulaires du site acceptés
Chaque formulaire `POST` servi par le site SHALL inclure un jeton valide, de sorte qu'un voisin
qui le soumet depuis la page reçue n'est jamais refusé pour cette raison.

#### Scenario: Connexion depuis la page de connexion
- **WHEN** un visiteur ouvre `/login` et soumet le formulaire avec des identifiants valides et le jeton de la page
- **THEN** il est connecté et redirigé vers `/`

#### Scenario: Formulaire ouvert longtemps
- **WHEN** un visiteur soumet le formulaire de connexion deux heures après avoir ouvert `/login`, dans la même session de navigateur
- **THEN** il est connecté et redirigé vers `/`

### Requirement: Message au refus
Une requête refusée pour un jeton absent ou invalide SHALL afficher, dans la mise en page du site,
« Le formulaire a expiré ou est invalide. Rechargez la page et réessayez. »

#### Scenario: Formulaire expiré
- **WHEN** une requête `POST` est refusée faute de jeton valide
- **THEN** la page affiche « Le formulaire a expiré ou est invalide. Rechargez la page et réessayez. »
