#pragma once
#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>

static constexpr uint8_t TFT_MOSI_PIN = 19;
static constexpr uint8_t TFT_SCLK_PIN = 18;
static constexpr uint8_t TFT_CS_PIN = 5;
static constexpr uint8_t TFT_DC_PIN = 16;
static constexpr uint8_t TFT_BL_PIN = 4;
static constexpr uint8_t ADC_IN_PIN = 36;
static constexpr uint8_t BUTTON1_PIN = 35;
static constexpr uint8_t BUTTON2_PIN = 0;
static constexpr uint8_t ADC_POWER_PIN = 14;

static constexpr uint32_t ADC_SAMPLE_RATE_HZ = 20000;
static constexpr uint16_t OVERSAMPLE_FACTOR = 16;
static constexpr uint32_t OUTPUT_SAMPLE_RATE_HZ = ADC_SAMPLE_RATE_HZ / OVERSAMPLE_FACTOR;
static constexpr size_t ECG_BUFFER_SAMPLES = OUTPUT_SAMPLE_RATE_HZ * 5;

static constexpr size_t ADC_BLOCK_SAMPLES = 64;
static constexpr size_t ADC_QUEUE_LENGTH = 8;
static constexpr size_t DSP_QUEUE_LENGTH = 64;
static constexpr size_t BLE_QUEUE_LENGTH = 128;
static constexpr size_t DISPLAY_QUEUE_LENGTH = 1;

static constexpr uint16_t BLE_SERVICE_UUID = 0xEC00;
static constexpr uint16_t BLE_COMMAND_UUID = 0xEC01;
static constexpr uint16_t BLE_DATA_UUID = 0xEC02;
static constexpr char BLE_DEVICE_NAME[] = "LilyGO-ECG";

enum StreamMode : uint8_t { STREAM_OFF = 0, STREAM_RAW = 1, STREAM_FILTERED = 2 };

struct AdcBlock { uint16_t samples[ADC_BLOCK_SAMPLES]; size_t count; };
struct DecimatedSample { int16_t raw; uint32_t index; };
struct ProcessedSample { int16_t raw; int16_t filtered; uint32_t index; };

extern QueueHandle_t adcQueue;
extern QueueHandle_t dspQueue;
extern QueueHandle_t bleQueue;
extern QueueHandle_t displayQueue;
extern volatile bool bleConnected;
extern volatile StreamMode streamMode;
