#include <stdint.h>
#define U8(a) (*(volatile uint8_t *)(a))
#define RECT ((void (*)(int16_t,int16_t,uint16_t,uint16_t,uint8_t))0x86b6)
static const uint8_t paints[4]={20,142,210,74};
static const uint8_t highlights[4]={125,197,132,229};
void bonnet(void) {
 uint8_t p,h,c;
 if(U8(57921)!=1 || U8(60246))return;
 c=U8(51961)&3;p=paints[c];h=highlights[c];
 /* Bonnet remains entirely above dashboard row168. */
 RECT(32,159,192,1,h);
 RECT(16,160,224,2,p);
 RECT(0,162,256,5,p);
 RECT(32,161,2,4,h);
 RECT(222,161,2,4,h);
 RECT(0,167,256,1,12);
}
