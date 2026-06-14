#include "ble_task.h"
#include "config.h"
#include "sample_buffer.h"
#include <NimBLEDevice.h>

static NimBLECharacteristic *dataCharacteristic = nullptr;
static uint16_t mtuPayload = 180;
static int16_t snapshotBuf[ECG_BUFFER_SAMPLES];

class ServerCallbacks : public NimBLEServerCallbacks {
  void onConnect(NimBLEServer *server, NimBLEConnInfo &connInfo) override {
    bleConnected = true;
    server->updateConnParams(connInfo.getConnHandle(), 6, 12, 0, 200);
  }
  void onDisconnect(NimBLEServer *server, NimBLEConnInfo &, int) override {
    bleConnected = false;
    streamMode = STREAM_OFF;
    NimBLEDevice::startAdvertising();
  }
};

static void notifyText(const char *text) {
  if (bleConnected && dataCharacteristic) dataCharacteristic->setValue((uint8_t *)text, strlen(text)), dataCharacteristic->notify();
}

static void sendBuffer(CircularSampleBuffer &buffer) {
  const size_t n = buffer.snapshot(snapshotBuf, ECG_BUFFER_SAMPLES);
  size_t sent = 0;
  while (bleConnected && sent < n) {
    const size_t samplesPerPacket = mtuPayload / sizeof(int16_t);
    const size_t chunk = min(samplesPerPacket, n - sent);
    dataCharacteristic->setValue(reinterpret_cast<uint8_t *>(&snapshotBuf[sent]), chunk * sizeof(int16_t));
    dataCharacteristic->notify();
    sent += chunk;
    vTaskDelay(pdMS_TO_TICKS(8));
  }
}

class CommandCallbacks : public NimBLECharacteristicCallbacks {
  void onWrite(NimBLECharacteristic *c, NimBLEConnInfo &) override {
    const std::string cmd = c->getValue();
    if (cmd == "START_STREAM_RAW") { streamMode = STREAM_RAW; notifyText("OK RAW"); }
    else if (cmd == "START_STREAM_FILTERED") { streamMode = STREAM_FILTERED; notifyText("OK FILTERED"); }
    else if (cmd == "STOP_STREAM") { streamMode = STREAM_OFF; notifyText("OK STOP"); }
    else if (cmd == "GET_BUFFER_RAW") { streamMode = STREAM_OFF; sendBuffer(rawBuffer); }
    else if (cmd == "GET_BUFFER_FILTERED") { streamMode = STREAM_OFF; sendBuffer(filteredBuffer); }
    else if (cmd == "PING") notifyText("PONG");
    else notifyText("ERR UNKNOWN_COMMAND");
  }
};

static void taskBle(void *) {
  NimBLEDevice::init(BLE_DEVICE_NAME);
  NimBLEDevice::setMTU(247);
  NimBLEServer *server = NimBLEDevice::createServer();
  server->setCallbacks(new ServerCallbacks());
  NimBLEService *service = server->createService(NimBLEUUID(BLE_SERVICE_UUID));
  NimBLECharacteristic *cmd = service->createCharacteristic(NimBLEUUID(BLE_COMMAND_UUID), NIMBLE_PROPERTY::WRITE | NIMBLE_PROPERTY::WRITE_NR);
  dataCharacteristic = service->createCharacteristic(NimBLEUUID(BLE_DATA_UUID), NIMBLE_PROPERTY::NOTIFY | NIMBLE_PROPERTY::READ);
  cmd->setCallbacks(new CommandCallbacks());
  service->start();
  NimBLEAdvertising *adv = NimBLEDevice::getAdvertising();
  adv->addServiceUUID(service->getUUID());
  adv->setScanResponse(true);
  adv->start();

  ProcessedSample s;
  int16_t packet[120];
  size_t count = 0;
  TickType_t lastFlush = xTaskGetTickCount();
  for (;;) {
    if (bleConnected) mtuPayload = min<uint16_t>(NimBLEDevice::getMTU() - 3, sizeof(packet));
    while (xQueueReceive(bleQueue, &s, pdMS_TO_TICKS(5)) == pdTRUE) {
      const StreamMode mode = streamMode;
      if (bleConnected && mode != STREAM_OFF) packet[count++] = (mode == STREAM_RAW) ? s.raw : s.filtered;
      if (count >= (mtuPayload / sizeof(int16_t))) break;
    }
    const bool due = (xTaskGetTickCount() - lastFlush) >= pdMS_TO_TICKS(20);
    if (bleConnected && count && (due || count >= (mtuPayload / sizeof(int16_t)))) {
      dataCharacteristic->setValue(reinterpret_cast<uint8_t *>(packet), count * sizeof(int16_t));
      dataCharacteristic->notify();
      count = 0;
      lastFlush = xTaskGetTickCount();
    }
    if (!bleConnected) count = 0;
  }
}

void startBleTask() {
  xTaskCreatePinnedToCore(taskBle, "TaskBLE", 8192, nullptr, 2, nullptr, 0);
}
