---
status: accepted
date: 2026-11-19
decision-makers: Gabriel Charland
---

# Règles communes des champs de recherche

## Contexte et problème

L'ADR 0016 a doté la recherche d'outils de `pg_trgm` et `unaccent`, mais la recherche
d'utilisateurs est restée une sous-chaîne avec égard aux accents : « Fred » ne trouve pas
« Fréd » (issue #39). L'échappement des jokers se fait en Python avant `unaccent`, qui change
ensuite `％ ＿ ＼` en `% _ \` : « ％％％ » trouve tous les outils visibles. Et l'absence d'index de
l'ADR 0016 se justifiait par une recherche limitée aux outils des contacts, alors que la recherche
d'utilisateurs parcourt tous les comptes. Changement OpenSpec :
`openspec/changes/recherche-sans-accents/` (`questions.md` #4, #5, #8, #11, B/F).

## Options considérées

* Garder deux règles : outils floue, utilisateurs en sous-chaîne sans accents seulement
* Une règle commune en SQL : normalisation et échappement partagés, flou pour les deux, réglages
  propres à chaque recherche
* Normalisation en Python (NFKD), données et texte normalisés avant la requête

## Décision

Option retenue : « Une règle commune en SQL », parce qu'elle corrige l'issue et la faille des
jokers en un seul endroit, et que seule `unaccent` traite ß, œ, ø et les ponctuations
typographiques comme la recherche d'outils le fait déjà. Elle remplace l'ADR 0016, dont elle
reprend les extensions et le choix d'une constante plutôt qu'un `SET` de session.

Règles, pour tout champ de recherche :

* Normalisation, appliquée en SQL au texte cherché et aux champs comparés : `unaccent`, puis
  tiret → espace, puis espaces consécutives réduites à une ; la casse est ignorée (`ILIKE`,
  `word_similarity`).
* Sous-chaîne : `ILIKE` sur un motif échappé (`\`, `%`, `_`) **après** normalisation, en SQL ;
  jamais d'échappement Python avant `unaccent`. Le texte cherché est toujours un paramètre lié.
* Ressemblance : `word_similarity(texte normalisé, champ normalisé)` comparée à un seuil constant,
  à partir d'une longueur minimale ; seuil et longueur sont des constantes de chaque recherche.
  Outils : 0.5 dès 3 caractères. Utilisateurs : 0.5 dès 4 caractères, car à 3 caractères deux
  lettres initiales communes suffisent sur un nom de personne.
* Tri propre à chaque recherche et décrit dans sa spec ; ce qui contient le texte passe avant ce
  qui lui ressemble.
* La longueur minimale, de la recherche comme du flou, se compte sur le texte normalisé : « --- »
  devient une espace et trouverait tout.
* Une seule implémentation, partagée par les recherches (`app/text_search.py`).
* Pas d'index trigramme ni de fonction `unaccent` immuable, y compris pour la recherche
  d'utilisateurs, qui balaie toute la table `user` : le volume reste celui d'un voisinage.

### Conséquences

* Bon, parce que « fred » trouve « Fréd » et « jean pierre » trouve « Jean-Pierre » dans les deux
  recherches, avec une seule règle à tester.
* Bon, parce que `%`, `_` et `\`, pleine chasse comprise, sont toujours cherchés tels quels.
* Bon, parce que chaque recherche règle son seuil sans toucher l'autre.
* Mauvais, parce que le flou sur des noms courts donne des faux positifs (« fred » trouve
  « Alfred », « martin » trouve « Martel ») et renvoie plus de comptes par requête, sans plafond.
* Mauvais, parce que chaque recherche d'utilisateurs normalise et note toutes les lignes de
  `user` ; si le volume l'exige, il faudra un index GIN `gin_trgm_ops` sur une fonction de
  normalisation immuable, car `unaccent` à un argument dépend du `search_path`.
* Mauvais, parce que la classe d'espaces de `regexp_replace` dépend de la locale de la base, non
  vérifiée en production ; un test fixe le comportement sur l'image de la CI.
