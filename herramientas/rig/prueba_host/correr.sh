#!/bin/sh
# Prueba de la LÓGICA de rig.ino en la compu (Linux/maquinon), con el ESP32 imitado: tiempo, serie,
# DAC, GPIO y TWAI falsos. No reemplaza al banco: prueba que el código hace lo que dice antes de cargarlo.
#   sh herramientas/rig/prueba_host/correr.sh            → tiene que decir TODO PASA
#   sh herramientas/rig/prueba_host/correr.sh control    → con WATCHDOG_MS = 5000: tiene que FALLAR (11, 12, 14)
cd "$(dirname "$0")"
sed -e 's/#include "driver\/twai.h"//' -e 's/#include <esp_task_wdt.h>/#include "esp_task_wdt.h"/' ../rig/rig.ino > rig_body.inc
[ "$1" = "control" ] && sed -i 's/#define WATCHDOG_MS      200 /#define WATCHDOG_MS      5000/' rig_body.inc
g++ -std=gnu++17 -I. -o /tmp/prueba_rig prueba.cpp && /tmp/prueba_rig
