/* V9968 SCREEN8 / 256-entry EPAL / high-speed commands. */
#include "hardware.h"
#include "palette.h"
#include "stages.h"
__sfr __at(IO_VRAM) vram;
__sfr __at(IO_CONTROL) control;
__sfr __at(IO_PALETTE) pal;
__sfr __at(IO_COMMAND) command;
__sfr __at(IO_UNLOCK) unlock;
__sfr __at(0xe6) timer_low;
__sfr __at(0xe7) timer_high;
u16 gfx_timer(void){u8 a,b,c;do{a=timer_high;b=timer_low;c=timer_high;}while(a!=c);return ((u16)a<<8)|b;}
__sfr __at(0xa0) hw_psg_select;
__sfr __at(0xa1) hw_psg_write;
__sfr __at(0xa2) hw_psg_read;
__sfr __at(0xa9) hw_key_data;
__sfr __at(0xaa) hw_key_select;
static void reg(u8 r,u8 v){control=v;control=0x80|r;}
#define CW(v) do{command=(u8)(v);command=(u8)((v)>>8);}while(0)
u16 span_y;
u8 span_height;
volatile u16 scaled_draws;
/* Independent motion clock. Sample during GPU waits as well as frames so
 * slow rendering cannot lose a 16-bit E6 timer wrap. Never reset E6/E7. */
volatile unsigned long simulation_ticks;
u16 simulation_timer_last;
void simulation_clock_init(void){simulation_ticks=0;simulation_timer_last=gfx_timer();}
void bgm_poll(void) __naked{
 __asm
 call 0xd600
 push af
 push bc
 push de
 push hl
motion_timer_read:
 in a,(0xe7)
 ld b,a
 in a,(0xe6)
 ld c,a
 in a,(0xe7)
 cp b
 jr nz,motion_timer_read
 ld h,b
 ld l,c
 ld de,(_simulation_timer_last)
 ld (_simulation_timer_last),hl
 or a
 sbc hl,de
 ld de,(_simulation_ticks)
 add hl,de
 ld (_simulation_ticks),hl
 jr nc,motion_timer_done
 ld hl,(_simulation_ticks+2)
 inc hl
 ld (_simulation_ticks+2),hl
motion_timer_done:
 pop hl
 pop de
 pop bc
 pop af
 ret
 __endasm;
}
void bgm_start(void) __naked{__asm jp 0xd603 __endasm;}
void gfx_wait(void){bgm_poll();reg(15,2);while(control&1){bgm_poll();}}
/* A completed back buffer can flip during the current blanking interval. */
void gfx_vblank(void){reg(15,2);while(!(control&0x40)){bgm_poll();}}
void gfx_set_palette(const u8 *p){u16 i;gfx_wait();*((volatile u8*)0x6000)=250;reg(16,0);for(i=0;i<768;++i)pal=p[i];}
#ifdef REFERENCE_COMMANDS
void gfx_fill(u16 x,u16 y,u16 w,u16 h,u8 c){
    u8 aligned=!((x|w)&1);if(!w||!h)return;
    gfx_wait();reg(17,36);CW(x);CW(y);CW(w);CW(h);
    command=c;command=0;command=0xc0;
}
#else
/* SDCC call1: x in HL, y in DE; w, h and color on the stack. */
void gfx_fill(u16 x,u16 y,u16 w,u16 h,u8 c) __naked {
 x;y;w;h;c;
 __asm
 push ix
 ld ix,#0
 add ix,sp
 ld a,4(ix)
 or 5(ix)
 jr z,fill_done
 ld a,6(ix)
 or 7(ix)
 jr z,fill_done
 ld a,#2
 out (IO_CONTROL),a
 ld a,#0x8f
 out (IO_CONTROL),a
fill_wait:
 call _bgm_poll
 in a,(IO_CONTROL)
 and #1
 jr nz,fill_wait
 ld a,#36
 out (IO_CONTROL),a
 ld a,#0x91
 out (IO_CONTROL),a
 ld a,l
 out (IO_COMMAND),a
 ld a,h
 out (IO_COMMAND),a
 ld a,e
 out (IO_COMMAND),a
 ld a,d
 out (IO_COMMAND),a
 push ix
 pop hl
 ld bc,#4
 add hl,bc
 ld bc,#((0x0500) | IO_COMMAND)
 otir
 xor a
 out (IO_COMMAND),a
 ld a,#0xc0
 out (IO_COMMAND),a
fill_done:
 pop ix
 pop de
 ld hl,#5
 add hl,sp
 ld sp,hl
 ex de,hl
 jp (hl)
 __endasm;
}
#endif

#ifdef REFERENCE_COMMANDS
void gfx_blit(u16 sx,u16 sy,u16 dx,u16 dy,u16 w,u16 h,u8 t){
    if(!w||!h)return;gfx_wait();reg(17,32);
    CW(sx);CW(sy);CW(dx);CW(dy);CW(w);CW(h);
    command=0;command=0;command=t?0x98:0xd0;
}
#else
void gfx_blit(u16 sx,u16 sy,u16 dx,u16 dy,u16 w,u16 h,u8 t) __naked{
    sx;sy;dx;dy;w;h;t;
    __asm
    push ix
    ld ix,#0
    add ix,sp
    ld a,8(ix)
    or 9(ix)
    jr z,blit_done
    ld a,10(ix)
    or 11(ix)
    jr z,blit_done
    ld b,#0xd0
blit_aligned:
    ld a,12(ix)
    or a
    jr z,blit_wait
    ld b,#0x98
blit_wait:
    call _bgm_poll
    in a,(IO_CONTROL)
    and #1
    jr nz,blit_wait
    push bc
    ld a,#32
    out (IO_CONTROL),a
    ld a,#0x91
    out (IO_CONTROL),a
    ld a,l
    out (IO_COMMAND),a
    ld a,h
    out (IO_COMMAND),a
    ld a,e
    out (IO_COMMAND),a
    ld a,d
    out (IO_COMMAND),a
    push ix
    pop hl
    ld bc,#4
    add hl,bc
    ld bc,#((0x0800) | IO_COMMAND)
    otir
    xor a
    out (IO_COMMAND),a
    out (IO_COMMAND),a
    pop bc
    ld a,b
    out (IO_COMMAND),a
blit_done:
    pop ix
    pop de
    ld hl,#9
    add hl,sp
    ld sp,hl
    ex de,hl
    jp (hl)
    __endasm;
}
#endif
/* One LRMM command scales a complete object. CPU only clips its bounds.
 * Same X/Y step: no per-row software scaling or intermediate bitmaps.
 */
void gfx_scaled(u8 origin_x,u16 sy,u8 sw,u8 w,u8 h,u16 step,s16 x,s16 y,s16 bottom,u16 page,u8 mirror){
    u16 sx=origin_x,srcy=sy; s16 dw=w,dh=h;
    if(x>=256||x+dw<=0||y>=bottom||y+dh<=0)return;
    if(x<0){if(!mirror)sx=origin_x+(((u16)(-x)*step)>>8);dw+=x;x=0;}
    if(y<0){srcy+=((u16)(-y)*step)>>8;dh+=y;y=0;}
    if(x+dw>256){if(mirror)sx+=((u16)(x+dw-256)*step)>>8;dw=256-x;}if(y+dh>bottom)dh=bottom-y;
    if(dw<=0||dh<=0)return;
    gfx_wait();reg(17,47);CW(step);CW(0);
    CW((u16)origin_x);CW(sy);CW((u16)origin_x+sw-1);CW(sy+127);
    reg(17,32);CW(sx);CW(srcy);CW((u16)(mirror?x+dw-1:x));CW(page+y);CW((u16)dw);CW((u16)dh);
    command=0;command=mirror?4:0;command=0x38;++scaled_draws;
}
void gfx_texture_window(u16 x,u16 y,u16 ex,u16 ey){gfx_wait();reg(17,51);CW(x);CW(y);CW(ex);CW(ey);}
void gfx_begin_spans(void){}
#ifdef REFERENCE_COMMANDS
void gfx_span(s16 left,s16 right,u8 c){
    if(left<0)left=0;if(right>256)right=256;
    if(right>left)gfx_fill(left,span_y,right-left,span_height,c);
}
#else
void gfx_span(s16 left,s16 right,u8 c) __naked{
    left;right;c;
    __asm
    bit 7,h
    jr z,span_nonnegative
    ld hl,#0
span_nonnegative:
    bit 7,d
    jr nz,span_done
    ld a,d
    or a
    jr z,span_clipped
    ld de,#256
span_clipped:
    ld a,h
    or a
    jr nz,span_done
    ld a,e
    sub l
    ld c,a
    ld a,d
    sbc a,#0
    jr c,span_done
    ld b,a
    or c
    jr z,span_done
span_wait:
    call _bgm_poll
    in a,(IO_CONTROL)
    and #1
    jr nz,span_wait
    ld a,#36
    out (IO_CONTROL),a
    ld a,#0x91
    out (IO_CONTROL),a
    ld a,l
    out (IO_COMMAND),a
    xor a
    out (IO_COMMAND),a
    ld a,(_span_y)
    out (IO_COMMAND),a
    ld a,(_span_y+1)
    out (IO_COMMAND),a
    ld a,c
    out (IO_COMMAND),a
    ld a,b
    out (IO_COMMAND),a
    ld a,(_span_height)
    out (IO_COMMAND),a
    xor a
    out (IO_COMMAND),a
    ld hl,#2
    add hl,sp
    ld a,(hl)
    ld c,#0xc0
span_color:
    out (IO_COMMAND),a
    xor a
    out (IO_COMMAND),a
    ld a,c
    out (IO_COMMAND),a
span_done:
    pop hl
    inc sp
    jp (hl)
    __endasm;
}
#endif
/* Start the next back buffer during blanking; do not spend it idling. */
void gfx_flip(u8 page){gfx_wait();gfx_vblank();reg(2,page?63:31);}
static void vaddr(u8 high,u16 low){reg(14,high);control=low;control=0x40|((low>>8)&63);}
static void upload8k(void) __naked{
    __asm
    ld hl,#0x6000
    ld c,#IO_VRAM
    ld e,#32
upload_loop:
    ld b,#0
    otir
    dec e
    jr nz,upload_loop
    ret
    __endasm;
}
void hardware_upload(void){
 u8 b,row;u16 offset;
 gfx_wait();
 for(b=0;b<8;++b){*((volatile u8*)0x6000)=4+b;vaddr(8+b/2,(b&1)?8192:0);upload8k();}
 gfx_upload_begin(212);
 for(row=0;row<88;++row){
  if(row==44)gfx_upload_begin(468);
  offset=(u16)row<<8;*((volatile u8*)0x6000)=12+(offset>>13);
  gfx_upload_256((const u8*)(0x6000+(offset&8191)));
 }
 reg(1,0x40);
}
void gfx_upload_begin(u16 y){gfx_wait();vaddr((u8)(y>>6),(y&63)<<8);}
void gfx_upload_256(const u8 *data) __naked{
    data;
    __asm
    ld bc,#IO_VRAM
    otir
    ret
    __endasm;
}
void gfx_init(void){
    static const u8 regs[]={21,0,20,25,0,14,1,0,2,31,7,0,8,10,9,128,18,0,23,0,25,0,26,0,27,0};
    u8 i;unlock=0;for(i=0;i<sizeof(regs);i+=2)reg(regs[i],regs[i+1]);
    gfx_set_palette(v9990_palette);gfx_fill(0,0,256,512,0);scaled_draws=0;
}
u8 input_read(void){
    u8 k,result=0,ppi=hw_key_select,joy;
    hw_key_select=(ppi&0xf0)|8;k=(u8)~hw_key_data;
    if(k&0x10)result|=INPUT_LEFT;if(k&0x80)result|=INPUT_RIGHT;
    if(k&0x20)result|=INPUT_UP;if(k&0x40)result|=INPUT_DOWN;
    if(k&1)result|=INPUT_FIRE;
    hw_key_select=(ppi&0xf0)|5;
    if(!(hw_key_data&0x20))result|=INPUT_BRAKE;
    hw_key_select=(ppi&0xf0)|7;
    if(!(hw_key_data&4))result|=INPUT_PAUSE;
    hw_key_select=(ppi&0xf0)|2;
    if(!(hw_key_data&2))result|=INPUT_VIEW;
    hw_key_select=ppi;
    hw_psg_select=7;hw_psg_write=(hw_psg_read&0x3f)|0x80;
    hw_psg_select=15;joy=hw_psg_read;hw_psg_write=(joy&0xaf)|3;
    hw_psg_select=14;k=(u8)~hw_psg_read;
    if(k&4)result|=INPUT_LEFT;if(k&8)result|=INPUT_RIGHT;
    if(k&1)result|=INPUT_UP;if(k&2)result|=INPUT_DOWN;
    if(k&0x10)result|=INPUT_FIRE;if(k&0x20)result|=INPUT_BRAKE;
    hw_psg_select=15;hw_psg_write=joy;return result;
}
static void psg(u8 r,u8 v){hw_psg_select=r;hw_psg_write=v;}
void engine_sound(u16 speed,u8 offroad,u8 muted){
    u16 tone=720-speed;
    psg(0,(u8)tone);psg(1,(u8)(tone>>8));
    psg(2,(u8)(tone+9));psg(3,(u8)((tone+9)>>8));
    psg(6,offroad?12:4);
    psg(7,0x9c); /* A+B tone, C noise; keep joystick port directions. */
    psg(8,muted?0:8);psg(9,muted?0:5);
    psg(10,muted?0:((speed>12)?(offroad?6:1):0));
}
