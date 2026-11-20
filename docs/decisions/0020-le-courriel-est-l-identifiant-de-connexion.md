---
status: accepted
date: 2026-11-20
decision-makers: Gabriel Charland
---

# Le courriel est l'identifiant de connexion

## Contexte et problème

Un compte a un nom d'utilisateur, unique, choisi à l'inscription et demandé à la connexion, en
plus d'un courriel unique sans égard à la casse. L'issue #38 demande de se connecter par courriel
et de retirer le nom d'utilisateur de la base, du code et de l'affichage. Le nom d'utilisateur
servait aussi d'identité publique (listes, tri, titre de la page d'un contact) et fondait le
compromis d'énumération accepté à l'inscription, qui le jugeait public.
Changement OpenSpec : `openspec/changes/archive/2026-11-20-authentification-par-courriel/`. Complète 0007.

## Options considérées

* Courriel comme seul identifiant de connexion, nom d'utilisateur retiré
* Connexion par courriel ou nom d'utilisateur, nom d'utilisateur gardé
* Courriel comme identifiant, nom d'utilisateur gardé comme pseudonyme public

## Décision

Option retenue : « courriel comme seul identifiant, nom d'utilisateur retiré », parce que l'issue
le demande et qu'un seul identifiant évite d'en faire retenir deux.

Règles :

* Le courriel est comparé sans égard à la casse ni aux espaces autour, avec l'expression de
  l'index `uq_user_email_lower` ; il est enregistré sans espaces autour.
* À la connexion, un courriel inconnu et un mauvais mot de passe donnent la même réponse et la
  même vérification de hachage.
* L'identité affichée d'un compte est « Prénom Nom ». Les listes de comptes sans ordre propre (contacts, résultats
  de recherche) trient par prénom, puis nom, sans égard à la casse ni aux accents, puis par id. Le courriel n'est jamais affiché à
  un autre utilisateur ni cherché.
* La colonne `user.username` est retirée en deux passes (0007) : d'abord nullable et inutilisée,
  puis supprimée après le déploiement. Un `downgrade` qui la recrée la remplit avec `user<id>`, suffixé de `_` tant
  qu'un ancien nom d'utilisateur occupe déjà la valeur.

### Conséquences

* Bon, parce qu'un utilisateur n'a plus qu'un identifiant à retenir, déjà unique en base.
* Bon, parce que les listes affichent le nom réel, que les contacts reconnaissent.
* Mauvais, parce que deux homonymes sont indiscernables dans les listes ; les actions portent
  l'id et restent justes. Un champ public de distinction serait une autre décision.
* Mauvais, parce que « Le courriel est déjà utilisé » révèle désormais qu'une adresse privée a un
  compte ; le taire demanderait une inscription par courriel vérifié.
* Mauvais, parce qu'un courriel se devine mieux qu'un pseudonyme et qu'aucune limitation des
  essais de mot de passe n'existe ; à traiter dans une issue séparée.
* Mauvais, parce que la passe *expand* laisse la colonne dans le modèle jusqu'à la PR suivante.
