# Catastrophe

MDPro3 커스텀 카드군 「카타스트로피」.

현재 테스트 팩: **Alpha 0.24 — 융합 소재 조건·선구자·재앙왕 효과 변경**

- [Alpha 0.24 YPK 다운로드](https://github.com/sudun-1231/Catastrophe/raw/refs/heads/codex/alpha09-fusion-fix/Catastrophe_MDPro3_alpha_v24_revised_effects.ypk)
- [변경 사항·검증 범위](EFFECT_DEBUG_ALPHA24.md)

MDPro3를 종료한 뒤 이전 Catastrophe 팩을 백업하고 `Expansions`에는 최신 팩 하나만 넣어 다시 시작하세요. 공개 MDPro3 미러의 네이티브 코어와 동봉 Lua에서 총 239개 시나리오를 검증했습니다. 사용 중인 클라이언트 버전 및 Unity UI에서의 검증은 별도입니다.

프레이·랜서·가디언·매지션·해츨링·선구자·용기사의 묘지 / 제외 융합에서 발동 카드 자신을 필수 소재로 지정하는 제한을 삭제했습니다. 선구자는 일반 / 특수 소환 시 테마 카드 전체를 검색합니다. 재앙왕은 자신의 패 효과로 특수 소환한 뒤 새 체인에서 선택적으로 카드 1장을 대상으로 제외합니다.

현재 카드 21장. 기존 능력치·이미지·샘플 덱을 보존했습니다. 파수꾼은 기존 정상 동작을 유지합니다. 철회된 Alpha 0.23 변경은 포함하지 않습니다.

새 팩 재생성: `python3 tools/build_alpha24.py`.

Alpha 0.8~0.22 팩과 문서는 과거 기록으로 보존합니다.
