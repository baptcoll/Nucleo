#ifndef BUTTON_H
#define BUTTON_H

#include <stdbool.h>

void Button_Init(void);
/* Appeler regulierement : un seul evenement par appui, apres anti-rebond. */
bool Button_PollPressed(void);

#endif
