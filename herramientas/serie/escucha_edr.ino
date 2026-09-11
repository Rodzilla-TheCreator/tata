/* ──────────────────────────────────────────────────────────────────────────
   TaTa · escucha del puerto de servicio del EDR18N2
   ESP32-U  +  módulo T132 (SP3232, RS-232 ⇄ TTL)

   CABLEADO
     T132 GND → ESP32 GND
     T132 VCC → ESP32 3V3      (3.3 V, nunca 5 V)
     T132 TX  → ESP32 GPIO16
     T132 RX  → ESP32 GPIO17
     Si no oye nada, intercambiá GPIO16 y GPIO17.

   SOLO ESCUCHA. Nunca transmite al montacargas.
   Abrí el Monitor Serie a 115200.
   ────────────────────────────────────────────────────────────────────────── */

#include <Arduino.h>

#define PIN_RX   16
#define PIN_TX   17

// ── modo ──────────────────────────────────────────────────────────────────
// false = barre todas las combinaciones
// true  = se queda fijo en FIJO_BAUD / FIJO_CFG  (para navegar el menú
//         del tablero mientras escucha)
const bool  MODO_FIJO  = false;
const long  FIJO_BAUD  = 9600;
const uint32_t FIJO_CFG = SERIAL_8N1;

const uint32_t VENTANA_MS = 3000;   // escucha por combinación

// ── combinaciones ─────────────────────────────────────────────────────────
const long BAUDS[] = {1200, 2400, 4800, 9600, 14400, 19200,
                      38400, 57600, 115200};
struct Cfg { uint32_t v; const char* nom; };
const Cfg CFGS[] = {
  {SERIAL_8N1, "8N1"}, {SERIAL_8E1, "8E1"}, {SERIAL_8O1, "8O1"},
  {SERIAL_7E1, "7E1"}, {SERIAL_7O1, "7O1"}, {SERIAL_8N2, "8N2"},
};
const int NB = sizeof(BAUDS)/sizeof(BAUDS[0]);
const int NC = sizeof(CFGS)/sizeof(CFGS[0]);

uint8_t buf[2048];

void volcar(int n, long baud, const char* cfg) {
  int legibles = 0;
  for (int i = 0; i < n; i++)
    if ((buf[i] >= 32 && buf[i] < 127) || buf[i] == 10 || buf[i] == 13) legibles++;
  int pct = (100 * legibles) / n;

  Serial.printf("\n  >>> %ld %s : %d bytes, %d%% legible %s\n",
                baud, cfg, n, pct, pct > 70 ? "  <<< MIRA ESTO" : "");

  Serial.print("      HEX  ");
  for (int i = 0; i < n && i < 64; i++) Serial.printf("%02X ", buf[i]);
  Serial.print("\n      TXT  ");
  for (int i = 0; i < n && i < 160; i++) {
    char c = buf[i];
    Serial.print((c >= 32 && c < 127) ? c : '.');
  }
  Serial.println();
}

int escuchar(long baud, uint32_t cfg, const char* nom) {
  Serial2.begin(baud, cfg, PIN_RX, PIN_TX);
  delay(60);
  while (Serial2.available()) Serial2.read();     // limpia lo viejo

  int n = 0;
  uint32_t t0 = millis();
  while (millis() - t0 < VENTANA_MS) {
    while (Serial2.available() && n < (int)sizeof(buf)) buf[n++] = Serial2.read();
    delay(2);
  }
  Serial2.end();
  return n;
}

void setup() {
  Serial.begin(115200);
  delay(1200);
  Serial.println("\n\n===========================================");
  Serial.println("  TaTa · escucha del puerto EDR18N2");
  Serial.println("  SOLO LECTURA · nunca transmite");
  Serial.println("===========================================\n");
  if (MODO_FIJO)
    Serial.printf("MODO FIJO: %ld 8N1 — navegá el menú del tablero ahora\n\n",
                  FIJO_BAUD);
}

void loop() {
  if (MODO_FIJO) {
    Serial2.begin(FIJO_BAUD, FIJO_CFG, PIN_RX, PIN_TX);
    Serial.println("escuchando... (todo lo que llegue sale acá)\n");
    while (true) {
      if (Serial2.available()) {
        uint8_t c = Serial2.read();
        Serial.printf("%02X ", c);
        if (c == 10 || c == 13) Serial.println();
      }
    }
  }

  int total = 0;
  for (int b = 0; b < NB; b++) {
    Serial.printf("\n─── %ld baudios ───\n", BAUDS[b]);
    for (int c = 0; c < NC; c++) {
      int n = escuchar(BAUDS[b], CFGS[c].v, CFGS[c].nom);
      if (n) { volcar(n, BAUDS[b], CFGS[c].nom); total += n; }
      else   { Serial.printf("  %s : silencio\n", CFGS[c].nom); }
    }
  }

  Serial.printf("\n===========================================\n");
  Serial.printf("  VUELTA COMPLETA · %d bytes en total\n", total);
  if (!total) {
    Serial.println("  Cero en las 54 combinaciones.");
    Serial.println("  · probá intercambiando GPIO16 y GPIO17");
    Serial.println("  · probá con y sin el null-modem");
    Serial.println("  · o el puerto calla hasta que le preguntan");
  }
  Serial.println("===========================================");
  Serial.println("  repitiendo en 5 s...\n");
  delay(5000);
}
