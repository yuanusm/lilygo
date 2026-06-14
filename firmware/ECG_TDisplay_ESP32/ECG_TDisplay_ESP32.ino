#include "config.h"
#include "adc_task.h"
#include "dsp_task.h"
#include "ble_task.h"
#include "display_task.h"
#include "sample_buffer.h"

CircularSampleBuffer rawBuffer;
CircularSampleBuffer filteredBuffer;
QueueHandle_t adcQueue;
QueueHandle_t dspQueue;
QueueHandle_t bleQueue;
QueueHandle_t displayQueue;
volatile bool bleConnected = false;
volatile StreamMode streamMode = STREAM_OFF;

void setup() {
  Serial.begin(115200);
  pinMode(ADC_POWER_PIN, OUTPUT);
  digitalWrite(ADC_POWER_PIN, HIGH);
  pinMode(BUTTON1_PIN, INPUT);
  pinMode(BUTTON2_PIN, INPUT_PULLUP);

  rawBuffer.begin();
  filteredBuffer.begin();

  adcQueue = xQueueCreate(ADC_QUEUE_LENGTH, sizeof(AdcBlock));
  dspQueue = xQueueCreate(DSP_QUEUE_LENGTH, sizeof(DecimatedSample));
  bleQueue = xQueueCreate(BLE_QUEUE_LENGTH, sizeof(ProcessedSample));
  displayQueue = xQueueCreate(DISPLAY_QUEUE_LENGTH, sizeof(ProcessedSample));

  startBleTask();
  startDisplayTask();
  startDspTask();
  startAdcTask();
}

void loop() {
  vTaskDelay(pdMS_TO_TICKS(1000));
}
