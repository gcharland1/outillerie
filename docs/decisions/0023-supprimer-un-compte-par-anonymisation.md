---
status: accepted
date: 2026-11-20
decision-makers: Gabriel Charland
---

# Supprimer un compte par anonymisation

## Contexte et problème

L'issue #46 permet à un utilisateur de supprimer son compte : ses données personnelles disparaissent,
mais l'historique des prêts de ses anciens partenaires doit rester lisible, avec son nom suivi de
« (supprimé) ». Aucune clé étrangère vers `user` n'a d'`ondelete`, et un outil prêté ne peut pas être
supprimé (spec `prets`, « Historique des prêts conservé »). La session vit dans un cookie signé, sans
état serveur (ADR 0006). Changement OpenSpec : `openspec/changes/archive/2026-11-20-modification-du-profil/`
(`questions.md` #4 à #8, #15, #17).

## Options considérées

* `DELETE` de la ligne `user` en cascade : outils, photos, prêts, demandes et relations supprimés avec elle
* Ligne `user` gardée et anonymisée, marquée par `deleted_at`
* Ligne `user` marquée supprimée, sans rien effacer

## Décision

Option retenue : « ligne `user` gardée et anonymisée, marquée par `deleted_at` », parce qu'elle efface
ce que l'issue demande d'effacer tout en gardant les références dont l'historique des prêts des autres
a besoin. La cascade supprimerait des prêts qui appartiennent aussi à l'autre partie ; le marquage seul
garderait courriel, adresse et téléphone, contrairement à l'issue.

Règles :

* `user.deleted_at` : `timestamptz` nullable, posé à la suppression. Pas de colonne `is_active` :
  elle masquerait `UserMixin.is_active` de Flask-Login.
* `user.email` devient nullable et passe à NULL ; un nouveau compte peut reprendre le courriel.
  L'index `uq_user_email_lower` admet plusieurs NULL. Le `downgrade` remplit chaque NULL avec
  `supprime-<id>@invalid` avant de remettre `NOT NULL` (ADR 0007).
* Effacé : courriel, adresse, téléphone ; mot de passe remplacé par une valeur qu'aucune saisie ne
  vérifie ; demandes et relations de contact, des deux côtés ; photo (par le module photo, ADR 0008),
  description (`''`) et notes privées des outils ; `loan.message` des prêts où le compte emprunte.
* Gardé : prénom et nom, nom et état des outils, retirés de la circulation ; prêts où le compte est
  emprunteur ou prêteur, avec leurs dates, leur statut et le message écrit par l'autre partie.
* Un prêt `OUT` (remise déclarée, prêté, retour déclaré) bloque la suppression ; les demandes en
  attente et les prêts acceptés à venir sont annulés, comme au retrait d'un contact ou d'un outil.
* La suppression verrouille la ligne `user` (`FOR UPDATE`), puis ses outils et ses prêts, et ne
  vérifie l'absence de prêt `OUT` qu'une fois les verrous pris ; une écriture qui lie un compte à un
  autre (demande de contact, acceptation, demande d'emprunt) verrouille d'abord les lignes `user`
  concernées et refuse un compte supprimé.
* `load_user` renvoie `None` pour un compte supprimé : toute session ouverte ailleurs est traitée en
  visiteur dès sa requête suivante. Complète l'ADR 0006 sans le remplacer : le cookie et son
  expiration ne changent pas ; la révocation repose sur la lecture du compte que `load_user` fait
  déjà à chaque requête, pas sur un état de session côté serveur.
* Un compte supprimé est exclu de la recherche d'utilisateurs ; une demande de contact vers lui et
  sa page répondent 404.

### Conséquences

* Bon, parce que l'historique des prêts de l'autre partie reste entier, sans clé étrangère cassée
  ni `ondelete` à ajouter.
* Bon, parce que les sessions du compte sont coupées sans table de sessions ni changement de cookie.
* Bon, parce que la révision est un relâchement (colonne nullable ajoutée, `NOT NULL` retiré), sans
  passe *contract* à suivre.
* Mauvais, parce qu'après un retour à l'image précédente sans `downgrade` (ADR 0017), qui tourne sur
  le nouveau schéma, cette image ignore `deleted_at` : jusqu'au redéploiement, son `load_user`
  rendrait de nouveau valides les sessions d'un compte supprimé, et les comptes supprimés
  réapparaîtraient dans la recherche.
* Mauvais, parce que chaque requête sur des comptes doit penser à exclure `deleted_at` ; un oubli
  rend un compte supprimé visible ou joignable.
* Mauvais, parce que les données effacées restent dans les sauvegardes `pg_dump` prises avant chaque
  déploiement (10 gardées, ADR 0017) jusqu'à leur rotation ; cette limite n'est pas annoncée à
  l'utilisateur.
* Mauvais, parce que le prénom et le nom restent en base, visibles des anciens partenaires de prêt.
* Mauvais, parce que les écritures qui lient deux comptes prennent un verrou de plus.
