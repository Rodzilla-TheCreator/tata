// multipiloto_campo.ino — nodo 2 falso para el EQUIPO, con el CAN del multipiloto real cortado
//
// TaTa · herramientas/can/banco_imitador · se maneja con campo_nodo2.py (no con el monitor serie)
//
// ############################################################################
// #  TRANSMITE AL EQUIPO, pero solo después de armarlo ('A' por serie).       #
// #  Antes de armar: LISTEN_ONLY, no manda ni un bit (ni ACK).                #
// #  El 0x182 arranca EN CERO y vuelve a cero por NMT START, por '0' y por    #
// #  WATCHDOG (200 ms sin línea por serie). Mandos solo después de armar.     #
// #  Requiere el CAN del multipiloto real FUERA (2,3,4,5): un solo nodo 2.    #
// ############################################################################
//
// MANDO (22-oct, prueba 2 de la ruta B), por serie, una orden por línea, como multipiloto_falso:
//   a N / t N   joystick adelante / atrás, magnitud 0–255     i N / d N   izquierda / derecha
//   n s e w     botón north / south / east / west (queda hasta '0')   r   botón trasero (pito)
//   0           todo a cero        .   solo latido        X   SILENCIO: vuelve a LISTEN_ONLY
// campo_nodo2.py manda '.' cada 50 ms: si la laptop o el script se caen, el watchdog pone cero.
//
// PREGUNTA QUE CONTESTA (22-oct): con el CAN del multipiloto cortado, el Master no aparece.
// ¿Es porque alguien espera al nodo 2? Si sí, con este nodo presente debería verse 602 → 582,
// NMT START y SYNC. Si no aparece ninguna trama del Master, nadie lo esperaba.
//
// QUÉ HACE, imitando lo grabado del real (06-oct y 22-oct):
//   · espera el boot-up de cualquier nodo del grupo (701, 704, 707, 708, 71E; no la pantalla
//     703, que prende sola 6–8 s antes) y 800 ms después manda 702 00. Si el bus está vivo
//     15 s sin que llegue ninguno, lo manda igual
//   · latido 702 cada 100 ms: 7F en pre-operacional, 05 operacional, 04 parado
//   · contesta 602 40 00 10 00 → 582 43 00 10 00 00 00 00 00; cualquier otra lectura: abort
//   · en operacional, 182 con todo en cero detrás de cada SYNC
// Imprime cada trama recibida y sus propias acciones con '#' para que el .py lo registre.

#include "driver/twai.h"

#define PIN_TX   GPIO_NUM_22
#define PIN_RX   GPIO_NUM_21

const uint8_t  NODO          = 2;
const uint32_t PERIODO_HB_MS = 100;    // medido 19-oct
const uint32_t RETARDO_BOOT  = 800;    // el real: ~0.8 s después del grupo (22-oct)
const uint32_t PLAN_B_MS     = 15000;  // bus vivo sin grupo → boot-up igual
const uint32_t WATCHDOG_MS   = 200;    // docs/10, en chico

enum Estado { SIN_BOOT, PREOP, OPERACIONAL, PARADO };
Estado estado = SIN_BOOT;
bool armado = false;
uint32_t tGrupo = 0, tPrimeraTrama = 0, thb = 0, tEstado = 0, enviadas = 0;

// las posiciones de 0x182 (tabla de multipiloto.md)
uint8_t b0 = 0, b1 = 0, b2 = 0, b4 = 0, b5 = 0;
uint32_t ultimoLatido = 0;
bool enCero = true;

void todoACero() { b0 = b1 = b2 = b4 = b5 = 0; }

void armar182(uint8_t* d) {
  d[0] = b0; d[1] = b1; d[2] = b2;
  d[3] = (b5 & (0x02 | 0x01)) ? 255 : 0;   // east / west apretados
  d[4] = b4; d[5] = b5;
  d[6] = 0;                                // «sin cambios» en la grabación
  d[7] = (b5 & (0x08 | 0x04)) ? 255 : 0;   // north / south apretados
}

twai_timing_config_t t = TWAI_TIMING_CONFIG_250KBITS();
twai_filter_config_t f = TWAI_FILTER_CONFIG_ACCEPT_ALL();

void instalar(twai_mode_t modo) {
  twai_general_config_t g = TWAI_GENERAL_CONFIG_DEFAULT(PIN_TX, PIN_RX, modo);
  g.rx_queue_len = 64; g.tx_queue_len = (modo == TWAI_MODE_NORMAL) ? 8 : 0;
  twai_driver_install(&g, &t, &f); twai_start();
}

void mandar(uint32_t id, const uint8_t* d, uint8_t n) {
  twai_message_t m = {}; m.identifier = id; m.data_length_code = n; if (n) memcpy(m.data, d, n);
  if (twai_transmit(&m, pdMS_TO_TICKS(5)) == ESP_OK) enviadas++;
}

void imprimir(const twai_message_t& m) {
  Serial.printf("%lu %03lX [%d]", (unsigned long)millis(), (unsigned long)m.identifier, m.data_length_code);
  for (int i = 0; i < m.data_length_code; i++) Serial.printf(" %02X", m.data[i]);
  Serial.println();
}

void bootup() {
  const uint8_t b = 0x00; mandar(0x700 + NODO, &b, 1);
  estado = PREOP; thb = millis();
  Serial.printf("# YO %lu boot-up 702 00\n", (unsigned long)millis());
}

void atender(const twai_message_t& m) {
  uint32_t id = m.identifier;
  if (id == 0x000 && m.data_length_code >= 2 && (m.data[1] == NODO || m.data[1] == 0) && estado != SIN_BOOT) {
    switch (m.data[0]) {
      case 0x01: estado = OPERACIONAL; todoACero(); Serial.println("# YO NMT START recibido -> operacional (182 en cero)"); break;
      case 0x02: estado = PARADO;      Serial.println("# YO NMT STOP recibido"); break;
      case 0x80: estado = PREOP;       Serial.println("# YO NMT PRE-OP recibido"); break;
      case 0x81: case 0x82: Serial.println("# YO NMT RESET recibido"); bootup(); break;
    }
  } else if (id == 0x600 + NODO && estado != SIN_BOOT) {
    if (m.data[0] == 0x40 && m.data[1] == 0x00 && m.data[2] == 0x10 && m.data[3] == 0x00) {
      const uint8_t r[8] = {0x43, 0x00, 0x10, 0x00, 0, 0, 0, 0};
      mandar(0x580 + NODO, r, 8);
      Serial.println("# YO contesto 0x1000 = 0");
    } else if ((m.data[0] & 0xE0) == 0x40) {
      const uint8_t ab[8] = {0x80, m.data[1], m.data[2], m.data[3], 0x00, 0x00, 0x02, 0x06};
      mandar(0x580 + NODO, ab, 8);
      Serial.printf("# YO abort a lectura %02X%02X.%02X\n", m.data[2], m.data[1], m.data[3]);
    }
  } else if (id == 0x080 && estado == OPERACIONAL) {
    uint8_t d[8]; armar182(d);              // PDO síncrono: sale detrás del SYNC
    mandar(0x180 + NODO, d, 8);
  } else if (estado == SIN_BOOT && tGrupo == 0 && m.data_length_code == 1 && m.data[0] == 0x00 &&
             (id == 0x701 || id == 0x704 || id == 0x707 || id == 0x708 || id == 0x71E)) {
    tGrupo = millis();
    Serial.printf("# YO grupo detectado (%03lX), boot-up en %lu ms\n", (unsigned long)id, (unsigned long)RETARDO_BOOT);
  }
}

void silencio() {
  twai_stop(); twai_driver_uninstall(); instalar(TWAI_MODE_LISTEN_ONLY);
  armado = false; estado = SIN_BOOT; tGrupo = tPrimeraTrama = 0; todoACero(); enCero = true;
  Serial.println("# YO SILENCIO: LISTEN_ONLY, no transmitimos nada ('A' para rearmar)");
}

void leerSerie() {
  static char linea[24]; static int n = 0;
  while (Serial.available()) {
    char c = Serial.read();
    if (!armado) {                           // antes de armar solo vale 'A'
      if (c == 'A') {
        twai_stop(); twai_driver_uninstall(); instalar(TWAI_MODE_NORMAL);
        armado = true; Serial.println("# ARMADO (modo normal, esperando el bus)");
      }
      continue;
    }
    if (c == '\r') continue;
    if (c != '\n') { if (n < 23) linea[n++] = c; continue; }
    linea[n] = 0; n = 0;
    ultimoLatido = millis();
    if (enCero && linea[0] != '.') { enCero = false; Serial.println("# YO latido de mando presente"); }
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
      case 'X': silencio(); return;
      default: continue;                     // '.' y cualquier otra: solo latido
    }
    uint8_t d[8]; armar182(d);
    Serial.printf("# YO mando '%s' -> 182 %02X %02X %02X %02X %02X %02X %02X %02X%s\n", linea,
                  d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7],
                  estado == OPERACIONAL ? "" : " (todavía NO operacional: no sale)");
  }
}

void setup() {
  Serial.begin(921600); delay(300);
  instalar(TWAI_MODE_LISTEN_ONLY);
  Serial.println("# LISTO (solo escucha hasta armar)");
}

void loop() {
  leerSerie();
  if (armado && !enCero && millis() - ultimoLatido > WATCHDOG_MS) {
    todoACero(); enCero = true;
    Serial.println("# YO WATCHDOG: sin latido por serie -> 182 a CERO");
  }
  twai_message_t m;
  while (twai_receive(&m, 0) == ESP_OK) {
    if (armado && tPrimeraTrama == 0) tPrimeraTrama = millis();   // plan B cuenta desde el Enter
    imprimir(m);
    if (armado) atender(m);
  }
  if (!armado) return;
  uint32_t ahora = millis();
  if (estado == SIN_BOOT && tGrupo && ahora - tGrupo >= RETARDO_BOOT) bootup();
  if (estado == SIN_BOOT && !tGrupo && tPrimeraTrama && ahora - tPrimeraTrama >= PLAN_B_MS) {
    Serial.println("# YO plan B: bus vivo 15 s sin grupo");
    bootup();
  }
  if (ahora - tEstado >= 2000) {             // prueba de que estamos en el bus
    tEstado = ahora; twai_status_info_t st; twai_get_status_info(&st);
    Serial.printf("# YO estado %d · encoladas %lu · pendientes %lu · TEC %lu · REC %lu · bus %s\n",
                  (int)estado, (unsigned long)enviadas, (unsigned long)st.msgs_to_tx,
                  (unsigned long)st.tx_error_counter, (unsigned long)st.rx_error_counter,
                  st.state == TWAI_STATE_RUNNING ? "ok" : (st.state == TWAI_STATE_BUS_OFF ? "OFF" : "?"));
  }
  if (estado != SIN_BOOT && ahora - thb >= PERIODO_HB_MS) {
    thb = ahora;
    uint8_t s = (estado == OPERACIONAL) ? 0x05 : (estado == PARADO ? 0x04 : 0x7F);
    mandar(0x700 + NODO, &s, 1);
  }
}
