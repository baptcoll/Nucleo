#ifndef SPI_H
#define SPI_H

#include <stdbool.h>

/* Appeler apres HAL_Init(). Retourne true si l'initialisation reussit.
 * SPI1 : PB3/SCK, PB4/MISO, PB5/MOSI, maitre, mode 0, 8 bits, MSB en premier.
 * Horloge SPI divisee par 16 (1 MHz avec l'horloge actuelle de 16 MHz).
 * La broche CS du peripherique reste a definir et a gerer separement. */
bool SPI_Init(void);

#endif
