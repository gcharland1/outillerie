# Décisions d'architecture (ADR)

Format [MADR 4.0](https://adr.github.io/madr/), gabarit minimal : [adr-template.md](adr-template.md).
Créer un ADR avec le skill `/adr <titre>`.

## Quand écrire un ADR

Quand un choix est coûteux à défaire ou contraint le code futur : dépendance, schéma de données,
structure de l'app, outil de dev, convention transverse. Un détail d'implémentation local n'en a pas besoin.

## Règles

* Fichier `NNNN-titre-en-kebab.md`, numéro croissant, jamais réutilisé.
* `status` : `proposed` → `accepted` ; plus tard `deprecated` ou `superseded by NNNN`.
* Un ADR `accepted` est immuable : pour changer d'avis, écrire un nouvel ADR qui le remplace
  et mettre à jour le `status` de l'ancien (seule modification permise).
* Un changement OpenSpec qui tranche un choix d'architecture crée ou cite un ADR.

## Index

| #    | Décision                                                                 | Statut   |
|------|--------------------------------------------------------------------------|----------|
| 0000 | [Consigner les décisions avec MADR](0000-consigner-les-decisions-avec-madr.md) | accepted |
| 0001 | [Flask, app factory et rendu serveur Jinja](0001-flask-app-factory-et-rendu-serveur.md) | accepted |
| 0002 | [PostgreSQL, SQLAlchemy et migrations Alembic](0002-postgresql-sqlalchemy-et-alembic.md) | accepted |
| 0003 | [uv et Docker Compose pour le développement](0003-uv-et-docker-compose.md) | accepted |
| 0004 | [OpenSpec pour le développement piloté par spec](0004-openspec.md) | accepted |
| 0005 | [Archiver les sessions Claude dans le dépôt](0005-archiver-les-sessions-claude.md) | accepted |
| 0006 | [Sessions dans le cookie signé de Flask, expiration d'inactivité](0006-sessions-dans-le-cookie-signe-de-flask.md) | accepted |
| 0007 | [Règles d'évolution du schéma de persistance](0007-regles-d-evolution-du-schema-de-persistance.md) | accepted |
| 0008 | [Photos des outils en `bytea`](0008-photos-des-outils-en-bytea.md) | accepted |
| 0009 | [Diagramme du schéma généré par paracelsus](0009-diagramme-du-schema-genere-par-paracelsus.md) | accepted |
| 0010 | [Protection CSRF par Flask-WTF](0010-protection-csrf-par-flask-wtf.md) | superseded by 0012 |
| 0011 | [Une Blueprint par fonctionnalité](0011-une-blueprint-par-fonctionnalite.md) | accepted |
| 0012 | [Protection CSRF par Flask-WTF, jeton lié à la session](0012-jeton-csrf-lie-a-la-session.md) | accepted |
| 0013 | [Relation de contact symétrique en une ligne](0013-relation-de-contact-symetrique-en-une-ligne.md) | accepted |
| 0014 | [Normalisation des photos téléversées avec Pillow](0014-normalisation-des-photos-televersees-avec-pillow.md) | accepted |
| 0015 | [Exposer la production par Cloudflare Tunnel, app en boucle locale](0015-exposer-la-production-par-cloudflare-tunnel.md) | accepted |
| 0016 | [Recherche floue des outils avec pg_trgm et unaccent](0016-recherche-floue-des-outils-avec-pg-trgm-et-unaccent.md) | superseded by 0018 |
| 0017 | [Déployer la production par sondage du serveur](0017-deployer-la-production-par-sondage-du-serveur.md) | accepted |
| 0018 | [Règles communes des champs de recherche](0018-regles-communes-des-champs-de-recherche.md) | accepted |
| 0019 | [Couleurs des boutons : positif en bleu, négatif en neutre](0019-couleurs-des-boutons-positif-en-bleu-negatif-en-neutre.md) | superseded by 0022 |
| 0020 | [Le courriel est l'identifiant de connexion](0020-le-courriel-est-l-identifiant-de-connexion.md) | accepted |
| 0021 | [Livrer jusqu'à `main` derrière des gates, après l'accord sur la spec](0021-livrer-jusqu-a-main-derriere-des-gates.md) | superseded by 0024 |
| 0022 | [Couleurs des boutons : action en bleu, action dangereuse en rouge, le reste neutre](0022-couleurs-des-boutons-action-en-bleu-danger-en-rouge.md) | accepted |
| 0023 | [Supprimer un compte par anonymisation](0023-supprimer-un-compte-par-anonymisation.md) | accepted |
| 0024 | [Un seul skill, de l'issue jusqu'à `main`, derrière des gates](0024-un-seul-skill-de-l-issue-jusqu-a-main.md) | superseded by 0025 |
| 0025 | [Trier les issues par étiquettes et livrer les lots approuvés](0025-trier-les-issues-par-etiquettes-et-livrer-les-lots-approuves.md) | accepted |
| 0026 | [Ne pas rejouer les tests d'un arbre déjà testé par sa PR](0026-ne-pas-rejouer-les-tests-d-un-arbre-deja-teste-par-sa-pr.md) | proposed |
| 0027 | [Confirmer le courriel par un lien signé envoyé en SMTP](0027-confirmer-le-courriel-par-un-lien-signe-envoye-en-smtp.md) | proposed |
