-- Catastrophe Forerunner
local s,id=GetID()
local SET_CAT=0xfcb
function s.initial_effect(c)
 local sp=Effect.CreateEffect(c)
 sp:SetDescription(aux.Stringid(id,0))
 sp:SetCategory(CATEGORY_SPECIAL_SUMMON+CATEGORY_DESTROY)
 sp:SetType(EFFECT_TYPE_QUICK_O)
 sp:SetCode(EVENT_CHAINING)
 sp:SetRange(LOCATION_HAND)
 sp:SetCountLimit(1,198013201)
 sp:SetCondition(function(e,tp,eg,ep,ev,re,r,rp) return rp==1-tp end)
 sp:SetTarget(s.sptarget)
 sp:SetOperation(s.spoperation)
 c:RegisterEffect(sp)
 local search=Effect.CreateEffect(c)
 search:SetDescription(aux.Stringid(id,1))
 search:SetCategory(CATEGORY_TOHAND)
 search:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
 search:SetProperty(EFFECT_FLAG_DELAY)
 search:SetCode(EVENT_SPSUMMON_SUCCESS)
 search:SetCountLimit(1,198013202)
 search:SetTarget(s.searchtarget)
 search:SetOperation(s.searchoperation)
 c:RegisterEffect(search)
 s.fuse_register(c,id)
end
function s.sptarget(e,tp,eg,ep,ev,re,r,rp,chk)
 local c=e:GetHandler()
 if chk==0 then return Duel.GetLocationCount(tp,LOCATION_MZONE)>0 and c:IsCanBeSpecialSummoned(e,0,tp,false,false) end
 Duel.SetOperationInfo(0,CATEGORY_SPECIAL_SUMMON,c,1,0,0)
end
function s.destroyfilter(c) return c:IsSetCard(SET_CAT) and c:IsDestructable() end
function s.spoperation(e,tp)
 local c=e:GetHandler()
 if not c:IsRelateToEffect(e) or not c:IsLocation(LOCATION_HAND) or Duel.GetLocationCount(tp,LOCATION_MZONE)<=0 then return end
 if Duel.SpecialSummon(c,0,tp,tp,false,false,POS_FACEUP)==0 then return end
 if Duel.IsExistingMatchingCard(s.destroyfilter,tp,LOCATION_DECK,0,1,nil) and Duel.SelectYesNo(tp,aux.Stringid(id,3)) then
  Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_DESTROY)
  local g=Duel.SelectMatchingCard(tp,s.destroyfilter,tp,LOCATION_DECK,0,1,1,nil)
  Duel.Destroy(g,REASON_EFFECT)
 end
end
function s.searchfilter(c)
 return c:IsSetCard(SET_CAT) and c:IsType(TYPE_MONSTER) and c:IsAbleToHand()
  and (not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup())
end
function s.searchtarget(e,tp,eg,ep,ev,re,r,rp,chk)
 if chk==0 then return Duel.IsExistingMatchingCard(aux.NecroValleyFilter(s.searchfilter),tp,LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED,0,1,nil) end
 Duel.SetOperationInfo(0,CATEGORY_TOHAND,nil,1,tp,LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED)
end
function s.searchoperation(e,tp)
 Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_ATOHAND)
 local g=Duel.SelectMatchingCard(tp,aux.NecroValleyFilter(s.searchfilter),tp,LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED,0,1,1,nil)
 if g:GetCount()>0 and Duel.SendtoHand(g,nil,REASON_EFFECT)>0 then Duel.ConfirmCards(1-tp,g) end
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
    e:SetCountLimit(1,198013203)
    e:SetTarget(s.fus_target)
    e:SetOperation(s.fus_operation)
    c:RegisterEffect(e)
    local removed=e:Clone()
    removed:SetCode(EVENT_REMOVE)
    removed:SetCondition(function(e) return e:GetHandler():IsFaceup() end)
    c:RegisterEffect(removed)
end
