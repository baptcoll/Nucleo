#include "stm32g0xx_hal.h"
#include "measurement.h"
#include <stdio.h>
#include <string.h>

#define SAMPLE_COUNT 16U
#define HAL_TIMEOUT_MS 100U
#define ADC_SETTLE_MS 1U
#define ERROR_BLINK_MS 100U
#define LED_PORT GPIOA
#define LED_PIN GPIO_PIN_5
#define SERIAL_PINS (GPIO_PIN_2 | GPIO_PIN_3)

static ADC_HandleTypeDef adc = {0};
static UART_HandleTypeDef serial = {0};

/* En cas d'erreur, la LED clignote rapidement au lieu du rythme normal. */
static void Error_Stop(const char *message)
{
    if (serial.gState == HAL_UART_STATE_READY)
    {
        if (HAL_UART_Transmit(&serial, (uint8_t *)message,
                              (uint16_t)strlen(message), HAL_TIMEOUT_MS) != HAL_OK)
        {
            /* La LED signale aussi l'erreur si le port serie est indisponible. */
            HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_RESET);
        }
    }
    while (1)
    {
        HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
        HAL_Delay(ERROR_BLINK_MS);
    }
}

static void LED_Init(void)
{
    __HAL_RCC_GPIOA_CLK_ENABLE();
    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_RESET);
    GPIO_InitTypeDef led = {
        .Pin = LED_PIN,
        .Mode = GPIO_MODE_OUTPUT_PP,
        .Pull = GPIO_NOPULL,
        .Speed = GPIO_SPEED_FREQ_LOW
    };
    HAL_GPIO_Init(LED_PORT, &led);
}

static void Serial_Init(void)
{
    /* PA2 (TX) et PA3 (RX) sont relies au port serie USB du ST-LINK. */
    __HAL_RCC_USART2_CLK_ENABLE();
    GPIO_InitTypeDef pins = {
        .Pin = SERIAL_PINS,
        .Mode = GPIO_MODE_AF_PP,
        .Pull = GPIO_NOPULL,
        .Speed = GPIO_SPEED_FREQ_LOW,
        .Alternate = GPIO_AF1_USART2
    };
    HAL_GPIO_Init(GPIOA, &pins);

    serial.Instance = USART2;
    serial.Init.BaudRate = 115200;
    serial.Init.WordLength = UART_WORDLENGTH_8B;
    serial.Init.StopBits = UART_STOPBITS_1;
    serial.Init.Parity = UART_PARITY_NONE;
    serial.Init.Mode = UART_MODE_TX_RX;
    serial.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    serial.Init.OverSampling = UART_OVERSAMPLING_16;
    serial.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
    serial.Init.ClockPrescaler = UART_PRESCALER_DIV1;
    serial.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
    if (HAL_UART_Init(&serial) != HAL_OK)
    {
        Error_Stop("Erreur : initialisation USART2\r\n");
    }
}

static void ADC_Init(void)
{
    __HAL_RCC_ADC_CLK_ENABLE();
    adc.Instance = ADC1;
    adc.Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV4;
    adc.Init.Resolution = ADC_RESOLUTION_12B;
    adc.Init.DataAlign = ADC_DATAALIGN_RIGHT;
    adc.Init.ScanConvMode = ADC_SCAN_DISABLE;
    adc.Init.EOCSelection = ADC_EOC_SINGLE_CONV;
    adc.Init.NbrOfConversion = 1;
    adc.Init.ExternalTrigConv = ADC_SOFTWARE_START;
    adc.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
    adc.Init.Overrun = ADC_OVR_DATA_PRESERVED;
    /* A l'horloge par defaut (16 MHz), 160,5 cycles / 4 MHz = 40 us.
     * Cette duree convient au capteur interne et a VREFINT. */
    adc.Init.SamplingTimeCommon1 = ADC_SAMPLETIME_160CYCLES_5;
    adc.Init.SamplingTimeCommon2 = ADC_SAMPLETIME_160CYCLES_5;
    adc.Init.TriggerFrequencyMode = ADC_TRIGGER_FREQ_LOW;
    if (HAL_ADC_Init(&adc) != HAL_OK)
    {
        Error_Stop("Erreur : initialisation ADC\r\n");
    }
    if (HAL_ADCEx_Calibration_Start(&adc) != HAL_OK)
    {
        Error_Stop("Erreur : calibration ADC\r\n");
    }
    HAL_Delay(ADC_SETTLE_MS);
}

static uint32_t ADC_ReadAverage(uint32_t channel)
{
    ADC_ChannelConfTypeDef config = {
        .Channel = channel,
        .Rank = ADC_REGULAR_RANK_1,
        .SamplingTime = ADC_SAMPLINGTIME_COMMON_1
    };
    if (HAL_ADC_ConfigChannel(&adc, &config) != HAL_OK)
    {
        Error_Stop("Erreur : selection du canal ADC\r\n");
    }

    /* Laisser les sources internes se stabiliser avant la mesure. */
    HAL_Delay(ADC_SETTLE_MS);
    uint32_t sum = 0;
    for (uint32_t i = 0; i < SAMPLE_COUNT; ++i)
    {
        if (HAL_ADC_Start(&adc) != HAL_OK)
        {
            Error_Stop("Erreur : demarrage ADC\r\n");
        }
        if (HAL_ADC_PollForConversion(&adc, HAL_TIMEOUT_MS) != HAL_OK)
        {
            Error_Stop("Erreur : delai de conversion ADC depasse\r\n");
        }
        sum += HAL_ADC_GetValue(&adc);
        if (HAL_ADC_Stop(&adc) != HAL_OK)
        {
            Error_Stop("Erreur : arret ADC\r\n");
        }
    }
    return (sum + SAMPLE_COUNT / 2U) / SAMPLE_COUNT;
}

void Measurement_Report(void)
{
    HAL_GPIO_TogglePin(LED_PORT, LED_PIN);

    uint32_t reference = ADC_ReadAverage(ADC_CHANNEL_VREFINT);
    uint32_t raw_temperature = ADC_ReadAverage(ADC_CHANNEL_TEMPSENSOR);
    if (reference == 0U)
    {
        Error_Stop("Erreur : VREFINT nul\r\n");
    }

    /* Les macros HAL utilisent la calibration propre a cette puce.
     * La temperature obtenue est un entier en degres Celsius. */
    uint32_t supply_mv = __HAL_ADC_CALC_VREFANALOG_VOLTAGE(
        reference, ADC_RESOLUTION_12B);
    int32_t temperature = __HAL_ADC_CALC_TEMPERATURE(
        supply_mv, raw_temperature, ADC_RESOLUTION_12B);

    char message[96];
    int length = snprintf(message, sizeof(message),
                          "Temperature STM32 : %ld C | VDDA : %lu mV\r\n",
                          (long)temperature, (unsigned long)supply_mv);
    if (length <= 0 || (size_t)length >= sizeof(message))
    {
        Error_Stop("Erreur : formatage du message\r\n");
    }
    if (HAL_UART_Transmit(&serial, (uint8_t *)message,
                          (uint16_t)length, HAL_TIMEOUT_MS) != HAL_OK)
    {
        Error_Stop("Erreur : emission USART2\r\n");
    }

}

void Measurement_Init(void)
{
    HAL_StatusTypeDef init_status = HAL_Init();
    LED_Init();
    if (init_status != HAL_OK)
    {
        Error_Stop("Erreur : initialisation HAL\r\n");
    }
    Serial_Init();
    ADC_Init();
}

void Measurement_ReportPause(bool paused)
{
    const char *message = paused
        ? "Mesures en pause\r\n"
        : "Reprise des mesures\r\n";
    if (HAL_UART_Transmit(&serial, (uint8_t *)message,
                          (uint16_t)strlen(message), HAL_TIMEOUT_MS) != HAL_OK)
    {
        Error_Stop("Erreur : emission USART2\r\n");
    }
}
