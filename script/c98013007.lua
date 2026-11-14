-- Alpha 0.17: Quick-Play Threshold, with search cost and draw recovery.
local s,id=GetID()
local SET_CAT=0xfcb
function s.initial_effect(c)
    local e1=Effect.CreateEffect(c)
    e1:SetDescription(aux.Stringid(id,0))
    e1:SetCategory(CATEGORY_REMOVE+CATEGORY_HANDES)
    e1:SetType(EFFECT_TYPE_ACTIVATE)
    e1:SetCode(EVENT_FREE_CHAIN)
    e1:SetHintTiming(0,TIMINGS_CHECK_MONSTER+TIMING_END_PHASE)
    e1:SetCountLimit(1,id)
    e1:SetCost(s.activatecost)
    e1:SetTarget(s.activatetarget)
    e1:SetOperation(s.activateoperation)
    c:RegisterEffect(e1)
    local e2=Effect.CreateEffect(c)
    e2:SetDescription(aux.Stringid(id,1))
    e2:SetCategory(CATEGORY_DRAW)
    e2:SetType(EFFECT_TYPE_IGNITION)
    e2:SetRange(LOCATION_GRAVE+LOCATION_REMOVED)
    e2:SetCountLimit(1,198013071)
    e2:SetCondition(s.recovercondition)
    e2:SetCost(s.recovercost)
    e2:SetTarget(s.recovertarget)
    e2:SetOperation(s.recoveroperation)
    c:RegisterEffect(e2)
end
function s.searchcostfilter(c)
    return c:IsSetCard(SET_CAT) and c:IsAbleToHandAsCost()
        and (not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup())
end
function s.activatecost(e,tp,eg,ep,ev,re,r,rp,chk)
    local filter=aux.NecroValleyFilter(s.searchcostfilter)
    if chk==0 then return Duel.IsExistingMatchingCard(filter,tp,LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED,0,1,nil) end
    e:SetLabel(0)
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_ATOHAND)
    local g=Duel.SelectMatchingCard(tp,filter,tp,LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED,0,1,1,nil)
    local selected=g:GetFirst()
    if selected and Duel.SendtoHand(g,nil,REASON_COST)>0 and selected:IsLocation(LOCATION_HAND) then
        Duel.ConfirmCards(1-tp,g)
        e:SetLabel(1)
    end
end
function s.banishfilter(c,e)
    return c:IsAbleToRemove() and not c:IsImmuneToEffect(e)
end
function s.activatetarget(e,tp,eg,ep,ev,re,r,rp,chk)
    if chk==0 then return Duel.IsExistingMatchingCard(s.banishfilter,tp,LOCATION_ONFIELD,LOCATION_ONFIELD,1,nil,e) end
    Duel.SetOperationInfo(0,CATEGORY_REMOVE,nil,1,PLAYER_ALL,LOCATION_ONFIELD)
end
function s.discardfilter(c)
    return c:IsDiscardable(REASON_EFFECT)
end
function s.activateoperation(e,tp)
    if e:GetLabel()~=1 then return end
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_REMOVE)
    local g=Duel.SelectMatchingCard(tp,s.banishfilter,tp,LOCATION_ONFIELD,LOCATION_ONFIELD,1,1,nil,e)
    if g:GetCount()==0 or Duel.Remove(g,POS_FACEUP,REASON_EFFECT)==0 then return end
    local own=Duel.IsExistingMatchingCard(s.discardfilter,tp,LOCATION_HAND,0,1,nil)
    local other=Duel.IsExistingMatchingCard(s.discardfilter,tp,0,LOCATION_HAND,1,nil)
    if not (own or other) or not Duel.SelectYesNo(tp,aux.Stringid(id,4)) then return end
    local opponent=not own
    if own and other then opponent=Duel.SelectOption(tp,aux.Stringid(id,2),aux.Stringid(id,3))==1 end
    if opponent then Duel.ConfirmCards(tp,Duel.GetFieldGroup(tp,0,LOCATION_HAND)) end
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_DISCARD)
    local discarded=Duel.SelectMatchingCard(tp,s.discardfilter,tp,opponent and 0 or LOCATION_HAND,
        opponent and LOCATION_HAND or 0,1,1,nil)
    if discarded:GetCount()>0 then Duel.SendtoGrave(discarded,REASON_EFFECT+REASON_DISCARD) end
end

function s.recovercondition(e)
    local c=e:GetHandler()
    return not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup()
end
function s.recovercost(e,tp,eg,ep,ev,re,r,rp,chk)
    local c=e:GetHandler()
    if chk==0 then return c:IsAbleToDeckAsCost() end
    e:SetLabel(0)
    if Duel.SendtoDeck(c,nil,SEQ_DECKSHUFFLE,REASON_COST)>0 then e:SetLabel(1) end
end
function s.recovertarget(e,tp,eg,ep,ev,re,r,rp,chk)
    if chk==0 then return Duel.IsPlayerCanDraw(tp,2) end
    Duel.SetOperationInfo(0,CATEGORY_DRAW,nil,0,tp,2)
end
function s.recoveroperation(e,tp)
    -- Moving the spell as cost must not invalidate this draw effect.
    if e:GetLabel()==1 then Duel.Draw(tp,2,REASON_EFFECT) end
end
