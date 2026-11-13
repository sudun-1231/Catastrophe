-- Alpha 0.13: effect 2 implemented; effect 1 remains unimplemented.
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
    local e2=Effect.CreateEffect(c)
    e2:SetDescription(aux.Stringid(id,1))
    e2:SetCategory(CATEGORY_DRAW)
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
