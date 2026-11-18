"""Revised optional Fusion materials, Forerunner search, King follow-up chain."""
import pathlib,runpy
previous=runpy.run_path(str(pathlib.Path(__file__).with_name('check_alpha22_effects.py')))
state=previous['state'];fixture=state['fixture'];extra=state['extra'];logs=state['logs'];run=state['run_resolution'];test=state['test']
FILL=previous['FILL'];DRIVER=previous['DRIVER'];CAP=previous['CAP']
chaincase=previous['chaincase']
for code in [98013001,98013002,98013003,98013004,98013005,98013013,98013020]:
 for removed in [False,True]:
  chaincase(f'{code} Fusion without using handler removed={removed}',f'''
local c=Debug.AddCard({code},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local a=Debug.AddCard(98013001,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local b=Debug.AddCard(98013005,0,0,LOCATION_REMOVED,0,POS_FACEUP_ATTACK)
local fc=Debug.AddCard(98013013,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
''','''
Group.Select=function(g,tp,min,max,excluded) return Group.FromCards(fc) end
Duel.SelectFusionMaterial=function(tp,target,mg,mandatory,chkf)
 assert(mandatory==nil and target==fc)
 assert(mg:IsContains(c) and mg:IsContains(a) and mg:IsContains(b))
 assert(fc:CheckFusionMaterial(Group.FromCards(a,b),nil,tp))
 return Group.FromCards(a,b)
end
Duel.SortDecktop=function() end
''',f'''if fc:IsLocation(LOCATION_MZONE) then
 assert(c:IsLocation({'LOCATION_REMOVED' if removed else 'LOCATION_GRAVE'}),"handler was forced into materials")
 assert(a:IsLocation(LOCATION_DECK) and b:IsLocation(LOCATION_DECK) and fc:IsSummonType(SUMMON_TYPE_FUSION))
 Debug.Message("RESOLUTION PASS") end''','Duel.Remove(c,POS_FACEUP,REASON_EFFECT)' if removed else 'Duel.SendtoGrave(c,REASON_EFFECT)')
# Moving the source after activation must not stop an effect that no longer needs it.
chaincase('Fusion resolves after source leaves GY','''
local c=Debug.AddCard(98013001,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local a=Debug.AddCard(98013001,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local b=Debug.AddCard(98013005,0,0,LOCATION_REMOVED,0,POS_FACEUP_ATTACK)
local fc=Debug.AddCard(98013013,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
''','''
Group.Select=function(g,tp,min,max,excluded) return Group.FromCards(fc) end
Duel.SelectFusionMaterial=function(tp,target,mg,mandatory,chkf)
 assert(mandatory==nil and not mg:IsContains(c));return Group.FromCards(a,b)
end
Duel.SortDecktop=function() end
local move=Effect.CreateEffect(driver)
move:SetType(EFFECT_TYPE_QUICK_O)
move:SetCode(EVENT_CHAINING)
move:SetRange(LOCATION_MZONE)
move:SetCountLimit(1)
move:SetCondition(function(e,tp,eg,ep,ev,re) return re:GetHandler()==c and re:GetCode()==EVENT_TO_GRAVE end)
move:SetOperation(function() Duel.SendtoDeck(c,nil,SEQ_DECKBOTTOM,REASON_EFFECT) end)
driver:RegisterEffect(move)
''','if fc:IsLocation(LOCATION_MZONE) then assert(c:IsLocation(LOCATION_DECK));Debug.Message("RESOLUTION PASS") end','Duel.SendtoGrave(c,REASON_EFFECT)')
# Search any archetype card, for both Normal and Special Summon, across all areas.
for normal in [False,True]:
 for loc in ['LOCATION_DECK','LOCATION_GRAVE','LOCATION_REMOVED']:
  chaincase(f'Forerunner any-card search normal={normal} source={loc}',f'''
local c=Debug.AddCard(98013020,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local selected=Debug.AddCard(98013006,0,0,{loc},0,POS_FACEUP_ATTACK)
''','''Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 assert(filter(selected,...));return Group.FromCards(selected)
end
''','if selected:IsLocation(LOCATION_HAND) then Debug.Message("RESOLUTION PASS") end','Duel.Summon(0,c,true,nil)' if normal else 'Duel.SpecialSummon(c,0,0,0,false,false,POS_FACEUP)')
# King may summon onto an empty board, choose the follow-up, or decline it.
for banish in [False,True]:
 logs.clear()
 extra['script/probe.lua']=fixture(CAP+'''
local c=Debug.AddCard(98013017,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local cost=Debug.AddCard(98013006,0,0,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE)
'''+('local driver=Debug.AddCard(99998001,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n' if not banish else '')+FILL,'''
for _,e in ipairs(effects[c]) do if e:IsHasType(EFFECT_TYPE_IGNITION) then e:SetDescription(999999) end end
local native=Effect.CreateEffect
local chains=0
local ssended=false
if driver then
 local confirm=Effect.CreateEffect(driver)
 confirm:SetDescription(999999)
 confirm:SetType(EFFECT_TYPE_IGNITION)
 confirm:SetRange(LOCATION_HAND)
 confirm:SetCondition(function() return ssended end)
 confirm:SetCountLimit(1)
 confirm:SetOperation(function()
  assert(chains==1 and c:IsLocation(LOCATION_MZONE),"optional banish was not declined")
  Debug.Message("RESOLUTION PASS")
 end)
 driver:RegisterEffect(confirm)
end
local watch=Effect.CreateEffect(c)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_CHAIN_END)
watch:SetOperation(function()
 chains=chains+1
 if chains==1 then assert(c:IsLocation(LOCATION_MZONE),"summon must finish before banish chain");ssended=true end
 CHECK
end)
Duel.RegisterEffect(watch,0)
local inspect=Effect.CreateEffect(c)
inspect:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
inspect:SetCode(EVENT_CHAINING)
inspect:SetOperation(function(e,tp,eg,ep,ev,re)
 if re:GetCode()==EVENT_CUSTOM+98013017 then assert(ssended and Duel.GetCurrentChain()==1,"follow-up must start a new chain") end
end)
Duel.RegisterEffect(inspect,0)
'''.replace('CHECK','if c:IsLocation(LOCATION_REMOVED) then assert(chains>=2);Debug.Message("RESOLUTION PASS") end' if banish else ''))
 run(f'King empty-board summon, banish={banish}',yes_no=1 if banish else 0,activations=1 if banish else 2)
# A normal revival must not create the self-summon follow-up event.
chaincase('King revival has no banish follow-up','''
local c=Debug.AddCard(98013017,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK,true)
''','''
local watch=Effect.CreateEffect(driver)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_CHAINING)
watch:SetOperation(function(e,tp,eg,ep,ev,re) assert(re:GetCode()~=EVENT_CUSTOM+98013017,"revival raised hand-summon event") end)
Duel.RegisterEffect(watch,0)
''','if c:IsLocation(LOCATION_MZONE) then Debug.Message("RESOLUTION PASS") end','Duel.SpecialSummon(c,0,0,0,false,false,POS_FACEUP)')
