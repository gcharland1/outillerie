# Questions — plafonner la recherche d'utilisateurs (issue #40)

1. Quel plafond (50 suggéré par l'issue) et comment le choisir : constante, configuration ?
2. Le plafond coupe-t-il après le tri actuel (contient, puis ressemblance, puis nom) ?
3. Comment savoir qu'il y a plus de résultats : `LIMIT n+1` ou `COUNT` ? Affiche-t-on le total ?
4. Texte exact du message invitant à préciser la recherche, et emplacement (avant ou après la liste).
5. Pagination ou simple plafond ?
6. La page de résultats charge-t-elle les relations de contact par compte (N+1) ? Le plafond borne-t-il ces requêtes ?
7. Interaction avec l'issue #38 (retrait du nom d'utilisateur) dans le même lot : critère de départage du tri.
8. Faut-il un ADR (ADR 0018 règles communes des champs de recherche) ?

## Tri

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 1 | Valeur et forme du plafond | 25 comptes, constante `USER_RESULTS_MAX = 25` dans `app/search.py`, comme `USER_FUZZY_*`, `NEW_TOOLS`, `DASHBOARD_ROWS` | Valeur : utilisateur, 2026-11-20 (l'issue suggérait 50) ; forme : Sourced `app/search.py:10-13`, `app/catalog.py:26`, ADR 0018 | utilisateur |
| 2 | Coupe après le tri | `LIMIT` en SQL après le tri complet ; sous 4 caractères le tri est alphabétique, donc la spec dit « les 25 premiers dans l'ordre de tri » | Sourced `app/search.py:49-61` | dépôt |
| 3 | Savoir s'il y en a plus | `LIMIT max + 1`, booléen `more`, pas de total (un `COUNT` rebalaierait la table et dirait combien de comptes correspondent) | Sourced `app/catalog.py:225-236`, `app/loans.py:144-178` | convention |
| 4 | Texte et emplacement du message | Au-dessus du tableau, par l'emplacement `message` : « Plus de 25 utilisateurs correspondent à « texte » ; précisez votre recherche » | Utilisateur, 2026-11-20 | utilisateur |
| 5 | Pagination | Non : simple plafond, la pagination est un non-objectif constant | Sourced archives `liste-de-contacts/proposal.md:71`, `consulter-les-outils-des-contacts/design.md:17`, `gestion-des-outils/design.md:30` | convention |
| 6 | Relations de contact | Pas de N+1 : `relation_states` fait 3 requêtes `IN` ; ne lui passer que les 25 comptes gardés | Sourced `app/contacts.py:161-188`, `app/search.py:34` | dépôt |
| 7 | Départage après #38 | Le tri par nom est défini par `authentification-par-courriel` ; ce changement n'ajoute que la coupe, départage final `User.id` | Sourced `app/search.py:60` | convention |
| 8 | ADR | Aucun : plafond local, facile à défaire, le tri de chaque recherche relève de sa spec ; le design note que la conséquence « sans plafond » de l'ADR 0018 ne vaut plus pour les comptes | Sourced ADR 0018, `docs/decisions/README.md` | convention |
| N1 | Exactement 25 / 26 | Deux scénarios ; les tests abaissent la constante par `monkeypatch` | Inferred du modèle `accueil/spec.md` (« Exactement 6 » / « Plus de 6 ») ; ici 25 et 26 | convention |
| N2 | Coût SQL | Le plafond ne réduit pas le balayage (score calculé sur chaque compte) ; seulement transfert et rendu | Inferred de `app/search.py:50-61` | dépôt |
| N3 | Énumération | Le plafond ne l'empêche pas (aucune limitation de débit) ; noté au design | Sourced : aucun `limiter` dans `application/` | dépôt |
| N4 | Recherche d'outils | Hors périmètre : l'issue vise les comptes, « Trouver un outil » est borné aux contacts | Sourced `app/catalog.py:220-222` | convention |
| N5 | Coexistence des messages | Le message de plafond n'apparaît qu'avec des résultats ; il ne remplace jamais « Aucun utilisateur… » | Sourced `app/search.py:25-37` | dépôt |
