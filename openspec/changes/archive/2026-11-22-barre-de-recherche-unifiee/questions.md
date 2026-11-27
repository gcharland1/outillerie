# Questions — barre de recherche unifiée

Issue traitée : #57 « Amélioration de barre de recherche », livrée en lot (`/traiter-issue lots`, ADR 0025).
Entrées : l'issue et son dernier commentaire de tri (`understood`), qui tranche les questions `utilisateur`.

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 1 | Compteur au-delà de 25 comptes ? | « 5 de plus de 25 », sans `COUNT` | Commentaire de l'utilisateur sur #57 | utilisateur |
| 2 | Message au-delà de 25 comptes ? | Texte actuel conservé (« Plus de 25 utilisateurs correspondent à « texte » ; précisez votre recherche »), affiché seulement après « Voir plus » | Commentaire de l'utilisateur sur #57 | utilisateur |
| 3 | Libellé du lien ? | « Voir plus », un seul libellé dans tout le site | Commentaire de l'utilisateur sur #57 | utilisateur |
| 4 | Demandes de contact en attente et filtre de relation ? | Rangées sous « Pas en contact uniquement » | Commentaire de l'utilisateur sur #57 | utilisateur |
| 5 | Sélecteur de distance ? | « Aucune limite » affiché, grisé, « à venir », sans effet | Commentaire de l'utilisateur sur #57 | utilisateur |
| 6 | `<n>` ? | 25 utilisateurs ; les outils n'ont pas de plafond ; « 6 de <n> » se lit « 6 de Y » | Spec recherche « Nombre de comptes listés » ; tri de #57 | convention |
| 7 | Structure ? | Blueprint `search` étendue ; cartes d'outils et recherche d'utilisateurs réutilisées | ADR 0011 ; tri de #57 | convention |
| 8 | Outils de la section ? | Outils visibles des contacts, triés par pertinence, comme « Trouver un outil » | Spec outils-des-contacts ; tri de #57 | convention |
| 9 | Utilisateurs de la section ? | Sans soi-même ni les comptes supprimés ; prénom et nom ; comptes non confirmés visibles | ADR 0023 ; spec recherche ; tri de #57 | convention |
| 10 | « Voir plus » des utilisateurs ? | Même page, par un paramètre d'URL, sans JavaScript ; vue dépliée : « X de X » ou « 25 de plus de 25 » | ADR 0001 ; tri de #57 | convention |
| 11 | « Voir plus » des outils ? | « Trouver un outil » avec le texte prérempli, sans « Disponible uniquement », tri par pertinence | Spec recherche ; tri de #57 | convention |
| 12 | « Voir tous mes prêts » de l'accueil ? | Devient « Voir plus » (libellé unique) | Réponse 3 ; tri de #57 | convention |
| 13 | Filtres ? | En tête de la section « Utilisateurs », sans effet sur les outils, visibles dès une recherche valide (même sans résultat), appliqués par un bouton « Filtrer » dans la requête, avant le plafond de 25 | Tri de #57 | convention |
| 14 | Valeur de filtre inconnue dans l'URL ? | « Tous les utilisateurs » ; le paramètre de distance est ignoré | Tri de #57 | convention |
| 15 | Moins de 3 caractères ? | Seulement « Saisissez au moins 3 caractères », sans les sections | ADR 0018 ; tri de #57 | convention |
| 16 | Messages vides ? | « Aucun résultat d'utilisateur » remplace « Aucun utilisateur ne correspond » ; « Aucun résultat d'outil », même sans contact | Issue ; tri de #57 | convention |
| 17 | Paramètre `type` ? | Ignoré, les anciens liens fonctionnent ; exigences de type retirées de la spec recherche | Tri de #57 | convention |
| 18 | Liens « ouvrez la recherche d'utilisateurs » ? | Deviennent « Cherchez un utilisateur avec la barre de recherche » | Specs accueil et outils-des-contacts ; tri de #57 | convention |
| 19 | Après « Envoyer une demande » depuis les résultats ? | Retour aux résultats avec le texte, le filtre et l'état déplié | Tri de #57 | convention |
| 20 | Après « Emprunter » depuis une carte des résultats ? | « Annuler » ramène à « Trouver un outil » avec le texte (provenance existante) | `application/app/loans.py` ; tri de #57 | convention |
| 21 | Vrai filtre de distance ? | Issue future, avec un ADR (géocodage, schéma, vie privée) | Tri de #57 | convention |
| 22 | Décision passée de #40 (« ni total, ni pagination, ni Voir plus ») ? | Remplacée par les réponses 1, 2 et 10 ; toujours ni pagination ni total exact au-delà de 25 | `openspec/changes/archive/2026-11-20-plafonner-la-recherche-d-utilisateurs/proposal.md:13-15` | utilisateur |
| 23 | Libellés du filtre de relation ? | « Tous les utilisateurs » (défaut), « Mes contacts uniquement », « Pas en contact uniquement » | Issue | dépôt |
| 24 | Condition SQL du filtre ? | Sous-requête des contacts (`catalog._contact_ids`), en `IN` / `NOT IN` ; les demandes en attente sont hors contacts | `application/app/catalog.py:316-321` | convention |
| 25 | État déplié falsifié ? | Seule la valeur `1` déplie ; toute autre vaut replié ; paramètre répété : première valeur | `request.args.get` ; motif de `loans._origin` | convention |
| 26 | Déplié avec 5 résultats ou moins ? | Sans effet : « X de X », pas de « Voir plus » | — | convention |
| 27 | Filtrer garde-t-il l'état déplié ? | Oui, champ caché, comme le retour après une demande (question 19) | Question 19 | convention |
| 28 | Retour après une demande : sécurité ? | Texte, filtre et état déplié relus du formulaire en liste blanche, URL construite par `url_for`, jamais reçue | `application/app/loans.py:426-434` | convention |
| 29 | Compte supprimé entre l'affichage et « Envoyer une demande » ? | Inchangé : 404 | `application/app/contacts.py:95-96` | dépôt |
| 30 | Filtre qui ne laisse aucun compte ? | « Aucun résultat d'utilisateur », sans compteur, filtre toujours affiché et sélectionné | Issue ; question 13 | convention |
| 31 | Formulaire « Filtrer » ? | GET, sans effet de bord ni jeton CSRF ; répète le texte et l'état déplié ; pas d'envoi automatique | ADR 0001 | convention |
| 32 | Sélecteur de distance ? | `select` désactivé avec étiquette « Dans un rayon de » et la mention visible « à venir » ; n'est pas envoyé | Question 5 | convention |
| 33 | Compte non confirmé qui cherche ? | Les cartes de la section grisent « Emprunter » comme ailleurs (mêmes cartes) | `application/app/catalog.py:266` | dépôt |
| 34 | Specs touchées ? | `recherche` (barre, sections, compteurs, filtres, retrait du type) ; `accueil` (« Voir plus », lien de recherche) ; `outils-des-contacts` (listes vides) ; `interface` (scénario « Voir plus en bleu ») | Specs principales | dépôt |
| 35 | Nouvel ADR ? | Aucun : ADR 0001, 0011, 0018, 0022, 0023 suivis | `docs/decisions/` | dépôt |
