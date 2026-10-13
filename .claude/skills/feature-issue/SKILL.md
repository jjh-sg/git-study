---
name: feature-issue
description: 새 기능(feat 커밋)을 추가할 때 GitHub 이슈를 자동으로 등록하고 라벨을 붙인다. Claude가 feat 커밋을 만든 직후 실행하며, "이슈 만들어줘", "기능 이슈 등록해줘" 같은 요청에도 사용한다. gh CLI를 사용한다.
---

# 기능 추가 이슈 자동 등록

`feat` 커밋이 만들어진 직후 같은 커밋 내용으로 GitHub 이슈를 등록하고 라벨을 붙인다. 사용자 확인 없이 등록하고, 결과 URL을 보고한다.
라벨 표는 [references/labels.md](references/labels.md)를 따른다.

## 언제 실행하나

- Claude가 `feat(...)` 커밋을 만들었을 때 자동으로 실행한다.
- 사용자가 "이슈 만들어줘", "기능 이슈 등록해줘"라고 요청하면 최신 `feat` 커밋 기준으로 실행한다.
- `docs:`, `fix:`, `chore:` 등 `feat`가 아닌 커밋에는 실행하지 않는다.

## 절차

1. **인증과 대상 확인**
   - `gh auth status`가 실패하면 중단하고 `gh auth login`을 안내한다.
   - `gh repo view --json nameWithOwner --jq .nameWithOwner`로 대상 저장소를 얻는다. 하드코딩하지 않는다.

2. **커밋 정보 읽기**
   - `git log -1 --format=%H%n%s%n%b`로 커밋 제목과 본문을 읽는다.
   - `git show --stat --format= HEAD`로 변경 파일을 읽는다.
   - 제목이 `feat(scope): 요약` 형식이 아니면 중단하고 사용자에게 알린다.

3. **중복 확인**
   - `gh issue list --state all --search "<커밋 요약>" --json number,title`로 같은 제목의 이슈가 있는지 본다.
   - 있으면 등록하지 않고 기존 이슈 번호를 보고한다.

4. **제목과 본문 작성 (한글)**
   - 제목: `[기능] <커밋 요약>`
   - 본문 구성:
     - `## 배경`: 왜 필요한지. 커밋 본문의 "왜"를 옮긴다.
     - `## 변경 내용`: 변경 파일과 한 줄 설명.
     - `## 완료 조건`: 체크박스 목록. 변경 내용에서 검증 가능한 항목만 쓴다.
   - 본문은 scratchpad 임시 파일에 UTF-8로 쓰고, 저장소 안에는 임시 파일을 남기지 않는다.

5. **라벨 결정**
   - `gh label list --limit 200 --json name --jq '.[].name'`로 저장소의 라벨을 가져온다.
   - 기본으로 `enhancement`를 붙인다. 존재하지 않으면 붙이지 않는다.
   - 스코프 라벨은 `references/labels.md`의 경로 매핑으로 정한다. 저장소에 있는 라벨만 붙인다.
   - 필요한 라벨이 저장소에 없으면 **이슈를 라벨 없이 먼저 등록**하고, 누락 라벨을 목록으로 보여주며 생성 승인을 묻는다. 승인 없이는 `gh label create`를 실행하지 않는다.

6. **이슈 등록**
   ```bash
   gh issue create --title "<제목>" --body-file <scratchpad 파일> --label "<라벨1>,<라벨2>"
   ```
   - PowerShell 5.1에서 한글 인자가 깨지므로 제목과 본문 모두 파일 또는 변수 경로로 넘긴다.
   - 실패하면 원인을 보고한다. 커밋은 되돌리지 않는다.

7. **결과 보고**
   - 대상 저장소, 이슈 URL, 붙은 라벨, 라벨 없이 남은 항목을 보고한다.
   - `gh issue view <번호> --json title,labels,url`로 실제 등록 결과를 확인한다.

## 하지 않는 것

- 커밋을 amend하거나 커밋 메시지에 이슈 번호를 넣지 않는다.
- 저장소에 없는 라벨을 사용자 승인 없이 만들지 않는다.
- 다른 저장소에 등록하지 않는다. 대상은 항상 현재 저장소의 `origin`이다.
- 이슈를 닫거나 수정하지 않는다. 등록만 한다.
- 이슈 번호를 PR 연결에 자동으로 쓰지 않는다. 연결 여부는 사용자에게 묻는다.

## 참고

- 라벨 목록과 경로 매핑은 `references/labels.md`에 있다. 새 라벨이 생기면 거기에 한 줄 추가한다.
- 커밋 컨벤션은 `.claude/skills/data-commit-message/references/convention.md`를 따른다.
