/* Geo3D fills connected road quads, interpolating each scanline on the device.
 * All scenery and traffic still use the same projected course anchors.
 * SCREEN8 palette 16..47 is reserved for the pavement depth ramp.
 */
#include "road_uv.h"
__sfr __at(IO_GEO_INDEX) road_index;
__sfr __at(IO_GEO_DATA) road_data;
void road_word(u8 index,s16 v){road_index=index;road_data=(u8)v;road_data=(u8)(v>>8);}
void road_vertex(s16 x,s16 y){
 road_data=(u8)x;road_data=(u8)(x>>8);y=-y;
 road_data=(u8)y;road_data=(u8)(y>>8);road_data=1;road_data=0;
}
/* SDCC call1: a in A, b in L, remaining three bytes on stack. */
static void road_face(u8 a,u8 b,u8 c,u8 d,u8 color) __naked {
 a;b;c;d;color;
 __asm
 out (IO_GEO_DATA),a
 ld a,l
 out (IO_GEO_DATA),a
 ld hl,#2
 add hl,sp
 ld a,(hl)
 out (IO_GEO_DATA),a
 inc hl
 ld a,(hl)
 out (IO_GEO_DATA),a
 inc hl
 xor a
 out (IO_GEO_DATA),a
 out (IO_GEO_DATA),a
 out (IO_GEO_DATA),a
 out (IO_GEO_DATA),a
 out (IO_GEO_DATA),a
 out (IO_GEO_DATA),a
 ld a,(hl)
 out (IO_GEO_DATA),a
 pop hl
 pop de
 inc sp
 jp (hl)
 __endasm;
}
static u8 rows[24],flags[24],widths[24];
s16 sea_extent;
u8 sea_crest;
static const u8 terrain_shade[192]={7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,7,6,6,6,6,6,6,6,6,6,6,6,6,6,5,5,5,5,5,5,5,5,5,5,5,5,5,4,4,4,4,4,4,4,4,4,4,4,4,4,3,3,3,3,3,3,3,3,3,3,3,3,3,2,2,2,2,2,2,2,2,2,2,2,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};
/* Stored width projects 1450 units; actual half-width is 1812.5 (two broad lanes). */
s16 row_center;
u8 row_screen_y;
/* Precomputed cross sections, 64 bytes per width. The exact same twelve
 * vertices are streamed using additions, with no repeated C stack arithmetic. */
extern u8 beach_factor;
extern u16 beach_extra;
void road_row(s16 center,u8 y,u8 w) __naked {
 center;y;w;
 __asm
 push ix
 ld ix,#0
 add ix,sp
 ld (_row_center),hl
 ld a,(_beach_factor)
 ld c,a
 ld a,5(ix)
 .db 0xed,0xc9
 srl h
 rr l
 srl h
 rr l
 srl h
 rr l
 srl h
 rr l
 ld (_beach_extra),hl
 ld a,4(ix)
 ld (_row_screen_y),a
 ld a,5(ix)
 rlca
 and #1
 add a,#212
 ld (0x6000),a
 ld a,5(ix)
 and #127
 ld l,a
 ld h,#0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld bc,#0x6000
 add hl,bc
 ld e,#12
row_stream:
 ld c,(hl)
 inc hl
 ld b,(hl)
 inc hl
 ld d,(hl)
 inc hl
 ld a,(hl)
 inc hl
 push hl
 or a
 ld hl,#0
 jr nz,row_absolute
 ld hl,(_row_center)
row_absolute:
 add hl,bc
 ld a,e
 cp #6
 jr z,row_beach
 cp #5
 jr nz,row_beach_done
row_beach:
 push de
 ld de,(_beach_extra)
 or a
 sbc hl,de
 pop de
row_beach_done:
 ld a,l
 out (IO_GEO_DATA),a
 ld a,h
 out (IO_GEO_DATA),a
 ld a,(_row_screen_y)
 add a,d
 ld b,a
 xor a
 sub b
 out (IO_GEO_DATA),a
 sbc a,a
 out (IO_GEO_DATA),a
 ld a,#1
 out (IO_GEO_DATA),a
 xor a
 out (IO_GEO_DATA),a
 pop hl
 dec e
 jr nz,row_stream
 pop ix
 pop hl
 pop bc
 jp (hl)
 __endasm;
}

/* The former elevated ribbons are degenerate: grounded narrow shoulders only.
 * Fixed topology, unchanged eight slots per band. Emit directly from RAM
 * code data instead of rebuilding five C arguments for every polygon. */
static const u8 road_topology[40]={
 0,0,0,0,128,4,5,17,16,254,1,2,14,13,COL_VERGE,
 3,4,16,15,COL_VERGE,2,3,15,14,128,10,11,23,22,253,
 6,1,13,18,COL_VERGE,7,6,18,19,148};
u8 road_face_base,road_face_shade,road_face_line;
static void road_band_faces(void) __naked {
 __asm
 ld hl,#_road_topology
 ld a,(_road_face_base)
 ld e,a
 ld d,#8
road_face_stream:
 ; Four indices are adjacent; the sixth face can be made degenerate.
 ld b,#4
 ld a,d
 cp #3
 jr nz,road_regular_face
 ld a,(_road_face_line)
 and #1
 jr nz,road_regular_face
 ld a,e
 out (IO_GEO_DATA),a
 out (IO_GEO_DATA),a
 out (IO_GEO_DATA),a
 out (IO_GEO_DATA),a
 inc hl
 inc hl
 inc hl
 inc hl
 jr road_face_attributes
road_regular_face:
 ld a,(hl)
 add a,e
 out (IO_GEO_DATA),a
 inc hl
 djnz road_regular_face
road_face_attributes:
 xor a
 out (IO_GEO_DATA),a
 out (IO_GEO_DATA),a
 out (IO_GEO_DATA),a
 out (IO_GEO_DATA),a
 out (IO_GEO_DATA),a
 out (IO_GEO_DATA),a
 ld a,(hl)
 inc hl
 cp #254
 jr nz,road_face_not_terrain
 ld a,(_road_face_shade)
 jr road_face_color
road_face_not_terrain:
 cp #253
 jr nz,road_face_color
 ld a,#15
road_face_color:
 out (IO_GEO_DATA),a
 dec d
 jr nz,road_face_stream
 ret
 __endasm;
}
/* V2 resident road faces 0..111. Only terrain shade and lane dashes change. */
static u8 resident_terrain[14],resident_line[14],resident_left[14];
static void road_resident_init(void){
 u8 k;
 road_index=0x58;road_data=0;road_index=0x52;
 for(k=0;k<14;++k){road_face_base=k*12;road_face_shade=40;road_face_line=1;road_band_faces();resident_terrain[k]=40;resident_line[k]=1;resident_left[k]=255;}
 /* Separate level sea backdrop, never connected to road cross sections. */
 road_index=0x58;road_data=112;road_index=0x52;road_face(224,225,226,227,128);road_face(228,229,230,231,128);
}

static void draw_road(void){
 u8 i,j,y,w=1,n=0,k,base,v0,v1;s16 dv,center=128;
 sea_extent=0;

 road_word(0x56,0);
 road_word(0x60,128);road_word(0x62,896);road_index=0x64;road_data=0;
 road_word(24,1);road_word(26,0);road_word(28,0);road_word(30,1);road_word(34,view_bottom);
 road_index=0x40;road_data=0;road_index=0x50;
 for(i=0;i<COURSE_BANDS;i+=3){
  y=band_y[i]+band_h[i]/2;
  if(y<profile[123]||!profile[(u16)i*3+1])continue;if(y>168)break;
  if(!n)y=profile[123];
  w=profile[(u16)i*3+1];
  if(camera_mode){center=view_x(128+(s8)profile[(u16)i*3],w)-camera_shift(view_width(w)>>1);y=view_y(y,w);w=view_width(w);}
  else center=128+(s8)profile[(u16)i*3]-camera_shift(w>>1);
  rows[n]=y;widths[n]=w;flags[n]=profile[(u16)i*3+2];++n;
  sea_include(center,w);
  road_row(center,y,w);
 }
 if(camera_mode){center=128+(s16)((long)(center-128)*238/w);w=238;}
 sea_crest=rows[0];
 sea_include(center,w);
 rows[n]=view_bottom;widths[n]=w;flags[n]=flags[n-1];++n;road_row(center,view_bottom,w);
 road_index=0x42;road_data=n*12;
 for(k=0;k<n-1;++k){
  bgm_poll();
  base=k*12;
  y=route_piece>=8?scene_ground:11;
  if(terrain_active)y=terrain_ground((u16)road_depth[widths[k]]<<2);
  if(resident_left[k]!=y){
   road_index=0x58;road_data=k*8+6;road_index=0x52;road_face(base+6,base+1,base+13,base+18,y);
   road_index=0x58;road_data=k*8+7;road_index=0x52;road_face(base+7,base+6,base+18,base+19,route_piece<8?148:y);
   resident_left[k]=y;
  }
  if(route_piece<8||y==43)y=40+terrain_shade[rows[k]];
  if(resident_terrain[k]!=y){
   road_index=0x58;road_data=k*8+1;road_index=0x52;
   road_face(base+4,base+5,base+17,base+16,y);resident_terrain[k]=y;
  }
  y=flags[k]&1;
  if(resident_line[k]!=y){
   road_index=0x58;road_data=k*8+5;road_index=0x52;
   if(y)road_face(base+10,base+11,base+23,base+22,COL_WHITE);
   else road_face(base,base,base,base,COL_WHITE);
   resident_line[k]=y;
  }
 }
 for(k=0;k<n-1;++k){
  bgm_poll();
  v0=16+((course_phase+road_depth[widths[k]])&15);
  dv=(s16)road_depth[widths[k+1]]-road_depth[widths[k]];
  if(dv< -15)dv=-15;if(dv>0)dv=0;v1=v0+dv;
  for(j=0;j<1;++j){
   road_index=0x65;road_data=k*8+4;road_index=0x53;
   road_data=64;road_data=v0+88;road_data=127;road_data=v0+88;
   road_data=127;road_data=v1+88;road_data=64;road_data=v1+88;
  }
  /* Existing waterline face samples a narrow foam tile, sharing road depth. */
  road_index=0x65;road_data=k*8+7;road_index=0x53;
  v0=120+((course_phase+road_depth[widths[k]])&7);
  v1=120+((course_phase+road_depth[widths[k+1]])&7);
  road_data=64;road_data=v0;road_data=127;road_data=v0;
  road_data=127;road_data=v1;road_data=64;road_data=v1;
 }
 draw_sea();
 road_index=0x42;road_data=n*12;road_word(0x56,0);
 road_index=0x59;road_data=(n-1)*8;road_index=0x45;road_data=0;road_word(0x46,page_y());
 gfx_texture_window(128,896,255,1023);
 road_index=0x48;road_data=7;while(road_index&1){bgm_poll();} /* Next VDP submit waits; CPU setup may overlap its final span. */

}
