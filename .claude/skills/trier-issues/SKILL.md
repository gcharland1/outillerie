---
name: trier-issues
description: Trie les issues GitHub ouvertes — des agents répondent à ce que le dépôt sait, un commentaire pose dans l'issue les questions qui restent à l'utilisateur et les décisions prises par convention, puis l'issue reçoit `clarification-required` ou `understood`. N'écrit que sur GitHub. Utiliser sur "/trier-issues" ou "trier les issues".
argument-hint: "[<numéro d'issue>…]"
allowed-tools: Read, Write, Grep, Glob, Agent, Bash(gh repo view:*), Bash(gh label list:*), Bash(gh label create:*), Bash(gh issue list:*), Bash(gh issue view:*), Bash(gh issue comment:*), Bash(gh issue edit:*), Bash(openspec:*), Bash(git log:*), Bash(git branch:*), Bash(git worktree list:*), Bash(git ls-tree:*), Bash(sha256sum:*), Bash(grep:*), Bash(test:*), Bash(ls:*)
---

# Trier les issues

Premier workflow de l'ADR 0025. Rien n'est écrit dans le dépôt : ni fichier, ni branche, ni commit. Sur GitHub,
seulement un commentaire et des étiquettes par issue triée. Aucune question à l'utilisateur pendant le tri :
les questions vont dans les issues.

## 1. Préparer

1. Propriétaire : `gh repo view --json owner -q .owner.login`.
2. Termes interdits : le `.claude/forbidden-terms.local` du checkout principal (premier chemin de
   `git worktree list`). Absent : arrêt avant toute publication.
3. Étiquettes `clarification-required`, `understood`, `ready-to-implement`, `delivery-blocked` : créer celles
   que `gh label list --json name` ne montre pas.
4. Contexte du dépôt comme `/traiter-issue` étapes 1.5 et 1.6 : travail en cours, specs, ADR, règles.

## 2. Choisir les issues

Seuls les issues et commentaires du propriétaire sont lus ; ceux d'un tiers n'entrent jamais dans le contexte,
car le dépôt est public. Lecture d'une issue, toujours filtrée à la source ; l'issue d'un tiers ne rend que
son numéro et son auteur :

```
gh issue view <n> --json number,title,body,labels,author,comments \
  --jq 'if .author.login == "<propriétaire>" then {number, title, body, labels, comments: [.comments[] | select(.author.login == "<propriétaire>") | {body, createdAt}]} else {number, author: .author.login} end'
```

Liste : `gh issue list --state open --author <propriétaire> --limit 200 --json number,title,labels`.
Arguments `$ARGUMENTS` : seulement ces issues, triées même sans changement, sauf celles d'un tiers ou qui
portent `delivery-blocked`, signalées à la fin.

L'agent publie avec le compte du propriétaire ; ses commentaires se reconnaissent à leur première ligne :

- tri : `<!-- trier-issues body-sha256=<empreinte> -->`, l'empreinte étant les 64 caractères hexadécimaux
  de `gh issue view <n> --json body -q .body | sha256sum` ;
- arrêt de livraison : `<!-- traiter-issue delivery-blocked -->`.

Un commentaire du propriétaire sans aucun de ces marqueurs est un commentaire humain.

À trier :

- l'issue n'a aucun commentaire de tri, quelles que soient ses étiquettes ;
- ou elle ne porte ni `clarification-required` ni `understood` ;
- ou un commentaire humain suit le dernier commentaire de tri ;
- ou l'empreinte du corps diffère de celle du dernier commentaire de tri.

Ignorée : `delivery-blocked`, que l'utilisateur retire lui-même. Un titre modifié ou un commentaire humain
édité n'est pas détecté : l'utilisateur ajoute alors un commentaire pour relancer le tri.

## 3. Analyser

Un agent `Explore` par issue, en un seul message, chacun avec l'issue filtrée (les commentaires de tri
compris : leurs questions et les réponses humaines sont des faits), le contexte de l'étape 1.4, les catégories
d'inconnues de `/traiter-issue` étape 1.8, et les angles et le format de réponse de son étape 2. Lecture seule.

Trier les réponses comme `/traiter-issue` étape 3 (`dépôt`, `convention`, `utilisateur`). Relever aussi :

- les décisions qui demandent un ADR (critère de `/traiter-issue` étape 6.2) ;
- une révision de schéma qui retire ou resserre (`DROP`, `NOT NULL`, renommage), que la livraison isole (ADR 0007).

## 4. Commenter et étiqueter

Corps écrit avec Write dans le dossier temporaire de la session, puis `grep -iEf <termes> <fichier>` : un code
de sortie autre que 1 (terme trouvé ou erreur) : ne rien publier sur cette issue et le signaler à la fin, sans
citer le terme.

```
<!-- trier-issues body-sha256=<empreinte> -->
**Tri : understood** | **Tri : clarification-required**

**Questions** (répondre en commentaire)
1. <question> — A : <option> ; B : <option>. Recommandé : <option>, parce que <raison>.

**Décisions de l'utilisateur** (réponses déjà données)
- <décision>

**Décisions par convention** (à renverser en commentaire)
- <décision> (<ADR, règle ou motif suivi>)

**ADR à écrire** : <sujets> | aucun
**Schéma retiré ou resserré** : oui | non
```

Une section vide est omise. Une ligne par entrée, sans le détail des agents.

Dans cet ordre, pour qu'une approbation antérieure ne couvre jamais le nouveau commentaire :

1. `gh issue edit <n> --remove-label` pour celles que l'issue porte parmi `ready-to-implement`,
   `understood` et `clarification-required` ;
2. `gh issue comment <n> --body-file <fichier>` ;
3. `gh issue edit <n> --add-label` : `understood` sans question, `clarification-required` sinon.

## 5. Fin

Tableau court : issue (numéro et titre), étiquette posée, nombre de questions ; puis les issues ignorées ou
non publiées et pourquoi. Rappeler que `ready-to-implement` sur une issue `understood` vaut accord pour
`/traiter-issue lots`.
