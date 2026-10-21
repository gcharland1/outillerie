---
status: accepted
date: 2026-10-21
decision-makers: Gabriel Charland
---

# Diagramme du schéma généré par paracelsus

## Contexte et problème

Les modèles SQLAlchemy sont la source du schéma (0007). Pour le lire d'un coup d'œil, il faut un
diagramme entité-relation qui ne puisse pas diverger des modèles. Changement OpenSpec :
`openspec/changes/schemas-initiaux/`.

## Options considérées

* paracelsus : lit les modèles, écrit un diagramme Mermaid dans un fichier Markdown
* eralchemy : lit les modèles ou la base, produit une image via Graphviz
* SchemaSpy ou l'ERD de DBeaver et pgAdmin : lisent la base migrée

## Décision

Option retenue : « paracelsus », parce qu'il lit les modèles sans base ni Graphviz, que GitHub
affiche le Mermaid sans outil, et que `paracelsus inject --check` échoue quand `docs/schema.md`
n'est plus à jour : l'étape tourne dans `/verifier` et en CI. Dépendance de développement
seulement.

### Conséquences

* Bon, parce que le diagramme est du texte relu dans les PR, et toujours à jour.
* Mauvais, parce qu'il montre ce que déclarent les modèles, pas ce que les révisions Alembic ont
  réellement créé ; une contrainte ajoutée seulement dans une révision n'y paraît pas.
* Mauvais, parce qu'il ajoute une dépendance et une étape de vérification.
