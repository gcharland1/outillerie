# Questions — s'authentifier par courriel (issue #38)

1. Connexion : le champ devient « Courriel » ; comparaison sans égard à la casse (index `uq_user_email_lower`) ? Espaces autour retirés ?
2. Message d'identifiants invalides : nouveau texte (« Le courriel ou le mot de passe est invalide ») ; garder la vérification de hachage factice contre l'énumération.
3. Inscription : retrait du champ nom d'utilisateur ; le courriel reste unique sans égard à la casse.
4. Schéma : retrait de la colonne `user.username` et de `uq_user_username` ; ADR 0007 impose *expand/contract* — une ou deux révisions ? Le `downgrade` doit-il recréer des noms d'utilisateur (à partir de quoi) ?
5. Comptes existants en production : leurs utilisateurs connaissent-ils leur courriel ? Faut-il les prévenir ? Un courriel en double sans égard à la casse peut-il exister ?
6. Affichage : menu de l'entête avec le nom complet (prénom nom). Colonnes « Nom d'utilisateur » des tableaux (recherche, mes contacts, demandes reçues, accueil) : retirées ? Titre de la page d'un contact « Prénom Nom (@username) » ?
7. Tris qui utilisent le nom d'utilisateur (Mes contacts, résultats de recherche) : nouveau critère (nom, prénom ? prénom nom ?), départage.
8. Recherche d'utilisateurs : ne correspond plus qu'au prénom suivi du nom ? Le courriel reste-t-il non cherché (vie privée) ?
9. Homonymes : deux comptes « Bob Gagnon » deviennent indiscernables dans les listes et la recherche ; quoi afficher pour les distinguer sans révéler le courriel ?
10. Tests : la fixture de connexion et les fabriques utilisent `username` partout ; remplacer par le courriel.
11. Session : le cookie (ADR 0006) contient-il le nom d'utilisateur ou l'id ? Les sessions existantes survivent-elles ?
12. Specs touchées : authentification, recherche, contacts, inventaire, outils-des-contacts, accueil ; `docs/schema.md` à régénérer (ADR 0009).
13. Un ADR est-il requis (retrait d'une colonne d'identité, changement de l'identifiant de connexion) ?

## Tri

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 1 | Courriel à la connexion | Champ `<input type="email" name="email" autocomplete="username">` ; recherche par `lower(email) = lower(strip(saisie))`, l'expression de `uq_user_email_lower` ; `strip` aussi à l'inscription | Sourced `app/auth.py:32,38`, `models/user.py:14` | convention |
| 2 | Message et hachage factice | « Le courriel ou le mot de passe est invalide » ; hachage factice et appel inconditionnel gardés ; courriel saisi réaffiché, jamais le mot de passe | Sourced `app/auth.py:18-19,66-73`, `tests/test_auth.py:92` | convention |
| 3 | Inscription | Champ, contrôle et message du nom d'utilisateur retirés ; unicité du courriel sans casse déjà en place | Sourced `app/auth.py:28-45`, `sign_up.html:14-15` | dépôt |
| 4 | Révisions Alembic | Deux révisions, deux PR : cette PR rend `username` nullable et le code ne le lit ni ne l'écrit plus (le modèle garde la colonne) ; une PR suivante supprime la colonne et `uq_user_username`. `downgrade` : `'user' || id` | Utilisateur, 2026-11-20 | utilisateur |
| 5 | Comptes de production | La production ne contient que des comptes de test : aucune révision de données ni communication aux usagers ; espaces retirés et casse ignorée à l'inscription et à la connexion pour les nouveaux comptes | Utilisateur, 2026-11-20 | utilisateur |
| 6 | Affichage | Entête « Prénom Nom » ; colonnes « Nom d'utilisateur » retirées (recherche, Mes contacts, demandes de l'accueil) ; lien de « Mes contacts » sur le nom ; titres « Bob Gagnon » | Sourced gabarits `base.html:44`, `search/results.html`, `contacts/*`, `index.html:40,45` | convention |
| 7 | Tri sans nom d'utilisateur | Prénom puis nom, sans égard à la casse ni aux accents, départage par `User.id` ; même ordre pour « Mes contacts » et la recherche (dernier critère après contient et ressemblance) | Utilisateur, 2026-11-20 | utilisateur |
| 8 | Recherche | Prénom suivi du nom seulement ; courriel jamais cherché (scénario existant) | Sourced `app/search.py:43-53`, `recherche/spec.md` « Courriel non cherché » | dépôt |
| 9 | Homonymes | Ambiguïté acceptée : aucun discriminant affiché, les actions portent l'id ; risque noté au design et à l'ADR ; un champ public de distinction serait une issue séparée | Utilisateur, 2026-11-20 | utilisateur |
| 10 | Tests | Fixtures et fabriques par courriel, un `login` commun dans `conftest`, `test_schema.py` adapté | Sourced `tests/conftest.py`, `tests/factories.py` | convention |
| 11 | Session | Le cookie porte l'id ; rien à changer | Sourced `app/__init__.py:71-73` | dépôt |
| 12 | Specs touchées | authentification, recherche, contacts, inventaire, outils-des-contacts ; accueil seulement au gabarit ; `docs/schema.md` régénéré (ADR 0009) | Sourced (grep des specs) | dépôt |
| 13 | ADR | ADR 0019 « Le courriel est l'identifiant de connexion » : identifiant, normalisation, énumération à l'inscription, homonymes, révisions | Inferred de `docs/decisions/README.md` (convention transverse, schéma) | convention |
| N1 | Énumération à l'inscription | Message « Le courriel est déjà utilisé » gardé ; risque consigné au design et à l'ADR ; inscription par courriel vérifié = issue séparée | Utilisateur, 2026-11-20 | utilisateur |
| N2 | Force brute | Hors périmètre : risque noté au design et à l'ADR ; issue séparée « Connexion - Limiter les essais de mot de passe », ouverte après accord sur son texte | Utilisateur, 2026-11-20 | utilisateur |
| N3 | Lien avec #40 | Ce changement définit le tri de « Correspondance des utilisateurs » ; #40 n'ajoute que la coupe, dans une exigence distincte | Sourced `app/search.py:56-61` | convention |
| N4 | `User.full_name` | Motif en ligne gardé, factorisation hors périmètre | Sourced (une quinzaine d'occurrences) | convention |
