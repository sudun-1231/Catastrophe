"""Updated Fray/Lancer/Guardian tests, including all Alpha 0.11 regressions."""
import pathlib
import runpy
previous=runpy.run_path(str(pathlib.Path(__file__).with_name('check_alpha11_effects.py')))
state=previous['state']
fixture=state['fixture'];extra=state['extra'];logs=state['logs'];run=state['run_resolution']

for code in [98013001,98013002,98013003]:
 for location in ['LOCATION_DECK','LOCATION_GRAVE','LOCATION_REMOVED']:
  logs.clear()
  extra['script/probe.lua']=fixture(f'''
local c=Debug.AddCard({code},0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local destroyed=Debug.AddCard(98013006,0,0,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE)
local follow=Debug.AddCard(98013007,0,0,{location},0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local selections=0
Duel.SelectMatchingCard=function(tp,filter,p,own,other,min,max,excluded,...)
 selections=selections+1
 local chosen=selections==1 and destroyed or follow
 assert(filter(chosen,...),"chosen card did not pass actual material/search filter")
 return Group.FromCards(chosen)
end
local observer=Effect.CreateEffect(c)
observer:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
observer:SetCode(EVENT_CHAIN_END)
observer:SetOperation(function()
 assert(destroyed:IsLocation(LOCATION_GRAVE) and c:IsLocation(LOCATION_MZONE),"destroy/summon sequence failed")
 CHECK
 assert(selections==2,"follow-up must resolve within the summon effect")
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(observer,0)
'''.replace('CHECK','assert(follow:IsLocation(LOCATION_SZONE) and follow:IsFacedown())' if code==98013003 else 'assert(follow:IsLocation(LOCATION_HAND))'))
  run(f'{code} self-summon and follow-up from {location}')

logs.clear()
extra['script/probe.lua']=fixture('''
local c=Debug.AddCard(98013001,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local target=Debug.AddCard(98013005,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local observer=Effect.CreateEffect(c)
observer:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
observer:SetCode(EVENT_CHAIN_END)
observer:SetOperation(function()
 assert(target:IsDisabled() and target:IsHasEffect(EFFECT_DISABLE_EFFECT),"face-up target not negated")
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(observer,0)
''')
run('Fray field ignition negate',select_code=98013005)

logs.clear()
extra['script/probe.lua']=fixture('''
local c=Debug.AddCard(98013003,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local cost=Debug.AddCard(98013013,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
local target=Debug.AddCard(98013005,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local observer=Effect.CreateEffect(c)
observer:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
observer:SetCode(EVENT_CHAIN_END)
observer:SetOperation(function()
 assert(cost:IsLocation(LOCATION_GRAVE) and cost:IsReason(REASON_COST),"Extra Deck cost was not paid")
 assert(target:IsLocation(LOCATION_DECK),"field card not returned")
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(observer,0)
''')
run('Guardian Extra Deck cost and field return',select_code=98013005)

for hand in [False,True]:
 for other_player in [False,True]:
  logs.clear()
  lancer_owner=1 if other_player else 0
  cards=f'''
local driver=Debug.AddCard(98013005,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local lancer=Debug.AddCard(98013002,{lancer_owner},{lancer_owner},LOCATION_MZONE,1,POS_FACEUP_ATTACK)
local hand1=Debug.AddCard(98013006,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local hand2=Debug.AddCard(98013006,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
'''
  body='''
local resolved=false
local operation=Effect.CreateEffect(driver)
operation:SetDescription(999999)
operation:SetType(EFFECT_TYPE_IGNITION)
operation:SetRange(LOCATION_MZONE)
operation:SetCountLimit(1)
operation:SetOperation(function() resolved=true end)
driver:RegisterEffect(operation)
local observer=Effect.CreateEffect(driver)
observer:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
observer:SetCode(EVENT_CHAIN_END)
observer:SetOperation(function()
 assert(resolved,"Lancer must destroy without negating the activating effect")
 CHECK
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(observer,0)
'''.replace('CHECK','assert(hand1:IsLocation(LOCATION_GRAVE)~=hand2:IsLocation(LOCATION_GRAVE),"exactly one random hand card must be destroyed")' if hand else 'assert(driver:IsLocation(LOCATION_GRAVE),"chosen field card not destroyed")')
  extra['script/probe.lua']=fixture(cards,body)
  # When controlled by player 0 only own field/own hand are populated; with player 1, own field/opponent field/opponent hand.
  option=(2 if other_player else 1) if hand else (1 if other_player else 0)
  run('Lancer '+('random hand' if hand else 'field')+' response to '+('opponent' if other_player else 'own')+' effect',select_code=98013005,option_index=option)
