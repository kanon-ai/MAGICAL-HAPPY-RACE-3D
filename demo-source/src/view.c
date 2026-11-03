/* View/vehicle code in the main page-0 RAM segment, separate from BGM RAM. */
#include "hardware.h"
#include "route_config.h"
#include <string.h>
#include "view.h"
extern u16 traffic_gap[5];
extern s16 traffic_screen_x[5],traffic_screen_y[5];
extern u8 traffic_clip[5],traffic_width[5],traffic_visible[5];
__sfr __at(IO_GEO_INDEX) car_index;
__sfr __at(IO_GEO_DATA) car_data;
#define road_index car_index
#define road_data car_data
volatile u8 camera_mode;
u8 view_bottom;
u8 view_factor;

static const u8 view_scales[256]={255,254,252,250,247,245,243,241,239,238,236,234,232,230,228,227,225,223,222,220,218,217,215,214,212,211,209,208,206,205,203,202,201,199,198,197,195,194,193,192,190,189,188,187,186,184,183,182,181,180,179,178,177,176,175,174,173,172,171,170,169,168,167,166,165,164,163,162,161,161,160,159,158,157,156,155,155,154,153,152,152,151,150,149,148,148,147,146,146,145,144,143,143,142,141,141,140,139,139,138,137,137,136,136,135,134,134,133,133,132,131,131,130,130,129,129,128,127,127,126,126,125,125,124,124,123,123,122,122,121,121,120,120,119,119,118,118,117,117,116,116,116,115,115,114,114,113,113,112,112,112,111,111,110,110,110,109,109,108,108,108,107,107,106,106,106,105,105,105,104,104,103,103,103,102,102,102,101,101,101,100,100,100,99,99,99,98,98,98,97,97,97,96,96,96,95,95,95,95,94,94,94,93,93,93,93,92,92,92,91,91,91,91,90,90,90,89,89,89,89,88,88,88,88,87,87,87,87,86,86,86,86,85,85,85,85,84,84,84,84,83,83,83,83,82,82,82,82,82,81,81,81,81,80,80,80};
static const u8 view_widths[256]={0,1,2,3,4,5,6,7,7,8,9,10,11,12,12,13,14,15,16,16,17,18,18,19,20,21,21,22,23,23,24,24,25,26,26,27,27,28,29,29,30,30,31,31,32,32,33,33,34,34,35,35,36,36,37,37,38,38,39,39,40,40,40,41,41,42,42,42,43,43,44,44,44,45,45,46,46,46,47,47,47,48,48,48,49,49,49,50,50,50,51,51,51,52,52,52,53,53,53,53,54,54,54,55,55,55,55,56,56,56,56,57,57,57,57,58,58,58,58,59,59,59,59,60,60,60,60,61,61,61,61,62,62,62,62,62,63,63,63,63,63,64,64,64,64,64,65,65,65,65,65,66,66,66,66,66,67,67,67,67,67,67,68,68,68,68,68,68,69,69,69,69,69,69,70,70,70,70,70,70,71,71,71,71,71,71,71,72,72,72,72,72,72,72,73,73,73,73,73,73,73,74,74,74,74,74,74,74,74,75,75,75,75,75,75,75,75,76,76,76,76,76,76,76,76,77,77,77,77,77,77,77,77,77,78,78,78,78,78,78,78,78,78,79,79,79,79,79,79,79,79,79,79,80,80,80};
static const s8 view_lifts[256]={0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-2,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-3,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-4,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5,-5};
/* Camera is 1500 world units behind and 100 units below the driver's eye.
 * Exact signed Q8 multiply; use the same transform for all scene anchors. */
static s16 view_scale(s16 value) __naked {
 value;
 __asm
 ld a,h
 push af
 bit 7,h
 jr z,view_positive
 xor a
 sub l
 ld l,a
 sbc a,a
 sub h
 ld h,a
view_positive:
 ld a,(_view_factor)
 ld c,a
 ld b,#0
 .db 0xed,0xc3
 ld d,e
 ld e,h
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
u8 view_width(u8 width){return view_widths[width];}
s16 view_x(s16 x,u8 width){view_factor=view_scales[width];return 128+view_scale(x-128);}
s16 view_y(s16 y,u8 width){view_factor=view_scales[width];return 130+view_scale(y-78)+view_lifts[width];}
#include "traffic_mesh.h"

extern volatile u8 route_piece,tunnel_cover;
extern u16 scene_pan;
extern s16 sea_extent;
extern u8 sea_crest;
void draw_sea(void){
 u8 top=camera_mode?130:78,join=sea_crest>top?sea_crest:top;
 s16 right=sea_extent>256?256:((sea_extent+3)&~3);
 if(scene_pan==256||route_piece>8){gfx_fill(0,page_y()+top,256,view_bottom-top,tunnel_cover==2?12:terrain_ground(1020));return;}
 gfx_texture_window(128,896,191,1015);
 road_word(24,1);road_word(26,0);road_word(28,0);road_word(30,1);road_word(34,view_bottom);
 road_word(0x60,128);road_word(0x62,896);road_index=0x64;road_data=0;
 road_index=0x40;road_data=224;road_index=0x50;
 road_vertex(0,top);road_vertex(256,top);road_vertex(256,join);road_vertex(0,join);
 road_vertex(0,join);road_vertex(right,join);road_vertex(right,view_bottom);road_vertex(0,view_bottom);
 road_index=0x65;road_data=112;road_index=0x53;
 road_data=0;road_data=14;road_data=64;road_data=14;
 road_data=64;road_data=14+join-top;road_data=0;road_data=14+join-top;
 road_data=0;road_data=14+join-top;road_data=right>>2;road_data=14+join-top;
 road_data=right>>2;road_data=14+view_bottom-top;road_data=0;road_data=14+view_bottom-top;
 road_word(0x54,224);road_index=0x42;road_data=8;road_word(0x56,112);
 road_index=0x59;road_data=2;road_index=0x45;road_data=0;road_word(0x46,page_y());
 road_index=0x48;road_data=7;while(road_index&1){bgm_poll();}
 road_word(0x54,0);

}

void sea_include(s16 center,u8 width){
 s16 edge=center-width-(width>>2)-6-(width>>3);
 if(edge>sea_extent)sea_extent=edge;
}

extern volatile u8 mode,keys,offroad;
extern volatile s16 player_x;
extern s16 steering_velocity,steering_fraction;
extern volatile s8 course_curve;
extern u8 distance_fraction,stage_finish_pending;
extern volatile u8 route_piece;
extern volatile u16 laps,simulation_steps;
extern volatile unsigned long simulation_ticks;
extern unsigned long simulation_fraction,simulation_previous_ticks;
extern u8 simulation_previous_mode;
extern volatile u8 simulation_frame_steps;
void load_course(void);
void step_encounters(void);
static void update_motion(void){
    s16 steering;
    if(mode!=1)return;
    if(keys&(INPUT_DOWN|INPUT_BRAKE))speed=speed>5?speed-5:0;
    else if(keys&(INPUT_UP|INPUT_FIRE)){if(speed<124)speed+=4;else speed=128;}
    else if(speed)--speed;

    steering=0;
    if(speed){
        if(keys&INPUT_LEFT)steering-=16+(speed>>2);
        if(keys&INPUT_RIGHT)steering+=16+(speed>>2);
        if(steering_velocity<steering){steering_velocity+=8;if(steering_velocity>steering)steering_velocity=steering;}
        if(steering_velocity>steering){steering_velocity-=8;if(steering_velocity<steering)steering_velocity=steering;}
        steering_fraction+=steering_velocity;
        player_x+=steering_fraction/16;steering_fraction%=16;
        /* Gentle outward drift, without binary lane changes or auto-steering. */
        if(speed>64&&!(simulation_steps&7))player_x-=course_curve/32;
    }
    if(!speed){steering_velocity=0;steering_fraction=0;}
    offroad=player_x>64||player_x< -64;
    if(player_x>100){player_x=100;steering_velocity=0;}if(player_x< -100){player_x=-100;steering_velocity=0;}
    if(offroad&&speed>64)speed-=3;
}
/* 1 world unit = 2.5mm; 1 distance unit = 25 world units = 62.5mm.
 * Display speed = speed*15/8 km/h. At 60 movement checks/s, advance is
 * speed*5/36 distance units/check. The remainder preserves exact speed. */
volatile u8 simulation_substep;
static const u8 movement_whole[129]={0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,2,2,2,2,2,2,2,3,3,3,3,3,3,3,4,4,4,4,4,4,4,5,5,5,5,5,5,5,5,6,6,6,6,6,6,6,7,7,7,7,7,7,7,8,8,8,8,8,8,8,9,9,9,9,9,9,9,10,10,10,10,10,10,10,10,11,11,11,11,11,11,11,12,12,12,12,12,12,12,13,13,13,13,13,13,13,14,14,14,14,14,14,14,15,15,15,15,15,15,15,15,16,16,16,16,16,16,16,17,17,17,17,17,17};
static const u8 movement_remainder[129]={0,5,10,15,20,25,30,35,4,9,14,19,24,29,34,3,8,13,18,23,28,33,2,7,12,17,22,27,32,1,6,11,16,21,26,31,0,5,10,15,20,25,30,35,4,9,14,19,24,29,34,3,8,13,18,23,28,33,2,7,12,17,22,27,32,1,6,11,16,21,26,31,0,5,10,15,20,25,30,35,4,9,14,19,24,29,34,3,8,13,18,23,28,33,2,7,12,17,22,27,32,1,6,11,16,21,26,31,0,5,10,15,20,25,30,35,4,9,14,19,24,29,34,3,8,13,18,23,28};
static void move_player_substep(void){
 u8 move=movement_whole[speed];
 distance_fraction+=movement_remainder[speed];
 if(distance_fraction>=36){distance_fraction-=36;++move;}
 distance+=move;
 if(distance>=16384){
  if(route_piece<ROUTE_LAST_PIECE){distance-=16384;++route_piece;}
  else {distance=16383;++laps;speed=0;mode=3;stage_finish_pending=1;}
 }
}

/* Native validation hook: one complete movement/traffic/collision step. */
void simulation_step_done(void){++simulation_steps;}
/* Physics needs only the current curve. Full scenery/profile transfer is
 * once per displayed frame, after all fixed steps have completed. */
static void load_motion_curve(void){
 u16 phase=(distance>>2)&4095;
 *((volatile u8*)0x6000)=251;
 course_curve=*((const s8*)(0x7000+phase));
}
void advance_simulation(void){
 unsigned long now,elapsed;
 bgm_poll();now=simulation_ticks;elapsed=now-simulation_previous_ticks;
 simulation_previous_ticks=now;simulation_frame_steps=0;
 if(mode!=1||simulation_previous_mode!=1){
  simulation_fraction=0;simulation_previous_mode=mode;return;
 }
 simulation_fraction+=elapsed*420UL;
 while(simulation_fraction>=3579545UL&&mode==1){
  simulation_fraction-=3579545UL;
  update_motion();
  for(simulation_substep=0;simulation_substep<2&&mode==1;++simulation_substep){
   move_player_substep();step_encounters();
  }
  load_motion_curve();
  simulation_step_done();++simulation_frame_steps;bgm_poll();
 }
 simulation_previous_mode=mode;
}
#ifdef TEST_RENDER_DELAY
/* Test ROM only: exercise multiple E6 wraps without slowing the physics CPU. */
void simulation_render_delay(void){
 u8 i;u16 start;
 for(i=0;i<2;++i){start=gfx_timer();while((u16)(gfx_timer()-start)<51136U)bgm_poll();}
}
#endif


/* Two-bit appearance decisions per stable world object, generated per segment.
 * Geometry, sorting, traffic and physical road coordinates stay unchanged. */
extern u8 profile[256];
extern void translate_left_mesh(u8 *mesh);
void apply_harbor_appearance(u16 phase);
void apply_coast_appearance(u16 phase){
 u8 i,op,kind,*p=profile+128,*mesh;
 s16 delta;
 u16 choices;
 *((volatile u8*)0x6000)=238+(route_piece&7);
 choices=*((const u16*)(0x6000+(phase<<1)));
 for(i=0;i<8;++i,p+=8){
  op=choices&3;choices>>=2;
  if(!p[7])continue;
  if(p[5]&64){if(route_piece<7){p[7]=0;continue;}op=1;}
  if((route_piece==7&&phase>=3072)||(route_piece==8&&phase<1024))op=1;
  if(!op){p[7]=0;continue;}
  kind=p[5]&7;
  if(op==2||kind==4){kind=(p[5]>>3)&3;kind=kind==0?4:(kind==1?5:7);}
  else if(op==3&&(kind==0||kind==2))kind^=2;
  /* World-encoded vegetation identity; never reflect a sorted screen slot. */
  if(route_piece>=8){
   mesh=(u8*)(0x0100+(u16)i*60);
   if(route_piece>=16){kind=(p[5]>>3)&3;kind=route_piece>=32?(kind==3?(route_piece>=40?1:5):(kind==2?2:0)):(route_piece>=24?4:(kind<2?4:(kind==2?5:7)));}
   if(p[5]&96){
    delta=*((s16*)(mesh+40));
    if((p[5]&32)||route_piece>=16)*((s16*)p)+=delta;
    translate_left_mesh(mesh);
   }
  }
  p[5]=(p[5]&248)|kind;
 }
 if(route_piece>=7)apply_harbor_appearance(phase);
}

extern volatile u8 scene_ready;

u8 route_progress(void){
 u16 step=(u16)route_piece*8+(distance>>11);
 return (step*((1024+ROUTE_STAGE_COUNT-1)/ROUTE_STAGE_COUNT))>>10;
}

void draw_night_sky_top(u16 mix){
 if(!camera_mode||route_piece<39)return;
 if(mix<256)gfx_fill(0,page_y(),256-mix,52,158);
 if(mix)gfx_fill(256-mix,page_y(),mix,52,12);
}

/* World-distance terrain approach; camera motion cannot drag the boundary. */
static const u8 ground_ramps[4][9]={{75,75,92,115,115,115,47,45,43},{43,47,116,91,90,73,72,64,63},{63,64,64,72,72,82,82,90,91},{91,116,121,124,125,151,184,194,9}};
u8 terrain_active;
static s16 terrain_origin;
static const u8 *terrain_ramp;
void prepare_terrain_ground(void){
 u8 stage=route_piece>>3,part=route_piece&7;
 terrain_active=0;
 if(stage<1)return;
 if(part==7&&stage<ROUTE_STAGE_COUNT-1&&distance>=14852){terrain_origin=(s16)distance-15872;}
 else if(part==0&&stage>1&&distance<768){--stage;terrain_origin=(s16)distance+512;}
 else return;
 terrain_ramp=ground_ramps[stage-1];terrain_active=1;
}
u8 terrain_ground(s16 ahead){
 s16 offset;
 if(!terrain_active)return scene_ground;
 /* Negative depth samples the rear view; its camera is not the chase camera. */
 if(camera_mode&&ahead>=0)ahead=ahead>60?ahead-60:0;
 offset=terrain_origin+(s16)ahead;
 if(offset<0)return terrain_ramp[0];
 if(offset>=1024)return terrain_ramp[8];
 return terrain_ramp[offset>>7];
}

void car_resident_init(void){
 u8 i;
 car_upload_stride=11;
 *((volatile u8*)0x6000)=195;
 for(i=0;i<6;++i){car_resident_slot=256+(u16)i*64;car_upload((const u8*)(0x6000+(u16)i*1024));}
 *((volatile u8*)0x6000)=251;
 for(i=0;i<2;++i){car_resident_slot=768+(u16)i*64;car_upload((const u8*)(0x6000+(u16)i*1024));}
 *((volatile u8*)0x6000)=215;car_upload_stride=12;road_index=0x6f;road_data=1;
 car_resident_slot=640;car_upload((const u8*)0x6000);
 road_index=0x6f;road_data=0;
 road_index=0x6c;road_data=0;road_index=0x6e;road_data=0;
 road_word(0x56,0);
}
