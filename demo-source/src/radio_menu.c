#include <stdint.h>
#define U8(a) (*(volatile uint8_t *)(a))
#define RECT ((void (*)(int16_t,int16_t,uint16_t,uint16_t,uint8_t))0x86b6)
#define TEXT ((void (*)(int16_t,int16_t,const char *))0x888d)
void radio_menu(void) {
 uint8_t c;
 if(U8(57921)!=0)return;
 c=U8(51961)&3;
 RECT(20,60,216,78,12);
 TEXT(38,63,"RADIO: 1 / 2 / 3");
 RECT(36+36*U8(0xdff0),75,30,10,3);
 TEXT(38,76,"BGM1  BGM2  BGM3");
 TEXT(38,94,"COLOR: 5 / 6 / 7 / 8");
 TEXT(38,106,c==0?"BLACK":c==1?"RED":c==2?"BLUE":"YELLOW");
 TEXT(38,123,"SPACE: START");
}
