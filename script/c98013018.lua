-- Catastrophe Watchkeeper
local s,id=GetID()
local SET_CAT=0xfcb
function s.initial_effect(c)
 c:EnableReviveLimit()
 if Link and Link.AddProcedure then Link.AddProcedure(c,nil,1,1) else aux.AddLinkProcedure(c,nil,1,1) end
 local protect=Effect.CreateEffect(c)
 protect:SetType(EFFECT_TYPE_FIELD)
 protect:SetCode(EFFECT_CANNOT_BE_EFFECT_TARGET)
 protect:SetRange(LOCATION_ONFIELD)
 protect:SetTargetRange(LOCATION_MZONE,0)
 protect:SetTarget(function(e,c) return c:IsFaceup() and c:IsSetCard(SET_CAT) and c:IsType(TYPE_FUSION) end)
 protect:SetValue(aux.tgoval)
 c:RegisterEffect(protect)
 local on=Effect.CreateEffect(c)
 on:SetDescription(aux.Stringid(id,1))
 on:SetCategory(CATEGORY_TOHAND)
 on:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_TRIGGER_O)
 on:SetRange(LOCATION_MZONE)
 on:SetProperty(EFFECT_FLAG_DELAY)
 on:SetCode(EVENT_SUMMON_SUCCESS)
 on:SetCountLimit(1,198013182)
 on:SetCondition(s.othercon)
 on:SetTarget(s.searchtarget)
 on:SetOperation(s.searchoperation)
 c:RegisterEffect(on)
 local special=on:Clone()
 special:SetCode(EVENT_SPSUMMON_SUCCESS)
 c:RegisterEffect(special)
 -- A separate SINGLE trigger handles this card's own Summon.
 -- The FIELD triggers above handle other archetype monsters only.
 local selfsummon=on:Clone()
 selfsummon:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
 selfsummon:SetCode(EVENT_SPSUMMON_SUCCESS)
 selfsummon:SetCondition(function(e) return e:GetHandler():IsFaceup() and e:GetHandler():IsLocation(LOCATION_MZONE) end)
 c:RegisterEffect(selfsummon)
 local recover=Effect.CreateEffect(c)
 recover:SetDescription(aux.Stringid(id,2))
 recover:SetCategory(CATEGORY_TODECK+CATEGORY_SPECIAL_SUMMON)
 recover:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
 recover:SetProperty(EFFECT_FLAG_DELAY)
 recover:SetCode(EVENT_TO_GRAVE)
 recover:SetCountLimit(1,198013183)
 recover:SetTarget(s.rectarget)
 recover:SetOperation(s.recoperation)
 c:RegisterEffect(recover)
 local removed=recover:Clone()
 removed:SetCode(EVENT_REMOVE)
 removed:SetCondition(function(e) return e:GetHandler():IsFaceup() end)
 c:RegisterEffect(removed)
end
function s.summoned(c,tp,handler)
 return c~=handler and c:IsControler(tp) and c:IsSetCard(SET_CAT)
end
function s.othercon(e,tp,eg)
 return eg and eg:IsExists(s.summoned,1,nil,tp,e:GetHandler())
end
function s.revivefilter(c,e,tp)
 return c:IsSetCard(SET_CAT) and c:IsType(TYPE_MONSTER) and (not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup())
  and c:IsCanBeSpecialSummoned(e,0,tp,false,false)
end
function s.rectarget(e,tp,eg,ep,ev,re,r,rp,chk)
 local c=e:GetHandler()
 if chk==0 then return c:IsAbleToDeck() and Duel.GetLocationCount(tp,LOCATION_MZONE)>0
  and Duel.IsExistingMatchingCard(aux.NecroValleyFilter(s.revivefilter),tp,LOCATION_HAND+LOCATION_GRAVE+LOCATION_REMOVED,0,1,c,e,tp) end
 Duel.SetOperationInfo(0,CATEGORY_TODECK,c,1,0,0)
 Duel.SetOperationInfo(0,CATEGORY_SPECIAL_SUMMON,nil,1,tp,LOCATION_HAND+LOCATION_GRAVE+LOCATION_REMOVED)
end
function s.recoperation(e,tp)
 local c=e:GetHandler()
 if not c:IsRelateToEffect(e) or not c:IsAbleToDeck() or Duel.SendtoDeck(c,nil,SEQ_DECKSHUFFLE,REASON_EFFECT)==0 then return end
 if Duel.GetLocationCount(tp,LOCATION_MZONE)<=0 then return end
 Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_SPSUMMON)
 local g=Duel.SelectMatchingCard(tp,aux.NecroValleyFilter(s.revivefilter),tp,LOCATION_HAND+LOCATION_GRAVE+LOCATION_REMOVED,0,1,1,c,e,tp)
 if g:GetCount()>0 then Duel.SpecialSummon(g,0,tp,tp,false,false,POS_FACEUP) end
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
