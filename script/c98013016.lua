-- Catastrophe Abyss Dragon
local s,id=GetID()
local SET_CAT=0xfcb
function s.initial_effect(c)
 local normal=Effect.CreateEffect(c)
 normal:SetDescription(aux.Stringid(id,0))
 normal:SetType(EFFECT_TYPE_SINGLE)
 normal:SetProperty(EFFECT_FLAG_UNCOPYABLE)
 normal:SetCode(EFFECT_SUMMON_PROC)
 normal:SetCondition(function(e,c,minc) return c==nil or minc==0 and Duel.GetLocationCount(c:GetControler(),LOCATION_MZONE)>0 end)
 c:RegisterEffect(normal)
 local sp=Effect.CreateEffect(c)
 sp:SetDescription(aux.Stringid(id,1))
 sp:SetCategory(CATEGORY_SPECIAL_SUMMON+CATEGORY_DRAW)
 sp:SetType(EFFECT_TYPE_IGNITION)
 sp:SetRange(LOCATION_HAND)
 sp:SetCountLimit(1,198013162)
 sp:SetCost(s.summoncost)
 sp:SetTarget(s.summontarget)
 sp:SetOperation(s.summonoperation)
 c:RegisterEffect(sp)
 local on=Effect.CreateEffect(c)
 on:SetDescription(aux.Stringid(id,2))
 on:SetCategory(CATEGORY_TOHAND)
 on:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
 on:SetProperty(EFFECT_FLAG_DELAY)
 on:SetCode(EVENT_SUMMON_SUCCESS)
 on:SetCountLimit(1,198013163)
 on:SetTarget(s.searchtarget)
 on:SetOperation(s.searchoperation)
 c:RegisterEffect(on)
 local special=on:Clone()
 special:SetCode(EVENT_SPSUMMON_SUCCESS)
 c:RegisterEffect(special)
 s.registergrave(c,198013164,3)
end

function s.destroyfilter(c) return c:IsSetCard(SET_CAT) and c:IsDestructable() end
function s.summoncost(e,tp,eg,ep,ev,re,r,rp,chk)
 if chk==0 then return Duel.IsExistingMatchingCard(s.destroyfilter,tp,LOCATION_DECK,0,1,nil) end
 e:SetLabel(0)
 Duel.Hint(HINT_SELECTMSG,tp,HINTMSG_DESTROY)
 local g=Duel.SelectMatchingCard(tp,s.destroyfilter,tp,LOCATION_DECK,0,1,1,nil)
 if g:GetCount()>0 and Duel.Destroy(g,REASON_COST)>0 then e:SetLabel(1) end
end
function s.summontarget(e,tp,eg,ep,ev,re,r,rp,chk)
 if chk==0 then return Duel.GetLocationCount(tp,LOCATION_MZONE)>0 and e:GetHandler():IsCanBeSpecialSummoned(e,0,tp,false,false)  end
 Duel.SetOperationInfo(0,CATEGORY_SPECIAL_SUMMON,e:GetHandler(),1,0,0)

end
function s.summonoperation(e,tp)
 local c=e:GetHandler()
 if e:GetLabel()~=1 or not c:IsRelateToEffect(e) or not c:IsLocation(LOCATION_HAND) or Duel.GetLocationCount(tp,LOCATION_MZONE)<=0 then return end
 if Duel.SpecialSummon(c,0,tp,tp,false,false,POS_FACEUP)==0 then return end
 if Duel.IsPlayerCanDraw(tp,1) and Duel.SelectYesNo(tp,aux.Stringid(id,4)) then Duel.Draw(tp,1,REASON_EFFECT) end
end

function s.searchfilter(c)
 return c:IsSetCard(SET_CAT) and c:IsAbleToHand() and (not c:IsLocation(LOCATION_REMOVED) or c:IsFaceup())
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
function s.registergrave(c,key,description)
 local e=Effect.CreateEffect(c)
 e:SetDescription(aux.Stringid(id,description))
 e:SetCategory(CATEGORY_TOHAND)
 e:SetType(EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O)
 e:SetProperty(EFFECT_FLAG_DELAY)
 e:SetCode(EVENT_TO_GRAVE)
 e:SetCountLimit(1,key)
 e:SetTarget(s.searchtarget)
 e:SetOperation(s.searchoperation)
 c:RegisterEffect(e)
 local removed=e:Clone()
 removed:SetCode(EVENT_REMOVE)
 removed:SetCondition(function(e) return e:GetHandler():IsFaceup() end)
 c:RegisterEffect(removed)
end
