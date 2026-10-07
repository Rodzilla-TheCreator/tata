// multipiloto_falso.ino — un ESP32 que se hace pasar por el nodo 2 (Multi-Pilot 1)
//
// TaTa · herramientas/can/banco_imitador · ver LEEME.md de esta carpeta
//
// ############################################################################
// #  SOLO BANCO. Este sketch TRANSMITE. Va en el bus de diodos de la mesa,    #
// #  contra master_falso.ino. NUNCA al montacargas: ni por el DB9 ni por la   #
// #  ficha del multipiloto, y menos con el multipiloto real enchufado (dos   #
// #  nodos 2 en el mismo bus).                                               #
// ############################################################################
//
// QUÉ IMITA — lo grabado el 06-oct (herramientas/can/multipiloto.md)
//   1. al arrancar: boot-up            702 [1] 00
//   2. contesta la lectura de 0x1000:  602 40 00 10 00 … → 582 43 00 10 00 00 00 00 00
//      cualquier otra lectura SDO: aborto 0x06020000 (objeto inexistente) y se avisa
//   3. tras NMT START (000 01 02 o 000 01 00): manda 182 cada PERIODO_182_MS
//      y heartbeat 702 [1] 05 cada PERIODO_HB_MS. En pre-operacional, heartbeat 7F
//
// LO QUE NO SE SABE TODAVÍA (salen del log del 06-oct, no se adivinan)
//   · PERIODO_182_MS: cada cuánto manda el real el 0x182. Hoy es un supuesto
//   · PERIODO_HB_MS:  cada cuánto manda el real su heartbeat. Hoy es un supuesto
//   · si el 0x182 va por tiempo o por SYNC (080)
//   · si b6 es un contador: en la grabación «sin cambios»
//
// MANDO, por el monitor serie (115200, fin de línea \n). Cada orden renueva el latido:
//   a N    joystick adelante, magnitud N (0–255)      t N    atrás
//   i N    izquierda                                  d N    derecha
//   n / s / e / w      botón north / south / east / west (se mantiene hasta «0»)
//   r      botón trasero                              0      todo a cero
//   .      solo latido (no cambia nada)
//
// WATCHDOG: si pasan WATCHDOG_MS sin ninguna línea por serie, todo vuelve a CERO y se
// avisa. Es la misma regla de docs/10, en chico. Y arranca en cero: regla 4 de docs/20.

#include "driver/twai.h"

#define PIN_TX   GPIO_NUM_21
#define PIN_RX   GPIO_NUM_22

const uint8_t  NODO           = 2;
const uint32_t PERIODO_182_MS = 20;    // SUPUESTO — reemplazar por lo medido en el log
const uint32_t PERIODO_HB_MS  = 500;   // SUPUESTO — reemplazar por lo medido en el log
const uint32_t WATCHDOG_MS    = 200;

enum Estado { PREOP, OPERACIONAL, PARADO };
Estado estado = PREOP;

// las 8 posiciones de 0x182 (tabla de multipiloto.md)
uint8_t b0 = 0, b1 = 0, b2 = 0, b4 = 0, b5 = 0;
uint32_t ultimoLatido = 0;
bool     enCero = true;

bool mandar(uint32_t id, const uint8_t* d, uint8_t n) {
  twai_message_t m = {};
  m.identifier = id; m.data_length_code = n;
  memcpy(m.data, d, n);
  return twai_transmit(&m, pdMS_TO_TICKS(5)) == ESP_OK;
}

void todoACero() { b0 = b1 = b2 = b4 = b5 = 0; }

void armar182(uint8_t* d) {
  d[0] = b0; d[1] = b1; d[2] = b2;
  d[3] = (b5 & (0x02 | 0x01)) ? 255 : 0;   // east / west apretados
  d[4] = b4; d[5] = b5;
  d[6] = 0;                                // «sin cambios» en la grabación
  d[7] = (b5 & (0x08 | 0x04)) ? 255 : 0;   // north / south apretados
}

void atenderSDO(const twai_message_t& m) {
  if (m.data_length_code < 4) return;
  uint8_t cmd = m.data[0];
  uint16_t idx = m.data[1] | (m.data[2] << 8);
  uint8_t sub = m.data[3];
  if (cmd == 0x40 && idx == 0x1000 && sub == 0) {
    const uint8_t r[8] = {0x43, 0x00, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00};
    mandar(0x580 + NODO, r, 8);
    Serial.println("SDO  lectura 0x1000 -> contestada 0 (como el real)");
    return;
  }
  const uint8_t ab[8] = {0x80, m.data[1], m.data[2], sub, 0x00, 0x00, 0x02, 0x06};
  mandar(0x580 + NODO, ab, 8);
  Serial.printf("SDO  NO CONOCIDA: cmd %02X idx %04X sub %02X -> aborto. El real puede contestar otra cosa\n",
                cmd, idx, sub);
}

void atenderNMT(const twai_message_t& m) {
  if (m.data_length_code < 2) return;
  if (m.data[1] != NODO && m.data[1] != 0) return;
  switch (m.data[0]) {
    case 0x01: estado = OPERACIONAL; todoACero(); Serial.println("NMT  START -> operacional, en cero"); break;
    case 0x02: estado = PARADO;      Serial.println("NMT  STOP");  break;
    case 0x80: estado = PREOP;       Serial.println("NMT  PRE-OP"); break;
    case 0x81: case 0x82:
      Serial.println("NMT  RESET -> boot-up de nuevo");
      estado = PREOP; todoACero();
      { const uint8_t bu = 0x00; mandar(0x700 + NODO, &bu, 1); }
      break;
  }
}

void leerSerie() {
  static char linea[24]; static int n = 0;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\r') continue;
    if (c != '\n') { if (n < 23) linea[n++] = c; continue; }
    linea[n] = 0; n = 0;
    ultimoLatido = millis();
    if (enCero) { enCero = false; Serial.println("LATIDO de vuelta"); }
    int v = constrain(atoi(linea + 1), 0, 255);
    switch (linea[0]) {
      case 'a': b0 = v; b4 = (b4 & ~0x18) | (v ? 0x08 : 0); break;
      case 't': b0 = v; b4 = (b4 & ~0x18) | (v ? 0x10 : 0); break;
      case 'i': b1 = v; b4 = (b4 & ~0x06) | (v ? 0x04 : 0); break;
      case 'd': b1 = v; b4 = (b4 & ~0x06) | (v ? 0x02 : 0); break;
      case 'n': b5 |= 0x08; break;
      case 's': b5 |= 0x04; break;
      case 'e': b5 |= 0x02; break;
      case 'w': b5 |= 0x01; break;
      case 'r': b4 |= 0x01; break;
      case '0': todoACero(); break;
      default: break;                       // '.' y cualquier otra: solo latido
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== multipiloto_falso — SOLO BANCO, transmite ===");
  twai_general_config_t g = TWAI_GENERAL_CONFIG_DEFAULT(PIN_TX, PIN_RX, TWAI_MODE_NORMAL);
  g.rx_queue_len = 32; g.tx_queue_len = 16;
  twai_timing_config_t t = TWAI_TIMING_CONFIG_250KBITS();
  twai_filter_config_t f = TWAI_FILTER_CONFIG_ACCEPT_ALL();
  if (twai_driver_install(&g, &t, &f) != ESP_OK || twai_start() != ESP_OK) {
    Serial.println("FALLA: no arrancó el TWAI"); while (true) delay(1000);
  }
  delay(300);                                // el real bootea tarde; el master reintenta
  const uint8_t bu = 0x00;
  mandar(0x700 + NODO, &bu, 1);
  Serial.println("boot-up 702 00 enviado");
}

void loop() {
  twai_message_t m;
  while (twai_receive(&m, 0) == ESP_OK) {
    if (m.identifier == 0x000)              atenderNMT(m);
    else if (m.identifier == 0x600 + NODO)  atenderSDO(m);
  }
  leerSerie();

  if (!enCero && millis() - ultimoLatido > WATCHDOG_MS) {
    todoACero(); enCero = true;
    Serial.println("WATCHDOG: sin latido por serie -> todo a CERO");
  }

  static uint32_t t182 = 0, thb = 0;
  uint32_t ahora = millis();
  if (estado == OPERACIONAL && ahora - t182 >= PERIODO_182_MS) {
    t182 = ahora;
    uint8_t d[8]; armar182(d);
    mandar(0x180 + NODO, d, 8);
  }
  if (ahora - thb >= PERIODO_HB_MS) {
    thb = ahora;
    uint8_t s = (estado == OPERACIONAL) ? 0x05 : (estado == PARADO ? 0x04 : 0x7F);
    mandar(0x700 + NODO, &s, 1);
  }
}
