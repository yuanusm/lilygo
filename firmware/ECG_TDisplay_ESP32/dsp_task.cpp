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
//static Biquad notch50(0.991114f, -1.604644f, 0.991114f, -1.604644f, 0.982228f);
//static Biquad notch100(0.982385f, -0.607183f, 0.982385f, -0.607183f, 0.964770f);
//static Biquad notch150(0.973809f, 0.601883f, 0.973809f, 0.601883f, 0.947619f);
// Fs = 1000Hz, Q=35 notch
//static Biquad notch50(0.995532033f, -1.893614454f, 0.995532033f, -1.893614454f, 0.991064065f);
//static Biquad notch100(0.991103636f, -1.603639369f, 0.991103636f, -1.603639369f, 0.982207271f);
//static Biquad notch150(0.986714109f, -1.159952004f, 0.986714109f, -1.159952004f, 0.973428219f);
// Fs = 1000Hz , Q=100 notch
/*static Biquad notch50(
    0.998431666f,
    -1.899129884f,
    0.998431666f,
    -1.899129884f,
    0.996863332f
);


static Biquad notch100(
    0.996868236f,
    -1.612966688f,
    0.996868236f,
    -1.612966688f,
    0.993736472f
);


static Biquad notch150(
    0.995309679f,
    -1.170056701f,
    0.995309679f,
    -1.170056701f,
    0.990619358f
);*/
//Fs=1000 Q=40
/*static Biquad notch50(
    0.996088350f,
    -1.894672632f,
    0.996088350f,
    -1.894672632f,
    0.992176700f
);


static Biquad notch100(
    0.992207064f,
    -1.605424753f,
    0.992207064f,
    -1.605424753f,
    0.984414127f
);


static Biquad notch150(
    0.988355670f,
    -1.161881774f,
    0.988355670f,
    -1.161881774f,
    0.976711341f
);

50 Hz = 40 dB 100 Hz = 5 dB 150 Hz = 14-17 dB a 50 Hz = 20 dB 100 Hz = -20 dB 150 Hz = 10 dB

*/

//Fs1000 Q=15
static Biquad notch50(
    0.989636175f,
    -1.882399867f,
    0.989636175f,
    -1.882399867f,
    0.979272351f
);


static Biquad notch100(
    0.979482761f,
    -1.584836399f,
    0.979482761f,
    -1.584836399f,
    0.958965522f
);


static Biquad notch150(
    0.969531253f,
    -1.139752344f,
    0.969531253f,
    -1.139752344f,
    0.939062506f
);
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
