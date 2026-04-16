#ifndef NETWORK_MANAGER_H
#define NETWORK_MANAGER_H

#include <WiFi.h>
#include <HTTPClient.h>

const char* serverGet = "http://192.168.100.3:5001/ultima_respuesta";

String extraerRespuesta(String json) {
  int start = json.indexOf("\"respuesta\":\"");
  if (start == -1) return "error";

  start += 13;

  String res = "";
  bool escape = false;

  for (int i = start; i < json.length(); i++) {
    char c = json[i];

    if (escape) {
      res += c;
      escape = false;
      continue;
    }

    if (c == '\\') {
      escape = true;
      continue;
    }

    if (c == '"') break;

    res += c;
  }

  return res;
}

String obtenerRespuesta() {
  HTTPClient http;
  http.begin(serverGet);

  int httpCode = http.GET();
  String payload = http.getString();
  http.end();

  return extraerRespuesta(payload);
}

#endif