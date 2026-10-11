/**
 * @file spi.c
 * @brief Configuration SPI1 maître sur PB3/PB4/PB5.
 */

#include "spi.h"
#include "stm32g0xx_hal.h"

#define SPI_PORT GPIOB
#define SPI_SCK_PIN GPIO_PIN_3
#define SPI_MISO_PIN GPIO_PIN_4
#define SPI_MOSI_PIN GPIO_PIN_5
#define SPI_BAUD_PRESCALER SPI_BAUDRATEPRESCALER_16

static SPI_HandleTypeDef spi = {
    .Instance = SPI1,
    .Init = {
        .Mode = SPI_MODE_MASTER,
        .Direction = SPI_DIRECTION_2LINES,
        .DataSize = SPI_DATASIZE_8BIT,
        .CLKPolarity = SPI_POLARITY_LOW,
        .CLKPhase = SPI_PHASE_1EDGE,
        .NSS = SPI_NSS_SOFT,
        .BaudRatePrescaler = SPI_BAUD_PRESCALER,
        .FirstBit = SPI_FIRSTBIT_MSB,
        .TIMode = SPI_TIMODE_DISABLE,
        .CRCCalculation = SPI_CRCCALCULATION_DISABLE,
        .CRCPolynomial = 7U,
        .CRCLength = SPI_CRC_LENGTH_DATASIZE,
        .NSSPMode = SPI_NSS_PULSE_DISABLE
    }
};

bool SPI_Init(void)
{
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_SPI1_CLK_ENABLE();

    /* Utiliser le port B pour conserver PA5 disponible pour la LED. */
    GPIO_InitTypeDef pins = {
        .Pin = SPI_SCK_PIN | SPI_MISO_PIN | SPI_MOSI_PIN,
        .Mode = GPIO_MODE_AF_PP,
        .Pull = GPIO_NOPULL,
        .Speed = GPIO_SPEED_FREQ_HIGH,
        .Alternate = GPIO_AF0_SPI1
    };
    HAL_GPIO_Init(SPI_PORT, &pins);

    if (HAL_SPI_Init(&spi) != HAL_OK)
    {
        return false;
    }

    return true;
}
