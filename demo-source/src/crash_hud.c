#include <stdint.h>
#define U8(a) (*(volatile uint8_t *)(a))
#define U16(a) (*(volatile uint16_t *)(a))
#define TEXT ((void (*)(int16_t,int16_t,const char *))0x888d)
#define RECT ((void (*)(int16_t,int16_t,uint16_t,uint16_t,uint8_t))0x86b6)
void crash_hud(void) {
 uint8_t phase;
 if(U8(57921)!=1 || U8(0x3fd8)!=0xc7)return;
 phase=U16(57950)&7;
 if(U8(0x3fd9)) {
  TEXT(92,38,"RECOVERING");
  /* Two small dust clusters, only while the skid/recovery animation runs. */
  if(U8(60246)) {
   RECT(105-phase,185+phase/2,3+phase/2,2,15);
   RECT(148+phase,185+phase/2,3+phase/2,2,15);
  }
 } else if(U8(0x3fda)) {
  if(phase<5)TEXT(116,38,"GO!");
 } else if(U8(0x3fdd)) {
  if(U8(0x3fdc)==1)TEXT(108,38,"SCRAPE");
  else TEXT(108,38,"IMPACT");
 }
}
