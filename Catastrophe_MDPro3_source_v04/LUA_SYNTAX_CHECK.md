# 카타스트로피 Alpha 0.3 Lua 문법 검사

- 검사일: 2026-11-13
- 검사 대상: `script/c98013001.lua` ~ `script/c98013014.lua` (14개)
- 검사 방식: 시스템 `liblua5.4.so.0`의 `luaL_loadbufferx(..., mode="t")`를 이용한 Lua 5.4 구문 분석. 파일을 실행하지 않았음.
- 결과: **14/14 PASS**, 구문 오류 0건.

## 파일별 결과

- `c98013001.lua`: PASS
- `c98013002.lua`: PASS
- `c98013003.lua`: PASS
- `c98013004.lua`: PASS
- `c98013005.lua`: PASS
- `c98013006.lua`: PASS
- `c98013007.lua`: PASS
- `c98013008.lua`: PASS
- `c98013009.lua`: PASS
- `c98013010.lua`: PASS
- `c98013011.lua`: PASS
- `c98013012.lua`: PASS
- `c98013013.lua`: PASS
- `c98013014.lua`: PASS

## 범위 및 주의 사항

- MDPro3 실행 환경, Project Ignis `Fusion` API, `aux` 및 `Duel` 함수의 존재·시그니처와 효과 동작은 검사하지 않았음.
- 미구현 `TODO`와 로직 문제는 문법 검사에서 검출되지 않음.
- `Fusion.SummonEffTG/OP`, `Fusion.ForcedHandler` 등을 사용하는 스크립트는 엔진 버전과 라이브러리 호환성을 별도로 확인해야 함.
- 본 결과는 게임에서 정상 동작한다는 인증이 아님.
