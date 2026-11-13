"""Rebuild Alpha 0.9 without modifying the original Alpha 0.8 package."""
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
source = root / 'Catastrophe_MDPro3_alpha_v08_garura.ypk'
target = root / 'Catastrophe_MDPro3_alpha_v09_fusion_fix.ypk'
replacements = {f'script/c{card}.lua' for card in (98013001, 98013002, 98013003, 98013004, 98013005, 98013013)}
with zipfile.ZipFile(source) as src, zipfile.ZipFile(target, 'w') as dst:
    assert replacements <= set(src.namelist())
    for info in src.infolist():
        data = (root / info.filename).read_bytes() if info.filename in replacements else src.read(info.filename)
        dst.writestr(info, data)
    dst.write(root / 'FUSION_DEBUG.md', 'FUSION_DEBUG_ALPHA09.md', compress_type=zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(source) as src, zipfile.ZipFile(target) as dst:
    assert dst.testzip() is None
    changed = {name for name in src.namelist() if src.read(name) != dst.read(name)}
    assert changed == replacements, changed
print(f'{target.name}: ZIP CRC passed; exactly 6 scripts replaced; original database, pictures, deck and other entries preserved.')
