## ADDED Requirements

### Requirement: Comptes supprimés exclus
La recherche d'utilisateurs MUST NOT lister un compte supprimé (ADR 0023), même quand son prénom et
son nom correspondent au texte cherché, et il ne compte pas dans le plafond de 25 comptes.

#### Scenario: Compte supprimé absent des résultats
- **WHEN** Bob Gagnon a supprimé son compte et Alice cherche « gagnon »
- **THEN** le compte de Bob ne figure pas dans les résultats
- **AND** la page affiche « Aucun utilisateur ne correspond à « gagnon » » si aucun autre compte ne correspond

#### Scenario: Plafond sans les comptes supprimés
- **WHEN** 25 autres comptes actifs et 1 compte supprimé s'appellent Gagnon et Alice cherche « gagnon »
- **THEN** la page liste les 25 comptes actifs, sans message de plafond
