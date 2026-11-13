"""Native recovery-effect regressions, including Alpha 0.12's 55 scenarios."""
import pathlib
import runpy
previous=runpy.run_path(str(pathlib.Path(__file__).with_name('check_alpha12_effects.py')))
state=previous['state']
fixture=state['fixture'];extra=state['extra'];logs=state['logs'];run=state['run_resolution'];test=state['test']

for code in [98013006,98013007,98013010]:
 for location in ['LOCATION_GRAVE','LOCATION_REMOVED']:
  logs.clear()
  setup=f'''
local registered={{}}
local native=Card.RegisterEffect
Card.RegisterEffect=function(c,e,...)
 if c:GetCode()=={code} and e:IsHasType(EFFECT_TYPE_IGNITION) then registered[c]=e end
 return native(c,e,...)
end
local c=Debug.AddCard({code},0,0,{location},0,POS_FACEUP_ATTACK)
local copy=Debug.AddCard({code},0,0,{location},0,POS_FACEUP_ATTACK)
local own=Debug.AddCard(98013005,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
local other=Debug.AddCard(98013009,1,1,LOCATION_REMOVED,0,POS_FACEDOWN_DEFENSE)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
'''
  # Avoid multiple simultaneously legal copies obscuring selection; whichever copy activates is the source.
  body=f'''
local activated=nil
local before_resolve=false
Duel.SelectMatchingCard=function(tp,filter,p,loc1,loc2,min,max,excluded,...)
 assert(min==1 and max==4 and excluded:GetCode()==98013006)
 assert(filter(own,...) and filter(other,...))
 return Group.FromCards(own,other)
end
local watch=Effect.CreateEffect(c)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_CHAINING)
watch:SetOperation(function(e,tp,eg,ep,ev,re)
 if re:GetHandler():GetCode()=={code} then
  activated=re:GetHandler()
  BEFORE
  before_resolve=true
 end
end)
Duel.RegisterEffect(watch,0)
local finish=Effect.CreateEffect(c)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 assert(before_resolve and activated,"actual recovery effect did not activate")
 AFTER
 assert(not registered[c]:CheckCountLimit(0) and not registered[copy]:CheckCountLimit(0),"same-name recovery limit not shared")
 if {code}==98013006 then assert(c:GetActivateEffect():CheckCountLimit(0),"effect 1 limit must be separate") end
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(finish,0)
'''
  if code==98013006:
   before='assert(own:IsLocation(LOCATION_DECK) and other:IsLocation(LOCATION_DECK),"bottom-deck cost was not paid before activation"); assert(own:GetSequence()==0 and other:GetSequence()==0)'
   after='assert(activated:IsLocation(LOCATION_HAND) and Duel.GetFieldGroupCount(0,LOCATION_HAND,0)==1)'
  elif code==98013007:
   before='assert(activated:IsLocation(LOCATION_DECK) and activated:IsReason(REASON_COST),"self-return cost not paid")'
   after='assert(Duel.GetFieldGroupCount(0,LOCATION_HAND,0)==2,"two cards were not drawn")'
  else:
   before='assert(Duel.GetFieldGroupCount(0,LOCATION_HAND,0)==1,"draw cost not paid before activation")'
   after='assert(activated:IsLocation(LOCATION_HAND) and Duel.GetFieldGroupCount(0,LOCATION_HAND,0)==2,"draw plus recovery failed")'
  extra['script/probe.lua']=fixture(setup,body.replace('BEFORE',before).replace('AFTER',after))
  run(f'{code} recovery from {location} and same-name limit')

# Cost requirements and face-down banishment do not require a running chain to inspect.
for code in [98013006,98013007,98013010]:
 test(f'{code} facedown banished effect unavailable',fixture(f'''
local c=Debug.AddCard({code},0,0,LOCATION_REMOVED,0,POS_FACEDOWN_DEFENSE)
''',f'''
local e=Effect.CreateEffect(c)
e:SetType(EFFECT_TYPE_SINGLE);e:SetCode(EFFECT_UPDATE_ATTACK);e:SetValue(0);c:RegisterEffect(e)
assert(not c{code}.recovercondition(e))
'''))
for code in [98013006,98013010]:
 test(f'{code} missing cost prerequisite',fixture(f'''
local c=Debug.AddCard({code},0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
''',f'''
local e=Effect.CreateEffect(c)
e:SetType(EFFECT_TYPE_SINGLE);e:SetCode(EFFECT_UPDATE_ATTACK);e:SetValue(0);c:RegisterEffect(e)
assert(not c{code}.recovercost(e,0,nil,0,0,nil,0,0,0))
'''))

# Negating recovery must not undo already-paid costs.
for code in [98013006,98013007,98013010]:
 logs.clear()
 extra['script/probe.lua']=fixture(f'''
local c=Debug.AddCard({code},0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
local magician=Debug.AddCard(98013004,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local costcard=Debug.AddCard(98013005,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
Duel.SelectMatchingCard=function(tp,filter,p,loc1,loc2,min,max,excluded,...)
 assert(filter(costcard,...))
 return Group.FromCards(costcard)
end
local finish=Effect.CreateEffect(c)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 assert(magician:IsLocation(LOCATION_GRAVE),"opponent's negation did not resolve")
 CHECK
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(finish,0)
'''.replace('CHECK',{
 98013006:'assert(costcard:IsLocation(LOCATION_DECK) and c:IsLocation(LOCATION_REMOVED)); assert(Duel.GetFieldGroupCount(0,LOCATION_HAND,0)==0)',
 98013007:'assert(c:IsLocation(LOCATION_DECK)); assert(Duel.GetFieldGroupCount(0,LOCATION_HAND,0)==0)',
 98013010:'assert(c:IsLocation(LOCATION_REMOVED)); assert(Duel.GetFieldGroupCount(0,LOCATION_HAND,0)==1)'
 }[code]))
 run(f'{code} recovery negated: costs persist')

for count in [1,4]:
 logs.clear()
 extra['script/probe.lua']=fixture('''
local c=Debug.AddCard(98013006,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
local a=Debug.AddCard(98013001,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
local b=Debug.AddCard(98013002,0,0,LOCATION_REMOVED,0,POS_FACEUP_ATTACK)
local x=Debug.AddCard(98013003,1,1,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
local y=Debug.AddCard(98013009,1,1,LOCATION_REMOVED,0,POS_FACEDOWN_DEFENSE)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''',f'''
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 assert(excluded==c and min==1 and max==4)
 return {'Group.FromCards(a)' if count==1 else 'Group.FromCards(a,b,x,y)'}
end
local observer=Effect.CreateEffect(c)
observer:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
observer:SetCode(EVENT_CHAIN_END)
observer:SetOperation(function()
 assert(c:IsLocation(LOCATION_HAND) and a:IsLocation(LOCATION_DECK) and a:GetSequence()<2)
 CHECK
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(observer,0)
'''.replace('CHECK','assert(b:IsLocation(LOCATION_DECK) and x:IsLocation(LOCATION_DECK) and y:IsLocation(LOCATION_DECK)); assert(b:GetSequence()<2 and x:GetSequence()<2 and y:GetSequence()<2)' if count==4 else 'assert(b:IsLocation(LOCATION_REMOVED) and x:IsLocation(LOCATION_GRAVE) and y:IsLocation(LOCATION_REMOVED))'))
 run(f'Omen returns {count} cost cards and sorts bottom')
