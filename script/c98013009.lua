-- Catastrophe detects Danger: targeting response and existing recovery.
local s,id=GetID()
local SET_CAT=0xfcb
function s.initial_effect(c)
    local e1=Effect.CreateEffect(c)
    e1:SetDescription(aux.Stringid(id,0))
    e1:SetCategory(CATEGORY_DESTROY+CATEGORY_TOHAND)
    e1:SetType(EFFECT_TYPE_ACTIVATE)
    e1:SetCode(EVENT_CHAINING)
    e1:SetCountLimit(1,198013090)
    e1:SetCondition(s.protectcondition)
    e1:SetTarget(s.protecttarget)
    e1:SetOperation(s.protectoperation)
    c:RegisterEffect(e1)
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

-- Record the opponent's original targets without making this effect target.
function s.protectedfilter(c,e,tp)
    return c~=e:GetHandler() and c:IsControler(tp) and c:IsOnField()
        and c:IsDestructable(e) and not c:IsImmuneToEffect(e)
end
function s.searchfilter(c)
    return c:IsSetCard(SET_CAT) and c:IsAbleToHand()
        and (not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup())
end
function s.protectcondition(e,tp,eg,ep,ev,re,r,rp)
    if rp~=1-tp or not re:IsHasProperty(EFFECT_FLAG_CARD_TARGET) then return false end
    local g=Duel.GetChainInfo(ev,CHAININFO_TARGET_CARDS)
    return g and g:IsExists(s.protectedfilter,1,nil,e,tp)
end
function s.protecttarget(e,tp,eg,ep,ev,re,r,rp,chk)
    if chk==0 then return Duel.IsExistingMatchingCard(aux.NecroValleyFilter(s.searchfilter),tp,
        LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED,0,1,nil) end
    local g=Duel.GetChainInfo(ev,CHAININFO_TARGET_CARDS):Filter(s.protectedfilter,nil,e,tp)
    Duel.SetTargetCard(g)
    Duel.SetOperationInfo(0,CATEGORY_DESTROY,g,1,0,0)
    Duel.SetOperationInfo(0,CATEGORY_TOHAND,nil,1,tp,LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED)
end
function s.relatedprotected(c,e,tp)
    return c:IsRelateToEffect(e) and s.protectedfilter(c,e,tp)
end
function s.protectoperation(e,tp)
    local original=Duel.GetChainInfo(0,CHAININFO_TARGET_CARDS)
    if not original then return end
    local g=original:Filter(s.relatedprotected,nil,e,tp)
    if g:GetCount()==0 then return end
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_DESTROY)
    local chosen=g:Select(tp,1,1,nil)
    if Duel.Destroy(chosen,REASON_EFFECT)==0 then return end
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_ATOHAND)
    local searched=Duel.SelectMatchingCard(tp,aux.NecroValleyFilter(s.searchfilter),tp,
        LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED,0,1,1,nil)
    if searched:GetCount()>0 and Duel.SendtoHand(searched,nil,REASON_EFFECT)>0 then
        Duel.ConfirmCards(1-tp,searched)
    end
end
