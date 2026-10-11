/**
 * @file i2c.h
 * @brief Interface d’initialisation du bus I2C1.
 */

#ifndef I2C_H
#define I2C_H

#include <stdbool.h>

/**
 * @brief Configure I2C1 maître, en adressage 7 bits et mode standard.
 * @retval true Horloge, périphérique et filtres initialisés.
 * @retval false Échec d’une étape de configuration HAL.
 * @pre Appeler après HAL_Init(), avec HSI16 actif.
 * @note PB8/SCL et PB9/SDA nécessitent des résistances de rappel externes.
 * Le timing vise au plus 100 kHz et doit être validé sur le bus réel
 * avant les premiers transferts.
 */
bool I2C_Init(void);

#endif
