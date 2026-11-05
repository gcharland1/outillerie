---
status: proposed
date: 2026-11-04
decision-makers: Gabriel Charland
---

# Déployer la production par sondage du serveur

## Contexte et problème

Chaque commit de `main` dont la CI est verte doit passer en production sans intervention (issue #5).
Le serveur n'accepte aucune connexion entrante hors SSH (ADR 0015), le dépôt est public, et
`compose.yaml` construit l'image sur place, avec un seul fichier pour le développement et la
production. Il faut choisir qui déclenche le déploiement, où tournent les tests, où se construit
l'image et comment revenir en arrière. Changement OpenSpec : `openspec/changes/deploiement-automatise/`
(décisions et sources dans `questions.md`).

## Options considérées

* Sondage par le serveur : un timer systemd interroge l'API GitHub et déploie le plus récent commit
  vert ; build sur le serveur
* SSH depuis GitHub Actions vers un script à commande forcée
* Runner GitHub auto-hébergé sur le serveur
* Image construite par Actions, poussée sur GHCR, tirée par le serveur
* Tests relancés sur le serveur avant le redémarrage

## Décision

Option retenue : « sondage par le serveur, build sur le serveur », parce qu'elle n'ouvre aucun port
entrant, ne met aucun secret dans GitHub et garde un seul `compose.yaml`.

* Tests : dans Actions seulement, `ci.yml` tournant aussi sur `push` vers `main`. Un commit est vert
  si son run `push` a réussi avec les jobs `tests` et `specs`. Le serveur ne lance jamais de tests :
  l'image n'a pas pytest (`UV_NO_DEV=1`, ADR 0003) et la fixture `mock_app` fait `drop_all`.
* Choix : le plus récent commit vert de `main` qui descend du commit déployé, toutes les 5 minutes.
* Protection : `pg_dump` avant chaque déploiement (10 gardés sur le serveur), build avant l'arrêt,
  image étiquetée par SHA (`outillerie-app:${APP_TAG:-dev}`), `up --wait` sur un healthcheck de l'app.
* Échec : retour automatique à l'image et au checkout précédents, sans downgrade Alembic ; le commit
  n'est plus retenté. Repose sur l'expand/contract de l'ADR 0007.
* Résultat : statut de commit `deploiement` sans détail, posé avec un jeton à grain fin gardé sur le
  serveur ; le détail reste dans journald.
* Compte : le service tourne sous le compte personnel de l'utilisateur.

SSH depuis Actions est écarté : clé privée et empreinte d'hôte dans GitHub, port 22 joignable depuis
les plages d'adresses de GitHub. Le runner auto-hébergé est écarté parce que, sur un dépôt public, le
code d'une PR de fork peut l'atteindre. GHCR est écarté parce qu'il demanderait `image:` en
production et `build:` en développement, donc un second fichier Compose, contraire à l'ADR 0015.
Tester sur le serveur ajouterait uv et un Postgres jetable sur l'hôte, et le risque d'un `drop_all`
sur la base de production, pour un commit déjà testé.

### Conséquences

* Bon, parce qu'aucun port entrant ni secret GitHub ne s'ajoute, et que l'ADR 0015 reste intact.
* Bon, parce qu'un déploiement raté revient seul à la version précédente, avec une sauvegarde prise
  juste avant.
* Mauvais, parce qu'un commit attend jusqu'à 5 minutes après sa CI avant d'être déployé.
* Mauvais, parce que le déroulement d'un déploiement se lit dans journald, pas dans Actions : GitHub
  ne montre que le statut.
* Mauvais, parce que le compte personnel, membre du groupe `docker`, exécute ce que `compose.yaml`
  décrit : tout commit mergé sur `main` agit avec des droits équivalents à root.
* Mauvais, parce que le script et les unités systemd s'installent et se mettent à jour à la main, et
  que le jeton GitHub expire.
* Mauvais, parce qu'un retour arrière sans downgrade suppose que chaque migration respecte
  l'expand/contract ; sinon, restauration manuelle depuis la sauvegarde.
