from pathlib import Path
p=Path(__file__).with_name('build_city_tunnel_faststream.py')
s=p.read_text().replace('drive_city_tunnel_fastcoord.c','drive_city_tunnel_portal_lod.c').replace('drive_city_tunnel_faststream.c','drive_city_tunnel_portal_stream.c').replace('city-tunnel-faststream','city-tunnel-portal-stream').replace('0x7e00','0x7ec0')
exec(compile(s,str(p),'exec'))
p=Path(__file__).with_name('build_city_tunnel_setup_once.py')
s=p.read_text().replace('drive_city_tunnel_fastcoord.c','drive_city_tunnel_portal_stream.c').replace('drive_city_tunnel_setup_once.c','drive_city_tunnel_portal_fast.c').replace('city-tunnel-setup-once','city-tunnel-portal-fast').replace('0x7e00','0x7ec0')
exec(compile(s,str(p),'exec'))
