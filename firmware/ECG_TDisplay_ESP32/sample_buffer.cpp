#include "sample_buffer.h"

void CircularSampleBuffer::begin() {
  portENTER_CRITICAL(&mux_);
  memset(data_, 0, sizeof(data_));
  head_ = 0;
  count_ = 0;
  portEXIT_CRITICAL(&mux_);
}

void CircularSampleBuffer::push(int16_t sample) {
  portENTER_CRITICAL(&mux_);
  data_[head_] = sample;
  head_ = (head_ + 1) % ECG_BUFFER_SAMPLES;
  if (count_ < ECG_BUFFER_SAMPLES) count_++;
  portEXIT_CRITICAL(&mux_);
}

size_t CircularSampleBuffer::snapshot(int16_t *dest, size_t maxSamples) const {
  portENTER_CRITICAL(&mux_);
  const size_t n = min(count_, maxSamples);
  const size_t start = (head_ + ECG_BUFFER_SAMPLES - n) % ECG_BUFFER_SAMPLES;
  for (size_t i = 0; i < n; ++i) dest[i] = data_[(start + i) % ECG_BUFFER_SAMPLES];
  portEXIT_CRITICAL(&mux_);
  return n;
}
