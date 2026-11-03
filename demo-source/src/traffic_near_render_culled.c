/* Experimental draw replacement for cockpit projection_base < 13 only.
 * Scratch vertex 180..184 and face 150..155 match transient gate workspace.
 * Integration/ownership and native pixels MUST be checked before adoption.
 */
#include "traffic_near_clip.c"
#include "near_car_data.h"
#include "gate_addresses.h"
__sfr __at(GEO_INDEX) gi;
__sfr __at(GEO_DATA) gd;
#define BASE (*(int16_t *)60628)
#define PX (*(int16_t *)60624)
#define PY (*(int16_t *)60626)
#define LEFT (*(uint8_t *)60634)
/* Exact signed Q12 product; call1 HL=value, DE=scale, DE=result. */
static int16_t project(int16_t v,uint16_t scale) __naked {
    v;scale;
    __asm
    ld b,d
    ld c,e
    ld a,h
    push af
    bit 7,h
    jr z,near_mul
    xor a
    sub l
    ld l,a
    sbc a,a
    sub h
    ld h,a
near_mul:
    .db 0xed,0xc3
    ld a,h
    rrca
    rrca
    rrca
    rrca
    and #15
    sla e
    rl d
    sla e
    rl d
    sla e
    rl d
    sla e
    rl d
    or e
    ld e,a
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
static void vertex(int16_t x,int16_t y) {
    gd=x;gd=x>>8;y=-y;gd=y;gd=y>>8;gd=1;gd=0;
}
void draw_near_car(uint8_t variant,uint8_t clip) {
    ClipVertex in[4],out[5];
    uint8_t face,j,n,t,reverse,k,a,b,c,indices[4],outside,mask;
    const uint8_t *p,*m=near_models+variant*156;
    TEX_WINDOW(0,212,255,255);WORD(0x60,0);WORD(0x62,212);gi=0x64;gd=0;
    WORD(24,1);WORD(26,0);WORD(28,0);WORD(30,1);WORD(34,clip<BOTTOM?clip:BOTTOM);
    gi=0x68;gd=0;gi=0x6c;gd=0;gi=0x6e;gd=0;gi=0x6f;gd=0;
    for(face=0;face<23;++face) {
        p=near_faces+(variant*23+face)*13;
        outside=7;
        for(j=0;j<4;++j) {
            const uint8_t *v=m+p[j]*3;
            in[j].x=(int16_t)(int8_t)v[0]*4;
            if(!LEFT)in[j].x=-in[j].x;
            in[j].x+=PX;in[j].y=(int16_t)v[1]*4+PY;
            in[j].z=(int16_t)v[2]*2+BASE;
            in[j].u=p[4+j*2];in[j].v=p[5+j*2];
            /* Convex homogeneous half-planes; four-pixel viewport margin.
             * Only bounded arithmetic is used; unusual values fall back.
             */
            mask=in[j].z<13?1:0;
            if(in[j].x>=-4096 && in[j].x<=4096 && in[j].z>=-900 && in[j].z<=900) {
                int16_t x6=in[j].x*6,z33=in[j].z*33;
                if(x6 < -z33)mask|=2;
                if(x6 > z33)mask|=4;
            }
            outside&=mask;
        }
        if(outside)continue;
        n=traffic_clip_quad(in,out);if(n<3)continue;
        gi=0x40;gd=180;gi=0x50;
        for(j=0;j<n;++j) {
            uint16_t scale=((uint16_t *)0x0400)[out[j].z];
            vertex(128+project(out[j].x,scale),78-project(out[j].y,scale));
        }
        gi=0x58;gd=150;gi=0x52;
        for(t=1;t<n-1;++t)for(reverse=0;reverse<2;++reverse) {
            a=0;b=reverse?t+1:t;c=reverse?t:t+1;
            gd=180+a;gd=180+b;gd=180+c;gd=180+c;
            for(k=0;k<6;++k)gd=0;
            gd=p[12];
        }
        gi=0x65;gd=150;gi=0x53;
        for(t=1;t<n-1;++t)for(reverse=0;reverse<2;++reverse) {
            indices[0]=0;indices[1]=reverse?t+1:t;
            indices[2]=reverse?t:t+1;indices[3]=indices[2];
            for(k=0;k<4;++k){gd=out[indices[k]].u;gd=out[indices[k]].v;}
        }
        WORD(0x54,180);WORD(0x56,150);gi=0x42;gd=n;
        gi=0x59;gd=(n-2)*2;gi=0x45;gd=0;WORD(0x46,(uint16_t)PAGE<<8);
        gi=0x48;gd=7;while(gi&1)POLL();
    }
    WORD(0x54,0);WORD(0x56,0);
}
