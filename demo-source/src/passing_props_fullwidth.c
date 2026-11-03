/* Shift right-hand scenery with the same taper as the road mesh.
   Called once after fresh course decode/appearance, never cumulatively. */
#include <stdint.h>
#define PIECE (*(volatile uint8_t*)0xe24f)
#define DISTANCE (*(volatile uint16_t*)0xe247)
/* Reuse the unchanged current bank211 shift helper, A input / DE return. */
static uint16_t shift(uint8_t width) __naked {
 width;
 __asm
 jp 0x60c2
 __endasm;
}
void shift_passing_props(void){
 uint8_t last_width=0,width;uint16_t amount=0;
 uint8_t local=PIECE&7;uint16_t distance=DISTANCE;
 uint8_t full=(local==2 && distance>=4096)||(local==3 && distance<=11268);
 uint8_t i,j,*p=(uint8_t*)0xe2e2,*m=(uint8_t*)0x100;
 for(i=0;i<8;++i,p+=8,m+=60){
  if(!p[7] || (p[5]&96))continue;
  *((int16_t*)p)+=(full?((uint16_t)p[7]*5)>>2:shift(p[7]));
  if((p[5]&7)!=4 && (p[5]&7)!=5 && (p[5]&7)!=7){
   for(j=0;j<8;++j){
    width=m[j*5+4];
    if(!j || width!=last_width){amount=full?((uint16_t)width*5)>>2:shift(width);last_width=width;}
    *((int16_t*)(m+j*5))+=amount;
   }
  }
 }
}
