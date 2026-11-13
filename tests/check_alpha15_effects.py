"""Avramax-style targeting protection and all previous native regressions."""
import pathlib
import runpy
previous=runpy.run_path(str(pathlib.Path(__file__).with_name('check_alpha14_effects.py')))
state=previous['state']
fixture=state['fixture'];extra=state['extra'];logs=state['logs'];run=state['run_resolution'];test=state['test']

for faceup in [True,False]:
 logs.clear()
 extra['script/probe.lua']=fixture("""
local c=Debug.AddCard(98013012,1,1,LOCATION_MZONE,0,POSITION)
local ally=Debug.AddCard(98013005,1,1,LOCATION_MZONE,1,POS_FACEUP_ATTACK)
local attacker=Debug.AddCard(98013005,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
""".replace('POSITION','POS_FACEUP_ATTACK' if faceup else 'POS_FACEDOWN_DEFENSE'),"""
local operation=Effect.CreateEffect(attacker)
operation:SetDescription(999999)
operation:SetType(EFFECT_TYPE_IGNITION)
operation:SetRange(LOCATION_MZONE)
operation:SetCountLimit(1)
operation:SetOperation(function()
 assert(not c:IsSummonType(SUMMON_TYPE_FUSION))
 local targets=attacker:GetAttackableTarget()
 CHECK
 Debug.Message("RESOLUTION PASS")
end)
attacker:RegisterEffect(operation)
""".replace('CHECK','assert(targets:GetCount()==1 and targets:IsContains(c) and not targets:IsContains(ally),"opponent must attack Catastrophe")' if faceup else 'assert(targets:IsContains(ally),"facedown Catastrophe must not restrict attacks")'))
 run('Catastrophe attack-target restriction '+('faceup' if faceup else 'facedown'))

for opponent in [True,False]:
 logs.clear()
 owner=1 if opponent else 0
 extra['script/probe.lua']=fixture(f'''
local c=Debug.AddCard(98013012,{owner},{owner},LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local driver=Debug.AddCard(98013005,0,0,LOCATION_MZONE,1,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
''','''
local operation=Effect.CreateEffect(driver)
operation:SetDescription(999999)
operation:SetType(EFFECT_TYPE_IGNITION)
operation:SetRange(LOCATION_MZONE)
operation:SetCountLimit(1)
operation:SetOperation(function(e)
 CHECK
 Debug.Message("RESOLUTION PASS")
end)
driver:RegisterEffect(operation)
'''.replace('CHECK','assert(not c:IsCanBeEffectTarget(e),"opponent can target Catastrophe")' if opponent else 'assert(c:IsCanBeEffectTarget(e),"own card must remain targetable")'))
 run('Catastrophe '+('opponent effect targeting blocked' if opponent else 'own effect targeting allowed'))

logs.clear()
extra['script/probe.lua']=fixture("""
local c=Debug.AddCard(98013012,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
local ally=Debug.AddCard(98013005,1,1,LOCATION_MZONE,1,POS_FACEUP_ATTACK)
local driver=Debug.AddCard(98013005,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK)
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
""","""
local operation=Effect.CreateEffect(driver)
operation:SetDescription(999999)
operation:SetType(EFFECT_TYPE_IGNITION)
operation:SetRange(LOCATION_MZONE)
operation:SetCountLimit(1)
operation:SetOperation(function()
 assert(not driver:GetAttackableTarget():IsContains(ally))
 Duel.SendtoGrave(c,REASON_COST)
 assert(c:IsLocation(LOCATION_GRAVE))
 assert(driver:GetAttackableTarget():IsContains(ally),"restriction survived leaving the field")
 Debug.Message("RESOLUTION PASS")
end)
driver:RegisterEffect(operation)
""")
run('Catastrophe attack restriction ends on leaving the field')
