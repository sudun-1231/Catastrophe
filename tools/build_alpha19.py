"""Replace only Chimera's artwork in the Alpha 0.18 pack."""
from copy import copy
from pathlib import Path
import zipfile

root=Path(__file__).resolve().parents[1]
source=root/'Catastrophe_MDPro3_alpha_v18_chimera_counter.ypk'
target=root/'Catastrophe_MDPro3_alpha_v19_chimera_art.ypk'
art=(root/'pics/98013015.jpg').read_bytes()
assert art.startswith(b'\xff\xd8') and art.endswith(b'\xff\xd9')
with zipfile.ZipFile(source) as src,zipfile.ZipFile(target,'w') as dst:
    assert art!=src.read('pics/98013014.jpg'), 'Chimera must not duplicate Golem'
    for info in src.infolist():
        dst.writestr(copy(info),art if info.filename=='pics/98013015.jpg' else src.read(info.filename))
    dst.write(root/'ART_UPDATE_ALPHA19.md','ART_UPDATE_ALPHA19.md',compress_type=zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(source) as src,zipfile.ZipFile(target) as dst:
    assert dst.testzip() is None
    assert {n for n in src.namelist() if src.read(n)!=dst.read(n)}=={'pics/98013015.jpg'}
    assert set(dst.namelist())-set(src.namelist())=={'ART_UPDATE_ALPHA19.md'}
print(f'{target.name}: unique Chimera JPEG replaced; DB, every Lua, Golem art and deck identical to Alpha 0.18; CRC passed.')
