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
    if Fusion and Fusion.AddProcMixN then
        Fusion.AddProcMixN(c,true,true,s.matfilter,3)
    else
        aux.AddFusionProcMix(c,true,true,s.matfilter,s.matfilter,s.matfilter)
    end
    -- Unaffected by other cards' effects
    local e1=Effect.CreateEffect(c)
    e1:SetType(EFFECT_TYPE_SINGLE)
    e1:SetCode(EFFECT_IMMUNE_EFFECT)
    e1:SetProperty(EFFECT_FLAG_SINGLE_RANGE)
    e1:SetRange(LOCATION_MZONE)
    e1:SetValue(s.immval)
    c:RegisterEffect(e1)
    local e2=Effect.CreateEffect(c)
    e2:SetType(EFFECT_TYPE_SINGLE)
    e2:SetCode(EFFECT_INDESTRUCTABLE_BATTLE)
    e2:SetValue(1)
    c:RegisterEffect(e2)
    local e3=e2:Clone()
    e3:SetCode(EFFECT_INDESTRUCTABLE_EFFECT)
    c:RegisterEffect(e3)
    local e4=Effect.CreateEffect(c)
    e4:SetType(EFFECT_TYPE_SINGLE)
    e4:SetCode(EFFECT_AVOID_BATTLE_DAMAGE)
    e4:SetValue(1)
    c:RegisterEffect(e4)
    -- Once during each damage calculation (the event occurs once per battle).
    local e5=Effect.CreateEffect(c)
    e5:SetDescription(aux.Stringid(id,2))
    e5:SetCategory(CATEGORY_ATKCHANGE)
    e5:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
    e5:SetCode(EVENT_PRE_DAMAGE_CALCULATE)
    e5:SetCondition(s.atkcon)
    e5:SetOperation(s.atkop)
    c:RegisterEffect(e5)
    -- Remember the opponent before it may leave the field through battle.
    local track=Effect.CreateEffect(c)
    track:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_CONTINUOUS)
    track:SetProperty(EFFECT_FLAG_CANNOT_DISABLE)
    track:SetCode(EVENT_BATTLED)
    track:SetOperation(s.battletrack)
    c:RegisterEffect(track)
    local e6=Effect.CreateEffect(c)
    e6:SetDescription(aux.Stringid(id,3))
    e6:SetCategory(CATEGORY_DAMAGE+CATEGORY_DESTROY)
    e6:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_F)
    e6:SetCode(EVENT_DAMAGE_STEP_END)
    e6:SetCondition(s.damcon)
    e6:SetLabelObject(track)
    e6:SetTarget(s.damtg)
    e6:SetOperation(s.damop)
    c:RegisterEffect(e6)
    local e7=Effect.CreateEffect(c)
    e7:SetDescription(aux.Stringid(id,4))
    e7:SetCategory(CATEGORY_DESTROY)
    e7:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
    e7:SetProperty(EFFECT_FLAG_DELAY)
    e7:SetCode(EVENT_LEAVE_FIELD)
    e7:SetCondition(s.leavecon)
    e7:SetTarget(s.leavetg)
    e7:SetOperation(s.leaveop)
    c:RegisterEffect(e7)
end

function s.immval(e,te)
    return te:GetOwner()~=e:GetOwner()
end

function s.matfilter(c)
    return c:IsSetCard(0xfcb)
end

function s.atkcon(e,tp)
    local bc=e:GetHandler():GetBattleTarget()
    return bc and bc:IsControler(1-tp)
end
function s.atkop(e,tp)
    local c=e:GetHandler()
    local bc=c:GetBattleTarget()
    if not (bc and c:IsFaceup() and c:IsRelateToBattle() and bc:IsFaceup() and bc:IsRelateToBattle()) then return end
    local gain=Effect.CreateEffect(c)
    gain:SetType(EFFECT_TYPE_SINGLE)
    gain:SetCode(EFFECT_UPDATE_ATTACK)
    gain:SetValue(math.max(0,bc:GetAttack()))
    gain:SetReset(RESET_EVENT+RESETS_STANDARD+RESET_PHASE+PHASE_DAMAGE_CAL)
    c:RegisterEffect(gain)
end
function s.battletrack(e,tp)
    local c=e:GetHandler()
    local bc=c:GetBattleTarget()
    if bc and c:IsAttackPos() and bc:IsControler(1-tp) then
        e:SetLabel(math.max(0,bc:GetAttack()))
        e:SetLabelObject(bc)
    else
        e:SetLabelObject(nil)
    end
end
function s.damcon(e,tp,eg,ep,ev,re,r,rp)
    return e:GetHandler():IsAttackPos() and aux.dsercon(e,tp,eg,ep,ev,re,r,rp)
end
function s.damtg(e,tp,eg,ep,ev,re,r,rp,chk)
    local track=e:GetLabelObject()
    local bc=track:GetLabelObject()
    if chk==0 then return bc~=nil end
    Duel.SetOperationInfo(0,CATEGORY_DAMAGE,nil,0,1-tp,track:GetLabel())
    if bc:IsRelateToBattle() then Duel.SetOperationInfo(0,CATEGORY_DESTROY,bc,1,0,0) end
end
function s.damop(e,tp)
    local track=e:GetLabelObject()
    Duel.Damage(1-tp,track:GetLabel(),REASON_EFFECT)
    local bc=track:GetLabelObject()
    if bc and bc:IsRelateToBattle() then Duel.Destroy(bc,REASON_EFFECT) end
end
function s.leavecon(e)
    local c=e:GetHandler()
    return c:IsPreviousLocation(LOCATION_ONFIELD) and c:IsPreviousPosition(POS_FACEUP)
end
function s.leavetg(e,tp,eg,ep,ev,re,r,rp,chk)
    if chk==0 then return true end
end
function s.leaveop(e,tp)
    local delayed=Effect.CreateEffect(e:GetHandler())
    delayed:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
    delayed:SetCode(EVENT_PHASE+PHASE_END)
    delayed:SetCountLimit(1)
    delayed:SetLabel(tp)
    delayed:SetOperation(s.enddestroy)
    delayed:SetReset(RESET_PHASE+PHASE_END)
    Duel.RegisterEffect(delayed,tp)
end
function s.enddestroy(e)
    local tp=e:GetLabel()
    local g=Duel.GetMatchingGroup(aux.TRUE,tp,0,LOCATION_ONFIELD+LOCATION_HAND,nil)
    if g:GetCount()>0 then Duel.Destroy(g,REASON_EFFECT) end
end
