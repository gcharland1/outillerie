# Questions — gestion-des-prets (issue #35)

Suite de `openspec/changes/archive/2026-11-04-demande-d-emprunt/` (questions.md #5 : remise, retour et
annulation d'un prêt accepté reportés à ce changement). Réponses fusionnées des agents Code, Specs et
ADR, Cas limites, Antériorité (2026-11-12).

Constat commun : aucune route n'écrit `lent` ni `returned` (grep `app/`) ; un prêt `accepted` jamais
récupéré cesse de bloquer l'outil après sa fin mais reste « Acceptée » pour toujours
(`application/app/catalog.py:237`, `application/app/loans.py:256-261`).

Piège de vocabulaire : dans le cycle approuvé le 2026-10-21, « remis » voulait dire « l'emprunteur a pris
l'outil » (devenu `lent`) ; dans l'issue, « Remis » veut dire « l'emprunteur déclare l'avoir rendu »
(`docs/sessions/2026-10-21-41172e1f.md:1426-1443`).

| # | Question | Réponse | Source | Décidé par |
|---|----------|---------|--------|------------|
| 1 | Statuts : liste finale, nouvelle valeur pour le retour déclaré, libellés ? | En suspens. Correspondance : Demande envoyée = `requested` (+ « Expirée » calculée), Attente de récupération = `accepted`, Prêté = `lent`, Complété = `returned`, Refusé = `refused`, Annulée = `canceled`. Le retour déclaré n'a pas de valeur : en ajouter une (`return_claimed`). Libellé « Remis » ambigu ; proposé « Retour à confirmer ». | Sourced `application/models/loan.py:10-16` ; `loans.py:29-37` ; session 2026-10-21:1426-1443 | utilisateur |
| 2 | Transitions : qui fait quoi ? | En suspens. Livré : `requested → accepted / refused` (propriétaire), `requested → canceled` (emprunteur, ou cascade). Proposé : propriétaire `accepted → lent` ; emprunteur `lent → return_claimed` ; propriétaire `lent / return_claimed → returned` (l'issue permet de sauter le retour déclaré) ; propriétaire `return_claimed → lent` (« Pas encore reçu ») pour un désaccord. | Sourced `loans.py:127-162` ; archive demande-d-emprunt questions.md:39-42 ; issue #35 | utilisateur |
| 3 | Annulation d'un prêt accepté ou en cours ? | En suspens. `accepted → canceled` approuvé le 2026-10-21 sans acteur, reporté deux fois. Proposé : l'une ou l'autre partie annule un `accepted` ; un `lent` ne s'annule jamais, il se termine par `returned`. | Sourced session 2026-10-21:1428-1430 ; archive demande-d-emprunt proposal.md:71 | utilisateur |
| 4 | Retard : à partir de quand, calculé ou planifié ? | Calculé à la lecture : `lent` et `end_date < site_today()` (lendemain du dernier jour, fuseau America/Toronto), une expression partagée sur le modèle de `pending_request()`. Pas de tâche planifiée (elle exigerait un ADR). | Sourced session 2026-10-21:1383,1435 ; `catalog.py:28,190-191,228-230` ; `openspec/specs/prets/spec.md:24-25` | dépôt |
| 5 | Notification de retard et de retour : forme, destinataires ? | En suspens. Seul mécanisme : pastille calculée (context processor) ; courriel écarté deux fois, il exigerait dépendance, SMTP, secrets, tâche planifiée et ADR. Proposé : pastille de « Mes prêts » élargie (propriétaire : demandes en attente, retours à confirmer, retards ; emprunteur : ses retards) ; total du nom d'utilisateur suit. | Sourced `loans.py:49-54` ; `base.html:1-3,44,49` ; archive demande-d-emprunt questions.md:48-50 ; archive liste-de-contacts proposal.md:27-28 | utilisateur |
| 6 | « Mes prêts » : ordre, actions, titres de section ? | En suspens. Aujourd'hui : actionnables puis autres, `created_at` décroissante ; sections « Demandes reçues » / « Mes demandes ». Le design prévoyait qu'un prêt avec action rejoigne le premier groupe. Proposé : retards (fin la plus ancienne d'abord), puis actionnables, puis autres ; sections « Mes prêts » / « Mes emprunts ». | Sourced `loans.py:104-124,251-253` ; `mine.html:3-53` ; archive demande-d-emprunt design.md:79-87 | utilisateur |
| 7 | Schéma : CHECK, exclusion, migration ? | Une révision après `13db5eeed32b` qui recrée `ck_loan_loan_status` avec la nouvelle valeur, écrite à la main (l'autogénération ne voit pas les CHECK), `downgrade` fonctionnel (ramène `return_claimed` à `lent`), `docs/schema.md` régénéré. | Sourced ADR 0007:29-46 ; `models/loan.py:25-55` ; `.claude/rules/migrations.md` | convention |
| 8 | Horodatages des transitions (`lent_at`, `returned_at`…) ? | En suspens. Seul `created_at` existe. Colonnes nullables = expand, sans ADR. Utiles seulement pour afficher « rendu le … » ou un historique. | Sourced `models/loan.py:40` ; ADR 0007 | utilisateur |
| 9 | Blocage : les états « à confirmer » bloquent-ils l'outil ? | Oui. `handover_claimed` et `return_claimed` bloquent comme `lent`, sans limite de date, jusqu'à confirmation ou « Pas reçu » : l'outil est peut-être chez l'emprunteur. Ajoutés à `blocking_loan()` et à l'exclusion `excl_loan_tool_dates`. `lent` en retard bloque toujours ; `accepted` bloque jusqu'à sa fin. | Inferred de `catalog.py:233-239`, `models/loan.py:53` et de l'issue (le prêteur doit confirmer) | convention |
| 10 | Retrait de l'outil, « Hors d'usage », retrait du contact pendant un prêt `accepted` ou `lent` ? | En suspens, ouvert depuis le 2026-10-21. Aujourd'hui seules les demandes en attente sont annulées. Proposé : annuler aussi les `accepted` (annoncé sur les confirmations) ; ne jamais annuler un `lent` ni un `return_claimed`. | Sourced `catalog.py:112-145` ; `tools.py:100-101,141-142` ; `contacts.py:119` ; session 2026-10-21:3720 ; session 2026-11-02:33712 | utilisateur |
| 11 | Actions sur un prêt d'un outil retiré ou d'un ex-contact ? | Les actions de « Mes prêts » vérifient l'acteur et le statut, jamais la visibilité de l'outil ni le lien de contact : un prêt en cours reste toujours clôturable. | Sourced `loans.py:107-120` ; Inferred de #10 | convention |
| 12 | Prêt `accepted` jamais remis dont la fin est passée ? | En suspens. Proposé : libellé calculé (« Non récupéré » ou « Expirée »), sans action ni écriture en base, comme une demande expirée. Couvre aussi les `accepted` déjà en production. | Sourced `catalog.py:237` ; `loans.py:256-261` ; archive demande-d-emprunt questions.md #18 | utilisateur |
| 13 | Remise (`accepted → lent`) avant la date de début ? après la fin ? | En suspens. Aucune règle. Proposé : permise dès l'acceptation, jusqu'à la fin ; dates inchangées. | No basis | utilisateur |
| 14 | Retour déclaré après la date de fin : encore « En retard » ? | En suspens. Proposé : non ; il attend la confirmation du propriétaire (pastille). | No basis | utilisateur |
| 15 | Prolongation, modification des dates, retour anticipé ? | En suspens. Retour anticipé permis de fait (`returned` avant la fin libère, `prets/spec.md:73-76`). Proposé : prolongation et modification hors périmètre. | Sourced `prets/spec.md:73-76` ; No basis pour la prolongation | utilisateur |
| 16 | Erreurs, concurrence, accès, CSRF ? | Généraliser `_pending_loan` (verrou `FOR UPDATE`, rôle et statuts de départ) ; 404 identique pour inconnu et tiers ; statut changé ⇒ flash « Ce prêt a déjà changé de statut » et retour à « Mes prêts » ; PRG ; CSRF global (400). Tests : double envoi, deux onglets, tiers, mauvais rôle, jeton absent. | Sourced `loans.py:26,133-140,232-244,264-267` ; `app/__init__.py:51-53` ; `demandes-d-emprunt/spec.md:164-202` | convention |
| 17 | Vie privée ? | Message et retard visibles seulement des deux parties ; la carte vue par les tiers garde « Prêté jusqu'au <date> » même en retard (scénario « Prêt en retard » inchangé), sans nom d'emprunteur ; aucune journalisation. | Sourced `outils-des-contacts/spec.md:110-122` ; `catalog.py:250-271` ; `demandes-d-emprunt/spec.md:76-91` | dépôt |
| 18 | Capacité OpenSpec ? | Nouvelle `suivi-des-prets` (remise, retour déclaré, confirmation, annulation, retard, actions par rôle) ; MODIFIED : `prets` « Statut du prêt », « Aucun chevauchement des prêts engagés » ; `demandes-d-emprunt` « Page « Mes prêts » », « Ordre et couleurs de « Mes prêts » », « Pastille des demandes d'emprunt » ; `contacts` « Pastille des demandes en attente » et, selon #10, « Retrait d'un contact » ; `inventaire` selon #10 ; `outils-des-contacts` « Statut de prêt ». | Inferred de `demandes-d-emprunt/spec.md:3-5`, `prets/spec.md:3-5` et du précédent archive demande-d-emprunt questions.md #23 | convention |
| 19 | ADR 0018 ? | Pas d'ADR si retard calculé, pastille, CHECK élargi et colonnes nullables (ADR 0007, précédent `loan.message`). ADR requis pour courriel, tâche planifiée, table de notifications ou JavaScript. Proposal cite ADR 0001, 0002, 0007, 0011, 0012, 0013, 0017. | Sourced `docs/decisions/README.md:8-9` ; archive demande-d-emprunt proposal.md:65-66 | convention |
| 21 | Pastille de l'emprunteur pour une remise à confirmer ? | Oui : celui qui reçoit l'outil confirme, la remise à confirmer attend donc l'action de l'emprunteur comme le retour à confirmer attend celle du propriétaire. | Inferred des réponses #2 et #5 | convention |
| 22 | Libellés des boutons ? | Donneur : « J'ai remis l'outil » (propriétaire), « J'ai rendu l'outil » (emprunteur). Receveur : « J'ai reçu l'outil » sans déclaration, « Confirmer la réception » et « Pas reçu » sur une déclaration ; « Annuler le prêt ». Rouge : « Refuser », « Annuler le prêt », « Pas reçu ». | Inferred de la réponse #2 et de `.claude/rules/templates.md` | convention |
| 20 | Tests et fixtures ? | `make_loan` accepte déjà `status` ; tests à adapter : libellé « Rendu », « Prêté jusqu'au » ; `test_schema` si l'exclusion change. | Sourced `tests/factories.py:43-54` ; `tests/test_catalog.py:100-117` ; `tests/test_schema.py:21` | convention |

## Réponses de l'utilisateur

- #5 : pastille seule. La pastille de « Mes prêts » compte aussi, pour le propriétaire, les retours à
  confirmer et les prêts en retard ; pour l'emprunteur, ses prêts en retard. Le total du nom d'utilisateur
  suit. Pas de courriel, pas de table de notifications, pas d'ADR.
- #2 : celui qui donne l'outil déclare, celui qui le reçoit confirme ou change lui-même le statut.
  - Remise : le propriétaire déclare l'avoir remis (`accepted → handover_claimed`), l'emprunteur confirme
    (`handover_claimed → lent`) ; sans déclaration, l'emprunteur passe lui-même `accepted → lent`.
  - Retour : l'emprunteur déclare l'avoir rendu (`lent → return_claimed`), le propriétaire confirme
    (`return_claimed → returned`) ; sans déclaration, le propriétaire passe lui-même `lent → returned`.
  - Conséquence (Inferred) : deux valeurs nouvelles, `handover_claimed` et `return_claimed` ; le donneur
    ne passe jamais lui-même à l'état final.
- #2 bis (désaccord) : le receveur peut répondre « Pas reçu » : `handover_claimed → accepted`,
  `return_claimed → lent`. Le donneur peut déclarer de nouveau. Aucun suivi de litige.
- #10 : annuler les prêts pas encore remis. Au retrait de l'outil, au passage « Hors d'usage » ou au
  retrait du contact, les prêts `accepted` et `handover_claimed` concernés passent à `canceled` dans la même
  transaction, annoncés sur la page de confirmation. `lent` et `return_claimed` ne sont jamais annulés et
  restent clôturables depuis « Mes prêts ».
- #3 : l'une ou l'autre partie annule un prêt `accepted` ou `handover_claimed`, par une page de
  confirmation ; il devient `canceled` et libère les dates. Un `lent` ne s'annule jamais.
- #12 : un prêt `accepted` dont la date de fin est passée s'affiche « Expirée » (même libellé que la
  demande sans réponse), sans action, sans écriture en base, et ne bloque plus l'outil ; couvre les
  `accepted` déjà en production. Un `handover_claimed` est traité comme remis : toujours actionnable,
  en retard après sa date de fin.
- #13 : remise permise dès l'acceptation, jusqu'au dernier jour du prêt ; les dates ne changent pas.
- #14 : un `return_claimed` n'est pas en retard ; il compte dans la pastille du propriétaire comme retour
  à confirmer. Ramené à `lent` par « Pas reçu », il redevient en retard si sa fin est passée.
- #1 : libellés de « Mes prêts » : En attente (`requested`) · Expirée (`requested` ou `accepted` passé) ·
  Attente de récupération (`accepted`) · Remise à confirmer (`handover_claimed`) · Prêté (`lent`) ·
  En retard (`lent` passé, calculé) · Retour à confirmer (`return_claimed`) · Complété (`returned`) ·
  Refusée (`refused`) · Annulée (`canceled`). Le mot « Remis » seul n'est pas employé.
- #6 : deux listes, « Mes prêts » (outils que je prête) et « Mes emprunts ». Dans chacune : prêts en
  retard d'abord (date de fin la plus ancienne d'abord), puis les lignes où j'ai une action, puis le
  reste, chaque groupe de la plus récente à la plus ancienne selon la date d'envoi.
- #8 : colonnes nullables `lent_at` et `returned_at` (expand, ADR 0007), écrites par les transitions vers
  `lent` et `returned` ; « Mes prêts » affiche « Prêté le … » et « Complété le … ».
- #15 : prolongation et modification des dates hors périmètre ; le retour anticipé reste permis.
- #3 et #10 révisés (grille, 2026-11-12) : une remise à confirmer est traitée partout comme une remise
  faite : ni « Annuler le prêt », ni annulation en cascade. Le receveur répond « Pas reçu » (retour à
  « Attente de récupération », annulable) ou confirme. Seuls les `accepted` non expirés s'annulent.
- Relecture (2026-11-12) : la cascade n'annule que les prêts acceptés non expirés (un `accepted` expiré
  reste « Expirée ») ; une remise à confirmer contestée (« Pas reçu ») devient `canceled` si l'outil est
  retiré ou « Hors d'usage », ou si les deux ne sont plus en contact, au lieu de redevenir `accepted`.
