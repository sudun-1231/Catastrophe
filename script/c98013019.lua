-- Catastrophe End Dragon
local s,id=GetID()
local SET_CAT=0xfcb
function s.initial_effect(c)
 c:EnableReviveLimit()
 if Link and Link.AddProcedure then Link.AddProcedure(c,aux.FilterBoolFunction(Card.IsSetCard,SET_CAT),2) else aux.AddLinkProcedure(c,aux.FilterBoolFunction(Card.IsSetCard,SET_CAT),2) end
 s.registerprotection(c)
 local negate=Effect.CreateEffect(c)
 negate:SetDescription(aux.Stringid(id,2))
 negate:SetCategory(CATEGORY_NEGATE+CATEGORY_DESTROY)
 negate:SetType(EFFECT_TYPE_QUICK_O)
 negate:SetCode(EVENT_CHAINING)
 negate:SetProperty(EFFECT_FLAG_DAMAGE_STEP+EFFECT_FLAG_DAMAGE_CAL)
 negate:SetRange(LOCATION_MZONE)
 negate:SetCountLimit(1,198013193)
 negate:SetCondition(function(e,tp,eg,ep,ev,re,r,rp) return rp==1-tp and Duel.IsChainNegatable(ev) end)
 negate:SetTarget(s.negtarget)
 negate:SetOperation(s.negoperation)
 c:RegisterEffect(negate)
 local recover=Effect.CreateEffect(c)
 recover:SetDescription(aux.Stringid(id,3))
 recover:SetCategory(CATEGORY_TODECK+CATEGORY_TOHAND)
 recover:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
 recover:SetProperty(EFFECT_FLAG_DELAY)
 recover:SetCode(EVENT_TO_GRAVE)
 recover:SetCountLimit(1,198013194)
 recover:SetTarget(s.rectarget)
 recover:SetOperation(s.recoperation)
 c:RegisterEffect(recover)
 local removed=recover:Clone()
 removed:SetCode(EVENT_REMOVE)
 removed:SetCondition(function(e) return e:GetHandler():IsFaceup() end)
 c:RegisterEffect(removed)
end
function s.negtarget(e,tp,eg,ep,ev,re,r,rp,chk)
 if chk==0 then return true end
 Duel.SetOperationInfo(0,CATEGORY_NEGATE,eg,1,0,0)
 if re:GetHandler():IsRelateToEffect(re) then Duel.SetOperationInfo(0,CATEGORY_DESTROY,eg,1,0,0) end
end
function s.negoperation(e,tp,eg,ep,ev,re)
 if Duel.NegateActivation(ev) and re:GetHandler():IsRelateToEffect(re) then Duel.Destroy(re:GetHandler(),REASON_EFFECT) end
end
function s.recfilter(c) return c:IsAbleToHand() end
function s.rectarget(e,tp,eg,ep,ev,re,r,rp,chk)
 local c=e:GetHandler()
 if chk==0 then return c:IsAbleToDeck() and Duel.IsExistingMatchingCard(aux.NecroValleyFilter(s.recfilter),tp,LOCATION_GRAVE+LOCATION_REMOVED,0,1,c) end
 Duel.SetOperationInfo(0,CATEGORY_TODECK,c,1,0,0)
 Duel.SetOperationInfo(0,CATEGORY_TOHAND,nil,1,tp,LOCATION_GRAVE+LOCATION_REMOVED)
end
function s.recoperation(e,tp)
 local c=e:GetHandler()
 if not c:IsRelateToEffect(e) or not c:IsAbleToDeck() or Duel.SendtoDeck(c,nil,SEQ_DECKSHUFFLE,REASON_EFFECT)==0 then return end
 Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_ATOHAND)
 local g=Duel.SelectMatchingCard(tp,aux.NecroValleyFilter(s.recfilter),tp,LOCATION_GRAVE+LOCATION_REMOVED,0,1,1,c)
 if g:GetCount()>0 and Duel.SendtoHand(g,nil,REASON_EFFECT)>0 then Duel.ConfirmCards(1-tp,g) end
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
