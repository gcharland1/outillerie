# Spec Delta

## ADDED Requirements

### Requirement: Courriel unique
Le système MUST refuser de créer un compte avec un courriel déjà utilisé par un autre compte, sans
égard à la casse, et l'indiquer sur la page d'inscription. Comme pour le nom d'utilisateur, le
message révèle qu'un compte utilise ce courriel.

#### Scenario: Courriel déjà utilisé
- **WHEN** un compte existe avec le courriel `alice@example.com`
- **AND** un visiteur soumet le formulaire d'inscription avec un autre nom d'utilisateur et le courriel `Alice@Example.com`
- **THEN** aucun compte n'est créé
- **AND** la page d'inscription affiche « Le courriel est déjà utilisé »
