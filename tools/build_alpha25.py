"""Build Danger I and verified Lancer II from Alpha 0.24."""
from pathlib import Path
from copy import copy
import sqlite3,tempfile,zipfile
root=Path(__file__).resolve().parents[1]
source=root/'Catastrophe_MDPro3_alpha_v24_revised_effects.ypk'
target=root/'Catastrophe_MDPro3_alpha_v25_danger_lancer.ypk'
replacements={'script/c98013009.lua','script/c98013002.lua'}
with zipfile.ZipFile(source) as src,tempfile.TemporaryDirectory() as folder:
 path=Path(folder)/'catastrophe.cdb';path.write_bytes(src.read('catastrophe.cdb'))
 with sqlite3.connect(path) as db:
  before=db.execute('select * from datas order by id').fetchall()
  texts=db.execute('select * from texts order by id').fetchall()
  columns=[r[1] for r in db.execute('pragma table_info(texts)')]
  title='상대가 대상으로 지정한 자신의 카드 1장 파괴 후 테마 카드 검색'
  assert db.execute('update texts set str1=? where id=98013009',(title,)).rowcount==1
  expected=[]
  for row in texts:
   values=dict(zip(columns,row))
   if row[0]==98013009:values['str1']=title
   expected.append(tuple(values[c] for c in columns))
  assert db.execute('select * from texts order by id').fetchall()==expected
  assert db.execute('select * from datas order by id').fetchall()==before
  assert db.execute('pragma integrity_check').fetchall()==[('ok',)]
 with zipfile.ZipFile(target,'w') as dst:
  for info in src.infolist():
   data=path.read_bytes() if info.filename=='catastrophe.cdb' else (root/info.filename).read_bytes() if info.filename in replacements else src.read(info.filename)
   dst.writestr(copy(info),data)
  dst.write(root/'EFFECT_DEBUG_ALPHA25.md','EFFECT_DEBUG_ALPHA25.md',compress_type=zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(source) as src,zipfile.ZipFile(target) as dst:
 assert dst.testzip() is None
 assert {n for n in src.namelist() if src.read(n)!=dst.read(n)}==replacements|{'catastrophe.cdb'}
print(f'{target.name}: CRC OK, 2 scripts + Danger activation label updated; stats, descriptions, other effects and art preserved.')
