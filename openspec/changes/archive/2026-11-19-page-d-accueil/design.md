# Design

## Context

Chaque décision et sa source (fichier:ligne, session, convention) sont dans
[questions.md](questions.md) ; ce document ne garde que le « comment ».

Le changement réutilise des briques qui existent déjà :

- l'état calculé d'un prêt (`pending_request`, `upcoming_acceptance`, `expired_acceptance`,
  `overdue_loan`, `OUT`) dans `app/catalog.py`, et les lignes de « Mes prêts » (`_row`, `LoanRow`,
  `BUTTONS`) dans `app/loans.py` ;
- la visibilité d'un outil (`_visible`), les cartes en lot (`tool_cards`, `_loan_states`, photos) ;
- l'origine fermée d'une demande d'emprunt (`_origin`, `_origin_url`, valeurs `find` / `contact`) ;
- `site_today()` et `SITE_TIMEZONE` (America/Toronto).

Aucun schéma ne change : `Tool.created_at`, `Loan.start_date` / `end_date` / `status` et
`ContactRelation.created_at` suffisent.

## Goals / Non-Goals

**Goals:**

- Un tableau de bord en un nombre fixe de requêtes bornées, sans N+1.
- Une seule source pour chaque état et chaque bouton d'un prêt : l'accueil et « Mes prêts » ne
  divergent que par le filtre et l'ordre.
- Le tri de « Trouver un outil » (issue #37), partagé par la page d'un contact et par « Voir plus ».

**Non-Goals:**

- Notifications, état « vu », historique de qui a demandé un contact.
- Toute colonne ou table nouvelle.

## Decisions

### `index` reste dans `create_app()`

L'ADR 0011 garde `index` dans la fabrique. La vue redirige un visiteur vers `auth.login` à la main,
pas par `@login_required`, pour éviter le `?next=/` et le message flash de Flask-Login. Elle appelle
trois fonctions de requête, chacune dans le module de sa fonctionnalité :

- `loans.dashboard(user_id)`, au plus 5 lignes par groupe (`DASHBOARD_ROWS`) ;
- `contacts.received_requests(user_id)`, extraite de `contacts.mine`, et
  `contacts.recent_contacts(user_id, since)` ;
- `catalog.recent_tools(user_id, since)`, qui renvoie des cartes (6, plus une pour « Voir plus »).

Pas de Blueprint `home`, donc pas d'ADR. Les endpoints `url_for("index")` existants ne changent pas.

### Fenêtre de 30 jours

`since` est minuit, heure du site, de `site_today() - 30 jours`, calculé en Python. Les tests figent
la date par `monkeypatch` comme ailleurs. Une borne `now()` côté SQL ne se figerait pas.

### Lignes de « Gestion des prêts »

Une requête par rôle (emprunteur, propriétaire), avec `joinedload` de l'outil, du propriétaire et de
l'emprunteur. Elle exclut en SQL les statuts `refused`, `canceled` et `returned`, les demandes dont
la date de début est passée et les acceptations dont la date de fin est passée. Le rang de catégorie
et la date de fin donnent l'ordre, calculé en Python à partir des mêmes prédicats que `_row` :

| Groupe | Rang | Lignes |
|---|---|---|
| Demandes reçues | 0 | `pending_request` sur mes outils (ordre : `start_date`) |
| Mes emprunts | 1 | `overdue_loan` |
| | 2 | `handover_claimed` non en retard |
| | 3 | `return_claimed` |
| | 4 | `accepted` non expiré, `lent` non en retard, mes `requested` non expirées |
| Mes prêts | 5 | `overdue_loan` |
| | 6 | `upcoming_acceptance` |
| | 7 | `return_claimed` |
| | 8 | `handover_claimed` non en retard, `lent` non en retard |

Chaque groupe garde ses 5 premières lignes ; une 6e lue indique qu'il faut « Voir tous mes prêts »
sous ce groupe. La requête des demandes reçues porte `LIMIT 6` ; les emprunts et les prêts sont
triés en Python, puis coupés. Les volumes d'un voisinage justifient ce tri (Inferred, aucune
mesure). À rang et date de fin égaux, le départage se fait par `Loan.id`.

Chaque ligne passe par `_row`, ce qui donne les mêmes libellés, les mêmes boutons et le même
`overdue`. Le gabarit des boutons est extrait de `loans/mine.html` en macro partagée.

### Retour à l'accueil

Un champ caché `origin` porte une valeur énumérée :

- actions de prêt (`act`) : `home` ou `mine`, `mine` par défaut ;
- réponses de contact : `home` ou `mine`, `mine` par défaut ;
- demande d'emprunt : `find`, `contact` ou `home`, `find` par défaut.

Une fonction par module traduit la valeur en `url_for`, jamais en adresse reçue. Tous les retours
de `act` (succès, `STATUS_CHANGED`, `NO_LONGER_PENDING`, dates prises) passent par elle.

### Messages de succès

Chaque action réussie fait un `flash(..., "success")` avant la redirection vers son origine :

| Action | Message |
|---|---|
| `accept` (demande d'emprunt) | « Demande de <prénom> <nom> acceptée » |
| `refuse` (demande d'emprunt) | « Demande de <prénom> <nom> refusée » |
| `withdraw` | « Demande retirée » |
| `hand-over` | « Remise déclarée, <prénom> <nom> doit la confirmer » |
| `receive` | « Outil reçu, prêt en cours » |
| `give-back` | « Retour déclaré, <prénom> <nom> doit le confirmer » |
| `take-back` | « Outil reçu, prêt complété » |
| `not-received` | « Réponse envoyée : pas reçu » |
| `cancel` | « Prêt annulé » |
| contact `accept` | « Vous êtes maintenant en contact avec <prénom> <nom> » |
| contact `refuse` | « Demande refusée » |

<prénom> <nom> désigne l'autre partie. Le refus de contact reste discret : seul celui qui refuse voit
le message.

### Tri de « Trouver un outil »

Le paramètre `sort` prend les valeurs `relevance` (défaut), `added-desc`, `added-asc`,
`borrowed-desc` et `borrowed-asc` ; toute autre valeur donne `relevance`. Il est lu à part de
`filters`, qui alimente `visible_tools(**filters)` et le calcul `filtered`. Il est transmis :

- par le formulaire `tool-filters` (`<select name="sort">`, envoyé par « Filtrer ») ;
- par l'origine d'une demande d'emprunt (`loans/confirm.html`, `_origin_url`).

« Dernier emprunt » vient d'une sous-requête `max(Loan.start_date)` groupée par outil, sur les
statuts `(*OUT, RETURNED)`. Elle est jointe en externe pour le tri, avec départage par `Tool.id` et
`nulls_last()` en `borrowed-desc`, `nulls_first()` en `borrowed-asc`. Les cartes la lisent en lot,
comme `_loan_states`. La carte n'affiche la date que si elle existe.

### Carte partagée

`<article class="card tool-card">` sort de `tools/_cards.html` dans un partiel `tools/_card.html`,
inclus par `_cards.html` et par `index.html`. Le formulaire de filtres reste dans `_cards.html`.

### Healthcheck

`compose.yaml` vise `http://127.0.0.1:5000/login`. Cette page répond 200 sans session ni requête
en base. Le healthcheck ne dépend ainsi plus du suivi des redirections par urllib.

## Risks / Trade-offs

- [Une date de « Dernier emprunt » future quand l'outil est remis avant le premier jour] →
  Accepté par l'utilisateur ; cas rare.
- [La date de « Dernier emprunt » révèle l'activité de prêt d'un outil à tous les contacts] →
  Seulement la date, jamais l'emprunteur ni le nombre de prêts. La carte montre déjà « Prêté
  jusqu'au ».
- [L'accueil montre plus que la pastille (2c, 2d, 3b, 3d)] → Voulu : la pastille compte ce qui
  attend une action, l'accueil montre les prêts en cours.
- [« Vous êtes maintenant en contact » est vu aussi par celui qui a accepté] → Choix de
  l'utilisateur, pour ne pas changer le schéma.
- [Tests qui repèrent la connexion par « Rebonjour » sur `/`] → Remplacés par la présence du menu
  du compte ; les vérifications de visiteur passent sur `/login`.
