# Spec Delta

## MODIFIED Requirements

### Requirement: Demande qui n'existe plus
« Accepter » et « Refuser » SHALL ramener à la page d'où ils ont été envoyés, « Mes contacts » ou
l'accueil ; une origine inconnue ramène à « Mes contacts ». Accepter affiche « Vous êtes maintenant
en contact avec <prénom> <nom> » et refuser « Demande refusée », comme message de succès. Répondre
à une demande qui n'existe plus, parce qu'on y a déjà répondu (retour arrière, second envoi), MUST
laisser tout inchangé :
l'utilisateur revient sur cette page avec le message « Cette demande n'est plus en attente ».

#### Scenario: Refus après acceptation
- **WHEN** Bob a accepté la demande d'Alice
- **AND** Bob soumet le refus de la même demande depuis « Mes contacts »
- **THEN** il est redirigé vers « Mes contacts », qui affiche « Cette demande n'est plus en attente »
- **AND** Alice et Bob restent en contact

#### Scenario: Réponse depuis l'accueil
- **WHEN** Bob accepte la demande d'Alice depuis l'accueil
- **THEN** il revient sur l'accueil et Alice et Bob sont en contact

#### Scenario: Message de succès
- **WHEN** Bob accepte la demande d'Alice depuis « Mes contacts »
- **THEN** la page affiche « Vous êtes maintenant en contact avec Alice Tremblay » comme un message de succès

#### Scenario: Origine inconnue
- **WHEN** Bob refuse la demande d'Alice avec l'origine « https://exemple.com »
- **THEN** il est redirigé vers « Mes contacts »
