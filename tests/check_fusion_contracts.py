"""Lua 5.4 registration/filter regression checks using a mocked duel API.

Run: python3 tests/check_fusion_contracts.py
Optional: --fusion-procedure /path/to/ProjectIgnis/proc_fusion.lua
This does not emulate a duel or prove MDPro3 engine compatibility.
"""
import argparse
import ctypes
import ctypes.util
import pathlib
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
CARDS = (98013001, 98013002, 98013003, 98013004, 98013005, 98013013)
parser = argparse.ArgumentParser()
parser.add_argument('--fusion-procedure', type=pathlib.Path)
args = parser.parse_args()
lua = ctypes.CDLL(ctypes.util.find_library('lua5.4') or 'liblua5.4.so.0')
lua.luaL_newstate.restype = ctypes.c_void_p
lua.luaL_openlibs.argtypes = [ctypes.c_void_p]
lua.luaL_loadstring.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
lua.lua_pcallk.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_longlong, ctypes.c_void_p]
lua.lua_tolstring.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
lua.lua_tolstring.restype = ctypes.c_char_p
lua.lua_close.argtypes = [ctypes.c_void_p]

HARNESS = r'''
local constants={"LOCATION_HAND","LOCATION_MZONE","LOCATION_GRAVE","LOCATION_REMOVED",
 "EFFECT_TYPE_SINGLE","EFFECT_TYPE_TRIGGER_O","EFFECT_TYPE_FIELD","EFFECT_TYPE_QUICK_O",
 "EFFECT_FLAG_DELAY","EFFECT_FLAG_UNCOPYABLE","EVENT_TO_GRAVE","EVENT_REMOVE",
 "EVENT_SUMMON_SUCCESS","EVENT_SPSUMMON_SUCCESS","EVENT_CHAINING","EFFECT_SPSUMMON_PROC",
 "CATEGORY_TOHAND","CATEGORY_TODECK","CATEGORY_SPECIAL_SUMMON","CATEGORY_FUSION_SUMMON",
 "CATEGORY_NEGATE","CATEGORY_DESTROY","EFFECT_COUNT_CODE_OATH","STATUS_COPYING_EFFECT"}
for i,name in ipairs(constants) do _G[name]=1 << (i-1) end
aux={TRUE=function() return true end, Stringid=function() return 0 end}
function aux.FunctionWithNamedArgs(fn,...)
 local names={...}
 return function(...)
  local args={...}
  if type(args[1])=='table' then
   local values={}
   for i,name in ipairs(names) do values[i]=args[1][name] end
   return fn(table.unpack(values,1,#names))
  end
  return fn(...)
 end
end
Card={IsAbleToDeck=function(c) return c.able end}
Duel={}
local methods={}
for _,key in ipairs({'Description','Category','Type','Property','Code','CountLimit','Condition','Target','Operation','Range','Value'}) do
 methods['Set'..key]=function(self,...) self[key]={...} end
end
function methods:Clone()
 local copy=setmetatable({}, {__index=methods})
 for key,val in pairs(self) do copy[key]=val end
 return copy
end
function methods:GetHandler() return self.handler end
Effect={CreateEffect=function(c) return setmetatable({handler=c},{__index=methods}) end}
Fusion={ForcedHandler=function(e) return e:GetHandler() end}
-- If provided, load the official procedure and use its actual AddProcMixN.
if REFERENCE then aux.FusionProcedure=Fusion; dofile(REFERENCE) end
local captured
Fusion.AddProcMix=function(c,sub,insf,...)
 captured={...}
end
if not REFERENCE then
 Fusion.AddProcMixN=function(c,sub,insf,filter,count)
  assert(type(filter)=='function','missing Fusion material predicate')
  captured={}
  for i=1,count do captured[i]=filter end
 end
end
Fusion.SummonEffTG=function(p) assert(type(p)=='table'); return function() return p end end
Fusion.SummonEffOP=function(p) assert(type(p)=='table'); return function() return p end end
local s={}
GetID=function() return s,CARD_ID end
dofile(SCRIPT_PATH)
local c={effects={}}
function c:RegisterEffect(e) table.insert(self.effects,e) end
function c:EnableReviveLimit() end
function c:IsStatus() return false end
s.initial_effect(c)
if CARD_ID==98013013 then
 assert(captured and #captured==2,'missing two-material Fusion procedure')
 for _,filter in ipairs(captured) do
  assert(type(filter)=='function','missing Fusion material predicate')
  assert(filter({IsSetCard=function(_,set) return set==0xfcb end}))
  assert(not filter({IsSetCard=function() return false end}))
 end
end
local grave,removed,search
for _,eff in ipairs(c.effects) do
 if eff.Code and eff.Code[1]==EVENT_TO_GRAVE then grave=eff end
 if eff.Code and eff.Code[1]==EVENT_REMOVE then removed=eff end
 if eff.Code and eff.Code[1]==EVENT_SUMMON_SUCCESS then search=eff end
end
assert(grave and removed,'both event registrations required')
for _,eff in ipairs({grave,removed}) do
 assert(eff.Type[1]==EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
 assert(eff.Property[1]==EFFECT_FLAG_DELAY)
 assert(eff.CountLimit[1]==1 and eff.CountLimit[2][1]==CARD_ID and eff.CountLimit[2][2]==2)
 local p=eff.Target[1]()
 assert(p.gc(eff)==c,'handler must be mandatory')
 assert(p.matfilter==Card.IsAbleToDeck)
 assert(p.extrafil==s.fus_extramat and p.extraop==s.fus_extraop and p.extratg==s.fus_extratg)
 assert(eff.Operation[1]()==p,'target and operation must share parameters')
end
assert(grave.CountLimit[2]==removed.CountLimit[2],'clones must share the same limit')
if search then
 assert(type(search.CountLimit[2])=='table' and search.CountLimit[2][1]==CARD_ID and search.CountLimit[2][2]==1,
  'search limit must not collide with another card ID or fusion effect')
end
local function mat(loc,face,monster,able)
 return {IsLocation=function(_,mask) return (loc & mask)~=0 end,
 IsFaceup=function() return face end,IsMonster=function() return monster end,
 IsAbleToDeck=function() return able end}
end
assert(s.fus_matfilter(mat(LOCATION_GRAVE,false,true,true)))
assert(s.fus_matfilter(mat(LOCATION_REMOVED,true,true,true)))
assert(not s.fus_matfilter(mat(LOCATION_REMOVED,false,true,true)))
assert(not s.fus_matfilter(mat(LOCATION_GRAVE,true,false,true)))
assert(not s.fus_matfilter(mat(LOCATION_GRAVE,true,true,false)))
local mask
Duel.GetMatchingGroup=function(filter,tp,own,other,exclude)
 assert(filter==s.fus_matfilter and tp==0 and other==0 and exclude==nil)
 mask=own
 return 'extra-materials'
end
assert(s.fus_extramat(grave,0,nil)=='extra-materials')
assert(mask==(LOCATION_GRAVE|LOCATION_REMOVED))
assert(removed.Condition[1]({GetHandler=function() return mat(LOCATION_REMOVED,true,true,true) end}))
assert(not removed.Condition[1]({GetHandler=function() return mat(LOCATION_REMOVED,false,true,true) end}))
'''


def run(card, path):
    # Lua long strings avoid shell interpolation; generated paths have no closing delimiter.
    prefix = f'CARD_ID={card}; SCRIPT_PATH=[==[{path}]==]; '
    if args.fusion_procedure:
        prefix += f'REFERENCE=[==[{args.fusion_procedure.resolve()}]==]; '
    state = lua.luaL_newstate()
    if not state:
        raise RuntimeError('Lua allocation failed')
    try:
        lua.luaL_openlibs(state)
        result = lua.luaL_loadstring(state, (prefix + HARNESS).encode())
        if not result:
            result = lua.lua_pcallk(state, 0, 0, 0, 0, None)
        return lua.lua_tolstring(state, -1, None).decode() if result else None
    finally:
        lua.lua_close(state)


for card in CARDS:
    error = run(card, ROOT / f'script/c{card}.lua')
    assert error is None, f'{card}: {error}'
    print(f'PASS c{card}: registration, limits, material filters, forced-handler wiring')
with tempfile.TemporaryDirectory() as folder:
    with zipfile.ZipFile(ROOT / 'Catastrophe_MDPro3_alpha_v08_garura.ypk') as pack:
        for card in (98013001, 98013013):
            path = pathlib.Path(folder) / f'c{card}.lua'
            path.write_bytes(pack.read(f'script/c{card}.lua'))
            error = run(card, path)
            assert error is not None, f'Original {card} unexpectedly passed'
            print(f'EXPECTED REGRESSION c{card}: {error}')
print('6 updated scripts passed. Mock checks do not validate duel execution.')
