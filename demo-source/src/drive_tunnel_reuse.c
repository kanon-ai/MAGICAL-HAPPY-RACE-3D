/* World-anchored checkpoint gates. No checkpoint or simulation writes. */
#include <stdint.h>
#include "gate_addresses.h"
__sfr __at(GEO_INDEX) gi;
__sfr __at(GEO_DATA) gd;
typedef struct { int16_t x,y,w; uint8_t clip; } Plane;
static const uint16_t depth[16]={28,32,36,42,50,60,72,86,102,124,150,184,230,292,380,512};
static int16_t scale(int16_t value,uint16_t numerator,uint16_t denominator){return (int32_t)value*numerator/denominator;}
static void project(int16_t gap,Plane *p){
 uint16_t at=gap<28?28:(gap>512?512:gap),part,span;
 uint8_t k=TRAFFIC_LUT[at],*a,*b,raw;
 int16_t cx,y,w,horizon;
 if(at<depth[k]&&k)--k;
 a=PROFILE+192+((uint16_t)k<<2);cx=(int8_t)a[0];y=a[1];w=a[2];p->clip=a[3];
 if(k<15){b=a+4;part=at-depth[k];span=depth[k+1]-depth[k];
  cx+=LERP((int8_t)b[0]-cx,part,span);y+=LERP((int16_t)b[1]-y,part,span);w+=LERP((int16_t)b[2]-w,part,span);}
 raw=w;horizon=PROFILE[123];
 if(CAMERA){cx=VIEW_X(128+cx,raw)-128;y=VIEW_Y(y,raw);p->clip=p->clip>=168?BOTTOM:VIEW_Y(p->clip,raw);w=VIEW_W(raw);horizon=VIEW_Y(horizon,0);}
 cx-=CAMERA_SHIFT((uint8_t)w>>1);
 if(gap<28 || gap>512){uint16_t offset=CAMERA?60:0,den=gap+offset;
  if((int16_t)den<4)den=4;
  cx=scale(cx,at+offset,den);y=horizon+scale(y-horizon,at+offset,den);w=scale(w,at+offset,den);}
 p->x=128+cx;p->y=y;p->w=w;if(p->clip>BOTTOM)p->clip=BOTTOM;
}
static void vertex(int16_t x,int16_t y){gd=x;gd=x>>8;y=-y;gd=y;gd=y>>8;gd=1;gd=0;}
static void rect_vertices(int16_t x,int16_t y,int16_t right,int16_t bottom){vertex(x,y);vertex(right,y);vertex(right,bottom);vertex(x,bottom);}
static void face(uint8_t base,uint8_t color){gd=base;gd=base+1;gd=base+2;gd=base+3;gd=0;gd=0;gd=0;gd=0;gd=0;gd=0;gd=color;}
#ifdef ROCK_ARCH
#include "rock_arch_model.h"
#include "rock_arch_streams.h"
#include "tunnel_inset_streams.h"
static void stream_faces(const uint8_t *p) __z88dk_fastcall __naked {
 p;
 __asm
 ld c,#GEO_DATA
 ld b,#176
 otir
 ret
 __endasm;
}
static void stream_uv(const uint8_t *p) __z88dk_fastcall __naked {
 p;
 __asm
 ld c,#GEO_DATA
 ld b,#128
 otir
 ret
 __endasm;
}
#ifdef ARCH_LOD
static void stream_far_faces(const uint8_t *p) __z88dk_fastcall __naked {
 p;
 __asm
 ld c,#GEO_DATA
 ld b,#88
 otir
 ret
 __endasm;
}
static void stream_far_uv(const uint8_t *p) __z88dk_fastcall __naked {
 p;
 __asm
 ld c,#GEO_DATA
 ld b,#64
 otir
 ret
 __endasm;
}
#endif
/* Exact truncation toward zero without a 32-bit multiply for every vertex.
   Model magnitude <=136; projected width <=4096: both products fit 16 bits. */
/* SDCC call1: signed value HL, positive width DE, result DE.
   magnitude<=136,width<=4096 => product<2^24, exact Q6 truncation. */
static int16_t arch_coord(int16_t value,uint16_t width) __naked {
 value;width;
 __asm
 ld b,d
 ld c,e
 ld a,h
 push af
 bit 7,h
 jr z,arch_mul
 xor a
 sub l
 ld l,a
 sbc a,a
 sub h
 ld h,a
arch_mul:
 .db 0xed,0xc3
 ld b,#6
arch_shift:
 srl e
 rr h
 rr l
 djnz arch_shift
 ex de,hl
 pop af
 bit 7,a
 ret z
 xor a
 sub e
 ld e,a
 sbc a,a
 sub d
 ld d,a
 ret
 __endasm;
}
/* Draw only visible faces, from the far portal to the near portal. */
static void draw_rock_shell(int16_t gap,int16_t halfdepth){
 Plane nearp,farp;uint8_t i;int16_t x,y;const int16_t *v;
 #ifdef ARCH_LOD
 uint8_t distant=gap>512;
 const uint8_t *front=halfdepth>24?tunnel_faces_front:arch_faces_front;
 const uint8_t *back=halfdepth>24?tunnel_faces_back:arch_faces_back;
 project(halfdepth>24 && gap-halfdepth < (CAMERA?-44:16) ? (CAMERA?-44:16) : gap-halfdepth,&nearp);
 if(!distant)project(gap+halfdepth,&farp);
 if(nearp.w>4096 || (distant?nearp.w:farp.w)<2)return;
 #else
 project(halfdepth>24 && gap-halfdepth < (CAMERA?-44:16) ? (CAMERA?-44:16) : gap-halfdepth,&nearp);project(gap+halfdepth,&farp);
 if(nearp.w>4096 || farp.w<2)return;
 #endif
 if(halfdepth>24)TEX_WINDOW(192,754,255,767);else TEX_WINDOW(0,768,127,831);
 WORD(24,1);WORD(26,0);WORD(28,0);WORD(30,1);WORD(34,nearp.clip);
 WORD(0x60,halfdepth>24?192:0);WORD(0x62,halfdepth>24?754:768);gi=0x64;gd=0;
 gi=0x68;gd=0;gi=0x6c;gd=0;gi=0x6e;gd=0;gi=0x6f;gd=0;
 gi=0x40;gd=180;gi=0x50;
 #ifdef ARCH_LOD
 for(i=0;i<(distant?18:36);++i){Plane *p=i<18?&nearp:&farp;v=rock_arch_vertices[i];
 #else
 for(i=0;i<36;++i){Plane *p=i<18?&nearp:&farp;v=rock_arch_vertices[i];
 #endif
  x=p->x+arch_coord(v[0],p->w);y=p->y-arch_coord(v[1],p->w);vertex(x,y);}
 gi=0x58;gd=150;gi=0x52;
 #ifdef ARCH_LOD
 if(distant)stream_far_faces(front+88);else
 #endif
 stream_faces(gap-halfdepth+(CAMERA?60:0)>4?front:back);
 gi=0x65;gd=150;gi=0x53;
 #ifdef ARCH_LOD
 if(distant)stream_far_uv(arch_uv+64);else
 #endif
 stream_uv(halfdepth>24?tunnel_uv:arch_uv);
 WORD(0x54,180);WORD(0x56,150);gi=0x42;gd=36;gi=0x59;gd=16;gi=0x45;gd=0;WORD(0x46,(uint16_t)PAGE<<8);
 #ifdef ARCH_LOD
 if(distant){gi=0x42;gd=18;gi=0x59;gd=8;}
 #endif
 gi=0x48;gd=7;while(gi&1)POLL();
 /* ARCH_GPU_DONE */
 WORD(0x54,0);WORD(0x56,0);
}
#endif


/* HL=Plane. Same Q6 coordinates and vertex order, avoiding C loop spills. */
static void lining_ring(Plane *p) __z88dk_fastcall __naked {
 p;
 __asm
 push ix
 push iy
 push hl
 pop ix
 ld iy,#(_rock_arch_vertices+54)
 ld b,#9
ring_loop:
 push bc
 ld l,0(iy)
 ld h,1(iy)
 ld e,4(ix)
 ld d,5(ix)
 call _arch_coord
 ld l,0(ix)
 ld h,1(ix)
 add hl,de
 ld a,l
 out (_gd),a
 ld a,h
 out (_gd),a
 ld l,2(iy)
 ld h,3(iy)
 ld e,4(ix)
 ld d,5(ix)
 call _arch_coord
 ld l,2(ix)
 ld h,3(ix)
 ex de,hl
 or a
 sbc hl,de
 ld a,l
 out (_gd),a
 ld a,h
 out (_gd),a
 ld a,#1
 out (_gd),a
 xor a
 out (_gd),a
 ld de,#6
 add iy,de
 pop bc
 djnz ring_loop
 pop iy
 pop ix
 ret
 __endasm;
}
/* World-fixed 4 m lining slices. Clip geometry and depth UV together. */
static uint8_t draw_lining_slice(int16_t zn,int16_t zf,Plane *shared,uint8_t valid){
 Plane a,b;int16_t clipz=CAMERA?-44:16,original=zn;uint8_t i,vnear=1,nearbase=valid==1?189:180,farbase=valid==1?180:189;
 if(zf<=clipz)return valid;
 if(zn<clipz){zn=clipz;vnear=1+(uint16_t)(zn-original)*11/64;}
 project(zn,&a);if(valid)b=*shared;else project(zf,&b);*shared=a;if(a.w>4096||b.w<2)return 1;
 TEX_WINDOW(192,754,255,767);
 WORD(24,1);WORD(26,0);WORD(28,0);WORD(30,1);WORD(34,a.clip);
 WORD(0x60,192);WORD(0x62,754);gi=0x64;gd=0;
 gi=0x68;gd=0;gi=0x6c;gd=0;gi=0x6e;gd=0;gi=0x6f;gd=0;
 if(!valid){gi=0x40;gd=farbase;gi=0x50;lining_ring(&b);}
 gi=0x40;gd=nearbase;gi=0x50;lining_ring(&a);
 gi=0x58;gd=150;gi=0x52;
 for(i=0;i<8;++i){gd=nearbase+i;gd=nearbase+1+i;gd=farbase+1+i;gd=farbase+i;
  gd=0;gd=0;gd=0;gd=0;gd=0;gd=0;gd=128;}
 gi=0x65;gd=150;gi=0x53;
 for(i=0;i<8;++i){gd=1;gd=vnear;gd=62;gd=vnear;gd=62;gd=12;gd=1;gd=12;}
 WORD(0x54,180);WORD(0x56,150);gi=0x42;gd=18;gi=0x59;gd=8;
 gi=0x45;gd=0;WORD(0x46,(uint16_t)PAGE<<8);gi=0x48;gd=7;
 while(gi&1)POLL();WORD(0x54,0);WORD(0x56,0);return valid==1?2:1;
}

void draw_drive_gate(void){
 int16_t gap,left,right,top,beam,thick;uint8_t goal;Plane p;
 if(MODE!=1&&MODE!=2&&MODE!=4)return;
 #ifdef ROCK_ARCH
 #ifdef ARCH_SERIES
 if(PIECE==12){uint8_t arch;
  /* Far to near; 64 m spacing, at most two portals in the draw window. */
  for(arch=4;arch;){--arch;gap=6144+((uint16_t)arch<<10)-DISTANCE;
   if(gap<=1400 && gap>(CAMERA?-84:-24))draw_rock_shell(gap,24);
  }
  return;}
 #else
 if(PIECE==12){gap=8192-DISTANCE;
  if(gap<=2048 && gap>(CAMERA?-84:-24))draw_rock_shell(gap,24);
  return;}
 #endif
#endif
 if((PIECE&7)==7){gap=16384-DISTANCE;if(gap>2048)return;goal=PIECE==47;}
 else if(CAMERA && PIECE && !(PIECE&7) && DISTANCE<56){gap=-(int16_t)DISTANCE;goal=0;}
 else return;
 project(gap,&p);if(p.w<2||p.w>2048)return;
 /* Supports begin beyond the paved shoulder; 5.4m head clearance. */
 left=p.x-p.w*3/2;right=p.x+p.w*3/2;thick=p.w/8;if(!thick)thick=1;
 top=p.y-p.w*15/8;beam=p.y-p.w*3/2;
 if(top>=p.clip || p.y<0)return;
 TEX_WINDOW(goal?64:0,650,goal?127:63,657);
 WORD(24,1);WORD(26,0);WORD(28,0);WORD(30,1);WORD(34,p.clip);
 WORD(0x60,goal?64:0);WORD(0x62,650);gi=0x64;gd=0;
 gi=0x68;gd=0;gi=0x6c;gd=0;gi=0x6e;gd=0;gi=0x6f;gd=0;
 gi=0x40;gd=210;gi=0x50;
 rect_vertices(left-thick,top,left,p.y);rect_vertices(right,top,right+thick,p.y);rect_vertices(left-thick,top,right+thick,beam);
 gi=0x58;gd=150;gi=0x52;face(210,15);face(214,14);face(218,128);
 gi=0x65;gd=152;gi=0x53;gd=0;gd=0;gd=63;gd=0;gd=63;gd=7;gd=0;gd=7;
 WORD(0x54,210);WORD(0x56,150);gi=0x42;gd=12;gi=0x59;gd=3;gi=0x45;gd=0;WORD(0x46,(uint16_t)PAGE<<8);
 gi=0x48;gd=7;while(gi&1)POLL();
 WORD(0x54,0);WORD(0x56,0);
}

/* Draw after roadside objects and beacons, before the player and HUD.
   Road opening remains transparent; walls cover exterior scenery. */
void draw_late_tunnel(void){
 int16_t gap;
 if(PIECE!=20 || (MODE!=1&&MODE!=2&&MODE!=4))return;
 gap=8192-DISTANCE;
 if(gap<=1400 && gap>-(256+(CAMERA?60:0))){
  uint8_t n,id,valid=0;int16_t car_gap;Plane shared;
  draw_rock_shell(gap,256);
  for(n=8;n;){--n;valid=draw_lining_slice(gap-256+((uint16_t)n<<6),gap-192+((uint16_t)n<<6),&shared,valid);}
  /* Re-submit only cars in front of the exit, far to near. Cars beyond
     the exit retain the wall mask from the first scenery/traffic pass. */
  for(n=0;n<5;++n){
   id=((uint8_t *)59555)[n];
   car_gap=((uint16_t *)59500)[id]&16383;
   if(car_gap&8192)car_gap-=16384;
   if(car_gap<gap+256)((void (*)(uint8_t))11298)(id);
  }
 }
}
