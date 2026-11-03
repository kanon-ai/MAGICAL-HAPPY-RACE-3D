#include "hardware.h"
#include "route_config.h"
#include "view.h"
/* Two unused atlas regions hold the incoming panorama. No visible tile is
 * overwritten until the sideways reveal has completely finished. */
static void sky_part(u16 sx,u16 dx,u16 y,u16 width,u8 incoming){
 u16 first=256-sx;
 if(first>width)first=width;
 if(incoming){
  gfx_blit(sx,590,dx,y,first,60,0);gfx_blit(sx,720,dx,y+60,first,18,0);
  if(width>first){gfx_blit(0,590,dx+first,y,width-first,60,0);gfx_blit(0,720,dx+first,y+60,width-first,18,0);}
 }else{
  gfx_blit(sx,512,dx,y,first,78,0);
  if(width>first)gfx_blit(0,512,dx+first,y,width-first,78,0);
 }
}
void draw_scene_sky(u16 pan,u16 y,u16 mix){
 if(mix<256)sky_part((pan+mix)&255,0,y,256-mix,0);
 if(mix)sky_part(pan,256-mix,y,mix,1);
}

extern volatile u8 route_piece,tunnel_cover,scene_rows,scene_ready;
extern u8 profile[256];
u8 scene_target;
u16 atlas_rows;
extern volatile u16 distance;
u16 scene_pan;
extern u8 beach_factor;
static const u8 scene_sky_banks[ROUTE_STAGE_COUNT]={0,252,246,144,153,164};
static const u8 scene_atlas_banks[ROUTE_STAGE_COUNT]={0,128,136,147,156,167};
u8 scene_ground;
static const u8 scene_ground_colors[ROUTE_STAGE_COUNT]={43,75,43,63,91,9};
static u8 upcoming_scene(void){
 u8 target=(route_piece+2)>>3;
 return target<ROUTE_STAGE_COUNT?target:ROUTE_STAGE_COUNT-1;
}
void update_scene_transition(void){
 u8 target=upcoming_scene(),boundary=target<<3;
 tunnel_cover=0;scene_pan=0;beach_factor=0;
 scene_ground=scene_ground_colors[route_piece>>3];
 prepare_terrain_ground();
 if(route_piece==7&&distance>=8192)beach_factor=distance<12288?(distance-8192)>>5:128;
 if(route_piece==8&&distance<4096)beach_factor=128-(distance>>5);
 if(!target)return;
 if(route_piece==boundary-1&&distance>=14336)scene_pan=(distance-14336)>>4;
 if(route_piece==boundary)scene_pan=distance<2048?128+(distance>>4):256;
 if(route_piece>boundary)scene_pan=256;
}

u8 beach_factor;
u16 beach_extra;

void translate_left_mesh(u8 *mesh){
 u8 j,*v=mesh;
 s16 *d=(s16*)(mesh+40);
 for(j=0;j<8;++j,v+=5) *((s16*)v)+=*d++;
}

/* Bounded streams: 512 panorama bytes and 512 atlas bytes at most per frame.
 * No visible old object uses the atlas once the approach-clearance mask ends. */
void unpack_atlas_row(u8 first,u8 row);
void stream_next_scene(void){
 u8 n,bank,target=upcoming_scene(),approach=(target<<3)-1;
 if(!target)return;
 if(scene_target!=target){scene_target=target;scene_rows=scene_ready=0;atlas_rows=0;}
 if(!scene_ready){
  bank=scene_sky_banks[target];
  for(n=0;n<2&&scene_rows<78;++n){
   *((volatile u8*)0x6000)=bank+(scene_rows>>5);
   gfx_upload_begin(scene_rows<60?590+scene_rows:660+scene_rows);
   gfx_upload_256((const u8*)(0x6000+((u16)(scene_rows&31)<<8)));
   ++scene_rows;bgm_poll();
  }
  if(scene_rows==78)scene_ready=1;
 }
 if(scene_ready==1&&scene_pan==256){
  gfx_blit(0,590,0,512,256,60,0);gfx_blit(0,720,0,572,256,18,0);scene_ready=2;
 }
 if((route_piece>approach||(route_piece==approach&&distance>=6144))&&atlas_rows<256){
  for(n=0;n<2&&atlas_rows<256;++n){
   unpack_atlas_row(scene_atlas_banks[target],(u8)atlas_rows);
   gfx_upload_begin(768+atlas_rows);
   gfx_upload_256((const u8*)0xF400);
   ++atlas_rows;bgm_poll();
  }
 }
}


/* Decode one independent atlas row into the existing course scratch buffer.
 * Called after the course record has been copied to its persistent buffers. */
void unpack_atlas_row(u8 first,u8 row){
 const u8 *p;u8 bank,token,n,value;u16 address,total=0;u8 *out=(u8*)0xF400;
 *((volatile u8*)0x6000)=first;
 p=(const u8*)(0x6000+(u16)row*3);
 bank=*p++;address=*p++;address|=(u16)*p<<8;
 *((volatile u8*)0x6000)=bank;p=(const u8*)address;
 while(total<256){
  token=*p++;n=(token&127)+1;total+=n;
  if(token&128){value=*p++;do{*out++=value;}while(--n);}
  else {do{*out++=*p++;}while(--n);}
 }
}
