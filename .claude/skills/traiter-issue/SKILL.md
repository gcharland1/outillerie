---
name: traiter-issue
description: Prend une ou plusieurs issues GitHub jusqu'au merge dans main — des agents en parallèle répondent à tout ce que le dépôt sait, l'utilisateur ne tranche que le reste et valide la spec, puis la livraison implémente, vérifie, relit, archive, ouvre la PR et merge, chaque étape gardée par une gate. Utiliser sur "/traiter-issue <n>" ou "prendre l'issue <n>".
argument-hint: <numéro d'issue> [<numéro>…] [consignes, ex. « dans un worktree », « sans livrer »]
allowed-tools: Read, Write, Edit, Grep, Glob, Agent, Skill, EnterWorktree, Bash(gh issue view:*), Bash(openspec:*), Bash(git log:*), Bash(git branch:*), Bash(git worktree list:*), Bash(git ls-tree:*), Bash(uv run:*), Bash(uv sync:*), Bash(git status:*), Bash(git diff:*), Bash(git ls-files:*), Bash(git grep:*), Bash(git add:*), Bash(git commit:*), Bash(git fetch:*), Bash(git rebase:*), Bash(git push:*), Bash(git switch:*), Bash(git pull:*), Bash(gh pr create:*), Bash(gh pr checks:*), Bash(gh pr view:*), Bash(gh pr merge:*), Bash(gh run view:*), Bash(gh run list:*), Bash(git merge-base:*), Bash(docker compose exec:*), Bash(grep:*), Bash(ls:*)
---

# Traiter une issue

Workflow complet de `CLAUDE.md`. Deux interventions humaines seulement : les décisions `utilisateur` (étape 4) et
l'accord sur la spec (étape 8). Avant cet accord : aucun code applicatif, aucun commit. Après : la livraison
(étapes 9 à 17), sans autre question tant qu'aucune gate n'échoue. Plusieurs issues : un changement par issue,
une seule branche, étapes 1 à 7 menées pour chacune, une seule question à la fois pour l'ensemble.

## 1. Cadrer

1. Arguments : `$ARGUMENTS`. Les nombres sont les numéros d'issue ; le reste, ce sont des consignes
   à suivre pendant tout le skill. Sans numéro : le demander.
2. `gh issue view <n> --json number,title,state,body,labels,comments` (sans `--json`, la sortie peut être
   vide). Issue fermée ou introuvable : s'arrêter et le dire.
3. Choisir un nom de changement en kebab-case français.
4. Si les consignes demandent un worktree : `EnterWorktree` avec ce nom, avant toute écriture. Sinon, depuis
   `main` à jour, créer une branche à ce nom (plusieurs issues : un nom commun) ; une branche courante qui
   porte d'autres commits ou modifications ne sert pas, car la PR les mergerait. Le worktree
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
- ce que fera la livraison : implémentation, vérifications, relecture, archivage, PR et merge dans `main`,
  donc déploiement (ADR 0017).

Terminer par : « Valider la spec pour lancer la livraison jusqu'à `main`. » Puis attendre. Seul un accord
explicite sur ces changements ouvre l'étape 9 ; une remarque ou une question reprend à l'étape 4 ou 6.
Consigne « sans livrer » : s'arrêter ici.

# Livraison

Mène tous les changements validés jusqu'au merge dans `main`. **Merger `main`, c'est déployer** : le serveur
déploie chaque commit vert de `main` (ADR 0017). GitHub n'exige pas la CI pour merger : seules les gates
ci-dessous la font respecter. Chacune est un arrêt dur, pas un avertissement, et remplace toute question.

## 9. Préconditions (gate d'entrée)

Arrêter sans rien écrire si l'une manque :

- l'utilisateur a donné un accord explicite sur la spec de ces changements à l'étape 8 ; une approbation
  donnée pour un autre changement ne compte pas, et une remarque ou une question postérieure à l'accord
  l'annule ;
- chaque changement passe `openspec validate <nom> --strict --no-interactive` ;
- `tasks.md` ne contient aucune tâche qui exige un humain (QA à la main, décision, accès à la production) ;
  sinon arrêt : la spec est à corriger avant l'accord (étape 6) ;
- la branche porte cette livraison et rien d'autre : `git log origin/main..HEAD` ne montre que des commits
  de ces changements et `git status --short` que leurs fichiers. Sinon arrêt, car la PR les mergerait sans
  accord.

## 10. Implémenter

`/opsx:apply <nom>` pour chaque changement, une tâche à la fois, tests compris, sans pause pour demander la
suite. Les règles de pause de l'apply restent : une tâche qui demande plus que la spec, ou une spec qui se révèle
fausse, arrête la livraison (voir § Arrêt).

## 11. Gate « terminé »

`/verifier` doit rendre **terminé**. Sinon, corriger ce qu'il signale et relancer, au plus trois fois ; au-delà,
arrêt.

Une révision Alembic ajoutée est aussi testée en aller-retour sur une base dédiée, jamais sur celle de
développement :
`docker compose exec -T db sh -c 'dropdb --if-exists -U "$POSTGRES_USER" outillerie_livraison && createdb -U "$POSTGRES_USER" outillerie_livraison'`,
puis, avec `DATABASE_URL` sur cette base (identifiants de `.env.example`, jamais lus dans `.env`),
`uv run flask db upgrade`, des lignes qui exercent le `downgrade`, `uv run flask db downgrade`,
`uv run flask db upgrade` ; enfin `dropdb` de cette base.

## 12. Commit local

Commits selon `CLAUDE.md` (français, `Thème - Description`, trailer `Session:`), adresse personnelle, avant la
relecture : le `relecteur` ne lit que l'historique et `git diff`, pas les fichiers non suivis.

## 13. Gate relecture

1. Agent `relecteur` sur `origin/main..HEAD`, avec dans sa demande les changements livrés et ce contrôle en
   plus : une révision qui retire, renomme ou resserre (`DROP`, `NOT NULL`, renommage) dans la même PR que le
   code qui en dépend est BLOQUANTE (ADR 0007, retour arrière de 0017).
2. Corriger chaque constat BLOQUANT et À CORRIGER ; une SUGGESTION est corrigée si elle est sûre et dans le
   périmètre, sinon notée dans le corps de PR. Commiter les corrections.
3. Repasser la gate 11, puis le `relecteur` une seconde fois. Un BLOQUANT restant à ce second passage : arrêt.
   Un À CORRIGER restant va dans « Pas fait » du corps de PR.

« Repasser la gate 13 », plus bas, veut dire ses deux passages.

## 14. Archiver

`openspec archive <nom> --yes` pour chaque changement (les specs principales sont mises à jour), puis
`openspec validate --all --no-interactive`. Les ADR et notes créés dans la branche pointent vers
`openspec/changes/archive/<date>-<nom>/`. Puis seulement, les ADR `proposed` cités par le proposal passent à
`accepted` (fichier et index), car un ADR accepté est immuable : le récapitulatif soumis à l'accord les
nommait (ADR 0024). Commiter.

## 15. PR

1. `git fetch` ; si `origin/main` a avancé, `git rebase origin/main`, puis repasser les gates 11 et 13. Un
   conflit qui touche le comportement : arrêt.
2. `git push -u origin <branche>:<branche>` ; après un rebase d'une branche déjà poussée,
   `git push --force-with-lease origin <branche>:<branche>`. Jamais vers `main`.
3. Corps de PR écrit avec l'outil Write dans le dossier temporaire de la session (jamais dans le dépôt), dans un
   appel séparé de `gh`, sur le modèle des PR précédentes : `Closes #n` pour chaque issue que la spec validée
   résout entièrement, `Refs #n` sinon, exactement selon la liste du récapitulatif accepté ; « Ce qui change » ; « Vérifications » avec ce qui a réellement tourné ;
   « Pas fait » sans rien omettre ; « Suivis ».
4. Titre au format `Thème - Description` des commits.
5. Garde-fous de `CLAUDE.local.md`, juste avant de créer la PR : termes interdits absents des fichiers
   suivis, des messages de commit, du titre et du corps de PR. Une seule occurrence : arrêt, sans citer le terme.
6. `gh pr create --base main --title "<titre>" --body-file <fichier>`.

## 16. Gate CI

`gh pr checks <n> --watch`. Un échec : lire le journal (`gh run view <id> --log-failed`), corriger dans la
branche, commiter, repasser les gates 11 et 13 (sans réimplémenter ni réarchiver), pousser. Deux échecs de suite :
arrêt.

## 17. Merger

Seulement si tout est vrai, vérifié juste avant :

- la CI de la PR est verte sur le dernier commit poussé (`gh pr view <n> --json headRefOid` égal à `HEAD`) ;
- `gh pr view <n> --json mergeable,mergeStateStatus` : `MERGEABLE` et `CLEAN` ;
- aucun commit n'a été ajouté depuis le dernier passage des gates 11 et 13 ;
- `git fetch` puis `git merge-base --is-ancestor origin/main HEAD` : la branche contient `main` ; sinon
  rebase et reprise au § 15.1.

Alors `gh pr merge <n> --merge`. Hors worktree : `git switch main && git pull --ff-only`. Dans un worktree,
`main` est extrait par le dépôt principal et `git switch main` y échoue : seulement `git fetch`, et laisser le
worktree en place. Vérifier avec
`gh run list --branch main --limit 1` que la CI de `main` démarre sur le commit de merge ; ne pas attendre le déploiement.

## Arrêt

Une gate qui échoue arrête tout : ni push, ni PR, ni merge de plus. Rendre à l'utilisateur l'étape, la cause
avec sa sortie, ce qui est déjà fait (branche, commits, PR) et les options. Ne jamais contourner une gate :
pas de `--no-verify`, pas de test sauté ou marqué `xfail` pour passer, pas de `--admin` au merge, pas de push
vers `main`.

Hors de ce skill, toujours après accord explicite : ouvrir une issue, fermer une issue autrement que par le
`Closes` d'une spec validée, modifier la production, toucher une autre branche que celle de la livraison.

## Fin

Récapitulatif court : PR et commit de merge, issues fermées, worktree laissé en place s'il y en a un, gates passées (avec le nombre de tests),
constats de relecture corrigés ou laissés, ce qui n'a pas été fait, suivis à ouvrir.
