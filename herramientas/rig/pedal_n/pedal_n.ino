// pedal_n.ino — banco: la tecla n alterna el pedal de hombre muerto (GPIO27 -> IN de los modulos).
// Lee el paro: GPIO35 mide el VCC de los modulos (despues del paro) con un divisor 10k / 20k.
// Si el paro corta, el pedal queda SUELTO y no vuelve a pisar solo: hay que apretar n otra vez.
// Sin watchdog: solo para probar el emulador en el escritorio, nunca en el montacargas.
const int PIN_PIE  = 27;
const int PIN_PARO = 35;   // solo entrada; alto = los modulos tienen 5 V. En el banco el pulsador es NA (apretado = 5 V); en el montacargas el hongo es NC (apretado = corta)

bool pisado = false;
bool paroOk = false;
uint32_t tCambio = 0;

// Lectura analogica con histeresis: CON 5 V arriba de 2000 mV, SIN 5 V abajo de 1200 mV.
// Con 5 V el divisor da ~3300 mV; sin 5 V, ~0.
int mvParo = 0;
bool leeParo() {
  mvParo = analogReadMilliVolts(PIN_PARO);
  if (mvParo > 2000) return true;
  if (mvParo < 1200) return false;
  return paroOk;   // zona muerta: se queda como estaba
}

void setup() {
  pinMode(PIN_PIE, OUTPUT);
  digitalWrite(PIN_PIE, LOW);   // arranca suelto
  pinMode(PIN_PARO, INPUT);
  Serial.begin(115200);
  paroOk = leeParo();
  Serial.printf("Pedal SUELTO. %s (GPIO35 = %d mV). Apreta n para alternar.\n",
                paroOk ? "modulos CON 5 V" : "modulos SIN 5 V (cortado)", analogReadMilliVolts(PIN_PARO));
}

void loop() {
  bool ahora = leeParo();
  if (ahora != paroOk) {
    if (tCambio == 0) tCambio = millis();
    if (millis() - tCambio >= 20) {          // 20 ms estable para creerle
      paroOk = ahora;
      tCambio = 0;
      if (!paroOk) {
        bool estaba = pisado;
        pisado = false;
        digitalWrite(PIN_PIE, LOW);
        Serial.printf(estaba ? "CORTE (%d mV): modulos SIN 5 V -> pedal SUELTO. No vuelve a pisar solo.\n"
                             : "CORTE (%d mV): modulos SIN 5 V.\n", mvParo);
      } else {
        Serial.printf("5 V DE VUELTA (%d mV). El pedal sigue SUELTO; apreta n para pisar.\n", mvParo);
      }
    }
  } else {
    tCambio = 0;
  }

  if (Serial.available()) {
    char c = Serial.read();
    if (c == 'v' || c == 'V') {
      Serial.printf("GPIO35 = %d mV -> modulos %s, pedal %s\n", mvParo, paroOk ? "CON 5 V" : "SIN 5 V",
                    pisado ? "PISADO" : "SUELTO");
    }
    if (c == 'n' || c == 'N') {
      if (!pisado && !paroOk) {
        Serial.println("Modulos SIN 5 V: no se puede pisar.");
      } else {
        pisado = !pisado;
        digitalWrite(PIN_PIE, pisado ? HIGH : LOW);
        Serial.println(pisado ? "Pedal PISADO (blanco ~12 V, negro ~0)" : "Pedal SUELTO (blanco ~0, negro ~12 V)");
      }
    }
  }
}
