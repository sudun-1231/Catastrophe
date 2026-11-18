"""Add Forerunner and Invasion to Alpha 0.21 while preserving existing assets."""
from pathlib import Path
from copy import copy
import json, sqlite3, tempfile, zipfile
root=Path(__file__).resolve().parents[1]
source=root/'Catastrophe_MDPro3_alpha_v21_new_dragons_links.ypk'
target=root/'Catastrophe_MDPro3_alpha_v22_forerunner_invasion.ypk'
replacements={f'script/c{c}.lua' for c in [98013017,98013018,98013019]}
meta=json.loads((root/'data/card_updates_alpha22.json').read_text())
with zipfile.ZipFile(source) as src,tempfile.TemporaryDirectory() as folder:
 dbpath=Path(folder)/'catastrophe.cdb';dbpath.write_bytes(src.read('catastrophe.cdb'))
 with sqlite3.connect(dbpath) as db:
  dc=[r[1] for r in db.execute('pragma table_info(datas)')];tc=[r[1] for r in db.execute('pragma table_info(texts)')]
  before=db.execute('select * from datas order by id').fetchall()
  before_text=db.execute('select * from texts order by id').fetchall()
  assert len(before)==len(before_text)==19
  for code,values in meta['card_updates'].items():
   assert set(values)=={'desc'}
   assert db.execute('update texts set desc=? where id=?',(values['desc'],int(code))).rowcount==1
  for card in meta['new_cards']:
   for table,columns in [('datas',dc),('texts',tc)]:
    values={c:'' for c in columns};values.update(card[table])
    db.execute('insert into '+table+' ('+','.join(columns)+') values ('+','.join('?' for _ in columns)+')',[values[c] for c in columns])
  assert db.execute('pragma integrity_check').fetchall()==[('ok',)]
  assert db.execute('select * from datas where id<98013020 order by id').fetchall()==before
  assert db.execute('select count(*) from datas').fetchone()[0]==21
  expected=[]
  for row in before_text:
   values=dict(zip(tc,row));values.update(meta['card_updates'].get(str(row[0]),{}))
   expected.append(tuple(values[c] for c in tc))
  for card in meta['new_cards']:
   values={c:'' for c in tc};values.update(card['texts'])
   expected.append(tuple(values[c] for c in tc))
  assert db.execute('select * from texts order by id').fetchall()==expected
 with zipfile.ZipFile(target,'w') as dst:
  for info in src.infolist():
   data=src.read(info.filename)
   if info.filename=='catastrophe.cdb':data=dbpath.read_bytes()
   elif info.filename in replacements:data=(root/info.filename).read_bytes()
   dst.writestr(copy(info),data)
  for code in range(98013020,98013022):
   for path in [f'script/c{code}.lua',f'pics/{code}.jpg']:dst.write(root/path,path,compress_type=zipfile.ZIP_DEFLATED)
  dst.write(root/'EFFECT_DEBUG_ALPHA22.md','EFFECT_DEBUG_ALPHA22.md',compress_type=zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(source) as src,zipfile.ZipFile(target) as dst:
 assert dst.testzip() is None
 assert {n for n in src.namelist() if src.read(n)!=dst.read(n)}=={'catastrophe.cdb'}|replacements
 assert len({dst.read(f'pics/{c}.jpg') for c in range(98013020,98013022)})==2
print(f'{target.name}: 21 cards, CRC OK; existing stats and artwork preserved.')
