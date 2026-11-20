## MODIFIED Requirements

### Requirement: Correspondance des utilisateurs
La recherche d'utilisateurs SHALL lister les autres comptes dont le nom d'utilisateur, ou le
prénom suivi du nom, contient le texte ou, dès 4 caractères, lui ressemble malgré une faute
légère, sans égard à la casse, aux accents ni aux espaces autour ; un tiret vaut une espace,
plusieurs espaces une seule ; `%`, `_` et `\` sont cherchés tels quels. Tri : ceux qui
contiennent le texte, puis ressemblance décroissante, puis nom d'utilisateur sans égard à la
casse. Jamais son propre compte.

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
- **WHEN** aucun nom d'utilisateur, prénom ni nom ne contient « 50% » et Alice cherche « 50% »
- **THEN** aucun compte ne figure dans les résultats

#### Scenario: Joker pleine chasse cherché tel quel
- **WHEN** aucun nom d'utilisateur, prénom ni nom ne contient « %%% » et Alice cherche « ％％％ »
- **THEN** aucun compte ne figure dans les résultats

#### Scenario: Joker présent dans un nom
- **WHEN** le nom d'utilisateur de Bob est « bob%%% », aucun autre compte ne contient « %%% », et Alice cherche « %%% »
- **THEN** seul le compte de Bob figure dans les résultats

#### Scenario: Ordre des résultats
- **WHEN** les comptes « carole », « Bob » et « albert » ont le nom « Leclerc » et Alice cherche « leclerc »
- **THEN** ils sont listés dans l'ordre « albert », « Bob », « carole »

#### Scenario: Contenu avant ressemblance
- **WHEN** « albert » s'appelle Albert Gagnon, « zoe » s'appelle Zoé Gagné et Alice cherche « gagne »
- **THEN** « zoe » est listée avant « albert »

### Requirement: Recherche trop courte ou sans résultat
Un texte cherché qui compte moins de 3 caractères une fois normalisé (sans accents, un tiret
valant une espace, espaces consécutives réduites à une, espaces des bords retirées) SHALL
afficher « Saisissez au moins 3 caractères » sans chercher ni lister de compte ; le champ de
recherche l'indique aussi avant l'envoi. Une recherche sans résultat SHALL afficher « Aucun
utilisateur ne correspond à « texte » ». Un type de recherche inconnu SHALL afficher « Ce type
de recherche n'est pas disponible ».

#### Scenario: Texte trop court
- **WHEN** Bob Gagnon a un compte et Alice cherche «  bo  »
- **THEN** la page affiche « Saisissez au moins 3 caractères » et aucun compte

#### Scenario: Trois caractères
- **WHEN** Bob Gagnon a un compte et Alice cherche « bob »
- **THEN** le compte de Bob figure dans les résultats

#### Scenario: Texte vide
- **WHEN** Alice lance une recherche avec un texte fait d'espaces
- **THEN** la page affiche « Saisissez au moins 3 caractères » et aucun compte

#### Scenario: Tirets seuls
- **WHEN** Bob Gagnon a un compte et Alice cherche « --- »
- **THEN** la page affiche « Saisissez au moins 3 caractères » et aucun compte

#### Scenario: Tirets typographiques seuls
- **WHEN** Bob Gagnon a un compte et Alice cherche « ––– »
- **THEN** la page affiche « Saisissez au moins 3 caractères » et aucun compte

#### Scenario: Accents sans lettre
- **WHEN** Bob Gagnon a un compte et Alice cherche « e » suivi de trois accents aigus combinants
- **THEN** la page affiche « Saisissez au moins 3 caractères » et aucun compte

#### Scenario: Aucun résultat
- **WHEN** aucun compte ne correspond à « zzz » et Alice cherche « zzz »
- **THEN** la page affiche « Aucun utilisateur ne correspond à « zzz » »

#### Scenario: Recherche d'outils
- **WHEN** Alice demande la page de résultats avec le type « Outil » et le texte « perceuse »
- **THEN** elle arrive sur la page « Trouver un outil » et aucun compte n'est listé

#### Scenario: Tirets seuls en type « Outil »
- **WHEN** Alice choisit « Outil » et cherche « --- »
- **THEN** la page affiche « Saisissez au moins 3 caractères » et elle n'est pas menée à « Trouver un outil »

#### Scenario: Type inconnu
- **WHEN** Alice demande la page de résultats avec le type « lieu »
- **THEN** la page affiche « Ce type de recherche n'est pas disponible » et aucun compte
