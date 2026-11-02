# Proposal

## Why

Depuis la PR #30, un utilisateur voit les outils de ses contacts, mais « Emprunter » reste grisé :
il ne peut pas demander un outil, et le propriétaire n'a aucun moyen d'être prévenu ni de répondre
(issue #29, seconde moitié). Les règles de prêt reportées depuis `schemas-initiaux` (qui accepte,
refuse ou annule ; dates passées ; outil retiré pendant une demande) doivent être fixées ici.

## What Changes

- « Emprunter » devient actif sur un outil « Disponible » et mène à une page de confirmation :
  nom, photo, description entière, état et propriétaire de l'outil, champs « Du » et « Au »
  obligatoires, « Message pour <Prénom Nom> » facultatif (500 caractères au plus), « Confirmer »
  et « Annuler ».
- Dates : « Du » entre aujourd'hui et 14 jours plus tard, « Au » au plus tôt « Du », prêt de
  30 jours au plus ; « aujourd'hui » dans le fuseau du site.
- « Confirmer » crée une demande et ramène à la liste d'origine (« Trouver un outil » ou page du
  contact, avec ses filtres) avec le message de succès « Demande envoyée à <Prénom Nom> ».
  « Annuler » y ramène sans rien créer.
- Sur la carte, l'emprunteur voit « Demande envoyée » grisé sur sa propre demande ; les autres
  voient « En attente de prêt ».
- Page « Mes prêts » dans le menu du compte : demandes reçues (« Accepter », « Refuser ») et mes
  demandes (« Retirer ma demande »), avec leur statut.
- Une demande sans réponse expire le lendemain de son premier jour : elle n'est plus acceptable
  et ne bloque plus l'outil.
- Pastille du nombre de demandes d'emprunt reçues à côté de « Mes prêts » ; la pastille du nom
  d'utilisateur devient le total des demandes de contact et d'emprunt.
- Retirer un outil, le passer « Hors d'usage » ou retirer un contact annule les demandes en
  attente concernées ; les pages de confirmation de retrait l'annoncent.
- Messages flash par catégorie : succès en vert, erreurs comme aujourd'hui.

## Capabilities

### New Capabilities
- `demandes-d-emprunt`: demande d'un outil par un contact, réponse du propriétaire, retrait par
  l'emprunteur, expiration, page « Mes prêts » et pastille des demandes reçues.

### Modified Capabilities
- `outils-des-contacts`: « Carte d'un outil » (bouton « Emprunter » actif, « Demande envoyée ») ;
  « Statut de prêt » (une demande expirée ne bloque plus l'outil).
- `contacts`: « Pastille des demandes en attente » (total avec les demandes d'emprunt) ; « Retrait
  d'un contact » (annule les demandes en attente entre les deux).
- `inventaire`: « Modification d'un outil » et « Retrait avec confirmation » (annulent les
  demandes en attente de l'outil).

## Impact

- Code : nouvelle Blueprint `app/loans.py` (`/loans`) ; `app/catalog.py` (règle de blocage,
  vue de l'emprunteur, lien « Emprunter ») ; `app/tools.py` (retrait, passage hors d'usage) ;
  `app/contacts.py` (retrait, pastille) ; gabarits `base.html` (menu, pastilles, catégories de
  flash), `tools/_cards.html`, `tools/confirm_retire.html`, `contacts/confirm_remove.html`, nouveaux
  `loans/confirm.html` et `loans/mine.html` ; `app/static/site.css`.
- Schéma : colonne `loan.message` nullable (`String(500)`), une révision Alembic ; `docs/schema.md`
  régénéré.
- Dépendance : aucune.
- Règle : `.claude/rules/templates.md` ajoute « Mes prêts » au menu du compte.
- ADR concernés : 0001 (sans JavaScript), 0002 et 0007 (colonne ajoutée par révision, sans
  rupture), 0011 (Blueprint `loans`), 0012 (jeton CSRF sur chaque POST), 0013 (relation de contact).
  Aucun nouvel ADR : pas de table de notifications, de courriel, de tâche planifiée ni de dates
  nullables.
- Décisions : `questions.md`.

**Hors périmètre**

- Remise (`lent`), retour (`returned`) et annulation d'un prêt accepté : changement suivant.
- Courriel ou autre notification hors du site.
- File d'attente : une seule demande ou un seul prêt ouvert à la fois par outil (règle livrée,
  reconfirmée).
- Tâche planifiée d'expiration : l'expiration se déduit des dates à la lecture.
- Conservation de la saisie après une expiration de session (comportement connu des formulaires).
