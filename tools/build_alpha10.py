"""Build Alpha 0.10 while preserving both earlier archives."""
from pathlib import Path
import zipfile

root=Path(__file__).resolve().parents[1]
source=root/'Catastrophe_MDPro3_alpha_v09_fusion_fix.ypk'
target=root/'Catastrophe_MDPro3_alpha_v10_mdpro3_compat.ypk'
replacements={f'script/c{code}.lua' for code in (98013001,98013002,98013003,98013004,98013005,98013008,98013012,98013013,98013014)}
with zipfile.ZipFile(source) as src,zipfile.ZipFile(target,'w') as dst:
    assert replacements<=set(src.namelist())
    for info in src.infolist():
        dst.writestr(info,(root/info.filename).read_bytes() if info.filename in replacements else src.read(info.filename))
    dst.write(root/'FUSION_DEBUG_ALPHA10.md','FUSION_DEBUG_ALPHA10.md',compress_type=zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(source) as src,zipfile.ZipFile(target) as dst:
    assert dst.testzip() is None
    assert {n for n in src.namelist() if src.read(n)!=dst.read(n)}==replacements
print(f'{target.name}: CRC passed; 9 scripts replaced; DB, pictures, deck and other entries preserved.')
