"""Quick-Play Threshold activation and all earlier native scenarios."""
import pathlib
import runpy
previous=runpy.run_path(str(pathlib.Path(__file__).with_name('check_alpha16_effects.py')))
state=previous['state']
fixture=state['fixture'];extra=state['extra'];logs=state['logs'];run=state['run_resolution'];test=state['test']

for location in ['LOCATION_DECK','LOCATION_GRAVE','LOCATION_REMOVED']:
 for discard in ['own','opponent','skip']:
  logs.clear()
  extra['script/probe.lua']=fixture(f'''
local spell=Debug.AddCard(98013007,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local searched=Debug.AddCard(98013006,0,0,{location},0,POS_FACEUP_ATTACK)
local target=Debug.AddCard(98013005,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local hand=Debug.AddCard(98013006,1,1,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
assert(spell:IsType(TYPE_QUICKPLAY),"Threshold must be a Quick-Play Spell in the DB")
local paid=false
local calls=0
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 calls=calls+1
 local chosen=calls==1 and searched or calls==2 and target or DISCARD
 assert(filter(chosen,...),"selected card does not satisfy actual filter")
 return Group.FromCards(chosen)
end
Duel.SelectYesNo=function() return CONSENT end
Duel.SelectOption=function() return OPTION end
local watch=Effect.CreateEffect(spell)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_CHAINING)
watch:SetOperation(function(e,tp,eg,ep,ev,re)
 if re:GetHandler()==spell then
  assert(searched:IsLocation(LOCATION_HAND) and searched:IsReason(REASON_COST),"search must be paid before activation")
  paid=true
 end
end)
Duel.RegisterEffect(watch,0)
local finish=Effect.CreateEffect(spell)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 assert(paid and target:IsLocation(LOCATION_REMOVED) and target:IsFaceup())
 RESULT
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(finish,0)
'''.replace('DISCARD','hand' if discard=='opponent' else 'searched').replace('CONSENT','false' if discard=='skip' else 'true').replace('OPTION','1' if discard=='opponent' else '0').replace('RESULT',{
 'own':'assert(searched:IsLocation(LOCATION_GRAVE) and searched:IsReason(REASON_DISCARD)); assert(hand:IsLocation(LOCATION_HAND))',
 'opponent':'assert(hand:IsLocation(LOCATION_GRAVE) and hand:IsReason(REASON_DISCARD)); assert(searched:IsLocation(LOCATION_HAND))',
 'skip':'assert(searched:IsLocation(LOCATION_HAND) and hand:IsLocation(LOCATION_HAND)); assert(calls==2)'
 }[discard]))
  run(f'Threshold search cost from {location}, banish, discard={discard}')

# Opponent can negate the activation, but the searched cost card remains in hand.
logs.clear()
extra['script/probe.lua']=fixture('''
local spell=Debug.AddCard(98013007,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local searched=Debug.AddCard(98013006,0,0,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE)
local target=Debug.AddCard(98013005,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local magician=Debug.AddCard(98013004,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...) return Group.FromCards(searched) end
local finish=Effect.CreateEffect(spell)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 assert(searched:IsLocation(LOCATION_HAND) and searched:IsReason(REASON_COST))
 assert(spell:IsLocation(LOCATION_REMOVED) and magician:IsLocation(LOCATION_GRAVE))
 assert(target:IsLocation(LOCATION_MZONE),"negated activation must not banish field card")
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(finish,0)
''')
run('Threshold negated activation preserves search cost')

# Previously set Quick-Play Spell works on the opponent's turn.
logs.clear()
extra['script/probe.lua']=fixture('''
local spell=Debug.AddCard(98013007,1,1,LOCATION_SZONE,0,POS_FACEDOWN_DEFENSE)
local searched=Debug.AddCard(98013006,1,1,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
local driver=Debug.AddCard(98013005,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local target=Debug.AddCard(98013005,0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local activation=spell:GetActivateEffect()
activation:SetCondition(function()
 if Duel.GetCurrentChain()==0 then return false end
 local effect=Duel.GetChainInfo(0,CHAININFO_TRIGGERING_EFFECT)
 return effect and effect:GetHandler()==driver
end)
local resolved=false
local operation=Effect.CreateEffect(driver)
operation:SetDescription(999999)
operation:SetType(EFFECT_TYPE_IGNITION)
operation:SetRange(LOCATION_MZONE)
operation:SetCountLimit(1)
operation:SetOperation(function() resolved=true end)
driver:RegisterEffect(operation)
local calls=0
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 calls=calls+1
 local chosen=calls==1 and searched or target
 assert(tp==1 and filter(chosen,...))
 return Group.FromCards(chosen)
end
Duel.SelectYesNo=function() return false end
local finish=Effect.CreateEffect(spell)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 assert(resolved and searched:IsLocation(LOCATION_HAND) and target:IsLocation(LOCATION_REMOVED))
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(finish,0)
''')
run('Threshold previously set Quick-Play activation on opponent turn')

for issue in ['no search card','facedown banished search card','immune field card']:
 setup=''
 if issue=='facedown banished search card':setup='Debug.AddCard(98013006,0,0,LOCATION_REMOVED,0,POS_FACEDOWN_DEFENSE)'
 if issue=='immune field card':setup='Debug.AddCard(98013012,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)'
 test('Threshold rejects '+issue,fixture('''
local spell=Debug.AddCard(98013007,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
'''+setup,'''
local e=spell:GetActivateEffect()
CHECK
'''.replace('CHECK','assert(not c98013007.activatetarget(e,0,nil,0,0,nil,0,0,0))' if issue=='immune field card' else 'assert(not c98013007.activatecost(e,0,nil,0,0,nil,0,0,0))')))

# Both effects can be used once each; multiple copies share the activation limit.
logs.clear()
extra['script/probe.lua']=fixture('''
local registered={}
local native=Card.RegisterEffect
Card.RegisterEffect=function(c,e,...)
 if c:GetCode()==98013007 then
  e:SetDescription(999999)
  if e:IsHasType(EFFECT_TYPE_IGNITION) then registered[c]=e end
 end
 return native(c,e,...)
end
local spell=Debug.AddCard(98013007,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local copy=Debug.AddCard(98013007,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local searched=Debug.AddCard(98013006,0,0,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE)
local target=Debug.AddCard(98013005,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local calls=0
local activated=nil
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 calls=calls+1
 local selected=calls==1 and searched or target
 assert(filter(selected,...))
 return Group.FromCards(selected)
end
Duel.SelectYesNo=function() return false end
local watch=Effect.CreateEffect(spell)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_CHAINING)
watch:SetOperation(function(e,tp,eg,ep,ev,re)
 if re:GetHandler():GetCode()==98013007 and re:IsHasType(EFFECT_TYPE_ACTIVATE) then activated=re:GetHandler() end
end)
Duel.RegisterEffect(watch,0)
local chains=0
local finish=Effect.CreateEffect(spell)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 chains=chains+1
 if chains==1 then
  assert(activated and activated:IsLocation(LOCATION_GRAVE))
  assert(not spell:GetActivateEffect():CheckCountLimit(0) and not copy:GetActivateEffect():CheckCountLimit(0))
  assert(registered[spell]:CheckCountLimit(0) and registered[copy]:CheckCountLimit(0))
 elseif chains==2 then
  assert(Duel.GetFieldGroupCount(0,LOCATION_HAND,0)==4,"effect 2 did not draw two additional cards")
  assert(not registered[spell]:CheckCountLimit(0) and not registered[copy]:CheckCountLimit(0))
  Debug.Message("RESOLUTION PASS")
 end
end)
Duel.RegisterEffect(finish,0)
''')
run('Threshold shared activation limit and independent draw recovery',activations=2)
