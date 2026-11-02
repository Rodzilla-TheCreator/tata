// mcp_prueba.ino — ¿el módulo MCP2515 + TJA1050 de C&D transmite bien a 250k? SOLO BANCO.
// ESTE SKETCH TRANSMITE. NUNCA con el cable en el equipo.
//
// Tres pruebas, cada una con su lectura:
//  1. SPI: reset, CANSTAT debe dar 0x80 y un registro escrito debe leerse igual.
//  2. LOOPBACK interno del MCP2515 (no usa el transceptor): manda y se recibe a sí mismo.
//  3. NORMAL a 250k, sin nadie que dé ACK: el MCP2515 reintenta la misma trama sin parar.
//     a) El propio MCP2515 lee cada bit que pone. Si su TJA tarda en soltar el bus,
//        detecta errores de bit: TEC sube de 8 en 8 hasta BUS-OFF (EFLG bit 5).
//        Transceptor sano: solo errores de ACK, TEC se queda en 128 (pasivo) y no hay bus-off.
//     b) El TJA viejo, que como RECEPTOR es rápido (0.24/0.40 µs), mide en GPIO RX cuánto
//        dura cada tramo dominante/recesivo. Sano: múltiplos de 4 µs (1 bit a 250k).
//        Lento al soltar (~16 µs): dominantes de 20 µs o más y recesivos cortos que faltan.
//
// Cableado: MCP VCC 5V, GND común. SCK→18, SI→23, SO→19, CS→5 (por el conversor de nivel,
// el MCP2515 a 5 V pide 3.5 V en sus entradas y su SO saca 5 V). INT sin conectar.
// Bus: CANH MCP ↔ CANH TJA viejo (pin 8 del DB9 macho), CANL ↔ CANL (pin 3), los 120 Ω de
// siempre en 8–3, jumper J1 del MCP QUITADO (mismo bus que en las pruebas de retardo).
// TJA viejo igual que antes: RX → divisor → GPIO 21, TX → GPIO 22 (queda en alto, recesivo).
#include <SPI.h>
#include "soc/gpio_reg.h"
#define CS 5
#define RX 21
#define TX_VIEJO 22
#define CRISTAL_MHZ 8          // leer el cristal del módulo: 8.000 o 16.000

static inline int rx() { return (REG_READ(GPIO_IN_REG) >> RX) & 1; }
SPISettings spi(1000000, MSBFIRST, SPI_MODE0);
uint8_t lee(uint8_t a) { SPI.beginTransaction(spi); digitalWrite(CS, LOW); SPI.transfer(0x03); SPI.transfer(a);
  uint8_t v = SPI.transfer(0); digitalWrite(CS, HIGH); SPI.endTransaction(); return v; }
void escribe(uint8_t a, uint8_t v) { SPI.beginTransaction(spi); digitalWrite(CS, LOW); SPI.transfer(0x02); SPI.transfer(a);
  SPI.transfer(v); digitalWrite(CS, HIGH); SPI.endTransaction(); }
void comando(uint8_t c) { SPI.beginTransaction(spi); digitalWrite(CS, LOW); SPI.transfer(c); digitalWrite(CS, HIGH); SPI.endTransaction(); }
bool modo(uint8_t reqop) { escribe(0x0F, reqop); for (int i = 0; i < 100; i++) { if ((lee(0x0E) & 0xE0) == reqop) return true; delay(1); } return false; }

void cargarTrama() {           // 0x123, 8 bytes con 0x55/0xAA: muchos flancos
  escribe(0x31, 0x123 >> 3); escribe(0x32, (0x123 & 7) << 5); escribe(0x35, 8);
  for (int i = 0; i < 8; i++) escribe(0x36 + i, (i & 1) ? 0xAA : 0x55);
}

uint32_t dom[101], rec[101];   // histograma en µs: tramo 0..99, 100 = más largo
void medirTramos(uint32_t ventanas) {
  memset(dom, 0, sizeof dom); memset(rec, 0, sizeof rec);
  for (uint32_t w = 0; w < ventanas; w++) {
    noInterrupts();
    uint32_t fin = ESP.getCycleCount() + 240 * 20000, t = ESP.getCycleCount(); int s = rx();   // 20 ms
    while ((int32_t)(fin - ESP.getCycleCount()) > 0) {
      int r = rx();
      if (r != s) { uint32_t ahora = ESP.getCycleCount(), us = (ahora - t + 120) / 240;
        if (us > 100) us = 100; (s ? rec : dom)[us]++; s = r; t = ahora; }
    }
    interrupts(); delay(2);
  }
}
void imprimirHisto(const char* nom, uint32_t* h) {
  Serial.printf("  %s (µs: veces)", nom);
  for (int i = 0; i <= 100; i++) if (h[i]) Serial.printf("  %s%d:%lu", i == 100 ? ">=" : "", i, (unsigned long)h[i]);
  Serial.println();
}

void setup() {
  Serial.begin(115200); delay(700);
  pinMode(TX_VIEJO, OUTPUT); digitalWrite(TX_VIEJO, HIGH); pinMode(RX, INPUT);
  pinMode(CS, OUTPUT); digitalWrite(CS, HIGH); SPI.begin(18, 19, 23, CS);
  Serial.println("\n=== mcp_prueba · SOLO BANCO · este sketch TRANSMITE ===");

  comando(0xC0); delay(10);
  uint8_t st = lee(0x0E); escribe(0x2A, 0x5A); uint8_t eco = lee(0x2A);
  Serial.printf("1. SPI   CANSTAT=0x%02X (esperado 0x80)   escribo 0x5A, leo 0x%02X   -> %s\n", st, eco,
                (st == 0x80 && eco == 0x5A) ? "OK" : "FALLA: revisar SCK/SI/SO/CS, conversor y 5 V");
  if (!(st == 0x80 && eco == 0x5A)) return;

  escribe(0x2A, CRISTAL_MHZ == 16 ? 0x01 : 0x00); escribe(0x29, 0xB1); escribe(0x28, 0x05);   // 250k, 16 TQ, muestreo 62.5 %
  escribe(0x60, 0x60);                                    // RXB0: aceptar todo
  cargarTrama();
  modo(0x40); escribe(0x2C, 0); comando(0x81); delay(5);
  uint8_t intf = lee(0x2C), d0 = lee(0x66), sidh = lee(0x61);
  Serial.printf("2. LOOPBACK  recibido=%s  SIDH=0x%02X (esperado 0x24)  D0=0x%02X (esperado 0x55)  -> %s\n",
                (intf & 1) ? "si" : "no", sidh, d0, ((intf & 1) && sidh == 0x24 && d0 == 0x55) ? "OK, el MCP2515 anda" : "FALLA");

  comando(0xC0); delay(10);
  escribe(0x2A, CRISTAL_MHZ == 16 ? 0x01 : 0x00); escribe(0x29, 0xB1); escribe(0x28, 0x05);
  cargarTrama();
  bool ok = modo(0x00);
  Serial.printf("3. NORMAL 250k (cristal %d MHz) modo=%s · transmitiendo sin ACK...\n", CRISTAL_MHZ, ok ? "OK" : "NO ENTRA");
  comando(0x81);
  medirTramos(25);                                        // 0.5 s de bus
  uint8_t tec = lee(0x1C), eflg = lee(0x2D), txc = lee(0x30);
  Serial.printf("   a) MCP2515: TEC=%u  EFLG=0x%02X  TXB0CTRL=0x%02X  -> %s\n", tec, eflg, txc,
                (eflg & 0x20) ? "BUS-OFF: errores de bit, su transceptor NO sigue al bus"
                : (eflg & 0x10) ? "pasivo sin bus-off: solo falta de ACK, su transceptor SIGUE al bus"
                : "raro: ni pasivo ni bus-off (¿alguien da ACK?)");
  Serial.println("   b) tramos medidos con el TJA viejo como receptor (sano: 4, 8, 12, 16, 20 µs):");
  imprimirHisto("dominante", dom); imprimirHisto("recesivo ", rec);
  modo(0x80);                                             // deja de transmitir
  Serial.println("Fin. El MCP2515 queda en configuración, callado.");
}
void loop() { delay(1000); }
