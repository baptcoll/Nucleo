#ifndef BUTTON_H
#define BUTTON_H

#include <stdbool.h>

typedef void (*ButtonPressedCallback)(void);

/* TIM14 est reserve a l'anti-rebond.
 * Le callback s'execute en interruption : aucun traitement bloquant. */
bool Button_Init(ButtonPressedCallback callback);

#endif
