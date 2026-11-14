# Alpha 0.10 — MDPro3 융합 호환성 수정

## 재현한 원인

Alpha 0.9는 최신 Project Ignis의 `Fusion.SummonEffTG/OP`, `Fusion.CreateSummonEff`, `Fusion.AddProcMixN`과 테이블 형태 `SetCountLimit`에 의존했다. 그러나 공개 MDPro3 미러의 동봉 `Data/script.zip`에는 `Fusion` 네임스페이스가 없고, `aux.AddFusionProcMix`, `aux.AddFusionProcMixRep` 및 직접 융합 소재 선택을 사용한다. 그 소스의 `SetCountLimit`도 숫자를 받는다.

MDPro3 미러 `SethPDA/MDPro3` 커밋 `1d106cc4919f6996209215441035781f6f85203b`의 C++ 코어와 동봉 Lua를 Linux x86_64 공유 라이브러리로 직접 빌드했다. 동봉 스크립트를 그대로 사용해 Alpha 0.9를 로드하면 대상 6종, 탄생 및 융합 몬스터에서 **`attempt to index a nil value (global 'Fusion')`** 오류가 재현된다. 따라서 이전 mock 검사의 통과는 해당 MDPro3 라이브러리에서의 등록 성공을 입증하지 못했다.

또한 이 코어에는 `Duel.SortDeckbottom`이 없다. 탄생 ② 해결을 실행하여 해당 nil 함수 오류도 재현했다. 구형 라이브러리에서는 공식 메이루처럼 `aux.PlaceCardsOnDeckBottom`을 사용해야 한다.

사용자의 정확한 MDPro3 버전은 아직 제공되지 않았다. 위 미러의 결과를 모든 버전의 동작 보장으로 해석하지 않는다.

## 수정 내용

- `c98013008.lua`: 탄생 ①을 일반 마법의 활성화 효과로 직접 등록. 패/덱/몬스터 존에서 소재를 모아 「카타스트로피」 융합 몬스터만 소환한다. 소재는 융합 소재로 묘지에 보낸다.
- 탄생 ②: 묘지 또는 앞면 제외에서 발동하는 기동 효과. 자신을 덱으로 되돌리는 코스트를 지불한 후 패/몬스터 존/묘지/앞면 제외 소재로 융합한다. 코스트로 장소를 옮긴 마법 자신에게 `IsRelateToEffect`를 요구하지 않는다. 이 효과는 융합 몬스터를 카드군으로 제한하지 않는다.
- 대상 6종: `Fusion.SummonEffTG/OP` 의존성을 없애고 `CheckFusionMaterial`과 `Duel.SelectFusionMaterial`에 핸들러를 필수 소재로 직접 전달한다. 해결 시 관련성이 없거나 소재 그룹에 자신이 없으면 중단한다.
- 융합 소재의 반환은 `aux.PlaceCardsOnDeckBottom`이 있으면 해당 공식 함수를 사용한다. 없으면 현대 라이브러리의 `SendtoDeck`/`SortDeckbottom` 경로를 사용한다. 융합 몬스터 소재는 규칙대로 엑스트라 덱으로 돌아간다.
- `c98013012/13/14.lua`: `Fusion` 절차가 없는 라이브러리에서는 `aux.AddFusionProcMix/Rep`를 사용한다. 용기사의 카타스트로피 몬스터 2장 정의는 유지한다. 이 셋이 로드되지 않으면 발동 가능한 융합 대상도 사라지므로 함께 수정했다.
- ②/③ 및 탄생 효과의 턴당 제한을 숫자 전용 키 `198013000+(카드ID-98013000)*10+효과인덱스`로 분리했다. 몬스터 융합 효과의 묘지/제외 Clone은 같은 키를 공유한다. 원래 ①의 카드 ID와도 충돌하지 않는다.
- 앞면 제외만 소재로 사용하고 `IsAbleToDeck`, 면역, 묘지 이동 제한을 검사한다. 패와 자신의 뒷면 필드 소재는 허용한다.

별도의 Chain Material 대체 융합 경로는 제공하지 않는다. 각종 외부 카드 상호작용을 모두 검증한 것은 아니다. 다른 효과의 기존 Alpha 부분 구현은 유지한다.

## 검증 범위

`tests/check_fusion_contracts.py`는 이제 mock 등록 검사 대신 위 MDPro3 코어와 동봉 Lua 라이브러리를 사용한다.

- 원본 Alpha 0.9의 Fusion 네임스페이스 오류 재현.
- 수정 팩 카드 14장의 초기 효과 등록 오류 없음.
- 대상 6종 × 묘지/앞면 제외 = 12가지 융합 가능 판정 통과.
- 탄생 ①/② 소재 판정 통과; 소재 부족 및 뒷면 제외 필수 소재는 거절.
- 탄생 ②의 코스트 지불 후 소재 반환과 융합 소환을 네이티브 코어에서 실행.
- 프레이를 실제 효과로 묘지에 보내거나 앞면 제외 → 네이티브 코어의 선택 트리거 발동 → 프레이 자신을 포함한 소재 반환 → 용기사 융합 소환 통과.
- 탄생 ①을 실제 마법 효과로 활성화하여 덱의 두 소재를 묘지에 보내고 용기사 융합 소환 통과.
- 탄생 ②를 실제 기동 효과로 발동하여 마법의 덱 반환 코스트와 앞면 제외 소재의 덱 반환, 용기사 융합 소환 통과.

카드/소재 선택과 덱 아래 정렬 UI 입력은 고정된 합법적인 예제로 자동화했다. 융합 소재 가능성 판정, 코스트, 이벤트/체인, 카드 이동, 소환은 실제 코어가 처리한다. MDPro3 Unity UI나 사용자의 클라이언트에서 테스트한 것은 아니다. 턴당 제한의 전체 멀티카드 소비, 모든 대상 몬스터의 실제 체인 해결, 모든 소재 조합과 외부 카드 상호작용은 별도 검증 대상이다.

재현 명령(저장소 안에서 실행):

```sh
# 외부 테스트 작업 폴더에 동일한 공개 미러를 준비한다.
git clone --depth 1 https://github.com/SethPDA/MDPro3.git /workspace/mdpro3-reference
# 위에서 명시한 커밋과 일치하는지 확인한다. HEAD가 달라지면 해당 커밋을 fetch/checkout한다.
git -C /workspace/mdpro3-reference rev-parse HEAD
python3 tools/build_mdpro3_test_core.py /workspace/mdpro3-reference /workspace/mdpro3-native
python3 tests/check_fusion_contracts.py --core /workspace/mdpro3-native/build/libocgcore.so --scripts /workspace/mdpro3-native/script.zip --baseline
python3 tests/check_fusion_contracts.py --core /workspace/mdpro3-native/build/libocgcore.so --scripts /workspace/mdpro3-native/script.zip
python3 tools/build_alpha10.py
```

빌드에는 git, gcc, g++가 필요하며 최대 4개 컴파일 작업을 병렬로 실행한다. 테스트는 Python 표준 라이브러리만 사용한다.

## 설치 및 현장 확인

1. MDPro3를 종료한다.
2. `Expansions`의 이전 Catastrophe Alpha 0.8/0.9 YPK 및 같은 카드 ID를 가진 중복 팩을 다른 폴더로 옮긴다. 이전 파일은 백업한다.
3. **`Catastrophe_MDPro3_alpha_v10_mdpro3_compat.ypk` 하나만** 넣고 클라이언트를 다시 시작한다.
4. 엑스트라 덱에 용기사, 패에 랜서를 두고 프레이를 효과로 묘지에 보내거나 앞면 제외한다. 프레이를 포함하여 융합하는지 확인한다.
5. 탄생 ①은 덱의 프레이/랜서로 용기사를 소환한다. 탄생 ②는 탄생을 묘지 또는 앞면 제외에 두고 다른 소재를 준비하여 별도로 시험한다. 효과별로 턴당 1회이므로 새 듀얼에서 확인하면 제한 소비와 혼동하지 않는다.
6. 여전히 발동하지 않으면 MDPro3 버전, 해당 시도의 Lua 오류 로그, 설치된 중복 팩 여부를 확인한다. 실제 클라이언트의 `Data/script.zip`과 테스트에 사용한 미러의 라이브러리가 다를 수 있다.

이 문서는 Alpha 0.9의 FUSION_DEBUG.md 및 팩 안의 이전 검증 기록을 대체한다. 이전 문서는 과거 기록으로 보존한다.
