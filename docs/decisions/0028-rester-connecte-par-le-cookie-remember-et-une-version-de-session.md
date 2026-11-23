---
status: proposed
date: 2026-11-22
decision-makers: Gabriel Charland
---

# Rester connecté par le cookie remember de Flask-Login et une version de session

## Contexte et problème

L'ADR 0006 ferme toute session après 30 minutes d'inactivité, vérifiées par le serveur. L'issue #56
demande une case « Rester connecté sur cet appareil » qui supprime cette déconnexion sur l'appareil où
elle est cochée. Flask applique une seule durée à tout cookie de session : un second mécanisme est
nécessaire. Changement OpenSpec : `openspec/changes/rester-connecte/`.

## Options considérées

* Cookie « remember » de Flask-Login, 30 jours glissants, et colonne `user.session_version` portée
  par l'identifiant de session
* Cookie « remember » de Flask-Login seul
* Table de jetons par appareil (sélecteur et hachage), révocable un par un
* Cookie persistant maison, signé avec sa date, refusé par le serveur après 30 jours sans visite

## Décision

Option retenue : « cookie remember de Flask-Login et `user.session_version` », parce que Flask-Login
est déjà une dépendance, qu'une seule colonne s'ajoute, et que changer la version invalidera d'un coup
toutes les sessions et tous les cookies persistants d'un compte (« Déconnecter tous mes appareils »,
issue #61). Sans la case, l'ADR 0006 vaut toujours : cookie de session signé, 30 minutes glissantes,
`HttpOnly`, `SameSite=Lax`. Le cookie persistant porte les mêmes attributs, `Secure` hors
développement (ADR 0015), et n'est prolongé que s'il est déjà présent.

### Conséquences

* Bon, parce que la session de 30 minutes, son jeton CSRF (ADR 0012) et la révocation d'un compte
  supprimé par le chargeur (ADR 0023) restent inchangés.
* Bon, parce que la révocation de tous les appareils ne demandera ni schéma ni dépendance.
* Mauvais, parce que le cookie persistant n'a pas de date : le serveur n'impose pas les 30 jours, et
  une copie volée reste valide jusqu'à la suppression du compte ou un changement de version, qu'aucune
  fonction n'offre avant l'issue #61. Limite acceptée sur l'issue #56.
* Mauvais, parce qu'une session restée connectée garde son utilisateur mais perd son jeton CSRF après
  30 minutes d'inactivité : un formulaire ouvert avant est refusé (« Rechargez la page »).
* Mauvais, parce que l'identifiant de session passe de `<id>` à `<id>:<version>` : les sessions
  ouvertes au déploiement sont fermées une fois, et un retour arrière d'image exige de changer
  `FLASK_SECRET_KEY`, sinon l'ancien code échoue sur le nouveau format.
* Mauvais, parce que changer `FLASK_SECRET_KEY` invalide aussi tous les cookies persistants.
