// Pulsos cortos en TX (GPIO21) y lectura de RX (GPIO22) DURANTE el pulso.
// Más corto que el time-out de dominante del TJA1050 (~0.3–1 ms).
#define TX 21
#define RX 22
void setup() {
  Serial.begin(115200); delay(700);
  pinMode(TX, OUTPUT); pinMode(RX, INPUT); digitalWrite(TX, HIGH);
  for (int us : {4, 10, 20, 50}) {
    int bajo_en_pulso = 0, alto_en_reposo = 0;
    for (int i = 0; i < 200; i++) {
      digitalWrite(TX, LOW);  delayMicroseconds(us);
      bajo_en_pulso += (digitalRead(RX) == 0);
      digitalWrite(TX, HIGH); delayMicroseconds(200);
      alto_en_reposo += (digitalRead(RX) == 1);
    }
    Serial.printf("PULSO %2d us: RX bajo durante el pulso %3d/200 · RX alto en reposo %3d/200\n",
                  us, bajo_en_pulso, alto_en_reposo);
  }
  Serial.println("PULSO FIN");
}
void loop() { delay(1000); }
