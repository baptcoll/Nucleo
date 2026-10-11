#include "button.h"
#include "stm32g0xx_hal.h"

#define BUTTON_PORT GPIOC
#define BUTTON_PIN GPIO_PIN_13
#define BUTTON_PRESSED_STATE GPIO_PIN_RESET
#define BUTTON_DEBOUNCE_MS 30U

static GPIO_PinState last_state = GPIO_PIN_SET;
static GPIO_PinState stable_state = GPIO_PIN_SET;
static uint32_t last_change_ms = 0U;

void Button_Init(void)
{
    __HAL_RCC_GPIOC_CLK_ENABLE();
    GPIO_InitTypeDef config = {
        .Pin = BUTTON_PIN,
        .Mode = GPIO_MODE_INPUT,
        .Pull = GPIO_NOPULL,
        .Speed = GPIO_SPEED_FREQ_LOW
    };
    HAL_GPIO_Init(BUTTON_PORT, &config);

    /* Un bouton maintenu au demarrage doit etre relache avant un nouvel appui. */
    last_state = HAL_GPIO_ReadPin(BUTTON_PORT, BUTTON_PIN);
    stable_state = last_state;
    last_change_ms = HAL_GetTick();
}

bool Button_PollPressed(void)
{
    uint32_t now = HAL_GetTick();
    GPIO_PinState state = HAL_GPIO_ReadPin(BUTTON_PORT, BUTTON_PIN);

    if (state != last_state)
    {
        last_state = state;
        last_change_ms = now;
    }

    /* La soustraction reste valide lors du debordement du compteur HAL. */
    if (state != stable_state && (uint32_t)(now - last_change_ms) >= BUTTON_DEBOUNCE_MS)
    {
        stable_state = state;
        return stable_state == BUTTON_PRESSED_STATE;
    }

    return false;
}
