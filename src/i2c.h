#ifndef I2C_H
#define I2C_H

#include <stdbool.h>

/* Appeler apres HAL_Init(), avec HSI16 actif.
 * Retourne true si l'initialisation reussit.
 * I2C1 : PB8/SCL, PB9/SDA, adressage 7 bits, utilisation en maitre.
 * Mode standard (au plus 100 kHz), resistances de rappel externes requises.
 * Le timing devra etre valide sur le bus reel avant les premiers transferts. */
bool I2C_Init(void);

#endif
