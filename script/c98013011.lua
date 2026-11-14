-- Catastrophe Counterattack: Tachyon Transmigration-style chain sweep.
local s,id=GetID()
local SET_CAT=0xfcb
function s.initial_effect(c)
    local e1=Effect.CreateEffect(c)
    e1:SetDescription(aux.Stringid(id,0))
    e1:SetCategory(CATEGORY_NEGATE+CATEGORY_TODECK)
    e1:SetType(EFFECT_TYPE_ACTIVATE)
    e1:SetCode(EVENT_CHAINING)
    e1:SetCondition(s.negcon)
    e1:SetTarget(s.negtg)
    e1:SetOperation(s.negop)
    c:RegisterEffect(e1)
    local hand=Effect.CreateEffect(c)
    hand:SetType(EFFECT_TYPE_SINGLE)
    hand:SetCode(EFFECT_TRAP_ACT_IN_HAND)
    hand:SetCondition(function(e) return s.hasarchetype(e:GetHandlerPlayer()) end)
    c:RegisterEffect(hand)
    local e2=Effect.CreateEffect(c)
    e2:SetDescription(aux.Stringid(id,1))
    e2:SetType(EFFECT_TYPE_IGNITION)
    e2:SetRange(LOCATION_GRAVE+LOCATION_REMOVED)
    e2:SetCountLimit(1,198013112)
    e2:SetCondition(s.setcon)
    e2:SetTarget(s.settg)
    e2:SetOperation(s.setop)
    c:RegisterEffect(e2)
end
function s.catfield(c)
    return c:IsSetCard(SET_CAT) and (c:IsLocation(LOCATION_GRAVE) or c:IsFaceup())
end
function s.hasarchetype(tp)
    return Duel.IsExistingMatchingCard(s.catfield,tp,LOCATION_ONFIELD+LOCATION_GRAVE+LOCATION_REMOVED,0,1,nil)
end
function s.canrespond(te,player,tp)
    return player==1-tp and (te:IsActiveType(TYPE_MONSTER) or te:IsHasType(EFFECT_TYPE_ACTIVATE))
end
function s.negcon(e,tp,eg,ep,ev,re,r,rp)
    if ev<1 or not s.hasarchetype(tp) then return false end
    for link=1,ev do
        local effect,player=Duel.GetChainInfo(link,CHAININFO_TRIGGERING_EFFECT,CHAININFO_TRIGGERING_PLAYER)
        if s.canrespond(effect,player,tp) and Duel.IsChainNegatable(link) then return true end
    end
    return false
end
function s.negtg(e,tp,eg,ep,ev,re,r,rp,chk)
    if chk==0 then return true end
    local negated=Group.CreateGroup()
    local returning=Group.CreateGroup()
    for link=1,ev do
        local effect,player=Duel.GetChainInfo(link,CHAININFO_TRIGGERING_EFFECT,CHAININFO_TRIGGERING_PLAYER)
        if s.canrespond(effect,player,tp) and Duel.IsChainNegatable(link) then
            local card=effect:GetHandler()
            negated:AddCard(card)
            if card:IsOnField() and card:IsRelateToEffect(effect) then returning:AddCard(card) end
        end
    end
    -- Register relation without declaring targeting, as in official Transmigration.
    Duel.SetTargetCard(returning)
    Duel.SetOperationInfo(0,CATEGORY_NEGATE,negated,negated:GetCount(),0,0)
    Duel.SetOperationInfo(0,CATEGORY_TODECK,returning,returning:GetCount(),0,0)
end
function s.negop(e,tp,eg,ep,ev,re,r,rp)
    local returning=Group.CreateGroup()
    for link=1,ev do
        local effect,player=Duel.GetChainInfo(link,CHAININFO_TRIGGERING_EFFECT,CHAININFO_TRIGGERING_PLAYER)
        if s.canrespond(effect,player,tp) and Duel.NegateActivation(link) then
            local card=effect:GetHandler()
            if card:IsRelateToEffect(e) and card:IsRelateToEffect(effect) then returning:AddCard(card) end
        end
    end
    if returning:GetCount()>0 then Duel.SendtoDeck(returning,nil,SEQ_DECKSHUFFLE,REASON_EFFECT,tp,true) end
end

function s.setcon(e)
    local c=e:GetHandler()
    return not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup()
end
function s.settg(e,tp,eg,ep,ev,re,r,rp,chk)
    if chk==0 then return Duel.GetLocationCount(tp,LOCATION_SZONE)>0 and e:GetHandler():IsSSetable() end
end
function s.setop(e,tp,eg,ep,ev,re,r,rp)
    local c=e:GetHandler()
    if c:IsRelateToEffect(e) and Duel.GetLocationCount(tp,LOCATION_SZONE)>0 and c:IsSSetable() then
        Duel.SSet(tp,c)
    end
end
