// pie.ino — el pie del rig (hombre muerto) con watchdog de 200 ms y rearme manual.
// Módulo que después entra tal cual en rig.ino (herramientas/rig/tarea_firmware.md, reglas 2, 3, 5 y 7).
//
// Hardware (herramientas/emulador_pedal/LEEME.md, dos módulos de relé activos en ALTO, jumper en H):
//   GPIO27 -> IN de los dos módulos (recomendado 10 k de IN a GND)
//   GPIO32 -> botón de rearme a GND (pull-up interno)
//   GPIO2  -> LED: fijo = pisando · parpadeo = disparado, esperando rearme · apagado = sin pisar
//   GPIO34 <- puente desde GPIO27, SOLO para medir el tiempo de suelta (prueba P2). Opcional.
//   GPIO35 <- el paro: VCC de los módulos (después del paro) por un divisor 10 k arriba / 20 k abajo.
//             Con 5 V lee ~3120 mV, sin 5 V ~140 mV (medido 19-nov). Si cae, el pie queda DISPARADO.
//
// Protocolo serie, 115200: la laptop manda una línea cada 50 ms, que es a la vez mando y latido.
//   "L ... pie=1"  (pisar)   ·   "L ... pie=0"  (soltar)
//   Solo cuenta como latido una línea que empieza con 'L' y trae pie=0 o pie=1. Lo demás se ignora.
//   "R" = pedido de rearme desde el teclado, SOLO si REARME_POR_SERIE = 1 (banco).
// El ESP manda cada 1 s:  E est=<SIN_ARMAR|ARMADO|DISPARADO> pie=<0|1> lat=<ms> paro=<mV> loopmax=<us> disparos=<n>
// y en cada evento:       EV <texto>

#include <esp_task_wdt.h>

// ---- Ajustes (las compilaciones de prueba cambian solo esto) ----
#define WATCHDOG_MS      200   // P2, control: compilar con 5000 y la prueba tiene que dar FALLA
#define USAR_TASK_WDT    1     // P5, control: compilar con 0 y el cuelgue deja el pie pisado
#define PRUEBA_CUELGUE   0     // P5: con 1, la línea "HANG" cuelga el loop a propósito
#define TASK_WDT_MS      1000
// Banco: la tecla r de pie.py rearma (además del botón del GPIO32). En el montacargas va en 0:
// el rearme tiene que ser un botón en el fierro, no algo que la laptop pueda mandar sola.
#define REARME_POR_SERIE 1

const int PIN_PIE    = 27;
const int PIN_REARME = 32;
const int PIN_LED    = 2;
const int PIN_MIDE   = 34;   // entrada solamente
const int PIN_PARO   = 35;   // entrada solamente
const int PARO_ALTO_MV = 2000;   // arriba de esto: módulos CON 5 V
const int PARO_BAJO_MV = 1200;   // abajo de esto: módulos SIN 5 V (en medio, se queda como estaba)

enum Estado { SIN_ARMAR, ARMADO, DISPARADO };
Estado estado = SIN_ARMAR;

bool     pideMando   = false;   // último pie= recibido
uint32_t tUltLinea   = 0;       // millis() de la última línea válida
bool     hayLatido   = false;   // alguna vez llegó una línea válida
uint32_t disparos    = 0;
uint32_t loopMaxUs   = 0;
uint32_t tAntLoop    = 0;
uint32_t tReporte    = 0;
uint32_t tBotonBajo  = 0;
bool     botonPrevio = false;

// medición de P2 (puente 27 -> 34)
bool     midiendo    = false;
uint32_t tDisparoUs  = 0;
uint32_t tLineaUs    = 0;
uint32_t tUltLineaUs = 0;

char     buf[128];
uint8_t  nbuf = 0;

bool     paroOk      = false;   // los módulos tienen 5 V
int      mvParo      = 0;
bool     pideRearme  = false;   // llegó "R" por serie (solo con REARME_POR_SERIE)

static void leerParo() {
  mvParo = analogReadMilliVolts(PIN_PARO);
  if (mvParo > PARO_ALTO_MV) paroOk = true;
  else if (mvParo < PARO_BAJO_MV) paroOk = false;
}

static inline void pie(bool pisar) { digitalWrite(PIN_PIE, pisar ? HIGH : LOW); }

static const char* nombre(Estado e) {
  return e == SIN_ARMAR ? "SIN_ARMAR" : e == ARMADO ? "ARMADO" : "DISPARADO";
}

static bool latidoFresco(uint32_t ahora) {
  return hayLatido && (uint32_t)(ahora - tUltLinea) < WATCHDOG_MS;
}

static void procesarLinea(const char* s) {
#if PRUEBA_CUELGUE
  if (strcmp(s, "HANG") == 0) { Serial.println("EV cuelgue a proposito"); Serial.flush(); while (1) { } }
#endif
#if REARME_POR_SERIE
  if (s[0] == 'R' && s[1] == 0) { pideRearme = true; return; }
#endif
  if (s[0] != 'L') return;
  const char* p = strstr(s, "pie=");
  if (!p || (p[4] != '0' && p[4] != '1')) return;
  pideMando   = (p[4] == '1');
  tUltLinea   = millis();
  tUltLineaUs = micros();
  hayLatido   = true;
}

static void leerSerie() {
  while (Serial.available()) {       // sin esperas: solo lo que ya llegó
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') { buf[nbuf] = 0; if (nbuf) procesarLinea(buf); nbuf = 0; }
    else if (nbuf < sizeof(buf) - 1) buf[nbuf++] = c;
    else nbuf = 0;                   // línea demasiado larga: se descarta entera
  }
}

void setup() {
  // Regla 5: lo primero, el pie suelto. Nada antes de esto.
  pinMode(PIN_PIE, OUTPUT);
  digitalWrite(PIN_PIE, LOW);

  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);
  pinMode(PIN_REARME, INPUT_PULLUP);
  pinMode(PIN_MIDE, INPUT);
  pinMode(PIN_PARO, INPUT);

  Serial.begin(115200);
  leerParo();

#if USAR_TASK_WDT
  esp_task_wdt_config_t cfg = { .timeout_ms = TASK_WDT_MS, .idle_core_mask = 0, .trigger_panic = true };
  if (esp_task_wdt_reconfigure(&cfg) != ESP_OK) esp_task_wdt_init(&cfg);
  esp_task_wdt_add(NULL);
#endif

  Serial.printf("EV arranque WATCHDOG_MS=%d TASK_WDT=%d CUELGUE=%d REARME_SERIE=%d paro=%d mV (%s)\n",
                WATCHDOG_MS, USAR_TASK_WDT, PRUEBA_CUELGUE, REARME_POR_SERIE, mvParo,
                paroOk ? "modulos CON 5 V" : "modulos SIN 5 V");
  tAntLoop = micros();
}

void loop() {
#if USAR_TASK_WDT
  esp_task_wdt_reset();
#endif
  uint32_t ahoraUs = micros();
  uint32_t dt = ahoraUs - tAntLoop;
  tAntLoop = ahoraUs;
  if (dt > loopMaxUs) loopMaxUs = dt;

  uint32_t ahora = millis();
  leerSerie();
  bool fresco = latidoFresco(ahora);

  // Regla 2: sin latido fresco, el pie suelta. Si estaba armado, queda DISPARADO.
  if (estado == ARMADO && !fresco) {
    pie(false);
    estado = DISPARADO;
    disparos++;
    tDisparoUs = micros();
    tLineaUs   = tUltLineaUs;
    midiendo   = true;
    Serial.printf("EV watchdog: %lu ms sin latido -> pie suelto, esperando rearme\n",
                  (unsigned long)(ahora - tUltLinea));
  }

  // El paro: si los módulos se quedan sin 5 V, el pie suelta y queda DISPARADO.
  // Al volver los 5 V no se re-pisa: hace falta el rearme (ISO 13850).
  bool paroAntes = paroOk;
  leerParo();
  if (paroAntes && !paroOk) {
    pie(false);
    if (estado == ARMADO) { estado = DISPARADO; disparos++; }
    Serial.printf("EV paro: modulos sin 5 V (%d mV) -> pie suelto, %s\n", mvParo,
                  estado == DISPARADO ? "DISPARADO, esperando rearme" : nombre(estado));
  } else if (!paroAntes && paroOk) {
    Serial.printf("EV paro liberado: modulos con 5 V (%d mV). El pie sigue suelto hasta el rearme\n", mvParo);
  }

  // Regla 3: rearme manual. Botón 50 ms abajo (o r en el banco) + latido fresco + paro liberado.
  // Nunca se re-pisa solo.
  bool boton = (digitalRead(PIN_REARME) == LOW);
  static bool botonUsado = false;          // un pedido por apretada
  if (boton && !botonPrevio) { tBotonBajo = ahora; botonUsado = false; }
  botonPrevio = boton;
  bool botonListo = boton && !botonUsado && (ahora - tBotonBajo) >= 50;
  if (botonListo) botonUsado = true;
  bool pedido = botonListo || pideRearme;
  pideRearme = false;
  if (pedido && estado == ARMADO) {
    Serial.println("EV rearme: ya estaba armado");
  } else if (pedido) {
    if (!paroOk)      Serial.println("EV rearme rechazado: el paro esta cortando (modulos sin 5 V)");
    else if (!fresco) Serial.println("EV rearme rechazado: no hay latido fresco");
    else { estado = ARMADO; Serial.println("EV rearmado"); }
  }

  // Salida
  bool pisar = (estado == ARMADO) && fresco && pideMando && paroOk;
  pie(pisar);

  // P2: tiempo desde la última línea hasta que GPIO34 (puenteado a 27) lee bajo
  if (midiendo) {
    if (digitalRead(PIN_MIDE) == LOW) {
      Serial.printf("EV P2 suelta: %lu ms desde la ultima linea (limite %d)\n",
                    (unsigned long)((micros() - tLineaUs) / 1000), WATCHDOG_MS);
      midiendo = false;
    } else if (micros() - tDisparoUs > 100000) {
      Serial.println("EV P2: GPIO34 no baja (sin puente 27->34?)");
      midiendo = false;
    }
  }

  // LED
  if (pisar)                    digitalWrite(PIN_LED, HIGH);
  else if (estado == DISPARADO) digitalWrite(PIN_LED, (ahora / 250) % 2);
  else                          digitalWrite(PIN_LED, LOW);

  // Reporte cada 1 s
  if (ahora - tReporte >= 1000) {
    tReporte = ahora;
    Serial.printf("E est=%s pie=%d lat=%ld paro=%d loopmax=%lu disparos=%lu\n", nombre(estado), pisar ? 1 : 0,
                  hayLatido ? (long)(ahora - tUltLinea) : -1L, mvParo, (unsigned long)loopMaxUs,
                  (unsigned long)disparos);
  }
}
