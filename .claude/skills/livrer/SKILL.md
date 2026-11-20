---
name: livrer
description: Mène un changement OpenSpec validé jusqu'à `main` sans intervention — implémentation, vérifications, relecture, archivage, PR, CI et merge, chaque étape gardée par une gate. Utiliser quand l'utilisateur a validé la spec et demande de livrer, après `/traiter-issue`, ou sur "/livrer <changement>". Ne se lance jamais sans cet accord.
argument-hint: <changement> [<changement>…]
allowed-tools: Read, Write, Edit, Grep, Glob, Agent, Skill, Bash(uv run:*), Bash(uv sync:*), Bash(openspec:*), Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git ls-files:*), Bash(git grep:*), Bash(git add:*), Bash(git commit:*), Bash(git fetch:*), Bash(git rebase:*), Bash(git push:*), Bash(git switch:*), Bash(git pull:*), Bash(gh pr:*), Bash(grep:*), Bash(ls:*)
---

# Livrer

Prend un ou plusieurs changements de `openspec/changes/` jusqu'au merge dans `main`. **Merger `main`, c'est
déployer** : le serveur déploie chaque commit vert de `main` (ADR 0017). Chaque gate ci-dessous est donc un arrêt
dur, pas un avertissement.

## 0. Préconditions (gate d'entrée)

Arrêter sans rien écrire si l'une manque :

- l'utilisateur a validé la spec et demandé la livraison, dans ce message ou dans la conversation ; une
  approbation donnée pour un autre changement ne compte pas ;
- chaque changement passe `openspec validate <nom> --strict --no-interactive` ;
- `tasks.md` ne contient aucune tâche qui exige un humain (QA à la main, décision, accès à la production). Une
  telle tâche est retirée et notée dans la section « Pas fait » du corps de PR, après accord de l'utilisateur
  si elle protégeait un comportement de la spec ;
- la branche courante n'est pas `main` ; sinon créer une branche nommée d'après le changement depuis
  `origin/main` à jour.

Les ADR `proposed` cités par le proposal passent à `accepted` (fichier et index) : l'accord sur la spec les couvre.

## 1. Implémenter

`/opsx:apply <nom>` pour chaque changement, une tâche à la fois, tests compris, sans pause pour demander la
suite. Les règles de pause de l'apply restent : une tâche qui demande plus que la spec, ou une spec qui se révèle
fausse, arrête la livraison (voir § Arrêt).

## 2. Gate « terminé »

`/verifier` doit rendre **terminé**. Sinon, corriger ce qu'il signale et relancer, au plus trois fois ; au-delà,
arrêt. Une migration ajoutée est aussi testée en aller-retour (`upgrade`, `downgrade` sur des lignes qui
exercent le `downgrade`, `upgrade`) sur une base dédiée, jamais sur la base de développement.

## 3. Gate relecture

1. Agent `relecteur` sur le diff complet par rapport à `origin/main`.
2. Corriger chaque constat BLOQUANT et À CORRIGER ; une SUGGESTION est corrigée si elle est sûre et dans le
   périmètre, sinon notée dans le corps de PR.
3. Relancer `/verifier`, puis le `relecteur` une seconde fois. Un BLOQUANT restant à ce second passage : arrêt.

## 4. Archiver

`/opsx:archive <nom>` pour chaque changement, puis `openspec validate --all --no-interactive`. Les ADR et notes
créés dans la branche pointent vers `openspec/changes/archive/<date>-<nom>/`.

## 5. Commit et PR

1. `git fetch` ; si `origin/main` a avancé, `git rebase origin/main`, puis reprendre à la gate 2. Un conflit
   qui touche le comportement : arrêt.
2. Commits selon `CLAUDE.md` (français, `Thème - Description`, trailer `Session:`), adresse personnelle.
3. Garde-fous de `CLAUDE.local.md` : termes interdits absents des fichiers suivis, des messages de commit et du
   corps de PR. Une seule occurrence : arrêt, sans citer le terme.
4. `git push -u origin <branche>:<branche>`.
5. Corps de PR écrit dans un fichier (outil Write, dans un appel séparé de `gh`), sur le modèle des PR
   précédentes : `Closes #n` (ou `Refs #n` si l'issue reste ouverte), « Ce qui change », « Vérifications »
   avec ce qui a réellement tourné, « Pas fait » sans rien omettre, « Suivis ».
6. `gh pr create --base main --body-file <fichier>`.

## 6. Gate CI

`gh pr checks <n> --watch`. Un échec : lire le journal (`gh run view --log-failed`), corriger dans la branche,
reprendre à la gate 2. Deux échecs de suite : arrêt.

## 7. Merger

Seulement si tout est vrai, vérifié juste avant :

- la CI de la PR est verte sur le dernier commit poussé ;
- `gh pr view <n> --json mergeable,mergeStateStatus` : `MERGEABLE` et `CLEAN` ;
- aucun commit n'a été poussé sur la branche depuis la dernière relecture sans repasser les gates 2 et 3.

Alors `gh pr merge <n> --merge`, puis `git switch main && git pull --ff-only`. Vérifier que la CI de `main`
démarre sur le commit de merge ; ne pas attendre le déploiement.

## Arrêt

Une gate qui échoue arrête tout : ni push, ni PR, ni merge de plus. Rendre à l'utilisateur l'étape, la cause
avec sa sortie, ce qui est déjà fait (branche, commits, PR) et les options. Ne jamais contourner une gate :
pas de `--no-verify`, pas de test sauté ou marqué `xfail` pour passer, pas de `--admin` au merge, pas de
`force` push sur `main`.

Hors de ce skill, toujours après accord explicite : ouvrir ou fermer une issue, modifier la production,
toucher une autre branche que celle de la livraison.

## Fin

Récapitulatif court : PR et commit de merge, issues fermées, gates passées (avec le nombre de tests),
constats de relecture corrigés ou laissés, ce qui n'a pas été fait, suivis à ouvrir.
