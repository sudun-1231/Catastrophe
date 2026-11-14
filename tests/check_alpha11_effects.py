"""Run Alpha 0.11 effect checks against the native MDPro3 core.
Uses the existing fusion suite's callbacks, fixture builder and protocol responder.
"""
import pathlib
import runpy
state=runpy.run_path(str(pathlib.Path(__file__).with_name('check_fusion_contracts.py')))
test=state['test'];fixture=state['fixture'];extra=state['extra'];logs=state['logs'];run=state['run_resolution']

# Actual EVENT_CHAINING, chain negation and follow-up movement.
for code,location in [(98013013,'LOCATION_MZONE'),(98013011,'LOCATION_SZONE'),(98013004,'LOCATION_HAND'),(98013004,'LOCATION_MZONE')]:
 for opponent in [True,False]:
  owner=1 if opponent else 0
  pos='POS_FACEDOWN_DEFENSE' if location=='LOCATION_SZONE' else 'POS_FACEUP_ATTACK'
  logs.clear()
  cards=f'''
local driver=Debug.AddCard(98013003,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local negator=Debug.AddCard({code},{owner},{owner},{location},1,{pos})
Debug.AddCard(98013006,{owner},{owner},LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
'''
  body='''
local resolved=false
local driver_effect=Effect.CreateEffect(driver)
driver_effect:SetDescription(999999)
driver_effect:SetType(EFFECT_TYPE_IGNITION)
driver_effect:SetRange(LOCATION_MZONE)
driver_effect:SetCountLimit(1)
driver_effect:SetOperation(function() resolved=true end)
driver:RegisterEffect(driver_effect)
local observer=Effect.CreateEffect(driver)
observer:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
observer:SetCode(EVENT_CHAIN_END)
observer:SetOperation(function(e)
 CHECK
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(observer,0)
'''
  if opponent:
   check='assert(not resolved,"opponent effect was not negated"); assert(driver:IsLocation(DEST),"negated card not moved")'
   check=check.replace('DEST','LOCATION_REMOVED' if code==98013004 else 'LOCATION_DECK' if code==98013011 else 'LOCATION_GRAVE')
   if code==98013004:check+='; assert(negator:IsLocation(LOCATION_GRAVE),"Magician did not destroy itself")'
  else:check='assert(resolved and driver:IsLocation(LOCATION_MZONE),"own effect must not be negated")'
  extra['script/probe.lua']=fixture(cards,body.replace('CHECK',check))
  run(f'{code} {location} '+('opponent negation' if opponent else 'own effect allowed'))

# Trap recovery must set face down, not allow activation during the same turn.
for loc in ['LOCATION_GRAVE','LOCATION_REMOVED']:
 logs.clear()
 extra['script/probe.lua']=fixture(f'''
local c=Debug.AddCard(98013011,0,0,{loc},0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local observer=Effect.CreateEffect(c)
observer:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
observer:SetCode(EVENT_CHAIN_END)
observer:SetOperation(function(e)
 assert(c:IsLocation(LOCATION_SZONE) and c:IsFacedown(),"trap not set")
 assert(c:IsStatus(STATUS_SET_TURN),"trap must obey normal set-turn restriction")
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(observer,0)
''')
 run('Counterattack recovery '+loc)

# Real attack declaration, damage calculation and damage-step-end trigger chains.
for attackpos in [True,False]:
 logs.clear()
 owner=0 if attackpos else 1
 cards=f"""
local c=Debug.AddCard(98013012,{owner},{owner},LOCATION_MZONE,0,POSITION,true)
local opponent=Debug.AddCard(98013002,{1-owner},{1-owner},LOCATION_MZONE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
""".replace('POSITION','POS_FACEUP_ATTACK' if attackpos else 'POS_FACEUP_DEFENSE')
 body="""
local protect=Effect.CreateEffect(opponent)
protect:SetType(EFFECT_TYPE_SINGLE)
protect:SetCode(EFFECT_INDESTRUCTABLE_BATTLE)
protect:SetValue(1)
opponent:RegisterEffect(protect)
local saw_boost=false
local ended=false
local tracker=Effect.CreateEffect(c)
tracker:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
tracker:SetCode(EVENT_CHAIN_SOLVED)
tracker:SetOperation(function()
 if Duel.GetCurrentPhase()==PHASE_DAMAGE_CAL and c:GetAttack()==2000 then saw_boost=true end
end)
Duel.RegisterEffect(tracker,0)
local endwatch=Effect.CreateEffect(c)
endwatch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
endwatch:SetCode(EVENT_DAMAGE_STEP_END)
endwatch:SetOperation(function() ended=true end)
Duel.RegisterEffect(endwatch,0)
local finish=Effect.CreateEffect(c)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_ADJUST)
finish:SetOperation(function()
 if ended and saw_boost and c:GetAttack()==0 and RESULT then
  assert(c:IsLocation(LOCATION_MZONE),"battle destruction protection failed")
  assert(Duel.GetLP(OWNER)==8000,"own battle damage must be zero")
  Debug.Message("RESOLUTION PASS")
 end
end)
Duel.RegisterEffect(finish,0)
""".replace('OWNER',str(owner)).replace('RESULT','Duel.GetLP(1)==6000 and opponent:IsLocation(LOCATION_GRAVE)' if attackpos else 'Duel.GetLP(0)==8000 and opponent:IsLocation(LOCATION_MZONE)')
 extra['script/probe.lua']=fixture(cards,body).replace('Debug.ReloadFieldBegin(0)','Debug.ReloadFieldBegin(DUEL_ATTACK_FIRST_TURN)')
 run('Catastrophe battle '+('attack position' if attackpos else 'defense position'),battle=True)

logs.clear()
extra['script/probe.lua']=fixture('''
local c=Debug.AddCard(98013012,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)
local driver=Debug.AddCard(98013003,0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local operation=Effect.CreateEffect(driver)
operation:SetDescription(999999)
operation:SetType(EFFECT_TYPE_IGNITION)
operation:SetRange(LOCATION_MZONE)
operation:SetCountLimit(1)
operation:SetOperation(function()
 local foreign=Effect.CreateEffect(driver)
 foreign:SetType(EFFECT_TYPE_SINGLE)
 foreign:SetCode(EFFECT_UPDATE_ATTACK)
 foreign:SetValue(5000)
 c:RegisterEffect(foreign)
 assert(c:GetAttack()==0,"other card's effect bypassed immunity")
 assert(Duel.Destroy(c,REASON_EFFECT)==0 and c:IsLocation(LOCATION_MZONE),"effect destruction protection failed")
 Debug.Message("RESOLUTION PASS")
end)
driver:RegisterEffect(operation)
''')
run('Catastrophe immunity and effect-destruction protection')

logs.clear()
extra['script/probe.lua']=fixture('''
local c=Debug.AddCard(98013012,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)
local driver=Debug.AddCard(98013003,0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)
local enemy=Debug.AddCard(98013005,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local hand=Debug.AddCard(98013007,1,1,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local backrow=Debug.AddCard(98013009,1,1,LOCATION_SZONE,0,POS_FACEDOWN_DEFENSE)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local scheduled=false
local operation=Effect.CreateEffect(driver)
operation:SetDescription(999999)
operation:SetType(EFFECT_TYPE_IGNITION)
operation:SetRange(LOCATION_MZONE)
operation:SetCountLimit(1)
operation:SetOperation(function()
 Duel.SendtoGrave(c,REASON_COST)
 assert(c:IsLocation(LOCATION_GRAVE))
 assert(enemy:IsLocation(LOCATION_MZONE) and hand:IsLocation(LOCATION_HAND) and backrow:IsLocation(LOCATION_SZONE),"destruction must wait for End Phase")
end)
driver:RegisterEffect(operation)
local chainwatch=Effect.CreateEffect(driver)
chainwatch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
chainwatch:SetCode(EVENT_CHAIN_SOLVED)
chainwatch:SetOperation(function(e,tp,eg,ep,ev)
 local resolved=Duel.GetChainInfo(ev,CHAININFO_TRIGGERING_EFFECT)
 if resolved and resolved:GetCode()==EVENT_LEAVE_FIELD then
  scheduled=true
  assert(enemy:IsLocation(LOCATION_MZONE) and hand:IsLocation(LOCATION_HAND) and backrow:IsLocation(LOCATION_SZONE))
 end
end)
Duel.RegisterEffect(chainwatch,0)
local finish=Effect.CreateEffect(driver)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_ADJUST)
finish:SetOperation(function()
 if scheduled and Duel.GetCurrentPhase()==PHASE_END and enemy:IsLocation(LOCATION_GRAVE) and hand:IsLocation(LOCATION_GRAVE) and backrow:IsLocation(LOCATION_GRAVE) then
  Debug.Message("RESOLUTION PASS")
 end
end)
Duel.RegisterEffect(finish,0)
''')
run('Catastrophe leave-field trigger and deferred End Phase destruction',end_phase=True)

# Different copies of the same named card must share their negate limit.
for code,loc in [(98013013,'LOCATION_MZONE'),(98013011,'LOCATION_SZONE'),(98013004,'LOCATION_HAND')]:
 logs.clear()
 extra['script/probe.lua']=fixture(f'''
local first=Debug.AddCard(98013003,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local second=Debug.AddCard(98013003,0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)
Debug.AddCard({code},1,1,{loc},0,POSITION)
Debug.AddCard({code},1,1,{loc},1,POSITION)
Debug.AddCard(98013006,1,1,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
'''.replace('POSITION','POS_FACEDOWN_DEFENSE' if loc=='LOCATION_SZONE' else 'POS_FACEUP_ATTACK'),'''
local chains=0
local resolved=0
for _,driver in ipairs({first,second}) do
 local operation=Effect.CreateEffect(driver)
 operation:SetDescription(999999)
operation:SetType(EFFECT_TYPE_IGNITION)
 operation:SetRange(LOCATION_MZONE)
 operation:SetCountLimit(1)
 operation:SetOperation(function() resolved=resolved+1 end)
 driver:RegisterEffect(operation)
end
local observer=Effect.CreateEffect(first)
observer:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
observer:SetCode(EVENT_CHAIN_END)
observer:SetOperation(function()
 chains=chains+1
 if chains==2 then
  assert(resolved==1 and second:IsLocation(LOCATION_MZONE),"same-name negate must be usable only once per turn")
  Debug.Message("RESOLUTION PASS")
 end
end)
Duel.RegisterEffect(observer,0)
''')
 run(f'{code} '+('multiple Counterattack responses allowed' if code==98013011 else 'same-name negate once per turn'),activations=2)

# No face-up archetype card/GY card: Counterattack cannot negate.
test('Counterattack prerequisite and facedown banished recovery',fixture('''
local trap=Debug.AddCard(98013011,0,0,LOCATION_SZONE,0,POS_FACEDOWN_DEFENSE)
local hidden=Debug.AddCard(98013011,0,0,LOCATION_REMOVED,0,POS_FACEDOWN_DEFENSE)
local source=Debug.AddCard(98013003,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
''','''
local effect=Effect.CreateEffect(trap)
effect:SetType(EFFECT_TYPE_SINGLE)
effect:SetCode(EFFECT_UPDATE_ATTACK)
effect:SetValue(0)
trap:RegisterEffect(effect)
local opposing=Effect.CreateEffect(source)
opposing:SetType(EFFECT_TYPE_IGNITION)
opposing:SetRange(LOCATION_MZONE)
source:RegisterEffect(opposing)
Duel.IsChainNegatable=function() return true end
assert(not c98013011.negcon(effect,0,nil,0,1,opposing,0,1))
local hidden_effect=Effect.CreateEffect(hidden)
hidden_effect:SetType(EFFECT_TYPE_SINGLE)
hidden_effect:SetCode(EFFECT_UPDATE_ATTACK)
hidden_effect:SetValue(0)
hidden:RegisterEffect(hidden_effect)
assert(not c98013011.setcon(hidden_effect))
'''))
