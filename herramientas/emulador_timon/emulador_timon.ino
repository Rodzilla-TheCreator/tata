/*
  Emulador del sensor del volante (direccion) — ESP32, version LM358 (DAC nativo 8-bit)
  Ver herramientas/emulador_timon/LEEME.md y armado_emulador.svg.

  Objetivo (lo que daba el sensor real): Vo=2.47 V, Va=1.98 V.
    verde = Vo + Va*cos(theta)      cafe = Vo + Va*sin(theta)
  node 4 deriva VELOCIDAD del cambio de theta -> para girar, theta BARRE (quieto = recto).

  CALIBRACION: la etapa (DAC nativo + op-amp LM358, Rg=10k Rf=5.1k, Vcc=+11V) es lineal:
      salida = k*Vdac + o
  Para sacar un voltaje D en el pin se invierte:  Vdac = (D - o) / k.
  Esto corrige ganancia Y centro (el DAC nativo mete un offset ~0.13V que la ganancia sola
  no arregla). Los k/o se miden UNA vez con el caracterizador y van abajo. Re-medir si se
  cambian resistencias o el ESP.

  CONTROLADO POR EL ESP (sin pote). Dos modos por SERIAL:
    - VELOCIDAD: un numero = grados/seg (con signo). 0 = recto.   ej. "90", "-45", "0"
    - POSICION : "P<grados>" = angulo absoluto. Lo usa la GUI rueda_timon.py.  ej. "P30", "P-120"
    [en el kit la velocidad la pone la Jetson/gamepad por el mismo canal]

  Salidas: DAC GPIO25 (verde), GPIO26 (cafe) -> etapa op-amp -> conector node 4.
  SEGURIDAD: equipo parado/en gato, paro en mano. Validar contra el caracterizador antes de node 4.
*/
#include <math.h>

const float Vo = 2.47, Va = 1.98;   // objetivo (sensor real, 24-oct)

// CALIBRACION POR CANAL (medida con el caracterizador, 26-oct): salida = k*Vdac + o
const float kV = 1.381, oV = 0.131; // verde (GPIO25)
const float kC = 1.386, oC = 0.115; // cafe  (GPIO26)

const int DAC_V = 25, DAC_C = 26;

float theta = 0;                    // rad
float rate  = 0;                    // rad/s (comandado por serial)
unsigned long tPrev;
String buf = "";

int code(float vdac){               // voltaje DAC deseado (0-3.3V) -> codigo 8-bit
  if(vdac < 0) vdac = 0; if(vdac > 3.3) vdac = 3.3;
  return (int)(vdac/3.3*255.0 + 0.5);
}
void sacar(float verde, float cafe){               // escribe los dos DAC con su calibracion
  dacWrite(DAC_V, code((verde - oV)/kV));
  dacWrite(DAC_C, code((cafe  - oC)/kC));
}

void setup(){
  Serial.begin(115200);
  sacar(Vo + Va, Vo);               // arranca en un punto valido del circulo (theta=0)
  tPrev = micros();
  Serial.println("Emulador LM358 listo. Numero = vel (deg/s), o 'P<grados>' = posicion.");
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
  sacar(verde, cafe);

  static unsigned long tp = 0;
  if(millis() - tp > 200){ tp = millis();
    Serial.print("theta="); Serial.print(theta*57.2958,1);
    Serial.print(" verde="); Serial.print(verde,3);
    Serial.print(" cafe=");  Serial.println(cafe,3);
  }
  delayMicroseconds(500);
}
