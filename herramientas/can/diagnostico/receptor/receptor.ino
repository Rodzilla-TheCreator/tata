// Prueba del RECEPTOR del TJA1050: el ESP32 simula otro nodo por GPIO25 (→100Ω→CANH)
// y GPIO26 (→100Ω→CANL). TX del TJA1050 (GPIO21) fijo en alto: su transmisor no actúa.
// Dominante: CANH alto, CANL bajo.  Recesivo: los dos bajos (diferencia 0).
#include "soc/gpio_reg.h"
#define TXT 21
#define RXT 22
#define H 25
#define L 26
static inline int rx() { return (REG_READ(GPIO_IN_REG) >> RXT) & 1; }
void setup() {
  Serial.begin(115200); delay(700);
  pinMode(TXT, OUTPUT); digitalWrite(TXT, HIGH);
  pinMode(RXT, INPUT);
  pinMode(H, OUTPUT); pinMode(L, OUTPUT); digitalWrite(H, LOW); digitalWrite(L, LOW);
  delay(10);
  Serial.printf("RECEPTOR reposo: RX=%d (debe ser 1)\n", rx());
  digitalWrite(H, HIGH); delayMicroseconds(20);
  Serial.printf("RECEPTOR dominante 20us: RX=%d (debe ser 0)\n", rx());
  digitalWrite(H, LOW); delay(5);
  uint32_t bmin=1e9,bmax=0,smin=1e9,smax=0,fallas=0; uint64_t bs=0,ss=0; int n=0;
  for (int i = 0; i < 500; i++) {
    noInterrupts();
    uint32_t t0 = ESP.getCycleCount(); REG_WRITE(GPIO_OUT_W1TS_REG, 1 << H);   // a dominante
    while (rx() == 1 && ESP.getCycleCount() - t0 < 24000) {}
    uint32_t tb = ESP.getCycleCount() - t0;
    for (volatile int k = 0; k < 400; k++) {}                                    // ~2 us
    uint32_t t1 = ESP.getCycleCount(); REG_WRITE(GPIO_OUT_W1TC_REG, 1 << H);   // a recesivo
    while (rx() == 0 && ESP.getCycleCount() - t1 < 24000) {}
    uint32_t ts = ESP.getCycleCount() - t1;
    interrupts();
    if (tb >= 24000 || ts >= 24000) { fallas++; delayMicroseconds(300); continue; }
    bs += tb; ss += ts; n++;
    bmin=min(bmin,tb); bmax=max(bmax,tb); smin=min(smin,ts); smax=max(smax,ts);
    delayMicroseconds(300);
  }
  float k = 1000.0/240.0;
  Serial.printf("RECEPTOR bus a dominante -> RX baja: prom %.0f ns  min %.0f  max %.0f\n", n?bs*k/n:0, bmin*k, bmax*k);
  Serial.printf("RECEPTOR bus a recesivo  -> RX sube: prom %.0f ns  min %.0f  max %.0f\n", n?ss*k/n:0, smin*k, smax*k);
  Serial.printf("RECEPTOR muestras %d  fallas %lu  (bit a 250k = 4000 ns)\n", n, (unsigned long)fallas);
}
void loop() { delay(1000); }
