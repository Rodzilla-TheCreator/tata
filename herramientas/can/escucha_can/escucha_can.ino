// escucha_can.ino — escucha pasiva del bus CAN del EDR18N2 por el DB9 de servicio
//
// TaTa · herramientas/can · cadena ESP32 + TJA1050, sin conversor de nivel
//
// ############################################################################
// #  SOLO ESCUCHA. TWAI_MODE_LISTEN_ONLY: el ESP32 no transmite NADA — ni    #
// #  tramas, ni ACK, ni tramas de error. Para el bus, este nodo no existe.   #
// #  Este archivo no llama a twai_transmit() en ningún lado. Que siga así.   #
// ############################################################################
//
// VALIDACIÓN (05-oct-2026, ver LEEME.md y diagnostico/)
//   prueba_can.ino NO pasa con el módulo TJA1050 actual: su transmisor tarda ~15 µs en
//   soltar el bus. Para ESCUCHAR no importa. Lo que valida esta cadena es:
//     · diagnostico/receptor  — otro nodo simulado: RX baja en 0.40 µs y sube en 0.24 µs
//     · este sketch en la mesa, sin bus: 5 min, 0 tramas y 0 errores (no inventa nada)
//
// CABLEADO FINAL — sin conversor de nivel (el conversor fue descartado el 02-oct)
//
//      ESP32 5V/VIN  →  TJA1050 VCC          ESP32 GND  →  TJA1050 GND
//      ESP32 GPIO 22 →  NADA. El TX del TJA1050 queda AL AIRE: su pull-up interno lo
//                       deja en recesivo y el módulo físicamente no puede transmitir
//      TJA1050 RX → 1 kΩ → GPIO 21, y de GPIO 21 → 2 kΩ → GND   (divisor 5 V → 3.3 V)
//      (14-oct: pines alineados con el armado real; hasta el 13-oct el repo decía TX 21 / RX 22)
//
//      TJA1050 CANH  →  DB9 pin 8   (CAN_H — medido: 120 Ω contra el 3, mismo hilo que
//      TJA1050 CANL  →  DB9 pin 3    el multipiloto)
//      DB9 pin 2     →  SIN CONECTAR en la primera escucha: no está confirmado como masa
//      pines 5, 6, 9 del DB9: NUNCA (GND conmutado, +24 V del 4F15, +12 V)
//      SIN terminador: el bus del equipo ya tiene el suyo. La 100/120 Ω es solo de banco
//
//   Laptop a BATERÍA, desenchufada. Conectar con la llave en OFF.
//
// QUÉ HACE
//   Arranca FIJO a 250k (22-oct). El barrido 250k/500k/125k de antes se quitó: la
//            velocidad está confirmada por el manual y por la escucha del 06-oct.
//   Escucha: imprime cada trama y cada 5 s un resumen por identificador.
//            Decodifica el COB-ID como CANopen: función + nodo, con los nombres
//            de la tabla de nodos del manual (págs. 346–348 del PDF de Scribd).

#include "driver/twai.h"

#define PIN_TX   GPIO_NUM_22     // armado vigente (06-oct en adelante): el divisor quedó en el 21
#define PIN_RX   GPIO_NUM_21     // RX del TJA → 1k/2k → GPIO 21

const uint32_t RESUMEN_MS         = 5000;
const bool     IMPRIMIR_CADA_TRAMA = true;   // en false, solo el resumen

// ── nombres ──────────────────────────────────────────────────────────────────
const char* nombreNodo(int n) {
  switch (n) {
    case 1:  return "Master";
    case 2:  return "Multi-Pilot 1";
    case 3:  return "Display";
    case 4:  return "Direccion 1";
    case 5:  return "Direccion 2 (carga der)";
    case 6:  return "Direccion 3 (carga izq)";
    case 7:  return "Elevacion";
    case 8:  return "Traccion 1";
    case 9:  return "Traccion 2";
    case 10: return "Multi-Pilot 2";
    case 11: return "MFC 1 (frenos)";
    case 12: return "MFC 2 (hidraulica)";
    case 13: return "Interruptor de marcha";
    case 14: return "MFC 05";
    case 15: return "Display 2";
    case 16: return "Control de bateria";
    case 17: return "Cargador";
    case 28: return "CanCode";
    case 29: return "ISM";
    case 30: return "PC de servicio";
    case 31: return "APM+";
    default: return "?";
  }
}

// CANopen: COB-ID = función (4 bits altos de 11) + nodo (7 bits bajos)
const char* nombreFuncion(uint32_t id) {
  if (id == 0x000) return "NMT";
  if (id == 0x080) return "SYNC";
  if (id == 0x100) return "TIME";
  switch (id & 0x780) {
    case 0x080: return "EMCY";
    case 0x180: return "TPDO1";
    case 0x200: return "RPDO1";
    case 0x280: return "TPDO2";
    case 0x300: return "RPDO2";
    case 0x380: return "TPDO3";
    case 0x400: return "RPDO3";
    case 0x480: return "TPDO4";
    case 0x500: return "RPDO4";
    case 0x580: return "SDO resp";
    case 0x600: return "SDO pet";
    case 0x700: return "HEARTBEAT";
    default:    return "?";
  }
}

// ── driver ───────────────────────────────────────────────────────────────────
bool arrancar(long baud) {
  twai_general_config_t g = TWAI_GENERAL_CONFIG_DEFAULT(PIN_TX, PIN_RX, TWAI_MODE_LISTEN_ONLY);
  g.rx_queue_len = 64;
  g.tx_queue_len = 0;                          // sin cola de transmisión
  twai_timing_config_t t;
  if      (baud == 125000) t = TWAI_TIMING_CONFIG_125KBITS();
  else if (baud == 500000) t = TWAI_TIMING_CONFIG_500KBITS();
  else                     t = TWAI_TIMING_CONFIG_250KBITS();
  twai_filter_config_t f = TWAI_FILTER_CONFIG_ACCEPT_ALL();
  if (twai_driver_install(&g, &t, &f) != ESP_OK) return false;
  if (twai_start() != ESP_OK) { twai_driver_uninstall(); return false; }
  return true;
}

void parar() { twai_stop(); twai_driver_uninstall(); }

// ── resumen por identificador ────────────────────────────────────────────────
struct Cuenta { uint32_t id; uint32_t n; uint8_t dlc; uint8_t ultimo[8]; };
const int MAX_IDS = 96;
Cuenta tabla[MAX_IDS];
int nIds = 0;

void contar(const twai_message_t& m) {
  for (int i = 0; i < nIds; i++)
    if (tabla[i].id == m.identifier) {
      tabla[i].n++; tabla[i].dlc = m.data_length_code;
      memcpy(tabla[i].ultimo, m.data, 8);
      return;
    }
  if (nIds < MAX_IDS) {
    tabla[nIds].id = m.identifier; tabla[nIds].n = 1; tabla[nIds].dlc = m.data_length_code;
    memcpy(tabla[nIds].ultimo, m.data, 8);
    nIds++;
  }
}

void imprimirTrama(const twai_message_t& m) {
  Serial.printf("%10lu  %s %03lX  [%d]", (unsigned long)millis(),
                m.extd ? "EXT" : "   ", (unsigned long)m.identifier, m.data_length_code);
  for (int i = 0; i < m.data_length_code; i++) Serial.printf(" %02X", m.data[i]);
  if (!m.extd) {
    int nodo = m.identifier & 0x7F;
    Serial.printf("   %s nodo %d %s", nombreFuncion(m.identifier), nodo,
                  (m.identifier > 0x100) ? nombreNodo(nodo) : "");
  }
  if (m.rtr) Serial.print("  RTR");
  Serial.println();
}

void imprimirResumen(uint32_t ms) {
  twai_status_info_t st; twai_get_status_info(&st);
  Serial.println();
  Serial.printf("---- resumen %lu s · %d identificadores · err RX %lu · perdidas %lu ----\n",
                (unsigned long)(ms / 1000), nIds,
                (unsigned long)st.rx_error_counter, (unsigned long)st.rx_missed_count);
  for (int i = 0; i < nIds; i++) {
    const Cuenta& c = tabla[i];
    int nodo = c.id & 0x7F;
    Serial.printf("  %03lX  %6lu  %-10s nodo %-3d %-22s ultimo:",
                  (unsigned long)c.id, (unsigned long)c.n, nombreFuncion(c.id), nodo,
                  (c.id > 0x100) ? nombreNodo(nodo) : "");
    for (int k = 0; k < c.dlc; k++) Serial.printf(" %02X", c.ultimo[k]);
    Serial.println();
  }
  Serial.println();
}

// ── programa ─────────────────────────────────────────────────────────────────
long bausElegido = 0;

void setup() {
  Serial.begin(921600);   // 115200 perdía ~80 % de las tramas (06-oct)
  delay(700);
  Serial.println();
  Serial.println("========================================================");
  Serial.println("  escucha_can.ino  ·  SOLO ESCUCHA (LISTEN_ONLY)");
  Serial.println("========================================================");
  Serial.printf("  TX = GPIO %d (no se usa)   RX = GPIO %d\n\n", PIN_TX, PIN_RX);

  // 22-oct: sin barrido. La velocidad está confirmada (250k: manual y escucha del 06-oct)
  bausElegido = 250000;
  if (!arrancar(bausElegido)) { Serial.println("FALLA al instalar el driver"); return; }
  Serial.println("Escuchando FIJO a 250k desde el arranque.\n");
}

uint32_t proximoResumen = RESUMEN_MS;

void loop() {
  twai_message_t m;
  if (twai_receive(&m, pdMS_TO_TICKS(20)) == ESP_OK) {
    contar(m);
    if (IMPRIMIR_CADA_TRAMA) imprimirTrama(m);
  }
  if (millis() >= proximoResumen) {
    imprimirResumen(millis());
    proximoResumen = millis() + RESUMEN_MS;
  }
}
