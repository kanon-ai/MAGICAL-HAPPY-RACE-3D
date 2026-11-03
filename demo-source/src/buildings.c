#include "hardware.h"
#include "view.h"
#include "palette.h"
__sfr __at(IO_GEO_INDEX) road_index;
__sfr __at(IO_GEO_DATA) road_data;
void draw_building(u8 slot,u8 kind,u8 clip){
 u8 j,*p=(u8*)(0x0100+(u16)slot*60),origin=(kind==2)?128:0;
 s16 x,y;
 if(camera_mode)clip=view_y(clip,p[4]);
 if(clip>view_bottom)clip=view_bottom;
 road_word(0x56,kind==6?132:128);
 gfx_texture_window(origin,768,origin+77,895);
 road_word(24,1);road_word(26,0);road_word(28,0);road_word(30,1);road_word(34,clip);
 road_word(0x60,origin);road_word(0x62,768);road_index=0x64;road_data=0;
 road_index=0x40;road_data=0;road_index=0x50;
 for(j=0;j<12;++j,p+=5){
  x=(s16)((u16)p[0]|((u16)p[1]<<8));y=(s16)((u16)p[2]|((u16)p[3]<<8));
  if(camera_mode){x=view_x(x,p[4]);y=view_y(y,p[4]);}
  road_vertex(x-camera_shift((camera_mode?view_width(p[4]):p[4])>>1),y);
 }
 road_index=0x42;road_data=12;
 road_index=0x59;road_data=4;road_index=0x45;road_data=0;road_word(0x46,page_y());
 road_index=0x48;road_data=7;while(road_index&1){bgm_poll();} /* Next VDP submit waits; CPU setup may overlap its final span. */

}
