; A=source bank, HL=RLE row. Exactly72bytes -> F400. PreserveAF/HL/IX/IY.
org 07000h
push ix
push af
push hl
ld hl,-64
add hl,sp
ld sp,hl
push hl
pop ix
ex de,hl
ld hl,ram_template
ld bc,ram_end-ram_template
ldir
ld l,(ix+64)
ld h,(ix+65)
ld a,(ix+67)
ld de,decoded
push de
jp (ix)
decoded:
ld hl,64
add hl,sp
ld sp,hl
pop hl
pop af
pop ix
ret
ram_template:
ld (06000h),a
ld de,0f400h
next_token:
ld a,(hl)
inc hl
ld c,a
and 127
inc a
ld b,a
bit 7,c
jr z,literal
ld a,(hl)
inc hl
repeat:
ld (de),a
inc de
djnz repeat
jr row_check
literal:
ld a,(hl)
inc hl
ld (de),a
inc de
djnz literal
row_check:
ld a,e
cp 72
jr nz,next_token
ld a,211
ld (06000h),a
ret
ram_end:
