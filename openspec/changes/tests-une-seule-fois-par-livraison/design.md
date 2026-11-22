# Design

Décisions et sources : [questions.md](questions.md). Décision d'architecture : ADR 0026 (complète
l'ADR 0017). Motivation : [proposal.md](proposal.md).

## Preuve qu'un arbre a été testé

Un run `pull_request` teste le merge virtuel de la tête de PR dans la base de l'époque, pas la tête
seule. Ce résultat vaut pour le commit de merge `M` de `main` quand :

1. `M` a deux parents, `P1` (l'ancien `main`) et `P2` (la tête de la PR) ;
2. `P2` contient `P1` : `main` n'avance qu'en avant (règle `non_fast_forward` du ruleset), donc la
   base testée était un ancêtre de `P1`, donc de `P2`, et le merge virtuel avait l'arbre de `P2` ;
3. l'arbre de `M` égale celui de `P2` ;
4. un run `pull_request` de ce dépôt (`head_repository.full_name` = `gcharland1/outillerie`) pour
   `head_sha = P2` est `completed`/`success` et sa dernière tentative a `tests` et `specs` réussis.

La condition 2 écarte le cas où `main` aurait annulé un commit présent dans la base testée : l'arbre
de `M` pourrait alors égaler celui de `P2` sans avoir été testé tel quel. La gate 17 du skill
(branche qui contient `origin/main`) rend 2 et 3 vraies pour chaque livraison ; un squash, un rebase
ou un merge depuis l'interface sans branche à jour les rend fausses, et la suite se rejoue (sûr).

## Script `deploiement/already_tested.py`

Bibliothèque standard seulement, comme `deployer.py`, qu'il réutilise (`REPOSITORY`,
`REQUIRED_JOBS`, client `GitHub` à `opener` injectable). Entrées : `GITHUB_SHA`, `GITHUB_TOKEN`.
Toutes les lectures passent par l'API :

- `GET /repos/{r}/commits/{M}` : parents et arbre ; `GET /repos/{r}/commits/{P2}` : arbre ;
- `GET /repos/{r}/compare/{P1}...{P2}` : `behind_by == 0` ;
- `GET /repos/{r}/actions/runs?head_sha={P2}&event=pull_request` puis les jobs de chaque run candidat.

Sortie : `tested=true` ou `tested=false` dans `$GITHUB_OUTPUT`, et une ligne de journal qui dit
pourquoi. Toute erreur (HTTP, JSON, champ absent) donne `tested=false` : le doute rejoue les tests.
La décision est `proves_tested(sha, api)`, où `api` fait ces lectures et s'arrête à la première
condition fausse ; testée sans réseau avec un faux `api`.

## CI

- Nouveau job `already-tested`, `permissions: actions: read, contents: read`. Sur un événement autre
  que `push`, il sort `tested=false` sans appel.
- `tests` et `specs` gagnent `needs: already-tested`. Chaque étape après le checkout porte
  `if: needs.already-tested.outputs.tested != 'true'` ; le job réussit donc, et `is_green` le voit
  réussi (un job sauté rendrait le commit non vert, scénario « Job sauté »).
- `tests` et `specs` portent aussi `if: ${{ !cancelled() }}` : si `already-tested` échoue (panne du
  runner), ils tournent quand même, et sa sortie absente vaut « rejouer ». Sans cela, ils seraient
  sautés, et GitHub compte un check requis sauté comme réussi (Training) : une PR se mergerait sans
  tests.
- Les noms des jobs `tests` et `specs` ne changent pas : ce sont les checks exigés par le ruleset et
  par `is_green`.
- Sur une PR, `already-tested` sort `tested=false` en quelques secondes : la suite tourne toujours.

## Skill `/traiter-issue`

- Étape 17 : après le merge, vérifier que le run `push` du commit de merge réussit et que son job
  `already-tested` a sorti `tested=true` ; ne pas attendre le déploiement.
- Le paragraphe « GitHub n'exige pas la CI pour merger » devient : le ruleset exige une PR et les
  checks `tests` et `specs`, sans branche à jour (`strict: false`) et avec contournement admin ;
  seules les gates du skill imposent une branche à jour et interdisent le contournement.

## Limites

- Un merge fait à la main, en squash, en rebase ou sans branche à jour rejoue la suite (sûr, en
  double). Restreindre les méthodes de merge du dépôt à `merge` est laissé à l'utilisateur
  (question 12).
- Le gain dépend de l'API GitHub : une panne rejoue la suite, comme aujourd'hui.
