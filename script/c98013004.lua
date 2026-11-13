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
    local e2=Effect.CreateEffect(c)
    e2:SetCategory(CATEGORY_TOHAND)
    e2:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
    e2:SetProperty(EFFECT_FLAG_DELAY)
    e2:SetCode(EVENT_SUMMON_SUCCESS)
    e2:SetCountLimit(1,{id,1})
    e2:SetTarget(catsearchtg)
    e2:SetOperation(catsearchop)
    c:RegisterEffect(e2)
    local es=e2:Clone()
    es:SetCode(EVENT_SPSUMMON_SUCCESS)
    c:RegisterEffect(es)
    s.fuse_register(c,id)
end

-- Garura-style optional trigger + Merrli-style Fusion resolution.
-- The trigger is NOT limited to cards sent by effects: it works for any EVENT_TO_GRAVE.
function s.fus_matfilter(c)
    return c:IsMonster() and c:IsAbleToDeck()
        and (not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup())
end
function s.fus_extramat(e,tp,mg)
    return Duel.GetMatchingGroup(s.fus_matfilter,tp,LOCATION_GRAVE|LOCATION_REMOVED,0,nil)
end
function s.fus_extratg(e,tp,eg,ep,ev,re,r,rp,chk)
    if chk==0 then return true end
    Duel.SetOperationInfo(0,CATEGORY_TODECK,e:GetHandler(),1,tp,
        LOCATION_HAND|LOCATION_MZONE|LOCATION_GRAVE|LOCATION_REMOVED)
end
function s.fus_extraop(e,fc,tp,sg)
    local reveal=sg:Filter(Card.IsLocation,nil,LOCATION_HAND|LOCATION_GRAVE|LOCATION_REMOVED)
    if #reveal>0 then Duel.HintSelection(reveal,true) end
    local facedown=sg:Filter(Card.IsFacedown,nil)
    if #facedown>0 then Duel.ConfirmCards(1-tp,facedown) end
    Duel.SendtoDeck(sg,nil,SEQ_DECKBOTTOM,REASON_EFFECT|REASON_MATERIAL|REASON_FUSION)
    local dg=Duel.GetOperatedGroup():Filter(Card.IsLocation,nil,LOCATION_DECK)
    local ct=dg:FilterCount(Card.IsControler,nil,tp)
    if ct>0 then Duel.SortDeckbottom(tp,tp,ct) end
    if #dg>ct then Duel.SortDeckbottom(tp,1-tp,#dg-ct) end
    sg:Clear()
end
function s.fusparams()
    return {
        matfilter=Card.IsAbleToDeck,
        extrafil=s.fus_extramat,
        extraop=s.fus_extraop,
        -- Mandatory at activation and resolution; do not replace with nil.
        gc=Fusion.ForcedHandler,
        extratg=s.fus_extratg
    }
end
function s.fuse_register(c,code)
    local params=s.fusparams()
    -- Garura, Wings of Resonant Life: optional delayed single trigger on EVENT_TO_GRAVE.
    local e3=Effect.CreateEffect(c)
    e3:SetDescription(aux.Stringid(code,2))
    e3:SetCategory(CATEGORY_TODECK|CATEGORY_SPECIAL_SUMMON|CATEGORY_FUSION_SUMMON)
    e3:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
    e3:SetProperty(EFFECT_FLAG_DELAY)
    e3:SetCode(EVENT_TO_GRAVE)
    -- The GY and banishment clones share this card-specific limit.
    e3:SetCountLimit(1,{code,2})
    e3:SetTarget(Fusion.SummonEffTG(params))
    e3:SetOperation(Fusion.SummonEffOP(params))
    c:RegisterEffect(e3)
    local e4=e3:Clone()
    e4:SetCode(EVENT_REMOVE)
    e4:SetCondition(function(e) return e:GetHandler():IsFaceup() end)
    c:RegisterEffect(e4)
end
