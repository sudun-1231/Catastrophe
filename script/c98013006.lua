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
    local e1=Effect.CreateEffect(c)
    e1:SetCategory(CATEGORY_TOHAND)
    e1:SetType(EFFECT_TYPE_ACTIVATE)
    e1:SetCode(EVENT_FREE_CHAIN)
    e1:SetCountLimit(1,id)
    e1:SetTarget(catsearchtg)
    e1:SetOperation(catsearchop)
    c:RegisterEffect(e1)
    local e2=Effect.CreateEffect(c)
    e2:SetDescription(aux.Stringid(id,1))
    e2:SetCategory(CATEGORY_TOHAND)
    e2:SetType(EFFECT_TYPE_IGNITION)
    e2:SetRange(LOCATION_GRAVE+LOCATION_REMOVED)
    e2:SetCountLimit(1,198013000+(id-98013000)*10+1)
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
-- Return 1 to 4 other cards as cost; face-down banished cards are generic cards too.
function s.recoverfilter(c)
    return c:IsAbleToDeckAsCost()
end
function s.recovercost(e,tp,eg,ep,ev,re,r,rp,chk)
    local c=e:GetHandler()
    local loc=LOCATION_GRAVE+LOCATION_REMOVED
    if chk==0 then return Duel.IsExistingMatchingCard(s.recoverfilter,tp,loc,loc,1,c) end
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_TODECK)
    local g=Duel.SelectMatchingCard(tp,s.recoverfilter,tp,loc,loc,1,4,c)
    local count=g:GetCount()
    e:SetLabel(0)
    local moved
    if aux.PlaceCardsOnDeckBottom then
        moved=aux.PlaceCardsOnDeckBottom(tp,g,REASON_COST)
    else
        moved=Duel.SendtoDeck(g,nil,SEQ_DECKBOTTOM,REASON_COST)
        local returned=Duel.GetOperatedGroup():Filter(Card.IsLocation,nil,LOCATION_DECK)
        local own=returned:FilterCount(Card.IsControler,nil,tp)
        if own>0 then Duel.SortDeckbottom(tp,tp,own) end
        if returned:GetCount()>own then Duel.SortDeckbottom(tp,1-tp,returned:GetCount()-own) end
    end
    if count>0 and moved==count then e:SetLabel(1) end
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
