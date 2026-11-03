; ASCII16 bank 0, lower half. Run the C program from turbo R internal RAM.
    org 04000h
    db "AB"
    dw start
    dw 0,0,0,0,0,0
start:
    di
    ld sp,0F300h
    xor a
    ld (06000h),a
    ; Map page 2 to the same RAM slot as page 3, including expanded slots.
    in a,(0A8h)
    rlca
    rlca
    and 3
    ld c,a
    ld b,0
    ld hl,0FCC1h
    add hl,bc
    ld a,(hl)
    and 080h
    jr z,primary_ram
    ld hl,0FCC5h
    add hl,bc
    ld a,(hl)
    and 0C0h
    rrca
    rrca
    rrca
    rrca
    or 080h
primary_ram:
    or c
    ld h,080h
    call 0024h
    di
    ; R800 ROM mode: retain all 256KiB RAM, including the top 64KiB.
    ; Program and stage cache execute/read internal RAM, never BIOS in play.
    ld a,(0002Dh)
    cp 3
    jr c,no_turbo
    ld a,081h
    call 0180h
no_turbo:
    di
    ; Map page 0 to internal mapper RAM; all subsequent calls are our own.
    ; The cartridge boot runs in page 1 and runtime/stack in pages 2/3.
    in a,(0A8h)
    rlca
    rlca
    and 3
    ld c,a
    ld b,0
    ld hl,0FCC1h
    add hl,bc
    ld a,(hl)
    and 080h
    jr z,cache_primary
    ld hl,0FCC5h
    add hl,bc
    ld a,(hl)
    and 0C0h
    rrca
    rrca
    rrca
    rrca
    or 080h
cache_primary:
    or c
    ; Do not call the page-0 BIOS while removing it from page 0.
    ld c,a
    and 3
    ld b,a
    in a,(0A8h)
    and 0FCh
    or b
    out (0A8h),a
    bit 7,c
    jr z,cache_mapped
    ld a,c
    rrca
    rrca
    and 3
    ld b,a
    ld a,(0FFFFh)
    cpl
    and 0FCh
    or b
    ld (0FFFFh),a
cache_mapped:
    di
    ld sp,0F300h
    ld hl,ram_loader
    ld de,0F000h
    ld bc,ram_loader_end-ram_loader
    ldir
    jp 0F000h
ram_loader:

    ; Banks 1..3 are the runtime image for 8000..DFFF.
    ld a,1
    ld de,08000h
copy_bank:
    ld (06000h),a
    ld hl,06000h
    ld bc,02000h
    ldir
    inc a
    cp 4
    jr nz,copy_bank
    ; Reset all static data without touching BIOS workspace or our stack.
    xor a
    ld hl,0E000h
    ld de,0E001h
    ld bc,00FFFh
    ld (hl),a
    ldir
INITIALIZE_DATA
    ; Reserve a mapper segment not used by any current CPU page.
    in a,(0FCh)
    ld (0EE24h),a
    ld b,15
music_segment_try:
    in a,(0FCh)
    cp b
    jr z,music_segment_next
    in a,(0FDh)
    cp b
    jr z,music_segment_next
    in a,(0FEh)
    cp b
    jr z,music_segment_next
    in a,(0FFh)
    cp b
    jr nz,music_segment_ready
music_segment_next:
    dec b
    jr music_segment_try
music_segment_ready:
    ld a,b
    ld (0EE23h),a
    out (0FCh),a
    ld a,193
    ld (06000h),a
    ld hl,06000h
    ld de,00100h
    ld bc,02000h
    ldir
    ld a,194
    ld (06000h),a
    ld hl,06000h
    ld bc,7521
    ldir
    ld a,(0EE24h)
    out (0FCh),a
    ld a,255
    ld (06000h),a
    ld hl,06000h
    ld de,0F840h
    ld bc,1472
    ldir
    jp ENTRY_POINT

ram_loader_end:
    defs 02000h-($-04000h),0FFh
