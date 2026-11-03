#pragma save
#pragma opt_code_size
/* A small reflected rear camera, using the same world path and actual traffic.
 * Render to an isolated 88x32 scratch tile; the main view is never used as a mirror.
 */
#define MIRROR_Y 660 /* Retired rank-label tile, below sky and above font. */
volatile u8 mirror_count,mirror_mask;
u8 mirror_bottom;
volatile s16 mirror_x[TRAFFIC_COUNT],mirror_y[TRAFFIC_COUNT];
volatile u8 mirror_w[TRAFFIC_COUNT];
static const u16 rear_depth[8]={32,48,72,104,160,240,360,512};
static void mirror_rect(s16 x,s16 y,s16 w,s16 h,u8 color){
 if(x<0){w+=x;x=0;}if(y<0){h+=y;y=0;}
 if(x+w>88)w=88-x;if(y+h>mirror_bottom)h=mirror_bottom-y;
 if(w>0&&h>0)gfx_fill(x,MIRROR_Y+y,w,h,color);
}
static const u8 mirror_faces[132]={0,1,7,6,0,0,0,0,0,0,15,1,4,10,7,0,0,0,0,0,0,27,4,5,11,10,0,0,0,0,0,0,15,2,3,9,8,0,0,0,0,0,0,15,6,7,13,12,0,0,0,0,0,0,15,7,10,16,13,0,0,0,0,0,0,27,10,11,17,16,0,0,0,0,0,0,15,8,9,15,14,0,0,0,0,0,0,15,12,13,19,18,0,0,0,0,0,0,15,13,16,22,19,0,0,0,0,0,0,27,16,17,23,22,0,0,0,0,0,0,15,14,15,21,20,0,0,0,0,0,0,15};
static void mirror_upload(void) __naked {
 __asm
 ld hl,#_mirror_faces
 ld bc,#((0x8400) | IO_GEO_DATA)
 otir
 ret
 __endasm;
}
static void mirror_resident_init(void){
 road_index=0x6c;road_data=3;road_index=0x58;road_data=128;road_index=0x52;mirror_upload();
 road_index=0x6c;road_data=0;
}
static void draw_rear_mirror(void){
 u8 k,j,i,*p,*q,rw,w,h,clip,color;
 s16 x,y,half,cx,gy,width;u16 gap,part,span;
 mirror_count=mirror_mask=0;
 if(mode==0)return;
 gfx_fill(0,MIRROR_Y,88,8,route_piece>=40?12:COL_SKY_LIGHT);
 color=terrain_ground(-256);
 gfx_fill(0,MIRROR_Y+8,44,24,route_piece>=8?color:35);gfx_fill(44,MIRROR_Y+8,44,24,color);
 road_word(24,1);road_word(26,0);road_word(28,0);road_word(30,1);road_word(32,88);road_word(34,32);
 road_index=0x40;road_data=0;road_index=0x50;
 for(j=0;j<4;++j){
  k=j==0?7:(j==1?4:(j==2?2:0));p=rear_profile+k*4;rw=p[2];
  x=44+(s8)p[0]-camera_shift(rw>>1);y=p[1];half=rw+(rw>>2);
  road_vertex(x-half-1,y);road_vertex(x-half,y);road_vertex(x-1,y);
  road_vertex(x,y);road_vertex(x+half,y);road_vertex(x+half+1,y);
 }
 road_index=0x42;road_data=24;road_word(0x56,896);
 road_index=0x59;road_data=12;road_index=0x45;road_data=0;road_word(0x46,MIRROR_Y);
 road_index=0x48;road_data=3;while(road_index&1){bgm_poll();} /* Next VDP submit waits; CPU setup may overlap its final span. */
 road_word(24,120);road_word(26,128);road_word(28,91);road_word(30,32);road_word(32,256);road_word(34,212);
 /* Signed depth order is reversed in the rear camera: farthest first. */
 for(j=TRAFFIC_COUNT;j;){
  i=traffic_order[--j];gap=(distance-traffic_z[i])&16383;
  if(gap<(camera_mode?52:80)||gap>512)continue;
  /* Clamp before subtracting: overlapping front bumpers must not wrap. */
  gap=gap<108?32:gap-76;
  k=0;while(k<7&&gap>rear_depth[k+1])++k;
  p=rear_profile+k*4;cx=(s8)p[0];gy=p[1];width=p[2];clip=p[3];
  if(k<7){
   q=p+4;part=gap-rear_depth[k];span=rear_depth[k+1]-rear_depth[k];
   cx+=interpolate((s16)(s8)q[0]-cx,(u8)part,(u8)span);
   gy+=interpolate((s16)q[1]-gy,(u8)part,(u8)span);
   width+=interpolate((s16)q[2]-width,(u8)part,(u8)span);
  }
  rw=(u8)width;x=44+cx-camera_shift(rw>>1)+(s16)traffic_lane[i]*rw/64;
  w=(u16)rw*53/100;if(w<3)w=3;h=(u16)w*4/5;if(h<3)h=3;
  y=gy;if(y-h>=clip||x+w/2<0||x-w/2>=88)continue;
  mirror_x[i]=x;mirror_y[i]=y;mirror_w[i]=w;++mirror_count;mirror_mask|=1<<i;
  mirror_bottom=clip;
  color=i%3==0?51:(i%3==1?COL_METAL:3);
  /* Front silhouette: windshield above pale headlamps, never red rear lamps. */
  if(y>clip)y=clip;
  mirror_rect(x-w/2,gy-h/2,w,y-(gy-h/2),color);
  mirror_rect(x-w/3,gy-h,w*2/3,h/2,color);
  mirror_rect(x-w/3+1,gy-h+1,w*2/3-2,h/3,COL_DARK);
  mirror_rect(x-w/2,gy-2,w,2,COL_DARK);
  mirror_rect(x-w/2+1,gy-h/2+1,w/4,1,COL_WHITE);
  mirror_rect(x+w/4,gy-h/2+1,w/4,1,COL_WHITE);
 }
 rect(160,14,92,2,COL_DARK);rect(160,48,92,2,COL_DARK);
 rect(160,16,2,32,COL_DARK);rect(250,16,2,32,COL_DARK);
 gfx_blit(0,MIRROR_Y,162,page_y()+16,88,32,0);
}

#pragma restore
