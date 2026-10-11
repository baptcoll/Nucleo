/**
 * @file button.h
 * @brief Interface du bouton utilisateur et de son anti-rebond matériel.
 */

#ifndef BUTTON_H
#define BUTTON_H

#include <stdbool.h>

/** @brief Rappel sans argument, exécuté en interruption après un appui. */
typedef void (*ButtonPressedCallback)(void);

/**
 * @brief Configure PC13 et TIM14 pour valider les appuis après 30 ms.
 * @param[in] callback Fonction appelée lors d’un appui validé, ou NULL.
 * @retval true Initialisation réussie.
 * @retval false Échec de l’initialisation HAL de TIM14.
 * @pre La HAL et son horloge doivent être initialisées.
 * @note TIM14 est réservé à l’anti-rebond. Le rappel s’exécute en
 * interruption : il ne doit effectuer aucun traitement bloquant.
 * Un bouton maintenu au démarrage doit être relâché avant un nouvel appui.
 */
bool Button_Init(ButtonPressedCallback callback);

#endif
