"""Build the Watchkeeper summon-trigger compatibility update from Alpha 0.22."""
from pathlib import Path
from copy import copy
import zipfile
root=Path(__file__).resolve().parents[1]
source=root/'Catastrophe_MDPro3_alpha_v22_forerunner_invasion.ypk'
target=root/'Catastrophe_MDPro3_alpha_v23_watchkeeper_trigger.ypk'
changed='script/c98013018.lua'
with zipfile.ZipFile(source) as src,zipfile.ZipFile(target,'w') as dst:
 for info in src.infolist():
  dst.writestr(copy(info),(root/changed).read_bytes() if info.filename==changed else src.read(info.filename))
 dst.write(root/'EFFECT_DEBUG_ALPHA23.md','EFFECT_DEBUG_ALPHA23.md',compress_type=zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(source) as src,zipfile.ZipFile(target) as dst:
 assert dst.testzip() is None
 assert {n for n in src.namelist() if src.read(n)!=dst.read(n)}=={changed}
 assert set(dst.namelist())-set(src.namelist())=={'EFFECT_DEBUG_ALPHA23.md'}
print(f'{target.name}: CRC OK; only Watchkeeper script changed; database, all art and other scripts preserved.')
