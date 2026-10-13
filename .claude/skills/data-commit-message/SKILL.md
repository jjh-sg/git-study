---
name: data-commit-message
description: 데이터 분석 저장소(git-study)의 커밋 컨벤션에 맞춰 변경 파일을 타입·스코프별로 묶고 커밋 메시지를 작성·검사한다. "커밋 메시지 써줘", "변경사항 커밋 나눠줘", "커밋 묶어줘", "commit 준비해줘" 같은 요청에 사용한다.
---

# 데이터 분석 커밋 메시지 작성

변경 파일을 **같은 타입·스코프끼리** 묶고, 데이터 분석 컨벤션(수치 영향, 재현 명령, 더미 데이터 표기)을 담은 커밋 메시지를 만든다.
규칙 상세는 [references/convention.md](references/convention.md)를 따른다.

## 절차

1. **상태 확인**
   - `git status --short`로 변경 파일을 본다.
   - 이미 스테이징된 파일이 있으면 먼저 사용자에게 알린다. 그대로 쓸지 `git reset`으로 비울지 묻는다.

2. **그룹화**
   ```bash
   python .claude/skills/data-commit-message/scripts/commit_tools.py group --source status
   ```
   - 스테이징 후 확인하려면 `--source staged`를 쓴다.
   - 이미 만든 커밋을 리뷰용으로 다시 보려면 `--source commit:<해시>`를 쓴다.

3. **그룹별 변경 내용 파악**
   - `git diff -- <파일들>`로 텍스트 파일 변경을 읽는다.
   - `.xlsx`는 바이너리라 diff가 안 보인다. 대신 생성 명령을 확인하고, 필요하면 시트 요약을 비교한다.
   - `analysis/README.md`나 `dashboard/README.md`에 적힌 수치가 있으면 이전 값과 새 값을 비교해 `영향:`에 쓴다.

4. **메시지 작성**
   - 형식: `<type>(<scope>)[!]: <한글 요약>` + 본문(무엇을/왜/영향) + 푸터(`Run:`, `Data:`, `Refs:`, `BREAKING CHANGE:`).
   - 제목은 50자 이내, 명사형 종결(추가·수정·정리·갱신·보정).
   - 데이터 분석 커밋은 `영향:`(수치 변화)과 `Run:`(재현 명령)을 가능한 한 채운다.
   - 생성 데이터를 쓰면 `Data:`에 "더미", 기간, 시드를 적는다.
   - 스키마가 바뀌면 `!`를 붙이고 `BREAKING CHANGE:`를 쓴다.

5. **검사**
   ```bash
   python .claude/skills/data-commit-message/scripts/commit_tools.py check --file <메시지파일>
   ```
   - 메시지 파일은 scratchpad 임시 경로에 쓴다. 저장소 안에 임시 파일을 남기지 않는다.
   - 오류가 있으면 고치고 다시 검사한다.

6. **계획 제시와 승인**
   - 그룹 순서, 각 그룹의 파일, 전체 메시지를 보여준다.
   - 사용자가 승인하기 전에는 커밋하지 않는다.

7. **커밋 실행 (승인 후)**
   - 그룹마다 `git add -- <그룹 파일들>` 후 `git commit -F <메시지파일>`을 실행한다.
   - 그룹을 바꾸는 요청이 있으면 다시 그룹화하고 승인받는다.
   - 완료 후 `git log --oneline -n <개수>`로 결과를 보여준다.

## 하지 않는 것

- 사용자 승인 없이 커밋하거나 `git push`하지 않는다.
- `git add -A`나 `git add .`로 한꺼번에 담지 않는다. 그룹 파일만 명시한다.
- `.gitignore` 대상(`*.xlsx` 등)을 새로 추가하지 않는다. 추적 중인 산출물을 바꾸는 경우에만 커밋한다.
- 작성자 정보(`user.name`, `user.email`)를 설정하거나 바꾸지 않는다.

## 참고

- 그룹화 기준과 경로 매핑은 `scripts/commit_tools.py`의 `RULES`에 있다. 새 파일 종류가 생기면 여기에 한 줄 추가한다.
- 컨벤션 근거: Conventional Commits 1.0.0 골격(`type(scope)!: subject`, 푸터)을 쓰고, 타입과 스코프는 데이터 분석 파이프라인(data → analysis → viz → docs)에 맞췄다.
