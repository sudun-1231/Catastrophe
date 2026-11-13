-- CATastrophe alpha: partial implementation only. See IMPLEMENTATION_STATUS.md.
local s,id=GetID()
local SET_CAT=0xfcb
local function catfilter(c)
    return c:IsSetCard(SET_CAT) and c:IsAbleToHand()
end
local function catsearchtg(e,tp,eg,ep,ev,re,r,rp,chk)
    if chk==0 then return Duel.IsExistingMatchingCard(catfilter,tp,LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED,0,1,nil) end
    Duel.SetOperationInfo(0,CATEGORY_TOHAND,nil,1,tp,LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED)
end
local function catsearchop(e,tp,eg,ep,ev,re,r,rp)
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_ATOHAND)
    local g=Duel.SelectMatchingCard(tp,catfilter,tp,LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED,0,1,1,nil)
    if #g>0 then Duel.SendtoHand(g,nil,REASON_EFFECT) Duel.ConfirmCards(1-tp,g) end
end

function s.initial_effect(c)
    c:EnableReviveLimit()
    -- TODO: register variable-count Fusion materials:
    -- 1 Catastrophe monster + at least 1 additional monster.
    -- An incorrect generic 2-material recipe would change the original design.
    -- Golem effect 1: forced trigger on successful Special Summon
    local e1=Effect.CreateEffect(c)
    e1:SetCategory(CATEGORY_DESTROY)
    e1:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_F)
    e1:SetCode(EVENT_SPSUMMON_SUCCESS)
    e1:SetCountLimit(1,id)
    e1:SetTarget(s.destg)
    e1:SetOperation(s.desop)
    c:RegisterEffect(e1)
    -- Effect 2: when THIS card goes to GY or is banished, return it and recover a card.
    local e2=Effect.CreateEffect(c)
    e2:SetCategory(CATEGORY_TODECK|CATEGORY_TOHAND)
    e2:SetType(EFFECT_TYPE_SINGLE|EFFECT_TYPE_TRIGGER_O)
    e2:SetProperty(EFFECT_FLAG_DELAY)
    e2:SetCode(EVENT_TO_GRAVE)
    e2:SetCountLimit(1,{id,2})
    e2:SetTarget(s.rectg)
    e2:SetOperation(s.recop)
    c:RegisterEffect(e2)
    local e3=e2:Clone()
    e3:SetCode(EVENT_REMOVE)
    c:RegisterEffect(e3)
end

function s.desfilter(c)
    return c:IsDestructable()
end
function s.destg(e,tp,eg,ep,ev,re,r,rp,chk)
    if chk==0 then return true end
    local g=Duel.GetMatchingGroup(s.desfilter,tp,0,LOCATION_ONFIELD+LOCATION_HAND,nil)
    Duel.SetOperationInfo(0,CATEGORY_DESTROY,g,#g,0,0)
end
function s.desop(e,tp,eg,ep,ev,re,r,rp)
    local g=Duel.GetMatchingGroup(s.desfilter,tp,0,LOCATION_ONFIELD+LOCATION_HAND,nil)
    if #g>0 then Duel.Destroy(g,REASON_EFFECT) end
end

function s.recfilter(c,ex)
    return c~=ex and c:IsAbleToHand() and (not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup())
end
function s.rectg(e,tp,eg,ep,ev,re,r,rp,chk)
    local c=e:GetHandler()
    if chk==0 then
        return c:IsAbleToDeck() and Duel.IsExistingMatchingCard(s.recfilter,tp,
            LOCATION_GRAVE|LOCATION_REMOVED,0,1,c,c)
    end
    Duel.SetOperationInfo(0,CATEGORY_TODECK,c,1,tp,0)
    Duel.SetOperationInfo(0,CATEGORY_TOHAND,nil,1,tp,LOCATION_GRAVE|LOCATION_REMOVED)
end
function s.recop(e,tp,eg,ep,ev,re,r,rp)
    local c=e:GetHandler()
    if not c:IsRelateToEffect(e) or not c:IsAbleToDeck() then return end
    if Duel.SendtoDeck(c,nil,SEQ_DECKSHUFFLE,REASON_EFFECT)==0 then return end
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_ATOHAND)
    local g=Duel.SelectMatchingCard(tp,s.recfilter,tp,LOCATION_GRAVE|LOCATION_REMOVED,0,1,1,nil,c)
    if #g>0 then
        Duel.SendtoHand(g,nil,REASON_EFFECT)
        Duel.ConfirmCards(1-tp,g)
    end
end
