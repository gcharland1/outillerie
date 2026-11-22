## MODIFIED Requirements

### Requirement: Carte d'un outil
Chaque outil SHALL être présenté par une carte qui affiche son nom, sa photo, le prénom et le nom
de son propriétaire, menant à sa page, sa description, son état et son statut de prêt, ainsi qu'un
bouton « Emprunter » : actif s'il est « Disponible » et que l'utilisateur a confirmé son courriel, grisé sinon, ou « Demande envoyée » grisé sur
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

#### Scenario: Compte non confirmé
- **WHEN** Alice n'a pas confirmé son courriel et la perceuse de Bob est « Disponible »
- **THEN** la carte de la perceuse affiche, pour Alice, un bouton « Emprunter » grisé
