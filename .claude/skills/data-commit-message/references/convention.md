# 데이터 분석 커밋 컨벤션

이 문서는 `git-study` 저장소(버스 노선·하차 데이터 분석)를 기준으로 한 커밋 규칙이다.
Conventional Commits 1.0.0의 `<type>(<scope>)!: <subject>` 골격을 따르고, 데이터 분석 작업 단위(데이터 생성 → 분석 → 시각화 → 문서)에 맞게 타입과 스코프를 정했다.

## 1. 기본 형식

```
<type>(<scope>)[!]: <요약>

- 무엇을: 변경 내용
- 왜: 변경 이유
- 영향: 산출물·수치 변화 (데이터 분석 커밋은 필수 권장)

Run: <산출물을 재현하는 명령>
Data: <데이터 기간·버전·시드, 더미 여부>
Refs: <브랜치 또는 이슈>
BREAKING CHANGE: <스키마·산출 형식이 깨지는 경우만>
```

| 부분 | 규칙 |
|---|---|
| 제목 | 50자 이내 권장, 72자 초과 금지. 한글 요약, 마침표 없음 |
| 제목 어미 | 명사형 종결 권장: `추가`, `수정`, `정리`, `갱신`, `보정`, `생성` |
| 빈 줄 | 제목과 본문 사이, 본문과 푸터 사이에 반드시 한 줄 |
| 본문 | 한 줄 72자 이내, 글머리표는 `- ` |
| 푸터 | `Run:`, `Data:`, `Refs:`, `BREAKING CHANGE:` 순서 |

타입과 스코프는 Conventional Commits 관례대로 영어 소문자, 제목 요약과 본문은 한글로 쓴다.
기존 이력은 영어 명령형("Add ...")이라 전환 시점은 팀 합의가 필요하다. 이 문서는 한글 요약을 기본으로 한다.

## 2. 타입 (type)

| 타입 | 쓰는 경우 | 예시 |
|---|---|---|
| `data` | 데이터 생성·스키마·전처리 로직 변경 (산출 데이터가 바뀜) | `data(generator): 더미 데이터 v2 옵션 및 현실성 보정 추가` |
| `analysis` | 분석 로직 또는 분석 결과 산출물 변경 | `analysis(peak): 피크 시간대 혼잡도 분석 추가` |
| `viz` | 대시보드·차트·HTML 산출물 변경 | `viz(dashboard): 노선별 하차 현황 대시보드 추가` |
| `docs` | README, 방법론, 사용법 문서만 변경 (코드 동작 불변) | `docs(data): 생성기 v2 옵션 표 정리` |
| `feat` | 위 타입에 속하지 않는 새 기능 (도구·스크립트 등) | `feat(tools): 커밋 그룹화 스크립트 추가` |
| `fix` | 계산·집계·필터·경로 등 잘못된 동작 수정 | `fix(analysis): 주말 일평균 분모 오류 수정` |
| `refactor` | 동작과 결과가 같은 구조 개선 | `refactor(generator): 노선 생성 함수 분리` |
| `perf` | 실행 시간·메모리 개선 | `perf(dashboard): 대용량 JSON 인라인 최적화` |
| `test` | 검증 코드·샘플 데이터 검증 | `test(generator): 시드 재현성 검증 추가` |
| `chore` | `.gitignore`, 의존성, 설정 | `chore: xlsx 산출물 추적 정책 정리` |
| `revert` | 이전 커밋 되돌림 (본문에 원 커밋 해시) | `revert: analysis(peak) 결과 갱신 취소` |

구분 기준: 산출 **수치**가 바뀌면 `data` 또는 `analysis`, 산출 **화면·형식**만 바뀌면 `viz`, 문장만 바뀌면 `docs`.

## 3. 스코프 (scope)

스코프는 파이프라인 단계 또는 모듈 이름이다. 파일 경로에서 기계적으로 정한다.

| 경로 | 타입 | 스코프 |
|---|---|---|
| `make_dummy.py` | data | generator |
| `analysis/analyze_<name>.py` | analysis | `<name>` (예: peak) |
| `analysis/*.xlsx` (분석 결과) | analysis | 생성 스크립트 스코프와 동일 |
| `analysis/README.md` | docs | analysis |
| `dashboard/build_dashboard.py` | viz | dashboard |
| `dashboard/index.html` (생성물) | viz | dashboard |
| `dashboard/README.md` | docs | dashboard |
| `README_data.md` | docs | data |
| `README.md` (루트) | docs | 없음 |
| `.gitignore` | chore | 없음 |

스코프가 없어도 되는 경우 괄호를 생략한다. 예: `docs: ...`

## 4. 묶음 규칙 (무엇을 한 커밋에 넣는가)

1. **같은 (타입, 스코프) = 한 커밋.** 파일 하나가 여러 그룹에 걸치면 가장 가까운 산출 단계에 둔다.
2. **의존 순서로 커밋한다.** `data` → `analysis` → `viz` → `docs` → `chore`. 상위 단계가 먼저 있어야 하위 커밋의 `Run:`이 재현된다.
3. **로직과 재생성 산출물을 같은 커밋에 넣을 수 있다.** 단, 산출물이 로직의 직접 결과일 때만 묶고, 본문 `Run:`에 재생성 명령을 적는다. 예: `cd6459c`처럼 분석 결과 xlsx·HTML·README 수치를 함께 갱신하는 경우.
4. **데이터 값 변경과 코드 변경을 섞지 않는다.** 더미 데이터 시드·기간을 바꾸는 커밋은 `data` 타입으로 따로 한다.
5. **문서만 바뀐 경우 `docs`로 분리한다.** 코드 커밋에 README 수치 갱신이 딸려 오면 그 수치가 산출물과 일치할 때만 같이 넣는다.
6. **한 그룹이 10개 파일을 넘으면 쪼갤 수 있는지 검토한다.**
7. **merge 커밋은 Git 기본 메시지를 유지한다** (`Merge branch 'feat/data-v2'`). 필요하면 `Merge feat/x: <요약>`로 쓴다.

## 5. 데이터 분석 전용 규칙

- **수치 변화 명시.** 분석 결과가 바뀌면 `영향:`에 이전 값 → 새 값을 적는다.
  예: `영향: 08시 하차 18,555명(11.2%) 유지, 정류소 TOP1 종로3가 21,299명`
- **더미 데이터 표기.** 생성 데이터를 쓰는 커밋은 `Data:`에 "더미"와 기간·시드를 적는다.
  예: `Data: 더미 데이터, 2026-09-01~09-07, seed=42`
- **재현 명령 필수.** 산출물을 바꾸는 커밋은 `Run:`에 실행 명령을 적는다.
  예: `Run: python analysis/analyze_peak.py`
- **스키마 변경은 BREAKING.** 컬럼 추가·삭제·이름 변경, 시트 구조 변경은 제목에 `!`를 붙이고 `BREAKING CHANGE:` 푸터를 쓴다.
  예: `data(generator)!: 하차데이터 시트에 요일 컬럼 추가`
- **Git에서 추적하지 않는 파일.** `.gitignore`의 `*.xlsx` 대상(예: `버스_노선_하차_더미데이터.xlsx`)은 커밋하지 않는다. 커밋 메시지에는 "xlsx는 gitignore 대상" 같은 설명 대신 재현 명령(`Run:`)만 남긴다.
- **시드와 버전.** 생성기 옵션이 기본값과 다르면 `Data:`에 옵션을 적는다. 예: `Data: v2, --routes 12 --seed 7`
- **작업 브랜치 표기.** `Refs:`에 `feat/data-v2`처럼 브랜치명을 적는다.

## 6. 좋은 예와 나쁜 예

좋은 예:

```
analysis(peak): 피크 시간대 하차 혼잡도 분석 추가

- 무엇을: 정류소×시간대 하차 합계를 분위수로 등급화(상/중/하)
- 왜: 출퇴근 피크 집중 정류소 파악
- 영향: 08시 18,555명(11.2%), 18시 17,552명(10.6%) 최대

Run: python analysis/analyze_peak.py
Data: 더미 데이터, 2026-09-01~09-07, seed=42
Refs: feat/analysis-peak
```

나쁜 예와 개선:

| 나쁜 예 | 문제 | 개선 |
|---|---|---|
| `update` | 타입·대상·내용 없음 | `analysis(peak): 혼잡도 등급 분위수 기준 보정` |
| `Fix stuff` | 무엇을 고쳤는지 불명 | `fix(dashboard): 노선 드롭다운 전체 선택 시 KPI 미갱신 수정` |
| `make_dummy v2: argparse, realism, refactor` | 타입 없음, 여러 변경 혼합 | `data(generator): 더미 데이터 v2 옵션화` 와 `refactor(generator): ...` 로 분리 |
| `분석 결과 수정 및 대시보드 갱신 및 README 수정` | 세 그룹이 한 커밋, 수치 없음 | `analysis`, `viz`, `docs` 세 커밋으로 분리하고 `영향:` 명시 |

## 7. 이 저장소에서 확인된 점

- 전체 커밋 10개 중 본문이 있는 커밋은 없다. 이 문서 도입 후 본문과 푸터를 채운다.
- `.gitignore`는 `*.xlsx`를 제외하지만 `analysis/혼잡도_분석결과.xlsx`는 추적 중이다(커밋 `f4a05f0`). 추적 정책은 팀 확인이 필요하다.
- 커밋 작성자가 `공용 PC`와 `jjh-sg`로 섞여 있다. 본인 식별 정보는 설정하지 않는다.
