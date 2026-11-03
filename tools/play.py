from pathlib import Path
import argparse,os,shutil,subprocess
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description="Launch MAGICAL HAPPY RACE 3D with a separately installed Geo3D V2 openMSX.")
p.add_argument("--openmsx",default=os.environ.get("OPENMSX",shutil.which("openmsx")))
p.add_argument("--external-88h",action="store_true")
p.add_argument("--machine")
p.add_argument("--rom",type=Path)
p.add_argument("--dry-run",action="store_true")
a=p.parse_args()
if a.machine is None:a.machine="Panasonic_FS-A1ST" if a.external_88h else "Panasonic_FS-A1ST_V9968"
if a.rom is None:a.rom=R/"rom"/("MAGICAL_HAPPY_RACE_3D_EXTERNAL_88H.rom" if a.external_88h else "MAGICAL_HAPPY_RACE_3D_INTERNAL_98H.rom")
if not a.openmsx:p.error("Set OPENMSX to the compatible openMSX executable, or pass --openmsx.")
e=Path(a.openmsx).resolve()
if not e.is_file():p.error("openMSX executable not found")
if not a.rom.is_file():p.error("ROM not found")
extensions=["-ext","HRA_V9968","-ext","geo3d88"] if a.external_88h else ["-ext","geo3d"]
script="play-external.tcl" if a.external_88h else "play.tcl"
cmd=[str(e),"-machine",a.machine,*extensions,"-cart",str(a.rom.resolve()),"-romtype","ASCII16","-script",str(R/"tools"/script)]
env=dict(os.environ)
if (e.parent/"share").is_dir():env["OPENMSX_SYSTEM_DATA"]=str(e.parent/"share")
if a.dry_run:print(subprocess.list2cmdline(cmd))
else:raise SystemExit(subprocess.call(cmd,env=env))
