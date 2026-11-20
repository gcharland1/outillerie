## MODIFIED Requirements

### Requirement: Correspondance des utilisateurs
La recherche d'utilisateurs SHALL lister les autres comptes dont le prénom suivi du nom
contient le texte ou, dès 4 caractères, lui ressemble malgré une faute
légère, sans égard à la casse, aux accents ni aux espaces autour ; un tiret vaut une espace,
plusieurs espaces une seule ; `%`, `_` et `\` sont cherchés tels quels. Tri : ceux qui
contiennent le texte, puis ressemblance décroissante, puis prénom, puis nom, sans égard à la
casse ni aux accents, puis du plus ancien compte au plus récent. Jamais son propre compte.

#### Scenario: Par le nom
- **WHEN** Bob Gagnon a un compte et Alice cherche « GAGN »
- **THEN** le compte de Bob figure dans les résultats

#### Scenario: Par le prénom et le nom
- **WHEN** Bob Gagnon a un compte et Alice cherche «  bob gagnon  »
- **THEN** le compte de Bob figure dans les résultats

#### Scenario: Accents du compte ignorés
- **WHEN** Fréd Côté a un compte et Alice cherche « fred cote »
- **THEN** le compte de Fréd figure dans les résultats

#### Scenario: Accents du texte ignorés
- **WHEN** Fred Cote a un compte et Alice cherche « FRÉD CÔTÉ »
- **THEN** le compte de Fred figure dans les résultats

#### Scenario: Tiret et espace équivalents
- **WHEN** Jean-Pierre Roy a un compte et Alice cherche « jean pierre »
- **THEN** le compte de Jean-Pierre figure dans les résultats

#### Scenario: Espaces multiples
- **WHEN** Bob Gagnon a un compte et Alice cherche « bob    gagnon »
- **THEN** le compte de Bob figure dans les résultats

#### Scenario: Faute de frappe
- **WHEN** Bob Gagnon a un compte et Alice cherche « gagnion »
- **THEN** le compte de Bob figure dans les résultats

#### Scenario: Nom avant prénom
- **WHEN** Bob Gagnon a un compte et Alice cherche « gagnon bob »
- **THEN** le compte de Bob figure dans les résultats

#### Scenario: Pas de ressemblance sous 4 caractères
- **WHEN** Bob Gagnon a un compte, aucun compte ne contient « gax » et Alice cherche « gax »
- **THEN** aucun compte ne figure dans les résultats

#### Scenario: Courriel non cherché
- **WHEN** seul le courriel de Bob contient « courrielbob » et Alice cherche « courrielbob »
- **THEN** le compte de Bob ne figure pas dans les résultats

#### Scenario: Soi-même exclu
- **WHEN** Alice Tremblay cherche « tremblay »
- **THEN** son propre compte ne figure pas dans les résultats

#### Scenario: Caractère joker cherché tel quel
- **WHEN** aucun prénom ni nom ne contient « 50% » et Alice cherche « 50% »
- **THEN** aucun compte ne figure dans les résultats

#### Scenario: Joker pleine chasse cherché tel quel
- **WHEN** aucun prénom ni nom ne contient « %%% » et Alice cherche « ％％％ »
- **THEN** aucun compte ne figure dans les résultats

#### Scenario: Joker présent dans un nom
- **WHEN** le nom de Bob est « Gagnon%%% », aucun autre compte ne contient « %%% », et Alice cherche « %%% »
- **THEN** seul le compte de Bob figure dans les résultats

#### Scenario: Ordre des résultats
- **WHEN** Carole, bob, Élise et Albert ont le nom « Leclerc » et Alice cherche « leclerc »
- **THEN** ils sont listés dans l'ordre Albert, bob, Carole, Élise

#### Scenario: Homonymes
- **WHEN** deux comptes s'appellent Bob Gagnon et Alice cherche « gagnon »
- **THEN** le plus ancien des deux comptes est listé en premier

#### Scenario: Contenu avant ressemblance
- **WHEN** Albert Gagnon et Zoé Gagné ont un compte et Alice cherche « gagne »
- **THEN** Zoé Gagné est listée avant Albert Gagnon

### Requirement: Informations affichées
Chaque résultat SHALL afficher le prénom et le nom du compte, et MUST NOT
afficher son courriel, son adresse ni son téléphone.

#### Scenario: Coordonnées cachées
- **WHEN** Bob a un courriel, une adresse et un téléphone et Alice le trouve par une recherche
- **THEN** la page de résultats affiche « Bob Gagnon »
- **AND** elle n'affiche ni son courriel, ni son adresse, ni son téléphone
