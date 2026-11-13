"""Native MDPro3 regression tests; requires an externally built core and script.zip.
Selections and deck-order UI are automated; card movement and Fusion checks are native.
See FUSION_DEBUG_ALPHA10.md for build commands and exact test scope.
"""
import argparse
import ctypes as C,zipfile,sqlite3,tempfile,pathlib
parser=argparse.ArgumentParser()
parser.add_argument('--core',type=pathlib.Path,required=True)
parser.add_argument('--scripts',type=pathlib.Path,required=True)
parser.add_argument('--baseline',action='store_true')
parser.add_argument('--pack',type=pathlib.Path,help='Test scripts and card data directly from a generated pack')
args=parser.parse_args()
ROOT=pathlib.Path(__file__).resolve().parents[1]
lib=C.CDLL(str(args.core.resolve()))
class Data(C.Structure):
 _fields_=[('code',C.c_uint32),('alias',C.c_uint32),('setcode',C.c_uint16*16),('type',C.c_uint32),('level',C.c_uint32),('attribute',C.c_uint32),('race',C.c_uint32),('attack',C.c_int32),('defense',C.c_int32),('lscale',C.c_uint32),('rscale',C.c_uint32),('link_marker',C.c_uint32)]
original=zipfile.ZipFile(args.pack or ROOT/'Catastrophe_MDPro3_alpha_v09_fusion_fix.ypk')
base=zipfile.ZipFile(args.scripts)
with tempfile.TemporaryDirectory() as d:
 p=pathlib.Path(d)/'cards.cdb';p.write_bytes(original.read('catastrophe.cdb'));db=sqlite3.connect(p)
 rows={r[0]:r for r in db.execute('select id,alias,setcode,type,atk,def,level,race,attribute from datas')}
buffers=[];logs=[];extra={}
@C.CFUNCTYPE(C.c_void_p,C.c_char_p,C.POINTER(C.c_int))
def reader(name,size):
 n=name.decode().removeprefix('./')
 if n in extra:data=extra[n].encode()
 elif not args.baseline and not args.pack and n.startswith('script/') and (ROOT/n).is_file():data=(ROOT/n).read_bytes()
 elif n in original.namelist():data=original.read(n)
 elif n in base.namelist():data=base.read(n)
 else:size[0]=0;return None
 b=C.create_string_buffer(data);buffers.append(b);size[0]=len(data);return C.addressof(b)
@C.CFUNCTYPE(C.c_uint32,C.c_uint32,C.POINTER(Data))
def cardreader(code,p):
 if code not in rows:return 0
 r=rows[code];v=p.contents;v.code=r[0];v.alias=r[1];v.setcode[0]=r[2];v.type=r[3];v.attack=r[4];v.defense=r[5];v.level=r[6]&255;v.lscale=(r[6]>>24)&255;v.rscale=(r[6]>>16)&255;v.race=r[7];v.attribute=r[8];return 0
lib.get_log_message.argtypes=[C.c_void_p,C.c_void_p]
@C.CFUNCTYPE(C.c_uint32,C.c_void_p,C.c_uint32)
def handler(duel,kind):
 b=C.create_string_buffer(4096);lib.get_log_message(duel,b);s=b.value.decode(errors='replace');logs.append((kind,s));return 0
lib.set_script_reader(reader);lib.set_card_reader(cardreader);lib.set_message_handler(handler)
lib.create_duel.argtypes=[C.c_ulong];lib.create_duel.restype=C.c_void_p
lib.end_duel.argtypes=[C.c_void_p];lib.preload_script.argtypes=[C.c_void_p,C.c_char_p,C.c_int]
def test(name,script):
 logs.clear();extra['script/probe.lua']=script
 duel=lib.create_duel(123)
 try:
  result=lib.preload_script(duel,b'script/probe.lua',0)
  print(name,result,logs)
  if args.baseline:
   assert any(k==1 and 'Fusion' in s for k,s in logs),(name,logs)
   print('EXPECTED FAILURE: Alpha 0.9 cannot register Fusion effects against this library')
  else:
   assert result and not any(k==1 for k,s in logs),(name,logs)
 finally:lib.end_duel(duel)

test('registration','''Debug.ReloadFieldBegin(0)
Debug.SetPlayerInfo(0,8000,0,0)
Debug.SetPlayerInfo(1,8000,0,0)
for i=1,14 do Debug.AddCard(98013000+i,0,0,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end
Debug.ReloadFieldEnd()
Debug.Message("registration OK")''')

def fixture(cards,body):
 return '''Debug.ReloadFieldBegin(0)
Debug.SetPlayerInfo(0,8000,0,0)
Debug.SetPlayerInfo(1,8000,0,0)
'''+cards+'\nDebug.ReloadFieldEnd()\n'+body+'\nDebug.Message("PASS")'
if args.baseline: raise SystemExit(0)
for code in [98013001,98013002,98013003,98013004,98013005,98013013]:
 for loc in ['LOCATION_GRAVE','LOCATION_REMOVED']:
  test(f'trigger {code} {loc}',fixture(f'''
local c=Debug.AddCard({code},0,0,{loc},0,POS_FACEUP_ATTACK)
Debug.AddCard(98013002,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
Debug.AddCard(98013001,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
Debug.AddCard(98013012,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
''',f'local e=Effect.CreateEffect(c); e:SetType(EFFECT_TYPE_SINGLE); e:SetCode(EFFECT_UPDATE_ATTACK); e:SetValue(0); c:RegisterEffect(e); assert(c{code}.fus_target(e,0,nil,0,0,nil,0,0,0),"fusion target rejected")'))
for bottom in [False,True]:
 loc='LOCATION_GRAVE' if bottom else 'LOCATION_HAND'
 material='LOCATION_REMOVED' if bottom else 'LOCATION_DECK'
 test(f'Birth target {bottom}',fixture(f'''
local c=Debug.AddCard(98013008,0,0,{loc},0,POS_FACEUP_ATTACK)
Debug.AddCard(98013001,0,0,{material},0,POS_FACEUP_ATTACK)
Debug.AddCard(98013002,0,0,{material},0,POS_FACEUP_ATTACK)
Debug.AddCard(98013013,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
''',f'local e=Effect.CreateEffect(c); e:SetType(EFFECT_TYPE_SINGLE); e:SetCode(EFFECT_UPDATE_ATTACK); e:SetValue(0); c:RegisterEffect(e); assert(c98013008.target(e,0,0,{str(bottom).lower()}),"Birth target rejected")'))
test('no other material',fixture('''
local c=Debug.AddCard(98013001,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
Debug.AddCard(98013013,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
''','local e=Effect.CreateEffect(c); e:SetType(EFFECT_TYPE_SINGLE); e:SetCode(EFFECT_UPDATE_ATTACK); e:SetValue(0); c:RegisterEffect(e); assert(not c98013001.fus_target(e,0,nil,0,0,nil,0,0,0))'))
test('facedown banished mandatory',fixture('''
local c=Debug.AddCard(98013001,0,0,LOCATION_REMOVED,0,POS_FACEDOWN_DEFENSE)
Debug.AddCard(98013002,0,0,LOCATION_HAND,0,POS_FACEUP_ATTACK)
Debug.AddCard(98013013,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
''','local e=Effect.CreateEffect(c); e:SetType(EFFECT_TYPE_SINGLE); e:SetCode(EFFECT_UPDATE_ATTACK); e:SetValue(0); c:RegisterEffect(e); assert(not c98013001.fus_target(e,0,nil,0,0,nil,0,0,0))'))
lib.start_duel.argtypes=[C.c_void_p,C.c_int]
lib.process.argtypes=[C.c_void_p];lib.process.restype=C.c_uint32
lib.get_message.argtypes=[C.c_void_p,C.c_void_p]
lib.set_responseb.argtypes=[C.c_void_p,C.c_void_p]
lib.set_responsei.argtypes=[C.c_void_p,C.c_int]
logs.clear()
extra['script/probe.lua']=fixture('''
local c=Debug.AddCard(98013008,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
local a=Debug.AddCard(98013001,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local b=Debug.AddCard(98013002,0,0,LOCATION_REMOVED,0,POS_FACEUP_ATTACK)
local fc=Debug.AddCard(98013013,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
Duel.SortDecktop=function(tp,p,count) assert(count==2) end
Group.Select=function(g,tp,min,max,excluded) return Group.FromCards(g:GetFirst()) end
Duel.SelectFusionMaterial=function(tp,target,mg,mandatory,chkf)
 assert(target==fc and mandatory==nil)
 assert(fc:CheckFusionMaterial(mg,nil,tp))
 return Group.FromCards(a,b)
end
local run=Effect.CreateEffect(c)
run:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
run:SetRange(LOCATION_GRAVE)
run:SetCode(EVENT_ADJUST)
run:SetOperation(function(e)
 e:Reset()
 assert(c98013008.returncost(e,0,nil,0,0,nil,0,0,0))
 assert(c98013008.target(e,0,0,true))
 c98013008.returncost(e,0,nil,0,0,nil,0,0,1)
 assert(c:IsLocation(LOCATION_DECK),"cost not paid")
 c98013008.operation2(e,0,nil,0,0,nil,0,0)
 assert(a:IsLocation(LOCATION_DECK) and b:IsLocation(LOCATION_DECK),"materials not returned")
 assert(fc:IsLocation(LOCATION_MZONE) and fc:IsSummonType(SUMMON_TYPE_FUSION),"fusion not summoned")
 Debug.Message("RESOLUTION PASS")
end)
c:RegisterEffect(run)
''')
def run_resolution(name,battle=False,end_phase=False,activations=1,select_code=None,option_index=0):
 duel=lib.create_duel(123)
 try:
  assert lib.preload_script(duel,b'script/probe.lua',0)
  lib.start_duel(duel,0)
  started=0
  for step in range(100):
   result=lib.process(duel)
   out=C.create_string_buffer(65536);length=lib.get_message(duel,out)
   if any(k==1 for k,s in logs):raise AssertionError(logs)
   if any(s=='RESOLUTION PASS' for k,s in logs):break
   if result & 0x10000000 and length:
    data=out.raw[:length]
    if data[0]==11 and (started<activations or end_phase):
     command=7 if started>=activations and end_phase else 6 if battle else 5
     started+=1
     if command==5:
      offset=2
      for _ in range(5):offset+=1+7*data[offset]
      count=data[offset];offset+=1
      for index in range(count):
       if int.from_bytes(data[offset+index*11+7:offset+index*11+11],"little")==999999:
        command=5+(index<<16)
        break
     lib.set_responsei(duel,command)
     continue
    if data[0]==10 and battle:
     lib.set_responsei(duel,1)
     continue
    if data[0]==15:
     count=data[3]
     indices=list(range(count))
     if select_code is not None:
      matches=[i for i in range(data[5]) if int.from_bytes(data[6+i*8:10+i*8],"little")==select_code]
      if matches:indices=matches[:count]
     lib.set_responseb(duel,C.create_string_buffer(bytes([count,*indices])))
     continue
    if data[0]==14:
     lib.set_responsei(duel,option_index)
     continue
    if data[0] in (21,25):
     lib.set_responseb(duel,C.create_string_buffer(bytes(range(data[2]))))
     continue
    if data[0] in (12,13):
     lib.set_responsei(duel,1)
     continue
    if data[0]==16:
     lib.set_responsei(duel,0 if data[2] else -1)
     continue
    if data[0]==19:
     lib.set_responsei(duel,1)
     continue
    assert data[0]==18,("unexpected prompt",list(data),logs)
    mask=int.from_bytes(data[3:7],"little")
    bit=next(i for i in range(16) if not mask & (1<<i))
    response=C.create_string_buffer(bytes([data[1],4 if bit<8 else 8,bit%8]))
    lib.set_responseb(duel,response)
   if any(k==1 for k,s in logs):raise AssertionError(logs)
   if any(s=='RESOLUTION PASS' for k,s in logs):break
  else:raise AssertionError(('resolution did not finish',logs,result))
  print(name,logs)
 finally:lib.end_duel(duel)

run_resolution("Birth cost + real material movement + real Fusion Summon")

for destination,action in [('grave','Duel.SendtoGrave(c,REASON_EFFECT)'),('banished','Duel.Remove(c,POS_FACEUP,REASON_EFFECT)')]:
 logs.clear()
 extra['script/probe.lua']=fixture("""
local c=Debug.AddCard(98013001,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local driver=Debug.AddCard(98013003,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local b=Debug.AddCard(98013002,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local fc=Debug.AddCard(98013013,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
""","""
Duel.SortDecktop=function(tp,p,count) assert(count==2) end
Group.Select=function(g,tp,min,max,excluded) return Group.FromCards(g:GetFirst()) end
Duel.SelectFusionMaterial=function(tp,target,mg,mandatory,chkf)
 assert(target==fc and mandatory==c,"mandatory handler lost")
 assert(fc:CheckFusionMaterial(mg,c,tp))
 return Group.FromCards(c,b)
end
local observer=Effect.CreateEffect(fc)
observer:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
observer:SetCode(EVENT_SPSUMMON_SUCCESS)
observer:SetOperation(function(e)
 if fc:IsLocation(LOCATION_MZONE) then
  assert(c:IsLocation(LOCATION_DECK) and b:IsLocation(LOCATION_DECK))
  Debug.Message("RESOLUTION PASS")
 end
end)
Duel.RegisterEffect(observer,0)
local run=Effect.CreateEffect(driver)
run:SetDescription(999999)
run:SetType(EFFECT_TYPE_IGNITION)
run:SetRange(LOCATION_MZONE)
run:SetOperation(function(e) e:Reset(); ACTION end)
driver:RegisterEffect(run)
""".replace('ACTION',action))
 run_resolution('Real trigger event '+destination)

for bottom in [False,True]:
 logs.clear()
 extra['script/probe.lua']=fixture("""
local c=Debug.AddCard(98013008,0,0,SOURCE,0,POS_FACEUP_ATTACK)
local a=Debug.AddCard(98013001,0,0,MATERIAL,0,POS_FACEUP_ATTACK)
local b=Debug.AddCard(98013002,0,0,MATERIAL,0,POS_FACEUP_ATTACK)
local fc=Debug.AddCard(98013013,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
""".replace('SOURCE','LOCATION_GRAVE' if bottom else 'LOCATION_HAND').replace('MATERIAL','LOCATION_REMOVED' if bottom else 'LOCATION_DECK'),"""
Duel.SortDecktop=function(tp,p,count) assert(count==2) end
Group.Select=function(g,tp,min,max,excluded) return Group.FromCards(g:GetFirst()) end
Duel.SelectFusionMaterial=function(tp,target,mg,mandatory,chkf)
 assert(target==fc and mandatory==nil)
 assert(fc:CheckFusionMaterial(mg,nil,tp))
 return Group.FromCards(a,b)
end
local observer=Effect.CreateEffect(fc)
observer:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
observer:SetCode(EVENT_SPSUMMON_SUCCESS)
observer:SetOperation(function(e)
 if fc:IsLocation(LOCATION_MZONE) then
  assert(a:IsLocation(DESTINATION) and b:IsLocation(DESTINATION))
  COSTCHECK
  Debug.Message("RESOLUTION PASS")
 end
end)
Duel.RegisterEffect(observer,0)
""".replace('DESTINATION','LOCATION_DECK' if bottom else 'LOCATION_GRAVE').replace('COSTCHECK','assert(c:IsLocation(LOCATION_DECK))' if bottom else ''))
 run_resolution('Real Birth activation '+('2' if bottom else '1'))
