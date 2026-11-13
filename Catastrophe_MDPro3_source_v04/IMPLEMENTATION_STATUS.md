# 카타스트로피 MDPro3 Alpha 0.3 — 개발 상태

**미완성 / MDPro3에서 실행 검증되지 않은 개발 빌드**입니다. 모든 효과가 작동한다고 보증하지 않습니다.

## 새로 작업한 부분
- Rebuilt corrected CDB text for Dragon Knight and Golem
- Added 2/3 named archetype materials for level 8 Dragon Knight and level 12 Catastrophe fusion
- Drafted shared fusion-trigger code on 5 main-deck dragons and Dragon Knight for graveyard/banishment; includes banished material handling
- Drafted Golem self-recycling and own-GY/face-up banishment card recovery
- Kept Golem forced Special Summon destruction trigger

## 미완료 및 호환성 문제
- Golem variable-number material recipe (not yet registered)
- Fusion helper compatibility with installed MDPro3 engine
- All deck destruction to Special Summon mechanics
- Remaining magics/traps, boss effects, counter-trap recursion
- Full in-game effect timing and operation tests
- Artworks absent

## 해석 및 주의사항
- Prototype code not executed in MDPro3
- Merged Korean name variants mapped to setcode 0xfcb provisionally
- Golem retrieval assumes own GY/banished cards; source does not name controller
- Fusion helper relies on Project Ignis Fusion API, could differ by MDPro3 build

## 보존 사항
- 14장 및 카드 ID 98013001~98013014 유지
- 사용자가 정한 원본 카드 효과 문구는 CDB `texts.desc`와 ORIGINAL_SOURCE.txt에 보존
- 기존 게임 데이터 백업 후 테스트 필요
- Project Ignis 참고: https://github.com/ProjectIgnis/CardScripts/blob/master/official/c74078255.lua
