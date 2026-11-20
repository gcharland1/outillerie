# Design

Décisions et sources : [questions.md](questions.md). Décision d'architecture : ADR 0020.

## Deux passes pour la colonne

L'ADR 0017 revient à l'image précédente sans `downgrade` si un déploiement échoue ; l'ADR 0007
impose donc *expand/contract*. Cette PR (*expand*) :

- révision `user.username` nullable, `uq_user_username` gardée (un index unique admet plusieurs
  NULL) ; son `downgrade` remplit les NULL avec `'user' || id`, unique, puis remet `NOT NULL` ;
- le modèle garde `username = db.Column(db.String(250), unique=True, nullable=True)`, seule
  référence restante, pour que `flask db check` reste vide ; aucun code ne le lit ni ne l'écrit.

La PR suivante (*contract*), une fois cette version déployée : supprime la colonne du modèle,
révision `drop_constraint("uq_user_username")` puis `drop_column`, `downgrade` qui recrée la
colonne nullable, la remplit avec `'user' || id`, la remet `NOT NULL` et recrée la contrainte.
L'issue #38 n'est fermée qu'après elle.

## Connexion

`User.query.filter(func.lower(User.email) == func.lower(email.strip()))` reprend l'expression de
l'index `uq_user_email_lower`. Le hachage factice et l'appel inconditionnel à
`check_password_hash` restent. Le champ est `<input type="email" name="email" autocomplete="username">`
et réaffiche la saisie après un échec, comme le veut la règle des gabarits ; la réponse ne diffère
donc d'un cas à l'autre que par ce que le visiteur a lui-même saisi.

## Tri

`text_search.sort_key(column)` = `lower(normalized(column))`, la normalisation partagée de
l'ADR 0018. « Mes contacts » et la recherche trient par `sort_key(first_name)`,
`sort_key(last_name)`, `User.id`. Le plafond de `plafonner-la-recherche-d-utilisateurs` coupe
après ce tri.

## Affichage

Le nom complet reste écrit en ligne (`{{ u.first_name }} {{ u.last_name }}`), comme une quinzaine
d'endroits du code ; une propriété `full_name` est hors périmètre. Dans « Mes contacts », le lien
vers la page du contact passe sur le nom. Un nom long dans le menu du compte est coupé par CSS
(`text-overflow: ellipsis`).

## Risques

- Homonymes : deux « Bob Gagnon » sont indiscernables dans les listes ; les actions portent l'id
  et ne se trompent pas de compte. Accepté ; un champ public de distinction serait une autre issue.
- Énumération à l'inscription : « Le courriel est déjà utilisé » révèle qu'un courriel privé a un
  compte. Accepté faute d'envoi de courriel ; une inscription par courriel vérifié serait une autre issue.
- Force brute : aucune limitation des essais, et un courriel se devine mieux qu'un pseudonyme.
  Hors périmètre ; issue séparée « Connexion - Limiter les essais de mot de passe ».

## Suivis

Issues à ouvrir après accord de l'utilisateur sur leur texte, hors des tâches : la passe *contract*
(suppression de la colonne) et « Connexion - Limiter les essais de mot de passe ».
