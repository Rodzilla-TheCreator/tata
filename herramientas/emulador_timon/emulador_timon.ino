/*
  Emulador del sensor del volante (direccion) — ESP32, primera version (DAC nativo 8-bit)
  Ver herramientas/emulador_timon/LEEME.md y armado_emulador.svg para el circuito.

  Params de banco (24-oct): Vo=2.47, Va=1.98.   verde=Vo+Va*cos(th)   cafe=Vo+Va*sin(th)
  Etapa op-amp: ganancia G=1.36 (DAC 0-3.3V -> 0-4.49V), alimentada a 5V (clamp inherente).
  node 4 deriva VELOCIDAD del cambio de theta -> para girar, theta debe BARRER (quieto = recto).

  SIN RELE: el emulador va DIRECTO a node 4; el sensor real se desconecta.
  Entrada:  pote GPIO34 = velocidad de giro (centro = quieto).   [en el kit: Jetson/gamepad]
  Salidas:  DAC GPIO25 (verde), GPIO26 (cafe)  -> etapa op-amp -> conector de node 4.

  SEGURIDAD: equipo en gato / parado, paro en mano. Sin handoff automatico: si el ESP se
  cuelga, node 4 lee una senal invalida y deshabilita la direccion (seguro en parado).
  Validar contra el caracterizador (mismo circulo) ANTES de conectar a node 4.
*/
#include <math.h>

const float Vo = 2.47, Va = 1.98;   // medidos en banco (24-oct)
const float G  = 1.36;              // ganancia de la etapa op-amp (afinar con trimpot + caracterizador)
const int POT = 34, DAC_V = 25, DAC_C = 26;

float theta = 0;
float maxRate = 6.283;              // rad/s a fondo de pote (~1 vuelta/s); ajustar en campo
unsigned long tPrev;

int aDac(float out){                // volts deseados en el pin -> codigo DAC 8-bit (inverso de G)
  float v = out / G;
  if(v < 0) v = 0; if(v > 3.3) v = 3.3;
  return (int)(v/3.3*255.0 + 0.5);
}

void setup(){
  Serial.begin(115200);
  analogReadResolution(12);
  dacWrite(DAC_V, aDac(Vo + Va)); dacWrite(DAC_C, aDac(Vo));  // arranca en un punto valido del circulo
  tPrev = micros();
  Serial.println("Emulador del timon listo (directo a node 4, sin rele).");
}

void loop(){
  unsigned long t = micros(); float dt = (t - tPrev)/1e6; tPrev = t;

  float rate = ((analogRead(POT) - 2048)/2048.0) * maxRate;   // centro = 0
  if(fabs(rate) < 0.05*maxRate) rate = 0;                     // zona muerta

  theta += rate * dt;
  if(theta > 6.28318) theta -= 6.28318;
  if(theta < 0)       theta += 6.28318;

  float verde = Vo + Va*cos(theta);
  float cafe  = Vo + Va*sin(theta);
  dacWrite(DAC_V, aDac(verde));
  dacWrite(DAC_C, aDac(cafe));

  static unsigned long tp = 0;
  if(millis() - tp > 100){ tp = millis();
    Serial.print("theta="); Serial.print(theta*57.2958,1);
    Serial.print(" rate=");  Serial.print(rate,2);
    Serial.print(" verde="); Serial.print(verde,3);
    Serial.print(" cafe=");  Serial.println(cafe,3);
  }
  delayMicroseconds(500);
}
