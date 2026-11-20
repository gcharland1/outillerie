# Proposal

## Why

L'entrée « Mon profil » du menu du compte est grisée : un utilisateur ne peut ni corriger son adresse
ou son téléphone, ni quitter le site. L'issue #46 ajoute la page « Mon profil » et la suppression du
compte, qui efface ses données personnelles sans casser l'historique des prêts de ses anciens
partenaires.

Closes #46. Les décisions et leur source sont dans [questions.md](questions.md). Décision
d'architecture : ADR 0023 (`proposed`), « Supprimer un compte par anonymisation ». Les couleurs des
boutons suivent l'ADR 0022 (`proposed`, changement `couleurs-des-boutons-et-liens`, livré avant
celui-ci dans la même branche).

## What Changes

- Page « Mon profil » (`/profile`), première entrée du menu du compte : prénom, nom et courriel
  affichés sans être modifiables ; adresse et téléphone modifiables, vides pour les retirer, bornés
  à la longueur de leur colonne, le téléphone limité aux chiffres, espaces et `+ - ( ) .`.
- Section « Supprimer mon compte » au bas de la page : message d'irréversibilité et bouton rouge
  vers une page de confirmation ; tant qu'un prêt est en cours (remise déclarée, prêté, retour
  déclaré, retards compris), le bouton est désactivé et la section liste ces prêts avec un lien vers
  « Mes prêts ».
- Page de confirmation : nom complet et mot de passe actuel exigés, « Annuler » gris et « Confirmer
  la suppression » rouge, annonce des demandes d'emprunt et prêts acceptés qui seront annulés. Le
  serveur revérifie tout à l'envoi.
- Suppression : compte anonymisé et marqué supprimé (ADR 0023), demandes et relations de contact
  supprimées, outils retirés et vidés de leur photo, description et notes, demandes et prêts à venir
  annulés ; déconnexion vers `/logged-out?reason=account-deleted`, « Votre compte a été supprimé ».
- Un compte supprimé ne se connecte plus, ses sessions ouvertes sont coupées, son courriel redevient
  libre ; il est exclu de la recherche, une demande de contact vers lui et sa page répondent 404.
- Son nom s'affiche grisé suivi de « (supprimé) », sans lien, par la macro de nom de #49.
- Schéma : `user.deleted_at` ajoutée, `user.email` rendu nullable, en une révision.

Hors périmètre : purge des sauvegardes `pg_dump` (ADR 0017), page publique d'un non-contact,
limitation des essais de mot de passe, modification du nom, du courriel ou du mot de passe.

## Capabilities

### New Capabilities
- `profil`: page « Mon profil », modification de l'adresse et du téléphone, suppression du compte et
  affichage d'un compte supprimé.

### Modified Capabilities
- `authentification`: « Courriel unique », « Connexion », « Page de déconnexion » ; sessions d'un
  compte supprimé (ajout).
- `recherche`: comptes supprimés exclus (ajout).
- `contacts`: « Envoi d'une demande de contact », « Page d'un contact ».
- `interface`: « Nom d'un utilisateur », cas du compte supprimé. La capacité est créée par
  `couleurs-des-boutons-et-liens`, qui doit être archivé avant celui-ci.

## Impact

`models/user.py`, une révision Alembic chaînée après celle de `retrait-du-nom-d-utilisateur`,
`docs/schema.md` (ADR 0009) ; nouveau module `app/profile.py` (Blueprint `profile`, ADR 0011) et
gabarits `profile/*` ; `app/__init__.py` (`load_user`), `app/auth.py` (page de déconnexion),
`app/search.py`, `app/contacts.py`, `app/loans.py` (verrous), `app/photos.py` ; `base.html` (menu),
`logged_out.html`, macro de nom de #49 ; `.claude/rules/templates.md` (« plus tard « Mon profil » ») ;
tests, dont `test_navigation.py`.
