-- Catastrophe Alpha 0.12: updated summon follow-up and effect 2.
local s,id=GetID()
local SET_CAT=0xfcb
function s.initial_effect(c)
    local e1=Effect.CreateEffect(c)
    e1:SetDescription(aux.Stringid(id,0))
    e1:SetCategory(CATEGORY_DESTROY+CATEGORY_SPECIAL_SUMMON+CATEGORY_TOHAND)
    e1:SetType(EFFECT_TYPE_IGNITION)
    e1:SetRange(LOCATION_HAND)
    e1:SetCountLimit(1,id)
    e1:SetTarget(s.sptarget)
    e1:SetOperation(s.spoperation)
    c:RegisterEffect(e1)
    local e2=Effect.CreateEffect(c)
    e2:SetDescription(aux.Stringid(id,1))
    e2:SetType(EFFECT_TYPE_IGNITION)
    e2:SetRange(LOCATION_MZONE)
    e2:SetCountLimit(1,198013000+(id-98013000)*10+1)
    e2:SetProperty(EFFECT_FLAG_CARD_TARGET)
    e2:SetTarget(s.effect2target)
    e2:SetOperation(s.effect2operation)
    c:RegisterEffect(e2)
    s.fuse_register(c,id)
end
function s.deckdestroy(c)
    return c:IsSetCard(SET_CAT) and c:IsDestructable()
end
function s.sptarget(e,tp,eg,ep,ev,re,r,rp,chk)
    local c=e:GetHandler()
    if chk==0 then return Duel.GetLocationCount(tp,LOCATION_MZONE)>0
        and c:IsCanBeSpecialSummoned(e,0,tp,false,false)
        and Duel.IsExistingMatchingCard(s.deckdestroy,tp,LOCATION_DECK,0,1,nil) end
    Duel.SetOperationInfo(0,CATEGORY_DESTROY,nil,1,tp,LOCATION_DECK)
    Duel.SetOperationInfo(0,CATEGORY_SPECIAL_SUMMON,c,1,0,0)
end
function s.spoperation(e,tp)
    local c=e:GetHandler()
    if not c:IsRelateToEffect(e) or not c:IsLocation(LOCATION_HAND) then return end
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_DESTROY)
    local g=Duel.SelectMatchingCard(tp,s.deckdestroy,tp,LOCATION_DECK,0,1,1,nil)
    if g:GetCount()==0 or Duel.Destroy(g,REASON_EFFECT)==0 then return end
    if Duel.GetLocationCount(tp,LOCATION_MZONE)<=0 or not c:IsRelateToEffect(e) then return end
    if Duel.SpecialSummon(c,0,tp,tp,false,false,POS_FACEUP)==0 then return end
    s.followup(e,tp)
end
function s.followfilter(c)
    return c:IsSetCard(SET_CAT) and c:IsAbleToHand()
        and (not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup())
end
function s.followup(e,tp)
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_ATOHAND)
    local g=Duel.SelectMatchingCard(tp,aux.NecroValleyFilter(s.followfilter),tp,
        LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED,0,1,1,nil)
    if g:GetCount()>0 then Duel.SendtoHand(g,nil,REASON_EFFECT); Duel.ConfirmCards(1-tp,g) end
end

-- Direct Fusion procedure: compatible with MDPro3's legacy script library.
function s.fus_matfilter(c,e)
    return c:IsType(TYPE_MONSTER) and c:IsCanBeFusionMaterial()
        and c:IsAbleToDeck() and not c:IsImmuneToEffect(e)
        and (not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup())
end
function s.fus_group(e,tp)
    return Duel.GetMatchingGroup(aux.NecroValleyFilter(s.fus_matfilter),tp,
        LOCATION_HAND+LOCATION_MZONE+LOCATION_GRAVE+LOCATION_REMOVED,0,nil,e)
end
function s.fus_filter(c,e,tp,mg,mandatory)
    return c:IsType(TYPE_FUSION)
        and c:IsCanBeSpecialSummoned(e,SUMMON_TYPE_FUSION,tp,false,false)
        and c:CheckFusionMaterial(mg,mandatory,tp)
end
function s.fus_target(e,tp,eg,ep,ev,re,r,rp,chk)
    local mg=s.fus_group(e,tp)
    if chk==0 then return Duel.IsExistingMatchingCard(s.fus_filter,tp,LOCATION_EXTRA,0,1,nil,e,tp,mg,nil) end
    Duel.SetOperationInfo(0,CATEGORY_SPECIAL_SUMMON,nil,1,tp,LOCATION_EXTRA)
    Duel.SetOperationInfo(0,CATEGORY_TODECK,nil,0,tp,LOCATION_HAND+LOCATION_MZONE+LOCATION_GRAVE+LOCATION_REMOVED)
end
function s.fus_operation(e,tp,eg,ep,ev,re,r,rp)
    local mg=s.fus_group(e,tp)
    local candidates=Duel.GetMatchingGroup(s.fus_filter,tp,LOCATION_EXTRA,0,nil,e,tp,mg,nil)
    if candidates:GetCount()==0 then return end
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_SPSUMMON)
    local fc=candidates:Select(tp,1,1,nil):GetFirst()
    if not fc then return end
    local materials=Duel.SelectFusionMaterial(tp,fc,mg,nil,tp)
    if materials:GetCount()==0 then return end
    fc:SetMaterial(materials)
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
    Duel.BreakEffect()
    if Duel.SpecialSummon(fc,SUMMON_TYPE_FUSION,tp,tp,false,false,POS_FACEUP)>0 then fc:CompleteProcedure() end
end
function s.fuse_register(c,code)
    local e=Effect.CreateEffect(c)
    e:SetDescription(aux.Stringid(code,2))
    e:SetCategory(CATEGORY_TODECK+CATEGORY_SPECIAL_SUMMON+CATEGORY_FUSION_SUMMON)
    e:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
    e:SetProperty(EFFECT_FLAG_DELAY)
    e:SetCode(EVENT_TO_GRAVE)
    -- Numeric private key: old MDPro3 cores do not accept {id,index}.
    e:SetCountLimit(1,198013000+(code-98013000)*10+2)
    e:SetTarget(s.fus_target)
    e:SetOperation(s.fus_operation)
    c:RegisterEffect(e)
    local removed=e:Clone()
    removed:SetCode(EVENT_REMOVE)
    removed:SetCondition(function(e) return e:GetHandler():IsFaceup() end)
    c:RegisterEffect(removed)
end

function s.effect2filter(c)
    return c:IsFaceup() and not c:IsDisabled()
end
function s.effect2target(e,tp,eg,ep,ev,re,r,rp,chk,chkc)
    if chkc then return chkc:IsOnField() and s.effect2filter(chkc) end
    if chk==0 then return Duel.IsExistingTarget(s.effect2filter,tp,LOCATION_ONFIELD,LOCATION_ONFIELD,1,nil) end
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_FACEUP)
    Duel.SelectTarget(tp,s.effect2filter,tp,LOCATION_ONFIELD,LOCATION_ONFIELD,1,1,nil)
end
function s.effect2operation(e)
    local tc=Duel.GetFirstTarget()
    if not tc or not tc:IsFaceup() or not tc:IsRelateToEffect(e) then return end
    Duel.NegateRelatedChain(tc,RESET_TURN_SET)
    local disable=Effect.CreateEffect(e:GetHandler())
    disable:SetType(EFFECT_TYPE_SINGLE)
    disable:SetCode(EFFECT_DISABLE)
    disable:SetReset(RESET_EVENT+RESETS_STANDARD)
    tc:RegisterEffect(disable)
    local effects=disable:Clone()
    effects:SetCode(EFFECT_DISABLE_EFFECT)
    tc:RegisterEffect(effects)
    if tc:IsType(TYPE_TRAPMONSTER) then
        local trap=disable:Clone()
        trap:SetCode(EFFECT_DISABLE_TRAPMONSTER)
        tc:RegisterEffect(trap)
    end
end
