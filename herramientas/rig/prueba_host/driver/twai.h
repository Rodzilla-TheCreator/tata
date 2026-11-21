#pragma once
#include <stdint.h>
#include <vector>
#include <deque>
#define GPIO_NUM_22 22
#define GPIO_NUM_21 21
typedef enum {TWAI_MODE_NORMAL,TWAI_MODE_NO_ACK,TWAI_MODE_LISTEN_ONLY} twai_mode_t;
typedef enum {TWAI_STATE_STOPPED,TWAI_STATE_RUNNING,TWAI_STATE_BUS_OFF,TWAI_STATE_RECOVERING} twai_state_t;
typedef struct { uint32_t identifier; uint8_t data_length_code; uint8_t data[8]; uint32_t flags;} twai_message_t;
typedef struct { int x; } twai_timing_config_t;
typedef struct { int y; } twai_filter_config_t;
typedef struct { int mode; int tx_io; int rx_io; uint32_t rx_queue_len; uint32_t tx_queue_len; } twai_general_config_t;
typedef struct { twai_state_t state; uint32_t msgs_to_tx, msgs_to_rx, tx_error_counter, rx_error_counter; } twai_status_info_t;
#define TWAI_TIMING_CONFIG_250KBITS() {0}
#define TWAI_FILTER_CONFIG_ACCEPT_ALL() {0}
#define TWAI_GENERAL_CONFIG_DEFAULT(tx,rx,m) {m,tx,rx,5,5}
#define pdMS_TO_TICKS(x) (x)
extern int MODO; extern std::deque<twai_message_t> RXQ; extern std::vector<twai_message_t> TXL;
inline int twai_driver_install(const twai_general_config_t*g,const twai_timing_config_t*,const twai_filter_config_t*){MODO=g->mode;return 0;}
inline int twai_start(){return 0;} inline int twai_stop(){return 0;} inline int twai_driver_uninstall(){return 0;}
inline int twai_transmit(const twai_message_t*m,uint32_t){ if(MODO!=TWAI_MODE_NORMAL) return 1; TXL.push_back(*m); return 0;}
inline int twai_receive(twai_message_t*m,uint32_t){ if(RXQ.empty()) return 1; *m=RXQ.front(); RXQ.pop_front(); return 0;}
inline int twai_get_status_info(twai_status_info_t*s){ s->state=TWAI_STATE_RUNNING; s->tx_error_counter=0; s->rx_error_counter=0; s->msgs_to_tx=0; return 0;}
