-- Catastrophe Absorption: Super Polymerization-inspired activation, plus recovery.
local s,id=GetID()
s.fusion_effect=true
function s.initial_effect(c)
    local e1=Effect.CreateEffect(c)
    e1:SetDescription(aux.Stringid(id,0))
    e1:SetCategory(CATEGORY_SPECIAL_SUMMON+CATEGORY_FUSION_SUMMON)
    e1:SetType(EFFECT_TYPE_ACTIVATE)
    e1:SetCode(EVENT_FREE_CHAIN)
    e1:SetHintTiming(0,TIMINGS_CHECK_MONSTER+TIMING_END_PHASE)
    e1:SetCountLimit(1,id)
    e1:SetCost(s.fusioncost)
    e1:SetTarget(s.fusiontarget)
    e1:SetOperation(s.fusionoperation)
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
function s.fusioncost(e,tp,eg,ep,ev,re,r,rp,chk)
    local c=e:GetHandler()
    if chk==0 then return Duel.IsExistingMatchingCard(Card.IsDestructable,tp,LOCATION_HAND,0,1,c) end
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_DESTROY)
    local g=Duel.SelectMatchingCard(tp,Card.IsDestructable,tp,LOCATION_HAND,0,1,1,c)
    e:SetLabel(0)
    if g:GetCount()>0 and Duel.Destroy(g,REASON_COST)>0 then e:SetLabel(1) end
end
function s.ownmaterial(c,e)
    return c:IsOnField() and c:IsCanBeFusionMaterial() and not c:IsImmuneToEffect(e)
end
function s.opponentmaterial(c,e)
    return c:IsFaceup() and c:IsCanBeFusionMaterial() and not c:IsImmuneToEffect(e)
end
function s.materialgroup(e,tp)
    local own=Duel.GetFusionMaterial(tp):Filter(s.ownmaterial,nil,e)
    local opponent=Duel.GetMatchingGroup(s.opponentmaterial,tp,0,LOCATION_MZONE,nil,e)
    own:Merge(opponent)
    return own
end
function s.fusionfilter(c,e,tp,mg)
    return c:IsType(TYPE_FUSION) and c:IsCanBeSpecialSummoned(e,SUMMON_TYPE_FUSION,tp,false,false)
        and c:CheckFusionMaterial(mg,nil,tp)
end
function s.fusiontarget(e,tp,eg,ep,ev,re,r,rp,chk)
    local mg=s.materialgroup(e,tp)
    if chk==0 then return Duel.IsExistingMatchingCard(s.fusionfilter,tp,LOCATION_EXTRA,0,1,nil,e,tp,mg) end
    Duel.SetOperationInfo(0,CATEGORY_SPECIAL_SUMMON,nil,1,tp,LOCATION_EXTRA)
    -- Official Super Polymerization pattern: neither player may chain to this activation.
    Duel.SetChainLimit(aux.FALSE)
end
function s.fusionoperation(e,tp)
    if e:GetLabel()~=1 then return end
    local mg=s.materialgroup(e,tp)
    local candidates=Duel.GetMatchingGroup(s.fusionfilter,tp,LOCATION_EXTRA,0,nil,e,tp,mg)
    if candidates:GetCount()==0 then return end
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_SPSUMMON)
    local fc=candidates:Select(tp,1,1,nil):GetFirst()
    if not fc then return end
    local materials=Duel.SelectFusionMaterial(tp,fc,mg,nil,tp)
    if materials:GetCount()==0 then return end
    fc:SetMaterial(materials)
    Duel.SendtoGrave(materials,REASON_EFFECT+REASON_MATERIAL+REASON_FUSION)
    Duel.BreakEffect()
    if Duel.SpecialSummon(fc,SUMMON_TYPE_FUSION,tp,tp,false,false,POS_FACEUP)>0 then fc:CompleteProcedure() end
end

function s.recovercondition(e)
    local c=e:GetHandler()
    return not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup()
end
function s.recovercost(e,tp,eg,ep,ev,re,r,rp,chk)
    if chk==0 then return Duel.GetFieldGroupCount(tp,LOCATION_DECK,0)>0 and Duel.IsPlayerCanDraw(tp,1) end
    e:SetLabel(0)
    if Duel.Draw(tp,1,REASON_COST)>0 then e:SetLabel(1) end
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
