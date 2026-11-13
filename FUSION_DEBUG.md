# Alpha 0.9 융합 효과 디버깅

## 확인한 결함과 수정

1. **용기사(c98013013)의 `s.matfilter` 누락.** `Fusion.AddProcMixN(c,true,true,s.matfilter,2)`에 nil이 전달됐다. 공식 `AddProcMixN`으로 등록을 검사했을 때 정상적인 2장 소재 절차가 등록되지 않았다. 원문 `ORIGINAL_SOURCE.txt`의 「카타스트로피」 몬스터 × 2에 맞춰 필터를 정의했다. 따라서 Alpha 0.8 문서의 프레이＋랜서→용기사 예시에서 융합 대상의 소재 판정이 깨질 수 있다. 이것이 모든 MDPro3 발동 실패의 유일한 원인이라고 단정하지 않는다.
2. **메인 덱 5장의 ② 효과 제한 키 충돌.** `id+2`는 다른 카드 ID와 겹친다. 예를 들어 프레이의 ② 키 98013003은 가디언의 ① 키와 같다. `SetCountLimit(1,{id,1})`로 분리했다. 이 결함은 ③의 발동 실패와 별개의 문제다.
3. **제외 소재 필터 명확화.** `IsMonster()` 및 `IsAbleToDeck()`을 유지하고 `not IsLocation(LOCATION_REMOVED) or IsFaceup()`으로 표현했다. 기존 묘지/제외 그룹에서는 의미가 동일하다. 앞면 제외만 허용하며 뒷면 제외는 허용하지 않는다.

원본 Alpha 0.8 YPK는 변경하지 않는다. `script/`의 6개 파일을 수정 원본으로 제공하며 `python3 tools/build_alpha09.py`로 새 YPK를 만든다. 새 팩의 기존 구현 상태 문서는 과거 기록으로 보존되며 이번 수정 내용은 이 문서를 우선한다. ③으로 지칭한 용기사의 융합 효과는 원문상 ②이다.

## 필수 조사 결과

| 조사 항목 | 결과 |
| --- | --- |
| `EVENT_TO_GRAVE`, `EVENT_REMOVE` | 단일 카드 이벤트로 등록됨. 제외 이벤트는 묘지 이벤트의 Clone이며 앞면 조건이 있음. 유지. |
| 타입·지연 | 가루라·메이루와 같은 `EFFECT_TYPE_SINGLE+EFFECT_TYPE_TRIGGER_O`, `EFFECT_FLAG_DELAY`. 유지. |
| TG/OP 매개변수 | 공식 메이루와 동일한 named-argument table 사용. `extratg`는 TG가 사용하는 항목이며 OP의 table에 함께 있어도 문제가 아님. 유지. |
| `Fusion.ForcedHandler` | 효과 핸들러를 반환. 공식 라이브러리가 이를 필수 소재 그룹으로 사용하고 소재 검사·선택에 전달함. 유지. |
| 패/필드 소재 | 라이브러리의 `Duel.GetFusionMaterial(tp)` 기본 그룹 사용. 자신의 뒷면 몬스터 존 소재도 엔진이 허용하는 범위에서 유지. |
| 묘지/제외 소재 | `extrafil`이 자신의 `LOCATION_GRAVE|LOCATION_REMOVED` 그룹을 추가. 상대 소재를 추가하지 않음. |
| `IsAbleToDeck` | 공식 메이루와 동일. 덱으로 돌아갈 수 없는 소재는 제외. 융합 몬스터가 소재가 되면 게임 규칙에 따라 엑스트라 덱으로 돌아감. |
| 자신 필수 포함 | `gc=Fusion.ForcedHandler` 유지. 공식 라이브러리는 해결 시 핸들러의 효과 관련성도 검사(`Fusion.ForcedMatValidity`). |
| 턴당 제한 | ③의 `{code,2}`는 묘지/제외 및 동명 카드가 공유. ②는 `{id,1}`로 분리. 용기사 무효 효과의 `id`와 융합 효과의 `{id,2}`도 분리. |
| 소재 처리 | 메이루 방식의 `SendtoDeck(...SEQ_DECKBOTTOM, REASON_EFFECT|REASON_MATERIAL|REASON_FUSION)`, `SortDeckbottom`, `sg:Clear()` 유지. 이 Clear는 기본 묘지 전송을 중복 수행하지 않게 하는 공식 패턴. |

메이루의 `IsReason(REASON_EFFECT)` 및 데미지 페이즈 조건은 이 카드의 원문과 다르므로 새로 이식하지 않았다. 코스트로 묘지에 보내지는 경우도 원문대로 제외하지 않는다. 나이트메어 쓰론은 필드 마법의 커스텀 이벤트 추적용이므로 이 카드의 단일 묘지/제외 트리거에 그 구조를 이식할 이유가 없다. 제외 앞면 필터 패턴은 참고했다.

## 검증 및 한계

- `python3 tests/check_fusion_contracts.py`: Lua 5.4에서 6개 스크립트의 등록, Clone, 제한 키, 매개변수 연결, 필수 핸들러 연결 및 소재 필터 검사. 원본 프레이의 제한 키 및 원본 용기사의 소재 정의 결함이 검출되는 것도 확인한다.
- `python3 tests/check_fusion_contracts.py --fusion-procedure /path/to/proc_fusion.lua`: 실제 공식 `AddProcMixN`으로 같은 등록 검사. 테스트의 엔진 API와 TG/OP는 mock이다. 실제 융합 가능성 판정·선택·소환 및 턴 카운터 소비를 실행한 테스트가 아니다.
- 새 YPK CRC 및 원본 대비 변경 범위 검사. 기존 DB·이미지·덱은 그대로 보존.
- 실제 MDPro3 클라이언트/엔진/동봉 라이브러리는 저장소에 없으므로 듀얼 실행 및 해당 버전의 라이브러리 호환성은 **미검증**. 추가 실패가 있으면 클라이언트 버전과 해당 듀얼의 스크립트 오류 로그를 확인해야 한다.

## MDPro3 재현 체크리스트 — 실행 전

구버전 팩과 새 팩을 동시에 로드하지 말고 Alpha 0.9만 테스트한다. 독립적인 각 테스트는 새 듀얼 또는 다음 턴에서 진행한다. ③ 사용 후 같은 턴에 다시 발동되지 않는 것은 정상이다.

1. 엑스트라 덱에 용기사(98013013), 패 또는 몬스터 존에 랜서(98013002)를 둔다. 프레이(98013001)를 덱에서 효과로 파괴해 묘지로 보낸다. ③ 선택창에서 프레이＋랜서→용기사, 두 소재의 덱 아래 이동을 확인한다.
2. 프레이를 앞면 제외하고 1과 같은 소재로 융합한다. 뒷면 제외한 경우 선택창이 없어야 한다.
3. 랜서를 묘지 또는 앞면 제외에 두어도 프레이와 함께 소재가 되는지 확인한다. 덱으로 되돌릴 수 없게 제한된 소재는 선택되지 않아야 한다.
4. 다른 소재가 없는 경우, 엑스트라 덱에 적합한 융합 몬스터가 없는 경우에는 발동할 수 없어야 한다.
5. 해결 전에 발동한 프레이가 다른 장소로 이동하면 다른 소재만으로 소환하지 않아야 한다.
6. 같은 턴에 같은 이름의 묘지 트리거와 제외 트리거를 모두 사용하지 못해야 한다. 다른 이름의 융합 효과와 ①/② 효과는 서로 제한을 소비하지 않아야 한다. 프레이의 ② 사용 후 가디언의 ①도 별도로 확인한다.
7. 나머지 4종 메인 덱 몬스터도 1~6을 반복한다. 용기사 자신의 융합 트리거는 다른 카타스트로피 몬스터와 함께 소재가 되어 다른 적합한 융합 몬스터를 소환하는지 확인한다. 용기사는 메인 덱이 아닌 엑스트라 덱으로 돌아가야 한다.

## 참고 버전

Project Ignis CardScripts 커밋 `195bfa78dcfa848c0dd1d26d6ea8216420e8b8a5`의 아래 5개 파일을 직접 읽고 고정 커밋 다운로드 내용이 같은지 확인했다.

- https://github.com/ProjectIgnis/CardScripts/blob/195bfa78dcfa848c0dd1d26d6ea8216420e8b8a5/official/c74078255.lua
- https://github.com/ProjectIgnis/CardScripts/blob/195bfa78dcfa848c0dd1d26d6ea8216420e8b8a5/official/c11765832.lua
- https://github.com/ProjectIgnis/CardScripts/blob/195bfa78dcfa848c0dd1d26d6ea8216420e8b8a5/official/c93729896.lua
- https://github.com/ProjectIgnis/CardScripts/blob/195bfa78dcfa848c0dd1d26d6ea8216420e8b8a5/proc_fusion.lua
- https://github.com/ProjectIgnis/CardScripts/blob/195bfa78dcfa848c0dd1d26d6ea8216420e8b8a5/proc_fusion_spell.lua
