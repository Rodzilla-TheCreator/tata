/*
  Emulador del sensor del volante (direccion) — ESP32, version LM358 (DAC nativo 8-bit)
  Ver herramientas/emulador_timon/LEEME.md y armado_emulador.svg.

  Params de banco (24-oct): Vo=2.47, Va=1.98.  verde=Vo+Va*cos(th)  cafe=Vo+Va*sin(th)
  Etapa op-amp LM358: G=1.51 (DAC 0-3.3V -> 0-4.5V), Vcc=+11V del blanco, clamp R100+zener.
  node 4 deriva VELOCIDAD del cambio de theta -> para girar, theta BARRE (quieto = recto).

  CONTROLADO POR EL ESP (sin pote). Dos modos por SERIAL:
    - VELOCIDAD: un numero = grados/seg (con signo). 0 = recto.   ej. "90", "-45", "0"
    - POSICION : "P<grados>" = angulo absoluto. Lo usa la GUI rueda_timon.py.  ej. "P30", "P-120"
    [en el kit la velocidad la pone la Jetson/gamepad por el mismo canal]

  Salidas: DAC GPIO25 (verde), GPIO26 (cafe) -> etapa op-amp -> conector node 4.
  SEGURIDAD: equipo parado/en gato, paro en mano. Validar contra el caracterizador antes de node 4.
*/
#include <math.h>

const float Vo = 2.47, Va = 1.98;   // medidos en banco (24-oct)
// Ganancia POR CANAL (G = 1 + Rf/Rg). Mismos resistores en ambos: Rg=10k, Rf=5.1k -> G=1.51.
// AJUSTAR cada uno con el caracterizador hasta que el circulo de radio ~1.95 / nrad ~1.
const float G_V = 1.51;             // ganancia canal verde  (Rg=10k, Rf=5.1k)
const float G_C = 1.51;             // ganancia canal cafe   (Rg=10k, Rf=5.1k)
const int DAC_V = 25, DAC_C = 26;

float theta = 0;                    // rad
float rate  = 0;                    // rad/s (comandado por serial)
unsigned long tPrev;
String buf = "";

int aDac(float out, float G){       // volts deseados en el pin -> codigo DAC 8-bit (inverso de G)
  float v = out / G;
  if(v < 0) v = 0; if(v > 3.3) v = 3.3;
  return (int)(v/3.3*255.0 + 0.5);
}

void setup(){
  Serial.begin(115200);
  dacWrite(DAC_V, aDac(Vo + Va, G_V)); dacWrite(DAC_C, aDac(Vo, G_C));  // arranca en un punto valido del circulo
  tPrev = micros();
  Serial.println("Emulador LM358 listo. Escribi velocidad en deg/s (+/-). 0 = parar.");
}

void loop(){
  while(Serial.available()){
    char c = Serial.read();
    if(c=='\n' || c=='\r'){
      if(buf.length()){
        if(buf[0]=='P' || buf[0]=='p'){            // POSICION: angulo absoluto en grados
          theta = buf.substring(1).toFloat() * PI / 180.0;
          while(theta > 6.28318) theta -= 6.28318;
          while(theta < 0)       theta += 6.28318;
          rate = 0;                                // modo posicion: no acumula
        } else {                                   // VELOCIDAD: grados/seg
          rate = buf.toFloat() * PI / 180.0;
        }
        buf = "";
      }
    } else buf += c;
  }

  unsigned long t = micros(); float dt = (t - tPrev)/1e6; tPrev = t;
  theta += rate * dt;
  if(theta > 6.28318) theta -= 6.28318;
  if(theta < 0)       theta += 6.28318;

  float verde = Vo + Va*cos(theta);
  float cafe  = Vo + Va*sin(theta);
  dacWrite(DAC_V, aDac(verde, G_V));
  dacWrite(DAC_C, aDac(cafe, G_C));

  static unsigned long tp = 0;
  if(millis() - tp > 200){ tp = millis();
    Serial.print("theta="); Serial.print(theta*57.2958,1);
    Serial.print(" verde="); Serial.print(verde,3);
    Serial.print(" cafe=");  Serial.println(cafe,3);
  }
  delayMicroseconds(500);
}
