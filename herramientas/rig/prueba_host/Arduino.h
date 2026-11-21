#pragma once
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include <math.h>
#include <string>
#include <deque>
#define HIGH 1
#define LOW 0
#define OUTPUT 1
#define INPUT 0
#define INPUT_PULLUP 2
template<class T,class L,class H> T constrain(T x,L a,H b){return x<a?a:(x>b?b:x);}
struct S_{ std::deque<char> in; std::string out;
 void begin(long){} int available(){return in.size();} int read(){char c=in.front();in.pop_front();return c;} void flush(){}
 int printf(const char*f,...) __attribute__((format(printf,2,3))) {char b[512];va_list a;va_start(a,f);vsnprintf(b,512,f,a);va_end(a);out+=b;return 0;}
 void println(const char*s=""){out+=s;out+="\n";} void print(const char*s){out+=s;}
 void send(const char*s){while(*s)in.push_back(*s++);} };
extern S_ Serial;
extern uint32_t T_US; extern int PINS[40]; extern int DAC[40]; extern int ADC_MV;
inline void pinMode(int,int){} inline void digitalWrite(int p,int v){PINS[p]=v;} inline int digitalRead(int p){return PINS[p];}
inline uint32_t millis(){return T_US/1000;} inline uint32_t micros(){return T_US;}
inline void dacWrite(int p,int v){DAC[p]=v;} inline int analogReadMilliVolts(int){return ADC_MV;}
#define ESP_OK 0
