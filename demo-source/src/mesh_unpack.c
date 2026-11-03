#include "hardware.h"
/* Expand each compact cuboid to the unchanged renderer's 60-byte layout.
 * Alternate HL addresses the single source page; preserve it across the call.
 * No indexed instruction patching or previous-frame dependency.
 * Source F500..F5EF; destination 0100..02DF. No previous-frame dependency. */
static const u8 mesh_unpack_offsets[60]={
 0,1,4,5,8, 2,3,4,5,8, 2,3,6,7,8, 0,1,6,7,8,
 13,14,17,18,21, 15,16,17,18,21, 15,16,19,20,21, 13,14,19,20,21,
 9,10,11,12,11,12,9,10, 22,23,24,25,24,25,22,23, 26,27,28,29
};
void expand_course_mesh(void) __naked {
 __asm
 push iy
 exx
 push hl
 ld h,#0xf5
 exx
 ld de,#0x0100
 ld c,#0
mesh_expand_object:
 ld hl,#_mesh_unpack_offsets
 ld b,#60
mesh_expand_byte:
 ld a,(hl)
 inc hl
 add a,c
 exx
 ld l,a
 ld a,(hl)
 exx
 ld (de),a
 inc de
 djnz mesh_expand_byte
 ld a,c
 add a,#30
 ld c,a
 cp #240
 jr nz,mesh_expand_object
 exx
 pop hl
 exx
 pop iy
 ret
 __endasm;
}
