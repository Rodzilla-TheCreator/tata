// pedal_n.ino — banco: la tecla n alterna el pedal de hombre muerto (GPIO27 -> IN de los modulos).
// Sin watchdog: solo para probar el emulador en el escritorio, nunca en el montacargas.
const int PIN_PIE = 27;
bool pisado = false;

void setup() {
  pinMode(PIN_PIE, OUTPUT);
  digitalWrite(PIN_PIE, LOW);   // arranca suelto
  Serial.begin(115200);
  Serial.println("Pedal SUELTO. Apreta n para alternar.");
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    if (c == 'n' || c == 'N') {
      pisado = !pisado;
      digitalWrite(PIN_PIE, pisado ? HIGH : LOW);
      Serial.println(pisado ? "Pedal PISADO (blanco ~12 V, negro ~0)" : "Pedal SUELTO (blanco ~0, negro ~12 V)");
    }
  }
}
