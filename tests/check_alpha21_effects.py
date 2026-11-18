"""Native tests for four new cards, including previous regressions."""
import pathlib,runpy
previous=runpy.run_path(str(pathlib.Path(__file__).with_name('check_alpha20_effects.py')))
state=previous['state'];fixture=state['fixture'];extra=state['extra'];logs=state['logs'];run=state['run_resolution'];test=state['test']
FILL='for p=0,1 do for i=1,10 do Debug.AddCard(98013006,p,p,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end\n'
CAP='''local effects={}
local native=Card.RegisterEffect
Card.RegisterEffect=function(card,e,...)
 if card:GetCode()>=98013016 and card:GetCode()<=98013019 then
  effects[card]=effects[card] or {};table.insert(effects[card],e)
 end
 return native(card,e,...)
end
'''
DRIVER='''local driver=Debug.AddCard(99998001,0,0,LOCATION_MZONE,4,POS_FACEUP_ATTACK)
'''
def resolve(name,cards,operation,check,setup=''):
 logs.clear()
 extra['script/probe.lua']=fixture(CAP+cards+DRIVER+FILL,setup+'''
local action=Effect.CreateEffect(driver)
action:SetDescription(999999)
action:SetType(EFFECT_TYPE_IGNITION)
action:SetRange(LOCATION_MZONE)
action:SetCountLimit(1)
action:SetOperation(function(e) OPERATION end)
driver:RegisterEffect(action)
local watch=Effect.CreateEffect(driver)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_ADJUST)
watch:SetOperation(function() if CHECK then Debug.Message("RESOLUTION PASS") end end)
Duel.RegisterEffect(watch,0)
'''.replace('OPERATION',operation).replace('CHECK',check))
 run(name)
# Actual hand ignition effects: native costs, summons and delayed triggers.
for code in [98013016,98013017]:
 logs.clear()
 extra['script/probe.lua']=fixture(CAP+f'''
local c=Debug.AddCard({code},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local cost=Debug.AddCard(98013006,0,0,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE)
local enemy=Debug.AddCard(99998001,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
'''+FILL,'''
local ignition
for _,e in ipairs(effects[c]) do if bit.band(e:GetType(),EFFECT_TYPE_IGNITION)~=0 then ignition=e;e:SetDescription(999999) end end
local watch=Effect.CreateEffect(c)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_ADJUST)
watch:SetOperation(function()
 if c:IsLocation(LOCATION_MZONE) then
  assert(not ignition:CheckCountLimit(0),"hand ignition count not consumed")
  assert(Duel.GetMatchingGroupCount(Card.IsLocation,0,LOCATION_GRAVE,0,nil,LOCATION_GRAVE)>0,"deck destruction not paid")
  FINISH
 end
end)
Duel.RegisterEffect(watch,0)
'''.replace('FINISH','if Duel.GetFieldGroupCount(0,LOCATION_HAND,0)>=2 then Debug.Message("RESOLUTION PASS") end' if code==98013016 else 'if enemy:IsLocation(LOCATION_REMOVED) then assert(c:IsStatus(STATUS_PROC_COMPLETE));Debug.Message("RESOLUTION PASS") end'))
 run(f'{code} actual hand ignition + cost + follow-up',select_code=99998001 if code==98013017 else None)
# GY / banish delayed searches and Link recoveries.
for code in [98013016,98013017,98013018,98013019]:
 for removed in [False,True]:
  for destination in (['LOCATION_DECK','LOCATION_GRAVE','LOCATION_REMOVED'] if code in [98013016,98013017] else ['LOCATION_HAND','LOCATION_GRAVE','LOCATION_REMOVED'] if code==98013018 else ['LOCATION_GRAVE','LOCATION_REMOVED']):
   searched=98013006 if code!=98013018 else 98013005
   cards=f'local c=Debug.AddCard({code},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)\nlocal selected=Debug.AddCard({searched},0,0,{destination},0,POS_FACEUP_ATTACK)\n'
   setup='''Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 assert(filter(selected,...),"expected candidate rejected")
 return Group.FromCards(selected)
end
'''
   action='Duel.Remove(c,POS_FACEUP,REASON_EFFECT)' if removed else 'Duel.SendtoGrave(c,REASON_EFFECT)'
   check='selected:IsLocation(LOCATION_MZONE) and c:IsLocation(LOCATION_EXTRA)' if code==98013018 else 'selected:IsLocation(LOCATION_HAND)'+(' and c:IsLocation(LOCATION_EXTRA)' if code==98013019 else '')
   resolve(f'{code} {"banish" if removed else "GY"} trigger -> {destination}',cards,action,check,setup)
# Native Link procedures: non-archetype monster permitted for Link1, four archetype monsters for Link4.
for code in [98013018,98013019]:
 cards=f'local c=Debug.AddCard({code},0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)\nlocal materials=Group.CreateGroup()\n'
 for i in range(1 if code==98013018 else 4):cards+=f'materials:AddCard(Debug.AddCard({99998001 if code==98013018 else 98013001},0,0,LOCATION_MZONE,{i},POS_FACEUP_ATTACK))\n'
 setup='''Group.SelectSubGroup=function(g,tp,goal,cancel,min,max,...)
 assert(goal(materials,...),"native Link goal failed")
 return materials:Clone()
end
'''
 resolve(f'{code} actual Link Summon',cards,'Duel.LinkSummon(0,c,materials)',f'c:IsLocation(LOCATION_MZONE) and c:IsSummonType(SUMMON_TYPE_LINK) and c:GetMaterialCount()=={1 if code==98013018 else 4}'+(' and Duel.GetFieldGroupCount(0,LOCATION_HAND,0)>0' if code==98013018 else ''),setup)
# Material protection is conditional on the controller of the monster being summoned.
for code in [98013017,98013019]:
 test(f'{code} opponent-only material protection',fixture(f'''
local c=Debug.AddCard({code},0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)
local protected=Debug.AddCard(98013012,0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK,true)
local own=Debug.AddCard(98013019,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
local opponent=Debug.AddCard(98013019,1,1,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
''','''
for _,method in ipairs({Card.IsCanBeFusionMaterial,Card.IsCanBeSynchroMaterial,Card.IsCanBeXyzMaterial,Card.IsCanBeLinkMaterial}) do
 assert(method(protected,own),"own material use blocked")
 assert(not method(protected,opponent),"opponent material use allowed through immunity")
end

'''))
# Target protection applies to own Fusion monsters, not ordinary allies.
resolve('Watchkeeper Fusion target protection','local c=Debug.AddCard(98013018,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)\nlocal fusion=Debug.AddCard(98013014,1,1,LOCATION_MZONE,1,POS_FACEUP_ATTACK,true)\nlocal ally=Debug.AddCard(98013001,1,1,LOCATION_MZONE,2,POS_FACEUP_ATTACK)\n','assert(not fusion:IsCanBeEffectTarget(e));assert(ally:IsCanBeEffectTarget(e));done=true','done==true','local done=false\n')
# Tribute permissions evaluated in a real effect's player context.
for code in [98013017,98013019]:
 for owner in [0,1]:
  resolve(f'{code} tribute protection owner={owner}',f'local c=Debug.AddCard({code},{owner},{owner},LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)\n',f'assert(c:IsReleasable()=={str(owner==0).lower()},"tribute permission incorrect");done=true','done==true','local done=false\nfor _,eff in ipairs(effects[c]) do if eff:GetCode()==EVENT_CHAINING then eff:SetCondition(function() return false end) end end\n')
# No-tribute Normal Summon and its optional search.
logs.clear()
extra['script/probe.lua']=fixture('local c=Debug.AddCard(98013016,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)\n'+FILL,'''
local watch=Effect.CreateEffect(c)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_ADJUST)
watch:SetOperation(function()
 if c:IsLocation(LOCATION_MZONE) and c:IsSummonType(SUMMON_TYPE_NORMAL) and Duel.GetFieldGroupCount(0,LOCATION_HAND,0)>0 then Debug.Message("RESOLUTION PASS") end
end)
Duel.RegisterEffect(watch,0)
''')
run('Abyss no-tribute Normal Summon and search',first_command=0)
# End Dragon actual quick negation, and no response to own effect.
for owner in [0,1]:
 logs.clear()
 extra['script/probe.lua']=fixture(f'local c=Debug.AddCard(98013019,{owner},{owner},LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)\n'+DRIVER+FILL,'''
local resolved=false
local action=Effect.CreateEffect(driver)
action:SetDescription(999999)
action:SetType(EFFECT_TYPE_IGNITION)
action:SetRange(LOCATION_MZONE)
action:SetCountLimit(1)
action:SetOperation(function() resolved=true end)
driver:RegisterEffect(action)
local watch=Effect.CreateEffect(c)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_CHAIN_END)
watch:SetOperation(function()
 CHECK
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(watch,0)
'''.replace('CHECK','assert(not resolved and driver:IsLocation(LOCATION_GRAVE))' if owner else 'assert(resolved and driver:IsLocation(LOCATION_MZONE))'))
 run(f'End Dragon negate opponent / allow own owner={owner}')
