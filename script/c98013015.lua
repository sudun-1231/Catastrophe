-- Catastrophe Chimera: opponent-only Battle Phase suppression.
local s,id=GetID()
local SET_CAT=0xfcb
function s.initial_effect(c)
    c:EnableReviveLimit()
    if Fusion and Fusion.AddProcMixRep then
        Fusion.AddProcMixRep(c,true,true,aux.TRUE,1,99,s.matfilter)
    else
        aux.AddFusionProcMixRep(c,true,true,aux.TRUE,1,99,s.matfilter)
    end
    local disable=Effect.CreateEffect(c)
    disable:SetType(EFFECT_TYPE_FIELD)
    disable:SetCode(EFFECT_DISABLE)
    disable:SetRange(LOCATION_MZONE)
    disable:SetTargetRange(0,LOCATION_ONFIELD)
    disable:SetCondition(s.battlephase)
    disable:SetTarget(s.faceup)
    c:RegisterEffect(disable)
    local effects=disable:Clone()
    effects:SetCode(EFFECT_DISABLE_EFFECT)
    c:RegisterEffect(effects)
    local traps=disable:Clone()
    traps:SetCode(EFFECT_DISABLE_TRAPMONSTER)
    traps:SetTarget(function(e,c) return c:IsFaceup() and c:IsType(TYPE_TRAPMONSTER) end)
    c:RegisterEffect(traps)
    local lock=Effect.CreateEffect(c)
    lock:SetType(EFFECT_TYPE_FIELD)
    lock:SetProperty(EFFECT_FLAG_PLAYER_TARGET)
    lock:SetCode(EFFECT_CANNOT_ACTIVATE)
    lock:SetRange(LOCATION_MZONE)
    lock:SetTargetRange(0,1)
    lock:SetCondition(s.battlephase)
    lock:SetValue(aux.TRUE)
    c:RegisterEffect(lock)
    local gain=Effect.CreateEffect(c)
    gain:SetDescription(aux.Stringid(id,1))
    gain:SetCategory(CATEGORY_ATKCHANGE)
    gain:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
    gain:SetCode(EVENT_PRE_DAMAGE_CALCULATE)
    gain:SetCondition(s.atkcon)
    gain:SetCost(s.atkcost)
    gain:SetOperation(s.atkop)
    c:RegisterEffect(gain)
    local pierce=Effect.CreateEffect(c)
    pierce:SetType(EFFECT_TYPE_SINGLE)
    pierce:SetCode(EFFECT_PIERCE)
    pierce:SetValue(DOUBLE_DAMAGE)
    c:RegisterEffect(pierce)
    local recover=Effect.CreateEffect(c)
    recover:SetDescription(aux.Stringid(id,3))
    recover:SetCategory(CATEGORY_TODECK+CATEGORY_TOHAND)
    recover:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
    recover:SetProperty(EFFECT_FLAG_DELAY)
    recover:SetCode(EVENT_TO_GRAVE)
    recover:SetCountLimit(1,id)
    recover:SetTarget(s.rectarget)
    recover:SetOperation(s.recoperation)
    c:RegisterEffect(recover)
    local removed=recover:Clone()
    removed:SetCode(EVENT_REMOVE)
    removed:SetCondition(function(e) return e:GetHandler():IsFaceup() end)
    c:RegisterEffect(removed)
end
function s.matfilter(c) return c:IsSetCard(SET_CAT) end
function s.battlephase()
    local phase=Duel.GetCurrentPhase()
    return phase>=PHASE_BATTLE_START and phase<=PHASE_BATTLE
end
function s.faceup(e,c) return c:IsFaceup() end
function s.atkcon(e)
    return e:GetHandler():GetBattleTarget()~=nil
end
function s.atkcost(e,tp,eg,ep,ev,re,r,rp,chk)
    local c=e:GetHandler()
    if chk==0 then return c:GetFlagEffect(id)==0 end
    c:RegisterFlagEffect(id,RESET_EVENT+RESETS_STANDARD+RESET_PHASE+PHASE_DAMAGE_CAL,0,1)
end
function s.atkop(e)
    local c=e:GetHandler()
    local bc=c:GetBattleTarget()
    if not (bc and c:IsFaceup() and c:IsRelateToBattle() and bc:IsFaceup() and bc:IsRelateToBattle()) then return end
    local effect=Effect.CreateEffect(c)
    effect:SetType(EFFECT_TYPE_SINGLE)
    effect:SetCode(EFFECT_UPDATE_ATTACK)
    effect:SetValue(math.max(0,bc:GetAttack()))
    effect:SetReset(RESET_EVENT+RESETS_STANDARD+RESET_PHASE+PHASE_DAMAGE_CAL)
    c:RegisterEffect(effect)
end
function s.searchfilter(c)
    return c:IsSetCard(SET_CAT) and c:IsAbleToHand()
        and (not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup())
end
function s.rectarget(e,tp,eg,ep,ev,re,r,rp,chk)
    local c=e:GetHandler()
    if chk==0 then return c:IsAbleToDeck() and Duel.IsExistingMatchingCard(
        aux.NecroValleyFilter(s.searchfilter),tp,LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED,0,1,c) end
    Duel.SetOperationInfo(0,CATEGORY_TODECK,c,1,0,0)
    Duel.SetOperationInfo(0,CATEGORY_TOHAND,nil,1,tp,LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED)
end
function s.recoperation(e,tp)
    local c=e:GetHandler()
    if not c:IsRelateToEffect(e) or not c:IsAbleToDeck() then return end
    if Duel.SendtoDeck(c,nil,SEQ_DECKSHUFFLE,REASON_EFFECT)==0 then return end
    Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_ATOHAND)
    local g=Duel.SelectMatchingCard(tp,aux.NecroValleyFilter(s.searchfilter),tp,
        LOCATION_DECK+LOCATION_GRAVE+LOCATION_REMOVED,0,1,1,c)
    if g:GetCount()>0 and Duel.SendtoHand(g,nil,REASON_EFFECT)>0 then Duel.ConfirmCards(1-tp,g) end
end
