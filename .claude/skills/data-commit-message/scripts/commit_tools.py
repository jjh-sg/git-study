#!/usr/bin/env python3
"""커밋 그룹화와 메시지 검증 도구 (git-study 저장소 기준 매핑).

사용법:
  python commit_tools.py group --source staged          # 스테이징된 파일
  python commit_tools.py group --source status          # 수정·추가·삭제·미추적 파일 전체
  python commit_tools.py group --source commit:<rev>    # 이미 만든 커밋의 파일 (리뷰용)
  python commit_tools.py check "<제목 줄>"               # 제목 한 줄만 검사
  python commit_tools.py check --file <메시지파일>       # 전체 메시지 검사

경로 규칙을 바꾸려면 RULES만 수정한다. 규칙은 위에서부터 처음 매칭되는 것을 쓴다.
"""
import argparse
import fnmatch
import re
import subprocess
import sys
from collections import OrderedDict

sys.stdout.reconfigure(encoding="utf-8")

ALLOWED_TYPES = ["data", "analysis", "viz", "docs", "feat", "fix",
                 "refactor", "perf", "test", "chore", "revert"]
# 의존 순서: 데이터 생성 → 분석 → 시각화 → 문서 → 기타
TYPE_ORDER = {t: i for i, t in enumerate(ALLOWED_TYPES)}

# (glob 패턴, 타입, 스코프). 스코프가 "*stem"이면 파일명에서 접두어를 뺀 이름을 쓴다.
RULES = [
    ("make_dummy.py", "data", "generator"),
    ("README_data.md", "docs", "data"),
    ("analysis/analyze_*.py", "analysis", "*stem"),
    ("analysis/*.xlsx", "analysis", "peak"),
    ("analysis/README.md", "docs", "analysis"),
    ("dashboard/build_*.py", "viz", "dashboard"),
    ("dashboard/index.html", "viz", "dashboard"),
    ("dashboard/README.md", "docs", "dashboard"),
    ("*.xlsx", "data", "dummy"),
    ("README.md", "docs", None),
    (".gitignore", "chore", None),
]
DEFAULT_RULE = ("chore", None)

SUBJECT_RE = re.compile(
    r"^(?P<type>[a-z]+)(\((?P<scope>[a-z0-9가-힣_\-]+)\))?(?P<bang>!)?: (?P<summary>.+)$"
)


def git(*args):
    result = subprocess.run(
        ["git", "-c", "core.quotepath=off", *args],
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        sys.exit(f"git {' '.join(args)} 실패: {result.stderr.strip()}")
    return result.stdout


def collect_files(source):
    """(상태, 경로) 목록을 돌려준다. 상태는 A/M/D/R 등 git 표기."""
    if source == "staged":
        lines = git("diff", "--cached", "--name-status").splitlines()
    elif source == "status":
        entries = []
        for line in git("status", "--porcelain=v1", "-uall").splitlines():
            code, path = line[:2].strip() or "M", line[3:]
            entries.append(f"{code}\t{path}")
        lines = entries
    elif source.startswith("commit:"):
        rev = source.split(":", 1)[1]
        lines = git("show", "--name-status", "--format=", rev).splitlines()
    else:
        sys.exit("--source는 staged, status, commit:<rev> 중 하나여야 합니다.")

    files = []
    for line in lines:
        parts = line.split("\t")
        status = parts[0][0]
        path = parts[-1]  # 이름 변경(R)이면 새 경로를 쓴다
        files.append((status, path))
    return files


def classify(path):
    """파일 경로를 (타입, 스코프)로 바꾼다."""
    for pattern, ctype, scope in RULES:
        if fnmatch.fnmatch(path, pattern):
            if scope == "*stem":
                stem = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
                scope = re.sub(r"^(analyze|build)_", "", stem)
            return ctype, scope
    return DEFAULT_RULE


def group(files):
    groups = OrderedDict()
    for status, path in files:
        key = classify(path)
        groups.setdefault(key, []).append((status, path))
    return sorted(groups.items(),
                  key=lambda kv: TYPE_ORDER.get(kv[0][0], len(TYPE_ORDER)))


def cmd_group(args):
    files = collect_files(args.source)
    if not files:
        print("변경 파일이 없습니다. (--source staged는 스테이징된 파일만 봅니다)")
        return
    groups = group(files)
    for step, ((ctype, scope), items) in enumerate(groups, 1):
        head = f"{ctype}({scope})" if scope else ctype
        print(f"[{step}] {head}  — 파일 {len(items)}개")
        for status, path in items:
            print(f"      {status}  {path}")
        if len(items) > 10:
            print("      ! 10개 초과: 더 잘게 나눌 수 있는지 검토")
    print(f"\n총 {len(groups)}개 그룹. 커밋 순서는 위에서 아래로 권장.")


def check_subject(subject):
    problems, warnings = [], []
    m = SUBJECT_RE.match(subject)
    if not m:
        problems.append("형식이 `<type>(<scope>)[!]: <요약>`과 맞지 않습니다.")
    else:
        if m.group("type") not in ALLOWED_TYPES:
            problems.append(f"허용되지 않은 타입: {m.group('type')} "
                            f"(허용: {', '.join(ALLOWED_TYPES)})")
        if subject.endswith("."):
            warnings.append("제목 끝에 마침표를 쓰지 않습니다.")
    length = len(subject)
    if length > 72:
        problems.append(f"제목이 {length}자입니다. 72자 이하로 줄이세요.")
    elif length > 50:
        warnings.append(f"제목이 {length}자입니다. 50자 이내를 권장합니다.")
    return problems, warnings


def check_message(text):
    lines = text.rstrip("\n").splitlines()
    problems, warnings = check_subject(lines[0] if lines else "")
    if len(lines) > 1 and lines[1].strip():
        problems.append("제목과 본문 사이에 빈 줄이 없습니다.")
    for i, line in enumerate(lines[2:], 3):
        if len(line) > 72 and not line.startswith(("Run:", "Data:", "Refs:")):
            warnings.append(f"{i}행이 {len(line)}자입니다. 72자 이내를 권장합니다.")
    return problems, warnings


def cmd_check(args):
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read()
        problems, warnings = check_message(text)
    else:
        problems, warnings = check_subject(args.message)
    for w in warnings:
        print(f"경고: {w}")
    for p in problems:
        print(f"오류: {p}")
    if not problems:
        print("통과")
    sys.exit(1 if problems else 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_group = sub.add_parser("group", help="변경 파일을 타입·스코프별로 묶기")
    p_group.add_argument("--source", default="staged",
                         help="staged | status | commit:<rev>")
    p_group.set_defaults(func=cmd_group)

    p_check = sub.add_parser("check", help="커밋 메시지 형식 검사")
    p_check.add_argument("message", nargs="?", default="", help="제목 한 줄")
    p_check.add_argument("--file", help="메시지 파일 경로 (전체 검사)")
    p_check.set_defaults(func=cmd_check)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
