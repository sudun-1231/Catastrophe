"""Build revised Fusion, Forerunner and Calamity King effects from Alpha 0.22."""
from pathlib import Path
from copy import copy
import json,sqlite3,tempfile,zipfile
root=Path(__file__).resolve().parents[1]
source=root/'Catastrophe_MDPro3_alpha_v22_forerunner_invasion.ypk'
target=root/'Catastrophe_MDPro3_alpha_v24_revised_effects.ypk'
updates=json.loads((root/'data/card_updates_alpha24.json').read_text())
replacements={f'script/c{c}.lua' for c in updates}
with zipfile.ZipFile(source) as src,tempfile.TemporaryDirectory() as folder:
 path=Path(folder)/'catastrophe.cdb';path.write_bytes(src.read('catastrophe.cdb'))
 with sqlite3.connect(path) as db:
  before=db.execute('select * from datas order by id').fetchall()
  columns=[r[1] for r in db.execute('pragma table_info(texts)')]
  texts=db.execute('select * from texts order by id').fetchall()
  for code,values in updates.items():
   assert set(values)<={'desc',*[f'str{i}' for i in range(1,17)]}
   keys=list(values)
   assert db.execute('update texts set '+','.join(k+'=?' for k in keys)+' where id=?',[values[k] for k in keys]+[int(code)]).rowcount==1
  assert db.execute('pragma integrity_check').fetchall()==[('ok',)]
  assert db.execute('select * from datas order by id').fetchall()==before
  expected=[]
  for row in texts:
   values=dict(zip(columns,row));values.update(updates.get(str(row[0]),{}));expected.append(tuple(values[c] for c in columns))
  assert db.execute('select * from texts order by id').fetchall()==expected
 with zipfile.ZipFile(target,'w') as dst:
  for info in src.infolist():
   data=path.read_bytes() if info.filename=='catastrophe.cdb' else (root/info.filename).read_bytes() if info.filename in replacements else src.read(info.filename)
   dst.writestr(copy(info),data)
  dst.write(root/'EFFECT_DEBUG_ALPHA24.md','EFFECT_DEBUG_ALPHA24.md',compress_type=zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(source) as src,zipfile.ZipFile(target) as dst:
 assert dst.testzip() is None
 assert {n for n in src.namelist() if src.read(n)!=dst.read(n)}==replacements|{'catastrophe.cdb'}
 assert dst.read('script/c98013018.lua')==src.read('script/c98013018.lua')
print(f'{target.name}: 8 scripts + text updated; 21 cards, stats, art and Watchkeeper preserved; CRC OK.')
