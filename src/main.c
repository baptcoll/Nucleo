/**
 * @file main.c
 * @brief Boucle des mesures périodiques et gestion de la pause utilisateur.
 */

#include "stm32g0xx_hal.h"
#include "button.h"
#include "measurement.h"

#define PERIOD_MS 1000U

static volatile bool measurements_paused = false;
static volatile bool pause_changed = false;

/**
 * @brief Bascule la pause et notifie la boucle principale.
 * @note Rappel exécuté en interruption après validation de l’anti-rebond.
 * Les entrées/sorties restent à la charge de la boucle principale.
 */
static void OnButtonPressed(void)
{
    /* Appel en interruption, uniquement apres validation de l'anti-rebond. */
    measurements_paused = !measurements_paused;
    pause_changed = true;
}

/**
 * @brief Incrémente la base de temps HAL à chaque interruption SysTick.
 */
void SysTick_Handler(void)
{
    HAL_IncTick();
}

/**
 * @brief Initialise la carte et exécute les mesures avec pause utilisateur.
 * @details Effectue une mesure toutes les 1000 ms et dès la reprise.
 * Un échec du bouton annonce la pause et laisse la carte en attente.
 * @return Ne retourne jamais : la boucle principale est permanente.
 */
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
