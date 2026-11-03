; Passing-zone profile, isolated prototype. Does not yet alter live road/AI.
; In: A=route piece, HL=distance0..16383, DE=signed ahead -8192..8192.
; Out: A=right-side extra-width fraction0..32, B=phase, C=admission mask.
; Phase:0 normal,1 opening,2 open,3 merge warning,4 closing.
; Admission bits refer to original lanes -40,+40 and extra lane+120.
; IX/IY and SP preserved. AF/BC/DE/HL scratch. No timer or I/O access.
org 06000h
 ld c,a
 add hl,de
 bit 7,h
 jr z,nonnegative
 ld de,04000h
 add hl,de
 dec c
 jr normalized
nonnegative:
 ld a,h
 cp 040h
 jr c,normalized
 ld de,04000h
 or a
 sbc hl,de
 inc c
normalized:
 ld a,c
 and 7
 cp 2
 jr z,entry_piece
 cp 3
 jr z,exit_piece
normal:
 xor a
 ld b,0
 ld c,3
 ret
entry_piece:
 ld a,h
 cp 010h
 jr nc,open
 call fraction
 ld b,1
 ld c,3
 ret
open:
 ld a,32
 ld b,2
 ld c,7
 ret
exit_piece:
 ld a,h
 cp 020h
 jr c,open
 cp 030h
 jr nc,closing
 ld a,32
 ld b,3
 ld c,3
 ret
closing:
 ex de,hl
 ld hl,04000h
 or a
 sbc hl,de
 call fraction
 ld b,4
 ld c,3
 ret
fraction:
 ; floor(HL/128), inputs0..4096.
 add hl,hl
 ld a,h
 ret
