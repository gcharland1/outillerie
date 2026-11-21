# Tasks

## 1. Schéma

- [x] 1.1 `deleted_at` (`timestamptz` nullable) et `email` nullable dans `models/user.py` ; révision Alembic chaînée après `43880597035b` (`retrait-du-nom-d-utilisateur` n'a pas de révision), nom de fichier ASCII, `downgrade` qui remplit `supprime-<id>@invalid` avant de remettre `NOT NULL` ; vérifier `flask db upgrade`, `flask db downgrade -1` (avec un compte au courriel NULL) puis `upgrade` sur la base de test ; `flask db check` vide ; `docs/schema.md` régénéré ; `test_schema.py` adapté s'il le faut

## 2. Page « Mon profil »

- [x] 2.1 Blueprint `profile` (`app/profile.py`) enregistrée par `create_app`, `GET /profile` et gabarit `profile/show.html` ; entrée « Mon profil » en lien, première du menu du compte (`base.html`) ; `test_navigation.py:47-52` adapté (« Préférences » seule grisée) ; tests de « Profil réservé à un utilisateur connecté », « Accès depuis le menu du compte » et « Informations du profil »
- [x] 2.2 `POST /profile` : `strip`, vide = `NULL`, longueurs des colonnes, caractères du téléphone, formulaire réaffiché avec la saisie et chaque erreur, message de succès ; tests de « Modification de l'adresse et du téléphone » et « Validation de l'adresse et du téléphone » (250/251, 20/21, caractère refusé, champs nom et courriel envoyés ignorés, `<script>` affiché échappé), et refus sans jeton CSRF
- [x] 2.3 Retirer « plus tard » devant « Mon profil » dans `.claude/rules/templates.md`, si la ligne du menu du compte le dit encore après `retrait-du-nom-d-utilisateur`

## 3. Section et confirmation de la suppression

- [x] 3.1 Section « Supprimer mon compte » : message, bouton `button error` vers la confirmation, ou bouton désactivé, message de blocage, liste des prêts `OUT` (outil, autre partie rendue par la macro `user_name`, statut, « En retard » compris) et lien vers « Mes prêts » ; ajouter « Supprimer mon compte » à la liste fermée des libellés admis en `error` dans le test qui remplace `test_no_button_is_red_or_green` (`couleurs-des-boutons-et-liens`, tâche 1.5) ; tests de « Section « Supprimer mon compte » » et « Suppression bloquée par un prêt en cours » (emprunteur, prêteur, remise et retour déclarés, retard, demande et acceptation non bloquantes, `GET /profile/delete` redirigé)
- [x] 3.2 `GET /profile/delete` et `profile/confirm_delete.html` : champs nom complet et mot de passe, « Annuler » gris, « Confirmer la suppression » rouge, annonce par `catalog.cancel_notice` ; ajouter « Confirmer la suppression » à la liste fermée des libellés admis en `error` dans le test qui remplace `test_no_button_is_red_or_green` (`couleurs-des-boutons-et-liens`, tâche 1.5) ; tests de « Page de confirmation de la suppression » (aucune annulation, annonce combinée, rien supprimé à l'ouverture, « Annuler » qui mène à `/profile` sans supprimer le compte)
- [x] 3.3 Vérification au `POST` : nom comparé par `text_search.sort_key`, mot de passe par `check_password_hash`, erreur unique, nom réaffiché et mot de passe vide ; tests de « Vérification avant la suppression » : accents, casse et tiret, mauvais nom, mauvais mot de passe, champs vides, `GET` sans effet, `POST` sans jeton CSRF (400), `POST` forgé avec un prêt `OUT` (rien supprimé, prêt toujours « Prêté »)

## 4. Suppression

- [x] 4.1 Transaction ordonnée du design (compte `FOR UPDATE`, outils et prêts `FOR UPDATE ORDER BY id`, revérification `OUT`, annulations, messages, outils vidés par `photos.remove_photo`, contacts, anonymisation, `deleted_at`) ; tests de « Effet de la suppression » (données effacées, nom gardé, contacts défaits des deux côtés, outils retirés et vidés, annulations des deux côtés, messages, deux suppressions sans erreur)
- [x] 4.2 Fin de session et page de déconnexion : `logout_user`, `session.clear`, redirection vers `/logged-out?reason=account-deleted`, motif `account-deleted` dans `auth.logged_out` et `logged_out.html` ; tests de « Fin de session après la suppression » et de « Page de déconnexion » (nouveau motif, motifs existants inchangés)
- [x] 4.3 Test de concurrence à deux connexions : une transaction passe un prêt accepté à « Remise à confirmer » sans valider, la suppression attend son verrou, puis la validation fait refuser la suppression ; vérifier que le test échoue si le verrou des prêts est retiré
- [x] 4.4 `POST /profile` par `UPDATE … WHERE id = :me AND deleted_at IS NULL` ; test à deux connexions : la suppression tient le verrou du compte, l'envoi du profil attend, puis ne réécrit ni l'adresse ni le téléphone (toujours NULL) et mène à `/login` ; vérifier que le test échoue sans la condition `deleted_at IS NULL`

## 5. Compte supprimé ailleurs dans le site

- [x] 5.1 `load_user` renvoie `None` pour un compte supprimé ; tests de « Sessions d'un compte supprimé » (deux clients connectés, cookie réutilisé) et du scénario « Compte supprimé » de « Connexion » (même réponse qu'un courriel inconnu)
- [x] 5.2 Courriel libre : test du scénario « Courriel d'un compte supprimé » de « Courriel unique »
- [x] 5.3 Recherche : `deleted_at IS NULL` avant le plafond ; tests de « Comptes supprimés exclus »
- [x] 5.4 Contacts : 404 pour la page et la demande vers un compte supprimé ; verrous `FOR SHARE` des comptes, triés par id, dans `send_request` et `accept` ; `accept` relit la demande après les verrous des comptes et, si elle n'existe plus, répond comme « Demande qui n'existe plus » (pas de 404) ; tests des scénarios « Demande à un compte supprimé » et « Ancien contact supprimé », et d'une acceptation dont le demandeur a été supprimé entre-temps (redirection avec « Cette demande n'est plus en attente », aucune relation créée)
- [x] 5.5 `loans.create` : verrous `FOR SHARE` de l'emprunteur et du propriétaire avant celui de l'outil ; test d'une demande d'emprunt envoyée, depuis une page restée ouverte, vers un outil d'un compte supprimé (404, aucune demande enregistrée) ; suite `test_loans.py` toujours verte
- [x] 5.6 Macro `user_name` : branche « compte supprimé » en tête (texte grisé par une classe de `site.css`, « (supprimé) », sans lien, échappé) ; test du scénario « Compte supprimé » de « Nom d'un utilisateur » dans « Mes prêts »
- [x] 5.7 Envoi en double de `POST /profile/delete` : `deleted_at` lu sous le verrou du compte, déjà posé → déconnexion sans réanonymiser ; écritures d'outils (`tools.new`, `tools.edit`, `tools.retire`, `tools.restore`) derrière `lock_live_accounts` du compte, supprimé → déconnexion et `/login` ; tests à deux connexions, vérifiés en échec sans ces gardes

## 6. Fin

- [x] 6.1 `openspec validate modification-du-profil --strict --no-interactive` passe
- [x] 6.2 `/verifier` rend « terminé »

## Workflow follow-up

- Archiver après `couleurs-des-boutons-et-liens`, qui crée la capacité `interface` modifiée ici.
- Passer l'ADR 0023 à `accepted` sur accord de l'utilisateur.
