; Cooperative 60 Hz OPZ host. Never touches VDP ports, IRQs or the lap timer.
; Entry points: D600 poll, D603 start, D606 stop. CPU remains in R800 mode.
        org 0xd600
        jp service
        jp start_music
        jp stop_music
active: equ 0xee25
fraction: equ 0xee26
next_tick: equ 0xee28
tick_count: equ 0xee2c
max_late: equ 0xee2e
music_segment: equ 0xee23
saved_segment: equ 0xee24
service:
        push af
        ld a,(active)
        or a
        jr z,service_af
        push bc
        push de
        push hl
        call timer_read
        ld de,(next_tick)
        or a
        sbc hl,de
        bit 7,h
        jr nz,service_done
        push hl
        ld de,(max_late)
        or a
        sbc hl,de
        pop hl
        jr c,keep_late
        ld (max_late),hl
keep_late:
        in a,(0xfc)
        ld (saved_segment),a
        ld a,(music_segment)
        out (0xfc),a
        call tick
        ld a,(saved_segment)
        out (0xfc),a
        ld hl,(tick_count)
        inc hl
        ld (tick_count),hl
        ; E6 clock = 3579545/14 Hz. One 60 Hz tick = 4261 + 61/168.
        ld hl,(next_tick)
        ld de,4261
        add hl,de
        ld a,(fraction)
        add a,61
        cp 168
        jr c,store_fraction
        sub 168
        inc hl
store_fraction:
        ld (fraction),a
        ld (next_tick),hl
service_done:
        pop hl
        pop de
        pop bc
service_af:
        pop af
        ret
start_music:
        push af
        push bc
        push de
        push hl
        call stop
        ld hl,0x0100
        call init
        ld a,1
        ld (loop_enabled),a
        ld (active),a
        xor a
        ld (fraction),a
        ld hl,0
        ld (tick_count),hl
        ld (max_late),hl
        call timer_read
        ld (next_tick),hl
        pop hl
        pop de
        pop bc
        pop af
        ret
stop_music:
        push af
        xor a
        ld (active),a
        call stop
        pop af
        ret
timer_read:
        in a,(0xe7)
        ld h,a
        in a,(0xe6)
        ld l,a
        in a,(0xe7)
        cp h
        jr nz,timer_read
        ret
        include "src/bgm_player.asm"
