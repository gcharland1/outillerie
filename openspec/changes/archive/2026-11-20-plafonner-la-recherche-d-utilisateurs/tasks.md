## 1. Plafond

- [x] 1.1 `USER_RESULTS_MAX = 25` et `.limit(USER_RESULTS_MAX + 1)` dans `_matching_users` ; la vue coupe à 25 avant `relation_states` et affiche le message au-delà ; tests pytest de « Plus de 25 comptes », « Exactement 25 comptes » et « Correspondances exactes gardées »
- [x] 1.2 Test : le texte cherché du message est échappé (`<b>` affiché tel quel)

## 2. Fin

- [x] 2.1 `/verifier` rend « terminé »
