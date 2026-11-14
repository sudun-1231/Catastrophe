-- Catastrophe's Birth: MDPro3 legacy/modern compatible Fusion effects.
local s,id=GetID()
local SET_CAT=0xfcb
function s.initial_effect(c)
    local e1=Effect.CreateEffect(c)
    e1:SetDescription(aux.Stringid(id,0))
    e1:SetCategory(CATEGORY_SPECIAL_SUMMON+CATEGORY_FUSION_SUMMON)
    e1:SetType(EFFECT_TYPE_ACTIVATE)
    e1:SetCode(EVENT_FREE_CHAIN)
    e1:SetCountLimit(1,198013081)
    e1:SetTarget(s.target1)
    e1:SetOperation(s.operation1)
    c:RegisterEffect(e1)
    local e2=Effect.CreateEffect(c)
    e2:SetDescription(aux.Stringid(id,1))
    e2:SetCategory(CATEGORY_TODECK+CATEGORY_SPECIAL_SUMMON+CATEGORY_FUSION_SUMMON)
    e2:SetType(EFFECT_TYPE_IGNITION)
    e2:SetRange(LOCATION_GRAVE+LOCATION_REMOVED)
    e2:SetCountLimit(1,198013082)
    e2:SetCondition(function(e)
        local c=e:GetHandler()
        return not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup()
    end)
    e2:SetCost(s.returncost)
    e2:SetTarget(s.target2)
    e2:SetOperation(s.operation2)
    c:RegisterEffect(e2)
end
function s.returncost(e,tp,eg,ep,ev,re,r,rp,chk)
    local c=e:GetHandler()
    if chk==0 then return c:IsAbleToDeckAsCost() end
    Duel.SendtoDeck(c,nil,SEQ_DECKSHUFFLE,REASON_COST)
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
    return c:IsType(TYPE_FUSION) and (bottom or c:IsSetCard(SET_CAT))
        and c:IsCanBeSpecialSummoned(e,SUMMON_TYPE_FUSION,tp,false,false)
        and c:CheckFusionMaterial(mg,nil,tp)
end
function s.target(e,tp,chk,bottom)
    local mg=s.group(e,tp,bottom)
    if chk==0 then return Duel.IsExistingMatchingCard(s.fusion,tp,LOCATION_EXTRA,0,1,nil,e,tp,mg,bottom) end
    Duel.SetOperationInfo(0,CATEGORY_SPECIAL_SUMMON,nil,1,tp,LOCATION_EXTRA)
end
function s.target1(e,tp,eg,ep,ev,re,r,rp,chk) return s.target(e,tp,chk,false) end
function s.target2(e,tp,eg,ep,ev,re,r,rp,chk) return s.target(e,tp,chk,true) end
function s.operation1(e,tp,eg,ep,ev,re,r,rp)
    if not e:GetHandler():IsRelateToEffect(e) then return end
    s.summon(e,tp,false)
end
function s.operation2(e,tp,eg,ep,ev,re,r,rp)
    -- This card was returned as cost: it need not remain related to the Chain.
    s.summon(e,tp,true)
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
