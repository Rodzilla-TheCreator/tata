/*
  teleop_wasd.ino — UN ESP: marcha por el nodo 2 falso (CAN) + timón emulado con lazo cerrado. 23-nov-2026.
  Se maneja con teleop_wasd.py (W/S marcha, A/D timón). maje PARADO EN EL PEDAL REAL: el pedal es el paro.

  Junta, sin cambiar su lógica:
    · herramientas/can/banco_imitador/multipiloto_campo/multipiloto_campo.ino  (nodo 2 falso; movió el equipo 21-nov)
    · herramientas/emulador_timon/timon_lazo/timon_lazo.ino                     (la rueda llegó a todo, 23-nov)
  Solo se usa el eje izquierda/derecha del joystick (b1 del 0x182), que en este equipo es la MARCHA
  (campo/2026-11-23/resultados.md). Elevación, botones y palanca quedan en cero.

  ARRANQUE: LISTEN_ONLY, no manda ni un bit. 'A' (con la llave en OFF) lo arma: modo normal, espera el boot-up
  del grupo y se presenta como nodo 2. El timón funciona desde el arranque (no es CAN; solo lee el 0x184).

  SERIE 115200. La ventana manda cada 50 ms una línea que es mando y latido a la vez:
    L m=<-255..255> r=<grados|->
      m  marcha: + = joystick a la DERECHA (b4 0x02, hacia las uñas), - = IZQUIERDA (b4 0x04)
      r  objetivo de la rueda en grados (lazo cerrado con el 0x184), o '-' = sin objetivo (volante quieto)
    A   armar el CAN          X   silencio: vuelve a LISTEN_ONLY, 182 a cero, timón quieto
    S   invertir el sentido del timón
  WATCHDOG 200 ms sin línea L: 0x182 a CERO y volante quieto (la rueda se queda donde está).
  Cada 100 ms:  T can=<estado> arm=<0|1> m=<n> ang=<g> obj=<g|-> gps=<n> tim=<estado> hz184=<n> tec=<n> rec=<n>
*/
#include <math.h>
#include "driver/twai.h"

#define PIN_TX GPIO_NUM_22
#define PIN_RX GPIO_NUM_21

// ================= nodo 2 falso (multipiloto_campo) =================
const uint8_t  NODO = 2;
const uint32_t PERIODO_HB_MS = 100, RETARDO_BOOT = 800, PLAN_B_MS = 15000, WATCHDOG_MS = 200;
enum Estado { SIN_BOOT, PREOP, OPERACIONAL, PARADO };
Estado estado = SIN_BOOT;
bool armado = false;
uint32_t tGrupo = 0, tPrimeraTrama = 0, thb = 0, enviadas = 0;
uint8_t b1 = 0, b4 = 0;                // solo el eje X del joystick
int mando = 0;

// ================= timón (timon_lazo) =================
const float Vo = 2.47, Va = 1.98;
const float kV = 1.381, oV = 0.131, kC = 1.386, oC = 0.115;
const int DAC_V = 25, DAC_C = 26;
const uint32_t ID_ANG = 0x184;
const float ANG_MIN = -100.0f, ANG_MAX = 78.0f, BANDA = 0.5f, KP = 30.0f, RATE_MAX = 180.0f, RATE_MIN = 25.0f;
const uint32_t SIN184_MS = 300, SIGNO_MS = 400, STALL_MS = 1500;
float theta = 0, gps = 0, obj = 0, ang = NAN, angEmpuje = 0;
int signo = -1;                        // medido 23-nov
bool hayObj = false;
int dirEmpuje = 0;
uint32_t tAng = 0, n184 = 0, hz184 = 0, tHz = 0, tEmpuje = 0;
const char* estTim = "QUIETO";

uint32_t tLinea = 0;
bool latidoVivo = false;
unsigned long tPrev;
String buf;

// ---------------- CAN ----------------
twai_timing_config_t tcfg = TWAI_TIMING_CONFIG_250KBITS();
twai_filter_config_t fcfg = TWAI_FILTER_CONFIG_ACCEPT_ALL();
void instalar(twai_mode_t modo) {
  twai_general_config_t g = TWAI_GENERAL_CONFIG_DEFAULT(PIN_TX, PIN_RX, modo);
  g.rx_queue_len = 64; g.tx_queue_len = (modo == TWAI_MODE_NORMAL) ? 8 : 0;
  twai_driver_install(&g, &tcfg, &fcfg); twai_start();
}
void mandar(uint32_t id, const uint8_t* d, uint8_t n) {
  twai_message_t m = {}; m.identifier = id; m.data_length_code = n; if (n) memcpy(m.data, d, n);
  if (twai_transmit(&m, pdMS_TO_TICKS(5)) == ESP_OK) enviadas++;
}
void aCero() { b1 = 0; b4 = 0; mando = 0; }
void bootup() {
  const uint8_t b = 0x00; mandar(0x700 + NODO, &b, 1);
  estado = PREOP; thb = millis();
  Serial.printf("EV nodo 2: boot-up 702 00\n");
}
void atender(const twai_message_t& m) {
  uint32_t id = m.identifier;
  if (id == 0x000 && m.data_length_code >= 2 && (m.data[1] == NODO || m.data[1] == 0) && estado != SIN_BOOT) {
    switch (m.data[0]) {
      case 0x01: estado = OPERACIONAL; aCero(); Serial.println("EV nodo 2: NMT START -> operacional (182 en cero)"); break;
      case 0x02: estado = PARADO; Serial.println("EV nodo 2: NMT STOP"); break;
      case 0x80: estado = PREOP; Serial.println("EV nodo 2: NMT PRE-OP"); break;
      case 0x81: case 0x82: Serial.println("EV nodo 2: NMT RESET"); bootup(); break;
    }
  } else if (id == 0x600 + NODO && estado != SIN_BOOT) {
    if (m.data[0] == 0x40 && m.data[1] == 0x00 && m.data[2] == 0x10 && m.data[3] == 0x00) {
      const uint8_t r[8] = {0x43, 0x00, 0x10, 0x00, 0, 0, 0, 0}; mandar(0x580 + NODO, r, 8);
    } else if ((m.data[0] & 0xE0) == 0x40) {
      const uint8_t ab[8] = {0x80, m.data[1], m.data[2], m.data[3], 0x00, 0x00, 0x02, 0x06}; mandar(0x580 + NODO, ab, 8);
    }
  } else if (id == 0x080 && estado == OPERACIONAL) {
    uint8_t d[8] = {0, b1, 0, 0, b4, 0, 0, 0};   // PDO síncrono: sale detrás del SYNC
    mandar(0x180 + NODO, d, 8);
  } else if (estado == SIN_BOOT && tGrupo == 0 && m.data_length_code == 1 && m.data[0] == 0x00 &&
             (id == 0x701 || id == 0x704 || id == 0x707 || id == 0x708 || id == 0x71E)) {
    tGrupo = millis();
    Serial.printf("EV nodo 2: grupo detectado (%03lX), boot-up en %lu ms\n", (unsigned long)id, (unsigned long)RETARDO_BOOT);
  }
}
void silencio() {
  twai_stop(); twai_driver_uninstall(); instalar(TWAI_MODE_LISTEN_ONLY);
  armado = false; estado = SIN_BOOT; tGrupo = tPrimeraTrama = 0; aCero();
  Serial.println("EV SILENCIO: LISTEN_ONLY, no transmitimos nada ('A' para rearmar)");
}

// ---------------- timón ----------------
int code(float vdac) { if (vdac < 0) vdac = 0; if (vdac > 3.3) vdac = 3.3; return (int)(vdac / 3.3 * 255.0 + 0.5); }
void sacar(float verde, float cafe) { dacWrite(DAC_V, code((verde - oV) / kV)); dacWrite(DAC_C, code((cafe - oC) / kC)); }
void pararTimon(const char* porque, const char* e) {
  hayObj = false; gps = 0; dirEmpuje = 0; estTim = e;
  if (porque) Serial.printf("EV timon: %s -> volante quieto\n", porque);
}

// ---------------- serie ----------------
void linea(String s) {
  s.trim();
  if (!s.length()) return;
  char c = s[0];
  if (s == "A") {
    if (!armado) { twai_stop(); twai_driver_uninstall(); instalar(TWAI_MODE_NORMAL); armado = true;
                   Serial.println("EV ARMADO (modo normal, esperando el bus)"); }
    return;
  }
  if (s == "X") { silencio(); pararTimon(NULL, "QUIETO"); return; }
  if (s == "S") { signo = -signo; pararTimon(NULL, "QUIETO"); Serial.printf("EV timon: sentido %+d\n", signo); return; }
  if (c != 'L') return;
  tLinea = millis(); latidoVivo = true;
  const char* p = s.c_str();
  const char* pm = strstr(p, "m=");
  if (pm) {
    int v = constrain(atoi(pm + 2), -255, 255);
    mando = v;
    b1 = (uint8_t)abs(v);
    b4 = v > 0 ? 0x02 : (v < 0 ? 0x04 : 0);
  }
  const char* pr = strstr(p, "r=");
  if (pr) {
    if (pr[2] == '-') { if (hayObj) pararTimon(NULL, "QUIETO"); }
    else if (!isnan(ang)) {
      float o = constrain(atof(pr + 2), ANG_MIN, ANG_MAX);
      if (!hayObj) { dirEmpuje = 0; estTim = "YENDO"; }
      obj = o; hayObj = true;
    }
  }
}

void setup() {
  Serial.begin(115200);
  sacar(Vo + Va, Vo);
  instalar(TWAI_MODE_LISTEN_ONLY);
  tPrev = micros();
  Serial.println("EV teleop_wasd listo: CAN solo escucha hasta 'A'; timon con lazo, sentido -1");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') { if (buf.length()) { linea(buf); buf = ""; } }
    else if (buf.length() < 40) buf += c;
  }

  twai_message_t m;
  while (twai_receive(&m, 0) == ESP_OK) {
    if (m.identifier == ID_ANG && m.data_length_code >= 4) {
      ang = (int16_t)(m.data[2] | (m.data[3] << 8)) / 100.0f; tAng = millis(); n184++;
    }
    if (armado && tPrimeraTrama == 0) tPrimeraTrama = millis();
    if (armado) atender(m);
  }
  uint32_t ahora = millis();
  if (ahora - tHz >= 1000) { hz184 = n184; n184 = 0; tHz = ahora; }

  // watchdog: sin línea L -> 182 a cero y volante quieto
  if (latidoVivo && (int32_t)(ahora - tLinea) > (int32_t)WATCHDOG_MS) {
    latidoVivo = false; aCero(); pararTimon(NULL, "QUIETO");
    Serial.println("EV WATCHDOG: sin latido -> 182 a CERO, volante quieto");
  }

  // nodo 2
  if (armado) {
    if (estado == SIN_BOOT && tGrupo && ahora - tGrupo >= RETARDO_BOOT) bootup();
    if (estado == SIN_BOOT && !tGrupo && tPrimeraTrama && ahora - tPrimeraTrama >= PLAN_B_MS) {
      Serial.println("EV nodo 2: plan B, bus vivo 15 s sin grupo"); bootup();
    }
    if (estado != SIN_BOOT && ahora - thb >= PERIODO_HB_MS) {
      thb = ahora; uint8_t s = (estado == OPERACIONAL) ? 0x05 : (estado == PARADO ? 0x04 : 0x7F);
      mandar(0x700 + NODO, &s, 1);
    }
  }

  // timón: lazo cerrado
  float pedido = 0;
  if (hayObj && (isnan(ang) || (int32_t)(ahora - tAng) > (int32_t)SIN184_MS)) pararTimon("SIN 0x184", "SIN_184");
  if (hayObj) {
    float err = obj - ang;
    if (fabsf(err) < BANDA) { estTim = "LLEGO"; dirEmpuje = 0; }
    else {
      pedido = constrain(KP * err, -RATE_MAX, RATE_MAX);
      if (fabsf(pedido) < RATE_MIN) pedido = pedido > 0 ? RATE_MIN : -RATE_MIN;
      estTim = "YENDO";
      int dir = pedido > 0 ? 1 : -1;
      if (dir != dirEmpuje) { dirEmpuje = dir; tEmpuje = ahora; angEmpuje = ang; }
      float avance = (ang - angEmpuje) * dirEmpuje;
      if (ahora - tEmpuje > SIGNO_MS && avance < -1.0f) { pararTimon("SENTIDO AL REVES (S invierte)", "SIGNO_MAL"); pedido = 0; }
      else if (ahora - tEmpuje > STALL_MS) {
        if (fabsf(avance) < 0.3f) { pararTimon("SIN RESPUESTA", "SIN_RESP"); pedido = 0; }
        else { tEmpuje = ahora; angEmpuje = ang; }
      }
    }
  }
  gps = pedido * signo;
  unsigned long tu = micros(); float dt = (tu - tPrev) / 1e6; tPrev = tu;
  theta += gps * (PI / 180.0f) * dt;
  if (theta > 6.28318f) theta -= 6.28318f;
  if (theta < 0) theta += 6.28318f;
  sacar(Vo + Va * cos(theta), Vo + Va * sin(theta));

  static uint32_t tp = 0;
  if (ahora - tp >= 100) {
    tp = ahora;
    twai_status_info_t st; twai_get_status_info(&st);
    char o[12]; if (hayObj) snprintf(o, sizeof o, "%.1f", obj); else strcpy(o, "-");
    const char* ne[] = {"SIN_BOOT", "PREOP", "OPERACIONAL", "PARADO"};
    Serial.printf("T can=%s arm=%d m=%d ang=%.2f obj=%s gps=%.0f tim=%s hz184=%lu tec=%lu rec=%lu bus=%s\n",
                  ne[estado], armado ? 1 : 0, mando, isnan(ang) ? 0.0f : ang, o, gps, estTim, (unsigned long)hz184,
                  (unsigned long)st.tx_error_counter, (unsigned long)st.rx_error_counter,
                  st.state == TWAI_STATE_RUNNING ? "ok" : (st.state == TWAI_STATE_BUS_OFF ? "OFF" : "?"));
  }
  delayMicroseconds(500);
}
