// prueba_can.ino — valida la cadena ESP32 + conversor + TJA1050 contra sí misma
//
// TaTa · herramientas/can · ver herramientas/can/protoboard_can.svg
//
// QUÉ HACE
//   Pone el TWAI del ESP32 en modo self-test (NO_ACK): transmite tramas y las
//   recibe él mismo, pasando por el transceptor. Si el eco vuelve completo, la
//   cadena entera funciona: pines, conversor de nivel, alimentación y TJA1050.
//
// EL CONTROL DE FALSACIÓN — sin esto la prueba no vale nada
//   Corrida 1: con el transceptor conectado      →  debe dar ECO COMPLETO
//   Corrida 2: desconectá el cable de RX del     →  debe dar CERO RECIBIDAS
//              conversor al ESP32
//   Si la corrida 2 también da eco, el lazo se está cerrando adentro del ESP32
//   y esta prueba NO está midiendo el transceptor. El sketch te lo dice.
//
// ############################################################################
// #  ESTE SKETCH TRANSMITE. NUNCA se conecta al montacargas con este código.  #
// #  Para el equipo va escucha_can.ino, en TWAI_MODE_LISTEN_ONLY.             #
// ############################################################################

#include "driver/twai.h"

#define PIN_TX   GPIO_NUM_21     // va al LV1 del conversor
#define PIN_RX   GPIO_NUM_22     // viene del LV2 del conversor

const int   N_TRAMAS   = 20;
const int   ESPERA_MS  = 120;    // por trama, antes de darla por perdida
const long  BAUD_BUS   = 250000; // el del EDR18N2, segun docs/16

int enviadas = 0, recibidas = 0, correctas = 0;

void banner(const char* t) {
  Serial.println();
  Serial.println("========================================================");
  Serial.print  ("  "); Serial.println(t);
  Serial.println("========================================================");
}

bool arrancarTWAI() {
  twai_general_config_t g = TWAI_GENERAL_CONFIG_DEFAULT(PIN_TX, PIN_RX, TWAI_MODE_NO_ACK);
  g.rx_queue_len = 32;
  g.tx_queue_len = 32;
  twai_timing_config_t t = TWAI_TIMING_CONFIG_250KBITS();
  twai_filter_config_t f = TWAI_FILTER_CONFIG_ACCEPT_ALL();

  if (twai_driver_install(&g, &t, &f) != ESP_OK) {
    Serial.println("FALLA: no se pudo instalar el driver TWAI.");
    return false;
  }
  if (twai_start() != ESP_OK) {
    Serial.println("FALLA: no se pudo arrancar el TWAI.");
    return false;
  }
  return true;
}

// Manda una trama y espera su propio eco. Devuelve true si volvio identica.
bool unaVuelta(int n) {
  twai_message_t tx = {};
  tx.identifier       = 0x100 + n;
  tx.extd             = 0;
  tx.data_length_code = 8;
  for (int i = 0; i < 8; i++) tx.data[i] = (uint8_t)(n * 8 + i);

  if (twai_transmit(&tx, pdMS_TO_TICKS(ESPERA_MS)) != ESP_OK) {
    Serial.printf("  trama %2d  NO SE PUDO TRANSMITIR\n", n);
    return false;
  }
  enviadas++;

  twai_message_t rx;
  if (twai_receive(&rx, pdMS_TO_TICKS(ESPERA_MS)) != ESP_OK) {
    Serial.printf("  trama %2d  enviada, SIN ECO\n", n);
    return false;
  }
  recibidas++;

  bool igual = (rx.identifier == tx.identifier) &&
               (rx.data_length_code == tx.data_length_code);
  for (int i = 0; igual && i < 8; i++) igual = (rx.data[i] == tx.data[i]);

  if (!igual) {
    Serial.printf("  trama %2d  ECO CORRUPTO  (id 0x%03X)\n", n, (unsigned)rx.identifier);
    return false;
  }
  correctas++;
  return true;
}

void setup() {
  Serial.begin(115200);
  delay(700);

  banner("prueba_can.ino  ·  self-test de la cadena CAN");
  Serial.printf("  TX = GPIO %d      RX = GPIO %d\n", PIN_TX, PIN_RX);
  Serial.printf("  Velocidad: %ld baud\n", BAUD_BUS);
  Serial.println("  Modo: NO_ACK (self-test). ESTE SKETCH TRANSMITE.");
  Serial.println();

  if (!arrancarTWAI()) {
    Serial.println("Revisá que no haya otro sketch usando esos GPIO.");
    return;
  }

  Serial.printf("Mandando %d tramas...\n\n", N_TRAMAS);
  for (int n = 0; n < N_TRAMAS; n++) { unaVuelta(n); delay(15); }

  twai_status_info_t st;
  twai_get_status_info(&st);

  banner("RESULTADO");
  Serial.printf("  transmitidas ......... %d de %d\n", enviadas,  N_TRAMAS);
  Serial.printf("  recibidas de vuelta .. %d\n",       recibidas);
  Serial.printf("  identicas ............ %d\n",       correctas);
  Serial.printf("  errores del bus ...... TX %lu   RX %lu\n",
                (unsigned long)st.tx_error_counter, (unsigned long)st.rx_error_counter);
  Serial.println();

  if (correctas == N_TRAMAS) {
    Serial.println("  >>> ECO COMPLETO. La cadena pasa.");
    Serial.println();
    Serial.println("  AHORA EL CONTROL, y no es opcional:");
    Serial.println("  desconectá el cable de RX (LV2 -> GPIO 22), reiniciá,");
    Serial.println("  y volvé a correr. Tiene que dar CERO RECIBIDAS.");
    Serial.println("  Si igual da eco, el lazo se cierra adentro del ESP32");
    Serial.println("  y esta prueba no probo el transceptor.");
  } else if (recibidas == 0 && enviadas > 0) {
    Serial.println("  >>> TRANSMITE PERO NO VUELVE NADA.");
    Serial.println("  Si es la corrida del control, con RX desconectado: PERFECTO,");
    Serial.println("  la prueba si estaba midiendo el transceptor.");
    Serial.println("  Si es la corrida normal, con todo conectado, revisá:");
    Serial.println("    · TX y RX cruzados en el conversor o en el TJA1050");
    Serial.println("    · el pad TX del TJA1050 es su ENTRADA (ver el SVG)");
    Serial.println("    · VCC del TJA1050 en 5 V, no en 3.3");
    Serial.println("    · los dos rieles de GND puenteados entre si");
  } else if (enviadas == 0) {
    Serial.println("  >>> NO LOGRO TRANSMITIR NI UNA.");
    Serial.println("  Casi siempre es alimentacion: sin 5 V el TJA1050 no");
    Serial.println("  suelta la linea y el controlador se queda esperando.");
  } else {
    Serial.println("  >>> ECO PARCIAL O CORRUPTO.");
    Serial.println("  Cables largos, contactos flojos, o el conversor al limite.");
    Serial.println("  Reasenta todo en la protoboard antes de depurar nada mas.");
  }

  Serial.println();
  Serial.println("  Medicion extra, con el multimetro y esto corriendo:");
  Serial.println("  CANH y CANL contra GND deben dar ~2.5 V en reposo.");
  Serial.println("  Eso confirma que el transceptor esta vivo de verdad.");
  Serial.println();

  twai_stop();
  twai_driver_uninstall();
}

void loop() { delay(1000); }
