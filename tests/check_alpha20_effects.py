"""Double piercing damage, with all previous native regression cases."""
import pathlib
import runpy
previous=runpy.run_path(str(pathlib.Path(__file__).with_name('check_alpha18_effects.py')))
state=previous['state']
fixture=state['fixture'];extra=state['extra'];logs=state['logs'];run=state['run_resolution']

cases=[
 ('double pierce 11000',2000,500,'POS_FACEUP_DEFENSE',1,0,11000),
 ('double pierce 4000',500,2500,'POS_FACEUP_DEFENSE',1,0,4000),
 ('decline ATK gain, double pierce 3000',500,2500,'POS_FACEUP_DEFENSE',0,0,3000),
 ('higher DEF: own damage stays 500',500,5000,'POS_FACEUP_DEFENSE',1,500,0),
 ('equal DEF: no damage',500,4500,'POS_FACEUP_DEFENSE',1,0,0),
 ('attack-position battle is not doubled',500,2500,'POS_FACEUP_ATTACK',1,0,4000),
 ('direct attack is not doubled',500,2500,None,1,0,4000),
]
for name,atk,defense,position,consent,own_damage,other_damage in cases:
 logs.clear()
 state['rows'][99998002]=(99998002,0,0,17,atk,defense,4,8192,32)
 enemy=f'local enemy=Debug.AddCard(99998002,1,1,LOCATION_MZONE,0,{position})' if position else ''
 extra['script/probe.lua']=fixture('''
local c=Debug.AddCard(98013015,0,0,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)
ENEMY
for player=0,1 do for i=1,10 do Debug.AddCard(98013006,player,player,LOCATION_DECK,0,POS_FACEDOWN_DEFENSE) end end
'''.replace('ENEMY',enemy),f'''
local ended=false
local finish=Effect.CreateEffect(c)
finish:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
finish:SetCode(EVENT_DAMAGE_STEP_END)
finish:SetOperation(function() ended=true end)
Duel.RegisterEffect(finish,0)
local watch=Effect.CreateEffect(c)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_ADJUST)
watch:SetOperation(function()
 if ended and c:GetAttack()==4000 then
  assert(Duel.GetLP(0)=={20000-own_damage},"incorrect damage to attacking player")
  assert(Duel.GetLP(1)=={20000-other_damage},"incorrect damage to defending player")
  Debug.Message("RESOLUTION PASS")
 end
end)
Duel.RegisterEffect(watch,0)
''').replace('Debug.ReloadFieldBegin(0)','Debug.ReloadFieldBegin(DUEL_ATTACK_FIRST_TURN)').replace('Debug.SetPlayerInfo(0,8000,0,0)','Debug.SetPlayerInfo(0,20000,0,0)').replace('Debug.SetPlayerInfo(1,8000,0,0)','Debug.SetPlayerInfo(1,20000,0,0)')
 run('Chimera '+name,battle=True,yes_no=consent)
