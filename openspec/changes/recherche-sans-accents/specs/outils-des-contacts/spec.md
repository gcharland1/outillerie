## MODIFIED Requirements

### Requirement: Filtre par texte
Les pages qui listent des outils SHALL offrir un champ de texte : seuls les outils dont le nom ou
la description ressemble au texte sont listés, sans égard à la casse, aux accents ni à une faute
de frappe légère ; un tiret vaut une espace et plusieurs espaces n'en valent qu'une ; `%`, `_` et
`\`, y compris en pleine chasse, sont cherchés tels quels. Un texte vide ne filtre pas. Le champ
garde le texte cherché.

#### Scenario: Faute de frappe
- **WHEN** Bob a une « Perceuse » et Alice cherche « perseuse »
- **THEN** la perceuse figure dans les résultats

#### Scenario: Accents ignorés
- **WHEN** Bob a une « Scie à métaux » et Alice cherche « scie a metaux »
- **THEN** la scie figure dans les résultats

#### Scenario: Accents du texte ignorés
- **WHEN** Bob a une « Scie a metaux » et Alice cherche « SCIE À MÉTAUX »
- **THEN** la scie figure dans les résultats

#### Scenario: Tiret et espace équivalents
- **WHEN** Bob a un « Tire-bouchon » et Alice cherche « tire bouchon »
- **THEN** le tire-bouchon figure dans les résultats

#### Scenario: Espaces multiples
- **WHEN** Bob a une « Scie sauteuse » et Alice cherche « scie    sauteuse »
- **THEN** la scie sauteuse figure dans les résultats

#### Scenario: Dans la description
- **WHEN** Bob a un « Coffret » décrit « embouts de vissage » et Alice cherche « vissage »
- **THEN** le coffret figure dans les résultats

#### Scenario: Sans rapport
- **WHEN** Bob a une « Perceuse » sans description et Alice cherche « tondeuse »
- **THEN** la perceuse ne figure pas dans les résultats

#### Scenario: Caractère joker cherché tel quel
- **WHEN** aucun outil ne contient « 50% » et Alice cherche « 50% »
- **THEN** aucun outil n'est listé

#### Scenario: Joker pleine chasse cherché tel quel
- **WHEN** Bob a une « Perceuse » et une « Scie », aucun outil ne contient « %%% », et Alice cherche « ％％％ »
- **THEN** aucun outil n'est listé

#### Scenario: Joker présent dans une description
- **WHEN** Bob a un « Niveau » décrit « précis à 100%%% » et une « Scie » sans description, et Alice cherche « %%% »
- **THEN** seul le niveau est listé

#### Scenario: Notes privées non cherchées
- **WHEN** seules les notes privées de la perceuse de Bob contiennent « cadenas » et Alice cherche « cadenas »
- **THEN** la perceuse ne figure pas dans les résultats

### Requirement: Ordre des outils
Avec un texte cherché, les outils SHALL être listés dans cet ordre : ceux dont le nom contient le
texte, selon les règles du filtre par texte, puis par ressemblance décroissante du nom, puis de la
description, puis par nom sans égard à la casse. Sans texte, ils sont triés par nom sans égard à
la casse.

#### Scenario: Correspondance exacte en tête
- **WHEN** Bob a un « Robot culinaire » et un « Rabot électrique » et Alice cherche « rabot »
- **THEN** le rabot électrique est listé en premier

#### Scenario: Contenu normalisé en tête
- **WHEN** Bob a un « Tire-bouchon » et un « Tire-clou » et Alice cherche « tire bouchon »
- **THEN** le tire-bouchon est listé en premier

#### Scenario: Nom avant description
- **WHEN** Bob a une « Scie sauteuse » et un « Établi » décrit « idéal pour la scie »
- **AND** Alice cherche « scie »
- **THEN** la scie sauteuse est listée avant l'établi

#### Scenario: Sans texte
- **WHEN** Bob a « carotteuse », « Bêche » et « agrafeuse » et Alice ouvre « Trouver un outil » sans texte
- **THEN** ils sont listés dans l'ordre « agrafeuse », « Bêche », « carotteuse »
