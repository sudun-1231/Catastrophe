-- Catastrophe Calamity King
local s,id=GetID()
local SET_CAT=0xfcb
function s.initial_effect(c)
 c:EnableReviveLimit()
 local limit=Effect.CreateEffect(c)
 limit:SetType(EFFECT_TYPE_SINGLE)
 limit:SetProperty(EFFECT_FLAG_CANNOT_DISABLE+EFFECT_FLAG_UNCOPYABLE)
 limit:SetCode(EFFECT_SPSUMMON_CONDITION)
 limit:SetValue(function(e,se)
  local card=e:GetHandler()
  return card:IsLocation(LOCATION_GRAVE+LOCATION_REMOVED) or se and se:GetHandler()==card
 end)
 c:RegisterEffect(limit)
 local sp=Effect.CreateEffect(c)
 sp:SetDescription(aux.Stringid(id,0))
 sp:SetCategory(CATEGORY_SPECIAL_SUMMON+CATEGORY_REMOVE)
 sp:SetProperty(EFFECT_FLAG_CARD_TARGET)
 sp:SetType(EFFECT_TYPE_IGNITION)
 sp:SetRange(LOCATION_HAND)
 sp:SetCountLimit(1,198013171)
 sp:SetCost(s.summoncost)
 sp:SetTarget(s.summontarget)
 sp:SetOperation(s.summonoperation)
 c:RegisterEffect(sp)
 s.registerprotection(c)
 s.registergrave(c,198013174,3)
end
function s.banishfilter(c,e) return c:IsAbleToRemove() and not c:IsImmuneToEffect(e) end

function s.destroyfilter(c) return c:IsSetCard(SET_CAT) and c:IsDestructable() end
function s.summoncost(e,tp,eg,ep,ev,re,r,rp,chk)
 if chk==0 then return Duel.IsExistingMatchingCard(s.destroyfilter,tp,LOCATION_DECK,0,1,nil) end
 e:SetLabel(0)
 Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_DESTROY)
 local g=Duel.SelectMatchingCard(tp,s.destroyfilter,tp,LOCATION_DECK,0,1,1,nil)
 if g:GetCount()>0 and Duel.Destroy(g,REASON_COST)>0 then e:SetLabel(1) end
end
function s.summontarget(e,tp,eg,ep,ev,re,r,rp,chk)
 if chk==0 then return Duel.GetLocationCount(tp,LOCATION_MZONE)>0 and e:GetHandler():IsCanBeSpecialSummoned(e,0,tp,true,false) and Duel.IsExistingTarget(s.banishfilter,tp,LOCATION_ONFIELD,LOCATION_ONFIELD,1,nil,e) end
 Duel.SetOperationInfo(0,CATEGORY_SPECIAL_SUMMON,e:GetHandler(),1,0,0)
 Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_REMOVE)
 Duel.SelectTarget(tp,s.banishfilter,tp,LOCATION_ONFIELD,LOCATION_ONFIELD,1,1,nil,e)
end
function s.summonoperation(e,tp)
 local c=e:GetHandler()
 if e:GetLabel()~=1 or not c:IsRelateToEffect(e) or not c:IsLocation(LOCATION_HAND) or Duel.GetLocationCount(tp,LOCATION_MZONE)<=0 then return end
 if Duel.SpecialSummon(c,0,tp,tp,true,false,POS_FACEUP)==0 then return end
 c:CompleteProcedure()
 local target=Duel.GetFirstTarget()
 if target and target:IsRelateToEffect(e) and s.banishfilter(target,e) then Duel.Remove(target,POS_FACEUP,REASON_EFFECT) end
end

function s.searchfilter(c)
 return c:IsSetCard(SET_CAT) and c:IsAbleToHand() and (not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup())
end
function s.searchtarget(e,tp,eg,ep,ev,re,r,rp,chk)
 if chk==0 then return Duel.IsExistingMatchingCard(aux.NecroValleyFilter(s.searchfilter),tp,LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED,0,1,nil) end
 Duel.SetOperationInfo(0,CATEGORY_TOHAND,nil,1,tp,LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED)
end
function s.searchoperation(e,tp)
 Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_ATOHAND)
 local g=Duel.SelectMatchingCard(tp,aux.NecroValleyFilter(s.searchfilter),tp,LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED,0,1,1,nil)
 if g:GetCount()>0 and Duel.SendtoHand(g,nil,REASON_EFFECT)>0 then Duel.ConfirmCards(1-tp,g) end
end
function s.registergrave(c,key,description)
 local e=Effect.CreateEffect(c)
 e:SetDescription(aux.Stringid(id,description))
 e:SetCategory(CATEGORY_TOHAND)
 e:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
 e:SetProperty(EFFECT_FLAG_DELAY)
 e:SetCode(EVENT_TO_GRAVE)
 e:SetCountLimit(1,key)
 e:SetTarget(s.searchtarget)
 e:SetOperation(s.searchoperation)
 c:RegisterEffect(e)
 local removed=e:Clone()
 removed:SetCode(EVENT_REMOVE)
 removed:SetCondition(function(e) return e:GetHandler():IsFaceup() end)
 c:RegisterEffect(removed)
end

function s.registerprotection(c)
 local release=Effect.CreateEffect(c)
 release:SetType(EFFECT_TYPE_FIELD)
 release:SetProperty(EFFECT_FLAG_PLAYER_TARGET)
 release:SetCode(EFFECT_CANNOT_RELEASE)
 release:SetRange(LOCATION_MZONE)
 release:SetTargetRange(0,1)
 release:SetTarget(function(e,card) return card:IsControler(e:GetHandlerPlayer()) and card:IsLocation(LOCATION_MZONE) and s.protected(e,card) end)
 c:RegisterEffect(release)
 for _,code in ipairs({EFFECT_CANNOT_BE_FUSION_MATERIAL,EFFECT_CANNOT_BE_SYNCHRO_MATERIAL,EFFECT_CANNOT_BE_XYZ_MATERIAL,EFFECT_CANNOT_BE_LINK_MATERIAL}) do
  local material=Effect.CreateEffect(c)
  material:SetType(EFFECT_TYPE_FIELD)
  material:SetProperty(EFFECT_FLAG_IGNORE_IMMUNE)
  material:SetCode(code)
  material:SetRange(LOCATION_MZONE)
  material:SetTargetRange(LOCATION_MZONE,0)
  material:SetTarget(s.protected)
  material:SetValue(s.materiallimit)
  c:RegisterEffect(material)
 end
end
function s.protected(e,c) return c:IsFaceup() and c:IsSetCard(SET_CAT) end
function s.materiallimit(e,fc)
 return fc~=nil and fc:IsControler(1-e:GetHandlerPlayer())
end
