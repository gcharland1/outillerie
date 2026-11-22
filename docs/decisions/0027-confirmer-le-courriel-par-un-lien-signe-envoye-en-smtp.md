---
status: proposed
date: 2026-11-21
decision-makers: Gabriel Charland
---

# Confirmer le courriel par un lien signé envoyé en SMTP

## Contexte et problème

L'issue #50 demande un courriel de confirmation à l'inscription et réserve les prêts aux comptes
confirmés. L'app n'a jamais envoyé de courriel : il faut choisir le moyen d'envoi, le format du lien,
la façon de marquer un compte confirmé et ce que ce lien expose. Changement OpenSpec :
`openspec/changes/confirmation-du-courriel/` (décisions et sources dans `questions.md`).

## Options considérées

* Envoi : SMTP générique par `smtplib` (bibliothèque standard) ; API HTTP d'un fournisseur nommé ;
  aucun envoi réel
* Lien : jeton signé et horodaté sans état ; jeton aléatoire stocké en base, à usage unique
* Ouverture du lien : confirmation directe au GET ; page avec un bouton qui confirme par POST

## Décision

Option retenue : « SMTP générique, jeton signé sans état, page avec bouton POST », parce qu'elle
n'ajoute ni dépendance tierce ni table, ne lie pas le code à un fournisseur, et résiste aux
scanners de liens des messageries.

* Envoi par `smtplib`, configuré par `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`,
  `MAIL_SENDER` et `SITE_URL`. Hors `development`, l'app refuse de démarrer sans elles. Le
  fournisseur, le DNS (SPF, DKIM) et le `.env` du serveur relèvent de l'utilisateur, avant le
  déploiement.
* Lien : `URLSafeTimedSerializer` d'`itsdangerous` (déclaré en dépendance directe), signé par
  `FLASK_SECRET_KEY`, sel propre, charge `{id, courriel}`, valide 30 jours. Pas d'usage unique :
  confirmer est idempotent. Le courriel dans la charge invalide le lien d'un compte supprimé (ADR
  0023) ou d'une adresse changée.
* Le lien ouvre une page sans effet ; son bouton confirme par POST, protégé par le jeton CSRF (ADR
  0012). Il ne connecte pas.
* Schéma : `user.email_confirmed_at` et `user.email_confirmation_sent_at`, nullables (ADR 0007).
  Les comptes existants restent non confirmés.
* Un compte non confirmé ne peut ni demander un emprunt ni accepter une demande.
* Le jeton est masqué dans les lignes de requête journalisées par l'app ; au plus un courriel de
  confirmation par compte toutes les 5 minutes.

### Conséquences

* Bon, parce que changer de fournisseur ne demande que de changer des variables.
* Bon, parce qu'aucun état de jeton n'est stocké, et qu'un double clic ou un scanner ne casse rien.
* Mauvais, parce que changer `FLASK_SECRET_KEY` invalide tous les liens en circulation, comme les
  sessions (ADR 0006).
* Mauvais, parce qu'un lien envoyé ne se révoque pas avant ses 30 jours ; il ne fait que confirmer
  l'adresse qui l'a reçu.
* Mauvais, parce que les journaux de Cloudflare Tunnel peuvent garder l'URL du lien, jeton compris.
* Mauvais, parce qu'un déploiement sans les variables SMTP échoue et revient à l'image précédente
  (ADR 0017), et qu'après un tel retour la confirmation n'est plus exigée jusqu'au redéploiement.
* Mauvais, parce que les comptes existants doivent se faire renvoyer le courriel avant d'emprunter
  ou d'accepter une demande.
