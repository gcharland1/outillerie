# Blocage — livraison en lot de #61 et #65

**Étape** : gate 13 (relecture), premier passage ; arrêt du lot par `/traiter-issue` § Lots point 3
(ADR que le commentaire de tri n'annonçait pas).

**Cause** : la règle décidée sur #61, « toute action irréversible ou dangereuse passe par une page de
confirmation » (`.claude/rules/templates.md`), contredit l'ADR 0022, `accepted`, qui accepte dans ses
conséquences que « Refuser » (demande de contact, demande d'emprunt) et « Pas reçu », irréversibles,
restent sans page de confirmation. Un ADR accepté est immuable : appliquer la règle demande un nouvel
ADR qui remplace l'ADR 0022 sur ce point, et des pages de confirmation pour ces actions (ou des
exceptions nommées). Le tri de #61 annonçait « ADR à écrire : aucun ».

À trancher par l'utilisateur, en commentaire sur #61 :
- A : nouvel ADR, et pages de confirmation pour « Refuser » et « Pas reçu », dans ce changement ou dans
  une issue à part ;
- B : la règle nomme ces exceptions (« Refuser » et « Pas reçu » restent sans confirmation), sans ADR ;
- C : la règle vise seulement les actions dangereuses (retrait, suppression, effacement, déconnexion de
  tous les appareils), sans ADR.

**Ce qui est fait** : branche `worktree-lot-issue-61`, commit « Profil - Déconnecter tous mes
appareils » (action, gabarits, tests, spec du changement, règle des gabarits). `/verifier` : ruff,
format, migrations, schéma, specs OK ; suite complète 848 réussis et 1 échec corrigé
(`DESTRUCTIVE_LABELS` de `test_navigation.py`). Aucune PR.

**Autres constats de la relecture, à corriger à la reprise** :
- La puce des couleurs de `.claude/rules/templates.md` doit nommer la déconnexion de tous les appareils
  parmi les boutons rouges (ADR 0022 met « me déconnecter » en gris).
- `profile.logout_all` : lire courriel, prénom et confirmation par `RETURNING` dans l'`UPDATE`, pour
  qu'une suppression concurrente ne laisse pas un faux échec d'envoi au journal.
- Tests : lien vers `/login` de la page `all-devices`, aucun compte modifié par un POST sans session,
  texte de la section.
- Avis : retirer « à votre demande », qui contredit la phrase suivante.
- Rebaser sur `origin/main` (PR #66 mergée depuis le départ de la branche).

**#65** (notifications par courriel) : groupée dans le même lot (même code : `profile.py`, `auth.py`,
`mail.py`, règle des gabarits ; l'avis de #61 entre dans sa règle des envois synchrones) ; non commencée.
