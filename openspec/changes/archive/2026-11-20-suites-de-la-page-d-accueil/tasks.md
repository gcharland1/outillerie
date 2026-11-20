## 1. Tests manquants ou incomplets

- [x] 1.1 « Remise en circulation » : une scie ajoutée il y a 90 jours, retirée puis remise en circulation, n'apparaît pas dans « Nouveaux outils » (`test_home.py`)
- [x] 1.2 « Sans script » : `GET /` ne contient aucun `<script>` (`test_home.py`)
- [x] 1.3 « Acceptation depuis l'accueil » : message de succès « Demande de … acceptée » sur l'accueil (`test_loans.py`)
- [x] 1.4 « Annuler le prêt » de l'accueil mène à la page de confirmation, sans `origin=home` (`test_home.py`)
- [x] 1.5 Refus d'une demande de contact : celui qui refuse ne voit plus la demande (`test_home.py`)
- [x] 1.6 « Tri inconnu » : avec plusieurs outils, la liste suit « Pertinence » (`test_tools_of_contacts.py`)

## 2. Couleurs et partiel

- [x] 2.1 ADR 0019 et règle « Interface » de `.claude/rules/templates.md`
- [x] 2.2 Boutons de prêt (`BUTTONS`), de retrait, de confirmation, de connexion et d'inscription selon l'ADR 0019 ; classe ajoutée seulement si un style existe ; tests de couleur mis à jour
- [x] 2.3 Partiel `contacts/_requests.html` utilisé par l'accueil et « Mes contacts »
- [x] 2.4 `--color-primary` bleu, boutons d'envoi neutres sauf `primary`, liens du menu du compte en bleu (`site.css`)

## 3. Notes archivées

- [x] 3.1 `design.md` et `tasks.md` de `2026-11-19-page-d-accueil` nomment `loans.dashboard(user_id)`, 5 lignes par groupe
- [x] 3.2 `questions.md` D11 décrit le `<label>` « Trier par » ; question 21 note l'écart des lectures sans `LIMIT`
