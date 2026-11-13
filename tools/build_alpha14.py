"""Build Alpha 0.14 Absorption Fusion activation from Alpha 0.13."""
from pathlib import Path
import json
import sqlite3
import tempfile
import zipfile

root=Path(__file__).resolve().parents[1]
source=root/'Catastrophe_MDPro3_alpha_v13_recovery_fix.ypk'
target=root/'Catastrophe_MDPro3_alpha_v14_absorption_fusion.ypk'
replacements={f'script/c{code}.lua' for code in (98013010,)}
updates=json.loads((root/'data/card_text_alpha14.json').read_text())
with zipfile.ZipFile(source) as src,tempfile.TemporaryDirectory() as directory:
    dbpath=Path(directory)/'catastrophe.cdb'
    dbpath.write_bytes(src.read('catastrophe.cdb'))
    with sqlite3.connect(dbpath) as db:
        before_data=db.execute("SELECT * FROM datas ORDER BY id").fetchall()
        columns=[row[1] for row in db.execute("PRAGMA table_info(texts)")]
        before_text=db.execute("SELECT * FROM texts ORDER BY id").fetchall()
        for code,values in updates.items():
            assert set(values)<={'desc',*[f'str{i}' for i in range(1,17)]}
            update_columns=list(values)
            cursor=db.execute('UPDATE texts SET '+','.join(f'{column}=?' for column in update_columns)+' WHERE id=?',
                              [values[column] for column in update_columns]+[int(code)])
            assert cursor.rowcount==1
        assert db.execute('PRAGMA integrity_check').fetchall()==[('ok',)]
        assert db.execute("SELECT * FROM datas ORDER BY id").fetchall()==before_data
        after_text=db.execute("SELECT * FROM texts ORDER BY id").fetchall()
        assert len(before_text)==len(after_text)==14
        for before,after in zip(before_text,after_text):
            expected=dict(zip(columns,before))
            expected.update(updates.get(str(before[0]),{}))
            assert tuple(expected[column] for column in columns)==after
    with zipfile.ZipFile(target,'w') as dst:
        for info in src.infolist():
            data=(root/info.filename).read_bytes() if info.filename in replacements else src.read(info.filename)
            if info.filename=='catastrophe.cdb':
                data=dbpath.read_bytes()
            dst.writestr(info,data)
        dst.write(root/'EFFECT_DEBUG_ALPHA14.md','EFFECT_DEBUG_ALPHA14.md',compress_type=zipfile.ZIP_DEFLATED)
with zipfile.ZipFile(source) as src,zipfile.ZipFile(target) as dst:
    assert dst.testzip() is None
    assert {n for n in src.namelist() if src.read(n)!=dst.read(n)}==replacements|{'catastrophe.cdb'}
print(f'{target.name}: CRC passed; 1 script and card text DB updated; stats, images and other scripts preserved.')
