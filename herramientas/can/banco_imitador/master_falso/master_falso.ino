// master_falso.ino — un ESP32 que hace del master (nodo 1) en la mesa
//
// TaTa · herramientas/can/banco_imitador · ver LEEME.md de esta carpeta
//
// ############################################################################
// #  SOLO BANCO. Este sketch TRANSMITE (SDO, NMT y SYNC). Va en la mesa, con  #
// #  el multipiloto falso (bus de diodos) o con el multipiloto de REPUESTO    #
// #  real (TJA nuevo). NUNCA al montacargas: el master de verdad ya está ahí. #
// ############################################################################
//
// QUÉ HACE — repite la conversación de arranque grabada el 06-oct (multipiloto.md)
//   1. espera al nodo 2: su boot-up 702 00, o su latido de pre-operacional 702 7F
//      (si el multipiloto arrancó antes que este ESP32 y el boot-up se perdió)
//   2. lee 0x1000 del nodo 2:   602 40 00 10 00 00 00 00 00   y espera 582 43 00 10 00 …
//      si no contesta en 1 s, reintenta (el real también reintentó)
//   3. NMT START:               000 01 02
//   4. vigila: cada 0x182 y cada heartbeat 702; imprime el 0x182 decodificado cuando
//      cambia, y el período medido cada 5 s
//   5. si pasan 3.5 períodos sin 0x182 → avisa «8.08 simulado», como el master real
//   6. cualquier otro identificador se imprime la primera vez que aparece
//
// ESTE NODO DA ACK. Con un nodo solo en la mesa (el multipiloto), nadie le da ACK y sus
// tramas no las ve ni un receptor en LISTEN_ONLY: por eso en banco va este, no escucha_can.
//
// COMANDOS por el monitor serie (115200, fin de línea \n):
//   n        manda NMT START ya (000 01 02), sin esperar la lectura de 0x1000
//   r        vuelve a leer 0x1000
//   y <ms>   manda SYNC (080) cada <ms> milisegundos; «y 0» lo apaga. Para probar si el
//            0x182 sale solo o espera SYNC (en el equipo hay SYNC en el bus)
//
// Es un CONTROL, no una copia del master: el real hace más cosas.

#include "driver/twai.h"

// Mismo armado que escucha_can y sdo_lee desde el 14-oct: TX del TJA ← GPIO 22,
// RX del TJA → 1k/2k → GPIO 21
#define PIN_TX   GPIO_NUM_22
#define PIN_RX   GPIO_NUM_21

const uint8_t  NODO_MP          = 2;
const uint32_t PERIODO_ESPERADO = 20;   // SUPUESTO: reemplazar por lo medido (resumen 5 s)

enum Fase { ESPERA_BOOTUP, ESPERA_SDO, OPERANDO };
Fase fase = ESPERA_BOOTUP;
uint32_t tFase = 0;
uint32_t periodoSync = 0, tSync = 0;

// identificadores ya vistos (para imprimir solo la primera vez)
uint32_t vistos[64]; int nVistos = 0;
bool yaVisto(uint32_t id) {
  for (int i = 0; i < nVistos; i++) if (vistos[i] == id) return true;
  if (nVistos < 64) vistos[nVistos++] = id;
  return false;
}

bool mandar(uint32_t id, const uint8_t* d, uint8_t n) {
  twai_message_t m = {};
  m.identifier = id; m.data_length_code = n;
  if (n) memcpy(m.data, d, n);
  return twai_transmit(&m, pdMS_TO_TICKS(5)) == ESP_OK;
}

void pedir1000() {
  const uint8_t q[8] = {0x40, 0x00, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00};
  mandar(0x600 + NODO_MP, q, 8);
  fase = ESPERA_SDO; tFase = millis();
  Serial.println("-> 602 lectura de 0x1000");
}

void nmtStart() {
  const uint8_t s[2] = {0x01, NODO_MP};
  mandar(0x000, s, 2);
  Serial.println("-> 000 01 02 NMT START");
  fase = OPERANDO;
}

void imprimir182(const uint8_t* d) {
  Serial.printf("%8lu  182  ", (unsigned long)millis());
  for (int i = 0; i < 8; i++) Serial.printf("%02X ", d[i]);
  Serial.printf("|  adelante/atras %3u %s  izq/der %3u %s  trasera %3u  botones%s%s%s%s%s\n",
    d[0], (d[4] & 0x08) ? "ADEL" : (d[4] & 0x10) ? "ATRAS" : "-",
    d[1], (d[4] & 0x04) ? "IZQ"  : (d[4] & 0x02) ? "DER"   : "-",
    d[2],
    (d[5] & 0x08) ? " N" : "", (d[5] & 0x04) ? " S" : "",
    (d[5] & 0x02) ? " E" : "", (d[5] & 0x01) ? " W" : "",
    (d[4] & 0x01) ? " TRASERO" : "");
}

void imprimirCruda(const twai_message_t& m, const char* nota) {
  Serial.printf("%8lu  %03lX [%d] ", (unsigned long)millis(), (unsigned long)m.identifier,
                m.data_length_code);
  for (int i = 0; i < m.data_length_code; i++) Serial.printf("%02X ", m.data[i]);
  Serial.printf(" %s\n", nota);
}

void leerSerie() {
  static char linea[24]; static int n = 0;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\r') continue;
    if (c != '\n') { if (n < 23) linea[n++] = c; continue; }
    linea[n] = 0; n = 0;
    if (linea[0] == 'n') nmtStart();
    else if (linea[0] == 'r') pedir1000();
    else if (linea[0] == 'y') {
      periodoSync = (uint32_t)atoi(linea + 1);
      Serial.printf("SYNC %s\n", periodoSync ? "encendido" : "apagado");
      if (periodoSync) Serial.printf("     cada %lu ms\n", (unsigned long)periodoSync);
    }
  }
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
  Serial.println("esperando al nodo 2 (boot-up 702 00 o latido 702 7F)");
  Serial.println("comandos: n = NMT START · r = leer 0x1000 · y <ms> = SYNC");
}

void loop() {
  static uint8_t  ultimo[8] = {0xFF};
  static int      ultimoHb = -1;
  static uint32_t tUlt182 = 0, n182 = 0, tResumen = 0, maxHueco = 0;
  static bool     avisado808 = false;

  leerSerie();

  twai_message_t m;
  while (twai_receive(&m, 0) == ESP_OK) {
    uint32_t ahora = millis();
    if (m.identifier == 0x700 + NODO_MP && m.data_length_code >= 1) {
      if (m.data[0] != ultimoHb) {
        ultimoHb = m.data[0];
        imprimirCruda(m, m.data[0] == 0x00 ? "<- boot-up" :
                         m.data[0] == 0x7F ? "<- latido: PRE-OPERACIONAL" :
                         m.data[0] == 0x05 ? "<- latido: OPERACIONAL" :
                         m.data[0] == 0x04 ? "<- latido: DETENIDO" : "<- latido: ¿estado?");
      }
      if (fase == ESPERA_BOOTUP && (m.data[0] == 0x00 || m.data[0] == 0x7F)) pedir1000();
      if (m.data[0] == 0x00 && fase == OPERANDO) {
        Serial.println("   el nodo 2 se reinició → se repite el arranque");
        pedir1000();
      }
    } else if (m.identifier == 0x580 + NODO_MP) {
      imprimirCruda(m, "<- respuesta SDO");
      if (fase == ESPERA_SDO) {
        bool ok = m.data[0] == 0x43 && m.data[1] == 0x00 && m.data[2] == 0x10 && m.data[3] == 0x00;
        Serial.printf("   %s\n", ok ? "43 00 10 00 … igual que en el equipo" : "RESPUESTA DISTINTA de la del equipo");
        if (ok) { nmtStart(); tUlt182 = ahora; avisado808 = false; }
      }
    } else if (m.identifier == 0x180 + NODO_MP) {
      if (tUlt182) maxHueco = max(maxHueco, ahora - tUlt182);
      tUlt182 = ahora; n182++; avisado808 = false;
      if (memcmp(ultimo, m.data, 8) != 0) { memcpy(ultimo, m.data, 8); imprimir182(m.data); }
    } else if (!yaVisto(m.identifier)) {
      imprimirCruda(m, "<- identificador nuevo");
    }
  }

  uint32_t ahora = millis();
  if (periodoSync && ahora - tSync >= periodoSync) { tSync = ahora; mandar(0x080, nullptr, 0); }
  if (fase == ESPERA_SDO && ahora - tFase > 1000) {
    Serial.println("   sin respuesta a 0x1000 en 1 s -> reintento (el real también reintenta)");
    pedir1000();
  }
  if (fase == OPERANDO && tUlt182 && !avisado808 && ahora - tUlt182 > PERIODO_ESPERADO * 7 / 2) {
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
