#ifndef AUDIO_MANAGER_H
#define AUDIO_MANAGER_H

#include <driver/i2s.h>
#include <WiFi.h>
#include <HTTPClient.h>

#define I2S_AMP_WS    27
#define I2S_AMP_BCLK  26
#define I2S_AMP_DOUT  14

bool i2sEnTX = false;

void instalarI2STX() {
  i2s_driver_uninstall(I2S_NUM_0);

  i2s_config_t configTX = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = 16000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .dma_buf_count = 8,
    .dma_buf_len = 256
  };

  i2s_pin_config_t pinTX = {
    .bck_io_num = I2S_AMP_BCLK,
    .ws_io_num = I2S_AMP_WS,
    .data_out_num = I2S_AMP_DOUT,
    .data_in_num = I2S_PIN_NO_CHANGE
  };

  i2s_driver_install(I2S_NUM_0, &configTX, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pinTX);
  i2s_zero_dma_buffer(I2S_NUM_0);

  i2sEnTX = true;
}

bool reproducirAudioStream(const char* url) {
  instalarI2STX();

  HTTPClient http;
  http.begin(url);

  int httpCode = http.GET();
  if (httpCode != 200) {
    http.end();
    extern void instalarI2SRX();
    instalarI2SRX();
    return false;
  }

  WiFiClient* stream = http.getStreamPtr();

  uint8_t buffer[1024];
  int headerRestante = 44;
  bool headerSaltado = false;

  while (http.connected() || stream->available()) {
    extern void loopDisplay();
    loopDisplay();

    int availableBytes = stream->available();
    if (availableBytes <= 0) {
      delay(1);
      continue;
    }

    int bytesRead = stream->readBytes(buffer, min((int)sizeof(buffer), availableBytes));

    if (!headerSaltado) {
      if (bytesRead <= headerRestante) {
        headerRestante -= bytesRead;
        continue;
      } else {
        int offset = headerRestante;
        headerSaltado = true;

        size_t written;
        i2s_write(I2S_NUM_0, buffer + offset, bytesRead - offset, &written, portMAX_DELAY);
      }
    } else {
      size_t written;
      i2s_write(I2S_NUM_0, buffer, bytesRead, &written, portMAX_DELAY);
    }
  }

  http.end();

  delay(50);
  extern void instalarI2SRX();
  instalarI2SRX();

  return true;
}

#endif