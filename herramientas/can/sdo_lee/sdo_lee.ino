// sdo_lee.ino — lee objetos CANopen por SDO. SOLO LECTURA: este archivo no sabe escribir.
//
// TaTa · herramientas/can · ESP32 + TJA1050 NUEVO (el viejo no transmite)
//
// ############################################################################
// #  TRANSMITE: pide lecturas (SDO upload, comandos 0x40 / 0x60 / 0x70) y    #
// #  da ACK a todo el bus. NO hay ningún comando de escritura (0x2x) en este  #
// #  archivo. Que siga así: escribir va en otro sketch, con su decisión.      #
// ############################################################################
//
// Antes de transmitir escucha 3 s: si no hay tráfico válido a 250k o hay errores RX, no
// transmite nada y lo dice. Así un bus equivocado no recibe ni un bit nuestro.
//
// Cableado: el de siempre. TX = GPIO 22 → TX del TJA nuevo; RX del TJA → 1k/2k → GPIO 21.
//
// Comandos por el monitor serie (115200, fin de línea \n):
//   l <nodo> <índice hex> <sub>   lee un objeto            ej:  l 1 1000 0
//   id <nodo>                     identidad: 1000, 1008, 1009, 100A, 1018.1-4
//   esperados <nodo>              0x1F81 sub 0..127 (CiA 302: qué nodos espera el Master)
//   barre <nodo> <desde> <hasta>  qué objetos existen (sub 0) en ese rango, ej: barre 1 2000 20FF

#include "driver/twai.h"

#define PIN_TX GPIO_NUM_22
#define PIN_RX GPIO_NUM_21
const uint32_t ESPERA_MS = 300;     // respuesta SDO
const uint32_t PAUSA_MS  = 40;      // entre pedidos: no cargar el bus

bool habilitado = false;

const char* abortTexto(uint32_t c) {
  switch (c) {
    case 0x05040000: return "timeout de protocolo SDO";
    case 0x05040001: return "comando SDO no valido";
    case 0x06010000: return "acceso no soportado";
    case 0x06010001: return "objeto de solo escritura";
    case 0x06020000: return "OBJETO NO EXISTE";
    case 0x06070010: return "tipo de dato no coincide";
    case 0x06090011: return "SUBINDICE NO EXISTE";
    case 0x08000000: return "error general";
    case 0x08000020: return "no se puede transferir/guardar";
    case 0x08000021: return "control local lo impide";
    case 0x08000022: return "estado del equipo lo impide";
    default:         return "?";
  }
}

bool mandar(uint32_t id, const uint8_t* d) {
  twai_message_t m = {}; m.identifier = id; m.data_length_code = 8; memcpy(m.data, d, 8);
  return twai_transmit(&m, pdMS_TO_TICKS(50)) == ESP_OK;
}

// espera la respuesta 0x580+nodo; descarta todo lo demás
bool respuesta(int nodo, uint8_t* r) {
  uint32_t fin = millis() + ESPERA_MS; twai_message_t m;
  while ((int32_t)(fin - millis()) > 0)
    if (twai_receive(&m, pdMS_TO_TICKS(10)) == ESP_OK && !m.extd && m.identifier == 0x580u + nodo) {
      memcpy(r, m.data, 8); return true;
    }
  return false;
}

uint32_t codigo(const uint8_t* r) { return r[4] | r[5] << 8 | r[6] << 16 | (uint32_t)r[7] << 24; }

// 0 = ok, 1 = abort, 2 = sin respuesta. Llena datos/largo.
int leer(int nodo, uint16_t idx, uint8_t sub, uint8_t* datos, int& largo, uint32_t& abortc) {
  uint8_t q[8] = {0x40, (uint8_t)idx, (uint8_t)(idx >> 8), sub, 0, 0, 0, 0}, r[8];
  twai_message_t basura; while (twai_receive(&basura, 0) == ESP_OK) {}
  if (!mandar(0x600 + nodo, q) || !respuesta(nodo, r)) return 2;
  if (r[0] == 0x80) { abortc = codigo(r); return 1; }
  if ((r[0] & 0xE2) == 0x42) {                          // expedito
    largo = (r[0] & 0x01) ? 4 - ((r[0] >> 2) & 3) : 4; memcpy(datos, r + 4, largo); return 0;
  }
  if ((r[0] & 0xE2) == 0x40) {                          // segmentado: pedir los trozos
    largo = 0; uint8_t t = 0;
    for (int k = 0; k < 40; k++) {
      uint8_t s[8] = {(uint8_t)(0x60 | t), 0, 0, 0, 0, 0, 0, 0};
      if (!mandar(0x600 + nodo, s) || !respuesta(nodo, r)) return 2;
      if (r[0] == 0x80) { abortc = codigo(r); return 1; }
      int n = 7 - ((r[0] >> 1) & 7);
      for (int i = 0; i < n && largo < 64; i++) datos[largo++] = r[1 + i];
      if (r[0] & 1) return 0;
      t ^= 0x10;
    }
    return 0;
  }
  return 2;
}

void mostrar(int nodo, uint16_t idx, uint8_t sub) {
  uint8_t d[64]; int n = 0; uint32_t a = 0;
  int e = leer(nodo, idx, sub, d, n, a);
  Serial.printf("nodo %2d  %04X.%02X  ", nodo, idx, sub);
  if (e == 2) { Serial.println("SIN RESPUESTA"); delay(PAUSA_MS); return; }
  if (e == 1) { Serial.printf("ABORT %08lX  %s\n", (unsigned long)a, abortTexto(a)); delay(PAUSA_MS); return; }
  uint32_t v = 0; for (int i = 0; i < n && i < 4; i++) v |= (uint32_t)d[i] << (8 * i);
  Serial.printf("= 0x%08lX (%lu)  bytes:", (unsigned long)v, (unsigned long)v);
  for (int i = 0; i < n; i++) Serial.printf(" %02X", d[i]);
  Serial.print("  '");
  for (int i = 0; i < n; i++) Serial.print(d[i] >= 32 && d[i] < 127 ? (char)d[i] : '.');
  Serial.println("'");
  delay(PAUSA_MS);
}

void setup() {
  Serial.begin(115200); delay(700);
  Serial.println("\n=== sdo_lee · SOLO LECTURA · este sketch TRANSMITE pedidos de lectura ===");
  twai_general_config_t g = TWAI_GENERAL_CONFIG_DEFAULT(PIN_TX, PIN_RX, TWAI_MODE_LISTEN_ONLY);
  g.rx_queue_len = 64;
  twai_timing_config_t t = TWAI_TIMING_CONFIG_250KBITS();
  twai_filter_config_t f = TWAI_FILTER_CONFIG_ACCEPT_ALL();
  twai_driver_install(&g, &t, &f); twai_start();
  uint32_t fin = millis() + 3000, validas = 0; twai_message_t m;
  while (millis() < fin) if (twai_receive(&m, pdMS_TO_TICKS(20)) == ESP_OK) validas++;
  twai_status_info_t st; twai_get_status_info(&st);
  Serial.printf("Escucha previa 3 s (sin transmitir): %lu tramas, %lu errores RX\n",
                (unsigned long)validas, (unsigned long)st.rx_error_counter);
  twai_stop(); twai_driver_uninstall();
  if (validas < 20 || st.rx_error_counter > 0) {
    Serial.println("NO TRANSMITO: no hay bus sano a 250k. Reiniciar cuando lo haya.");
    return;
  }
  g.mode = TWAI_MODE_NORMAL; g.tx_queue_len = 4;
  twai_driver_install(&g, &t, &f); twai_start(); habilitado = true;
  Serial.println("Bus sano. Modo normal. Comandos: l <n> <idx> <sub> · id <n> · esperados <n> · barre <n> <desde> <hasta>");
}

void loop() {
  if (!habilitado || !Serial.available()) { delay(5); return; }
  String s = Serial.readStringUntil('\n'); s.trim();
  int n; unsigned idx, sub, hasta;
  if (sscanf(s.c_str(), "l %d %x %u", &n, &idx, &sub) == 3) mostrar(n, idx, sub);
  else if (sscanf(s.c_str(), "id %d", &n) == 1) {
    mostrar(n, 0x1000, 0); mostrar(n, 0x1008, 0); mostrar(n, 0x1009, 0); mostrar(n, 0x100A, 0);
    for (int k = 1; k <= 4; k++) mostrar(n, 0x1018, k);
  }
  else if (sscanf(s.c_str(), "esperados %d", &n) == 1) {
    for (int k = 0; k <= 127; k++) {
      uint8_t d[64]; int l = 0; uint32_t a = 0; int e = leer(n, 0x1F81, k, d, l, a);
      if (e == 0) Serial.printf("  1F81.%02X (nodo %3d) = %02X %02X %02X %02X\n", k, k, d[0], d[1], d[2], d[3]);
      else if (e == 1) { Serial.printf("  1F81.%02X ABORT %08lX %s\n", k, (unsigned long)a, abortTexto(a)); if (k == 0) break; }
      else { Serial.printf("  1F81.%02X SIN RESPUESTA\n", k); if (k == 0) break; }
      delay(PAUSA_MS);
    }
  }
  else if (sscanf(s.c_str(), "barre %d %x %x", &n, &idx, &hasta) == 3) {
    for (unsigned i = idx; i <= hasta; i++) {
      uint8_t d[64]; int l = 0; uint32_t a = 0; int e = leer(n, i, 0, d, l, a);
      if (e == 0) Serial.printf("  %04X existe, sub0 = %02X\n", i, d[0]);
      else if (e == 1 && a != 0x06020000) Serial.printf("  %04X existe? ABORT %08lX %s\n", i, (unsigned long)a, abortTexto(a));
      else if (e == 2) { Serial.printf("  %04X SIN RESPUESTA, paro\n", i); break; }
      delay(PAUSA_MS);
    }
    Serial.println("  fin del barrido");
  }
  else Serial.println("? comandos: l <n> <idx> <sub> · id <n> · esperados <n> · barre <n> <desde> <hasta>");
}
