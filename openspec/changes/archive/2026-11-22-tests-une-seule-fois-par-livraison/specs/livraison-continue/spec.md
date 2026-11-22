## MODIFIED Requirements

### Requirement: Tests du commit mergé
La CI MUST lancer le job de tests (lint, vérification des migrations, pytest, diagramme du schéma)
et le job de validation des specs sur chaque `push` vers `main`, en plus des pull requests. Sur un
`push` vers `main`, ces deux jobs MUST réussir sans rejouer leurs étapes seulement si le commit est un
commit de merge dont le second parent contient le premier, dont l'arbre égale celui du second parent,
et pour lequel un run `pull_request` de ce dépôt, sur ce second parent, est terminé avec succès avec
`tests` et `specs` réussis à sa dernière tentative. Dans tous les autres cas, y compris quand cette
preuve ne peut pas être établie, ils MUST rejouer toutes leurs étapes.

#### Scenario: Merge d'une PR
- **WHEN** une PR est mergée sur `main`
- **THEN** un run de la CI déclenché par `push` s'exécute sur le commit de `main` qui en résulte
- **AND** ce run comprend les jobs `tests` et `specs`

#### Scenario: Arbre déjà testé par la PR
- **WHEN** une PR à jour avec `main`, dont le run `pull_request` a réussi avec `tests` et `specs`, est mergée par un commit de merge
- **THEN** les jobs `tests` et `specs` du run `push` réussissent sans relancer le lint, les migrations, pytest, le diagramme ni la validation des specs

#### Scenario: Arbre différent
- **WHEN** l'arbre du commit de merge diffère de celui de la tête de la PR, ou la tête de la PR ne contient pas le premier parent
- **THEN** les jobs `tests` et `specs` rejouent toutes leurs étapes

#### Scenario: Push sans PR
- **WHEN** un commit arrive sur `main` sans être un commit de merge
- **THEN** les jobs `tests` et `specs` rejouent toutes leurs étapes

#### Scenario: Run de PR absent, en échec ou annulé
- **WHEN** aucun run `pull_request` du second parent n'est terminé avec succès, ou sa dernière tentative n'a pas `tests` et `specs` réussis
- **THEN** les jobs `tests` et `specs` rejouent toutes leurs étapes

#### Scenario: Run d'un fork
- **WHEN** le seul run `pull_request` réussi du second parent vient d'un dépôt autre que celui-ci
- **THEN** les jobs `tests` et `specs` rejouent toutes leurs étapes

#### Scenario: Recherche impossible
- **WHEN** l'API GitHub répond en erreur pendant la recherche de la preuve
- **THEN** les jobs `tests` et `specs` rejouent toutes leurs étapes
