# Proposal

## Why

La page d'accueil n'est qu'une preuve de concept (« Bienvenue sur l'outillerie »). Un utilisateur
connecté doit ouvrir « Mes prêts », « Mes contacts » et « Trouver un outil » l'un après l'autre
pour savoir ce qui l'attend. L'issue #3 fait de `/` un tableau de bord qui regroupe les actions à
prendre et les nouveautés, avec un lien vers chaque page complète. Le lien « Voir plus » des
nouveaux outils exige le tri de « Trouver un outil » demandé par l'issue #37, livré ici.

Les décisions et leur source sont dans [questions.md](questions.md).

## What Changes

- **BREAKING** `/` est réservé à l'utilisateur connecté ; un visiteur est redirigé vers `/login`,
  sans message. Le healthcheck de Compose vise `/login`.
- Le tableau de bord a trois sections, dans cet ordre :
  - « Gestion des prêts » : demandes reçues, puis mes emprunts, puis mes prêts en cours, chacun
    par catégorie (en retard d'abord) et par date de fin ; au plus 5 lignes par groupe, puis « Voir
    tous mes prêts ». Les prêts finis, refusés, annulés ou expirés n'y sont pas.
  - « Gestion des contacts » : demandes de contact reçues, et les contacts noués depuis 30 jours
    (« Vous êtes maintenant en contact avec … »), vus des deux côtés. Un refus n'est jamais affiché.
  - « Nouveaux outils » : au plus 6 outils de mes contacts ajoutés depuis 30 jours, du plus récent
    au plus ancien, avec les cartes de « Trouver un outil » ; « Voir plus » au-delà.
- Les boutons d'action (Accepter, Refuser, J'ai remis l'outil, Confirmer la réception, Pas reçu,
  Emprunter…) agissent sur place et ramènent à l'accueil, message compris. « Annuler le prêt » reste
  un lien vers sa page de confirmation.
- Chaque action réussie sur une demande, un prêt ou une demande de contact affiche un message de
  succès, sur l'accueil comme sur « Mes prêts » et « Mes contacts ».
- Un prêt en retard est mis en évidence, sur l'accueil et sur « Mes prêts ».
- « Trouver un outil » et la page d'un contact reçoivent un menu de tri : « Pertinence » (ordre
  actuel), date d'ajout et dernier emprunt, chacun du plus récent au plus ancien ou l'inverse
  (issue #37). Un tri par date remplace la ressemblance ; le texte cherché ne fait plus que filtrer.
- Chaque carte d'outil déjà emprunté affiche « Dernier emprunt le <date> » (date de début du
  dernier prêt remis) ; aucune mention pour un outil jamais emprunté.

## Capabilities

### New Capabilities

Aucune.

### Modified Capabilities

- `accueil` : « Page d'accueil » (page publique) retirée, remplacée par « Tableau de bord de
  l'utilisateur connecté » ; ajout des trois sections, des sections vides et du retour à l'accueil
  après une action.
- `authentification` : « Pages connectées non mises en cache » (le retour arrière après
  déconnexion mène à la page de connexion).
- `deploiement` : « Healthcheck de l'app » (page de connexion).
- `outils-des-contacts` : « Carte d'un outil » (dernier emprunt) ; « Ordre des outils » (menu de tri).
- `demandes-d-emprunt` : « Envoi d'une demande » (l'accueil comme liste d'origine) ; « Réponse du
  propriétaire » et « Retrait d'une demande par l'emprunteur » (retour à la page d'origine) ;
  « Ordre et couleurs de « Mes prêts » » (retard mis en évidence) ; « Messages de succès » (chaque
  action réussie).
- `suivi-des-prets` : « Actions réservées aux parties » (retour à la page d'origine).
- `contacts` : « Demande qui n'existe plus » (retour à la page d'origine, message de succès).

## Impact

- Code : vue `index` de `app/__init__.py` (reste dans `create_app()`, ADR 0011) ; requêtes du
  tableau de bord dans `app/loans.py`, `app/contacts.py`, `app/catalog.py` ; tri et dernier emprunt
  dans `app/catalog.py` ; origine `home` dans `app/loans.py` et `app/contacts.py`.
- Gabarits : `index.html` réécrit ; carte extraite de `tools/_cards.html` ; menu de tri ;
  `loans/mine.html`, `loans/confirm.html`, `contacts/mine.html` (origine) ; `site.css` (retard,
  sections).
- Déploiement : `compose.yaml` (healthcheck), `README.md`.
- Tests : vérifications de visiteur déplacées de `/` vers `/login` ; `is_logged_in` et
  « Rebonjour » remplacés ; nouveau `tests/test_home.py`.
- Schéma : aucun changement ; aucune dépendance.
- ADR respectés : 0001 (rendu serveur sans JavaScript), 0006 et 0012 (session, CSRF), 0007 (pas
  de colonne), 0011 (`index` dans la fabrique), 0013 (relation de contact sans demandeur, refus
  discret), 0018 (règles communes des champs de recherche, pertinence). Aucun nouvel ADR : aucune dépendance, aucun schéma ni
  aucune structure ne change.

## Hors périmètre

- Informer l'emprunteur d'une demande de prêt refusée (les refus restent dans « Mes prêts »).
- Savoir qui a demandé un contact, et tout état « vu ».
- Une date de remise en circulation d'un outil (seule la date d'ajout compte).
- Le paramètre `next` de la connexion.
- La tâche 7.1 de `gestion-des-prets` (QA manuelle), à faire avant la PR de ce changement.
