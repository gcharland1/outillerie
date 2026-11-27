# Design

## Context

Voir [proposal.md](proposal.md) ; décisions et sources dans [questions.md](questions.md). Depuis
l'ADR 0028, l'identifiant de session est `"<id>:<version>"` (`"<id>"` à la version 0) et `load_user`
refuse une version qui n'est plus celle du compte.

## Goals / Non-Goals

**Goals:**
- Révoquer en une action toutes les sessions et tous les cookies persistants d'un compte.

**Non-Goals:**
- Changement ou réinitialisation du mot de passe.
- Déconnecter un seul appareil choisi.

## Decisions

### Rotation atomique
`UPDATE user SET session_version = session_version + 1 WHERE id = :me AND deleted_at IS NULL`, comme
`profile.save` : une suppression qui tient le verrou du compte l'emporte. Aucune ligne : le compte a
disparu, déconnexion et retour à `/login`.

### Appareil courant
`auth.end_session()` efface la session et le cookie persistant de l'appareil, puis redirection vers
`/logged-out?reason=all-devices`. Sans cela, l'appareil courant serait refusé à la requête suivante
sans message.

### Avis par courriel
Après le commit, `mail.send` vers l'adresse du compte, seulement si elle est confirmée. `mail.send` ne
lève jamais d'erreur : l'action ne dépend pas de l'envoi. Aucun lien, pour qu'un courriel imité ne
puisse pas s'en servir d'appât.

## Risks / Trade-offs

- Un porteur de cookie volé peut déconnecter le vrai propriétaire : sans gravité, et l'avis l'en
  informe.
- Qui connaît le mot de passe se reconnecte : limite acceptée tant qu'aucune fonction de mot de passe
  n'existe.
