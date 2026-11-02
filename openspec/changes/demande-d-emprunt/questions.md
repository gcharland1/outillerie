# Questions — demande-d-emprunt (issue #29, second changement)

Suite de `openspec/changes/archive/2026-11-01-consulter-les-outils-des-contacts/` (questions.md #1 :
la demande d'emprunt a été scindée de la consultation). Réponses fusionnées des agents Code, Specs et
ADR, Cas limites, Antériorité (2026-11-01).

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 1 | Dates de la demande ? | En suspens. `start_date`/`end_date` NOT NULL ; le statut « En attente de prêt » et l'exclusion GiST reposent sur les dates. Recommandé : champs « Du / Au » obligatoires. | Sourced `application/models/loan.py:23-24,44-52` ; `application/app/catalog.py:187-195` | utilisateur |
| 2 | Message au propriétaire : stockage, traitement ? | Colonne `loan.message` nullable, ajout « expand » (ADR 0007) ; `strip()`, vide → NULL, `maxlength` + contrôle serveur, affichage échappé avec `white-space: pre-line`, jamais dans une URL, un flash ou un log. | Sourced ADR 0007 ; `application/app/tools.py:12,229,233-234` | convention |
| 3 | Longueur maximale du message ? | En suspens. Aucune source ; 500 proposé. | No basis | utilisateur |
| 4 | Forme de la notification ? | En suspens. Seul précédent : pastille calculée (context processor), courriel exclu pour les contacts ; table ou courriel ⇒ ADR. | Sourced `application/app/contacts.py:18-27` ; `liste-de-contacts/proposal.md` | utilisateur |
| 5 | Périmètre : page du propriétaire (accepter / refuser), annulation par l'emprunteur ? | En suspens. Sans page, une demande bloque l'outil jusqu'à sa fin sans recours. Cycle approuvé le 2026-10-21 : `requested → accepted → lent → returned`, `requested → refused`, `accepted → canceled`. | Sourced `docs/sessions/2026-10-21-41172e1f.md:1426-1443` ; `schemas-initiaux/proposal.md:63-65` | utilisateur |
| 6 | Demandes concurrentes ? | Une demande ouverte par outil, de fait : toute demande ouverte rend l'outil « En attente de prêt » et grise « Emprunter ». Vérifié au POST sous verrou de la ligne `tool` ; aucune contrainte en base (« ouverte » dépend de la date). Le scénario `prets` « Demandes concurrentes » reste vrai pour les données. | Sourced `openspec/specs/prets/spec.md:63-66` ; `outils-des-contacts/spec.md:100-103` ; `contacts.py:165-172` | convention |
| 7 | Outil devenu indisponible, double clic, deuxième onglet, retour arrière ? | GET et POST revérifient « visible et disponible » ; sinon flash « Cet outil n'est plus disponible » et retour à la liste d'origine ; PRG ; `no-store` déjà global. | Sourced `tools.py:195-198` ; `contacts.py:184-192` ; `app/__init__.py:40-45` | convention |
| 8 | Ce que voit l'emprunteur après l'envoi ? | En suspens. Statut identique pour tous aujourd'hui ; précédent « Demande envoyée » grisé dans la recherche ; `base.html` affiche tout flash comme une erreur. | Sourced `catalog.py:128-146` ; `search/results.html:27-28` ; `base.html:67-69` | utilisateur |
| 9 | Retour à la liste d'origine ? | Origine énumérée `from` (`find` ou `contact`), `q`, `available` ; id du contact = `tool.owner_id` ; URL par `url_for` ; valeur inconnue ou contact perdu ⇒ `tools.find`. | Sourced archive questions.md:28,86 ; `contacts.py:59` | convention |
| 10 | « Annuler » sur la confirmation ? | Lien-bouton vers l'origine, rien n'est écrit (pas de `canceled`). | Sourced `templates/tools/confirm_retire.html:19` ; archive questions.md:29 | convention |
| 11 | Retrait de l'outil, passage « Hors d'usage », retrait du contact pendant une demande ? | En suspens. Rien n'est prévu aujourd'hui ; règle reportée explicitement à ce changement. | Sourced `contacts.py:108-116` ; `tools.py:84-107,130-140` ; `gestion-des-outils/proposal.md:72-73` | utilisateur |
| 12 | Dates passées ? | Refuser « Du » avant aujourd'hui (`site_today()`, America/Toronto) et « Au » avant « Du », par flash avec champs conservés ; dates lues en ISO (`date.fromisoformat`), vides ou invalides refusées. | Sourced `catalog.py:26-27,149-150` ; `loan.py:44` | convention |
| 13 | Durée maximale, horizon de réservation ? | En suspens. Aucune règle. | No basis | utilisateur |
| 14 | Outil « À réparer » ? | Empruntable, état affiché sur la confirmation. | Sourced archive questions.md:66-67 | dépôt |
| 15 | Accès, CSRF, son propre outil ? | Même 404 au GET et au POST pour un outil inconnu, à soi, d'un non-contact, retiré ou hors d'usage (conditions de `visible_tools`) ; jeton CSRF ; test `csrf_client`. | Sourced `catalog.py:78-107` ; `app/__init__.py:23` ; `tests/conftest.py:124-128` | dépôt |
| 16 | Prêt accepté pour des dates futures : bloque-t-il une demande pour demain ? | Oui, par la décision #5 de l'archive (« tout prêt ouvert bloque »). | Sourced archive questions.md:58-59 | utilisateur (reconfirmer) |
| 17 | Acceptation en conflit avec un prêt engagé ? | `IntegrityError` de `excl_loan_tool_dates` interceptée, rollback, flash « Ces dates ne sont plus libres ». | Sourced `loan.py:46-52` ; `contacts.py:68-72` | convention |
| 18 | Demande sans réponse dont la fin est passée ? | En suspens (affichage, acceptation tardive). Elle cesse de bloquer mais reste `requested` ; pas de tâche planifiée (ADR). | Sourced `catalog.py:187-195` | utilisateur |
| 19 | Qui lit le message ? | Propriétaire et emprunteur seulement ; jamais sur une carte ni ailleurs ; exigence + test. | Inferred de `outils-des-contacts/spec.md:67-81` (notes privées) | convention |
| 20 | Contenu de la confirmation ? | Nom, photo, description entière, état, « Prénom Nom » du propriétaire ; « Message pour <Prénom Nom> (facultatif) » ; jamais les notes privées. | Inferred de l'issue et de `_cards.html:19` | convention |
| 21 | Bouton « Emprunter » ? | `<a class="button primary">` vers la confirmation si « Disponible », `<button disabled>` sinon ; « Bientôt disponible » retiré ; MODIFIED « Carte d'un outil ». | Sourced `_cards.html:23-26` ; `.claude/rules/templates.md` | convention |
| 22 | Blueprint, routes ? | `app/loans.py`, Blueprint `loans` (`/loans`) : `GET/POST /loans/new/<tool_id>` ; actions du propriétaire et de l'emprunteur selon #5. | Sourced ADR 0011:13,28 ; `app/__init__.py:25-31` | convention |
| 23 | Capacité OpenSpec ? | Nouvelle `demandes-d-emprunt` (parcours et transitions ; `prets` garde les invariants de données) ; MODIFIED dans `outils-des-contacts` et, selon les réponses, `contacts`, `inventaire`. | Inferred des noms dans `openspec/specs/` | convention |
| 24 | ADR 0017 ? | Seulement pour dates nullables, table de notifications, courriel ou JavaScript. | Sourced `docs/decisions/README.md:8-9` | convention |
| 25 | Session expirée pendant la saisie ? | Saisie perdue, comportement déjà accepté pour les formulaires d'outil. | Sourced `gestion-des-outils/proposal.md:76-78` | dépôt |
| 26 | Tests et fixtures ? | `make_loan` dans `tests/factories.py` (trois `add_loan` en double aujourd'hui) ; `tests/test_loans.py` ; `/loans` dans `test_no_page_says_voisin`. | Sourced `tests/test_loan_model.py:31`, `test_catalog.py:32`, `test_tools_of_contacts.py:59` | convention |
| 27 | Migration ? | Une révision `flask db migrate` (nom ASCII) pour `loan.message` ; `docs/schema.md` régénéré ; `test_schema` inchangé (aucune contrainte nommée). | Sourced ADR 0007:46 ; `.claude/rules/migrations.md` | convention |

## Réponses de l'utilisateur

- #5 : demande, réponse, retrait. L'emprunteur crée la demande et peut la retirer
  (`requested → canceled`, élargit le cycle approuvé le 2026-10-21) ; le propriétaire accepte ou refuse
  sur une page « Mes prêts » du menu du compte, qui liste aussi les demandes de l'emprunteur. Remise
  (`lent`), retour (`returned`) et annulation d'un prêt accepté : changement suivant.
- #1 : champs « Du » et « Au » obligatoires sur la confirmation, « Du » prérempli à aujourd'hui ;
  aucune migration des dates, aucun ADR.
- #11 : annuler automatiquement. Au retrait de l'outil, à son passage « Hors d'usage » ou au retrait du
  contact, les demandes `requested` concernées passent à `canceled` dans la même transaction ; les
  confirmations de retrait l'annoncent. MODIFIED dans `inventaire` et `contacts`.
- #4 : pastille sur « Mes prêts » (demandes d'emprunt en attente reçues) ; la pastille du nom
  d'utilisateur devient le total contacts + emprunts (MODIFIED « Pastille des demandes en attente »).
  Pas de courriel, pas d'ADR.
- #16 : règle gardée. Une demande ou un prêt ouvert à la fois par outil ; une réservation future bloque
  jusqu'à sa fin.
- #8 : carte + message de succès. Sur sa propre demande, l'emprunteur voit « Demande envoyée » grisé ;
  les autres « En attente de prêt ». Message vert « Demande envoyée à <Prénom Nom> » : catégories de
  flash (succès / erreur) dans `base.html` et `site.css`, pour tout le site.
- #18 : expirée après son début. Une demande `requested` dont le premier jour est passé sans réponse est
  « Expirée » : plus d'acceptation, plus dans la pastille. Conséquence (convention, Inferred) : une
  demande expirée n'attend plus de réponse, elle cesse donc de bloquer l'outil le lendemain de son
  début (`requested` bloque tant que `start_date >= aujourd'hui`, au lieu de `end_date`) ; MODIFIED
  de « Statut de prêt » dans `outils-des-contacts`.
- #3, #13 : message de 500 caractères au plus ; prêt de 30 jours au plus (« 1 mois ») ; « Du » au plus
  tard 14 jours après aujourd'hui (« 2 sem. »). Réponse « 500 car. 1 mois, 2 sem. » lue dans l'ordre
  message, durée, horizon ; mois compté comme 30 jours.

## Ajouts à la rédaction et à la grille

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 28 | Nom de la page et libellés ? | « Mes prêts » (menu du compte) ; statuts « En attente », « Expirée », « Acceptée », « Refusée », « Annulée », « Prêté », « Rendu » ; action « Retirer ma demande ». | Inferred de #5 et du précédent « Mes contacts » | convention |
| 29 | Messages ? | « Cet outil n'est plus disponible », « Cette demande n'est plus en attente » (repris des contacts), « Ces dates ne sont plus libres », « Demande envoyée à <Prénom Nom> » ; messages de dates de la spec. | Inferred de `contacts.py` (`NO_LONGER_PENDING`) | convention |
| 30 | Annonce des annulations sur les confirmations de retrait ? | « N demande(s) d'emprunt en attente … sera / seront annulée(s) », seulement s'il y en a. | Inferred de #11 | convention |
| 31 | Demandes déjà expirées au moment d'un retrait ? | Laissées telles quelles (« Expirée ») ; seules les demandes non expirées sont annulées. | Inferred de #18 et #11 | convention |
