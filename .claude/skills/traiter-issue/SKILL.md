---
name: traiter-issue
description: Prend une ou plusieurs issues GitHub jusqu'au merge dans main — des agents en parallèle répondent à tout ce que le dépôt sait, l'utilisateur ne tranche que le reste et valide la spec, puis `/livrer` implémente et merge derrière des gates. Utiliser sur "/traiter-issue <n>" ou "prendre l'issue <n>".
argument-hint: <numéro d'issue> [<numéro>…] [consignes, ex. « dans un worktree », « sans livrer »]
allowed-tools: Read, Write, Edit, Grep, Glob, Agent, Skill, EnterWorktree, Bash(gh issue view:*), Bash(openspec:*), Bash(git log:*), Bash(git branch:*), Bash(git worktree list:*), Bash(git ls-tree:*)
---

# Traiter une issue

Workflow complet de `CLAUDE.md`. Deux interventions humaines seulement : les décisions `utilisateur` (étape 4) et
l'accord sur la spec (étape 8). Avant cet accord : aucun code applicatif, aucun commit. Après : `/livrer`, sans
autre question tant qu'aucune gate n'échoue. Plusieurs issues : un changement par issue, une seule branche,
étapes 1 à 7 menées pour chacune, une seule question à la fois pour l'ensemble.

## 1. Cadrer

1. Arguments : `$ARGUMENTS`. Les nombres sont les numéros d'issue ; le reste, ce sont des consignes
   à suivre pendant tout le skill. Sans numéro : le demander.
2. `gh issue view <n> --json number,title,state,body,labels,comments` (sans `--json`, la sortie peut être
   vide). Issue fermée ou introuvable : s'arrêter et le dire.
3. Choisir un nom de changement en kebab-case français.
4. Si les consignes demandent un worktree : `EnterWorktree` avec ce nom, avant toute écriture. Le worktree
   part de `origin/main` : les fichiers non commités du poste n'y sont pas, et les agents reçoivent son
   chemin comme racine.
5. Repérer le travail en cours ailleurs : `git worktree list`, `git branch`, puis les ADR et changements
   OpenSpec des autres branches (`git ls-tree -r --name-only <branche> docs/decisions openspec/changes`)
   et des autres worktrees, commités ou non. Le prochain numéro d'ADR est le plus grand vu partout + 1.
6. Lire `openspec/specs/` (`openspec list --specs`), `docs/decisions/README.md` et `.claude/rules/*.md`.
7. `openspec new change "<nom>"`.
8. Créer `openspec/changes/<nom>/questions.md` avec chaque inconnue qui bloque l'écriture d'une spec :
   acteurs, comportement attendu, périmètre, données et schéma, interface, erreurs, sécurité.

## 2. Déployer les agents

En un seul message, un agent `Explore` par angle. Chacun reçoit la racine du dépôt (le worktree s'il y en a un),
le texte de l'issue, la liste des questions, le travail en cours repéré à l'étape 1.5 et son angle :

- **Code** : blueprints, modèles, gabarits et migrations touchés ; motifs existants à réutiliser dans `application/`.
- **Specs et ADR** : specs principales concernées, contraintes des ADR `accepted`, nouvel ADR requis ou non.
- **Cas limites** : listes « Scénarios manquants » et « Sécurité et vie privée » de `.claude/skills/grill-spec/SKILL.md` §3, appliquées à l'issue.
- **Antériorité** : `openspec/changes/archive/` et `docs/sessions/` pour les décisions passées sur le même sujet.

Format de réponse imposé, une entrée par question :

```
Q : <question>
Réponse : <réponse ou « inconnue »>
Source : Sourced <fichier:ligne> | Inferred de <faits> | No basis
Recommandation : <choix et pourquoi>
Décision utilisateur requise : oui/non — <pourquoi>
```

Les agents ajoutent les questions nouvelles qu'ils découvrent, au même format.

## 3. Trier

Fusionner et dédoublonner les réponses dans `questions.md` :

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|

`Décidé par` :

- `dépôt` : réponse Sourced ; appliquée.
- `convention` : réponse Inferred d'un ADR, d'une règle ou d'un motif existant ; appliquée, signalée à l'utilisateur.
- `utilisateur` : choix produit, de périmètre, coûteux à défaire, ou No basis.

## 4. Interroger

- Les questions `utilisateur`, une à la fois, la plus lourde de conséquences d'abord.
- Chaque question est autonome : le contexte et ce que les agents ont trouvé, les options, la recommandation.
- Consigner chaque réponse dans `questions.md` dès qu'elle arrive.

## 5. Second passage

Si une réponse change le terrain d'un angle, relancer cet angle seul avec les réponses, puis trier et interroger.
Un seul passage supplémentaire ; ce qui reste ouvert passe à l'étape 7.

## 6. Rédiger la spec

1. Suivre la boucle d'artefacts de `.claude/skills/openspec-propose/SKILL.md` (`openspec status`, `openspec instructions`)
   sur le changement existant ; `design.md` renvoie à `questions.md`.
2. Passer `questions.md` en revue : chaque décision qui ajoute une dépendance, touche le schéma ou la
   structure, ou déroge à une règle transverse (hook global, convention d'un ADR) va dans un ADR via `/adr`,
   en `proposed`, cité par le proposal. Plusieurs décisions liées peuvent partager un ADR.
3. `tasks.md` ne contient que des tâches qu'un agent mène seul : pas de QA à la main, pas d'accès à la
   production ; une vérification qui exige un humain va dans le design, comme limite connue. La dernière
   tâche est « `/verifier` rend terminé ».
4. `openspec validate <nom> --strict --no-interactive`.

## 7. Se griller

Appliquer la grille de `.claude/skills/grill-spec/SKILL.md` §3 aux artefacts produits. Corriger ce que `questions.md`
tranche déjà ; poser le reste comme à l'étape 4.

## 8. Gate : accord de l'utilisateur

Récapitulatif court :

- nombre de questions par `Décidé par` ;
- la liste des décisions `convention`, que l'utilisateur peut renverser ;
- les artefacts et ADR créés ;
- le worktree et sa branche, s'il y en a un ;
- les ADR `proposed` que l'accord fera passer à `accepted`, et les issues que la PR fermera (`Closes`) ;
- ce que fera `/livrer` : implémentation, vérifications, relecture, archivage, PR et merge dans `main`,
  donc déploiement (ADR 0017).

Terminer par : « Valider la spec pour lancer la livraison jusqu'à `main`. » Puis attendre. Seul un accord
explicite sur ces changements ouvre l'étape 9 ; une remarque ou une question reprend à l'étape 4 ou 6.
Consigne « sans livrer » : s'arrêter ici.

## 9. Livrer

`/livrer <changement>…` avec tous les changements validés. Ses gates (vérification, relecture, CI, état de la
PR) remplacent toute question : une gate qui échoue arrête la livraison et rend la main.
