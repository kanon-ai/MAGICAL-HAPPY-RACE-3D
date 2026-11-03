; Isolated random-access shared dictionary experiment, not production code.
 org 0f000h
start:
 in a,(0fch)
 ld (saved_page),a
 ld b,15
choose:
 in a,(0fch)
 cp b
 jr z,next_segment
 in a,(0fdh)
 cp b
 jr z,next_segment
 in a,(0feh)
 cp b
 jr z,next_segment
 in a,(0ffh)
 cp b
 jr z,next_segment
 ld a,(0ee23h)
 cp b
 jr nz,selected
next_segment:
 djnz choose
 halt
selected:
 ld a,b
 out (0fch),a
ready:
 jp ready
load_group:
 ld de,0
 ld bc,1341
 ldir
decode:
 ld hl,0
 ld de,0f400h
 ld ix,447
field:
 ld a,(hl)
 ld (base_value),a
 inc hl
 ld c,(hl)
 inc hl
 ld b,(hl)
 inc hl
 push hl
 ld a,b
 or c
 jr z,constant
 ; 2048 four-byte entries per lower-half ROM bank, index banks 1..26.
 ld a,b
 srl a
 srl a
 srl a
 inc a
 ld (06000h),a
 ld h,b
 ld l,c
 add hl,hl
 add hl,hl
 ld a,h
 and 31
 or 040h
 ld h,a
 ld a,(hl)
 inc hl
 ld c,(hl)
 inc hl
 ld h,(hl)
 ld l,c
 ld (06000h),a
 ld a,(sample_phase)
 call sample
 ld c,a
 ld a,(base_value)
 add a,c
 jr store
constant:
 ld a,(base_value)
store:
 ld (de),a
 inc de
 pop hl
 dec ix
 ld a,ixh
 or ixl
 jr nz,field
done:
 jp done
finish:
 ld a,(saved_page)
 out (0fch),a
finished:
 jp finished
sample:
 ld c,a
 inc hl
token:
 ld a,(hl)
 inc hl
 ld b,a
 and 63
 inc a
 cp c
 jr z,skip
 jr c,skip
 ld a,b
 and 0c0h
 jr z,literal
 cp 040h
 jr z,repeated
 cp 080h
 jr z,unit_ramp
 ; Product lookup in the isolated mapper segment: 2000+delta*32+index.
 ld b,(hl)
 inc hl
 ld l,(hl)
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld a,h
 or 020h
 ld h,a
 ld a,l
 or c
 ld l,a
 ld a,(hl)
 add a,b
 ret
literal:
 ld a,l
 add a,c
 ld l,a
 jr nc,repeated
 inc h
repeated:
 ld a,(hl)
 ret
unit_ramp:
 ld a,(hl)
 add a,c
 ret
skip:
 neg
 add a,c
 ld c,a
 ld a,b
 and 0c0h
 jr z,skip_literal
 inc hl
 cp 0c0h
 jr nz,token
 inc hl
 jr token
skip_literal:
 ld a,b
 and 63
 inc a
 add a,l
 ld l,a
 jr nc,token
 inc h
 jr token
saved_page: db 0
sample_phase: db 0
base_value: db 0
