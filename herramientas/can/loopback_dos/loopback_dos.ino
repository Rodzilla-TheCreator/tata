// loopback_dos.ino — loopback entre DOS transceptores: la placa aislada soldada (ADuM1201 + B0505S + TJA nuevo)
// y el TJA1050 viejo, con UN solo ESP. 26-nov-2026.
//
// El ESP32 tiene un solo controlador CAN (TWAI), pero sus pines se pueden mover. Se prueban 4 caminos, en modo
// NO_ACK (self-test: no hace falta otro nodo que confirme):
//
//   R1  TX 22 -> placa aislada -> RX 21 de la MISMA placa          (referencia: la placa sola)
//   R2  TX 17 -> TJA viejo     -> RX 16 del MISMO viejo            (referencia: el viejo solo)
//   A   TX 22 -> placa aislada -> BUS -> TJA viejo -> RX 16        <- lo que importa: el aislado TRANSMITE al bus
//   B   TX 17 -> TJA viejo     -> BUS -> placa aislada -> RX 21     (el viejo transmite mal desde oct.: puede fallar)
//
// CABLEADO (placa aislada SIN TOCAR: VIB en 22, VOA en 21):
//   TJA viejo: VCC 5 V y GND del ESP · su TX <- GPIO17 · su RX -> divisor 1k/2k -> GPIO16 (el viejo saca 5 V)
//   CANH aislado <-> CANH viejo · CANL aislado <-> CANL viejo  (cada módulo trae 120 ohm: el bus queda en 60)
//   GND_bus <-> GND del ESP: PUENTE SOLO PARA ESTA PRUEBA (el viejo necesita referencia). Medir el aislamiento ANTES.
//
// El TX que no se usa en cada camino queda en ALTO (recesivo): así el otro transceptor no pisa el bus.
// Corre los 4 caminos al arrancar y repite cada 6 s, para hacer los controles en vivo:
//   control A: soltar CANH entre los dos -> A da 0 (R1 sigue en 20)   ·   control B: soltar el RX del viejo -> A da 0
//
// ESTE SKETCH TRANSMITE. Es para la mesa. Nunca al montacargas.

#include "driver/twai.h"

const int TX_AISL = 22, RX_AISL = 21, TX_VIEJO = 17, RX_VIEJO = 16;
const int N = 20;

struct Camino { const char* nombre; int tx, rx; };
const Camino CAMINOS[] = {
  {"R1  aislado -> aislado (referencia)", TX_AISL, RX_AISL},
  {"R2  viejo   -> viejo   (referencia)", TX_VIEJO, RX_VIEJO},
  {"A   aislado -> BUS -> viejo        ", TX_AISL, RX_VIEJO},
  {"B   viejo   -> BUS -> aislado      ", TX_VIEJO, RX_AISL},
};

void recesivo(int pin) { pinMode(pin, OUTPUT); digitalWrite(pin, HIGH); }

void probar(const Camino& c) {
  // los dos TX en alto; el driver toma el que corresponde
  recesivo(TX_AISL); recesivo(TX_VIEJO);
  pinMode(RX_AISL, INPUT); pinMode(RX_VIEJO, INPUT);
  twai_general_config_t g = TWAI_GENERAL_CONFIG_DEFAULT((gpio_num_t)c.tx, (gpio_num_t)c.rx, TWAI_MODE_NO_ACK);
  g.rx_queue_len = 32; g.tx_queue_len = 4;
  twai_timing_config_t t = TWAI_TIMING_CONFIG_250KBITS();
  twai_filter_config_t f = TWAI_FILTER_CONFIG_ACCEPT_ALL();
  if (twai_driver_install(&g, &t, &f) != ESP_OK || twai_start() != ESP_OK) {
    Serial.printf("%s : FALLA al instalar el driver\n", c.nombre); twai_driver_uninstall(); return;
  }
  int enviadas = 0, recibidas = 0, identicas = 0;
  for (int i = 0; i < N; i++) {
    twai_message_t m = {}; m.identifier = 0x321; m.self = 1; m.data_length_code = 8;
    for (int k = 0; k < 8; k++) m.data[k] = (uint8_t)(i * 17 + k * 29);
    if (twai_transmit(&m, pdMS_TO_TICKS(50)) == ESP_OK) enviadas++;
    twai_message_t r;
    uint32_t t0 = millis();
    while (millis() - t0 < 60) {
      if (twai_receive(&r, pdMS_TO_TICKS(10)) == ESP_OK && r.identifier == 0x321) {
        recibidas++;
        if (r.data_length_code == 8 && memcmp(r.data, m.data, 8) == 0) identicas++;
        break;
      }
    }
  }
  twai_status_info_t st; twai_get_status_info(&st);
  Serial.printf("%s : enviadas %2d · recibidas %2d · identicas %2d · err TX %3lu RX %3lu\n", c.nombre, enviadas,
                recibidas, identicas, (unsigned long)st.tx_error_counter, (unsigned long)st.rx_error_counter);
  twai_stop(); twai_driver_uninstall();
  recesivo(TX_AISL); recesivo(TX_VIEJO);
  delay(50);
}

void setup() {
  recesivo(TX_AISL); recesivo(TX_VIEJO);   // lo primero: nadie pisa el bus
  Serial.begin(115200);
  delay(500);
  Serial.println("\nloopback_dos · 250k · NO_ACK · 20 tramas por camino · se repite cada 6 s");
}

void loop() {
  Serial.println("----------------------------------------------------------------------");
  for (const Camino& c : CAMINOS) probar(c);
  delay(6000);
}
