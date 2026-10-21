# Tasks

## 1. Décision et base de tests

- [x] 1.1 Écrire l'ADR « Sessions dans le cookie signé de Flask, expiration d'inactivité » via `/adr` (choix, alternative des sessions côté serveur, risque de copie du cookie borné à 30 minutes) ; vérifier qu'il apparaît dans l'index `docs/decisions/README.md`
- [x] 1.2 Déplacer les fixtures `mock_app` et `client` de `tests/test_main.py` vers `tests/conftest.py` et ajouter une fixture qui crée un utilisateur avec mot de passe haché ; vérifier que `uv run pytest` passe toujours

## 2. Inscription et connexion (comportement existant)

- [x] 2.1 Afficher les erreurs d'inscription par `flash` avec le texte « Le nom d'utilisateur est déjà utilisé » ; vérifier par un test pytest qu'un doublon ne crée pas de compte et que la page affiche ce message
- [x] 2.2 Tester l'inscription réussie (compte créé, redirection vers `/login`) et le hachage du mot de passe (valeur stockée différente, vérifiable) ; vérifier que les tests passent
- [x] 2.3 Corriger le message d'échec de connexion en « Le nom d'utilisateur ou le mot de passe est invalide » ; vérifier par des tests pytest la connexion réussie (redirection vers `/`, utilisateur reconnu) et l'échec (nom inconnu, mauvais mot de passe)
- [x] 2.4 Vérifier le mot de passe soumis contre un hachage factice quand le nom d'utilisateur est inconnu ; vérifier par un test pytest (espion sur la fonction de vérification) que les deux échecs passent par la même vérification et rendent une réponse identique

## 3. Session et déconnexion

- [x] 3.1 Configurer la session dans la factory : `PERMANENT_SESSION_LIFETIME` à 30 minutes (remplaçable par la config de test), `SESSION_COOKIE_SAMESITE="Lax"`, et `session.permanent = True` à la connexion ; vérifier par un test que le cookie posé à la connexion porte `HttpOnly` et `SameSite=Lax`
- [x] 3.2 Ajouter la page `GET /logged-out` (nouveau gabarit, message selon `reason`, lien vers `/login`, redirection vers `/` si l'utilisateur est connecté) ; vérifier par des tests pytest les deux messages, que les minutes affichées suivent une durée configurée autre que 30 (ex. 15), qu'un `reason` inconnu affiche le message par défaut, et la redirection d'un utilisateur connecté sans déconnexion
- [x] 3.3 Ajouter la route `POST /logout` (`logout_user`, `session.clear()`, redirection vers `/logged-out`) ; vérifier par des tests pytest la déconnexion d'un utilisateur connecté, celle d'un visiteur sans erreur, et la réponse 405 à `GET /logout` sans fermer la session
- [x] 3.4 Tester l'expiration en contrôlant l'horloge de signature : une requête après plus de 30 minutes d'inactivité est traitée comme un visiteur, et des requêtes toutes les 20 minutes pendant une heure gardent la session ouverte ; vérifier que les tests passent sans attente réelle

## 4. Navigation

- [x] 4.1 Adapter `base.html` : « Connexion » et « Inscription » pour un visiteur ; nom d'utilisateur et bouton « Me déconnecter » (formulaire `POST /logout`) pour un utilisateur connecté ; vérifier par des tests pytest le contenu de la navigation dans les deux cas
- [x] 4.2 Vérifier dans l'app (`uv run main.py`) l'enchaînement inscription → connexion → déconnexion → page `/logged-out`

## 5. Avis d'expiration et cache

- [x] 5.1 Émettre dans `base.html`, pour un utilisateur connecté seulement, `<meta http-equiv="refresh">` vers `/logged-out?reason=inactivity` avec un délai égal à `PERMANENT_SESSION_LIFETIME` plus 5 secondes ; vérifier par des tests pytest la présence de la balise et son délai pour un utilisateur connecté, et son absence pour un visiteur
- [x] 5.2 Ajouter un hook `after_request` qui pose `Cache-Control: no-store` quand l'utilisateur est connecté ; vérifier par des tests pytest l'en-tête pour un utilisateur connecté et son absence pour un visiteur
- [x] 5.3 Vérifier à la main dans le navigateur, avec une durée de session courte : une page laissée ouverte affiche la page d'expiration ; avec un autre onglet actif, l'onglet inactif revient sur `/` en restant connecté ; après une déconnexion, « Précédent » n'affiche aucun contenu connecté

## 6. Vérification

- [x] 6.1 Exécuter `/verifier` et obtenir « terminé » (lint, format, tests sur Postgres, `flask db check`, `openspec validate`)

## Workflow follow-up

- Relecture par l'agent `relecteur` avant la mise à jour de la PR #13.
- Archiver le changement avec `/opsx:archive` une fois la PR #13 mergée.
