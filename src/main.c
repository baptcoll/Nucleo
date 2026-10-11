#include "stm32g0xx_hal.h"
#include "button.h"
#include "measurement.h"

#define PERIOD_MS 1000U

static volatile bool measurements_paused = false;
static volatile bool pause_changed = false;

static void OnButtonPressed(void)
{
    /* Appel en interruption, uniquement apres validation de l'anti-rebond. */
    measurements_paused = !measurements_paused;
    pause_changed = true;
}

void SysTick_Handler(void)
{
    HAL_IncTick();
}

int main(void)
{
    /* Conserver l'horloge HSI16 par defaut. */
    Measurement_Init();
    if (!Button_Init(OnButtonPressed))
    {
        Measurement_ReportPause(true);
        while (1)
        {
            __WFI();
        }
    }

    uint32_t last_measurement_ms = HAL_GetTick() - PERIOD_MS;

    while (1)
    {
        uint32_t now = HAL_GetTick();
        /* Consommer la notification sans effectuer d'entree/sortie en ISR. */
        __disable_irq();
        bool changed = pause_changed;
        bool paused = measurements_paused;
        pause_changed = false;
        __enable_irq();
        if (changed)
        {
            Measurement_ReportPause(paused);
            if (!paused)
            {
                /* Effectuer une mesure des la reprise. */
                last_measurement_ms = now - PERIOD_MS;
            }
        }

        if (!paused && (uint32_t)(now - last_measurement_ms) >= PERIOD_MS)
        {
            last_measurement_ms = now;
            Measurement_Report();
        }
        /* Dormir jusqu'a la prochaine interruption (dont le tick HAL). */
        __WFI();
    }
}
