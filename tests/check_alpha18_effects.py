"""Chimera and Counterattack chain-sweep tests, plus earlier native regressions."""
import pathlib
import runpy
previous=runpy.run_path(str(pathlib.Path(__file__).with_name('check_alpha17_effects.py')))
state=previous['state']
fixture=state['fixture'];extra=state['extra'];logs=state['logs'];run=state['run_resolution'];test=state['test']

# Both players' Battle Phases, plus restoration in Main Phase 2.
for owner in [0,1]:
 logs.clear()
 extra['script/probe.lua']=fixture(f'''
local c=Debug.AddCard(98013015,{owner},{owner},LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)
local ours=Debug.AddCard(98013005,{owner},{owner},LOCATION_MZONE,1,POS_FACEUP_ATTACK)
local theirs=Debug.AddCard(98013005,{1-owner},{1-owner},LOCATION_MZONE,1,POS_FACEUP_ATTACK)
local ourspell=Debug.AddCard(98013006,{owner},{owner},LOCATION_SZONE,0,POS_FACEUP_ATTACK)
local theirspell=Debug.AddCard(98013006,{1-owner},{1-owner},LOCATION_SZONE,0,POS_FACEUP_ATTACK)
local ourhand=Debug.AddCard(98013005,{owner},{owner},LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local theirhand=Debug.AddCard(98013005,{1-owner},{1-owner},LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''',f'''
local inspect=false
local function probe(card)
 local e=Effect.CreateEffect(card)
 e:SetType(EFFECT_TYPE_QUICK_O)
 e:SetRange(LOCATION_HAND)
 e:SetCode(EVENT_FREE_CHAIN)
 e:SetCondition(function() return inspect end)
 e:SetTarget(function() return true end)
 e:SetOperation(function() error("inspection probe unexpectedly activated") end)
 card:RegisterEffect(e)
 return e
end
local ownprobe=probe(ourhand)
local oppprobe=probe(theirhand)
local main=false
local battle=false
local watch=Effect.CreateEffect(c)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_ADJUST)
watch:SetOperation(function()
 local phase=Duel.GetCurrentPhase()
 if phase==PHASE_MAIN1 then
  assert(not theirs:IsDisabled() and not theirspell:IsDisabled())
  inspect=true
  assert(oppprobe:IsActivatable({1-owner}))
  inspect=false
  main=true
 elseif phase==PHASE_BATTLE_STEP and main then
  assert(theirs:IsDisabled() and theirspell:IsDisabled(),"opponent field not negated")
  assert(not c:IsDisabled() and not ours:IsDisabled() and not ourspell:IsDisabled(),"own field must remain enabled")
  inspect=true
  assert(not oppprobe:IsActivatable({1-owner}),"opponent hand effect not locked")
  assert(ownprobe:IsActivatable({owner}),"own activations must remain allowed")
  inspect=false
  battle=true
 elseif phase==PHASE_MAIN2 and battle then
  assert(not theirs:IsDisabled() and not theirspell:IsDisabled(),"Battle Phase negation did not expire")
  inspect=true
  assert(oppprobe:IsActivatable({1-owner}),"activation lock did not expire")
  inspect=false
  Debug.Message("RESOLUTION PASS")
 end
end)
Duel.RegisterEffect(watch,0)
''')
 extra['script/probe.lua']=extra['script/probe.lua'].replace('Debug.ReloadFieldBegin(0)','Debug.ReloadFieldBegin(DUEL_ATTACK_FIRST_TURN)')
 run(f'Chimera Battle Phase suppression, owner={owner}, restores in Main2',battle=True,battle_command=2)

# Two attacks in one turn: the ATK gain is once per calculation, not once per turn.
logs.clear()
extra['script/probe.lua']=fixture('''
local c=Debug.AddCard(98013015,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)
local a=Debug.AddCard(98013002,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local b=Debug.AddCard(98013002,1,1,LOCATION_MZONE,1,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local extra=Effect.CreateEffect(c)
extra:SetType(EFFECT_TYPE_SINGLE)
extra:SetCode(EFFECT_EXTRA_ATTACK)
extra:SetValue(1)
c:RegisterEffect(extra)
local gains=0
local track=Effect.CreateEffect(c)
track:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
track:SetCode(EVENT_CHAIN_SOLVED)
track:SetOperation(function(e,tp,eg,ep,ev)
 local resolved=Duel.GetChainInfo(ev,CHAININFO_TRIGGERING_EFFECT)
 if resolved:GetHandler()==c and resolved:GetCode()==EVENT_PRE_DAMAGE_CALCULATE then
  assert(c:GetAttack()==6000,"4000 base + 2000 opponent ATK expected")
  gains=gains+1
 end
end)
Duel.RegisterEffect(track,0)
local watch=Effect.CreateEffect(c)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_ADJUST)
watch:SetOperation(function()
 if gains==2 and a:IsLocation(LOCATION_GRAVE) and b:IsLocation(LOCATION_GRAVE) and c:GetAttack()==4000 then
  assert(Duel.GetLP(1)==8000 and Duel.GetLP(0)==8000)
  Debug.Message("RESOLUTION PASS")
 end
end)
Duel.RegisterEffect(watch,0)
''').replace('Debug.ReloadFieldBegin(0)','Debug.ReloadFieldBegin(DUEL_ATTACK_FIRST_TURN)').replace('Debug.SetPlayerInfo(1,8000,0,0)','Debug.SetPlayerInfo(1,16000,0,0)')
run('Chimera ATK gain twice in one Battle Phase and reset',battle=True)

for destination,action in [('grave','Duel.SendtoGrave(c,REASON_EFFECT)'),('removed','Duel.Remove(c,POS_FACEUP,REASON_EFFECT)')]:
 for location in ['LOCATION_DECK','LOCATION_GRAVE','LOCATION_REMOVED']:
  logs.clear()
  extra['script/probe.lua']=fixture(f'''
local recovery={{}}
local native=Card.RegisterEffect
Card.RegisterEffect=function(card,e,...)
 if card:GetCode()==98013015 and e:GetCode()==EVENT_TO_GRAVE then recovery[card]=e end
 return native(card,e,...)
end
local c=Debug.AddCard(98013015,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)
local copy=Debug.AddCard(98013015,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
local driver=Debug.AddCard(98013005,0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)
local searched=Debug.AddCard(98013006,0,0,{location},0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local operation=Effect.CreateEffect(driver)
operation:SetDescription(999999)
operation:SetType(EFFECT_TYPE_IGNITION)
operation:SetRange(LOCATION_MZONE)
operation:SetCountLimit(1)
operation:SetOperation(function() ACTION end)
driver:RegisterEffect(operation)
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 assert(excluded==c and filter(searched,...))
 return Group.FromCards(searched)
end
local finish=Effect.CreateEffect(c)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 if c:IsLocation(LOCATION_EXTRA) and searched:IsLocation(LOCATION_HAND) then
  assert(not recovery[c]:CheckCountLimit(0) and not recovery[copy]:CheckCountLimit(0))
  Debug.Message("RESOLUTION PASS")
 end
end)
Duel.RegisterEffect(finish,0)
'''.replace('ACTION',action))
  run(f'Chimera {destination} trigger, return to Extra, search {location}, shared limit')

# Material procedure: one archetype monster + at least one arbitrary monster.
state['rows'][99998001]=(99998001,0,0,17,1500,1500,4,8192,32)
test('Chimera variable Fusion materials',fixture('''
local fc=Debug.AddCard(98013015,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
local cat=Debug.AddCard(98013001,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local a=Debug.AddCard(99998001,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local b=Debug.AddCard(99998001,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
''','''
assert(fc:CheckFusionMaterial(Group.FromCards(cat,a),nil,0))
assert(fc:CheckFusionMaterial(Group.FromCards(cat,a,b),nil,0))
assert(not fc:CheckFusionMaterial(Group.FromCards(a,b),nil,0))
assert(not fc:CheckFusionMaterial(Group.FromCards(cat),nil,0))
'''))

# Conditional hand activation: field / GY / face-up banished, never face-down banished.
for place in ['field','grave','removed','facedown','none']:
 logs.clear()
 qualifier=''
 if place!='none':
  qualifier=f"Debug.AddCard(98013005,1,1,{ {'field':'LOCATION_MZONE','grave':'LOCATION_GRAVE','removed':'LOCATION_REMOVED','facedown':'LOCATION_REMOVED'}[place]},0,{'POS_FACEDOWN_DEFENSE' if place=='facedown' else 'POS_FACEUP_ATTACK'})"
 extra['script/probe.lua']=fixture('''
local driver=Debug.AddCard(98013005,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local trap=Debug.AddCard(98013011,1,1,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
QUALIFIER
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
'''.replace('QUALIFIER',qualifier),'''
local resolved=false
local operation=Effect.CreateEffect(driver)
operation:SetDescription(999999)
operation:SetType(EFFECT_TYPE_IGNITION)
operation:SetRange(LOCATION_MZONE)
operation:SetCountLimit(1)
operation:SetOperation(function() resolved=true end)
driver:RegisterEffect(operation)
local finish=Effect.CreateEffect(trap)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 CHECK
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(finish,0)
'''.replace('CHECK','assert(resolved and trap:IsLocation(LOCATION_HAND) and driver:IsLocation(LOCATION_MZONE))' if place in ['none','facedown'] else 'assert(not resolved and trap:IsLocation(LOCATION_GRAVE) and driver:IsLocation(LOCATION_DECK))'))
 run('Counterattack hand activation prerequisite: '+place)

# Non-field activated monster effects are negated, but their cards are not returned.
for location in ['LOCATION_HAND','LOCATION_GRAVE']:
 logs.clear()
 extra['script/probe.lua']=fixture(f'''
local driver=Debug.AddCard(98013005,0,0,{location},0,POS_FACEUP_ATTACK)
local trap=Debug.AddCard(98013011,1,1,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
Debug.AddCard(98013006,1,1,LOCATION_REMOVED,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local resolved=false
local operation=Effect.CreateEffect(driver)
operation:SetDescription(999999)
operation:SetType(EFFECT_TYPE_IGNITION)
operation:SetRange(PLACE)
operation:SetCountLimit(1)
operation:SetOperation(function() resolved=true end)
driver:RegisterEffect(operation)
local finish=Effect.CreateEffect(trap)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 assert(not resolved and driver:IsLocation(PLACE),"off-field card incorrectly returned")
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(finish,0)
'''.replace('PLACE',location))
 run('Counterattack negates off-field monster in '+location)

# Link 1 opposing monster; link 2 own effect; link 3 opposing spell/trap; link 4 Counterattack.
for kind in ['spell','trap']:
 logs.clear()
 extra['script/probe.lua']=fixture(f'''
local driver=Debug.AddCard(98013005,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local counter=Debug.AddCard(98013011,1,1,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local helper=Debug.AddCard({98013005 if kind=='spell' else 98013011},1,1,{ 'LOCATION_MZONE' if kind=='spell' else 'LOCATION_SZONE'},1,{'POS_FACEUP_ATTACK' if kind=='spell' else 'POS_FACEDOWN_DEFENSE'})
local enemy=Debug.AddCard({98013010 if kind=='spell' else 98013011},0,0,{'LOCATION_HAND' if kind=='spell' else 'LOCATION_SZONE'},0,POS_FACEDOWN_DEFENSE)
Debug.AddCard(98013006,1,1,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local driver_resolved=false
local helper_resolved=false
local enemy_resolved=false
local operation=Effect.CreateEffect(driver)
operation:SetDescription(999999)
operation:SetType(EFFECT_TYPE_IGNITION)
operation:SetRange(LOCATION_MZONE)
operation:SetCountLimit(1)
operation:SetOperation(function() driver_resolved=true end)
driver:RegisterEffect(operation)
local original=counter:GetActivateEffect():GetCondition()
counter:GetActivateEffect():SetCondition(function(...)
 return Duel.GetCurrentChain()>=3 and original(...)
end)
HELPER
response:SetCountLimit(1)
response:SetCondition(function(e,tp,eg,ep,ev,re)
 return Duel.GetCurrentChain()==1 and re:GetHandler()==driver
end)
response:SetTarget(function() return true end)
response:SetOperation(function() helper_resolved=true end)
local opposing=enemy:GetActivateEffect()
opposing:SetCountLimit(1)
opposing:SetCondition(function()
 if Duel.GetCurrentChain()~=2 then return false end
 return Duel.GetChainInfo(0,CHAININFO_TRIGGERING_EFFECT):GetHandler()==helper
end)
opposing:SetCost(function() return true end)
opposing:SetTarget(function() return true end)
opposing:SetOperation(function() enemy_resolved=true end)
local finish=Effect.CreateEffect(counter)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 assert(not driver_resolved and not enemy_resolved and helper_resolved,"chain sweep negated wrong players/links")
 assert(driver:IsLocation(LOCATION_DECK) and enemy:IsLocation(LOCATION_DECK))
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(finish,0)
'''.replace('HELPER','local response=Effect.CreateEffect(helper)\nresponse:SetType(EFFECT_TYPE_QUICK_O)\nresponse:SetCode(EVENT_CHAINING)\nresponse:SetRange(LOCATION_MZONE)\nhelper:RegisterEffect(response)' if kind=='spell' else 'local response=helper:GetActivateEffect()'))
 run('Counterattack sweep of opposing monster and '+kind+' preserves own link')

# A source that leaves the field above Counterattack must not be returned from the GY.
logs.clear()
extra['script/probe.lua']=fixture('''
local driver=Debug.AddCard(98013005,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local counter=Debug.AddCard(98013011,1,1,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local mover=Debug.AddCard(98013011,0,0,LOCATION_SZONE,0,POS_FACEDOWN_DEFENSE)
Debug.AddCard(98013006,1,1,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local resolved=false
local operation=Effect.CreateEffect(driver)
operation:SetDescription(999999)
operation:SetType(EFFECT_TYPE_IGNITION)
operation:SetRange(LOCATION_MZONE)
operation:SetCountLimit(1)
operation:SetOperation(function() resolved=true end)
driver:RegisterEffect(operation)
local move=mover:GetActivateEffect()
move:SetCondition(function(e,tp,eg,ep,ev,re) return re:GetHandler()==counter end)
move:SetTarget(function() return true end)
move:SetOperation(function() Duel.SendtoGrave(driver,REASON_EFFECT) end)
local finish=Effect.CreateEffect(counter)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 assert(not resolved and driver:IsLocation(LOCATION_GRAVE),"moved source incorrectly returned")
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(finish,0)
''')
run('Counterattack does not return a source that left above it')

# Re-use the same Counterattack in hand within the same turn: effect 1 has no limit.
logs.clear()
extra['script/probe.lua']=fixture('''
local first=Debug.AddCard(98013005,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local second=Debug.AddCard(98013005,0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)
local counter=Debug.AddCard(98013011,1,1,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
Debug.AddCard(98013006,1,1,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
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
local chains=0
local finish=Effect.CreateEffect(counter)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 chains=chains+1
 assert(counter:GetActivateEffect():CheckCountLimit(1),"activation unexpectedly has a turn limit")
 if chains==1 then
  assert(first:IsLocation(LOCATION_DECK) and counter:IsLocation(LOCATION_GRAVE))
  Duel.SendtoHand(counter,nil,REASON_EFFECT)
 elseif chains==2 then
  assert(resolved==0 and second:IsLocation(LOCATION_DECK))
  Debug.Message("RESOLUTION PASS")
 end
end)
Duel.RegisterEffect(finish,0)
''')
run('Counterattack same card activates twice in one turn',activations=2)

# Effect 2 remains once per name per turn across copies.
logs.clear()
extra['script/probe.lua']=fixture('''
local recovery={}
local native=Card.RegisterEffect
Card.RegisterEffect=function(c,e,...)
 if c:GetCode()==98013011 and e:IsHasType(EFFECT_TYPE_IGNITION) then recovery[c]=e end
 return native(c,e,...)
end
local a=Debug.AddCard(98013011,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
local b=Debug.AddCard(98013011,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local finish=Effect.CreateEffect(a)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 assert(not recovery[a]:CheckCountLimit(0) and not recovery[b]:CheckCountLimit(0))
 assert(a:IsLocation(LOCATION_SZONE) or b:IsLocation(LOCATION_SZONE))
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(finish,0)
''')
run('Counterattack recovery still shares once-per-turn limit')

# Turning Chimera face-down during Battle Phase removes both continuous restrictions.
logs.clear()
extra['script/probe.lua']=fixture('''
local c=Debug.AddCard(98013015,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)
local enemy=Debug.AddCard(98013005,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local hand=Debug.AddCard(98013005,1,1,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local inspect=false
local probe=Effect.CreateEffect(hand)
probe:SetType(EFFECT_TYPE_QUICK_O)
probe:SetRange(LOCATION_HAND)
probe:SetCode(EVENT_FREE_CHAIN)
probe:SetCondition(function() return inspect end)
probe:SetTarget(function() return true end)
probe:SetOperation(function() error("probe activated") end)
hand:RegisterEffect(probe)
local flipping=false
local watch=Effect.CreateEffect(c)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_ADJUST)
watch:SetOperation(function()
 if Duel.GetCurrentPhase()==PHASE_BATTLE_STEP and not flipping then
  flipping=true
  assert(enemy:IsDisabled())
  Duel.ChangePosition(c,POS_FACEDOWN_DEFENSE)
  Duel.AdjustInstantly(c)
  assert(c:IsFacedown() and not enemy:IsDisabled())
  inspect=true
  assert(probe:IsActivatable(1))
  inspect=false
  Debug.Message("RESOLUTION PASS")
 end
end)
Duel.RegisterEffect(watch,0)
''').replace('Debug.ReloadFieldBegin(0)','Debug.ReloadFieldBegin(DUEL_ATTACK_FIRST_TURN)')
run('Chimera face-down position removes Battle Phase suppression',battle=True)

# Let the engine pass the banishment event window before observing the absence of a trigger.
logs.clear()
extra['script/probe.lua']=fixture('''
local c=Debug.AddCard(98013015,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)
local first=Debug.AddCard(98013005,0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)
local second=Debug.AddCard(98013005,0,0,LOCATION_MZONE,2,POS_FACEUP_ATTACK)
local searched=Debug.AddCard(98013006,0,0,LOCATION_DECK,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local sent=false
local send=Effect.CreateEffect(first)
send:SetDescription(999999)
send:SetType(EFFECT_TYPE_IGNITION)
send:SetRange(LOCATION_MZONE)
send:SetCountLimit(1)
send:SetOperation(function() Duel.Remove(c,POS_FACEDOWN,REASON_EFFECT); sent=true end)
first:RegisterEffect(send)
local inspect=Effect.CreateEffect(second)
inspect:SetDescription(999999)
inspect:SetType(EFFECT_TYPE_IGNITION)
inspect:SetRange(LOCATION_MZONE)
inspect:SetCondition(function() return sent end)
inspect:SetCountLimit(1)
inspect:SetOperation(function()
 assert(c:IsLocation(LOCATION_REMOVED) and c:IsFacedown() and searched:IsLocation(LOCATION_DECK))
 Debug.Message("RESOLUTION PASS")
end)
second:RegisterEffect(inspect)
''')
run('Chimera face-down banishment does not trigger recovery',activations=2)
