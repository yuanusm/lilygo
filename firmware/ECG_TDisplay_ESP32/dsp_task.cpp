#include "dsp_task.h"
#include "config.h"
#include "sample_buffer.h"

class Biquad {
 public:
  Biquad(float b0, float b1, float b2, float a1, float a2) : b0_(b0), b1_(b1), b2_(b2), a1_(a1), a2_(a2) {}
  float process(float x) {
    const float y = b0_ * x + z1_;
    z1_ = b1_ * x - a1_ * y + z2_;
    z2_ = b2_ * x - a2_ * y;
    return y;
  }
 private:
  const float b0_, b1_, b2_, a1_, a2_;
  float z1_ = 0.0f, z2_ = 0.0f;
};

// Fs=500 Hz, Q=35, notch biquads normalized as a0=1.
static Biquad notch50(0.991114f, -1.604644f, 0.991114f, -1.604644f, 0.982228f);
static Biquad notch100(0.982385f, -0.607183f, 0.982385f, -0.607183f, 0.964770f);
static Biquad notch150(0.973809f, 0.601883f, 0.973809f, 0.601883f, 0.947619f);

static int16_t clampToInt16(float x) {
  if (x > 32767.0f) return 32767;
  if (x < -32768.0f) return -32768;
  return static_cast<int16_t>(lroundf(x));
}

static void taskDsp(void *) {
  DecimatedSample in;
  for (;;) {
    if (xQueueReceive(dspQueue, &in, portMAX_DELAY) == pdTRUE) {
      const float centered = static_cast<float>(in.raw) - 2048.0f;
      float y = notch50.process(centered);
      y = notch100.process(y);
      y = notch150.process(y);
      ProcessedSample out{in.raw, clampToInt16(y), in.index};
      rawBuffer.push(out.raw);
      filteredBuffer.push(out.filtered);
      xQueueSend(bleQueue, &out, 0);
      xQueueOverwrite(displayQueue, &out);
    }
  }
}

void startDspTask() {
  xTaskCreatePinnedToCore(taskDsp, "TaskDSP", 4096, nullptr, 4, nullptr, 1);
}
