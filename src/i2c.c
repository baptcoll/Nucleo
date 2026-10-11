#include "i2c.h"
#include "stm32g0xx_hal.h"

#define I2C_PORT GPIOB
#define I2C_SCL_PIN GPIO_PIN_8
#define I2C_SDA_PIN GPIO_PIN_9

/* HSI16 : PRESC=3 (250 ns), SCLDEL=4 (1,25 us), SDADEL=2 (500 ns),
 * SCLH=SCLL=19 (5 us chacun, hors synchronisation et filtres).
 * Reglage conservateur pour le mode standard : montee <= 1 us,
 * descente <= 300 ns, filtre analogique actif, filtre numerique desactive. */
#define I2C_TIMING_STANDARD_HSI16 0x30421313U

static I2C_HandleTypeDef i2c = {
    .Instance = I2C1,
    .Init = {
        .Timing = I2C_TIMING_STANDARD_HSI16,
        .OwnAddress1 = 0U,
        .AddressingMode = I2C_ADDRESSINGMODE_7BIT,
        .DualAddressMode = I2C_DUALADDRESS_DISABLE,
        .OwnAddress2 = 0U,
        .OwnAddress2Masks = I2C_OA2_NOMASK,
        .GeneralCallMode = I2C_GENERALCALL_DISABLE,
        .NoStretchMode = I2C_NOSTRETCH_DISABLE
    }
};

bool I2C_Init(void)
{
    /* Fixer l'horloge du peripherique pour conserver la validite du timing. */
    RCC_PeriphCLKInitTypeDef clock = {
        .PeriphClockSelection = RCC_PERIPHCLK_I2C1,
        .I2c1ClockSelection = RCC_I2C1CLKSOURCE_HSI
    };
    if (HAL_RCCEx_PeriphCLKConfig(&clock) != HAL_OK)
    {
        return false;
    }

    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_I2C1_CLK_ENABLE();

    /* Les deux lignes sont en drain ouvert avec rappels externes. */
    GPIO_InitTypeDef pins = {
        .Pin = I2C_SCL_PIN | I2C_SDA_PIN,
        .Mode = GPIO_MODE_AF_OD,
        .Pull = GPIO_NOPULL,
        .Speed = GPIO_SPEED_FREQ_HIGH,
        .Alternate = GPIO_AF6_I2C1
    };
    HAL_GPIO_Init(I2C_PORT, &pins);

    if (HAL_I2C_Init(&i2c) != HAL_OK)
    {
        return false;
    }
    if (HAL_I2CEx_ConfigAnalogFilter(&i2c, I2C_ANALOGFILTER_ENABLE) != HAL_OK)
    {
        return false;
    }
    if (HAL_I2CEx_ConfigDigitalFilter(&i2c, 0U) != HAL_OK)
    {
        return false;
    }

    return true;
}
