---
status: accepted
date: 2026-10-25
decision-makers: Gabriel Charland
---

# Relation de contact symétrique en une ligne

## Contexte et problème

L'issue #22 lie deux voisins comme contacts après une demande que l'un envoie et que l'autre
accepte ou refuse. La relation est symétrique : si Alice est le contact de Bob, Bob est celui
d'Alice, et un retrait la défait des deux côtés. L'issue laisse « à analyser » la façon de
l'enregistrer. Le schéma doit empêcher les doublons, les demandes à soi-même et les demandes
croisées. Changement OpenSpec : `openspec/changes/liste-de-contacts/`.

## Options considérées

* Une table `contact_relation` à une ligne par paire rangée (`user_a_id < user_b_id`), à côté
  d'une table `contact_request`
* Une table `contact_relation` à deux lignes dirigées par relation (Alice → Bob et Bob → Alice)
* Une seule table `contact_request` dont le statut « acceptée » tient lieu de relation

## Décision

Option retenue : « une ligne par paire rangée », parce qu'elle enregistre une relation une seule
fois et que la base garantit son unicité sans code applicatif. Règles :

* `contact_relation` : clé primaire composite (`user_a_id`, `user_b_id`), `CHECK user_a_id < user_b_id`,
  index sur `user_b_id`. Le code construit toujours la paire par une seule fonction qui la range.
* `contact_request` : `requester_id`, `recipient_id`, `CHECK requester_id <> recipient_id`, sans
  statut. Une demande existe tant qu'elle attend une réponse ; l'accepter ou la refuser la
  supprime, puisqu'aucun parcours ne la relit : la relation porte le résultat d'une acceptation,
  et un refus est discret. Une ligne qu'on garderait avec un statut `completed` n'apporterait
  aucune information.
* Index unique sur `(LEAST(requester_id, recipient_id), GREATEST(requester_id, recipient_id))` : au
  plus une demande par paire, dans un sens ou dans l'autre ; la suppression d'une demande traitée
  libère la paire pour une nouvelle demande.

### Conséquences

* Bon, parce qu'une relation ne peut ni exister en double, ni n'exister que d'un côté.
* Bon, parce que demandes en double et demandes croisées sont refusées par la base, même sous
  des envois simultanés.
* Bon, parce que les demandes ne contiennent que celles qui attendent une réponse : ni statut à
  tenir, ni lignes mortes, ni index partiel.
* Mauvais, parce qu'aucun historique ne dit qui a refusé qui, ni quand : un besoin futur
  (blocage, délai avant relance, statistiques) demandera un nouvel ADR.
* Mauvais, parce que lister les contacts d'un voisin demande un `OR` sur les deux colonnes, et
  que tout code doit ranger la paire avant de chercher ou d'insérer une relation.
* Mauvais, parce que l'autogénération d'Alembic compare mal les index d'expression :
  celui-ci est relu, et au besoin écrit, à la main dans la révision.
