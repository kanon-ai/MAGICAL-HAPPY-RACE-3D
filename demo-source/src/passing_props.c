/* Shift right-hand scenery with the same taper as the road mesh.
   Called once after fresh course decode/appearance, never cumulatively. */
#include <stdint.h>
#define PIECE (*(volatile uint8_t*)0xe24f)
#define DISTANCE (*(volatile uint16_t*)0xe247)
static uint8_t fraction(uint16_t ahead){
 uint16_t z=DISTANCE+ahead;uint8_t p=PIECE;
 if(z>=16384){z-=16384;++p;}p&=7;
 if(p==2)return z<4096?z>>7:32;
 if(p==3)return z<12288?32:(16384-z)>>7;
 return 0;
}
static uint16_t shift(uint8_t width){
 uint16_t ahead=((const uint8_t*)0x8c35)[width]*4;
 return ((uint16_t)width*fraction(ahead)*5)>>7;
}
void shift_passing_props(void){
 uint8_t i,j,*p=(uint8_t*)0xe2e2,*m=(uint8_t*)0x100;
 for(i=0;i<8;++i,p+=8,m+=60){
  if(!p[7] || (p[5]&96))continue;
  *((int16_t*)p)+=shift(p[7]);
  if((p[5]&7)!=4 && (p[5]&7)!=5 && (p[5]&7)!=7){
   for(j=0;j<8;++j)*((int16_t*)(m+j*5))+=shift(m[j*5+4]);
  }
 }
}
