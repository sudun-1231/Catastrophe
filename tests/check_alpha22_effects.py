"""Forerunner, Invasion and expanded protection, with prior native regressions."""
import pathlib,runpy
previous=runpy.run_path(str(pathlib.Path(__file__).with_name('check_alpha21_effects.py')))
state=previous['state'];fixture=state['fixture'];extra=state['extra'];logs=state['logs'];run=state['run_resolution'];test=state['test']
FILL=previous['FILL'];DRIVER=previous['DRIVER'];CAP=previous['CAP'].replace('<=98013019','<=98013021')
def chaincase(name,cards,setup,check,driverbody='resolved=true',driverlocation='LOCATION_MZONE'):
 logs.clear()
 driver=DRIVER.replace('LOCATION_MZONE',driverlocation)
 extra['script/probe.lua']=fixture(CAP+cards+driver+FILL,setup+'''
local resolved=false
local action=Effect.CreateEffect(driver)
action:SetDescription(999999)
action:SetType(EFFECT_TYPE_IGNITION)
action:SetRange(DRIVERLOCATION)
action:SetCountLimit(1)
action:SetOperation(function(e) DRIVERBODY end)
driver:RegisterEffect(action)
local watch=Effect.CreateEffect(driver)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_CHAIN_END)
watch:SetOperation(function()
 CHECK
end)
Duel.RegisterEffect(watch,0)
'''.replace('DRIVERLOCATION',driverlocation).replace('DRIVERBODY',driverbody).replace('CHECK',check))
 run(name)
# Opponent-only hand responses, across monster effects and Spell/Trap effect activations.
for code in [98013020,98013021]:
 for owner in [0,1]:
  for loc in ['LOCATION_MZONE','LOCATION_SZONE']:
   cards=f'''local c=Debug.AddCard({code},{owner},{owner},LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local selected=Debug.AddCard(98013020,{owner},{owner},LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
local cost=Debug.AddCard(98013006,{owner},{owner},LOCATION_DECK,0,POS_FACEDOWN_DEFENSE)
'''
   setup='''Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 for _,card in ipairs(l1==LOCATION_DECK and {cost,selected} or {selected,cost}) do
  if card~=excluded and card:IsControler(p) and card:IsLocation(l1) and filter(card,...) then return Group.FromCards(card) end
 end
 error("no expected candidate")
end
'''
   if owner==0:check='assert(resolved and c:IsLocation(LOCATION_HAND));Debug.Message("RESOLUTION PASS")'
   elif code==98013020:check='''if c:IsLocation(LOCATION_MZONE) and selected:IsLocation(LOCATION_HAND) then
assert(resolved and cost:IsLocation(LOCATION_GRAVE),"Forerunner response sequence")
for _,e in ipairs(effects[c]) do if e:GetCode()==EVENT_CHAINING or e:GetCode()==EVENT_SPSUMMON_SUCCESS then assert(not e:CheckCountLimit(1)) end end
Debug.Message("RESOLUTION PASS") end'''
   else:check='''if selected:IsLocation(LOCATION_MZONE) then
assert(not resolved and driver:IsLocation(DRIVERLOC),"Invasion must negate effect without destroying card")
assert(cost:IsLocation(LOCATION_DECK))
for _,e in ipairs(effects[c]) do
 if e:GetCode()==EVENT_CHAINING then assert(not e:CheckCountLimit(1))
 elseif bit.band(e:GetType(),EFFECT_TYPE_IGNITION)~=0 then assert(e:CheckCountLimit(1),"recovery must have independent HOPT") end
end
Debug.Message("RESOLUTION PASS") end'''.replace('DRIVERLOC',loc)
   chaincase(f'{code} response owner={owner} source={loc}',cards,setup,check,driverlocation=loc)
# Forerunner may decline Deck destruction; Special Summon still searches.
chaincase('Forerunner decline destruction', '''
local c=Debug.AddCard(98013020,1,1,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local selected=Debug.AddCard(98013020,1,1,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
''','''Duel.SelectYesNo=function() return false end
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 assert(filter(selected,...));return Group.FromCards(selected)
end
''','if c:IsLocation(LOCATION_MZONE) and selected:IsLocation(LOCATION_HAND) then assert(resolved);Debug.Message("RESOLUTION PASS") end')
# Forerunner actual mandatory-handler Fusion from GY and face-up banish.
for removed in [False,True]:
 chaincase(f'Forerunner mandatory Fusion removed={removed}','''
local c=Debug.AddCard(98013020,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local material=Debug.AddCard(98013001,0,0,LOCATION_REMOVED,0,POS_FACEUP_ATTACK)
local fc=Debug.AddCard(98013013,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
''','''
Group.Select=function(g,tp,min,max,excluded) return Group.FromCards(fc) end
Duel.SelectFusionMaterial=function(tp,target,mg,mandatory,chkf)
 if FUSION_SELF_OPTIONAL then assert(mandatory==nil) else assert(mandatory==c) end
 assert(mg:IsContains(c) and mg:IsContains(material))
 assert(fc:CheckFusionMaterial(mg,c,tp))
 return Group.FromCards(c,material)
end
Duel.SortDecktop=function() end
''','''if fc:IsLocation(LOCATION_MZONE) then
 assert(fc:IsSummonType(SUMMON_TYPE_FUSION) and c:IsLocation(LOCATION_DECK) and material:IsLocation(LOCATION_DECK))
 Debug.Message("RESOLUTION PASS") end''','Duel.Remove(c,POS_FACEUP,REASON_EFFECT)' if removed else 'Duel.SendtoGrave(c,REASON_EFFECT)')
# Invasion can summon from all four areas and optionally Fusion using bottom-deck material.
for loc in ['LOCATION_HAND','LOCATION_DECK','LOCATION_GRAVE','LOCATION_REMOVED']:
 for fusion in [False,True]:
  cards=f'''
local c=Debug.AddCard(98013021,1,1,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local selected=Debug.AddCard(98013020,1,1,{loc},0,POS_FACEUP_ATTACK)
local material=Debug.AddCard(98013001,1,1,LOCATION_REMOVED,0,POS_FACEUP_ATTACK)
local fc=Debug.AddCard(98013013,1,1,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
'''
  setup='''
Duel.SelectYesNo=function() return CONSENT end
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 assert(filter(selected,...));return Group.FromCards(selected)
end
Group.Select=function(g,tp,min,max,excluded) return Group.FromCards(fc) end
Duel.SelectFusionMaterial=function(tp,target,mg,mandatory,chkf)
 assert(mandatory==nil and target==fc)
 assert(fc:CheckFusionMaterial(mg,nil,tp))
 return Group.FromCards(selected,material)
end
Duel.SortDecktop=function() end
'''.replace('CONSENT',str(fusion).lower())
  if fusion:check='''if fc:IsLocation(LOCATION_MZONE) then
 assert(not resolved and selected:IsLocation(LOCATION_DECK) and material:IsLocation(LOCATION_DECK))
 assert(fc:IsSummonType(SUMMON_TYPE_FUSION));Debug.Message("RESOLUTION PASS") end'''
  else:
   # Use a monster without a summon trigger so the unrelated search does not obscure the assertion.
   cards=cards.replace('local selected=Debug.AddCard(98013020','local selected=Debug.AddCard(98013001')
   check='if selected:IsLocation(LOCATION_MZONE) then assert(not resolved and fc:IsLocation(LOCATION_EXTRA));Debug.Message("RESOLUTION PASS") end'
  chaincase(f'Invasion summon {loc}, optional Fusion={fusion}',cards,setup,check)
# Return as cost removes relation: recovery must still resolve from both locations.
for loc in ['LOCATION_GRAVE','LOCATION_REMOVED']:
 for destination in ['LOCATION_DECK','LOCATION_GRAVE','LOCATION_REMOVED']:
  logs.clear()
  extra['script/probe.lua']=fixture(CAP+f'''
local c=Debug.AddCard(98013021,0,0,{loc},0,POS_FACEUP_ATTACK)
local selected=Debug.AddCard(98013006,0,0,{destination},0,POS_FACEUP_ATTACK)
'''+FILL,'''
for _,e in ipairs(effects[c]) do if bit.band(e:GetType(),EFFECT_TYPE_IGNITION)~=0 then e:SetDescription(999999) end end
Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 assert(filter(selected,...));return Group.FromCards(selected)
end
local watch=Effect.CreateEffect(c)
watch:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
watch:SetCode(EVENT_CHAIN_END)
watch:SetOperation(function()
 if c:IsLocation(LOCATION_DECK) and selected:IsLocation(LOCATION_HAND) then Debug.Message("RESOLUTION PASS") end
end)
Duel.RegisterEffect(watch,0)
''')
  run(f'Invasion recovery from {loc} search {destination}')
# Continuous source range now includes the Spell/Trap Zone.
for code in [98013017,98013019]:
 chaincase(f'{code} SZONE tribute and material protection',f'''
local c=Debug.AddCard({code},1,1,LOCATION_SZONE,0,POS_FACEUP_ATTACK)
local protected=Debug.AddCard(98013012,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)
local own=Debug.AddCard(98013019,1,1,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
local other=Debug.AddCard(98013019,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
''','', 'assert(resolved);Debug.Message("RESOLUTION PASS")','''
assert(not protected:IsReleasable())
for _,method in ipairs({Card.IsCanBeFusionMaterial,Card.IsCanBeSynchroMaterial,Card.IsCanBeXyzMaterial,Card.IsCanBeLinkMaterial}) do
 assert(method(protected,own) and not method(protected,other))
end
resolved=true
''')
chaincase('Watchkeeper SZONE target protection','''
local c=Debug.AddCard(98013018,1,1,LOCATION_SZONE,0,POS_FACEUP_ATTACK)
local protected=Debug.AddCard(98013014,1,1,LOCATION_MZONE,0,POS_FACEUP_ATTACK,true)
''','','assert(resolved);Debug.Message("RESOLUTION PASS")','assert(not protected:IsCanBeEffectTarget(e));resolved=true')
for loc in ['LOCATION_DECK','LOCATION_REMOVED']:
 chaincase(f'Forerunner summon search from {loc}',f'''
local c=Debug.AddCard(98013020,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
local selected=Debug.AddCard(98013020,0,0,{loc},0,POS_FACEUP_ATTACK)
''','''Duel.SelectMatchingCard=function(tp,filter,p,l1,l2,min,max,excluded,...)
 assert(filter(selected,...));return Group.FromCards(selected)
end
''','if selected:IsLocation(LOCATION_HAND) then Debug.Message("RESOLUTION PASS") end','Duel.SpecialSummon(c,0,0,0,false,false,POS_FACEUP)')
for code in [98013020,98013021]:
 test(f'{code} facedown banish and archetype filters',fixture(f'''
local c=Debug.AddCard({code},0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
local facedown=Debug.AddCard(98013020,0,0,LOCATION_REMOVED,0,POS_FACEDOWN_DEFENSE)
local faceup=Debug.AddCard(98013020,0,0,LOCATION_REMOVED,1,POS_FACEUP_ATTACK)
local noncat=Debug.AddCard(99998001,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
local spell=Debug.AddCard(98013006,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
''',f'''
assert(not c{code}.searchfilter(facedown) and c{code}.searchfilter(faceup))
assert(not c{code}.searchfilter(noncat))
assert(c{code}.searchfilter(spell)=={str(code==98013021 or state['SELF_OPTIONAL']).lower()})
'''))
test('Invasion requires a legal Special Summon candidate',fixture('''
local c=Debug.AddCard(98013021,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
Debug.AddCard(98013020,0,0,LOCATION_REMOVED,0,POS_FACEDOWN_DEFENSE)
''','''local e=Effect.CreateEffect(c)
assert(not c98013021.sptarget(e,0,nil,0,0,nil,0,1,0))
'''))
test('Forerunner handler material requirement follows card text',fixture('''
local c=Debug.AddCard(98013020,0,0,LOCATION_GRAVE,0,POS_FACEUP_ATTACK)
Debug.AddCard(98013001,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
Debug.AddCard(98013002,0,0,LOCATION_HAND,0,POS_FACEDOWN_DEFENSE)
Debug.AddCard(98013013,0,0,LOCATION_EXTRA,0,POS_FACEDOWN_DEFENSE)
''','''
local block=Effect.CreateEffect(c);block:SetType(EFFECT_TYPE_SINGLE);block:SetCode(EFFECT_CANNOT_TO_DECK);c:RegisterEffect(block)
local e=Effect.CreateEffect(c);e:SetType(EFFECT_TYPE_SINGLE);e:SetCode(EFFECT_UPDATE_ATTACK);e:SetValue(0);c:RegisterEffect(e)
assert(c98013020.fus_target(e,0,nil,0,0,nil,0,0,0)==FUSION_SELF_OPTIONAL)
'''))
