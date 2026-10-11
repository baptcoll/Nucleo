/**
 * @file spi.h
 * @brief Interface d’initialisation du bus SPI1.
 */

#ifndef SPI_H
#define SPI_H

#include <stdbool.h>

/**
 * @brief Configure SPI1 maître en mode 0, sur 8 bits, MSB en premier.
 * @retval true Initialisation réussie.
 * @retval false Échec de HAL_SPI_Init().
 * @pre Appeler après HAL_Init().
 * @note Broches : PB3/SCK, PB4/MISO, PB5/MOSI. L’horloge est divisée
 * par 16, soit 1 MHz pour une horloge source de 16 MHz.
 * La broche CS du périphérique reste à définir et à gérer séparément.
 */
bool SPI_Init(void);

#endif
