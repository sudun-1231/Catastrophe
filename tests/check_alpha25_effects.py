"""Danger I targeting responses and focused Lancer II native regressions."""
import pathlib,runpy
previous=runpy.run_path(str(pathlib.Path(__file__).with_name('check_alpha24_effects.py')))
state=previous['state'];fixture=state['fixture'];extra=state['extra'];logs=state['logs'];run=state['run_resolution'];test=state['test']
FILL=previous['FILL'];DRIVER=previous['DRIVER']
state['rows'][10045474]=(10045474,0,0,4,0,0,0,0,0)
CAP='''local effects={}
local native=Card.RegisterEffect
Card.RegisterEffect=function(card,e,...)
 if card:GetCode()==98013009 or card:GetCode()==98013002 then
  effects[card]=effects[card] or {};table.insert(effects[card],e)
 end
 -- Automate choosing Danger rather than Dragon Knight's separate negate.
 if card:GetCode()==98013013 and e:GetCode()==EVENT_CHAINING then e:SetCondition(function() return false end) end
 return native(card,e,...)
end
'''
# Use the bundled official Infinite Impermanence script, not a fake negate effect.
for hand in [False,True]:
 for location in ['LOCATION_DECK','LOCATION_GRAVE','LOCATION_REMOVED']:
  owner=0 if hand else 1
  cards=CAP+f'''
local knight=Debug.AddCard(98013013,{owner},{owner},LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)
local spell=Debug.AddCard(98013009,{owner},{owner},{'LOCATION_HAND' if hand else 'LOCATION_SZONE'},0,POS_FACEDOWN_DEFENSE)
local copy=Debug.AddCard(98013009,{owner},{owner},LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
local imperm=Debug.AddCard(10045474,{1-owner},{1-owner},LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local selected=Debug.AddCard(98013007,{owner},{owner},{location},0,POS_FACEUP_ATTACK)
'''+(DRIVER if hand else '')+FILL
  body='''
local searched=0
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 assert(filter(selected,...));searched=searched+1;return Group.FromCards(selected)
end
local responded=false
local watch=Effect.CreateEffect(spell)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_CHAINING)
watch:SetOperation(function(e,tp,eg,ep,ev,re)
 if re:GetHandler()==spell then
  assert(ev>=2 and not re:IsHasProperty(EFFECT_FLAG_CARD_TARGET))
  responded=true
 end
end)
Duel.RegisterEffect(watch,0)
local finish=Effect.CreateEffect(spell)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 if responded then
  assert(knight:IsLocation(LOCATION_GRAVE) and knight:IsReason(REASON_DESTROY))
  assert(selected:IsLocation(LOCATION_HAND) and searched==1)
  assert(not knight:IsDisabled(),"Imperm must not negate a target that left the field")
  for _,card in ipairs({spell,copy}) do
   for _,eff in ipairs(effects[card]) do
    if eff:IsHasType(EFFECT_TYPE_ACTIVATE) then assert(not eff:CheckCountLimit(OWNER)) end
    if eff:IsHasType(EFFECT_TYPE_IGNITION) then assert(eff:CheckCountLimit(OWNER),"recovery must have independent HOPT") end
   end
  end
  Debug.Message("RESOLUTION PASS")
 end
end)
Duel.RegisterEffect(finish,0)
'''.replace('OWNER',str(owner))
  if hand:body+='''
local action=Effect.CreateEffect(driver)
action:SetDescription(999999)
action:SetType(EFFECT_TYPE_IGNITION)
action:SetRange(LOCATION_MZONE)
action:SetCountLimit(1)
action:SetOperation(function() end)
driver:RegisterEffect(action)
'''
  logs.clear();extra['script/probe.lua']=fixture(cards,body)
  run(f'Danger vs official Imperm: hand={hand}, search={location}',select_code=98013013)
# Invalid activations are rejected by native chain registration.
for issue in ['own effect','opponent target','not targeting','only itself','no search card']:
 owner=0 if issue=='own effect' else 1
 targetowner=0 if issue=='opponent target' else owner
 target='spell' if issue=='only itself' else 'protected'
 cards=CAP+f'''
local spell=Debug.AddCard(98013009,{owner},{owner},LOCATION_SZONE,0,POS_FACEDOWN_DEFENSE)
local protected=Debug.AddCard(99998001,{targetowner},{targetowner},LOCATION_MZONE,0,POS_FACEUP_ATTACK)
'''+DRIVER+(FILL.replace('98013006','99998001') if issue=='no search card' else FILL)
 body='''
local responded=false
local resolved=false
local action=Effect.CreateEffect(driver)
action:SetDescription(999999)
action:SetType(EFFECT_TYPE_IGNITION)
action:SetRange(LOCATION_MZONE)
action:SetCountLimit(1)
PROPERTY
action:SetTarget(function(e,tp,eg,ep,ev,re,r,rp,chk)
 if chk==0 then return true end
 Duel.SetTargetCard(__TARGET__)
end)
action:SetOperation(function() resolved=true end)
driver:RegisterEffect(action)
local watch=Effect.CreateEffect(spell)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_CHAINING)
watch:SetOperation(function(e,tp,eg,ep,ev,re) if re:GetHandler()==spell then responded=true end end)
Duel.RegisterEffect(watch,0)
local finish=Effect.CreateEffect(spell)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 assert(resolved and not responded and spell:IsFacedown())
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(finish,0)
'''.replace('PROPERTY','' if issue=='not targeting' else 'action:SetProperty(EFFECT_FLAG_CARD_TARGET)').replace('__TARGET__',target)
 logs.clear();extra['script/probe.lua']=fixture(cards,body);run('Danger rejects '+issue)
# All four Lancer choices, responding to our/opponent effects.
for owner in [0,1]:
 for option in range(4):
  cards=CAP+f'''
local lancer=Debug.AddCard(98013002,{owner},{owner},LOCATION_MZONE,1,POS_FACEUP_ATTACK)
local ownfield=Debug.AddCard(99998002,{owner},{owner},LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local otherfield=Debug.AddCard(99998002,{1-owner},{1-owner},LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local handa=Debug.AddCard(99998001,{owner},{owner},LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local handb=Debug.AddCard(99998002,{owner},{owner},LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local othera=Debug.AddCard(99998001,{1-owner},{1-owner},LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local otherb=Debug.AddCard(99998002,{1-owner},{1-owner},LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
'''+DRIVER+FILL
  body='''
local resolved=false
local randomcalls=0
local native=Group.RandomSelect
Group.RandomSelect=function(g,tp,count)
 randomcalls=randomcalls+1
 assert(count==1 and g:GetCount()==2)
 assert(g:IsContains(HANDA) and g:IsContains(HANDB),"random pool must be the whole chosen hand")
 return native(g,tp,count)
end
local action=Effect.CreateEffect(driver)
action:SetDescription(999999)
action:SetType(EFFECT_TYPE_IGNITION)
action:SetRange(LOCATION_MZONE)
action:SetCountLimit(1)
action:SetOperation(function() resolved=true end)
driver:RegisterEffect(action)
local watch=Effect.CreateEffect(driver)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_CHAIN_END)
watch:SetOperation(function()
 assert(resolved,"Lancer does not negate the original effect")
 CHECK
 for _,e in ipairs(effects[lancer]) do
  if e:GetCode()==EVENT_CHAINING then assert(not e:CheckCountLimit(OWNER))
  else assert(e:CheckCountLimit(OWNER),"Lancer I/III limits must remain available") end
 end
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(watch,0)
'''.replace('OWNER',str(owner))
  if option<2:
   body=body.replace('HANDA','handa').replace('HANDB','handb').replace('CHECK',f'assert(randomcalls==0 and {"ownfield" if option==0 else "otherfield"}:IsLocation(LOCATION_GRAVE))')
  else:
   a,b=('handa','handb') if option==2 else ('othera','otherb')
   body=body.replace('HANDA',a).replace('HANDB',b).replace('CHECK',f'assert(randomcalls==1 and {a}:IsLocation(LOCATION_GRAVE)~={b}:IsLocation(LOCATION_GRAVE))')
  logs.clear();extra['script/probe.lua']=fixture(cards,body)
  run(f'Lancer owner={owner} choice={option} + independent limits',select_code=99998002,option_index=option)
# The same named effect is shared between copies, and never reacts to itself.
test('Lancer rejects own-card effects, accepts another copy',fixture(CAP+'''
local lancer=Debug.AddCard(98013002,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local copy=Debug.AddCard(98013002,0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)
''','''
local response
for _,e in ipairs(effects[lancer]) do if e:GetCode()==EVENT_CHAINING then response=e end end
for _,e in ipairs(effects[lancer]) do assert(not response:GetCondition()(response,0,nil,0,1,e)) end
assert(response:GetCondition()(response,0,nil,0,1,effects[copy][1]))
response:UseCountLimit(0)
for _,e in ipairs(effects[copy]) do if e:GetCode()==EVENT_CHAINING then assert(not e:CheckCountLimit(0)) end end
'''))
# Multiple targets: destroy one of the original own targets, never an unrelated card.
for failure in [False,True]:
 cards=CAP+'''
local spell=Debug.AddCard(98013009,1,1,LOCATION_SZONE,0,POS_FACEDOWN_DEFENSE)
local target=Debug.AddCard(99998001,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local second=Debug.AddCard(99998001,1,1,LOCATION_MZONE,1,POS_FACEUP_ATTACK)
local unrelated=Debug.AddCard(99998001,1,1,LOCATION_MZONE,2,POS_FACEUP_ATTACK)
local enemy=Debug.AddCard(99998001,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local selected=Debug.AddCard(98013007,1,1,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
'''+DRIVER+FILL
 body='''
local resolved=false
local searched=0
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 searched=searched+1;assert(filter(selected,...));return Group.FromCards(selected)
end
Group.Select=function(g,tp,min,max,excluded)
 assert(g:IsContains(target) and not g:IsContains(enemy) and not g:IsContains(unrelated))
 return Group.FromCards(target)
end
local action=Effect.CreateEffect(driver)
action:SetDescription(999999)
action:SetType(EFFECT_TYPE_IGNITION)
action:SetRange(LOCATION_MZONE)
action:SetProperty(EFFECT_FLAG_CARD_TARGET)
action:SetCountLimit(1)
action:SetTarget(function(e,tp,eg,ep,ev,re,r,rp,chk)
 if chk==0 then return true end
 Duel.SetTargetCard(Group.FromCards(target,second,enemy))
end)
action:SetOperation(function() resolved=true end)
driver:RegisterEffect(action)
FAILURE
local finish=Effect.CreateEffect(driver)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 assert(resolved and unrelated:IsLocation(LOCATION_MZONE) and enemy:IsLocation(LOCATION_MZONE))
 CHECK
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(finish,0)
'''
 if failure:
  body=body.replace('FAILURE','''
local protect=Effect.CreateEffect(target)
protect:SetType(EFFECT_TYPE_QUICK_O)
protect:SetCode(EVENT_CHAINING)
protect:SetRange(LOCATION_MZONE)
protect:SetCountLimit(1)
protect:SetCondition(function(e,tp,eg,ep,ev,re) return re:GetHandler()==spell end)
protect:SetOperation(function()
 for _,c in ipairs({target,second}) do
  local immune=Effect.CreateEffect(c)
  immune:SetType(EFFECT_TYPE_SINGLE)
  immune:SetCode(EFFECT_INDESTRUCTABLE_EFFECT)
  immune:SetValue(1)
  c:RegisterEffect(immune)
 end
end)
target:RegisterEffect(protect)
''').replace('CHECK','assert(searched==0 and selected:IsLocation(LOCATION_GRAVE) and target:IsLocation(LOCATION_MZONE))')
 else:body=body.replace('FAILURE','').replace('CHECK','assert(searched==1 and target:IsLocation(LOCATION_GRAVE) and second:IsLocation(LOCATION_MZONE) and selected:IsLocation(LOCATION_HAND))')
 logs.clear();extra['script/probe.lua']=fixture(cards,body);run(f'Danger multiple targets, destruction blocked={failure}')
