#include "driver/twai.h"
void estado(const char* t) {
  twai_status_info_t s; twai_get_status_info(&s);
  const char* st[] = {"STOPPED","RUNNING","BUS_OFF","RECOVERING"};
  Serial.printf("DIAG %-14s estado=%s txerr=%lu rxerr=%lu pendTX=%lu pendRX=%lu txfail=%lu buserr=%lu arblost=%lu\n",
    t, st[s.state], (unsigned long)s.tx_error_counter, (unsigned long)s.rx_error_counter,
    (unsigned long)s.msgs_to_tx, (unsigned long)s.msgs_to_rx, (unsigned long)s.tx_failed_count,
    (unsigned long)s.bus_error_count, (unsigned long)s.arb_lost_count);
}
void alertas(const char* t) {
  uint32_t a = 0; twai_read_alerts(&a, pdMS_TO_TICKS(200));
  Serial.printf("DIAG %-14s alertas=0x%05lX", t, (unsigned long)a);
  struct { uint32_t f; const char* n; } L[] = {
    {TWAI_ALERT_TX_IDLE,"TX_IDLE"},{TWAI_ALERT_TX_SUCCESS,"TX_SUCCESS"},{TWAI_ALERT_RX_DATA,"RX_DATA"},
    {TWAI_ALERT_ERR_PASS,"ERR_PASS"},{TWAI_ALERT_BUS_ERROR,"BUS_ERROR"},{TWAI_ALERT_TX_FAILED,"TX_FAILED"},
    {TWAI_ALERT_RX_QUEUE_FULL,"RXQ_FULL"},{TWAI_ALERT_ERR_ACTIVE,"ERR_ACTIVE"},{TWAI_ALERT_BUS_OFF,"BUS_OFF"},
    {TWAI_ALERT_ABOVE_ERR_WARN,"ERR_WARN"},{TWAI_ALERT_ARB_LOST,"ARB_LOST"},{TWAI_ALERT_RX_FIFO_OVERRUN,"FIFO_OVR"}};
  for (auto& x : L) if (a & x.f) Serial.printf(" %s", x.n);
  Serial.println();
}
void setup() {
  Serial.begin(115200); delay(700);
  twai_general_config_t g = TWAI_GENERAL_CONFIG_DEFAULT(GPIO_NUM_21, GPIO_NUM_22, TWAI_MODE_NO_ACK);
  g.alerts_enabled = TWAI_ALERT_ALL;
  twai_timing_config_t t = TWAI_TIMING_CONFIG_250KBITS();
  twai_filter_config_t f = TWAI_FILTER_CONFIG_ACCEPT_ALL();
  Serial.printf("DIAG install=%d\n", twai_driver_install(&g, &t, &f));
  Serial.printf("DIAG start=%d\n", twai_start());
  delay(100); estado("tras arrancar"); alertas("tras arrancar");
  twai_message_t m = {}; m.identifier = 0x123; m.data_length_code = 2; m.data[0]=0xAA; m.data[1]=0x55; m.self = 1;
  Serial.printf("DIAG transmit=%d\n", twai_transmit(&m, pdMS_TO_TICKS(200)));
  delay(50); estado("tras 1 trama"); alertas("tras 1 trama");
  twai_message_t r; esp_err_t e = twai_receive(&r, pdMS_TO_TICKS(300));
  Serial.printf("DIAG receive=%d id=0x%03lX dlc=%d\n", e, (unsigned long)(e==ESP_OK ? r.identifier : 0), e==ESP_OK ? r.data_length_code : -1);
  Serial.println("DIAG FIN");
}
void loop() { delay(1000); }
