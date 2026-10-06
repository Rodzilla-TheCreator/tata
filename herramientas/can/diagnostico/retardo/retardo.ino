// Mide el retardo TX->RX de cada flanco, en ns, con el contador de ciclos (240 MHz).
#include "soc/gpio_reg.h"
#define TX 21
#define RX 22
static inline int rx() { return (REG_READ(GPIO_IN_REG) >> RX) & 1; }
void setup() {
  Serial.begin(115200); delay(700);
  pinMode(TX, OUTPUT); pinMode(RX, INPUT); digitalWrite(TX, HIGH); delay(10);
  uint32_t baja_min=1e9, baja_max=0, sube_min=1e9, sube_max=0, fallas=0; uint64_t baja_sum=0, sube_sum=0; int n=0;
  for (int i = 0; i < 500; i++) {
    noInterrupts();
    uint32_t t0 = ESP.getCycleCount(); REG_WRITE(GPIO_OUT_W1TC_REG, 1 << TX);
    while (rx() == 1 && ESP.getCycleCount() - t0 < 24000) {}          // hasta 100 us
    uint32_t tb = ESP.getCycleCount() - t0;
    for (volatile int k = 0; k < 400; k++) {}                           // ~2 us en dominante
    uint32_t t1 = ESP.getCycleCount(); REG_WRITE(GPIO_OUT_W1TS_REG, 1 << TX);
    while (rx() == 0 && ESP.getCycleCount() - t1 < 24000) {}
    uint32_t ts = ESP.getCycleCount() - t1;
    interrupts();
    if (tb >= 24000 || ts >= 24000) { fallas++; delayMicroseconds(300); continue; }
    baja_sum += tb; sube_sum += ts; n++;
    baja_min = min(baja_min, tb); baja_max = max(baja_max, tb);
    sube_min = min(sube_min, ts); sube_max = max(sube_max, ts);
    delayMicroseconds(300);
  }
  float k = 1000.0 / 240.0;   // ns por ciclo
  Serial.printf("RETARDO TX baja -> RX baja: prom %.0f ns  min %.0f  max %.0f\n", n?baja_sum*k/n:0, baja_min*k, baja_max*k);
  Serial.printf("RETARDO TX sube -> RX sube: prom %.0f ns  min %.0f  max %.0f\n", n?sube_sum*k/n:0, sube_min*k, sube_max*k);
  Serial.printf("RETARDO muestras %d  fallas %lu  (bit a 250k = 4000 ns, muestreo ~3500 ns)\n", n, (unsigned long)fallas);
}
void loop() { delay(1000); }
