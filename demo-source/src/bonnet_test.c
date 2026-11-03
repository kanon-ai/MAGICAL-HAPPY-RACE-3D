#include <stdint.h>
#define U8(a) (*(volatile uint8_t *)(a))
#define RECT ((void (*)(int16_t,int16_t,uint16_t,uint16_t,uint8_t))0x86b6)
static const uint8_t paints[4]={20,142,210,74};
static const uint8_t highlights[4]={125,197,132,229};
void bonnet(void) {
 uint8_t p,h,c;
 if(U8(57921)!=1 || U8(60246))return;
 c=U8(51961)&3;p=paints[c];h=highlights[c];
 /* Fixed cockpit lip: eight scanlines, no camera or simulation changes. */
 RECT(82,162,92,1,12);
 RECT(76,163,104,1,h);
 RECT(70,164,116,2,p);
 RECT(64,166,128,4,p);
 RECT(70,166,2,3,h);
 RECT(184,166,2,3,h);
 RECT(79,164,2,2,h);
 RECT(175,164,2,2,h);
 RECT(64,169,128,1,12);
}
