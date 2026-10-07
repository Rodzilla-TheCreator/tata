// master_falso.ino — un ESP32 que hace del master (nodo 1) frente al multipiloto falso
//
// TaTa · herramientas/can/banco_imitador · ver LEEME.md de esta carpeta
//
// ############################################################################
// #  SOLO BANCO. Este sketch TRANSMITE (SDO y NMT). Va en el bus de diodos    #
// #  de la mesa. NUNCA al montacargas: el master de verdad ya está ahí.       #
// ############################################################################
//
// QUÉ HACE — repite la conversación de arranque grabada el 06-oct (multipiloto.md)
//   1. espera el boot-up 702 00
//   2. lee 0x1000 del nodo 2:   602 40 00 10 00 00 00 00 00   y espera 582 43 00 10 00 …
//      si no contesta en 1 s, reintenta (el real también reintentó)
//   3. NMT START:               000 01 02
//   4. vigila: cada 0x182 y cada heartbeat 702; imprime el 0x182 decodificado cuando
//      cambia, y el período medido cada 5 s
//   5. si pasan 3.5 períodos sin 0x182 → avisa «8.08 simulado», como el master real
//
// Es un CONTROL del imitador, no una copia del master: el real hace más cosas.

#include "driver/twai.h"

#define PIN_TX   GPIO_NUM_21
#define PIN_RX   GPIO_NUM_22

const uint8_t  NODO_MP          = 2;
const uint32_t PERIODO_ESPERADO = 20;   // SUPUESTO, el mismo de multipiloto_falso

enum Fase { ESPERA_BOOTUP, ESPERA_SDO, OPERANDO };
Fase fase = ESPERA_BOOTUP;
uint32_t tFase = 0;

bool mandar(uint32_t id, const uint8_t* d, uint8_t n) {
  twai_message_t m = {};
  m.identifier = id; m.data_length_code = n;
  memcpy(m.data, d, n);
  return twai_transmit(&m, pdMS_TO_TICKS(5)) == ESP_OK;
}

void pedir1000() {
  const uint8_t q[8] = {0x40, 0x00, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00};
  mandar(0x600 + NODO_MP, q, 8);
  fase = ESPERA_SDO; tFase = millis();
  Serial.println("-> 602 lectura de 0x1000");
}

void imprimir182(const uint8_t* d) {
  Serial.printf("182  ");
  for (int i = 0; i < 8; i++) Serial.printf("%02X ", d[i]);
  Serial.printf("|  adelante/atras %3u %s  izq/der %3u %s  trasera %3u  botones%s%s%s%s%s\n",
    d[0], (d[4] & 0x08) ? "ADEL" : (d[4] & 0x10) ? "ATRAS" : "-",
    d[1], (d[4] & 0x04) ? "IZQ"  : (d[4] & 0x02) ? "DER"   : "-",
    d[2],
    (d[5] & 0x08) ? " N" : "", (d[5] & 0x04) ? " S" : "",
    (d[5] & 0x02) ? " E" : "", (d[5] & 0x01) ? " W" : "",
    (d[4] & 0x01) ? " TRASERO" : "");
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n=== master_falso — SOLO BANCO, transmite ===");
  twai_general_config_t g = TWAI_GENERAL_CONFIG_DEFAULT(PIN_TX, PIN_RX, TWAI_MODE_NORMAL);
  g.rx_queue_len = 64; g.tx_queue_len = 8;
  twai_timing_config_t t = TWAI_TIMING_CONFIG_250KBITS();
  twai_filter_config_t f = TWAI_FILTER_CONFIG_ACCEPT_ALL();
  if (twai_driver_install(&g, &t, &f) != ESP_OK || twai_start() != ESP_OK) {
    Serial.println("FALLA: no arrancó el TWAI"); while (true) delay(1000);
  }
  Serial.println("esperando boot-up del nodo 2 (reiniciá el multipiloto falso)");
}

void loop() {
  static uint8_t  ultimo[8] = {0xFF};
  static uint32_t tUlt182 = 0, n182 = 0, tResumen = 0, maxHueco = 0;
  static bool     avisado808 = false;

  twai_message_t m;
  while (twai_receive(&m, 0) == ESP_OK) {
    uint32_t ahora = millis();
    if (m.identifier == 0x700 + NODO_MP && m.data_length_code >= 1) {
      if (m.data[0] == 0x00) { Serial.println("<- 702 00 boot-up"); pedir1000(); }
    } else if (m.identifier == 0x580 + NODO_MP && fase == ESPERA_SDO) {
      bool ok = m.data[0] == 0x43 && m.data[1] == 0x00 && m.data[2] == 0x10 && m.data[3] == 0x00;
      Serial.printf("<- 582 %s\n", ok ? "43 00 10 00 … OK, igual que el real" : "RESPUESTA DISTINTA del real");
      if (ok) {
        const uint8_t s[2] = {0x01, NODO_MP};
        mandar(0x000, s, 2);
        Serial.println("-> 000 01 02 NMT START");
        fase = OPERANDO; tUlt182 = ahora; avisado808 = false;
      }
    } else if (m.identifier == 0x180 + NODO_MP) {
      if (tUlt182) maxHueco = max(maxHueco, ahora - tUlt182);
      tUlt182 = ahora; n182++; avisado808 = false;
      if (memcmp(ultimo, m.data, 8) != 0) { memcpy(ultimo, m.data, 8); imprimir182(m.data); }
    }
  }

  uint32_t ahora = millis();
  if (fase == ESPERA_SDO && ahora - tFase > 1000) {
    Serial.println("   sin respuesta a 0x1000 en 1 s -> reintento (el real también reintenta)");
    pedir1000();
  }
  if (fase == OPERANDO && !avisado808 && ahora - tUlt182 > PERIODO_ESPERADO * 7 / 2) {
    Serial.printf("!! 8.08 SIMULADO: %lu ms sin 0x182 (3.5 períodos de %lu)\n",
                  (unsigned long)(ahora - tUlt182), (unsigned long)PERIODO_ESPERADO);
    avisado808 = true;
  }
  if (fase == OPERANDO && ahora - tResumen >= 5000) {
    Serial.printf("   resumen 5 s: %lu tramas 0x182 (%.1f Hz), hueco máximo %lu ms\n",
                  (unsigned long)n182, n182 / 5.0, (unsigned long)maxHueco);
    n182 = 0; maxHueco = 0; tResumen = ahora;
  }
}
