#include <stdint.h>
#define U8(a) (*(volatile uint8_t *)(a))
#define U16(a) (*(volatile uint16_t *)(a))
#define TEXT ((void (*)(int16_t,int16_t,const char *))0x888d)
#define RECT ((void (*)(int16_t,int16_t,uint16_t,uint16_t,uint8_t))0x86b6)
void crash_hud(void){
 uint8_t phase,age,i;int16_t cx,cy,x,y;
 if(U8(57921)!=1||U8(0x3fd8)!=0xc7)return;
 phase=U16(57950)&7;
 if(U8(0x3fd9))TEXT(92,38,"RECOVERING");
 else if(U8(0x3fda)&&phase<5)TEXT(116,38,"GO!");
 if(U8(0x3fdc)==2&&U8(0x3fdd)){
  age=18-U8(0x3fdd);
  cx=U8(59563)==1?110:U8(59563)==2?146:128;
  /* Cockpit bonnet begins at y159: put impact sparks above it. */
  cy=U8(60246)?160:145;
  for(i=0;i<6;++i){
   if(age>10&&(i&1))continue;
   x=cx+((int16_t)i*2-5)*(age+2)/2;
   y=cy-(3+(i%3)*2)*age/3+age*age/18-(i&1)*3;
   RECT(x-1,y-1,5,3,12);RECT(x,y,3,1,15);
   if(age<8)RECT(x+1,y-2,1,5,15);
  }
 }
 if(U8(0x3fd9)&&U8(0x3fdc)==3&&U8(60246)){
  RECT(105-phase,185+phase/2,3+phase/2,2,15);
  RECT(148+phase,185+phase/2,3+phase/2,2,15);
 }
}
