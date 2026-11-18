"""Super Polymerization-inspired absorption tests and prior recovery regressions."""
import pathlib
import runpy
previous=runpy.run_path(str(pathlib.Path(__file__).with_name('check_alpha13_effects.py')))
state=previous['state']
fixture=state['fixture'];extra=state['extra'];logs=state['logs'];run=state['run_resolution'];test=state['test']

for owners,facedown in [((0,1),False),((0,1),True),((1,1),False),((0,0),False)]:
 logs.clear()
 extra['script/probe.lua']=fixture(f'''
local spell=Debug.AddCard(98013010,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local cost=Debug.AddCard(98013006,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local a=Debug.AddCard(98013005,{owners[0]},{owners[0]},LOCATION_MZONE,0,{'POS_FACEDOWN_DEFENSE' if facedown else 'POS_FACEUP_ATTACK'})
local b=Debug.AddCard(98013003,{owners[1]},{owners[1]},LOCATION_MZONE,1,POS_FACEUP_ATTACK)
local fc=Debug.AddCard(98013013,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
local our_response=Debug.AddCard(98013005,0,0,LOCATION_MZONE,2,POS_FACEUP_ATTACK)
local their_response=Debug.AddCard(98013005,1,1,LOCATION_MZONE,2,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
spell:GetActivateEffect():SetDescription(999999)
Duel.SelectMatchingCard=function(tp,filter,p,own,other,min,max,excluded,...)
 assert(excluded==spell and filter(cost,...))
 return Group.FromCards(cost)
end
Group.Select=function(g,tp,min,max,excluded) return Group.FromCards(g:GetFirst()) end
Duel.SelectFusionMaterial=function(tp,target,mg,mandatory,chkf)
 assert(target==fc and mandatory==nil and mg:IsContains(a) and mg:IsContains(b))
 assert(fc:CheckFusionMaterial(Group.FromCards(a,b),nil,tp))
 return Group.FromCards(a,b)
end
for _,responder in ipairs({our_response,their_response}) do
 local response=Effect.CreateEffect(responder)
 response:SetType(EFFECT_TYPE_QUICK_O)
 response:SetRange(LOCATION_MZONE)
 response:SetCode(EVENT_CHAINING)
 response:SetCondition(function(e,tp,eg,ep,ev,re) return re:GetHandler()==spell end)
 response:SetTarget(function() return true end)
 response:SetOperation(function() error("a player chained to Absorption") end)
 responder:RegisterEffect(response)
end
local observer=Effect.CreateEffect(spell)
observer:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
observer:SetCode(EVENT_CHAIN_END)
observer:SetOperation(function()
 assert(cost:IsLocation(LOCATION_GRAVE) and cost:IsReason(REASON_COST) and cost:IsReason(REASON_DESTROY))
 assert(not cost:IsReason(REASON_DISCARD),"cost must destroy, not discard")
 assert(a:IsLocation(LOCATION_GRAVE) and b:IsLocation(LOCATION_GRAVE))
 assert(a:IsReason(REASON_FUSION) and b:IsReason(REASON_FUSION))
 assert(fc:IsLocation(LOCATION_MZONE) and fc:IsSummonType(SUMMON_TYPE_FUSION))
 assert(our_response:IsLocation(LOCATION_MZONE) and their_response:IsLocation(LOCATION_MZONE))
 assert(Duel.GetFieldGroupCount(0,LOCATION_HAND,0)==0,"discarded material must not come from hand")
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(observer,0)
''')
 run(f'Absorption field Fusion owners={owners}, own facedown={facedown}; neither player can chain')

# A previously set Quick-Play Spell must also work during the opponent's turn.
logs.clear()
extra['script/probe.lua']=fixture('''
local driver=Debug.AddCard(98013005,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local spell=Debug.AddCard(98013010,1,1,LOCATION_SZONE,0,POS_FACEDOWN_DEFENSE)
local cost=Debug.AddCard(98013006,1,1,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local a=Debug.AddCard(98013005,1,1,LOCATION_MZONE,1,POS_FACEUP_ATTACK)
local b=Debug.AddCard(98013003,0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)
local fc=Debug.AddCard(98013013,1,1,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
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
Duel.SelectMatchingCard=function(tp,filter,p,own,other,min,max,excluded,...) return Group.FromCards(cost) end
Group.Select=function(g,tp,min,max,excluded) return Group.FromCards(g:GetFirst()) end
Duel.SelectFusionMaterial=function(tp,target,mg,mandatory,chkf)
 assert(tp==1 and target==fc and mg:IsContains(a) and mg:IsContains(b))
 assert(fc:CheckFusionMaterial(Group.FromCards(a,b),nil,tp))
 return Group.FromCards(a,b)
end
local observer=Effect.CreateEffect(driver)
observer:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
observer:SetCode(EVENT_CHAIN_END)
observer:SetOperation(function()
 assert(resolved,"Absorption must not negate the earlier chain link")
 assert(fc:IsLocation(LOCATION_MZONE) and fc:IsControler(1))
 assert(cost:IsReason(REASON_COST) and cost:IsReason(REASON_DESTROY))
 Debug.Message("RESOLUTION PASS")
end)
Duel.RegisterEffect(observer,0)
''')
run('Absorption previously set Quick-Play activation on opponent turn')

for issue in ['no extra hand card','opponent facedown material','immune material']:
 test('Absorption rejects '+issue,fixture('''
local spell=Debug.AddCard(98013010,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local a=Debug.AddCard(CODE,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)
local b=Debug.AddCard(98013003,1,1,LOCATION_MZONE,0,POSITION)
Debug.AddCard(98013013,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
'''.replace('CODE','98013012' if issue=='immune material' else '98013005').replace('POSITION','POS_FACEDOWN_DEFENSE' if issue=='opponent facedown material' else 'POS_FACEUP_ATTACK'),'''
local e=spell:GetActivateEffect()
CHECK
'''.replace('CHECK','assert(not c98013010.fusioncost(e,0,nil,0,0,nil,0,0,0))' if issue=='no extra hand card' else 'assert(not c98013010.fusiontarget(e,0,nil,0,0,nil,0,0,0))')))

logs.clear()
extra['script/probe.lua']=fixture('''
local recovery=nil
local native=Card.RegisterEffect
Card.RegisterEffect=function(c,e,...)
 if c:GetCode()==98013010 and e:IsHasType(EFFECT_TYPE_IGNITION) then recovery=e; e:SetDescription(999999) end
 return native(c,e,...)
end
local spell=Debug.AddCard(98013010,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local activation=spell:GetActivateEffect()
activation:SetDescription(999999)
local cost=Debug.AddCard(98013006,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local a=Debug.AddCard(98013005,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local b=Debug.AddCard(98013003,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local fc=Debug.AddCard(98013013,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
Duel.SelectMatchingCard=function(tp,filter,p,own,other,min,max,excluded,...) return Group.FromCards(cost) end
Group.Select=function(g,tp,min,max,excluded) return Group.FromCards(g:GetFirst()) end
Duel.SelectFusionMaterial=function(tp,target,mg,mandatory,chkf)
 assert(fc:CheckFusionMaterial(Group.FromCards(a,b),nil,tp))
 return Group.FromCards(a,b)
end
local chains=0
local finish=Effect.CreateEffect(spell)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_CHAIN_END)
finish:SetOperation(function()
 chains=chains+1
 if chains==1 then
  assert(spell:IsLocation(LOCATION_GRAVE) and fc:IsLocation(LOCATION_MZONE))
  assert(not activation:CheckCountLimit(0) and recovery:CheckCountLimit(0),"effect limits must be separate")
 elseif chains==2 then
  assert(spell:IsLocation(LOCATION_HAND) and Duel.GetFieldGroupCount(0,LOCATION_HAND,0)==2)
  assert(not activation:CheckCountLimit(0) and not recovery:CheckCountLimit(0))
  Debug.Message("RESOLUTION PASS")
 end
end)
Duel.RegisterEffect(finish,0)
''')
run('Absorption uses effect 1 then effect 2 in the same turn',activations=2)
