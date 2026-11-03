#pragma save
#pragma opt_code_size
#include "vehicle_mesh_data.h"
#include "player_projection_data.h"
volatile u8 car_draw_id;
s16 car_px[92],car_py[92];
/* Exact signed Q12 multiply, using R800 MULUW instead of Z80 long helpers.
 * SDCC call1: input HL, result DE. Truncate toward zero as in the C reference. */
u16 car_scale;
static s16 car_q12(s16 value) __naked{
 value;
 __asm
 ld a,h
 push af
 bit 7,h
 jr z,car_multiply
 xor a
 sub l
 ld l,a
 sbc a,a
 sub h
 ld h,a
car_multiply:
 ld bc,(_car_scale)
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
/* V2: six static face/UV packets reside at face slots 256..621. */
u16 car_resident_slot;
u8 car_upload_stride;
void car_upload(const u8 *packet) __naked {
 packet;
 __asm
 ld a,(hl)
 inc hl
 push af
 ld d,a
 ld a,#0x58
 out (IO_GEO_INDEX),a
 ld a,(_car_resident_slot)
 out (IO_GEO_DATA),a
 ld a,#0x6c
 out (IO_GEO_INDEX),a
 ld a,(_car_resident_slot+1)
 out (IO_GEO_DATA),a
 ld a,#0x52
 out (IO_GEO_INDEX),a
 ld c,#IO_GEO_DATA
car_faces_copy:
 ld a,(_car_upload_stride)
 ld b,a
 otir
 dec d
 jr nz,car_faces_copy
 pop af
 push af
 ld d,a
 ld a,#0x65
 out (IO_GEO_INDEX),a
 ld a,(_car_resident_slot)
 out (IO_GEO_DATA),a
 ld a,#0x6e
 out (IO_GEO_INDEX),a
 ld a,(_car_resident_slot+1)
 out (IO_GEO_DATA),a
 ld a,#0x53
 out (IO_GEO_INDEX),a
car_uv_copy:
 ld b,#8
 otir
 dec d
 jr nz,car_uv_copy
 pop af
 ld b,a
 ld a,#0x59
 out (IO_GEO_INDEX),a
 ld a,b
 out (IO_GEO_DATA),a
 ret
 __endasm;
}
/* 10-bit face addresses and FFIRST are V2-only; vertex indices stay 8-bit. */
u8 car_width;
/* Exact (signed screen displacement * 1450) / width. The bounded camera
 * and course anchors guarantee a 24-bit product and a 16-bit quotient. */
static s16 car_world(s16 value) __naked {
 value;
 __asm
 ld a,h
 push af
 bit 7,h
 jr z,car_world_positive
 xor a
 sub l
 ld l,a
 sbc a,a
 sub h
 ld h,a
car_world_positive:
 ld bc,#1450
 .db 0xed,0xc3
 ld a,(_car_width)
 ld c,a
 ld b,#16
car_world_divide:
 add hl,hl
 rl e
 jr c,car_world_subtract
 ld a,e
 cp c
 jr c,car_world_next
car_world_subtract:
 ld a,e
 sub c
 ld e,a
 inc l
car_world_next:
 djnz car_world_divide
 ld d,h
 ld e,l
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
s16 projection_x,projection_y,projection_base;
u16 projection_y_cursor,projection_model;
u8 projection_left,projection_count,projection_horizon;
s16 player_body_lift;
/* Same Q12 vertices as the C reference; stream without per-vertex C indexing. */
static void car_project(void) __naked {
 __asm
 push ix
 push iy
 ld ix,(_projection_model)
 ld iy,#_car_px
 ld hl,#_car_py
 ld (_projection_y_cursor),hl
 ld a,(_car_draw_id)
 cp #254
 ld a,#52
 jr nz,project_vertex_count
 ld a,#92
project_vertex_count:
 ld (_projection_count),a
project_vertex_loop:
 ld l,2(ix)
 ld h,#0
 add hl,hl
 ld bc,(_projection_base)
 add hl,bc
 bit 7,h
 jr nz,project_near
 ld a,h
 or a
 jr nz,project_reciprocal
 ld a,l
 cp #13
 jr c,project_near
project_reciprocal:
 add hl,hl
 ld bc,#0x0400
 add hl,bc
 ld e,(hl)
 inc hl
 ld d,(hl)
 jr project_scale
project_near:
 ld de,#7680
project_scale:
 ld (_car_scale),de
 ld l,0(ix)
 ld h,#0
 bit 7,l
 jr z,project_x_sign
 dec h
project_x_sign:
 add hl,hl
 add hl,hl
 ld a,(_projection_left)
 or a
 jr nz,project_x_side
 xor a
 sub l
 ld l,a
 sbc a,a
 sub h
 ld h,a
project_x_side:
 ld bc,(_projection_x)
 add hl,bc
 call _car_q12
 ld hl,#128
 add hl,de
 ld 0(iy),l
 ld 1(iy),h
 ld a,l
 out (IO_GEO_DATA),a
 ld a,h
 out (IO_GEO_DATA),a
 ld l,1(ix)
 ld h,#0
 add hl,hl
 add hl,hl
 ld a,(_car_draw_id)
 cp #254
 jr nz,project_suspension_done
 ld a,(_projection_count)
 cp #33
 jr c,project_suspension_done
 ld bc,(_player_body_lift)
 add hl,bc
project_suspension_done:
 ld bc,(_projection_y)
 add hl,bc
 call _car_q12
 ld a,(_projection_horizon)
 ld l,a
 ld h,#0
 or a
 sbc hl,de
 ld de,(_projection_y_cursor)
 ld a,l
 ld (de),a
 inc de
 ld a,h
 ld (de),a
 inc de
 ld (_projection_y_cursor),de
 xor a
 sub l
 out (IO_GEO_DATA),a
 sbc a,a
 sub h
 out (IO_GEO_DATA),a
 ld a,#1
 out (IO_GEO_DATA),a
 xor a
 out (IO_GEO_DATA),a
 inc ix
 inc ix
 inc ix
 inc iy
 inc iy
 ld a,(_projection_count)
 dec a
 ld (_projection_count),a
 jr z,project_complete
 and #7
 call z,_bgm_poll
 jp project_vertex_loop
project_complete:
 pop iy
 pop ix
 ret
 __endasm;
}
extern volatile u8 player_pose;
u8 player_projection_cached;
const u8 *player_vertex_stream;
static void player_stream_vertices(void) __naked {
 __asm
 ld hl,(_player_vertex_stream)
 ld c,#IO_GEO_DATA
 ld b,#0
 otir
 call _bgm_poll
 ld b,#0
 otir
 call _bgm_poll
 ld b,#40
 otir
 ret
 __endasm;
}
static void player_project_cached(void){
 u8 lift_slot=4,slot;
 const u8 *p;
 switch(player_body_lift){
 case -12:lift_slot=0;break;case -8:lift_slot=1;break;
 case -6:lift_slot=2;break;case -4:lift_slot=3;break;
 case 4:lift_slot=5;break;case 6:lift_slot=6;break;
 case 8:lift_slot=7;break;case 12:lift_slot=8;break;
 }
 slot=player_pose*9+lift_slot;
 *((volatile u8*)0x6000)=216+(slot>>3);
 p=(const u8*)(0x6000+(u16)(slot&7)*920);
 memcpy(car_px,p,184);memcpy(car_py,p+184,184);
 if(player_projection_cached!=slot+1){
  player_vertex_stream=p+368;
  road_index=0x68;road_data=1; /* VADDR_H: private vertices 256..347. */
  road_index=0x40;road_data=0;road_index=0x50;
  player_stream_vertices();
  road_index=0x68;road_data=0;
  player_projection_cached=slot+1;
 }
 road_word(0x54,256); /* VFIRST selects the untouched resident player mesh. */
}
static void draw_car_model(u8 variant,u8 clip){
 projection_horizon=camera_mode?130:78;
 projection_model=car_draw_id==254?0x3dd4:(variant==3?(camera_mode?0xf79c:0xf700):(camera_mode?0x3dd4:0x3c00)+(u16)variant*156);
 if(car_draw_id==254){gfx_texture_window(80,896,127,991);road_word(0x60,80);road_word(0x62,896);}
 else {gfx_texture_window(0,212,255,255);road_word(0x60,0);road_word(0x62,212);}road_index=0x64;road_data=0;
 road_word(24,1);road_word(26,0);road_word(28,0);road_word(30,1);
 road_word(34,clip<view_bottom?clip:view_bottom);
 road_index=0x40;road_data=0;road_index=0x50;
 if(car_draw_id==254)player_project_cached();else car_project();
 road_index=0x42;road_data=car_draw_id==254?92:52;
 road_index=0x56;road_data=((variant&1)<<7)+(projection_base<13?64:0);road_data=1+(variant>>1);
 if(variant==3)road_word(0x56,projection_base<13?832:768);
 if(car_draw_id==254){road_word(0x56,640);}
 road_index=0x59;road_data=car_draw_id==254?PLAYER_FACE_COUNT:(projection_base<13?46:50);
 road_index=0x45;road_data=0;road_word(0x46,page_y());
 road_index=0x48;road_data=7;while(road_index&1){bgm_poll();} /* Next VDP submit waits; CPU setup may overlap its final span. */
 if(car_draw_id==254)road_word(0x54,0);
}
extern u8 sea_crest;
void draw_one_traffic(u8 i){
 s16 bx,by,z,scale_base;long rear_x;
 u8 left,w,variant;

 if(!traffic_visible[i])return;
 /* The forward road is clipped at the crest: never draw a car over the sea. */
 if(camera_mode&&traffic_screen_y[i]<sea_crest)return;
 w=traffic_width[i];if(!w)return;
 car_width=w;bx=car_world(traffic_screen_x[i]-128);
 by=car_world((camera_mode?130:78)-traffic_screen_y[i]);
 scale_base=(s16)(traffic_gap[i]<<2)/4;scale_base*=5;if(camera_mode)scale_base+=300;z=scale_base*5;left=bx>0;variant=i==4?3:i%3;


 if(z+1900<=64)return;
 /* Behind the driver, let the centre leave the edge without enlarging
  * the body into the chase lens. Continuous at the driver plane. */
 if(camera_mode&&scale_base<300){
  if(z<=0)return;
  rear_x=(long)bx*1500/z;
  if(rear_x>4096||rear_x< -4096)return;
  bx=(s16)rear_x;scale_base=300;z=1500;
 }
 /* Conservative whole-body rejection. Four-pixel margin covers Q12 rounding. */
 if(bx>384 && (long)(bx-384)*120>(long)(z+1900)*132)return;
 if(bx< -384 && (long)(-bx-384)*120>(long)(z+1900)*132)return;
 car_draw_id=i;

 projection_x=bx;projection_y=by;projection_base=scale_base;projection_left=left;
 draw_car_model(variant,traffic_clip[i]);
}
extern s16 steering_velocity;
extern volatile u16 distance,speed;
volatile u8 player_pose;
static const s8 suspension_lift[8]={0,8,12,8,0,-8,-12,-8};
void draw_player_car(void){
 u8 pose=0;
 if(steering_velocity>8)pose=steering_velocity>24?2:1;
 if(steering_velocity< -8)pose=steering_velocity< -24?4:3;
 player_pose=pose;
 /* Sprung body moves less than one pixel; wheel vertices remain on the road.
  * Distance-driven phase freezes when stopped, regardless of frame rate. */
 player_body_lift=speed?suspension_lift[(distance>>3)&7]:0;
 if(speed<64)player_body_lift/=2;
 car_draw_id=254;
 gfx_fill(104,page_y()+190,48,1,12);
 gfx_fill(99,page_y()+191,58,2,12);
 gfx_fill(104,page_y()+193,48,1,12);
 projection_x=0;projection_y=-500;projection_base=290;projection_left=0;
 draw_car_model(0,212);
}
#pragma restore
