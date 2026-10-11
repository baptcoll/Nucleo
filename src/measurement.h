/**
 * @file measurement.h
 * @brief Interface des mesures internes et des messages série.
 */

#ifndef MEASUREMENT_H
#define MEASUREMENT_H

#include <stdbool.h>

/**
 * @brief Initialise la HAL, la LED, USART2 et l’ADC, puis émet la version.
 * @note Conserve l’horloge HSI16 par défaut. USART2 utilise 115200 bauds.
 * Une erreur entraîne un arrêt avec clignotement rapide de la LED.
 */
void Measurement_Init(void);
/**
 * @brief Mesure la température et VDDA, puis transmet les résultats.
 * @pre Measurement_Init() doit avoir terminé avec succès.
 * @note Moyenne 16 conversions par canal et utilise la calibration HAL.
 * Émet la version, puis la température en degrés Celsius et VDDA en mV.
 * Cette fonction est bloquante et doit être appelée hors interruption.
 * Une erreur entraîne un arrêt avec clignotement rapide de la LED.
 */
void Measurement_Report(void);
/**
 * @brief Émet la version du firmware et le nouvel état de pause.
 * @param[in] paused true pour annoncer la pause, false pour la reprise.
 * @pre Measurement_Init() doit avoir terminé avec succès.
 * @note Cette émission bloquante ne modifie pas l’état de la boucle de mesure.
 * Une erreur de transmission entraîne un arrêt avec clignotement de la LED.
 */
void Measurement_ReportPause(bool paused);

#endif
