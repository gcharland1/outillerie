---
status: accepted
date: 2026-10-20
decision-makers: Gabriel Charland
---

# OpenSpec pour le développement piloté par spec

## Contexte et problème

Avec Claude Code, une fonctionnalité demandée en une phrase produit du code dont l'intention
n'est écrite nulle part. Il faut que chaque changement parte d'une spec relue avant le code,
et que les specs reflètent toujours le comportement actuel.

## Options considérées

* OpenSpec (`openspec/specs/` + `openspec/changes/`, commandes `/opsx:*`)
* GitHub spec-kit (constitution + ~9 skills `/speckit-*`)
* BMAD-METHOD
* Specs Kiro écrites à la main (`requirements.md`, `design.md`, `tasks.md`)

## Décision

Option retenue : « OpenSpec », parce qu'il est léger, pensé pour un code existant
(changements exprimés en deltas sur les specs) et que l'archivage d'un changement met
à jour la spec de référence.

### Conséquences

* Bon, parce que `openspec/specs/` décrit le comportement actuel, et `openspec/changes/archive/` l'historique.
* Mauvais, parce qu'il requiert Node/npm sur le poste en plus de uv.
