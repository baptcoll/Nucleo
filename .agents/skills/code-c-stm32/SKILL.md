---
name: code-c-stm32
description: Générer et modifier du code C pour STM32 avec STM32Cube et PlatformIO selon mes conventions.
---

# Conventions de code

- Écrire en C avec la HAL STM32.
- Utiliser des noms de fonctions et de variables en anglais.
- Rédiger les commentaires en français.
- Indenter avec 4 espaces.
- Placer les accolades sur une nouvelle ligne.
- Toujours mettre des accolades autour des blocs if et else.
- Utiliser des constantes nommées pour les broches et les délais.
- Garder main.c court et séparer les périphériques en modules .c/.h.
- Vérifier les valeurs de retour des fonctions HAL.
- Laisser l’utilisateur lancer la compilation et l’upload.
- Initialiser une strucutre au moment de sa déclaration si possible