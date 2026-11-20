---
status: accepted
date: 2026-11-20
decision-makers: Gabriel Charland
---

# Couleurs des boutons : positif en bleu, négatif en neutre

## Contexte et problème

Chaque page a choisi ses couleurs de bouton : « Accepter » / « Refuser » sont bleu / neutre pour
une demande de contact mais vert / rouge pour une demande d'emprunt, les actions de retrait sont
rouges, les boutons de connexion et d'inscription n'ont pas de classe. La relecture de la PR #43
(issue #44) a relevé l'écart ; l'utilisateur demande une règle unique pour tout le site.
Changement OpenSpec : `openspec/changes/suites-de-la-page-d-accueil/`.

## Options considérées

* Deux styles de bouton selon le sens de l'action : positif en bleu (`primary`), négatif en neutre
* Trois styles : positif en vert (`success`), négatif en rouge (`error`), le reste neutre
* Couleur au cas par cas, avec le rouge réservé aux actions dangereuses (règle de `.claude/rules/templates.md`)

## Décision

Option retenue : « positif en bleu, négatif en neutre », parce qu'un seul style d'accent désigne
sans ambiguïté l'action attendue sur chaque écran, et que le rouge reste libre pour signaler un
état (erreur, retard) plutôt qu'une action.

Règles :

* Positif, `class="button primary"` : l'action qui fait avancer ce que l'utilisateur est venu
  faire (accepter, confirmer, enregistrer, emprunter, envoyer, se connecter, créer un compte,
  déclarer une remise ou un retour). Sur une page de confirmation, le bouton qui confirme est
  positif, même pour un retrait ou une annulation.
* Négatif, `class="button"` : refuser, annuler, retirer, revenir, signaler un problème
  (« Pas reçu »), et l'action qui ouvre la confirmation d'un retrait ou d'une annulation.
* Neutre aussi, `class="button"` : navigation et outils de page (« Voir plus », « Filtrer »,
  « Rechercher », « Modifier », « Me déconnecter »).
* Au plus un bouton positif par groupe d'actions (`<div class="actions">`) ou par formulaire.
* Aucun bouton rouge (`error`) ni vert (`success`) : ces couleurs signalent un état (message
  d'erreur ou de succès, prêt en retard, disponibilité).
* Le bleu est `--color-primary`, redéfini dans `app/static/site.css` (celui de Chota est vert) ;
  les liens, menu du compte compris, prennent ce même bleu. Le logo de la navigation reste neutre.
* Chota remplit tout bouton d'envoi (`type="submit"`) de la couleur primaire : `site.css` le rend
  neutre sauf s'il porte `primary`.

### Conséquences

* Bon, parce que la couleur d'un bouton se déduit du sens de l'action, sans comparer avec les
  autres pages.
* Bon, parce que les tests vérifient une seule classe pour une action positive.
* Mauvais, parce qu'une action destructrice n'est plus signalée par sa couleur : la page de
  confirmation (retrait d'un outil, d'un contact, annulation d'un prêt) porte seule l'avertissement.
* Mauvais, parce qu'une action irréversible sans page de confirmation (« Refuser », « Pas reçu »)
  n'a pas d'avertissement visuel.
