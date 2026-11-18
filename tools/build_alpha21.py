"""Add four illustrated cards to Alpha 0.20 while preserving existing assets."""
from pathlib import Path
from copy import copy
import json, sqlite3, tempfile, zipfile
root=Path(__file__).resolve().parents[1]
source=root/'Catastrophe_MDPro3_alpha_v20_chimera_pierce.ypk'
target=root/'Catastrophe_MDPro3_alpha_v21_new_dragons_links.ypk'
meta=json.loads((root/'data/card_updates_alpha21.json').read_text())
with zipfile.ZipFile(source) as src,tempfile.TemporaryDirectory() as folder:
 dbpath=Path(folder)/'catastrophe.cdb';dbpath.write_bytes(src.read('catastrophe.cdb'))
 with sqlite3.connect(dbpath) as db:
  dc=[r[1] for r in db.execute('pragma table_info(datas)')];tc=[r[1] for r in db.execute('pragma table_info(texts)')]
  before=db.execute('select * from datas order by id').fetchall()
  assert len(before)==15
  for code,values in meta['card_updates'].items():
   assert set(values)=={'desc'}
   assert db.execute('update texts set desc=? where id=?',(values['desc'],int(code))).rowcount==1
  for card in meta['new_cards']:
   for table,columns in [('datas',dc),('texts',tc)]:
    values={c:'' for c in columns};values.update(card[table])
    db.execute('insert into '+table+' ('+','.join(columns)+') values ('+','.join('?' for _ in columns)+')',[values[c] for c in columns])
  assert db.execute('pragma integrity_check').fetchall()==[('ok',)]
  assert db.execute('select * from datas where id<98013016 order by id').fetchall()==before
  assert db.execute('select count(*) from datas').fetchone()[0]==19
 with zipfile.ZipFile(target,'w') as dst:
  for info in src.infolist():dst.writestr(copy(info),dbpath.read_bytes() if info.filename=='catastrophe.cdb' else src.read(info.filename))
  for code in range(98013016,98013020):
   for path in [f'script/c{code}.lua',f'pics/{code}.jpg']:dst.write(root/path,path,compress_type=zipfile.ZIP_DEFLATED)
  dst.write(root/'EFFECT_DEBUG_ALPHA21.md','EFFECT_DEBUG_ALPHA21.md',compress_type=zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(source) as src,zipfile.ZipFile(target) as dst:
 assert dst.testzip() is None
 assert {n for n in src.namelist() if src.read(n)!=dst.read(n)}=={'catastrophe.cdb'}
 assert len({dst.read(f'pics/{c}.jpg') for c in range(98013016,98013020)})==4
print(f'{target.name}: 19 cards, CRC OK; existing scripts, stats and artwork preserved.')
