---
name: git-commit
description: Préparer et créer des commits Git clairs pour le projet. Utiliser lorsque l’utilisateur demande un commit ou un message de commit.
disable-model-invocation: true
---

# Commits Git

- Rédiger les messages de commit en français.
- Avant toute modification de l’index, vérifier la racine du dépôt, la branche courante, `git status --short`, `git diff` et `git diff --cached`.
- Examiner les fichiers non suivis concernés avant de les ajouter.
- Limiter le commit aux changements demandés. Préserver les autres modifications et les fichiers déjà indexés ; si leur présence rend le périmètre ambigu, demander une clarification.
- Ajouter les fichiers par chemin explicite, sans utiliser `git add .` par défaut.
- Exclure les secrets, identifiants, fichiers `.env`, sorties de compilation `.pio/` et fichiers système comme `.DS_Store`.
- Regrouper les changements liés dans un commit cohérent. Séparer les changements indépendants lorsque cela est possible sans altérer le travail en cours.
- Utiliser le format `type: description`, avec un titre bref décrivant concrètement le changement.
- Choisir parmi `feat`, `fix`, `refactor`, `docs`, `test`, `build` et `chore` selon la nature des changements.
- Ajouter un corps si nécessaire pour expliquer la raison du changement et les vérifications réalisées. Ne jamais prétendre avoir exécuté une vérification non effectuée.
- Pour ce projet STM32, laisser l’utilisateur lancer la compilation et l’upload.
- Relire le diff indexé et exécuter `git diff --cached --check` avant de créer le commit.
- Si l’utilisateur demande uniquement un message de commit, proposer le message sans modifier l’index ni créer de commit.
- Si l’utilisateur demande de créer un commit, le créer une fois les vérifications terminées, puis communiquer son identifiant et son résumé.
- Ne pas effectuer de push, réécrire l’historique, amender un commit ou annuler des modifications sans demande explicite.
- Fait un pull request après autorisation en utilisant l'api GitHub

## Exemples de titres

- `feat: ajouter la pause des mesures avec le bouton utilisateur`
- `fix: corriger l’anti-rebond du bouton`
- `refactor: isoler les mesures dans un module dédié`
- `docs: préciser les conventions STM32`
