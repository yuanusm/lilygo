#include "adc_task.h"
#include "config.h"
#include "driver/adc.h"
#include "esp_adc/adc_continuous.h"

static adc_continuous_handle_t adcHandle = nullptr;

static void configureAdcContinuous() {
  adc_continuous_handle_cfg_t handleConfig = {
    .max_store_buf_size = 2048,
    .conv_frame_size = 512,
  };
  ESP_ERROR_CHECK(adc_continuous_new_handle(&handleConfig, &adcHandle));

  adc_continuous_config_t adcConfig = {};
  adcConfig.sample_freq_hz = ADC_SAMPLE_RATE_HZ;
  adcConfig.conv_mode = ADC_CONV_SINGLE_UNIT_1;
  adcConfig.format = ADC_DIGI_OUTPUT_FORMAT_TYPE1;

  adc_digi_pattern_config_t pattern = {};
  pattern.atten = ADC_ATTEN_DB_11;
  pattern.channel = ADC_CHANNEL_6;  // GPIO34 on ADC1.
  pattern.unit = ADC_UNIT_1;
  pattern.bit_width = SOC_ADC_DIGI_MAX_BITWIDTH;
  adcConfig.pattern_num = 1;
  adcConfig.adc_pattern = &pattern;
  ESP_ERROR_CHECK(adc_continuous_config(adcHandle, &adcConfig));
}

static void taskAdc(void *) {
  configureAdcContinuous();
  ESP_ERROR_CHECK(adc_continuous_start(adcHandle));

  uint8_t result[512];
  uint32_t bytesRead = 0;
  uint32_t acc = 0;
  uint16_t osrCount = 0;
  uint32_t sampleIndex = 0;

  for (;;) {
    const esp_err_t ret = adc_continuous_read(adcHandle, result, sizeof(result), &bytesRead, pdMS_TO_TICKS(100));
    if (ret != ESP_OK && ret != ESP_ERR_TIMEOUT) continue;
    for (uint32_t i = 0; i + sizeof(adc_digi_output_data_t) <= bytesRead; i += sizeof(adc_digi_output_data_t)) {
      adc_digi_output_data_t *p = reinterpret_cast<adc_digi_output_data_t *>(&result[i]);
      if (p->type1.channel != ADC_CHANNEL_6) continue;
      acc += p->type1.data;
      if (++osrCount == OVERSAMPLE_FACTOR) {
        DecimatedSample out{static_cast<int16_t>(acc / OVERSAMPLE_FACTOR), sampleIndex++};
        xQueueSend(dspQueue, &out, 0);
        acc = 0;
        osrCount = 0;
      }
    }
  }
}

void startAdcTask() {
  xTaskCreatePinnedToCore(taskAdc, "TaskADC", 4096, nullptr, 6, nullptr, 0);
}
