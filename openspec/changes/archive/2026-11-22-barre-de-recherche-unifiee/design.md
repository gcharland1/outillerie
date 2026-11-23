# Design

## Context

Voir [proposal.md](proposal.md) ; décisions et sources dans [questions.md](questions.md).
`search.results` lit aujourd'hui `type` : `tool` redirige vers `tools.find`, `user` liste au plus 25
comptes par `_matching_users` (`LIMIT 26`, sans `COUNT`). La relation de chaque compte affiché vient
de `contacts.relation_states`. « Trouver un outil » s'appuie sur `catalog.visible_tools` et
`catalog.tool_cards`.

## Goals / Non-Goals

**Goals:**
- Une seule requête par section ; toujours aucun `COUNT` des comptes.
- Aucune adresse reçue n'est réutilisée telle quelle : tout paramètre passe par une liste blanche.

**Non-Goals:**
- Distance réelle, pagination au-delà de 25.

## Decisions

### Paramètres de la page
`q` (texte), `relation` (`all`, `contacts`, `others` ; autre valeur ou absence : `all`) et `more`
(`1` déplie ; autre valeur : replié). `type` et une distance éventuelle sont ignorés. Les valeurs
connues et leurs libellés vivent dans `contacts` (`RELATION_FILTERS`, `read_relation_filter`,
`read_expanded`), que `search` importe déjà ; `contacts.send_request` les relit ainsi sans import
circulaire. `contacts.search_results_url` construit l'adresse des résultats pour le « Voir plus » des
utilisateurs comme pour le retour après une demande.

### Section « Utilisateurs »
`_matching_users(text, fuzzy, relation)` garde la requête et son `LIMIT 26`, et ajoute
`User.id.in_(…)` ou `User.id.not_in(…)` avec la sous-requête des contacts, que `catalog` expose
désormais (`contact_ids_query`, ex-`_contact_ids`). Une demande en attente n'est pas un contact :
« Pas en contact uniquement » la garde. Compteur : `len(affichés) de len(trouvés)`, ou « plus de 25 »
quand la 26e ligne existe. Repliée : 5 comptes ; dépliée : 25. Le message de plafond n'apparaît que
dépliée.

### Formulaire de filtres
Formulaire GET en tête de section : `q` et `more` en champs cachés, `select name="relation"`, le
sélecteur « Dans un rayon de » en `select disabled` (non envoyé) avec « à venir », et le bouton bleu
« Filtrer ». Pas de jeton CSRF : aucun effet de bord. Affiché dès qu'un texte valide est cherché.

### Section « Outils »
`visible_tools(user_id, text=q)` (pertinence, sans plafond), puis `tool_cards(tools[:6], viewer_id,
origin={"origin": "find", "q": q})` : « Emprunter » puis « Annuler » ramènent à « Trouver un outil »
avec le texte (provenance existante de `loans._origin`). « Voir plus » : `url_for("tools.find", q=q)`.
Les cartes sont incluses une à une (`tools/_card.html`), comme sur l'accueil, sans le formulaire de
`tools/_cards.html`.

### Retour après « Envoyer une demande »
Le formulaire de chaque résultat porte `q`, `relation` et `more` en champs cachés. `send_request`
relit `relation` et `more` par les mêmes listes blanches et reconstruit l'URL par
`search_results_url` (`url_for`), sans `type`. Une demande déjà reçue mène toujours à « Mes contacts ».

### Gabarits et styles
`base.html` perd le `select` ; `site.css` perd les règles `.search-bar select`. Les filtres
réutilisent la mise en page de `.tool-filters` et `.tool-sort`. Chaque « Voir plus » est dans son
propre `div.actions` (un seul bleu par groupe, ADR 0022).

## Risks / Trade-offs

- [Deux requêtes d'outils pour un même texte] → section et « Trouver un outil » recalculent la
  visibilité ; un contact retiré entre les deux peut faire varier le total. Sans conséquence.
- [Sous-requête `NOT IN`] → colonnes de clés non nulles : pas de piège `NULL`.
- [« plus de 25 » sans total] → choix de l'issue #40, gardé par la réponse 1.
