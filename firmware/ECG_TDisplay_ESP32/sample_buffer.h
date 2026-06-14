#pragma once
#include "config.h"

class CircularSampleBuffer {
 public:
  void begin();
  void push(int16_t sample);
  size_t snapshot(int16_t *dest, size_t maxSamples) const;
  size_t capacity() const { return ECG_BUFFER_SAMPLES; }
 private:
  mutable portMUX_TYPE mux_ = portMUX_INITIALIZER_UNLOCKED;
  int16_t data_[ECG_BUFFER_SAMPLES];
  size_t head_ = 0;
  size_t count_ = 0;
};

extern CircularSampleBuffer rawBuffer;
extern CircularSampleBuffer filteredBuffer;
