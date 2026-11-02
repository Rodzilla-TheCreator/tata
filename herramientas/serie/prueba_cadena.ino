/* ──────────────────────────────────────────────────────────────────────────
   TaTa · NIVEL 1 — prueba de cadena
   ESP32-U  +  módulo T132 (SP3232, RS-232 ⇄ TTL)

   QUÉ VALIDA
     · el módulo T132 en las dos direcciones
     · tu cableado y los GPIO del ESP32
     · el conector DB9 del módulo
     · resuelve solo si las etiquetas TX/RX estaban al revés

   CABLEADO
     T132 GND → ESP32 GND
     T132 VCC → ESP32 3V3       (3.3 V, nunca 5 V)
     T132 TX  → ESP32 GPIO16
     T132 RX  → ESP32 GPIO17

   ANTES DE CORRER
     Puente entre el PIN 2 y el PIN 3 del DB9 del T132.
     Es un MACHO: el pin 1 va arriba a la IZQUIERDA, así que el 2 y el 3
     son el segundo y el tercero de la fila de arriba desde la izquierda.

   Monitor Serie a 115200.
   ────────────────────────────────────────────────────────────────────────── */

#include <Arduino.h>

#define GPIO_A  16          // a donde va el TX del T132
#define GPIO_B  17          // a donde va el RX del T132

const char* PATRON = "TATA-LOOPBACK-0123456789-abcdef\r\n";

struct Caso { long baud; uint32_t cfg; const char* nom; };
const Caso CASOS[] = {
  {  1200, SERIAL_8N1, "8N1" },
  {  9600, SERIAL_8N1, "8N1" },
  { 38400, SERIAL_8N1, "8N1" },
  {115200, SERIAL_8N1, "8N1" },
  {  9600, SERIAL_8E1, "8E1" },
  {  9600, SERIAL_7E1, "7E1" },
};
const int N = sizeof(CASOS) / sizeof(CASOS[0]);

// Devuelve cuantos casos dieron eco perfecto con esa orientacion de pines.
int corrida(int pinRx, int pinTx, bool imprimir) {
  int ok = 0;
  for (int i = 0; i < N; i++) {
    Serial2.begin(CASOS[i].baud, CASOS[i].cfg, pinRx, pinTx);
    delay(60);
    while (Serial2.available()) Serial2.read();

    Serial2.print(PATRON);
    Serial2.flush();

    String eco = "";
    uint32_t t0 = millis();
    while (millis() - t0 < 900 && eco.length() < strlen(PATRON)) {
      while (Serial2.available()) eco += (char)Serial2.read();
      delay(2);
    }
    Serial2.end();

    bool perfecto = (eco == String(PATRON));
    if (perfecto) ok++;

    if (imprimir) {
      Serial.printf("   %7ld  %-4s : ", CASOS[i].baud, CASOS[i].nom);
      if (perfecto)            Serial.printf("OK        %d/%d bytes idénticos\n",
                                             eco.length(), strlen(PATRON));
      else if (eco.length())   Serial.printf("CORRUPTO  volvieron %d bytes\n",
                                             eco.length());
      else                     Serial.println("SIN ECO   no volvió nada");
    }
    delay(250);
  }
  return ok;
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println("\n\n==========================================");
  Serial.println("  TaTa · NIVEL 1 — PRUEBA DE CADENA");
  Serial.println("  jumper entre pin 2 y pin 3 del T132");
  Serial.println("==========================================\n");
}

void loop() {
  Serial.printf("── cableado normal  (RX=GPIO%d  TX=GPIO%d) ──\n", GPIO_A, GPIO_B);
  int a = corrida(GPIO_A, GPIO_B, true);

  int b = 0;
  if (a == 0) {
    Serial.printf("\n── probando al revés (RX=GPIO%d  TX=GPIO%d) ──\n", GPIO_B, GPIO_A);
    b = corrida(GPIO_B, GPIO_A, true);
  }

  Serial.println("\n==========================================");
  if (a > 0) {
    Serial.printf("  LA CADENA SIRVE — %d de %d casos con eco perfecto\n", a, N);
    Serial.println("  Cableado correcto tal como está.");
    Serial.println("  Módulo, GPIOs y conector DB9: todos buenos.");
  } else if (b > 0) {
    Serial.printf("  LA CADENA SIRVE — %d de %d, pero AL REVÉS\n", b, N);
    Serial.println();
    Serial.printf("  Intercambiá los cables: T132 TX → GPIO%d\n", GPIO_B);
    Serial.printf("                          T132 RX → GPIO%d\n", GPIO_A);
    Serial.println("  O invertí GPIO_A y GPIO_B arriba en el código.");
  } else {
    Serial.println("  NO PASA NADA EN NINGUNA ORIENTACIÓN");
    Serial.println();
    Serial.println("  Revisá, en este orden:");
    Serial.println("   1. el jumper está entre el pin 2 y el 3 del DB9 del T132");
    Serial.println("      (macho: pin 1 arriba a la IZQUIERDA)");
    Serial.println("   2. T132 VCC llega a 3V3 y GND a GND");
    Serial.println("   3. los jumpers hacen contacto en el protoboard");
    Serial.println("   4. no estás usando los pines TX/RX del ESP32 (GPIO1/3)");
  }
  Serial.println("==========================================");
  Serial.println("  repite en 6 s — movele el jumper y mirá\n");
  delay(6000);
}
