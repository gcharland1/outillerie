# Proposal

Closes #49

## Why

L'issue #49 demande une passe d'uniformisation des couleurs du site : les actions courantes en bleu,
les actions dangereuses en rouge, le reste en gris, et le nom d'un utilisateur toujours en lien vers
ses outils. L'ADR 0019, en vigueur, interdit au contraire tout bouton rouge et laisse en gris
« Rechercher », « Filtrer » et « Voir plus » ; seuls certains noms (« Mes contacts », carte d'un
outil) sont des liens.

## What Changes

- Une nouvelle règle de couleurs pour tous les boutons, consignée dans l'ADR 0022 (`proposed`, remplace
  0019 à l'acceptation) : avancer en bleu, reculer ou dire non en gris, détruire en rouge. « Rechercher »,
  « Filtrer », « Voir plus », « Voir tous mes prêts », « Mes contacts » (accueil) et « Modifier »
  deviennent bleus ; « Retirer » (outil, contact), « Retirer ma demande », « Annuler le prêt » et leurs
  boutons de confirmation deviennent rouges. « Refuser » et « Pas reçu » restent gris. Jamais de vert
  sur un bouton.
- « Retirer ma demande » passe par une page de confirmation, comme toute action rouge, avec un champ
  « Raison » facultatif dont le texte s'ajoute au message de la demande.
- Un bouton d'envoi rouge garde son rouge : la règle de `site.css` qui grise les boutons d'envoi
  épargne `error` comme `primary`.
- Le nom d'un autre utilisateur mène à ses outils, sur la page du contact, quand c'est un contact ; son
  propre nom et le nom d'un non-contact (demande reçue, résultat de recherche, ex-contact d'un prêt)
  restent en texte. Une seule macro Jinja rend un nom, partout où le site en affiche un.
- Les liens gardent le bleu `--color-primary` (inchangé).
- `.claude/rules/templates.md` : ligne « Couleurs » réécrite d'après l'ADR 0022.

## Capabilities

### New Capabilities
- `interface` : règles d'affichage communes à toutes les pages : couleurs des boutons et des liens,
  rendu du nom d'un utilisateur.

### Modified Capabilities
- `demandes-d-emprunt` : « Ordre et couleurs de « Mes prêts » », qui renvoyait à l'ADR 0019, est scindé
  en « Ordre de « Mes prêts » » (inchangé) et « Couleurs des boutons de « Mes prêts » » selon l'ADR 0022
  (« Retirer ma demande » et « Annuler le prêt » en rouge).

## Impact

ADR 0022 (`proposed`, remplace 0019 ; son acceptation et le passage de 0019 à `superseded by 0022` se
font à l'archivage), `.claude/rules/templates.md`, `app/static/site.css`, `app/loans.py` (`BUTTONS`),
une fonction de `app/catalog.py` et un processeur de contexte de `app/contacts.py` (identifiants des
contacts), un nouveau gabarit de macro pour le nom, la plupart des gabarits sous `app/templates/`, et
les tests `test_navigation.py`, `test_loans.py`, `test_home.py`, `test_contacts.py`, `test_tools.py`,
`test_search.py`, `test_tools_of_contacts.py`. Aucun schéma, aucune dépendance.

Hors périmètre :
- une page publique pour un non-contact : son nom reste en texte, sa page répondant toujours 404 ;
- l'affichage grisé « Prénom Nom (supprimé) » d'un compte supprimé, ajouté à la macro par le
  changement `modification-du-profil`, livré après celui-ci dans la même branche ;
- la ligne du menu du compte de `.claude/rules/templates.md`, reprise par `retrait-du-nom-d-utilisateur` ;
- la couleur des états (« En retard », messages d'erreur et de succès, disponibilité), inchangée.
