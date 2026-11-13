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
    Fusion.AddProcMixN(c,true,true,s.matfilter,2)
    local e1=Effect.CreateEffect(c)
    e1:SetCategory(CATEGORY_NEGATE+CATEGORY_DESTROY)
    e1:SetType(EFFECT_TYPE_QUICK_O)
    e1:SetCode(EVENT_CHAINING)
    e1:SetRange(LOCATION_MZONE)
    e1:SetCountLimit(1,id)
    e1:SetCondition(s.negcon)
    e1:SetTarget(s.negtg)
    e1:SetOperation(s.negop)
    c:RegisterEffect(e1)
    s.fuse_register(c,id)
end

function s.negcon(e,tp,eg,ep,ev,re,r,rp)
    return Duel.IsChainNegatable(ev)
end
function s.negtg(e,tp,eg,ep,ev,re,r,rp,chk)
    if chk==0 then return true end
    Duel.SetOperationInfo(0,CATEGORY_NEGATE,eg,1,0,0)
    if re:GetHandler():IsRelateToEffect(re) then Duel.SetOperationInfo(0,CATEGORY_DESTROY,eg,1,0,0) end
end
function s.negop(e,tp,eg,ep,ev,re,r,rp)
    if Duel.NegateActivation(ev) and re:GetHandler():IsRelateToEffect(re) then
        Duel.Destroy(eg,REASON_EFFECT)
    end
end

-- Prototype bottom-deck Fusion procedure modeled on Project Ignis's Merrli helper.
-- Extra zone extension: face-up banished monsters, in addition to hand/field/GY.
function s.fuse_extra(e,tp,mg)
    return Duel.GetMatchingGroup(function(c)
        return c:IsMonster() and c:IsAbleToDeck()
            and (c:IsLocation(LOCATION_GRAVE) or c:IsFaceup())
    end,tp,LOCATION_GRAVE|LOCATION_REMOVED,0,nil)
end
function s.fuse_tg(e,tp,eg,ep,ev,re,r,rp,chk)
    if chk==0 then return true end
    Duel.SetOperationInfo(0,CATEGORY_TODECK,e:GetHandler(),1,tp,LOCATION_HAND|LOCATION_MZONE|LOCATION_GRAVE|LOCATION_REMOVED)
end
function s.fuse_bottom(e,tc,tp,sg)
    local gg=sg:Filter(Card.IsLocation,nil,LOCATION_HAND|LOCATION_GRAVE|LOCATION_REMOVED)
    if #gg>0 then Duel.HintSelection(gg,true) end
    local fg=sg:Filter(Card.IsFacedown,nil)
    if #fg>0 then Duel.ConfirmCards(1-tp,fg) end
    Duel.SendtoDeck(sg,nil,SEQ_DECKBOTTOM,REASON_EFFECT|REASON_MATERIAL|REASON_FUSION)
    local dg=Duel.GetOperatedGroup():Filter(Card.IsLocation,nil,LOCATION_DECK)
    local ct=dg:FilterCount(Card.IsControler,nil,tp)
    if ct>0 then Duel.SortDeckbottom(tp,tp,ct) end
    if #dg>ct then Duel.SortDeckbottom(tp,1-tp,#dg-ct) end
    sg:Clear()
end
function s.fuse_register(c,code)
    local params={matfilter=Card.IsAbleToDeck,extrafil=s.fuse_extra,extraop=s.fuse_bottom,
        gc=Fusion.ForcedHandler,extratg=s.fuse_tg}
    for _,event in ipairs({EVENT_TO_GRAVE,EVENT_REMOVE}) do
        local e=Effect.CreateEffect(c)
        e:SetCategory(CATEGORY_SPECIAL_SUMMON|CATEGORY_FUSION_SUMMON)
        e:SetType(EFFECT_TYPE_SINGLE|EFFECT_TYPE_TRIGGER_O)
        e:SetProperty(EFFECT_FLAG_DELAY)
        e:SetCode(event)
        e:SetCountLimit(1,{code,3})
        e:SetTarget(Fusion.SummonEffTG(params))
        e:SetOperation(Fusion.SummonEffOP(params))
        c:RegisterEffect(e)
    end
end

function s.matfilter(c)
    return c:IsSetCard(0xfcb)
end
