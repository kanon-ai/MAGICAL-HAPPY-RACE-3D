#ifndef RALLY_IO_PORTS_H
#define RALLY_IO_PORTS_H
#ifdef EXTERNAL_V9968
#define IO_VRAM 0x88
#define IO_CONTROL 0x89
#define IO_PALETTE 0x8a
#define IO_COMMAND 0x8b
#define IO_UNLOCK 0x8c
#define IO_GEO_INDEX 0x8d
#define IO_GEO_DATA 0x8f
#else
#define IO_VRAM 0x98
#define IO_CONTROL 0x99
#define IO_PALETTE 0x9a
#define IO_COMMAND 0x9b
#define IO_UNLOCK 0x9c
#define IO_GEO_INDEX 0x9d
#define IO_GEO_DATA 0x9f
#endif
#endif
