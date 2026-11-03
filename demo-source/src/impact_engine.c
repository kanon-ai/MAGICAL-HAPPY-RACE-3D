#include <stdint.h>
#define U8(a) (*(volatile uint8_t *)(a))
__sfr __at(0xa0) select;
__sfr __at(0xa1) output;
static void psg(uint8_t r,uint8_t v){select=r;output=v;}
void impact_engine(uint16_t speed,uint8_t offroad,uint8_t muted){
 uint16_t tone=1440-speed,thud;uint8_t age=18-U8(0x3fdd);
 uint8_t impact=!muted&&U8(0x3fd8)==0xc7&&U8(0x3fdc)==2&&U8(0x3fdd)&&age<8;
 psg(0,tone);psg(1,tone>>8);psg(2,tone+9);psg(3,(tone+9)>>8);
 psg(8,muted?0:9);psg(9,muted?0:6);
 if(impact){
  /* Short damped impact on channel C, not the former long explosion. */
  thud=160+((uint16_t)age<<6);psg(4,thud);psg(5,thud>>8);
  psg(6,12+age*2);psg(7,0x98);psg(10,12-age);
 }else{
  psg(6,offroad?12:4);psg(7,0x9c);
  psg(10,muted?0:(speed>12?(offroad?6:1):0));
 }
}
