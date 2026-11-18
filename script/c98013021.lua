-- Catastrophe Invasion
local s,id=GetID()
local SET_CAT=0xfcb
function s.initial_effect(c)
 local activate=Effect.CreateEffect(c)
 activate:SetDescription(aux.Stringid(id,0))
 activate:SetCategory(CATEGORY_DISABLE+CATEGORY_SPECIAL_SUMMON+CATEGORY_FUSION_SUMMON+CATEGORY_TODECK)
 activate:SetType(EFFECT_TYPE_ACTIVATE)
 activate:SetCode(EVENT_CHAINING)
 activate:SetCountLimit(1,198013211)
 activate:SetCondition(function(e,tp,eg,ep,ev,re,r,rp) return rp==1-tp and Duel.IsChainDisablable(ev) end)
 activate:SetTarget(s.sptarget)
 activate:SetOperation(s.spoperation)
 c:RegisterEffect(activate)
 local hand=Effect.CreateEffect(c)
 hand:SetType(EFFECT_TYPE_SINGLE)
 hand:SetCode(EFFECT_TRAP_ACT_IN_HAND)
 c:RegisterEffect(hand)
 local recover=Effect.CreateEffect(c)
 recover:SetDescription(aux.Stringid(id,1))
 recover:SetCategory(CATEGORY_TODECK+CATEGORY_TOHAND)
 recover:SetType(EFFECT_TYPE_IGNITION)
 recover:SetRange(LOCATION_GRAVE+LOCATION_REMOVED)
 recover:SetCountLimit(1,198013212)
 recover:SetCondition(function(e) local c=e:GetHandler();return not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup() end)
 recover:SetCost(s.returncost)
 recover:SetTarget(s.searchtarget)
 recover:SetOperation(s.searchoperation)
 c:RegisterEffect(recover)
end
function s.spfilter(c,e,tp)
 return c:IsSetCard(SET_CAT) and c:IsType(TYPE_MONSTER) and (not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup())
  and c:IsCanBeSpecialSummoned(e,0,tp,false,false)
end
function s.sptarget(e,tp,eg,ep,ev,re,r,rp,chk)
 if chk==0 then return Duel.GetLocationCount(tp,LOCATION_MZONE)>0 and Duel.IsExistingMatchingCard(aux.NecroValleyFilter(s.spfilter),tp,LOCATION_HAND+LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED,0,1,nil,e,tp) end
 Duel.SetOperationInfo(0,CATEGORY_DISABLE,eg,1,0,0)
 Duel.SetOperationInfo(0,CATEGORY_SPECIAL_SUMMON,nil,1,tp,LOCATION_HAND+LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED)
end
function s.spoperation(e,tp,eg,ep,ev)
 if not Duel.NegateEffect(ev) then return end
 if Duel.GetLocationCount(tp,LOCATION_MZONE)<=0 then return end
 Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_SPSUMMON)
 local g=Duel.SelectMatchingCard(tp,aux.NecroValleyFilter(s.spfilter),tp,LOCATION_HAND+LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED,0,1,1,nil,e,tp)
 if g:GetCount()==0 or Duel.SpecialSummon(g,0,tp,tp,false,false,POS_FACEUP)==0 then return end
 local mg=s.group(e,tp,true)
 if Duel.IsExistingMatchingCard(s.fusion,tp,LOCATION_EXTRA,0,1,nil,e,tp,mg,true) and Duel.SelectYesNo(tp,aux.Stringid(id,2)) then s.summon(e,tp,true) end
end
function s.returncost(e,tp,eg,ep,ev,re,r,rp,chk)
 local c=e:GetHandler()
 if chk==0 then return c:IsAbleToDeckAsCost() end
 Duel.SendtoDeck(c,nil,SEQ_DECKSHUFFLE,REASON_COST)
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
function s.material(c,e,bottom)
    return c:IsType(TYPE_MONSTER) and c:IsCanBeFusionMaterial()
        and not c:IsImmuneToEffect(e)
        and (not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup())
        and ((bottom and c:IsAbleToDeck()) or (not bottom and c:IsAbleToGrave()))
end
function s.group(e,tp,bottom)
    local loc=LOCATION_HAND+LOCATION_MZONE
    if bottom then loc=loc+LOCATION_GRAVE+LOCATION_REMOVED else loc=loc+LOCATION_DECK end
    return Duel.GetMatchingGroup(aux.NecroValleyFilter(s.material),tp,loc,0,nil,e,bottom)
end
function s.fusion(c,e,tp,mg,bottom)
    return c:IsType(TYPE_FUSION) and c:IsSetCard(SET_CAT)
        and c:IsCanBeSpecialSummoned(e,SUMMON_TYPE_FUSION,tp,false,false)
        and c:CheckFusionMaterial(mg,nil,tp)
end
function s.summon(e,tp,bottom)
    local mg=s.group(e,tp,bottom)
    local candidates=Duel.GetMatchingGroup(s.fusion,tp,LOCATION_EXTRA,0,nil,e,tp,mg,bottom)
    if candidates:GetCount()==0 then return end
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_SPSUMMON)
    local fc=candidates:Select(tp,1,1,nil):GetFirst()
    if not fc then return end
    local materials=Duel.SelectFusionMaterial(tp,fc,mg,nil,tp)
    if materials:GetCount()==0 then return end
    fc:SetMaterial(materials)
    if bottom then
        local hidden=materials:Filter(Card.IsFacedown,nil)
        if hidden:GetCount()>0 then Duel.ConfirmCards(1-tp,hidden) end
        local count=materials:GetCount()
        if aux.PlaceCardsOnDeckBottom then
            if aux.PlaceCardsOnDeckBottom(tp,materials,REASON_EFFECT+REASON_MATERIAL+REASON_FUSION)~=count then return end
        else
            if Duel.SendtoDeck(materials,nil,SEQ_DECKBOTTOM,REASON_EFFECT+REASON_MATERIAL+REASON_FUSION)~=count then return end
            local returned=Duel.GetOperatedGroup():Filter(Card.IsLocation,nil,LOCATION_DECK)
            local own=returned:FilterCount(Card.IsControler,nil,tp)
            if own>0 then Duel.SortDeckbottom(tp,tp,own) end
            if returned:GetCount()>own then Duel.SortDeckbottom(tp,1-tp,returned:GetCount()-own) end
        end
    else
        Duel.SendtoGrave(materials,REASON_EFFECT+REASON_MATERIAL+REASON_FUSION)
    end
    Duel.BreakEffect()
    if Duel.SpecialSummon(fc,SUMMON_TYPE_FUSION,tp,tp,false,false,POS_FACEUP)>0 then fc:CompleteProcedure() end
end
