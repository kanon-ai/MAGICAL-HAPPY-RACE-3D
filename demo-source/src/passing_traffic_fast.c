/* Additional-lane policy; original two-lane policy remains the fallback. */
#include <stdint.h>
#define Z ((volatile uint16_t*)59457)
#define LANE ((volatile int8_t*)59479)
#define TARGET ((volatile int8_t*)59484)
#define HOLD ((volatile uint8_t*)0xf6fb)
#define DIST (*(volatile uint16_t*)57927)
#define PIECE (*(volatile uint8_t*)57935)
#define PLAYER (*(volatile int16_t*)57939)
#define TICK (*(volatile uint8_t*)59471)
static int16_t relative(uint16_t a,uint16_t b){
 uint16_t d=(a-b)&16383;return d>=8192?(int16_t)d-16384:(int16_t)d;
}
static uint8_t close_lane(int16_t a,int16_t b){int16_t d=a-b;return d>-34&&d<34;}
static uint8_t clear_lane(uint8_t i,int8_t target){
 uint8_t j;int16_t gap;
 for(j=0;j<5;++j){
  if(i==j)continue;
  gap=relative(Z[j],Z[i]);
  if(gap<=-240 || gap>=240)continue;
  if(close_lane(LANE[j],target)||close_lane(TARGET[j],target))return 0;
 }
 gap=relative(DIST,Z[i]);
 if(gap>-1200&&gap<240&&close_lane(PLAYER,target))return 0;
 return 1;
}
uint8_t passing_traffic(uint8_t i){
 int16_t ahead,local;
 uint8_t piece=PIECE,admit;int8_t lane=LANE[i],target=TARGET[i];
 /* Relative placement spans at most one piece either way. Outside 1..3,
    no ordinary-lane car can reach admission piece 2. Keep extra-lane
    and mid-merge cars on the complete recovery path. */
 if(lane<=40&&target<=40&&((piece&7)<1||(piece&7)>3)){
  HOLD[i]=0;return 0;
 }
 ahead=relative(Z[i],DIST);local=(int16_t)DIST+ahead;
 if(local<0){local+=16384;--piece;}else if(local>=16384){local-=16384;++piece;}
 piece&=7;
 admit=piece==2&&local>=4096&&local<14336;
 HOLD[i]=0;
 if(lane>40||target>40){
  if(!admit){
   /* Start merging well before narrowing; wait while still on full pavement. */
   if(target!=40&&clear_lane(i,40))TARGET[i]=40;
   if(lane>40&&(piece!=2)&&(piece!=3||local>=4096))HOLD[i]=1;
  }
  return 1;
 }
 if(!admit)return 0;
 if(lane!=target)return 1;
 if((uint8_t)(TICK+i*17)&127)return 1;
 target=lane<0?40:120;
 if(clear_lane(i,target))TARGET[i]=target;
 return 1;
}
