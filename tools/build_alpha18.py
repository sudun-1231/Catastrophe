"""Build Alpha 0.18, adding Chimera and updating Counterattack."""
from pathlib import Path
from copy import copy
import json
import sqlite3
import tempfile
import zipfile

root=Path(__file__).resolve().parents[1]
source=root/'Catastrophe_MDPro3_alpha_v17_threshold_quickplay.ypk'
target=root/'Catastrophe_MDPro3_alpha_v18_chimera_counter.ypk'
meta=json.loads((root/'data/card_updates_alpha18.json').read_text())
new=meta['new_card']
with zipfile.ZipFile(source) as src,tempfile.TemporaryDirectory() as folder:
    dbpath=Path(folder)/'catastrophe.cdb'
    dbpath.write_bytes(src.read('catastrophe.cdb'))
    with sqlite3.connect(dbpath) as db:
        data_columns=[r[1] for r in db.execute('PRAGMA table_info(datas)')]
        text_columns=[r[1] for r in db.execute('PRAGMA table_info(texts)')]
        before_data=db.execute('SELECT * FROM datas ORDER BY id').fetchall()
        before_text=db.execute('SELECT * FROM texts ORDER BY id').fetchall()
        assert len(before_data)==len(before_text)==14
        assert new['datas']['id']==new['texts']['id']==98013015
        assert set(new['datas'])==set(data_columns)
        for code,values in meta['card_updates'].items():
            assert set(values)<={'name','desc',*[f'str{i}' for i in range(1,17)]}
            columns=list(values)
            cursor=db.execute('UPDATE texts SET '+','.join(f'{c}=?' for c in columns)+' WHERE id=?',
                              [values[c] for c in columns]+[int(code)])
            assert cursor.rowcount==1
        db.execute('INSERT INTO datas ('+','.join(data_columns)+') VALUES ('+','.join('?' for _ in data_columns)+')',
                   [new['datas'][c] for c in data_columns])
        new_text={c:'' for c in text_columns}
        new_text.update(new['texts'])
        db.execute('INSERT INTO texts ('+','.join(text_columns)+') VALUES ('+','.join('?' for _ in text_columns)+')',
                   [new_text[c] for c in text_columns])
        assert db.execute('PRAGMA integrity_check').fetchall()==[('ok',)]
        assert db.execute('SELECT * FROM datas ORDER BY id').fetchall()==before_data+[tuple(new['datas'][c] for c in data_columns)]
        expected=[]
        for row in before_text:
            values=dict(zip(text_columns,row))
            values.update(meta['card_updates'].get(str(row[0]),{}))
            expected.append(tuple(values[c] for c in text_columns))
        expected.append(tuple(new_text[c] for c in text_columns))
        assert db.execute('SELECT * FROM texts ORDER BY id').fetchall()==expected
    with zipfile.ZipFile(target,'w') as dst:
        for info in src.infolist():
            data=src.read(info.filename)
            if info.filename=='script/c98013011.lua':data=(root/info.filename).read_bytes()
            if info.filename=='catastrophe.cdb':data=dbpath.read_bytes()
            dst.writestr(copy(info),data)
        dst.write(root/'script/c98013015.lua','script/c98013015.lua',compress_type=zipfile.ZIP_DEFLATED)
        # Temporary art only: the existing Golem placeholder, pending a Chimera image.
        dst.writestr('pics/98013015.jpg',src.read('pics/98013014.jpg'),compress_type=zipfile.ZIP_DEFLATED)
        dst.write(root/'EFFECT_DEBUG_ALPHA18.md','EFFECT_DEBUG_ALPHA18.md',compress_type=zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(source) as src,zipfile.ZipFile(target) as dst:
    assert dst.testzip() is None
    assert {n for n in src.namelist() if src.read(n)!=dst.read(n)}=={'script/c98013011.lua','catastrophe.cdb'}
    assert set(dst.namelist())-set(src.namelist())=={'script/c98013015.lua','pics/98013015.jpg','EFFECT_DEBUG_ALPHA18.md'}
print(f'{target.name}: 15 cards; Chimera added; Counterattack updated; original stats/art/deck preserved.')
