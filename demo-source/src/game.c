/* MAGICAL HAPPY RALLY V9968 four-course hardware-scaling prototype.
 * No host-side simulation. All gameplay, input, sound and drawing run here.
 */
#include "hardware.h"
#include "route_config.h"
#include "view.h"
#include "assets.h"
#include "palette.h"
#include "course.h"
#include "scenery.h"
#include "stages.h"

volatile u8 ready,mode,keys,offroad,section;
volatile u16 frame_counter,distance,speed,course_phase,laps;
volatile u8 route_piece;
volatile u8 scene_rows,scene_ready,tunnel_cover;
extern u8 scene_target;
extern u16 atlas_rows;
volatile s16 player_x,road_center,hill;
s16 steering_velocity,steering_fraction;
volatile s8 course_curve;
volatile u16 simulation_steps;
extern volatile unsigned long simulation_ticks;
void simulation_clock_init(void);
u8 old_keys,draw_page,profile[256],distance_fraction;
u16 loaded_phase;
volatile u8 race_mode,race_position,rival_finished;
volatile u8 stage_id,unlocked_stage,menu_stage,journey_complete;
u8 stage_finish_pending,ground_color,ground_alt,road_color,verge_color,bridge;
unsigned long stage_best[STAGE_COUNT],stage_last[STAGE_COUNT];
u8 stage_best_valid[STAGE_COUNT],stage_last_valid[STAGE_COUNT],visual_night;
static void start_stage(u8 stage);
static void build_ui(void);
static void build_ui(void);
#include "stage_stream.h"
#include "course_cache.h"
u16 page_y(void){return (u16)draw_page<<8;}
/* R800 unsigned 8x8 multiply, ED C9 = MULUB A,C. SDCC call1 passes
 * half-width in A and returns the signed 16-bit result in DE. Work with
 * the magnitude before shifting to preserve C's division toward zero.
 * This cartridge explicitly targets turbo R in R800 mode.
 */
static s16 body_camera_shift(u8 halfwidth) __naked{
    halfwidth;
    __asm
    ld c,a
    ld a,(_player_x+1)
    ld b,a
    ld a,(_player_x)
    bit 7,b
    jr z,drive_multiply
    neg
drive_multiply:
    .db 0xed,0xc9
    ; Four-lane normalization: signed product / 32, with no lost low bit.
    ld a,l
    rlca
    rlca
    rlca
    and #7
    ld e,h
    ld d,#0
    sla e
    rl d
    sla e
    rl d
    sla e
    rl d
    or e
    ld e,a
    bit 7,b
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
/* About 0.40m right-hand seat offset on a 4.53m lane; player_x remains body center. */
s16 camera_shift(u8 halfwidth){return body_camera_shift(halfwidth)+(camera_mode?0:(((u16)halfwidth*14)>>6));}
/* Exact signed interpolation. abs(delta)<=255 and 0<=part<=span<=255.
 * R800 8x8 multiply followed by an eight-step quotient, truncated toward zero. */
static s16 interpolate(s16 delta,u8 part,u8 span) __naked {
 delta;part;span;
 __asm
 push ix
 ld ix,#0
 add ix,sp
 ld a,h
 push af
 ld a,l
 bit 7,h
 jr z,interpolate_positive
 neg
interpolate_positive:
 ld c,4(ix)
 .db 0xed,0xc9
 ld c,5(ix)
 ld b,#8
interpolate_divide:
 add hl,hl
 jr c,interpolate_subtract
 ld a,h
 cp c
 jr c,interpolate_next
interpolate_subtract:
 ld a,h
 sub c
 ld h,a
 inc l
interpolate_next:
 djnz interpolate_divide
 ld e,l
 ld d,#0
 pop af
 bit 7,a
 jr z,interpolate_done
 xor a
 sub e
 ld e,a
 sbc a,a
 ld d,a
interpolate_done:
 pop ix
 pop hl
 pop bc
 jp (hl)
 __endasm;
}
void rect(s16 x,s16 y,s16 w,s16 h,u8 color){
    if(x<0){w+=x;x=0;}if(y<0){h+=y;y=0;}
    if(x+w>256)w=256-x;if(y+h>212)h=212-y;
    if(w>0&&h>0)gfx_fill(x,page_y()+y,w,h,color);
}
static void sprite(const Sprite *s,s16 x,s16 y,s16 bottom){
    s16 sx=s->x,sy=s->y,w=s->w,h=s->h;
    if(x<0){sx-=x;w+=x;x=0;}
    if(y<0){sy-=y;h+=y;y=0;}
    if(x+w>256)w=256-x;if(y+h>bottom)h=bottom-y;
    if(w>0&&h>0)gfx_blit(sx,sy,x,page_y()+y,w,h,1);
}
static void text(s16 x,s16 y,const char *p){
    while(*p){u8 c=*p++;
        if(c>=32&&c<128&&x>=0&&x<251&&y>=0&&y<205){
            const Sprite *s=&font[c-32];
            gfx_blit(s->x,s->y,x,page_y()+y,6,8,1);
        }x+=6;
    }
}
static void number(s16 x,s16 y,u16 v){
    char b[4];b[3]=0;b[2]='0'+v%10;v/=10;
    b[1]='0'+v%10;b[0]='0'+v/10;text(x,y,b);
}
void load_course(void){
    course_phase=(distance>>2)&4095;
    if(loaded_phase!=course_phase||loaded_stage!=stage_id){
        cache_read(course_phase);
        loaded_phase=course_phase;loaded_stage=stage_id;
    }
    hill=(s16)profile[123]-91;course_curve=(s8)profile[124];section=profile[126];
    ground_color=COL_GRASS;
    ground_alt=COL_GRASS;
    road_color=COL_ROAD;verge_color=COL_VERGE;
    bridge=0;

}
static void update_controls(void){
    u8 edge=keys&(u8)~old_keys;
    if(mode==0){
        race_mode=0;


        if(edge&(INPUT_FIRE|INPUT_UP))start_stage(menu_stage);
        return;
    }
    if(mode==3||mode==4){
        if(edge&INPUT_PAUSE){mode=0;menu_stage=stage_id;return;}
        if(edge&(INPUT_FIRE|INPUT_UP)){
            if(stage_id<STAGE_COUNT-1)start_stage(stage_id+1);
            else {start_stage(3);}
        }
        return;
    }
    if(edge&INPUT_VIEW){camera_mode^=1;view_bottom=camera_mode?212:168;build_ui();}
    if(edge&INPUT_PAUSE){mode=mode==2?1:2;}
    if(mode==2&&(edge&INPUT_BRAKE)){speed=0;mode=0;menu_stage=stage_id;return;}
    if(mode!=1)return;
}
extern u16 scene_pan;
void draw_scene_sky(u16 pan,u16 y,u16 mix);
static void draw_sky(void){
 u16 pan=((s8)profile[127]/3)&255;
 u16 sky_page=page_y()+(camera_mode?52:0);

 /* Distant coast is independent of the projected road crest. */
 u8 sky_height=78;
 if(camera_mode)gfx_fill(0,page_y(),256,52,route_piece>=40?12:158);
 if(scene_pan&&scene_ready==1){draw_night_sky_top(scene_pan);draw_scene_sky(pan,sky_page,scene_pan);return;}
 /* Submit the larger, disjoint piece last, then build the road while it copies. */
 if(pan&&pan<=128){gfx_blit(0,SKY_Y,256-pan,sky_page,pan,sky_height,0);gfx_blit(pan,SKY_Y,0,sky_page,256-pan,sky_height,0);}
 else if(pan){gfx_blit(pan,SKY_Y,0,sky_page,256-pan,sky_height,0);gfx_blit(0,SKY_Y,256-pan,sky_page,pan,sky_height,0);}
 else gfx_blit(0,SKY_Y,0,sky_page,256,sky_height,0);
 /* The road pass covers every ground pixel; avoid painting it twice. */

}
#include "scene_transition.h"
#include "road_raster.h"
#include "buildings.h"
#include "encounters.h"
#include "rear_mirror.h"
#include "lap_clock.h"
#include "journey.h"
unsigned long simulation_fraction,simulation_previous_ticks;
u8 simulation_previous_mode;
volatile u8 simulation_frame_steps;
/* 30 fixed motion steps per real second: E6 ticks * 14 * 30 / 3579545.
 * Every catch-up step includes traffic and collision detection, not a jump. */

static void draw_objects(void){
    u8 i,*p=profile+128,size,kind,ti=0,car_id;
    s16 x,y,clip;
    car_draw_id=255;
    if(tunnel_cover==2){for(i=0;i<TRAFFIC_COUNT;++i)draw_one_traffic(traffic_order[i]);return;}
    for(i=0;i<8;++i,p+=8){
        if(!p[7])continue;
        while(ti<TRAFFIC_COUNT){
            car_id=traffic_order[ti];
            if(traffic_visible[car_id]&&traffic_width[car_id]>p[7])break;
            draw_one_traffic(car_id);++ti;
        }
        kind=p[5]&7;clip=p[6];
        /* Cuboids use their independently projected corners, not sprite x/y/size. */
        if(kind!=4&&kind!=5&&kind!=7){
            draw_building(i,kind,clip);continue;
        }
        x=(s16)((u16)p[0]|((u16)p[1]<<8));
        y=(s16)((u16)p[2]|((u16)p[3]<<8));
        size=p[4];
        if(camera_mode){x=view_x(x,p[7]);y=view_y(y,p[7]);clip=view_y(clip,p[7]);size=(u16)size*view_width(p[7])/p[7];}
        x-=camera_shift((camera_mode?view_width(p[7]):p[7])>>1);
        {
            u8 h=size+1,w,sw=78,ox=0;u16 sy=896,step;
            if(kind==5){h=(h>>1)+(h>>2);if(!h)h=1;w=h;sw=64;ox=192;step=scale_step[h]>>1;}
            else if(kind==7){h=(h+3)>>2;if(!h)h=1;w=(u16)h*8/3;sw=64;ox=192;sy=960;step=(scale_step[h]>>3)+(scale_step[h]>>4);}
            else {w=scenery_width[h];step=scale_step[h];}
            gfx_scaled(ox,sy,sw,w,h,step,x-w/2,y-h,clip,page_y(),p[5]&128);
        }
    }
    while(ti<TRAFFIC_COUNT){draw_one_traffic(traffic_order[ti]);++ti;}
}
u16 ui_speed[2],ui_remaining[2],chase_speed_cached;
u8 ui_progress[2];
static void build_ui(void){
 chase_speed_cached=0;
 for(draw_page=0;draw_page<2;++draw_page){
  gfx_blit(0,468,0,page_y()+168,256,44,0);
  gfx_blit(192,704,176,page_y()+181,30,8,1);
  ui_speed[draw_page]=ui_remaining[draw_page]=65535;ui_progress[draw_page]=255;
 }
 draw_page=1;
}
static void start_stage(u8 stage){
    if(scene_target||atlas_rows)cache_stage=255;
    stage_id=stage;menu_stage=stage;mode=1;
    speed=0;distance=0;distance_fraction=0;route_piece=0;scene_rows=scene_ready=tunnel_cover=scene_target=0;atlas_rows=0;player_x=-40;steering_velocity=0;steering_fraction=0;laps=0;offroad=0;
    stage_finish_pending=0;
    init_encounters();init_lap_clock();init_journey();
    lap_best_tenths=stage_best[stage];lap_best_valid=stage_best_valid[stage];
    if(cache_stage!=stage){
        rect(16,70,224,38,COL_DARK);
        text(47,78,"LOADING NEXT STAGE");text(47,94,"PLEASE WAIT...");
        gfx_flip(draw_page);draw_page^=1;
        stage_visuals(stage);cache_prepare(stage);
    }
    build_ui();build_encounter_ui();load_course();
    /* Do not charge stage loading / UI creation to the driving clock. */
    lap_previous_timer=read_lap_timer();lap_previous_mode=0;
}
static void finish_stage(void){
    if(!stage_finish_pending)return;
    stage_finish_pending=0;
    stage_last[stage_id]=lap_last_tenths;stage_last_valid[stage_id]=lap_last_valid;
    stage_best[stage_id]=lap_best_tenths;stage_best_valid[stage_id]=lap_best_valid;
    if(stage_id<STAGE_COUNT-1){if(unlocked_stage<stage_id+1)unlocked_stage=stage_id+1;}
    else {journey_complete=1;mode=4;}
}
static void draw_stage_panel(void){
 char time[13];

 if(mode==0){
  rect(20,36,216,102,COL_DARK);text(38,43,"PUBLIC ROAD / COCKPIT");
  text(62,65,"< COAST DRIVE >");
  text(38,84,"5 CARS / OPEN COAST");
  text(38,103,"LEFT/RIGHT: STEER");text(38,119,"SPACE: START");
 }else if(mode==3||mode==4){
  rect(25,39,206,97,COL_DARK);
  text(56,47,"DRIVE COMPLETE");
  format_lap_time(time,stage_last[stage_id]);text(45,69,"TIME");text(88,69,time);
  text(45,86,"CONTACTS");number(150,86,hits);
  text(45,107,"SPACE: DRIVE AGAIN");text(45,121,"ESC: MODE SELECT");
 }
}
static void draw_ui(void){
 u16 shown_speed=(speed*15)>>3;
 if(camera_mode){
  if(chase_speed_cached!=shown_speed+1){
   u8 saved_page=draw_page;
   /* Retired rank tile x128..177,y650..665; mirror uses x0..87. */
   draw_page=2;rect(128,138,50,16,COL_DARK);
   number(132,142,shown_speed);text(153,142,"KMH");draw_page=saved_page;
   chase_speed_cached=shown_speed+1;
  }
  gfx_blit(128,650,4,page_y()+190,50,16,0);
 }else{
 u16 remaining=(u16)(((unsigned long)(ROUTE_LAST_PIECE-route_piece)*16384UL+16383-distance+1599)/1600);
 u8 progress=route_progress();
 /* The road stops at y=168. Keep each page's static dashboard resident. */
 if(ui_speed[draw_page]!=shown_speed){
  gfx_blit(42,486,42,page_y()+186,18,8,0);number(42,186,shown_speed);ui_speed[draw_page]=shown_speed;
 }
 if(ui_remaining[draw_page]!=remaining){
  gfx_blit(176,494,176,page_y()+194,18,8,0);number(176,194,remaining);ui_remaining[draw_page]=remaining;
 }
 if(ui_progress[draw_page]!=progress){
  rect(173,205,72,2,COL_DARK);rect(173,205,progress,2,COL_SKY_LIGHT);ui_progress[draw_page]=progress;
 }
 }
 /* Compact information at the windshield edge, leaving the road clear. */
 /* Course title and its background were removed at user request. */

 draw_rear_mirror();
 if(notice_timer&&notice==2){
  rect(64,52,136,12,COL_DARK);
  text(70,54,contact_side==1?"CONTACT / FRONT LEFT":(contact_side==2?"CONTACT / FRONT RIGHT":"CONTACT / FRONT"));

 }
 if(mode==2){rect(49,58,158,43,COL_DARK);text(109,64,"PAUSE");text(61,78,"ESC: RESUME");text(61,90,"X: MODE SELECT");}
 draw_stage_panel();
}
/* Debug breakpoint hook: front VRAM page is complete and visible here. */
void frame_done(void){++frame_counter;}
volatile u16 ticks_update,ticks_sky,ticks_road,ticks_objects,ticks_ui,ticks_flip;
#ifdef TEST_RENDER_DELAY
void simulation_render_delay(void);
#endif
void main(void){
    u8 i;
    u16 t;
    simulation_clock_init();simulation_steps=0;
    simulation_fraction=0;simulation_previous_mode=0;simulation_previous_ticks=0;
    camera_mode=0;view_bottom=168;
    ready=0;mode=0;frame_counter=0;distance=0;speed=0;player_x=-40;
    distance_fraction=0;route_piece=0;scene_rows=scene_ready=tunnel_cover=scene_target=0;atlas_rows=0;steering_velocity=0;steering_fraction=0;laps=0;keys=0;old_keys=0;draw_page=1;
    loaded_phase=65535;loaded_stage=255;offroad=0;
    stage_id=3;menu_stage=3;unlocked_stage=3;journey_complete=0;stage_finish_pending=0;
    visual_night=0;race_mode=0;race_position=1;rival_finished=0;
    for(i=0;i<STAGE_COUNT;++i){stage_best[i]=0;stage_last[i]=0;stage_best_valid[i]=0;stage_last_valid[i]=0;}
    for(i=0;i<96;++i){font[i].x=(i&31)*6;font[i].y=696+(i>>5)*8;font[i].w=6;font[i].h=8;}
    init_encounters();
    init_lap_clock();init_journey();init_geo();
    gfx_init();cache_init();car_resident_init();mirror_resident_init();road_resident_init();building_resident_init();stage_visuals(3);cache_prepare(3);
    build_ui();build_encounter_ui();load_course();
    bgm_start();
    ready=0xa5;
    for(;;){
        t=gfx_timer();keys=input_read();update_controls();advance_simulation();load_course();
        update_scene_transition();prepare_traffic();
        step_lap_clock();step_journey();
        finish_stage();
        engine_sound(speed,offroad,mode!=1);
        ticks_update=gfx_timer()-t;t=gfx_timer();
        draw_sky();ticks_sky=gfx_timer()-t;t=gfx_timer();
        draw_road();ticks_road=gfx_timer()-t;t=gfx_timer();
        draw_road_markers();draw_objects();draw_beacons();if(camera_mode&&mode)draw_player_car();gfx_wait();ticks_objects=gfx_timer()-t;t=gfx_timer();
        draw_ui();gfx_wait();stream_next_scene();ticks_ui=gfx_timer()-t;t=gfx_timer();
#ifdef TEST_RENDER_DELAY
        simulation_render_delay();
#endif
        gfx_flip(draw_page);ticks_flip=gfx_timer()-t;frame_done();draw_page^=1;old_keys=keys;
    }
}
