#include "hardware.h"
__sfr __at(IO_GEO_INDEX) road_index;
__sfr __at(IO_GEO_DATA) road_data;
extern u16 car_resident_slot;
extern u8 car_upload_stride;
void car_upload(const u8 *packet);
void road_word(u8 index,s16 value);



#include "view.h"
extern volatile u16 course_phase;
/* Preprojected opaque posts. At most four posts/eight tiny fill commands. */
static void marker_post(s16 x,s16 y,u8 width,u8 height){
 u8 cap=height>=12?2:0;
 if(x>=256||x+width<=0||y+height<=0)return;
 if(x<0){width+=x;x=0;}if(x+width>256)width=256-x;
 if(y<0){height+=y;y=0;cap=0;}
 gfx_fill(x,page_y()+y,width,height,15);
 if(cap)gfx_fill(x,page_y()+y+1,width,cap,13);
}
void draw_road_markers(void){
 const u8 *p,*base;u8 i,h,w; s16 left,right,y,shift;
 *((volatile u8*)0x6000)=222+(u8)(course_phase>>8);
 base=(const u8*)(0x6000+((course_phase&255)<<5)+(camera_mode?16:0));
 for(i=2;i;){
  p=base+(--i)*8;
  h=p[6];if(!h)continue;
  left=(s16)((u16)p[0]|((u16)p[1]<<8));right=(s16)((u16)p[2]|((u16)p[3]<<8));
  y=(s16)((u16)p[4]|((u16)p[5]<<8));shift=camera_shift(p[7]);
  w=p[7]>>5;if(!w)w=1;
  marker_post(left-shift,y,w,h);marker_post(right-shift,y,w,h);
 }
}
