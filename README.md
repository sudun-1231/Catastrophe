# Catastrophe

MDPro3 커스텀 카드군 「카타스트로피」.

현재 테스트 팩: **Alpha 0.23 — 파수꾼 ② 소환 감지 호환성 보강**

- [Alpha 0.23 YPK 다운로드](https://github.com/sudun-1231/Catastrophe/raw/refs/heads/codex/alpha09-fusion-fix/Catastrophe_MDPro3_alpha_v23_watchkeeper_trigger.ypk)
- [변경 사항·검증 범위](EFFECT_DEBUG_ALPHA23.md)

MDPro3를 종료한 뒤 이전 Catastrophe 팩을 백업하고 `Expansions`에는 최신 팩 하나만 넣어 다시 시작하세요. 공개 MDPro3 미러의 네이티브 코어와 동봉 Lua에서 기존 215개와 파수꾼 집중 검사 10개, 총 225개 시나리오를 검증했습니다. 사용 중인 클라이언트 버전 및 Unity UI에서의 검증은 별도입니다.

파수꾼 ②의 자기 소환과 다른 몬스터 소환 반응을 분리했습니다. 검증 엔진에서는 이전 버전도 정상 동작하여, 사용자 환경의 최초 증상은 아직 재현하지 못했습니다. 실제 클라이언트에서 증상 해소 확인이 필요합니다.

현재 카드 21장. 신규 선구자(98013020)와 침공(98013021)은 메인 덱에 추가하세요. 각 카드에 새로 생성한 전용 일러스트를 적용했습니다. 재앙왕·파수꾼·종언룡의 지속 보호는 문서에 맞춰 마법·함정 존을 포함한 필드에서 적용합니다. 기존 샘플 덱은 보존했습니다.

새 팩 재생성: `python3 tools/build_alpha23.py`.

Alpha 0.8~0.22 팩과 문서는 과거 기록으로 보존합니다.
