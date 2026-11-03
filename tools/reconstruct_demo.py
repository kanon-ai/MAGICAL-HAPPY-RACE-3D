"""Reconstruct tested ROMs from preserved release bytes plus checked deltas; not source compilation."""
from pathlib import Path
import hashlib,json,zlib
R=Path(__file__).resolve().parents[1];O=R/'outputs/final-demo';O.mkdir(parents=True,exist_ok=True)
for e in json.loads((R/'assets/final-demo/manifest.json').read_text()):
 a=(R/e['base']).read_bytes();assert hashlib.sha256(a).hexdigest()==e['base_sha256']
 delta=zlib.decompress((R/e['patch']).read_bytes());assert len(a)==len(delta)==4194304
 b=bytes(x^y for x,y in zip(a,delta));assert hashlib.sha256(b).hexdigest()==e['sha256']
 (O/e['output']).write_bytes(b);print(e['output'],e['sha256'])
