#include "display_manager.h"
#include "audio_manager.h"
#include "network_manager.h"

#include <driver/i2s.h>
#include <HTTPClient.h>

// 🎤 MIC
#define I2S_MIC_WS    25
#define I2S_MIC_SD    32
#define I2S_MIC_BCLK  33

// 🎮 BOTONES
#define BTN_RECORD 18
#define BTN_REPLAY 21
#define BTN_CANCEL 22

#define CHUNK 512
int32_t micBuffer[CHUNK];

const char* serverAudio     = "http://192.168.100.3:5001/audio";
const char* serverFinal     = "http://192.168.100.3:5001/finalizar";
const char* serverAudioFile = "http://192.168.100.3:5001/audio_response";

// 🔥 instalar MIC (RX)
void instalarI2SRX() {
  i2s_driver_uninstall(I2S_NUM_0);

  i2s_config_t configRX = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = 16000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .dma_buf_count = 8,
    .dma_buf_len = 64
  };

  i2s_pin_config_t pinRX = {
    .bck_io_num = I2S_MIC_BCLK,
    .ws_io_num = I2S_MIC_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_MIC_SD
  };

  i2s_driver_install(I2S_NUM_0, &configRX, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pinRX);
  i2s_zero_dma_buffer(I2S_NUM_0);

  i2sEnTX = false;
  Serial.println("🎤 MIC listo");
}

// 🔥 esperar audio del backend
void esperarAudioYReproducir() {
  bool audioListo = false;

  for (int i = 0; i < 15; i++) { // ~7.5s
    HTTPClient http;
    http.begin(serverAudioFile);

    int code = http.GET();
    http.end();

    if (code == 200) {
      audioListo = true;
      break;
    }

    delay(500);
  }

  if (audioListo) {
    Serial.println("🔊 Audio listo, reproduciendo...");
    reproducirAudioStream(serverAudioFile);
  } else {
    Serial.println("❌ Audio nunca estuvo listo");
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(BTN_RECORD, INPUT_PULLUP);
  pinMode(BTN_REPLAY, INPUT_PULLUP);
  pinMode(BTN_CANCEL, INPUT_PULLUP);

  initDisplay();

  WiFi.begin("Totalplay-2.4G-be98", "eg4UztkzJsF8ECBH");
  while (WiFi.status() != WL_CONNECTED) delay(500);

  instalarI2SRX();

  Serial.println("ESP listo");
}

void loop() {
  loopDisplay();

    // 🔴 CANCELAR reproducción
  if (digitalRead(BTN_CANCEL) == LOW) {
    delay(100);

    Serial.println("⛔ Cancelando reproducción...");

    // detener audio (reset a RX mata el TX actual)
    instalarI2SRX();

    // limpiar display
    mostrarTexto("Cancelado");

    while (digitalRead(BTN_CANCEL) == LOW); // evitar rebotes
    return;
  }

  // 🔘 REPLAY
  if (digitalRead(BTN_REPLAY) == LOW) {
    delay(200);

    String respuesta = obtenerRespuesta();
    mostrarTexto(respuesta);

    esperarAudioYReproducir();

    while (digitalRead(BTN_REPLAY) == LOW); // evitar múltiples ejecuciones
  }

  // 🔘 GRABAR
  if (digitalRead(BTN_RECORD) == LOW) {
    delay(50);

    // asegurar modo RX
    if (i2sEnTX) {
      instalarI2SRX();
    }

    Serial.println("🎤 Grabando...");
    mostrarTexto("Escuchando...");

    size_t bytesRead = 0;

    while (digitalRead(BTN_RECORD) == LOW) {

      i2s_read(
        I2S_NUM_0,
        micBuffer,
        sizeof(micBuffer),
        &bytesRead,
        portMAX_DELAY
      );

      HTTPClient http;
      http.begin(serverAudio);
      http.addHeader("Content-Type", "application/octet-stream");

      int res = http.POST((uint8_t*)micBuffer, bytesRead);
      Serial.println(res);

      http.end();
    }

    Serial.println("🛑 Fin grabacion");
    mostrarTexto("Procesando...");

    HTTPClient http;
    http.begin(serverFinal);
    http.addHeader("Content-Type", "application/json");

    http.POST("{\"modoIA\":true}");
    http.end();

    // 🔥 flujo correcto
    String respuesta = obtenerRespuesta();
    mostrarTexto(respuesta);

    esperarAudioYReproducir();

    while (digitalRead(BTN_RECORD) == LOW);
  }
}