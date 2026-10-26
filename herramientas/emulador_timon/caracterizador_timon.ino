/*
  Caracterizador del sensor del volante — Arduino Uno/Nano
  Ver herramientas/emulador_timon/LEEME.md. Saca los parametros del emulador.

  Sensor con 12 V de fuente (blanco=+, amarillo=GND).  verde->A0,  cafe/rojo->A1.
  Tierra comun: amarillo + fuente(-) + GND Arduino.  NUNCA blanco a un pin.
  Terminal con soporte \r: CoolTerm / PuTTY / screen.

  PROCEDIMIENTO:
    1) 'r' reset.
    2) Gira LENTO cubriendo el circulo completo (>=1 vuelta; cualquier sentido/patron sirve).
    3) 'c' imprime el resumen: Vo/Va por canal, radio, veredicto cuadratura.
    4) 'l' activa/desactiva el LOG CSV (capturar con "capture to file" del terminal).
       Columnas: ms,verde,cafe,ang,radio,nrad

  El modelo es seno/coseno:  verde = Vo + Va*cos(th)   cafe = Vo + Va*sin(th)
  Invariante = RADIO (no la suma). El radio normalizado debe quedar ~1.000 plano.
*/
const float VREF = 5.0;
const float DEG  = 57.29578;

float gmin=5, gmax=0, rmin=5, rmax=0;         // se aprenden girando (sin semilla: miden lo real)
float radMin=1e9, radMax=-1e9, radSum=0; long radN=0;
float nradMin=1e9, nradMax=-1e9;
float angPrev=0; long vueltas=0; bool primera=true;
bool  logging=false;

float leer(int pin){
  analogRead(pin); delayMicroseconds(200);    // descarte: asienta el mux del ADC (anti-ghosting)
  long s=0; for(int i=0;i<8;i++){ s+=analogRead(pin); delayMicroseconds(200);}
  return (s/8.0)*VREF/1023.0;
}

void menu(){
  Serial.println(); Serial.println(F("=== Caracterizador sensor volante (seno/coseno) ==="));
  Serial.println(F("1) 'r' reset  2) gira LENTO cubriendo el circulo completo"));
  Serial.println(F("3) 'c' resumen (Vo/Va, radio, veredicto)  4) 'l' log CSV on/off"));
  Serial.println(F("------------------------------------------------"));
}

void resumen(){
  float Vog=(gmin+gmax)/2, Vag=(gmax-gmin)/2;
  float Voc=(rmin+rmax)/2, Vac=(rmax-rmin)/2;
  float radMean = radN? radSum/radN : 0;
  Serial.println(); Serial.println(F("===== RESUMEN DE CALIBRACION ====="));
  Serial.print(F("VERDE  min=")); Serial.print(gmin,3); Serial.print(F(" max=")); Serial.print(gmax,3);
  Serial.print(F("  Vo=")); Serial.print(Vog,3); Serial.print(F("  Va=")); Serial.println(Vag,3);
  Serial.print(F("CAFE   min=")); Serial.print(rmin,3); Serial.print(F(" max=")); Serial.print(rmax,3);
  Serial.print(F("  Vo=")); Serial.print(Voc,3); Serial.print(F("  Va=")); Serial.println(Vac,3);
  Serial.print(F("RADIO  min=")); Serial.print(radMin,3); Serial.print(F(" max=")); Serial.print(radMax,3);
  Serial.print(F(" mean=")); Serial.println(radMean,3);
  Serial.print(F("RADIO NORMALIZADO  min=")); Serial.print(nradMin,3);
  Serial.print(F(" max=")); Serial.print(nradMax,3);
  Serial.print(F("  (ideal=1.000, var=")); Serial.print((nradMax-nradMin)*100,1); Serial.println(F("%)"));
  Serial.print(F("Vueltas calibradas: ")); Serial.println(vueltas);
  Serial.println(F("(ignora radMin/nradMin=0.000 del arranque, antes de girar)"));
  Serial.println(F("Si Va_g ~ Va_c y nrad ~1 plano -> cuadratura limpia (circulo)."));
  Serial.println(F("PARA EL EMULADOR:  verde=Vo_g+Va_g*cos(th)   cafe=Vo_c+Va_c*sin(th)"));
  Serial.println(F("=================================="));
}

void reset(){
  gmin=5; gmax=0; rmin=5; rmax=0;
  radMin=1e9; radMax=-1e9; radSum=0; radN=0; nradMin=1e9; nradMax=-1e9;
  vueltas=0; primera=true;
  Serial.println(); Serial.println(F(">> RESET - gira cubriendo el circulo, luego 'c'"));
}

void setup(){ Serial.begin(115200); menu(); }

void loop(){
  while(Serial.available()){ char c=Serial.read();
    if(c=='r'||c=='R')reset();
    else if(c=='c'||c=='C')resumen();
    else if(c=='m'||c=='M')menu();
    else if(c=='l'||c=='L'){ logging=!logging;
      if(logging){ Serial.println(); Serial.println(F("ms,verde,cafe,ang,radio,nrad")); }
      else { Serial.println(); Serial.println(F(">> log OFF")); } }
  }

  float vg=leer(A0), vr=leer(A1);
  if(vg<gmin)gmin=vg; if(vg>gmax)gmax=vg;
  if(vr<rmin)rmin=vr; if(vr>rmax)rmax=vr;

  float Vog=(gmin+gmax)/2, Vag=(gmax-gmin)/2;
  float Voc=(rmin+rmax)/2, Vac=(rmax-rmin)/2;
  float x=vg-Vog, y=vr-Voc;
  float ang=atan2(y,x)*DEG; if(ang<0)ang+=360;
  float radio=sqrt(x*x+y*y);
  float nrad=0;
  if(Vag>0.1 && Vac>0.1) nrad=sqrt((x/Vag)*(x/Vag)+(y/Vac)*(y/Vac));

  if(radio<radMin)radMin=radio; if(radio>radMax)radMax=radio;
  radSum+=radio; radN++;
  if(nrad<nradMin)nradMin=nrad; if(nrad>nradMax)nradMax=nrad;

  if(!primera){ float d=ang-angPrev;
    if(d>180)vueltas--; else if(d<-180)vueltas++; }
  angPrev=ang; primera=false;

  if(logging){
    Serial.print(millis()); Serial.print(',');
    Serial.print(vg,3); Serial.print(',');
    Serial.print(vr,3); Serial.print(',');
    Serial.print(ang,1); Serial.print(',');
    Serial.print(radio,3); Serial.print(',');
    Serial.println(nrad,3);
  } else {
    Serial.print('\r');
    Serial.print(F("verde=")); Serial.print(vg,3);
    Serial.print(F(" cafe="));  Serial.print(vr,3);
    Serial.print(F(" ang="));   Serial.print(ang,1);
    Serial.print(F(" radio=")); Serial.print(radio,3);
    Serial.print(F(" vuelt="));Serial.print(vueltas);
    Serial.print(F("   "));
  }
  delay(30);
}
