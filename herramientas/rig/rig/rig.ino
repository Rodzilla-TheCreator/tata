// rig.ino — el rig integrado: UN ESP32 que hace de multipiloto (CAN, nodo 2), de timón (sensor
// seno/coseno del volante) y de pie (pedal de hombre muerto), con un solo latido y un solo watchdog.
//
// Junta, sin cambiar su lógica, tres sketches ya probados por separado:
//   herramientas/can/banco_imitador/multipiloto_campo  (aceptado por el Master el 22-oct)
//   herramientas/emulador_timon/emulador_timon.ino      (calibrado el 26-oct)
//   herramientas/rig/pie/pie.ino                        (banco del 19-nov)
// Se maneja con herramientas/rig/rig_gui.py. Reglas: herramientas/rig/tarea_firmware.md.
//
// ############################################################################
// #  EL CAN TRANSMITE, pero solo después de armarlo ('A'). Antes: LISTEN_ONLY. #
// #  Requiere el CAN del multipiloto real FUERA: un solo nodo 2 en el bus.     #
// #  200 ms sin línea L válida → 0x182 a cero, pie suelto, timón quieto.       #
// ############################################################################
//
// PINES (docs/24, «El circuito del ESP, pin por pin», + 19-nov)
//   22 TX TWAI → ADuM VIB · 21 RX TWAI ← ADuM VOA (3.3 V, VDD1 = 3V3)
//   25 DAC verde · 26 DAC café (→ LM358 → nodo 4)
//   27 → IN de los dos módulos de relé del pedal (10 k de IN a DC− recomendado)
//   32 ← botón de rearme a GND (pull-up interno) · 35 ← VCC de los módulos (divisor 10k/20k)
//   2  LED: fijo = pisando · parpadeo = disparado · apagado = sin pisar
//
// PROTOCOLO SERIE, 921600 baud, una orden por línea:
//   L y=<-255..255> x=<-255..255> b=<-255..255> n=0 s=0 e=0 w=0 r=0 th=<grados> pie=<0|1>
//       la línea de estado completo, cada 50 ms: es el mando Y el latido. Solo cuenta si trae pie=.
//       y: joystick adelante(+)/atrás(−) · x: derecha(+)/izquierda(−) · b: palanca trasera
//       n s e w: botones de arriba · r: botón trasero (pito) · th: ángulo del VOLANTE emulado
//   A   armar el CAN (sale de LISTEN_ONLY)          X   silencio: vuelve a LISTEN_ONLY
//   T <grados>  armar el timón: el ángulo actual del volante (el del sensor real al cambiarlo).
//               Antes de T, th se ignora y el timón se queda donde arrancó (0°).
//   R   rearme del pie (SOLO si REARME_POR_SERIE = 1, banco)
//   V1 / V0     volcar / no volcar cada trama CAN recibida (líneas F)
// El ESP manda:  S ... (estado, cada 200 ms) · EV ... (eventos) · F ... (tramas, con V1)

#include "driver/twai.h"
#include <esp_task_wdt.h>
#include <math.h>

// ---------------- Ajustes (las compilaciones de prueba cambian solo esto) ----------------
#define WATCHDOG_MS      200    // control de la prueba 2: compilar con 5000 → tiene que FALLAR
#define USAR_TASK_WDT    1      // control de la prueba del cuelgue: con 0, el pie queda pisado
#define PRUEBA_CUELGUE   0      // con 1, la línea "HANG" cuelga el loop a propósito
#define TASK_WDT_MS      1000
#define REARME_POR_SERIE 1      // BANCO. En el montacargas va en 0: el rearme es un botón en el fierro
#define TIMON_MAX_GPS    360.0f // grados/s máximos del volante emulado (un operador rápido: ~1 vuelta/s)

// ---------------- Pines ----------------
#define PIN_TX GPIO_NUM_22
#define PIN_RX GPIO_NUM_21
const int DAC_V = 25, DAC_C = 26;
const int PIN_PIE = 27, PIN_REARME = 32, PIN_PARO = 35, PIN_LED = 2;
const int PARO_ALTO_MV = 2000, PARO_BAJO_MV = 1200;

// ---------------- Timón: calibración del 26-oct (emulador_timon.ino) ----------------
const float Vo = 2.47f, Va = 1.98f;
const float kV = 1.381f, oV = 0.131f;   // verde (GPIO25)
const float kC = 1.386f, oC = 0.115f;   // café  (GPIO26)

static int codigoDac(float vdac) {
  if (vdac < 0) vdac = 0; if (vdac > 3.3f) vdac = 3.3f;
  return (int)(vdac / 3.3f * 255.0f + 0.5f);
}
static void sacarTimon(float grados) {
  float r = grados * (float)M_PI / 180.0f;
  dacWrite(DAC_V, codigoDac((Vo + Va * cosf(r) - oV) / kV));
  dacWrite(DAC_C, codigoDac((Vo + Va * sinf(r) - oC) / kC));
}

// ---------------- Latido y mando ----------------
uint32_t tUltLinea = 0;
bool hayLatido = false;
int mY = 0, mX = 0, mB = 0;            // joystick y palanca, con signo
bool mN = 0, mS = 0, mE = 0, mW = 0, mR = 0;
bool pideMando = false;                // pie=
float thPedido = 0;                    // th= (volante)
bool hayTh = false;

static bool latidoFresco(uint32_t ahora) { return hayLatido && (uint32_t)(ahora - tUltLinea) < WATCHDOG_MS; }

// ---------------- Pie (pie.ino) ----------------
enum EstPie { SIN_ARMAR, ARMADO, DISPARADO };
EstPie estPie = SIN_ARMAR;
bool paroOk = false, pideRearme = false, pisando = false;
int mvParo = 0;
uint32_t disparos = 0, tBotonBajo = 0;
bool botonPrevio = false, botonUsado = false;
static const char* nPie(EstPie e) { return e == SIN_ARMAR ? "SIN_ARMAR" : e == ARMADO ? "ARMADO" : "DISPARADO"; }
static void leerParo() {
  mvParo = analogReadMilliVolts(PIN_PARO);
  if (mvParo > PARO_ALTO_MV) paroOk = true; else if (mvParo < PARO_BAJO_MV) paroOk = false;
}

// ---------------- Timón ----------------
bool timonArmado = false;
float thActual = 0;                    // grados del volante emulado (multivuelta)
float thObjetivo = 0;

// ---------------- CAN (multipiloto_campo.ino) ----------------
const uint8_t  NODO = 2;
const uint32_t PERIODO_HB_MS = 100, RETARDO_BOOT = 800, PLAN_B_MS = 15000;
enum EstCan { SIN_BOOT, PREOP, OPERACIONAL, PARADO };
EstCan estCan = SIN_BOOT;
bool canArmado = false, volcar = false, masterVisto = false, enCero = true;
uint32_t tGrupo = 0, tPrimeraTrama = 0, thb = 0, enviadas = 0, rxCuenta = 0, rxPorSeg = 0, tRx = 0;
uint8_t ult182[8] = {0};
static const char* nCan() {
  if (!canArmado) return "SOLO_ESCUCHA";
  return estCan == SIN_BOOT ? "SIN_BOOT" : estCan == PREOP ? "PREOP" : estCan == OPERACIONAL ? "OPERACIONAL" : "PARADO";
}

twai_timing_config_t tCfg = TWAI_TIMING_CONFIG_250KBITS();
twai_filter_config_t fCfg = TWAI_FILTER_CONFIG_ACCEPT_ALL();

static void instalar(twai_mode_t modo) {
  twai_general_config_t g = TWAI_GENERAL_CONFIG_DEFAULT(PIN_TX, PIN_RX, modo);
  g.rx_queue_len = 64; g.tx_queue_len = (modo == TWAI_MODE_NORMAL) ? 8 : 0;
  twai_driver_install(&g, &tCfg, &fCfg); twai_start();
}
static void mandar(uint32_t id, const uint8_t* d, uint8_t n) {
  twai_message_t m = {}; m.identifier = id; m.data_length_code = n; if (n) memcpy(m.data, d, n);
  if (twai_transmit(&m, pdMS_TO_TICKS(5)) == ESP_OK) enviadas++;
}

// El 0x182 con la tabla de herramientas/can/multipiloto.md. Sin latido fresco: TODO EN CERO.
static void armar182(uint8_t* d, bool fresco) {
  memset(d, 0, 8);
  if (!fresco) return;
  uint8_t b4 = 0, b5 = 0;
  if (mY > 0) { d[0] = mY;  b4 |= 0x08; } else if (mY < 0) { d[0] = -mY; b4 |= 0x10; }
  if (mX < 0) { d[1] = -mX; b4 |= 0x04; } else if (mX > 0) { d[1] = mX;  b4 |= 0x02; }
  if (mB > 0) { d[2] = mB;  b4 |= 0x40; } else if (mB < 0) { d[2] = -mB; b4 |= 0x20; }  // SIN PROBAR en el equipo
  if (mR) b4 |= 0x01;
  if (mN) b5 |= 0x08; if (mS) b5 |= 0x04; if (mE) b5 |= 0x02; if (mW) b5 |= 0x01;
  d[3] = (mE || mW) ? 255 : 0;
  d[4] = b4; d[5] = b5; d[6] = 0;
  d[7] = (mN || mS) ? 255 : 0;
}

static void bootup() {
  const uint8_t b = 0x00; mandar(0x700 + NODO, &b, 1);
  estCan = PREOP; thb = millis();
  Serial.println("EV can: boot-up 702 00 enviado");
}

static void silencio() {
  twai_stop(); twai_driver_uninstall(); instalar(TWAI_MODE_LISTEN_ONLY);
  canArmado = false; estCan = SIN_BOOT; tGrupo = tPrimeraTrama = 0; enCero = true;
  Serial.println("EV can: SILENCIO, LISTEN_ONLY (no transmitimos nada)");
}

static void atender(const twai_message_t& m) {
  uint32_t id = m.identifier;
  if (id == 0x000 && m.data_length_code >= 2 && (m.data[1] == NODO || m.data[1] == 0) && estCan != SIN_BOOT) {
    switch (m.data[0]) {
      case 0x01: estCan = OPERACIONAL; Serial.println("EV can: NMT START -> operacional (182 en cero hasta el primer mando)"); break;
      case 0x02: estCan = PARADO;      Serial.println("EV can: NMT STOP"); break;
      case 0x80: estCan = PREOP;       Serial.println("EV can: NMT PRE-OP"); break;
      case 0x81: case 0x82: Serial.println("EV can: NMT RESET"); bootup(); break;
    }
  } else if (id == 0x600 + NODO && estCan != SIN_BOOT) {
    if (m.data[0] == 0x40 && m.data[1] == 0x00 && m.data[2] == 0x10 && m.data[3] == 0x00) {
      const uint8_t r[8] = {0x43, 0x00, 0x10, 0x00, 0, 0, 0, 0};
      mandar(0x580 + NODO, r, 8);
      Serial.println("EV can: el Master leyó 0x1000 y contestamos 0");
    } else if ((m.data[0] & 0xE0) == 0x40) {
      const uint8_t ab[8] = {0x80, m.data[1], m.data[2], m.data[3], 0x00, 0x00, 0x02, 0x06};
      mandar(0x580 + NODO, ab, 8);
      Serial.printf("EV can: abort a la lectura %02X%02X.%02X\n", m.data[2], m.data[1], m.data[3]);
    }
  } else if (id == 0x080 && estCan == OPERACIONAL) {
    armar182(ult182, latidoFresco(millis()));      // PDO síncrono: sale detrás del SYNC
    mandar(0x180 + NODO, ult182, 8);
  } else if (estCan == SIN_BOOT && tGrupo == 0 && m.data_length_code == 1 && m.data[0] == 0x00 &&
             (id == 0x701 || id == 0x704 || id == 0x707 || id == 0x708 || id == 0x71E)) {
    tGrupo = millis();
    Serial.printf("EV can: arrancó el grupo (%03lX), boot-up en %lu ms\n", (unsigned long)id, (unsigned long)RETARDO_BOOT);
  }
}

static void recibirCan() {
  twai_message_t m;
  while (twai_receive(&m, 0) == ESP_OK) {
    rxCuenta++;
    uint32_t id = m.identifier;
    if (id == 0x701 || id == 0x080) masterVisto = true;
    if (canArmado && tPrimeraTrama == 0) tPrimeraTrama = millis();
    if (id == 0x000) Serial.printf("EV can: NMT %02X %02X\n", m.data[0], m.data[1]);
    if (id > 0x080 && id < 0x100)                    // EMCY de cualquier nodo: siempre se avisa
      Serial.printf("EV can: EMERGENCIA nodo %lu: %02X %02X %02X %02X %02X %02X %02X %02X\n",
                    (unsigned long)(id & 0x7F), m.data[0], m.data[1], m.data[2], m.data[3],
                    m.data[4], m.data[5], m.data[6], m.data[7]);
    if (volcar) {
      Serial.printf("F %lu %03lX [%d]", (unsigned long)millis(), (unsigned long)id, m.data_length_code);
      for (int i = 0; i < m.data_length_code; i++) Serial.printf(" %02X", m.data[i]);
      Serial.println();
    }
    if (canArmado) atender(m);
  }
}

// ---------------- Serie ----------------
char buf[192]; uint8_t nbuf = 0;

static int campoInt(const char* s, const char* k, int def) {
  const char* p = strstr(s, k); return p ? atoi(p + strlen(k)) : def;
}

static void procesarLinea(const char* s) {
#if PRUEBA_CUELGUE
  if (strcmp(s, "HANG") == 0) { Serial.println("EV cuelgue a proposito"); Serial.flush(); while (1) { } }
#endif
  if (s[0] == 'A' && s[1] == 0) {
    if (!canArmado) {
      twai_stop(); twai_driver_uninstall(); instalar(TWAI_MODE_NORMAL);
      canArmado = true; Serial.println("EV can: ARMADO (modo normal, esperando el arranque del bus)");
    }
    return;
  }
  if (s[0] == 'X' && s[1] == 0) { silencio(); return; }
  if (s[0] == 'V' && (s[1] == '0' || s[1] == '1')) { volcar = (s[1] == '1'); return; }
  if (s[0] == 'T' && s[1] == ' ') {
    thActual = thObjetivo = thPedido = atof(s + 2);
    timonArmado = true; hayTh = false;
    Serial.printf("EV timon: ARMADO en %.1f grados\n", thActual);
    return;
  }
#if REARME_POR_SERIE
  if (s[0] == 'R' && s[1] == 0) { pideRearme = true; return; }
#endif
  if (s[0] != 'L') return;
  const char* p = strstr(s, "pie=");
  if (!p || (p[4] != '0' && p[4] != '1')) return;          // sin pie= no es latido
  pideMando = (p[4] == '1');
  mY = constrain(campoInt(s, "y=", 0), -255, 255);
  mX = constrain(campoInt(s, "x=", 0), -255, 255);
  mB = constrain(campoInt(s, "b=", 0), -255, 255);
  mN = campoInt(s, "n=", 0); mS = campoInt(s, "s=", 0); mE = campoInt(s, "e=", 0); mW = campoInt(s, "w=", 0);
  mR = campoInt(s, "r=", 0);
  const char* t = strstr(s, "th=");
  if (t) { thPedido = atof(t + 3); hayTh = true; }
  tUltLinea = millis(); hayLatido = true;
}

static void leerSerie() {
  while (Serial.available()) {                              // sin esperas: solo lo que ya llegó
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') { buf[nbuf] = 0; if (nbuf) procesarLinea(buf); nbuf = 0; }
    else if (nbuf < sizeof(buf) - 1) buf[nbuf++] = c;
    else nbuf = 0;                                          // línea demasiado larga: se descarta
  }
}

// ---------------- setup / loop ----------------
uint32_t tAntLoop = 0, loopMaxUs = 0, tReporte = 0, tLoopMax = 0;
bool frescoAntes = false;

void setup() {
  // Regla 5: lo primero, el pie suelto y los DAC en un punto válido del círculo.
  pinMode(PIN_PIE, OUTPUT); digitalWrite(PIN_PIE, LOW);
  sacarTimon(0);
  pinMode(PIN_LED, OUTPUT); digitalWrite(PIN_LED, LOW);
  pinMode(PIN_REARME, INPUT_PULLUP);
  pinMode(PIN_PARO, INPUT);

  Serial.begin(921600);
  leerParo();
  instalar(TWAI_MODE_LISTEN_ONLY);

#if USAR_TASK_WDT
  esp_task_wdt_config_t cfg = { .timeout_ms = TASK_WDT_MS, .idle_core_mask = 0, .trigger_panic = true };
  if (esp_task_wdt_reconfigure(&cfg) != ESP_OK) esp_task_wdt_init(&cfg);
  esp_task_wdt_add(NULL);
#endif
  Serial.printf("EV arranque rig WATCHDOG_MS=%d TASK_WDT=%d REARME_SERIE=%d TIMON_MAX=%.0f paro=%d mV\n",
                WATCHDOG_MS, USAR_TASK_WDT, REARME_POR_SERIE, TIMON_MAX_GPS, mvParo);
#if REARME_POR_SERIE
  Serial.println("EV OJO: REARME_POR_SERIE = 1 (BANCO). Para el montacargas compilar con 0.");
#endif
  tAntLoop = micros();
}

void loop() {
#if USAR_TASK_WDT
  esp_task_wdt_reset();
#endif
  uint32_t us = micros(), dtUs = us - tAntLoop; tAntLoop = us;
  if (dtUs > loopMaxUs) loopMaxUs = dtUs;
  uint32_t ahora = millis();

  leerSerie();
  recibirCan();
  bool fresco = latidoFresco(ahora);

  if (frescoAntes && !fresco)
    Serial.printf("EV WATCHDOG: %lu ms sin latido -> 182 a cero, pie suelto, timon quieto\n",
                  (unsigned long)(ahora - tUltLinea));
  if (!frescoAntes && fresco) Serial.println("EV latido presente");
  frescoAntes = fresco;

  // ---- Pie ----
  if (estPie == ARMADO && !fresco) { estPie = DISPARADO; disparos++; }
  bool paroAntes = paroOk;
  leerParo();
  if (paroAntes && !paroOk) {
    if (estPie == ARMADO) { estPie = DISPARADO; disparos++; }
    Serial.printf("EV paro: modulos sin 5 V (%d mV) -> pie suelto, %s\n", mvParo, nPie(estPie));
  } else if (!paroAntes && paroOk) {
    Serial.printf("EV paro liberado (%d mV): el pie sigue suelto hasta el rearme\n", mvParo);
  }
  bool boton = (digitalRead(PIN_REARME) == LOW);
  if (boton && !botonPrevio) { tBotonBajo = ahora; botonUsado = false; }
  botonPrevio = boton;
  bool botonListo = boton && !botonUsado && (ahora - tBotonBajo) >= 50;
  if (botonListo) botonUsado = true;
  bool pedido = botonListo || pideRearme; pideRearme = false;
  if (pedido && estPie == ARMADO)  Serial.println("EV rearme: ya estaba armado");
  else if (pedido && !paroOk)      Serial.println("EV rearme rechazado: el paro esta cortando (modulos sin 5 V)");
  else if (pedido && !fresco)      Serial.println("EV rearme rechazado: no hay latido fresco");
  else if (pedido)               { estPie = ARMADO; Serial.println("EV rearmado"); }
  bool pisar = (estPie == ARMADO) && fresco && pideMando && paroOk;
  if (pisar != pisando) Serial.printf("EV pie: %s\n", pisar ? "PISADO" : "suelto");
  pisando = pisar;
  digitalWrite(PIN_PIE, pisar ? HIGH : LOW);
  if (pisar)                      digitalWrite(PIN_LED, HIGH);
  else if (estPie == DISPARADO)   digitalWrite(PIN_LED, (ahora / 250) % 2);
  else                            digitalWrite(PIN_LED, LOW);

  // ---- Timón: sin latido se queda donde está (un salto de ángulo es un giro de la rueda) ----
  static uint32_t tTimonUs = us;
  float dt = (us - tTimonUs) / 1e6f; tTimonUs = us;
  if (timonArmado && fresco && hayTh) thObjetivo = thPedido;
  else thObjetivo = thActual;
  float paso = TIMON_MAX_GPS * dt, dif = thObjetivo - thActual;
  if (dif > paso) dif = paso; else if (dif < -paso) dif = -paso;
  thActual += dif;
  sacarTimon(thActual);

  // ---- CAN ----
  if (canArmado) {
    if (enCero && fresco && (mY || mX || mB || mN || mS || mE || mW || mR)) { enCero = false; Serial.println("EV can: primer mando"); }
    if (estCan == SIN_BOOT && tGrupo && ahora - tGrupo >= RETARDO_BOOT) bootup();
    if (estCan == SIN_BOOT && !tGrupo && tPrimeraTrama && ahora - tPrimeraTrama >= PLAN_B_MS) {
      Serial.println("EV can: plan B, bus vivo 15 s sin grupo"); bootup();
    }
    if (estCan != SIN_BOOT && ahora - thb >= PERIODO_HB_MS) {
      thb = ahora;
      uint8_t s = (estCan == OPERACIONAL) ? 0x05 : (estCan == PARADO ? 0x04 : 0x7F);
      mandar(0x700 + NODO, &s, 1);
    }
  }
  if (ahora - tRx >= 1000) { tRx = ahora; rxPorSeg = rxCuenta; rxCuenta = 0; }

  // ---- Estado cada 200 ms ----
  if (ahora - tReporte >= 200) {
    tReporte = ahora;
    twai_status_info_t st; twai_get_status_info(&st);
    Serial.printf("S can=%s tec=%lu rec=%lu bus=%s tx=%lu rx=%lu master=%d f182=%02X%02X%02X%02X%02X%02X%02X%02X "
                  "pie=%s pisa=%d paro=%d disparos=%lu tarm=%d th=%.1f tht=%.1f lat=%ld loopmax=%lu\n",
                  nCan(), (unsigned long)st.tx_error_counter, (unsigned long)st.rx_error_counter,
                  st.state == TWAI_STATE_RUNNING ? "ok" : (st.state == TWAI_STATE_BUS_OFF ? "OFF" : "otro"),
                  (unsigned long)enviadas, (unsigned long)rxPorSeg, masterVisto ? 1 : 0,
                  ult182[0], ult182[1], ult182[2], ult182[3], ult182[4], ult182[5], ult182[6], ult182[7],
                  nPie(estPie), pisar ? 1 : 0, mvParo, (unsigned long)disparos, timonArmado ? 1 : 0,
                  thActual, thObjetivo, hayLatido ? (long)(ahora - tUltLinea) : -1L, (unsigned long)loopMaxUs);
    if (ahora - tLoopMax >= 10000) { tLoopMax = ahora; loopMaxUs = 0; }   // el peor de cada 10 s
  }
}
