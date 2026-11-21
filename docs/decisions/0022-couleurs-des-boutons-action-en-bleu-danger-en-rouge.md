---
status: accepted
date: 2026-11-20
decision-makers: Gabriel Charland
---

# Couleurs des boutons : action en bleu, action dangereuse en rouge, le reste neutre

## Contexte et problème

L'ADR 0019 a mis les actions positives en bleu et tout le reste en neutre, sans aucun bouton rouge ; il
notait déjà qu'une action destructrice n'était plus signalée par sa couleur. L'issue #49, ouverte après son
merge, demande l'inverse : les actions dangereuses en rouge, les actions courantes (« Rechercher »,
« Filtrer », « Emprunter ») en bleu, les autres en gris. Remplace 0019.
Changement OpenSpec : `openspec/changes/archive/2026-11-20-couleurs-des-boutons-et-liens/`.

## Options considérées

* Garder 0019 : positif en bleu, au plus un par groupe, rien en rouge
* Trois styles : action en bleu, action dangereuse en rouge, le reste neutre
* Vert pour accepter, rouge pour refuser ou retirer, le reste neutre

## Décision

Option retenue : « action en bleu, action dangereuse en rouge, le reste neutre », parce que l'issue #49 le
demande et que le rouge avertit avant une action qu'on ne peut pas défaire, là où 0019 ne la distinguait pas.

Règle : **avancer en bleu, reculer ou dire non en gris, détruire en rouge.**

* Bleu, `class="button primary"` : avancer, vers la suite de la tâche ou vers plus de contenu (rechercher,
  filtrer, voir plus, modifier, emprunter, accepter, enregistrer, envoyer, se connecter, créer un compte,
  déclarer une remise ou un retour). Au plus un bleu par groupe d'actions (`<div class="actions">`) ou par
  formulaire : quand deux boutons avancent, le principal est bleu, l'autre gris.
* Rouge, `class="button error"` : détruire, c'est-à-dire retirer, annuler ou supprimer ce qui existe (retirer
  un outil, retirer un contact, retirer sa demande, annuler un prêt, supprimer son compte), ainsi que le
  bouton qui ouvre la page de confirmation d'une telle action et celui qui la confirme.
* Gris, `class="button"` : reculer, quitter ou dire non (retour, « Annuler » qui abandonne un formulaire
  sans rien détruire, me déconnecter, refuser, « Pas reçu »), le second bouton d'un groupe qui a déjà son
  bleu, et tout bouton désactivé.
* Jamais `success` sur un bouton : le vert signale un état (message de succès, disponibilité).
* Le bleu est `--color-primary`, redéfini dans `app/static/site.css` (celui de Chota est vert) ; le rouge est
  `--color-error` de Chota. Les liens, menu du compte compris, prennent le bleu. Le logo reste neutre.
* Chota remplit tout bouton d'envoi (`type="submit"`) de la couleur primaire : `site.css` le rend neutre
  sauf s'il porte `primary` ou `error`.

### Conséquences

* Bon, parce qu'une action destructrice se reconnaît avant le clic.
* Bon, parce que la couleur se déduit encore du sens de l'action, sans comparer avec les autres pages.
* Mauvais, parce que le rouge sert désormais aussi aux états (erreur, prêt en retard) : un bouton et un
  message d'erreur partagent la couleur.
* Mauvais, parce que « Refuser » et « Pas reçu », irréversibles et sans page de confirmation, restent gris :
  ils disent non sans rien détruire.
* Mauvais, parce que chaque gabarit et le test de 0019 (`test_no_button_is_red_or_green`) sont à reprendre.
