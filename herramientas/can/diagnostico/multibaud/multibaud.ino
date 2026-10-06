// Self-test NO_ACK a varias velocidades: 10 tramas cada una, con Self Reception Request.
#include "driver/twai.h"
struct V { const char* n; twai_timing_config_t t; };
void prueba(const char* nombre, twai_timing_config_t t) {
  twai_general_config_t g = TWAI_GENERAL_CONFIG_DEFAULT(GPIO_NUM_21, GPIO_NUM_22, TWAI_MODE_NO_ACK);
  twai_filter_config_t f = TWAI_FILTER_CONFIG_ACCEPT_ALL();
  if (twai_driver_install(&g, &t, &f) != ESP_OK || twai_start() != ESP_OK) { Serial.printf("BAUD %-5s no arranca\n", nombre); return; }
  int ok = 0;
  for (int n = 0; n < 10; n++) {
    twai_message_t m = {}; m.identifier = 0x100 + n; m.data_length_code = 8; m.self = 1;
    for (int i = 0; i < 8; i++) m.data[i] = n * 8 + i;
    twai_transmit(&m, pdMS_TO_TICKS(100));
    twai_message_t r;
    if (twai_receive(&r, pdMS_TO_TICKS(150)) == ESP_OK && r.identifier == m.identifier && !memcmp(r.data, m.data, 8)) ok++;
  }
  twai_status_info_t s; twai_get_status_info(&s);
  Serial.printf("BAUD %-5s eco %2d/10   txerr %3lu rxerr %3lu arblost %lu\n", nombre, ok,
    (unsigned long)s.tx_error_counter, (unsigned long)s.rx_error_counter, (unsigned long)s.arb_lost_count);
  twai_stop(); twai_driver_uninstall(); delay(50);
}
void setup() {
  Serial.begin(115200); delay(700);
  prueba("25k",  TWAI_TIMING_CONFIG_25KBITS());
  prueba("50k",  TWAI_TIMING_CONFIG_50KBITS());
  prueba("100k", TWAI_TIMING_CONFIG_100KBITS());
  prueba("125k", TWAI_TIMING_CONFIG_125KBITS());
  prueba("250k", TWAI_TIMING_CONFIG_250KBITS());
  Serial.println("BAUD FIN");
}
void loop() { delay(1000); }
