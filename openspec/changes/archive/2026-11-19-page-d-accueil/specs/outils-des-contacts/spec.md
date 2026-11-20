# Spec Delta

## MODIFIED Requirements

### Requirement: Carte d'un outil
Chaque outil SHALL être présenté par une carte qui affiche son nom, sa photo, le prénom et le nom
de son propriétaire, menant à sa page, sa description, son état et son statut de prêt, ainsi qu'un
bouton « Emprunter » : actif s'il est « Disponible », grisé sinon, ou « Demande envoyée » grisé sur
l'outil que l'utilisateur a lui-même demandé. Un outil déjà emprunté affiche « Dernier emprunt le
<date> », la date de début de son dernier prêt remis (« Remise à confirmer », « Prêté », « Retour à
confirmer » ou « Complété ») ; un outil jamais emprunté n'affiche aucune mention. La carte MUST NOT
nommer l'emprunteur ni le nombre de prêts. Les cartes sont disposées sur trois colonnes à partir
d'un écran moyen, sur une seule sur un petit écran. Les notes privées du propriétaire MUST NOT être
affichées.

#### Scenario: Contenu de la carte
- **WHEN** Bob, contact d'Alice, a une perceuse fonctionnelle avec photo et description
- **THEN** la carte de la perceuse affiche son nom, sa photo, « Bob Gagnon », sa description, « Fonctionnel » et son statut
- **AND** « Bob Gagnon » mène à la page de Bob
- **AND** elle affiche un bouton « Emprunter » actif, qui mène à la page de confirmation de la demande

#### Scenario: Outil indisponible
- **WHEN** la perceuse de Bob est prêtée ou en attente de prêt pour Carole
- **THEN** la carte de la perceuse affiche, pour Alice, un bouton « Emprunter » grisé

#### Scenario: Sa propre demande
- **WHEN** Alice a demandé la perceuse de Bob et la demande attend sa réponse
- **THEN** la carte de la perceuse affiche, pour Alice, « Demande envoyée » grisé
- **AND** elle affiche, pour Carole, « En attente de prêt » et « Emprunter » grisé

#### Scenario: Notes privées cachées
- **WHEN** la perceuse de Bob a les notes privées « code du cadenas 1234 »
- **THEN** aucune page d'Alice n'affiche « code du cadenas 1234 »

#### Scenario: Outil sans photo
- **WHEN** la perceuse de Bob n'a pas de photo
- **THEN** sa carte affiche un espace réservé à la place de la photo, à la même taille

#### Scenario: Dernier emprunt
- **WHEN** Carole a emprunté la perceuse de Bob du 3 au 5 novembre 2026 puis du 12 au 14 novembre 2026, tous deux « Complété »
- **THEN** la carte de la perceuse affiche, pour Alice, « Dernier emprunt le 12 novembre 2026 », sans nommer Carole

#### Scenario: Remise à confirmer comptée
- **WHEN** Bob a déclaré avoir remis sa perceuse à Carole pour un prêt qui commence le 20 novembre 2026
- **THEN** la carte de la perceuse affiche « Dernier emprunt le 20 novembre 2026 »

#### Scenario: Jamais emprunté
- **WHEN** la perceuse de Bob n'a eu que des demandes refusées, annulées ou expirées, et un prêt accepté jamais remis
- **THEN** sa carte n'affiche aucune mention d'emprunt

### Requirement: Ordre des outils
« Trouver un outil » et la page d'un contact SHALL offrir un menu « Trier par », appliqué avec
« Filtrer », sans JavaScript, et conservé dans l'adresse avec les filtres :

- « Pertinence » (par défaut) : avec un texte cherché, ceux dont le nom contient le texte, selon
  les règles du filtre par texte, puis par ressemblance décroissante du nom, puis de la
  description, puis par nom sans égard à la casse ; sans texte, par nom sans égard à la casse ;
- « Ajout : plus récents » et « Ajout : plus anciens » : par date d'ajout de l'outil ;
- « Dernier emprunt : plus récents » et « Dernier emprunt : plus anciens » : par date du dernier
  emprunt affichée sur la carte ; les outils jamais empruntés viennent à la fin du premier, en tête
  du second.

Un tri autre que « Pertinence » remplace la ressemblance : le texte cherché ne fait plus que
filtrer. Deux outils à égalité gardent toujours le même ordre. Une valeur de tri inconnue donne
« Pertinence ».

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
- **AND** le menu « Trier par » affiche « Pertinence »

#### Scenario: Ajout plus récents
- **WHEN** Bob a ajouté une scie le 1er novembre, une perceuse le 10 et une ponceuse le 5
- **AND** Alice trie par « Ajout : plus récents »
- **THEN** ils sont listés dans l'ordre perceuse, ponceuse, scie

#### Scenario: Ajout plus anciens
- **WHEN** Alice trie les mêmes outils par « Ajout : plus anciens »
- **THEN** ils sont listés dans l'ordre scie, ponceuse, perceuse

#### Scenario: Dernier emprunt
- **WHEN** la scie de Bob a été empruntée le 3 novembre, la perceuse le 10 et la ponceuse jamais
- **THEN** « Dernier emprunt : plus récents » liste perceuse, scie, ponceuse
- **AND** « Dernier emprunt : plus anciens » liste ponceuse, scie, perceuse

#### Scenario: Tri avec un texte
- **WHEN** Bob a ajouté un « Rabot électrique » il y a un mois et, hier, un « Établi » décrit « idéal sous le rabot »
- **AND** Alice cherche « rabot » et trie par « Ajout : plus récents »
- **THEN** l'établi est listé avant le rabot électrique

#### Scenario: Tri sur la page d'un contact
- **WHEN** Alice trie les outils de la page de Bob par « Ajout : plus récents »
- **THEN** les outils de Bob sont listés du plus récent au plus ancien

#### Scenario: Tri inconnu
- **WHEN** l'adresse de « Trouver un outil » porte un tri « au-hasard »
- **THEN** la page répond 200, liste les outils par « Pertinence » et le menu affiche « Pertinence »
