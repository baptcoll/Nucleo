/**
 * @file button.c
 * @brief Détection des appuis sur PC13 avec anti-rebond par TIM14.
 */

#include "button.h"
#include "stm32g0xx_hal.h"

#define BUTTON_PORT GPIOC
#define BUTTON_PIN GPIO_PIN_13
#define BUTTON_PRESSED_STATE GPIO_PIN_RESET
#define BUTTON_DEBOUNCE_MS 30U
#define BUTTON_TIMER_HZ 1000U
#define BUTTON_IRQ_PRIORITY 2U

static TIM_HandleTypeDef debounce_timer = {0};
static GPIO_PinState stable_state = GPIO_PIN_SET;
static ButtonPressedCallback pressed_callback = NULL;

bool Button_Init(ButtonPressedCallback callback)
{
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_TIM14_CLK_ENABLE();

    uint32_t timer_clock_hz = HAL_RCC_GetPCLK1Freq();
    if ((RCC->CFGR & RCC_CFGR_PPRE) != RCC_HCLK_DIV1)
    {
        timer_clock_hz *= 2U;
    }
    debounce_timer.Instance = TIM14;
    debounce_timer.Init.Prescaler = timer_clock_hz / BUTTON_TIMER_HZ - 1U;
    debounce_timer.Init.CounterMode = TIM_COUNTERMODE_UP;
    debounce_timer.Init.Period = BUTTON_DEBOUNCE_MS - 1U;
    debounce_timer.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    debounce_timer.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
    if (HAL_TIM_Base_Init(&debounce_timer) != HAL_OK)
    {
        return false;
    }
    /* Le timer s'arrete automatiquement a la fin des 30 ms. */
    SET_BIT(TIM14->CR1, TIM_CR1_OPM);
    __HAL_TIM_CLEAR_FLAG(&debounce_timer, TIM_FLAG_UPDATE);
    __HAL_TIM_ENABLE_IT(&debounce_timer, TIM_IT_UPDATE);

    GPIO_InitTypeDef config = {
        .Pin = BUTTON_PIN,
        .Mode = GPIO_MODE_IT_RISING_FALLING,
        .Pull = GPIO_NOPULL,
        .Speed = GPIO_SPEED_FREQ_LOW
    };
    HAL_GPIO_Init(BUTTON_PORT, &config);

    /* Un bouton maintenu au demarrage doit etre relache avant un nouvel appui. */
    __HAL_GPIO_EXTI_CLEAR_IT(BUTTON_PIN);
    stable_state = HAL_GPIO_ReadPin(BUTTON_PORT, BUTTON_PIN);
    pressed_callback = callback;

    /* La meme priorite empeche les deux gestionnaires de se preempter. */
    HAL_NVIC_SetPriority(TIM14_IRQn, BUTTON_IRQ_PRIORITY, 0U);
    HAL_NVIC_SetPriority(EXTI4_15_IRQn, BUTTON_IRQ_PRIORITY, 0U);
    HAL_NVIC_EnableIRQ(TIM14_IRQn);
    HAL_NVIC_EnableIRQ(EXTI4_15_IRQn);
    return true;
}

/**
 * @brief Transmet l’interruption EXTI du bouton PC13 à la HAL.
 */
void EXTI4_15_IRQHandler(void)
{
    HAL_GPIO_EXTI_IRQHandler(BUTTON_PIN);
}

/**
 * @brief Relance les 30 ms d’anti-rebond après un front sur PC13.
 * @param[in] pin Masque GPIO du front reçu ; les autres broches sont ignorées.
 * @note Exécutée en interruption, sans attente bloquante.
 */
static void Button_OnEdge(uint16_t pin)
{
    if (pin == BUTTON_PIN)
    {
        /* Chaque rebond redemarre le compteur et son prediviseur. */
        __HAL_TIM_DISABLE(&debounce_timer);
        TIM14->EGR = TIM_EGR_UG;
        __HAL_TIM_CLEAR_FLAG(&debounce_timer, TIM_FLAG_UPDATE);
        __HAL_TIM_ENABLE(&debounce_timer);
    }
}

/**
 * @brief Traite le rappel HAL d’un front montant.
 * @param[in] pin Masque GPIO transmis au gestionnaire d’anti-rebond.
 */
void HAL_GPIO_EXTI_Rising_Callback(uint16_t pin)
{
    Button_OnEdge(pin);
}

/**
 * @brief Traite le rappel HAL d’un front descendant.
 * @param[in] pin Masque GPIO transmis au gestionnaire d’anti-rebond.
 */
void HAL_GPIO_EXTI_Falling_Callback(uint16_t pin)
{
    Button_OnEdge(pin);
}

/**
 * @brief Transmet l’interruption du timer d’anti-rebond à la HAL.
 */
void TIM14_IRQHandler(void)
{
    HAL_TIM_IRQHandler(&debounce_timer);
}

/**
 * @brief Valide l’état stable du bouton à l’expiration de TIM14.
 * @param[in] timer Handle HAL du timer ayant déclenché le rappel.
 * @note Ignore les autres timers et les fronts EXTI encore en attente.
 * Appelle le rappel utilisateur uniquement lors d’un nouvel appui stable,
 *  dans le contexte de l’interruption.
 */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *timer)
{
    if (timer->Instance == TIM14)
    {
        GPIO_PinState state = HAL_GPIO_ReadPin(BUTTON_PORT, BUTTON_PIN);
        /* Un front en attente doit d'abord relancer les 30 ms. */
        if (__HAL_GPIO_EXTI_GET_RISING_IT(BUTTON_PIN) != 0U ||
            __HAL_GPIO_EXTI_GET_FALLING_IT(BUTTON_PIN) != 0U)
        {
            return;
        }
        if (state != stable_state)
        {
            stable_state = state;
            if (state == BUTTON_PRESSED_STATE && pressed_callback != NULL)
            {
                pressed_callback();
            }
        }
    }
}
