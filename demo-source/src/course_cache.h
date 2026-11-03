/* ASCII16 upper-half profiles: banks 64..191, 32 records per half-bank. */
#include <string.h>
u8 cache_stage,mesh_bank,mesh_record,rear_profile[32];
u16 mesh_phase=65535;
volatile u16 cache_loads,cache_crossings;
static void cache_init(void){
 cache_stage=255;cache_loads=cache_crossings=0;
 /* Main mapper page 0: mesh 0100..02DF, reciprocal 0400..23FF,
  * view code 2400..3BFF, models 3C00..3DD3. BGM uses a different segment. */
 *((volatile u8*)0x6000)=192;memcpy((void*)0x0400,(const void*)0x6000,8192);
 *((volatile u8*)0x6000)=195;memcpy((void*)0x3c00,(const void*)0x7800,468);
 /* Dedicated chase LOD; player uses its resident projected mesh. */
 memcpy((void*)0x3dd4,(const void*)0x79d4,468);
 *((volatile u8*)0x6000)=251;memcpy((void*)0xf700,(const void*)0x6800,312);
 *((volatile u8*)0x6000)=214;memcpy((void*)0x2400,(const void*)0x6000,6144);
}
static void cache_prepare(u8 stage){cache_stage=stage;++cache_loads;}
void apply_coast_appearance(u16 phase);
/* Decode at most one XOR delta into reserved F400..F6FF scratch.
 * No mapper-RAM switch, previous-frame dependency, or large cache allocation. */
static void unpack_course(u16 phase) __naked {
 phase;
 __asm
 ld a,l
 and #1
 push af
 srl h
 rr l
 ld d,h
 ld e,l
 add hl,hl
 add hl,de
 ld de,#0x6000
 add hl,de
 ld a,#249
 ld (0x6000),a
 ld a,(hl)
 inc hl
 ld e,(hl)
 inc hl
 ld d,(hl)
 ld (0x6000),a
 ex de,hl
 ld de,#0xf400
 ld bc,#528
 ldir
 pop af
 or a
 ret z
 ld b,a
course_delta_record:
 push bc
 ld de,#0xf400
course_delta_token:
 ld a,(hl)
 inc hl
 bit 7,a
 jr nz,course_delta_zero
 inc a
 ld b,a
course_delta_literal:
 ld a,(de)
 xor (hl)
 ld (de),a
 inc hl
 inc de
 djnz course_delta_literal
 jr course_delta_check
course_delta_zero:
 and #127
 inc a
 ld c,a
 ld b,#0
 ex de,hl
 add hl,bc
 ex de,hl
course_delta_check:
 ld a,d
 cp #0xf6
 jr nz,course_delta_token
 ld a,e
 cp #0x10
 jr nz,course_delta_token
 pop bc
 djnz course_delta_record
 ret
 __endasm;
}
void expand_course_mesh(void);
static void cache_read(u16 phase){
 unpack_course(phase);
 memcpy(profile,(const void*)0xf400,256);
 expand_course_mesh();
 memcpy(rear_profile,(const void*)0xf5f0,32);
 mesh_phase=phase;
 apply_coast_appearance(phase);
}
static void stage_visuals(u8 stage){
 stage;hardware_upload();
 upload_stage_stream(master_banks[0],master_addresses[0],128,768);
 upload_stage_stream(master_banks[1],master_addresses[1],128,896);
 gfx_set_palette(night_palette);visual_night=0;
}
