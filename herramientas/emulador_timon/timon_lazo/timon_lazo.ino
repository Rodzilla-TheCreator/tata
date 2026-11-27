/*
  timon_lazo.ino — el emulador del timón (emulador_timon.ino, calibrado 26-oct) con LAZO CERRADO
  sobre el ángulo real de la rueda, leído del bus. 23-nov-2026.

  QUÉ HACE
    Se le pide un ángulo de RUEDA en grados ("A30"). El ESP lee el ángulo real del 0x184 (nodo 4,
    bytes 2-3, int16, 0.01 grados, cero = rueda recta; campo/2026-11-23/resultados.md) y gira el
    volante emulado hasta que la rueda llega. No hace falta saber cuántas vueltas de volante hay de
    tope a tope: el lazo corrige solo.

  EL CAN SOLO ESCUCHA (TWAI_MODE_LISTEN_ONLY): no manda ni un bit, ni ACK. El timón no es CAN; el bus
  solo se lee para saber dónde está la rueda.

  HARDWARE: el de siempre del timón (DAC GPIO25 verde, GPIO26 café -> LM358 -> conector del nodo 4) MÁS
  la cadena CAN aislada al DB9 (GPIO22 TX, GPIO21 RX). GND del ESP = amarillo (el del timón).

  SERIE 115200, una orden por línea:
    A<grados>   objetivo de la rueda, lazo cerrado. Se recorta a [ANG_MIN, ANG_MAX]
    V<gps>      volante a mano, grados/s del volante (lazo abierto, para probar). V0 = quieto
    P<grados>   volante A MANO: posición absoluta del volante emulado (la ventana la manda al arrastrar el
                timón en pantalla, en pasos chicos). Cancela el objetivo
    X o 0       PARAR: volante quieto y sin objetivo
    S           invertir el sentido (si la rueda va al revés)
    K<kp>       ganancia (grados/s de volante por grado de error). Arranca en KP_INI
    M<gps>      velocidad máxima del volante. Arranca en RATE_MAX_INI
    .           latido
  WATCHDOG: 300 ms sin ninguna línea -> PARAR. La ventana (timon_lazo.py) manda '.' cada 50 ms.

  PARA SOLO, y lo dice con una línea "EV ...":
    · sin 0x184 por 300 ms (llave, CAN suelto)
    · SIGNO AL REVÉS: empujando, la rueda se movió > 1 grado para el otro lado (mandá S)
    · SIN RESPUESTA: 1.5 s empujando y la rueda se movió < 0.3 grados (tope, nodo 4 en falla)
  Cada 100 ms:  T obj=<g|-> ang=<g> err=<g> vol=<g> gps=<g> est=<...> sig=<+1|-1> hz184=<n>
*/
#include <math.h>
#include "driver/twai.h"

// ---- Timón: calibración del 26-oct (igual que emulador_timon.ino) ----
const float Vo = 2.47, Va = 1.98;
const float kV = 1.380, oV = 0.093;  // verde (GPIO25) · placa soldada, banco 27-nov
const float kC = 1.374, oC = 0.123;  // café  (GPIO26) · placa soldada, banco 27-nov
const int DAC_V = 25, DAC_C = 26;

// ---- CAN ----
#define PIN_TX GPIO_NUM_22
#define PIN_RX GPIO_NUM_21
const uint32_t ID_ANG = 0x184;

// ---- Lazo ----
const float ANG_MIN = -100.0f;       // topes medidos 23-nov: -103.2 / +80.6; se deja margen
const float ANG_MAX = 78.0f;
const float BANDA = 0.5f;            // grados: «llegó»
const float KP_INI = 30.0f;          // gps de volante por grado de error (rueda ~0.09 grados por grado de volante)
const float RATE_MAX_INI = 180.0f;   // gps de volante (~16 grados/s de rueda). Subir con M360 cuando el sentido este confirmado
const float RATE_MIN = 25.0f;        // gps mínimos mientras no llegó (para no quedarse a 0.6 grados)
const uint32_t WDOG_MS = 300, SIN184_MS = 300, SIGNO_MS = 400, STALL_MS = 1500;

float theta = 0;                     // rad, posición del volante emulado
float gps = 0;                       // grados/s del volante que se están aplicando
float kp = KP_INI, rateMax = RATE_MAX_INI;
int signo = -1;                      // medido 23-nov: volante + -> rueda - (con +1 las dos pruebas fueron al reves)
bool hayObj = false, manual = false;
float obj = 0, manualGps = 0;
float ang = NAN;                     // grados de rueda (0x184)
uint32_t tAng = 0, n184 = 0, hz184 = 0, tHz = 0;
uint32_t tLinea = 0, tEmpuje = 0;
float angEmpuje = 0;
int dirEmpuje = 0;
const char* est = "QUIETO";
unsigned long tPrev;
String buf;

int code(float vdac) { if (vdac < 0) vdac = 0; if (vdac > 3.3) vdac = 3.3; return (int)(vdac / 3.3 * 255.0 + 0.5); }
void sacar(float verde, float cafe) { dacWrite(DAC_V, code((verde - oV) / kV)); dacWrite(DAC_C, code((cafe - oC) / kC)); }

void parar(const char* porque, const char* estado) {
  hayObj = false; manual = false; gps = 0; dirEmpuje = 0; est = estado;
  if (porque) Serial.printf("EV %s -> volante quieto, sin objetivo\n", porque);
}

void orden(String s) {
  s.trim();
  if (!s.length()) return;
  char c = s[0];
  float v = s.substring(1).toFloat();
  if (c == '.') return;
  if (c == 'X' || c == 'x' || s == "0") { parar("PARAR pedido", "QUIETO"); return; }
  if (c == 'A' || c == 'a') {
    if (isnan(ang)) { Serial.println("EV no hay 0x184: no se puede ir a un angulo"); return; }
    obj = constrain(v, ANG_MIN, ANG_MAX); hayObj = true; manual = false; dirEmpuje = 0; est = "YENDO";
    if (obj != v) Serial.printf("EV objetivo %.1f recortado a %.1f (topes del equipo)\n", v, obj);
    else Serial.printf("EV objetivo %.1f\n", obj);
    return;
  }
  if (c == 'P' || c == 'p') {          // volante a mano: posición absoluta, como emulador_timon.ino
    float th = fmodf(v * PI / 180.0f, 6.28318f); if (th < 0) th += 6.28318f;
    theta = th; hayObj = false; manual = false; dirEmpuje = 0; est = "MANO";
    return;
  }
  if (c == 'V' || c == 'v') { manualGps = constrain(v, -rateMax, rateMax); manual = true; hayObj = false; dirEmpuje = 0; est = "MANUAL"; return; }
  if (c == 'S' || c == 's') { signo = -signo; parar(NULL, "QUIETO"); Serial.printf("EV signo invertido: ahora %+d\n", signo); return; }
  if (c == 'K' || c == 'k') { if (v > 0) kp = v; Serial.printf("EV kp=%.1f\n", kp); return; }
  if (c == 'M' || c == 'm') { if (v > 0) rateMax = v; Serial.printf("EV max=%.0f gps\n", rateMax); return; }
}

void leerCAN() {
  twai_message_t m;
  while (twai_receive(&m, 0) == ESP_OK) {
    if (m.identifier == ID_ANG && m.data_length_code >= 4) {
      int16_t raw = (int16_t)(m.data[2] | (m.data[3] << 8));
      ang = raw / 100.0f; tAng = millis(); n184++;
    }
  }
}

void setup() {
  Serial.begin(115200);
  sacar(Vo + Va, Vo);                  // punto válido del círculo (theta = 0), volante quieto
  twai_general_config_t g = TWAI_GENERAL_CONFIG_DEFAULT(PIN_TX, PIN_RX, TWAI_MODE_LISTEN_ONLY);
  g.rx_queue_len = 64;
  twai_timing_config_t t = TWAI_TIMING_CONFIG_250KBITS();
  twai_filter_config_t f = TWAI_FILTER_CONFIG_ACCEPT_ALL();
  bool can = twai_driver_install(&g, &t, &f) == ESP_OK && twai_start() == ESP_OK;
  tPrev = micros(); tLinea = millis();
  Serial.printf("EV timon_lazo listo · CAN %s (solo escucha) · topes %.0f / %.0f · kp %.0f · max %.0f gps\n",
                can ? "ok" : "FALLA", ANG_MIN, ANG_MAX, kp, rateMax);
}

void loop() {
  uint32_t ahora = millis();
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') { if (buf.length()) { tLinea = ahora; orden(buf); buf = ""; } }
    else if (buf.length() < 30) buf += c;
  }
  leerCAN();
  if (ahora - tHz >= 1000) { hz184 = n184; n184 = 0; tHz = ahora; }

  bool activo = hayObj || manual;
  ahora = millis();                    // 23-nov: leerCAN() pone tAng DESPUÉS del millis() de arriba; con el
                                       // ahora viejo, ahora - tAng daba negativo (uint32 enorme) = falso SIN 0x184
  if (activo && (int32_t)(ahora - tLinea) > (int32_t)WDOG_MS) parar("WATCHDOG: sin lineas por serie", "QUIETO");
  if (hayObj && (isnan(ang) || (int32_t)(ahora - tAng) > (int32_t)SIN184_MS)) parar("SIN 0x184 (llave o CAN)", "SIN_184");

  // ---- el lazo ----
  float pedido = 0;                    // gps del volante, antes del signo
  if (hayObj) {
    float err = obj - ang;
    if (fabsf(err) < BANDA) { pedido = 0; est = "LLEGO"; dirEmpuje = 0; }
    else {
      pedido = constrain(kp * err, -rateMax, rateMax);
      if (fabsf(pedido) < RATE_MIN) pedido = pedido > 0 ? RATE_MIN : -RATE_MIN;
      est = "YENDO";
      int dir = pedido > 0 ? 1 : -1;   // hacia dónde tiene que ir la rueda
      if (dir != dirEmpuje) { dirEmpuje = dir; tEmpuje = ahora; angEmpuje = ang; }
      float avance = (ang - angEmpuje) * dirEmpuje;    // + = va bien
      if (ahora - tEmpuje > SIGNO_MS && avance < -1.0f) { parar("SIGNO AL REVES: la rueda va para el otro lado (manda S)", "SIGNO_MAL"); pedido = 0; }
      else if (ahora - tEmpuje > STALL_MS) {
        if (fabsf(avance) < 0.3f) { parar("SIN RESPUESTA: 1.5 s empujando y la rueda no se mueve", "SIN_RESP"); pedido = 0; }
        else { tEmpuje = ahora; angEmpuje = ang; }   // se movió: ventana nueva
      }
    }
  } else if (manual) pedido = manualGps;
  gps = pedido * signo;

  unsigned long tu = micros(); float dt = (tu - tPrev) / 1e6; tPrev = tu;
  theta += gps * (PI / 180.0f) * dt;
  if (theta > 6.28318f) theta -= 6.28318f;
  if (theta < 0) theta += 6.28318f;
  sacar(Vo + Va * cos(theta), Vo + Va * sin(theta));

  static uint32_t tp = 0;
  if (ahora - tp >= 100) {
    tp = ahora;
    char o[12]; if (hayObj) snprintf(o, sizeof o, "%.1f", obj); else strcpy(o, "-");
    Serial.printf("T obj=%s ang=%.2f err=%.2f vol=%.1f gps=%.0f est=%s sig=%+d hz184=%lu\n", o,
                  isnan(ang) ? 0.0f : ang, hayObj && !isnan(ang) ? obj - ang : 0.0f, theta * 57.2958f, gps,
                  est, signo, (unsigned long)hz184);
  }
  delayMicroseconds(500);
}
