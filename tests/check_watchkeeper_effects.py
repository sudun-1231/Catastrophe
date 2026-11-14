"""Focused Watchkeeper II reproduction cases on the native MDPro3 core."""
import runpy,pathlib
p=runpy.run_path(str(pathlib.Path(__file__).with_name('check_alpha22_effects.py')))
s=p['state'];fixture=p['fixture'];run=p['run'];extra=p['extra'];logs=p['logs'];CAP=p['CAP'];FILL=p['FILL'];DRIVER=p['DRIVER']
for method in ['special','normal']:
 for source in ['LOCATION_DECK','LOCATION_GRAVE','LOCATION_REMOVED']:
  logs.clear()
  extra['script/probe.lua']=fixture(CAP+'''
local c=Debug.AddCard(98013018,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)
local ally=Debug.AddCard(98013001,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
'''+f'local selected=Debug.AddCard(98013006,0,0,{source},0,POS_FACEUP_ATTACK)\n'+DRIVER+FILL,'''
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 assert(filter(selected,...));return Group.FromCards(selected)
end
local action=Effect.CreateEffect(driver)
action:SetDescription(999999)
action:SetType(EFFECT_TYPE_IGNITION)
action:SetRange(LOCATION_MZONE)
action:SetCountLimit(1)
action:SetOperation(function() ACTION end)
driver:RegisterEffect(action)
local watch=Effect.CreateEffect(driver)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_CHAIN_END)
watch:SetOperation(function()
 if selected:IsLocation(LOCATION_HAND) then Debug.Message("RESOLUTION PASS") end
end)
Duel.RegisterEffect(watch,0)
'''.replace('ACTION','Duel.SpecialSummon(ally,0,0,0,false,false,POS_FACEUP)' if method=='special' else 'Duel.Summon(0,ally,true,nil)'))
  run(f'Watchkeeper ally {method}, source={source}')
# One use shared by Normal/Special Summon triggers and all copies of Watchkeeper.
for copies in [1,2]:
 logs.clear()
 extra['script/probe.lua']=fixture(CAP+'''
local c=Debug.AddCard(98013018,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)
local ally=Debug.AddCard(98013001,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local second=Debug.AddCard(98013001,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local selected=Debug.AddCard(98013006,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
'''+('local copy=Debug.AddCard(98013018,0,0,LOCATION_MZONE,3,POS_FACEUP_ATTACK,true)\n' if copies==2 else '')+DRIVER+FILL,'''
local searches=0
local operations=0
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 searches=searches+1
 assert(searches==1,"Watchkeeper search used more than once")
 assert(filter(selected,...));return Group.FromCards(selected)
end
local action=Effect.CreateEffect(driver)
action:SetDescription(999999)
action:SetType(EFFECT_TYPE_IGNITION)
action:SetRange(LOCATION_MZONE)
action:SetCountLimit(2)
action:SetOperation(function()
 operations=operations+1
 if operations==1 then Duel.SpecialSummon(ally,0,0,0,false,false,POS_FACEUP)
 else Duel.Summon(0,second,true,nil) end
end)
driver:RegisterEffect(action)
local watch=Effect.CreateEffect(driver)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_CHAIN_END)
watch:SetOperation(function()
 if searches==1 and operations==2 then
  for card,list in pairs(effects) do
   if card:GetCode()==98013018 then
    for _,e in ipairs(list) do
     if e:GetCode()==EVENT_SUMMON_SUCCESS or e:GetCode()==EVENT_SPSUMMON_SUCCESS then
      assert(not e:CheckCountLimit(0),"normal and special triggers must share named HOPT")
     end
    end
   end
  end
  Debug.Message("RESOLUTION PASS")
 end
end)
Duel.RegisterEffect(watch,0)
''')
 run(f'Watchkeeper named once-per-turn, copies={copies}',activations=2)
# The two registration paths must not both claim a lone self summon.
s['test']('Watchkeeper separates own Summon from other summons',fixture(CAP+'''
local c=Debug.AddCard(98013018,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)
local ally=Debug.AddCard(98013001,0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)
''','''
local own,other=0,0
for _,e in ipairs(effects[c]) do
 if e:GetCode()==EVENT_SPSUMMON_SUCCESS then
  if e:IsHasType(EFFECT_TYPE_SINGLE) then
   own=own+1;assert(e:GetCondition()(e,0,Group.FromCards(c)))
  elseif e:IsHasType(EFFECT_TYPE_FIELD) then
   other=other+1
   assert(not e:GetCondition()(e,0,Group.FromCards(c)))
   assert(e:GetCondition()(e,0,Group.FromCards(ally)))
  end
 end
end
assert(own==1 and other==1)
'''))
logs.clear()
extra['script/probe.lua']=fixture(CAP+'''
local c=Debug.AddCard(98013018,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK,true)
local ally=Debug.AddCard(98013001,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local selected=Debug.AddCard(98013006,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
'''+DRIVER+FILL,'''
local searches=0
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 searches=searches+1;assert(searches==1,"simultaneous summon produced duplicate search")
 assert(filter(selected,...));return Group.FromCards(selected)
end
local action=Effect.CreateEffect(driver)
action:SetDescription(999999)
action:SetType(EFFECT_TYPE_IGNITION)
action:SetRange(LOCATION_MZONE)
action:SetCountLimit(1)
action:SetOperation(function() Duel.SpecialSummon(Group.FromCards(c,ally),0,0,0,false,false,POS_FACEUP) end)
driver:RegisterEffect(action)
local watch=Effect.CreateEffect(driver)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_CHAIN_END)
watch:SetOperation(function()
 if selected:IsLocation(LOCATION_HAND) then
  assert(searches==1 and c:IsLocation(LOCATION_MZONE) and ally:IsLocation(LOCATION_MZONE))
  for _,e in ipairs(effects[c]) do
   if e:GetCode()==EVENT_SUMMON_SUCCESS or e:GetCode()==EVENT_SPSUMMON_SUCCESS then assert(not e:CheckCountLimit(0)) end
  end
  Debug.Message("RESOLUTION PASS")
 end
end)
Duel.RegisterEffect(watch,0)
''')
run('Watchkeeper simultaneous self + ally summon searches once')
