# Questions — déconnecter tous mes appareils

Issue traitée : #61 « Déconnecter tous mes appareils », livrée en lot (`/traiter-issue lots`, ADR 0025).
Entrées : l'issue et son dernier commentaire de tri (`understood`), qui tranche les questions `utilisateur`.

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 1 | Rôle du courriel ? | Avis « tous vos appareils ont été déconnectés » à l'adresse du compte, sans lien ni jeton ; un échec d'envoi ne bloque pas l'action | Réponse de l'utilisateur sur #61 | utilisateur |
| 2 | Page de confirmation ? | Oui : GET qui affiche, POST qui agit | Réponse de l'utilisateur sur #61 | utilisateur |
| 3 | Règle des gabarits ? | Toute action irréversible ou dangereuse passe par une page de confirmation, cette action en exemple | Réponse de l'utilisateur sur #61 | utilisateur |
| 4 | Redemander le mot de passe ? | Non | Réponse de l'utilisateur sur #61 | utilisateur |
| 5 | Changement ou réinitialisation du mot de passe ? | Hors périmètre ; la spec note qu'une future fonction de mot de passe devra aussi faire tourner la version | Réponse de l'utilisateur sur #61 | utilisateur |
| 6 | Où placer l'action ? | Une carte « Déconnecter tous mes appareils » sur « Mon profil », avant « Supprimer mon compte » | `.claude/rules/templates.md` ; tri de #61 | convention |
| 7 | Couleur des boutons ? | Rouge, celui qui ouvre la confirmation et celui qui la confirme ; « Annuler » gris | ADR 0022 ; tri de #61 | convention |
| 8 | Rotation ? | `UPDATE` atomique `session_version + 1` du compte connecté non supprimé, en POST, `@login_required`, CSRF ; aucune ligne touchée : déconnexion et retour à `/login` | `app/profile.py` (`save`) ; ADR 0012 | convention |
| 9 | Appareil courant ? | `end_session()`, puis `/logged-out?reason=all-devices`, « Tous vos appareils ont été déconnectés » | `app/auth.py` (`end_session`, `logged_out`) ; spec authentification | convention |
| 10 | Schéma ? | Aucun : `session_version` existe | ADR 0028 | dépôt |
| 11 | Retour arrière ? | Couvert : l'image précédente lit déjà `<id>:<version>` | ADR 0017, ADR 0028 | dépôt |
| 12 | Autre onglet ou resoumission après la rotation ? | Erreur CSRF « Rechargez la page », comme après une expiration | Tri de #56 | convention |
| 13 | Compte non confirmé ? | Action permise ; aucun JavaScript | ADR 0001 ; tri de #61 | convention |
| 14 | Avis à un compte au courriel non confirmé ? | Non envoyé : une adresse non confirmée peut être celle d'un tiers (motif de la décision 8 du tri de #65) | Tri de #65, décision 8 | convention (ajoutée) |
| 15 | Contenu de l'avis ? | Texte brut, en français, prénom, aucun lien, aucune adresse ni téléphone | ADR 0027 ; `app/email_confirmation.py` | convention |
