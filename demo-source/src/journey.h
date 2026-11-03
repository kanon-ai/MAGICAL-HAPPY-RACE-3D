/* Journey deadline affects the grade only. Geo3D projects roadside beacons. */
__sfr __at(IO_GEO_INDEX) geo_index;
__sfr __at(IO_GEO_DATA) geo_data;
volatile u8 geo_capacity,geo_id,checkpoint,timed_out,grade;
volatile u16 geo_projections,deadline,remaining_seconds;
u16 rewarded_passes,rewarded_near;
volatile s16 beacon_x,beacon_y;
static void geo_word(u8 index,s16 value){geo_index=index;geo_data=(u8)value;geo_data=(u8)(value>>8);}
static void init_geo(void){
 u8 i;geo_index=0x49;geo_id=geo_data;geo_projections=0;
 if(geo_id!=0x20)return;
 geo_index=0x6f;geo_capacity=geo_data;
 for(i=0;i<12;++i)geo_word(i*2,(i==0||i==4||i==8)?16384:0);
 geo_word(24,120);geo_word(26,128);geo_word(28,91);
 geo_word(30,32);geo_word(32,256);geo_word(34,212);
}
static void init_journey(void){checkpoint=0;timed_out=0;deadline=0;remaining_seconds=0;grade=0;race_position=1;rival_finished=0;}
static void step_journey(void){
 if(mode!=1&&!stage_finish_pending)return;
 checkpoint=distance>>12;

}
static void draw_beacons(void){
 u16 z;u8 lo,*anchor,k; s16 x,h,bottom;
 if(geo_id!=0x20||!mode||section!=5)return;
 geo_word(24,120);geo_word(30,32);geo_word(32,256);geo_word(34,212);
 z=900+(159-distance%160)*25;
 k=traffic_scale_lut[z/25];anchor=profile+192+(u16)k*4;
 geo_word(26,128+(s8)anchor[0]);geo_word(28,anchor[1]);
 geo_word(0x24,2200-player_x*23-(camera_mode?0:160));geo_word(0x26,1700);geo_word(0x28,z);
 geo_index=0x30;lo=geo_data;beacon_x=(s16)((u16)lo|((u16)geo_data<<8));
 lo=geo_data;beacon_y=(s16)((u16)lo|((u16)geo_data<<8));++geo_projections;
 x=beacon_x;bottom=anchor[1];if(bottom>anchor[3])bottom=anchor[3];if(camera_mode){beacon_x=view_x(beacon_x,anchor[2]);beacon_y=view_y(beacon_y,anchor[2]);bottom=view_y(bottom,anchor[2]);x=beacon_x;}if(bottom>view_bottom)bottom=view_bottom;h=bottom-beacon_y;
 if(h>0&&x>=0&&x<256){rect(x,beacon_y,2,h,COL_METAL);rect(x-2,beacon_y,6,2,COL_WHITE);}
}
