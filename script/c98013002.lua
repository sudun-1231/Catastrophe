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
    s.register_special(c)
    -- Supplemental action when Special Summoned by the custom procedure
    local ep=Effect.CreateEffect(c)
    ep:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
    ep:SetProperty(EFFECT_FLAG_DELAY)
    ep:SetCode(EVENT_SPSUMMON_SUCCESS)
    ep:SetCondition(s.postcon)
    ep:SetTarget(s.posttg)
    ep:SetOperation(s.postop)
    c:RegisterEffect(ep)
    local e2=Effect.CreateEffect(c)
    e2:SetCategory(CATEGORY_TOHAND)
    e2:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
    e2:SetProperty(EFFECT_FLAG_DELAY)
    e2:SetCode(EVENT_SUMMON_SUCCESS)
    e2:SetCountLimit(1,198013000+(id-98013000)*10+1)
    e2:SetTarget(catsearchtg)
    e2:SetOperation(catsearchop)
    c:RegisterEffect(e2)
    local es=e2:Clone()
    es:SetCode(EVENT_SPSUMMON_SUCCESS)
    c:RegisterEffect(es)
    s.fuse_register(c,id)
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
    local c=e:GetHandler()
    local mg=s.fus_group(e,tp)
    if chk==0 then return mg:IsContains(c)
        and Duel.IsExistingMatchingCard(s.fus_filter,tp,LOCATION_EXTRA,0,1,nil,e,tp,mg,c) end
    Duel.SetOperationInfo(0,CATEGORY_SPECIAL_SUMMON,nil,1,tp,LOCATION_EXTRA)
    Duel.SetOperationInfo(0,CATEGORY_TODECK,c,1,tp,0)
end
function s.fus_operation(e,tp,eg,ep,ev,re,r,rp)
    local c=e:GetHandler()
    if not c:IsRelateToEffect(e) then return end
    local mg=s.fus_group(e,tp)
    if not mg:IsContains(c) then return end
    local candidates=Duel.GetMatchingGroup(s.fus_filter,tp,LOCATION_EXTRA,0,nil,e,tp,mg,c)
    if candidates:GetCount()==0 then return end
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_SPSUMMON)
    local fc=candidates:Select(tp,1,1,nil):GetFirst()
    if not fc then return end
    local materials=Duel.SelectFusionMaterial(tp,fc,mg,c,tp)
    if not materials:IsContains(c) then return end
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

function s.postcon(e,tp,eg,ep,ev,re,r,rp)
    return e:GetHandler():GetSummonType()==SUMMON_TYPE_SPECIAL+1
end

function s.postfilter(c) return c:IsDestructable() end
function s.posttg(e,tp,eg,ep,ev,re,r,rp,chk)
    if chk==0 then return Duel.IsExistingMatchingCard(s.postfilter,tp,LOCATION_HAND|LOCATION_ONFIELD,LOCATION_HAND|LOCATION_ONFIELD,1,nil) end
    Duel.SetOperationInfo(0,CATEGORY_DESTROY,nil,1,PLAYER_ALL,LOCATION_HAND|LOCATION_ONFIELD)
end
function s.postop(e,tp,eg,ep,ev,re,r,rp)
    local loc=LOCATION_ONFIELD
    if Duel.SelectYesNo(tp,aux.Stringid(id,3)) then loc=LOCATION_HAND end
    if loc==LOCATION_HAND then
        local g=Duel.GetMatchingGroup(s.postfilter,tp,LOCATION_HAND,LOCATION_HAND,nil)
        if #g==0 then return end
        local p=tp
        if #Duel.GetMatchingGroup(s.postfilter,tp,LOCATION_HAND,0,nil)==0 then p=1-tp
        elseif #Duel.GetMatchingGroup(s.postfilter,tp,0,LOCATION_HAND,nil)>0 and Duel.SelectYesNo(tp,aux.Stringid(id,4)) then p=1-tp end
        local rg=Duel.GetMatchingGroup(s.postfilter,tp,LOCATION_HAND,0,nil)
        if p~=tp then rg=Duel.GetMatchingGroup(s.postfilter,tp,0,LOCATION_HAND,nil) end
        if #rg>0 then Duel.Destroy(rg:RandomSelect(tp,1),REASON_EFFECT) end
    else
        Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_DESTROY)
        local g=Duel.SelectMatchingCard(tp,s.postfilter,tp,LOCATION_ONFIELD,LOCATION_ONFIELD,1,1,nil)
        if #g>0 then Duel.Destroy(g,REASON_EFFECT) end
    end
end


-- Alpha 0.6: self-Special Summon by destroying a Catastrophe card from Deck.
-- Ext Ryzeal-style hand summoning procedure; deck destruction uses REASON_EFFECT.
function s.spfilter(c)
    return c:IsSetCard(0xfcb)
end
function s.spcon(e,c)
    if c==nil then return true end
    local tp=c:GetControler()
    return Duel.GetLocationCount(tp,LOCATION_MZONE)>0
        and Duel.IsExistingMatchingCard(s.spfilter,tp,LOCATION_DECK,0,1,nil)
end
function s.sptg(e,tp,eg,ep,ev,re,r,rp,chk,c)
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_DESTROY)
    local g=Duel.SelectMatchingCard(tp,s.spfilter,tp,LOCATION_DECK,0,1,1,nil)
    if #g==0 then return false end
    g:KeepAlive()
    e:SetLabelObject(g)
    return true
end
function s.spop(e,tp,eg,ep,ev,re,r,rp,c)
    local g=e:GetLabelObject()
    if g then
        Duel.Destroy(g,REASON_EFFECT)
        g:DeleteGroup()
        e:SetLabelObject(nil)
    end
end
function s.register_special(c)
    local e1=Effect.CreateEffect(c)
    e1:SetType(EFFECT_TYPE_FIELD)
    e1:SetCode(EFFECT_SPSUMMON_PROC)
    e1:SetProperty(EFFECT_FLAG_UNCOPYABLE)
    e1:SetRange(LOCATION_HAND)
    e1:SetValue(1)
    e1:SetCondition(s.spcon)
    e1:SetTarget(s.sptg)
    e1:SetOperation(s.spop)
    e1:SetCountLimit(1,id,EFFECT_COUNT_CODE_OATH)
    c:RegisterEffect(e1)
end
