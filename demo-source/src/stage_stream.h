/* Only the graphics decoder is live; obsolete rally delta-code was removed. */
u8 stream_bank,loaded_stage;
const u8 *stream_pointer;
/* Graphics decoding is used only during stage loading, never while driving. */
u8 graphics_buffer[1024];
static void read_graphics_block(void){
    u8 *dst=graphics_buffer,flags,mask,n;
    u16 token,offset;
    if(stream_pointer==(const u8*)0x8000||!*stream_pointer){
        ++stream_bank;stream_pointer=(const u8*)0x6000;
    }
    *((volatile u8*)0x6000)=stream_bank;
    ++stream_pointer;
    while(dst<graphics_buffer+1024){
        flags=*stream_pointer++;mask=1;
        do {
            if(flags&mask){
                token=*stream_pointer++;token|=(u16)*stream_pointer++<<8;
                offset=(token&1023)+1;n=(token>>10)+3;
                do { *dst=*(dst-offset);++dst; } while(--n);
            }else *dst++=*stream_pointer++;
            mask<<=1;
        }while(mask&&dst<graphics_buffer+1024);
    }
}
static void upload_stage_stream(u8 bank,u16 address,u16 blocks,u16 y){
    stream_bank=bank;stream_pointer=(const u8*)address;
    *((volatile u8*)0x6000)=bank;
    gfx_upload_begin(y);
    while(blocks){
        read_graphics_block();gfx_upload_256(graphics_buffer);gfx_upload_256(graphics_buffer+256);
        gfx_upload_256(graphics_buffer+512);gfx_upload_256(graphics_buffer+768);blocks-=4;
    }
    loaded_phase=65535;loaded_stage=255;
}
