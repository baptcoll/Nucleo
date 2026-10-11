#include "stm32g0xx_hal.h"
#include "button.h"
#include "measurement.h"

#define PERIOD_MS 1000U
#define BUTTON_POLL_MS 1U

void SysTick_Handler(void)
{
    HAL_IncTick();
}

int main(void)
{
    /* Conserver l'horloge HSI16 par defaut. */
    Measurement_Init();
    Button_Init();

    bool measurements_paused = false;
    uint32_t last_measurement_ms = HAL_GetTick() - PERIOD_MS;

    while (1)
    {
        uint32_t now = HAL_GetTick();
        if (Button_PollPressed())
        {
            measurements_paused = !measurements_paused;
            Measurement_ReportPause(measurements_paused);
            if (!measurements_paused)
            {
                /* Effectuer une mesure des la reprise. */
                last_measurement_ms = now - PERIOD_MS;
            }
        }

        if (!measurements_paused && (uint32_t)(now - last_measurement_ms) >= PERIOD_MS)
        {
            last_measurement_ms = now;
            Measurement_Report();
        }
        HAL_Delay(BUTTON_POLL_MS);
    }
}
