#ifndef DISPLAY_MANAGER_H
#define DISPLAY_MANAGER_H

#include <MD_Parola.h>
#include <MD_MAX72xx.h>
#include <SPI.h>

#define HARDWARE_TYPE MD_MAX72XX::FC16_HW
#define MAX_DEVICES 4
#define DIN_PIN 23
#define CS_PIN  5
#define CLK_PIN 4

MD_Parola display = MD_Parola(HARDWARE_TYPE, DIN_PIN, CLK_PIN, CS_PIN, MAX_DEVICES);

String textoDisplay = "";

void initDisplay() {
  display.begin();
  display.setIntensity(3);
  display.setSpeed(40);
  display.displayClear();
  display.displayText("Listo", PA_CENTER, 100, 0, PA_PRINT, PA_NO_EFFECT);
}

String limpiarTexto(String text) {
  text.replace("\n", " ");
  text.replace("\r", " ");
  text.replace("\"", "");
  text.trim();
  return text;
}

void mostrarTexto(String texto) {
  textoDisplay = limpiarTexto(texto);

  display.displayClear();
  display.displayReset();

  display.displayText(
    textoDisplay.c_str(),
    PA_LEFT,
    30,
    0,
    PA_SCROLL_LEFT,
    PA_SCROLL_LEFT
  );
}

void loopDisplay() {
  display.displayAnimate();
}

#endif