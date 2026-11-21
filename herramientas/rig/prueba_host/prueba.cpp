#include "Arduino.h"
#include "driver/twai.h"
S_ Serial; uint32_t T_US=0; int PINS[40]; int DAC[40]; int ADC_MV=3120;
int MODO; std::deque<twai_message_t> RXQ; std::vector<twai_message_t> TXL;
#include "rig_body.inc"
static void rx(uint32_t id,std::vector<uint8_t> d){twai_message_t m={};m.identifier=id;m.data_length_code=d.size();for(size_t i=0;i<d.size();i++)m.data[i]=d[i];RXQ.push_back(m);}
static void corre(uint32_t ms){ for(uint32_t i=0;i<ms*2;i++){T_US+=500; loop();} }
static int fallos=0;
#define CHECK(c,msg) do{ bool ok=(c); printf("%s  %s\n", ok?"PASA ":"FALLA", msg); if(!ok) fallos++; }while(0)
static const twai_message_t* ult(uint32_t id){ for(int i=TXL.size()-1;i>=0;i--) if(TXL[i].identifier==id) return &TXL[i]; return nullptr; }
static float angDAC(){ // reconstruye el angulo del volante desde los DAC
  float v=(DAC[25]/255.0f*3.3f)*1.381f+0.131f - 2.47f, c=(DAC[26]/255.0f*3.3f)*1.386f+0.115f - 2.47f; return atan2f(c,v)*180/M_PI; }
int main(){
  PINS[32]=1; // boton de rearme suelto (pull-up)
  setup();
  CHECK(PINS[27]==LOW, "1 arranque: pie suelto");
  corre(50);
  CHECK(TXL.empty() && MODO==TWAI_MODE_LISTEN_ONLY, "2 sin armar: LISTEN_ONLY, no transmite nada");
  // latido con mando pero sin armar nada
  Serial.send("L y=100 x=0 b=0 n=0 s=0 e=0 w=0 r=0 th=0 pie=1\n"); corre(20);
  CHECK(PINS[27]==LOW, "3 latido con pie=1 SIN rearme: no pisa");
  Serial.send("R\n"); Serial.send("L y=100 x=0 b=0 n=0 s=0 e=0 w=0 r=0 th=0 pie=1\n"); corre(20);
  CHECK(PINS[27]==HIGH, "4 rearme + latido + pie=1: pisa");
  // armar CAN y la conversacion
  Serial.send("A\n"); corre(5);
  rx(0x701,{0}); for(int k=0;k<18;k++){ Serial.send("L y=0 x=0 b=0 n=0 s=0 e=0 w=0 r=0 th=0 pie=1\n"); corre(50);}
  bool bu=false; uint32_t tbu=0; for(auto&m:TXL) if(m.identifier==0x702 && m.data[0]==0x00){bu=true;}
  CHECK(bu, "5 CAN: boot-up 702 00 tras el grupo (~0.8 s)");
  bool hb=false; for(auto&m:TXL) if(m.identifier==0x702 && m.data[0]==0x7F) hb=true;
  CHECK(hb, "5b CAN: latido 702 7F en pre-operacional");
  rx(0x602,{0x40,0x00,0x10,0x00,0,0,0,0}); corre(5);
  const twai_message_t* s=ult(0x582); CHECK(s && s->data[0]==0x43, "6 CAN: contesta 0x1000 con 43");
  rx(0x000,{0x01,0x00}); Serial.send("L y=0 x=0 b=0 n=0 s=0 e=0 w=0 r=0 th=0 pie=1\n"); corre(5);
  // mantener latido cada 50 ms con mando y SYNCs
  for(int k=0;k<6;k++){ Serial.send("L y=100 x=-40 b=0 n=1 s=0 e=0 w=0 r=0 th=90 pie=1\n"); rx(0x080,{}); corre(50);}
  const twai_message_t* p=ult(0x182);
  CHECK(p && p->data[0]==100 && p->data[1]==40 && (p->data[4]&0x08) && (p->data[4]&0x04) && (p->data[5]&0x08) && p->data[7]==255, "7 CAN: 182 = adelante 100, izquierda 40, N");
  CHECK(PINS[27]==HIGH, "8 con latido: sigue pisando");
  float a0=angDAC(); CHECK(fabsf(a0)<3, "9 timon SIN armar (sin T): th=90 se ignora, queda en 0");
  Serial.send("T 0\n"); 
  for(int k=0;k<4;k++){ Serial.send("L y=100 x=-40 b=0 n=1 s=0 e=0 w=0 r=0 th=90 pie=1\n"); rx(0x080,{}); corre(50);}
  float a1=angDAC(); CHECK(a1>55 && a1<80, "10 timon armado: va hacia 90 con rampa (360/s → ~72 en 200 ms)");
  // CORTE DE LATIDO
  uint32_t t_ult=T_US; int soltado_ms=-1;
  for(int i=0;i<600;i++){ T_US+=500; loop(); if(i%40==0) rx(0x080,{}); if(soltado_ms<0 && PINS[27]==LOW) soltado_ms=(T_US-t_ult)/1000; }
  CHECK(soltado_ms>=150 && soltado_ms<=205, ("11 watchdog: pie suelta a los "+std::to_string(soltado_ms)+" ms (<=200)").c_str());
  rx(0x080,{}); corre(2); p=ult(0x182);
  bool cero=true; for(int i=0;i<8;i++) if(p->data[i]) cero=false;
  CHECK(cero, "12 watchdog: 182 todo en cero");
  float a2=angDAC(); corre(300); float a3=angDAC();
  CHECK(fabsf(a3-a2)<2, "13 watchdog: el timon se queda quieto (no salta a 0 ni sigue)");
  float a4=angDAC();
  for(int k=0;k<4;k++){ Serial.send("L y=100 x=0 b=0 n=0 s=0 e=0 w=0 r=0 th=-90 pie=1\n"); rx(0x080,{}); corre(50);}
  CHECK(PINS[27]==LOW, "14 vuelve el latido: el pie NO re-pisa solo");
  p=ult(0x182); cero=true; for(int i=0;i<8;i++) if(p->data[i]) cero=false;
  CHECK(cero, "14b vuelve el latido sin rearme: el 182 SIGUE en cero aunque se pida y=100");
  CHECK(fabsf(angDAC()-a4)<2, "14c vuelve el latido sin rearme: el timon NO sigue a th=-90");
  Serial.send("R\n"); Serial.send("L y=0 x=0 b=0 n=0 s=0 e=0 w=0 r=0 th=0 pie=1\n"); corre(20);
  CHECK(PINS[27]==HIGH, "15 rearme con latido: pisa");
  for(int k=0;k<2;k++){ Serial.send("L y=50 x=0 b=0 n=0 s=0 e=0 w=0 r=0 th=0 pie=1\n"); rx(0x080,{}); corre(50);}
  p=ult(0x182); CHECK(p->data[0]==50 && (p->data[4]&0x08), "15b despues del rearme el 182 vuelve a mandar (y=50)");
  ADC_MV=140; Serial.send("L y=0 x=0 b=0 n=0 s=0 e=0 w=0 r=0 th=0 pie=1\n"); corre(20);
  CHECK(PINS[27]==LOW, "16 paro (modulos sin 5 V): suelta");
  for(int k=0;k<2;k++){ Serial.send("L y=50 x=0 b=0 n=0 s=0 e=0 w=0 r=0 th=0 pie=1\n"); rx(0x080,{}); corre(50);}
  p=ult(0x182); cero=true; for(int i=0;i<8;i++) if(p->data[i]) cero=false;
  CHECK(cero, "16b paro: el 182 tambien va a cero (la hidraulica no sigue)");
  ADC_MV=3120; Serial.send("L y=0 x=0 b=0 n=0 s=0 e=0 w=0 r=0 th=0 pie=1\n"); corre(20);
  CHECK(PINS[27]==LOW, "17 paro liberado: sigue suelto hasta el rearme");
  Serial.send("X\n"); size_t n=TXL.size(); rx(0x080,{}); corre(300);
  CHECK(TXL.size()==n && MODO==TWAI_MODE_LISTEN_ONLY, "18 X: silencio, no transmite mas");
  printf("\n%s (%d fallos)\n", fallos? "FALLA":"TODO PASA", fallos);
  return fallos;
}
