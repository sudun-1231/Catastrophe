"""Danger detection recovery tests and previous native regressions."""
import pathlib
import runpy
previous=runpy.run_path(str(pathlib.Path(__file__).with_name('check_alpha15_effects.py')))
state=previous['state']
fixture=state['fixture'];extra=state['extra'];logs=state['logs'];run=state['run_resolution'];test=state['test']

for location in ['LOCATION_GRAVE','LOCATION_REMOVED']:
 for owner in [0,1]:
  logs.clear()
  extra['script/probe.lua']=fixture(f'''
local registered={{}}
local native=Card.RegisterEffect
Card.RegisterEffect=function(c,e,...)
 if c:GetCode()==98013009 and e:IsHasType(EFFECT_TYPE_IGNITION) then registered[c]=e end
 return native(c,e,...)
end
local spell=Debug.AddCard(98013009,0,0,{location},0,POS_FACEUP_ATTACK)
local copy=Debug.AddCard(98013009,0,0,{location},0,POS_FACEUP_ATTACK)
local target=Debug.AddCard(98013005,{owner},{owner},LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local other=Debug.AddCard(98013005,{1-owner},{1-owner},LOCATION_MZONE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local activated=nil
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 assert(filter(target,...))
 return Group.FromCards(target)
end
local watch=Effect.CreateEffect(spell)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_CHAINING)
watch:SetOperation(function(e,tp,eg,ep,ev,re)
 if re:GetHandler():GetCode()==98013009 then
  activated=re:GetHandler()
  assert(target:IsDisabled(),"negation cost must be paid before activation")
 end
end)
Duel.RegisterEffect(watch,0)
local finish=Effect.CreateEffect(spell)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 assert(activated and activated:IsLocation(LOCATION_HAND))
 assert(target:IsDisabled() and not other:IsDisabled())
 assert(not registered[spell]:CheckCountLimit(0) and not registered[copy]:CheckCountLimit(0))
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(finish,0)
''')
  run(f'Danger recovery from {location}, negate player {owner} card, shared limit')

for issue in ['facedown','already disabled','cannot disable','immune','no field cards']:
 card='98013012' if issue=='immune' else '98013005'
 setup='local target=Debug.AddCard(CARD,0,0,LOCATION_MZONE,0,POS)'.replace('CARD',card).replace('POS','POS_FACEDOWN_DEFENSE' if issue=='facedown' else 'POS_FACEUP_ATTACK') if issue!='no field cards' else ''
 if issue in ['already disabled','cannot disable']:
  setup+='''
local protection=Effect.CreateEffect(target)
protection:SetType(EFFECT_TYPE_SINGLE)
protection:SetCode(CODE)
protection:SetValue(1)
target:RegisterEffect(protection)
Duel.AdjustInstantly(target)
'''.replace('CODE','EFFECT_DISABLE' if issue=='already disabled' else 'EFFECT_CANNOT_DISABLE')
 test('Danger cannot pay cost: '+issue,fixture('''
local spell=Debug.AddCard(98013009,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
'''+setup,'''
local e=Effect.CreateEffect(spell)
e:SetType(EFFECT_TYPE_SINGLE);e:SetCode(EFFECT_UPDATE_ATTACK);e:SetValue(0);spell:RegisterEffect(e)
assert(not c98013009.recovercost(e,0,nil,0,0,nil,0,0,0))
'''))

test('Danger facedown banished source cannot activate',fixture('''
local spell=Debug.AddCard(98013009,0,0,LOCATION_REMOVED,0,POS_FACEDOWN_DEFENSE)
''','''
local e=Effect.CreateEffect(spell)
e:SetType(EFFECT_TYPE_SINGLE);e:SetCode(EFFECT_UPDATE_ATTACK);e:SetValue(0);spell:RegisterEffect(e)
assert(not c98013009.recovercondition(e))
'''))

logs.clear()
extra['script/probe.lua']=fixture('''
local spell=Debug.AddCard(98013009,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
local target=Debug.AddCard(98013005,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local magician=Debug.AddCard(98013004,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...) return Group.FromCards(target) end
local finish=Effect.CreateEffect(spell)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 assert(spell:IsLocation(LOCATION_REMOVED) and magician:IsLocation(LOCATION_GRAVE))
 assert(Duel.GetFieldGroupCount(0,LOCATION_HAND,0)==0,"negated recovery returned the spell")
 assert(target:IsDisabled(),"paid negation cost must remain")
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(finish,0)
''')
run('Danger recovery negated: field negation cost remains')

logs.clear()
extra['script/probe.lua']=fixture('''
local spell=Debug.AddCard(98013009,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
local target=Debug.AddCard(98013005,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...) return Group.FromCards(target) end
local finish=Effect.CreateEffect(spell)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_ADJUST)
finish:SetOperation(function()
 if Duel.GetCurrentPhase()==PHASE_END and spell:IsLocation(LOCATION_HAND) then
  assert(target:IsDisabled(),"unspecified duration must not reset at End Phase")
  Debug.Message("RESOLUTION PASS")
 end
end)
Duel.RegisterEffect(finish,0)
''')
run('Danger field negation remains at End Phase',end_phase=True)

logs.clear()
extra['script/probe.lua']=fixture('''
local spell=Debug.AddCard(98013009,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
local target=Debug.AddCard(98013010,1,1,LOCATION_SZONE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 assert(filter(target,...))
 return Group.FromCards(target)
end
local finish=Effect.CreateEffect(spell)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 assert(spell:IsLocation(LOCATION_HAND) and target:IsDisabled(),"spell-zone cost did not work")
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(finish,0)
''')
run('Danger negates a faceup Spell as recovery cost')

logs.clear()
extra['script/probe.lua']=fixture('''
local spell=Debug.AddCard(98013009,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
local target=Debug.AddCard(98013005,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local driver=Debug.AddCard(98013005,0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local recovered=false
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...) return Group.FromCards(target) end
local finish=Effect.CreateEffect(spell)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 if spell:IsLocation(LOCATION_HAND) then recovered=true end
end)
Duel.RegisterEffect(finish,0)
local operation=Effect.CreateEffect(driver)
operation:SetDescription(999999)
operation:SetType(EFFECT_TYPE_IGNITION)
operation:SetRange(LOCATION_MZONE)
operation:SetCondition(function() return recovered end)
operation:SetCountLimit(1)
operation:SetOperation(function()
 assert(target:IsDisabled())
 Duel.SendtoHand(target,nil,REASON_COST)
 Duel.AdjustInstantly(target)
 assert(target:IsLocation(LOCATION_HAND) and not target:IsDisabled(),"negation survived field exit")
 Debug.Message("RESOLUTION PASS")
end)
driver:RegisterEffect(operation)
''')
run('Danger negation resets when negated card leaves field',activations=2)
