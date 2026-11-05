# Validations manuelles — issue #29, demande d'emprunt

Tâches 7.1 et 8.4 du changement `demande-d-emprunt`. Chaque étape renvoie au scénario de spec
qu'elle couvre (`specs/<capacité>/spec.md`). Cocher au fur et à mesure ; les écarts relevés sont
devenus la section 8 de `tasks.md`, vérifiée au §9.

## 1. Préparer

1. Depuis la racine : `cp .env.example .env` si `.env` n'existe pas, puis
   `docker compose up --build`. L'app est sur <http://127.0.0.1:8080>, la base sur
   `127.0.0.1:5430` (le port doit être libre : arrêter tout autre stack qui l'occupe).
2. Ouvrir trois sessions de navigateur séparées (profils ou fenêtres privées distinctes), une par
   compte. Sur `/register`, créer :

   | Compte | Prénom | Nom |
   |--------|--------|-----|
   | `alice` | Alice | Tremblay |
   | `bob` | Bob | Gagnon |
   | `carole` | Carole | Roy |

3. Contacts : Alice et Carole cherchent « bob » (barre de recherche, type « Utilisateur ») et
   cliquent « Envoyer une demande » ; Bob accepte les deux dans « Mes contacts ». Alice et Carole
   ne sont pas en contact entre elles.
4. Outils de Bob (« Gérer mes outils » → « Enregistrer un outil ») : « Perceuse » avec une photo,
   une description de plus de 125 caractères et des notes privées « code du cadenas 1234 » ;
   « Scie » ; « Ponceuse ». Outil d'Alice : « Rabot ».

Pour les cas qui exigent une date passée (expiration), la page refuse toute date antérieure à
aujourd'hui : on recule la date en base, depuis la racine :

```sh
docker compose exec db psql -U outillerie -d outillerie \
  -c "UPDATE loan SET start_date = current_date - 1 WHERE id = <id>;"
```

L'`id` d'une demande se lit avec
`docker compose exec db psql -U outillerie -d outillerie -c "SELECT id, tool_id, borrower_id, status, start_date, end_date FROM loan ORDER BY id;"`.

## 2. Carte et page de confirmation

- [x] Alice, « Trouver un outil » (menu du compte) : chaque carte de Bob affiche
      « Emprunter » en bouton actif ; aucune mention « Bientôt disponible ».
      *outils-des-contacts — Contenu de la carte*
- [x] Alice clique « Emprunter » sur la Perceuse : la page montre le nom, la photo, la description
      **entière**, « État : Fonctionnel », « Propriétaire : Bob Gagnon », « Du » prérempli à
      aujourd'hui, « Au » vide, « Message pour Bob Gagnon (facultatif) ». Les notes privées
      n'apparaissent pas. Dans « Mes prêts » d'Alice, aucune demande n'a été créée.
      *demandes-d-emprunt — Contenu de la page, Notes privées cachées*
- [x] « Annuler » ramène sur « Trouver un outil » sans rien créer.
      *Envoi d'une demande — Annuler*
- [x] En tapant à la main `/loans/new/<id du Rabot>` (outil d'Alice), puis l'id d'un outil de
      Carole, puis `/loans/new/999999` : page 404 dans les trois cas.
      *Outil qu'on peut demander — Outils refusés*
- [x] Déconnecté, ouvrir `/loans/new/<id de la Perceuse>` : redirection vers la connexion.
      *Outil qu'on peut demander — Visiteur*

## 3. Dates et message

Sur la page de confirmation de la Perceuse, Alice saisit un message « je passe samedi », puis
essaie chaque cas. À chaque refus, le message et les dates saisies restent dans le formulaire.

- [x] « Du » à hier (saisie au clavier si le sélecteur l'interdit) :
      « La date de début ne peut pas être passée ».
- [x] « Du » dans 15 jours : « La date de début doit être dans les 14 prochains jours ».
- [x] « Du » dans 14 jours et « Au » le même jour : accepté. Retirer aussitôt cette demande dans
      « Mes prêts » (« Retirer ma demande ») pour libérer la Perceuse avant le §4.
- [x] « Au » avant « Du » : « La date de fin ne peut pas précéder la date de début ».
- [x] « Du » aujourd'hui, « Au » dans 30 jours (31 jours) : « Un prêt dure au plus 30 jours ».
- [x] « Au » vide : « Indiquez des dates valides ».
- [x] Message de plus de 500 caractères (coller un long texte ; le champ bloque à 500, contourner
      avec les outils du navigateur) : « Le message ne doit pas dépasser 500 caractères ».
      *demandes-d-emprunt — Dates d'une demande, Message trop long*

## 4. Envoi, retour et carte

- [x] Alice, « Trouver un outil » filtré par « perc » avec « Disponible uniquement » coché, clique
      « Emprunter » sur la Perceuse, saisit « Du » aujourd'hui, « Au » dans 2 jours, le message
      « <b>merci</b> » sur deux lignes, et confirme. Elle revient sur la liste **avec les mêmes
      filtres**, et un message **vert** « Demande envoyée à Bob Gagnon ».
      *Envoi d'une demande — Demande envoyée ; Messages de succès*
- [x] Sur la carte de la Perceuse, Alice voit « Demande envoyée » grisé ; Carole (« Trouver un
      outil ») voit « En attente de prêt » et « Emprunter » grisé.
      *outils-des-contacts — Sa propre demande, Outil indisponible*
- [x] Depuis la page de Bob (« Mes contacts » → nom de Bob), Alice demande la Scie : elle revient
      sur la page de Bob.
      *Envoi d'une demande — Depuis la page du contact*
- [x] Deux onglets d'Alice sur la page de confirmation de la Ponceuse : confirmer dans le premier,
      puis dans le second. Le second ramène à la liste avec « Cet outil n'est plus disponible » ;
      « Mes prêts » ne montre qu'une demande de Ponceuse.
      *Une demande à la fois par outil — Deuxième onglet*
- [x] Carole ouvre la confirmation de la Perceuse (lien gardé avant la demande d'Alice, ou adresse
      tapée) : retour à la liste avec « Cet outil n'est plus disponible ».

## 5. « Mes prêts » et pastilles

- [x] Bob voit une pastille à côté de son nom d'utilisateur ; le menu montre une pastille à côté de
      « Mes prêts » égale au nombre de demandes reçues en attente. Une demande de contact en
      attente s'ajoute au total du nom d'utilisateur, pas à « Mes prêts ».
      *demandes-d-emprunt — Une demande reçue ; contacts — Demandes de contact et d'emprunt*
- [x] Bob, « Mes prêts » : section « Demandes reçues » avec Perceuse, Scie, Ponceuse, emprunteuse
      « Alice Tremblay », dates en toutes lettres, statut « En attente », boutons « Refuser » et
      « Accepter ». Le message s'affiche littéralement `<b>merci</b>`, sur deux lignes, sans gras.
      *Demandes reçues et envoyées ; Balisage affiché tel quel*
- [x] Alice, « Mes prêts » : section « Mes demandes » avec ses demandes et « Retirer ma demande ».
- [x] Carole ne voit le message « <b>merci</b> » nulle part (« Trouver un outil », page de Bob,
      « Mes prêts »).
      *Message au propriétaire — Message privé*

## 6. Réponses et retrait

- [x] Bob accepte la Perceuse : statut « Acceptée » ; Carole voit toujours « En attente de prêt ».
      *Réponse du propriétaire — Acceptation*
- [x] Bob refuse la Scie : statut « Refusée » ; la Scie redevient « Disponible » pour Carole.
      *Refus*
- [x] Alice retire sa demande de Ponceuse : statut « Annulée » ; la Ponceuse redevient
      « Disponible ».
      *Retrait d'une demande par l'emprunteur — Retrait*
- [x] Retour arrière du navigateur sur « Mes prêts » de Bob puis nouveau clic « Accepter » sur la
      Scie déjà refusée : retour sur « Mes prêts » avec « Cette demande n'est plus en attente ».
      *Réponse en double*
- [x] Expiration : Alice demande la Ponceuse à partir d'aujourd'hui ; reculer sa date de début
      d'un jour (§1). Bob voit la demande « Expirée », sans boutons, hors de la pastille ; la
      Ponceuse redevient « Disponible » pour Carole.
      *Expiration d'une demande ; Statut de prêt — Demande expirée*

## 7. Annulations automatiques

- [x] Alice demande la Ponceuse (aujourd'hui). Bob ouvre « Retirer » pour la Ponceuse : la page
      annonce « 1 demande d'emprunt en attente sera annulée ». Après confirmation, la demande
      d'Alice est « Annulée » dans ses « Mes prêts ». La Perceuse acceptée n'est pas touchée.
      *inventaire — Demandes annulées par le retrait*
- [x] Bob remet la Ponceuse en circulation ; Alice la redemande ; Bob la modifie à l'état
      « Hors d'usage » : la demande est « Annulée ».
      *inventaire — Demandes annulées par le passage hors d'usage*
- [x] Bob demande le Rabot d'Alice ; Alice demande la Scie de Bob. Bob ouvre « Retirer » à côté
      d'Alice dans « Mes contacts » : la page annonce « 2 demandes d'emprunt en attente entre vous
      seront annulées ». Après confirmation, les deux sont « Annulée ».
      *contacts — Demandes d'emprunt annulées*

## 8. Affichage

- [x] Grille des cartes : une colonne sur un écran étroit (fenêtre réduite ou mode mobile), trois
      sur un écran large ; « Emprunter » reste aligné en bas de chaque carte.
- [x] Page « Mes prêts » lisible sur écran étroit (le tableau peut défiler horizontalement).
- [x] Les messages d'erreur restent rouges ; seul le message de succès est vert.

## 9. Retours de QA (tâche 8.4)

- [x] « Mes prêts » : « Accepter » en vert, « Refuser » en rouge.
      *demandes-d-emprunt — Couleur des réponses*
- [x] « Mes prêts » : les demandes sur lesquelles on peut agir d'abord, puis les autres, chaque
      groupe de la plus récente à la plus ancienne.
      *Ordre des demandes*
- [x] Page de confirmation : les sélecteurs n'offrent pour « Du » que d'aujourd'hui à 14 jours,
      pour « Au » que d'aujourd'hui à 43 jours.
      *Bornes des sélecteurs*
- [x] Barre de recherche : « Outil » choisi par défaut ; « Utilisateur » gardé sur la page de
      résultats d'une recherche d'utilisateurs.
      *recherche — Utilisateur connecté, Texte cherché conservé*
