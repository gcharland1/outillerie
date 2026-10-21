---
name: grill-spec
description: Met à l'épreuve un changement OpenSpec (proposal, specs, design, tasks) avant l'implémentation pour en trouver les failles tant qu'elles coûtent peu. Utiliser avant /opsx:apply, quand l'utilisateur veut challenger une spec, ou sur "/grill-spec <changement>". Lecture seule.
argument-hint: <nom du changement>
allowed-tools: Read, Grep, Glob, Bash(openspec:*), Bash(git diff:*), Bash(git log:*)
---

# Griller une spec

Lecture seule : ne modifier aucun fichier. Les décisions de l'utilisateur s'appliquent ensuite avec `/opsx:update`.

## 1. Cibler le changement

1. Changement = `$ARGUMENTS` ; sinon le seul changement en cours de `openspec list --json`. S'il y en a plusieurs, demander lequel.
2. `openspec validate <changement> --strict --no-interactive` : chaque erreur devient une constatation.

## 2. Lire

- Tous les artefacts de `openspec/changes/<changement>/` : `proposal.md`, `specs/**/spec.md`, `design.md`, `tasks.md`.
- Les specs principales concernées : `openspec list --specs`, puis `openspec show <spec> --type spec`.
- Les ADR `accepted` de `docs/decisions/` (index dans `docs/decisions/README.md`).
- Le code que le changement touche dans `application/` (routes, modèles, templates, migrations, tests).

## 3. Griller

Noter chaque constatation avec sa source (`fichier:ligne`) et sa gravité (bloquant, important, mineur).

- **Scénarios testables** : chacun dit qui agit, avec quelle entrée, et quel résultat visible ou vérifiable par un test pytest.
- **Scénarios manquants** : chemins d'erreur ; entrée vide, invalide ou en double ; utilisateur anonyme vs connecté ; permissions (agir sur la ressource d'autrui) ; concurrence et onglets multiples ; JavaScript désactivé ; bornes de temps et d'expiration ; retour arrière du navigateur et resoumission de formulaire.
- **Cohérence** : aucune contradiction entre proposal, specs, design et tasks ; chaque exigence a ses tâches, chaque tâche sert une exigence.
- **Spec sans implémentation** : pas de nom de classe, de fonction, de table ou de bibliothèque dans les exigences ; ces détails vont dans `design.md`.
- **Forme** : chaque exigence emploie SHALL ou MUST ; description d'exigence ≤ 500 caractères ; titres OpenSpec en anglais, texte en français.
- **ADR** : conforme aux ADR `accepted` (ex. migration Alembic, jamais `db.create_all()`). Un nouvel ADR via `/adr` est-il requis (dépendance, schéma, structure, outil, convention transverse) ? Le proposal cite-t-il les ADR concernés ?
- **Périmètre** : le hors-périmètre du proposal est explicite et cohérent avec la spec ; rien de hors périmètre n'apparaît dans les tâches.
- **Tâches** : chacune vérifiable ; les tests pytest dans le même groupe que le travail qu'ils couvrent ; migration prévue s'il y a changement de schéma ; la dernière tâche lance `/verifier`.
- **Sécurité et vie privée** : CSRF sur tout POST, redirections ouvertes (`next`), fixation et invalidation de session, énumération de comptes par les messages d'erreur, données personnelles exposées ou journalisées, contrôle d'accès côté serveur.

## 4. Interroger l'utilisateur

- Une question à la fois, la plus lourde de conséquences d'abord.
- Chaque question : la constatation et sa source, la recommandation de l'agent et pourquoi, les autres options s'il y en a.
- Si le code ou les artefacts répondent déjà, ne pas poser la question : le dire.
- S'arrêter quand l'utilisateur le demande ou qu'il ne reste rien de significatif.

## 5. Conclure

Rendre un récapitulatif court :

| # | Décision | Artefact touché |
|---|----------|-----------------|

Puis la liste des modifications à appliquer avec `/opsx:update <changement>`, et les ADR à créer avec `/adr` le cas échéant. Ne rien modifier soi-même.
