---
status: accepted
date: 2026-10-20
decision-makers: Gabriel Charland
---

# Consigner les décisions avec MADR

## Contexte et problème

Le projet est développé en grande partie avec Claude Code. Sans trace écrite, les choix
d'architecture se perdent d'une session à l'autre et Claude ne peut pas les respecter.

## Options considérées

* MADR 4.0, fichiers Markdown dans `docs/decisions/`
* adr-tools (CLI bash, format Nygard)
* log4brains (site statique, Node)
* Pas d'ADR, seulement le README et l'historique git

## Décision

Option retenue : « MADR 4.0 », parce que c'est du Markdown pur, sans outil à installer,
lisible par Claude et révisable en PR. Le skill `/adr` remplace la CLI.

### Conséquences

* Bon, parce que chaque session peut lire les décisions en vigueur.
* Mauvais, parce que la numérotation et l'index sont maintenus à la main (atténué par `/adr`).
