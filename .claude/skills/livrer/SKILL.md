---
name: livrer
description: Mène un changement OpenSpec validé jusqu'à `main` sans intervention — implémentation, vérifications, relecture, archivage, PR, CI et merge, chaque étape gardée par une gate. Utiliser quand l'utilisateur a validé la spec et demande de livrer, après `/traiter-issue`, ou sur "/livrer <changement>". Ne se lance jamais sans cet accord.
argument-hint: <changement> [<changement>…]
allowed-tools: Read, Write, Edit, Grep, Glob, Agent, Skill, Bash(uv run:*), Bash(uv sync:*), Bash(openspec:*), Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git ls-files:*), Bash(git grep:*), Bash(git add:*), Bash(git commit:*), Bash(git fetch:*), Bash(git rebase:*), Bash(git push:*), Bash(git switch:*), Bash(git pull:*), Bash(gh pr create:*), Bash(gh pr checks:*), Bash(gh pr view:*), Bash(gh pr merge:*), Bash(gh run view:*), Bash(gh run list:*), Bash(git merge-base:*), Bash(docker compose exec:*), Bash(grep:*), Bash(ls:*)
---

# Livrer

Prend un ou plusieurs changements de `openspec/changes/` jusqu'au merge dans `main`. **Merger `main`, c'est
déployer** : le serveur déploie chaque commit vert de `main` (ADR 0017). GitHub n'exige pas la CI pour merger :
seules les gates ci-dessous la font respecter. Chacune est un arrêt dur, pas un avertissement.

## 0. Préconditions (gate d'entrée)

Arrêter sans rien écrire si l'une manque :

- l'utilisateur a donné un accord explicite sur la spec de ces changements et demandé la livraison ; une
  approbation donnée pour un autre changement ne compte pas, et une remarque ou une question postérieure
  à l'accord l'annule ;
- chaque changement passe `openspec validate <nom> --strict --no-interactive` ;
- `tasks.md` ne contient aucune tâche qui exige un humain (QA à la main, décision, accès à la production) ;
  sinon arrêt : la spec est à corriger avant l'accord (`/traiter-issue` étape 6) ;
- la branche porte cette livraison et rien d'autre : `git log origin/main..HEAD` ne montre que des commits
  de ces changements et `git status --short` que leurs fichiers. Sur `main`, créer une branche nommée
  d'après le changement depuis `origin/main` à jour. Toute autre branche qui porte d'autres commits ou
  modifications : arrêt, car la PR les mergerait sans accord.

## 1. Implémenter

`/opsx:apply <nom>` pour chaque changement, une tâche à la fois, tests compris, sans pause pour demander la
suite. Les règles de pause de l'apply restent : une tâche qui demande plus que la spec, ou une spec qui se révèle
fausse, arrête la livraison (voir § Arrêt).

## 2. Gate « terminé »

`/verifier` doit rendre **terminé**. Sinon, corriger ce qu'il signale et relancer, au plus trois fois ; au-delà,
arrêt.

Une révision Alembic ajoutée est aussi testée en aller-retour sur une base dédiée, jamais sur celle de
développement :
`docker compose exec -T db sh -c 'dropdb --if-exists -U "$POSTGRES_USER" outillerie_livraison && createdb -U "$POSTGRES_USER" outillerie_livraison'`,
puis, avec `DATABASE_URL` sur cette base (identifiants de `.env.example`, jamais lus dans `.env`),
`uv run flask db upgrade`, des lignes qui exercent le `downgrade`, `uv run flask db downgrade`,
`uv run flask db upgrade` ; enfin `dropdb` de cette base.

## 3. Commit local

Commits selon `CLAUDE.md` (français, `Thème - Description`, trailer `Session:`), adresse personnelle, avant la
relecture : le `relecteur` ne lit que l'historique et `git diff`, pas les fichiers non suivis.

## 4. Gate relecture

1. Agent `relecteur` sur `origin/main..HEAD`, avec dans sa demande les changements livrés et ce contrôle en
   plus : une révision qui retire, renomme ou resserre (`DROP`, `NOT NULL`, renommage) dans la même PR que le
   code qui en dépend est BLOQUANTE (ADR 0007, retour arrière de 0017).
2. Corriger chaque constat BLOQUANT et À CORRIGER ; une SUGGESTION est corrigée si elle est sûre et dans le
   périmètre, sinon notée dans le corps de PR. Commiter les corrections.
3. Repasser la gate 2, puis le `relecteur` une seconde fois. Un BLOQUANT restant à ce second passage : arrêt.
   Un À CORRIGER restant va dans « Pas fait » du corps de PR.

« Repasser la gate 4 », plus bas, veut dire ses deux passages.

## 5. Archiver

`openspec archive <nom> --yes` pour chaque changement (les specs principales sont mises à jour), puis
`openspec validate --all --no-interactive`. Les ADR et notes créés dans la branche pointent vers
`openspec/changes/archive/<date>-<nom>/`. Puis seulement, les ADR `proposed` cités par le proposal passent à
`accepted` (fichier et index), car un ADR accepté est immuable : le récapitulatif soumis à l'accord les
nommait (ADR 0021). Commiter.

## 6. PR

1. `git fetch` ; si `origin/main` a avancé, `git rebase origin/main`, puis repasser les gates 2 et 4. Un
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

## 7. Gate CI

`gh pr checks <n> --watch`. Un échec : lire le journal (`gh run view <id> --log-failed`), corriger dans la
branche, commiter, repasser les gates 2 et 4 (sans réimplémenter ni réarchiver), pousser. Deux échecs de suite :
arrêt.

## 8. Merger

Seulement si tout est vrai, vérifié juste avant :

- la CI de la PR est verte sur le dernier commit poussé (`gh pr view <n> --json headRefOid` égal à `HEAD`) ;
- `gh pr view <n> --json mergeable,mergeStateStatus` : `MERGEABLE` et `CLEAN` ;
- aucun commit n'a été ajouté depuis le dernier passage des gates 2 et 4 ;
- `git fetch` puis `git merge-base --is-ancestor origin/main HEAD` : la branche contient `main` ; sinon
  rebase et reprise au § 6.1.

Alors `gh pr merge <n> --merge`, puis `git switch main && git pull --ff-only`. Vérifier avec
`gh run list --branch main --limit 1` que la CI de `main` démarre sur le commit de merge ; ne pas attendre le déploiement.

## Arrêt

Une gate qui échoue arrête tout : ni push, ni PR, ni merge de plus. Rendre à l'utilisateur l'étape, la cause
avec sa sortie, ce qui est déjà fait (branche, commits, PR) et les options. Ne jamais contourner une gate :
pas de `--no-verify`, pas de test sauté ou marqué `xfail` pour passer, pas de `--admin` au merge, pas de push
vers `main`.

Hors de ce skill, toujours après accord explicite : ouvrir une issue, fermer une issue autrement que par le
`Closes` d'une spec validée, modifier la production, toucher une autre branche que celle de la livraison.

## Fin

Récapitulatif court : PR et commit de merge, issues fermées, gates passées (avec le nombre de tests),
constats de relecture corrigés ou laissés, ce qui n'a pas été fait, suivis à ouvrir.
