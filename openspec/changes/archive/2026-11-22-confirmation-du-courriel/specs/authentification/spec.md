## MODIFIED Requirements

### Requirement: Création de compte
Le système SHALL créer un compte non confirmé à partir d'un courriel, d'un mot de passe, d'un prénom
et d'un nom soumis sur la page `/register`, lui envoyer un courriel de confirmation (capacité
`confirmation-du-courriel`) une fois le compte créé, puis rediriger vers la page de connexion avec
« Compte créé. Un courriel de confirmation a été envoyé à <courriel>. » comme message de succès. Le
courriel est enregistré sans les espaces autour. Le formulaire MUST NOT demander de nom
d'utilisateur.

#### Scenario: Inscription réussie
- **WHEN** un visiteur soumet le formulaire d'inscription avec un courriel libre et tous les champs remplis
- **THEN** un compte non confirmé est créé avec ces informations
- **AND** un courriel de confirmation est envoyé à ce courriel
- **AND** le visiteur est redirigé vers `/login` avec « Compte créé. Un courriel de confirmation a été envoyé à <courriel>. »

#### Scenario: Échec d'envoi à l'inscription
- **WHEN** l'envoi du courriel de confirmation échoue à l'inscription
- **THEN** le compte est quand même créé et le visiteur est redirigé vers `/login` avec le même message

#### Scenario: Nom d'utilisateur déjà pris
- **WHEN** un visiteur ouvre la page d'inscription
- **THEN** le formulaire ne demande aucun nom d'utilisateur, et aucun nom n'est donc jamais « déjà pris »

#### Scenario: Espaces retirés
- **WHEN** un visiteur s'inscrit avec le courriel « ␠bob@example.com␠ »
- **THEN** le compte est enregistré avec le courriel `bob@example.com`
