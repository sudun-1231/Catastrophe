-- Alpha 0.16: recovery effect 2. Effect 1 remains unimplemented.
local s,id=GetID()
function s.initial_effect(c)
    local e2=Effect.CreateEffect(c)
    e2:SetDescription(aux.Stringid(id,1))
    e2:SetCategory(CATEGORY_TOHAND)
    e2:SetType(EFFECT_TYPE_IGNITION)
    e2:SetRange(LOCATION_GRAVE+LOCATION_REMOVED)
    e2:SetCountLimit(1,198013091)
    e2:SetCondition(s.recovercondition)
    e2:SetCost(s.recovercost)
    e2:SetTarget(s.recovertarget)
    e2:SetOperation(s.recoveroperation)
    c:RegisterEffect(e2)
end
function s.recovercondition(e)
    local c=e:GetHandler()
    return not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup()
end
function s.disablefilter(c,e)
    return c:IsFaceup() and not c:IsDisabled() and c:IsCanBeDisabledByEffect(e,false)
end
function s.recovercost(e,tp,eg,ep,ev,re,r,rp,chk)
    if chk==0 then return Duel.IsExistingMatchingCard(s.disablefilter,tp,LOCATION_ONFIELD,LOCATION_ONFIELD,1,nil,e) end
    e:SetLabel(0)
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_FACEUP)
    local tc=Duel.SelectMatchingCard(tp,s.disablefilter,tp,LOCATION_ONFIELD,LOCATION_ONFIELD,1,1,nil,e):GetFirst()
    if not tc then return end
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
    Duel.AdjustInstantly(tc)
    if tc:IsDisabled() then e:SetLabel(1) end
end
function s.recovertarget(e,tp,eg,ep,ev,re,r,rp,chk)
    if chk==0 then return e:GetHandler():IsAbleToHand() end
    Duel.SetOperationInfo(0,CATEGORY_TOHAND,e:GetHandler(),1,0,0)
end
function s.recoveroperation(e,tp)
    local c=e:GetHandler()
    if e:GetLabel()~=1 or not c:IsRelateToEffect(e) or not c:IsAbleToHand() then return end
    if Duel.SendtoHand(c,nil,REASON_EFFECT)>0 then Duel.ConfirmCards(1-tp,c) end
end
