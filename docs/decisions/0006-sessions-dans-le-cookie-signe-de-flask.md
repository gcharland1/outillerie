---
status: accepted
date: 2026-10-20
decision-makers: Gabriel Charland
---

# Sessions dans le cookie signé de Flask, expiration d'inactivité

## Contexte et problème

La connexion (Flask-Login) garde l'utilisateur dans la session par défaut de Flask : un cookie
signé, sans état côté serveur, valide 31 jours. L'issue #11 demande une déconnexion sécuritaire
et une fermeture automatique après inactivité. Il faut choisir où vit la session, ce qui décide
si une déconnexion peut invalider une copie du cookie. Changement OpenSpec :
`openspec/changes/fermeture-de-session/`.

## Options considérées

* Cookie signé de Flask, session permanente à expiration glissante de 30 minutes
* Sessions côté serveur (table de sessions, ou jeton de session par utilisateur vérifié à chaque requête)

## Décision

Option retenue : « cookie signé de Flask, expiration glissante de 30 minutes », parce qu'elle ne
demande ni dépendance ni schéma, et que Flask vérifie l'âge de la signature à chaque lecture :
un cookie copié est refusé par le serveur après 30 minutes d'inactivité. La déconnexion vide le
cookie du navigateur ; le cookie porte `HttpOnly` et `SameSite=Lax`.

### Conséquences

* Bon, parce qu'aucune table, aucune migration ni aucune requête en base ne s'ajoute pour lire la session.
* Bon, parce que la durée tient dans une seule valeur de configuration (`PERMANENT_SESSION_LIFETIME`),
  remplaçable dans les tests.
* Mauvais, parce qu'une copie volée du cookie reste valide jusqu'à 30 minutes après la dernière
  requête, même après la déconnexion : aucune révocation côté serveur.
* Mauvais, parce que « déconnecter tous mes appareils » ou bloquer un compte en cours de session
  demandera un nouvel ADR qui remplace celui-ci.
* Mauvais, parce que le serveur ne distingue pas une session expirée d'une absence de session :
  un message d'expiration doit venir d'ailleurs (page `/logged-out` atteinte par rafraîchissement).
