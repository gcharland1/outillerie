## ADDED Requirements

### Requirement: Nombre de comptes listés
La recherche d'utilisateurs SHALL lister au plus 25 comptes : les 25 premiers dans l'ordre de
« Correspondance des utilisateurs ». Quand plus de 25 comptes correspondent, la page SHALL afficher
au-dessus des résultats « Plus de 25 utilisateurs correspondent à « texte » ; précisez votre
recherche », avec le texte cherché tel que saisi, sans nombre total. Avec 25 comptes ou moins,
aucun message n'est affiché.

#### Scenario: Plus de 25 comptes
- **WHEN** 26 autres comptes s'appellent Gagnon et Alice cherche « gagnon »
- **THEN** la page liste 25 comptes, les 25 premiers dans l'ordre de tri
- **AND** elle affiche « Plus de 25 utilisateurs correspondent à « gagnon » ; précisez votre recherche »

#### Scenario: Exactement 25 comptes
- **WHEN** 25 autres comptes s'appellent Gagnon et Alice cherche « gagnon »
- **THEN** la page liste les 25 comptes, sans message

#### Scenario: Correspondances exactes gardées
- **WHEN** 25 comptes ressemblent à « gagnon » sans le contenir, un compte contient « gagnon » et Alice cherche « gagnon »
- **THEN** le compte qui contient « gagnon » figure parmi les 25 comptes listés
