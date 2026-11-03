/* Camera-correct cuboids: eight independently projected world-space corners.
 * Mesh pages occupy the lower half of ASCII16 banks; art uses the upper half.
 */
static void building_uv(u8 face,u8 top){
 road_index=0x65;road_data=128+face;road_index=0x53;
 u8 left=(face&3)==1?16:0,right=(face&3)==1?47:63;
 road_data=left;road_data=top;road_data=right;road_data=top;
 road_data=right;road_data=63;road_data=left;road_data=63;
}
/* V2 resident cuboid faces: facade UVs at 128, cropped shop UVs at 132. */
static void building_resident_init(void){
 u8 k,j;
 for(k=0;k<2;++k){
  road_index=0x58;road_data=128+k*4;road_index=0x52;
  road_face(3,2,6,7,COL_RUST);road_face(7,3,0,4,128);road_face(3,2,1,0,128);road_face(2,6,5,1,128);
  for(j=1;j<4;++j)building_uv(k*4+j,0);
 }
}
static void draw_building(u8 slot,u8 kind,u8 clip){
 u8 j,*p=(u8*)(0x0100+(u16)slot*60),origin=kind==2?64:(kind==6?128:(kind==1?192:0));
 u16 texture_y=kind==3?832:768;
 s16 x,y;
 if(camera_mode)clip=view_y(clip,p[4]);
 if(clip>view_bottom)clip=view_bottom;
 road_word(0x56,kind==6?132:128);
 gfx_texture_window(origin,texture_y,origin+63,texture_y+63);
 road_word(24,1);road_word(26,0);road_word(28,0);road_word(30,1);road_word(34,clip);
 road_word(0x60,origin);road_word(0x62,texture_y);road_index=0x64;road_data=0;
 road_index=0x40;road_data=0;road_index=0x50;
 for(j=0;j<8;++j,p+=5){
  x=(s16)((u16)p[0]|((u16)p[1]<<8));y=(s16)((u16)p[2]|((u16)p[3]<<8));
  if(camera_mode){x=view_x(x,p[4]);y=view_y(y,p[4]);}
  road_vertex(x-camera_shift((camera_mode?view_width(p[4]):p[4])>>1),y);
 }
 road_index=0x42;road_data=8;
 road_index=0x59;road_data=4;road_index=0x45;road_data=0;road_word(0x46,page_y());
 road_index=0x48;road_data=7;while(road_index&1){bgm_poll();} /* Next VDP submit waits; CPU setup may overlap its final span. */

}
