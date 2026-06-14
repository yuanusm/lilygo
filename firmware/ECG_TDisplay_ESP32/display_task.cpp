#include "display_task.h"
#include "config.h"
#include <LovyanGFX.hpp>

class LGFX : public lgfx::LGFX_Device {
  lgfx::Panel_ST7789 panel_;
  lgfx::Bus_SPI bus_;
 public:
  LGFX() {
    auto busConfig = bus_.config();
    busConfig.spi_host = VSPI_HOST;
    busConfig.spi_mode = 0;
    busConfig.freq_write = 40000000;
    busConfig.pin_sclk = TFT_SCLK_PIN;
    busConfig.pin_mosi = TFT_MOSI_PIN;
    busConfig.pin_miso = -1;
    busConfig.pin_dc = TFT_DC_PIN;
    bus_.config(busConfig);
    panel_.setBus(&bus_);
    auto panelConfig = panel_.config();
    panelConfig.pin_cs = TFT_CS_PIN;
    panelConfig.pin_rst = -1;
    panelConfig.pin_busy = -1;
    panelConfig.panel_width = 135;
    panelConfig.panel_height = 240;
    panelConfig.offset_x = 52;
    panelConfig.offset_y = 40;
    panelConfig.invert = true;
    panel_.config(panelConfig);
    setPanel(&panel_);
  }
};

static LGFX tft;

static void taskDisplay(void *) {
  pinMode(TFT_BL_PIN, OUTPUT);
  digitalWrite(TFT_BL_PIN, HIGH);
  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_GREEN, TFT_BLACK);

  int x = 0;
  int lastY = 67;
  ProcessedSample s;
  for (;;) {
    if (x == 0) tft.fillRect(0, 16, 240, 119, TFT_BLACK);
    if (x % 20 == 0) {
      tft.fillRect(0, 0, 240, 15, TFT_BLACK);
      tft.setCursor(0, 0);
      tft.printf("BLE:%s 500SPS", bleConnected ? "ON" : "OFF");
    }
    if (xQueueReceive(displayQueue, &s, pdMS_TO_TICKS(40)) == pdTRUE) {
      const int y = constrain(75 - (s.filtered / 45), 18, 133);
      tft.drawLine(max(0, x - 1), lastY, x, y, TFT_GREEN);
      lastY = y;
      x = (x + 1) % 240;
    }
    vTaskDelay(pdMS_TO_TICKS(4));
  }
}

void startDisplayTask() {
  xTaskCreatePinnedToCore(taskDisplay, "TaskDisplay", 4096, nullptr, 1, nullptr, 1);
}
