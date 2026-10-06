# #5699 독립 검증

기술 판정은 **해결 확인**이다. 초안 판정은 **유지**다. 아래에 한정한 관찰이며 최초 수정 커밋을 확정한 결과가 아니다.

[원본 이슈](https://github.com/RustPython/RustPython/issues/5699)는 2026-10-05T16:10:27.709506+00:00 UTC 조회 시 **open**였다. 본문과 댓글 0개를 확인했다. 현재 열린 상태이므로 기술적으로 해결된 범위의 종료 검토 요청은 의미가 있다.

원문은 class pattern codegen, frame.f_builtins, sys.stdlib_module_names, except* codegen 네 가지를 색상 traceback의 blocker로 나열한다. 본문에 실행 코드는 없다. 모두 실제로 사용하고 실제 미처리 예외 출력까지 확인해야 한다.

초안은 네 blocker의 동작, traceback API 및 실제 uncaught 예외 네 경로의 ANSI color와 builtin/stdlib suggestion을 주장한다.

class pattern이 Point(3,4)에서 4를 추출했고 f_builtins의 builtin 및 custom dict 동일성, stdlib names frozenset과 필수 이름, ExceptionGroup의 ValueError/TypeError 분리가 assert를 통과했다. traceback의 class-pattern helper도 호출했다. 실제 builtin typo/미import io/0으로 나누기/ExceptionGroup은 양쪽 각 4개 프로세스 모두 정상 예외 종료 1이다. 여덟 stderr에 ANSI가 있고 각 pair는 내용까지 정확히 일치한다. API plain/colorize=True의 네 경로도 assert를 통과했다.

실행 환경은 [슬롯 B 출처·환경 기록](../../agent-b/environment/IDENTITY.md)과 같다. 핵심적으로 RustPython은 SHA-256 d5742929…의 x86_64 재사용 산출물, CPython은 3.14.6 arm64다. B에서 실행하지만 실제 stdlib는 주 작업 폴더의 Lib를 우선 로드하며 2,324개 추적 파일의 목표 커밋 일치를 확인했다. 목표 출처는 embedded f39b054b9 배너와 보존 빌드/복사 기록·동일 산출물 해시로 뒷받침하며, 새 재현 빌드로 완전 입증한 것은 아니다.

아래 파일들을 IN 디렉터리에 해당 이름으로 저장하면 표시된 검증을 실행할 수 있다. 원문·보정·확장 입력은 파일로 구분한다.

실행 명령의 경로 변수와 환경은 다음과 같다. 실제 argv와 모든 환경 값, 시작·종료 시간은 각 실행 기록에 있다. 각 명령은 controller.py의 timeout/process-group 정리 아래 순차 실행했다.

```sh
cd <slot-b-source>
RP=<survey>/.build/slot-b/saved/current-f39-x86/rustpython
CP=<home>/.local/bin/python3
IN=<closure24-audit>/agent-b/inputs
export RUSTPYTHONPATH=<slot-b-source>/Lib
export PYTHONDONTWRITEBYTECODE=1 LANG=C.UTF-8 LC_ALL=C.UTF-8 LC_CTYPE=C.UTF-8 TERM=dumb
export TMPDIR=<closure24-audit>/agent-b/environment/tmp
export TMP="$TMPDIR" TEMP="$TMPDIR"
export PYTHON_HISTORY=<closure24-audit>/agent-b/environment/history
export RUSTPYTHON_HISTORY="$PYTHON_HISTORY"
export SYMPY_SITE=<survey>/verification-tools/package-history-4506-original/site
```

입력 파일 `5699-draft-0.py` ([저장된 파일](../../agent-b/inputs/5699-draft-0.py.txt)):

```python
import sys
import json
import builtins
import traceback
import ast


class Point:
    __match_args__ = ("x", "y")

    def __init__(self, x, y):
        self.x, self.y = x, y


match Point(3, 4):
    case Point(3, y=answer):
        assert answer == 4
    case _:
        raise AssertionError("class pattern did not execute")

assert sys._getframe().f_builtins["len"] is len
custom = {"__builtins__": {"custom_marker": 42}, "frame": sys._getframe}
exec("actual = frame().f_builtins", custom)
assert custom["actual"] is custom["__builtins__"]
assert isinstance(sys.stdlib_module_names, frozenset)
assert {"sys", "io", "_io", "traceback"} <= sys.stdlib_module_names

handled = []
try:
    raise ExceptionGroup("split", [ValueError("v"), TypeError("t")])
except* ValueError as exc:
    handled.append(("value", len(exc.exceptions)))
except* TypeError as exc:
    handled.append(("type", len(exc.exceptions)))
assert handled == [("value", 1), ("type", 1)]

anchors = traceback._extract_caret_anchors_from_line_segment("x + y")
assert anchors is not None, "actual traceback class-pattern branch failed"
records = {
    "class_match": answer,
    "builtins": True,
    "stdlib_module_names": True,
    "except_star": handled,
    "anchors": list(anchors),
}


def zero():
    return 1 / 0


def builtins_typo():
    return ZeroDivisionErrrrr


def stdlib_missing():
    return io.StringIO()


def group():
    raise ExceptionGroup("colored group", [ValueError("v"), TypeError("t")])


for label, function, needle in (
    ("zero", zero, "ZeroDivisionError"),
    ("builtins_typo", builtins_typo, "Did you mean: 'ZeroDivisionError'?"),
    ("stdlib_missing", stdlib_missing, "forget to import 'io'"),
    ("group", group, "ExceptionGroup"),
):
    try:
        function()
    except Exception as exc:
        plain = "".join(traceback.format_exception(exc, colorize=False))
        colored = "".join(traceback.format_exception(exc, colorize=True))
        assert needle in plain, (label, plain)
        assert "\x1b[" in colored, (label, colored)
        assert needle in colored or label == "zero", (label, colored)
        records[label] = {"plain": plain, "colored": colored}
print(json.dumps(records, ensure_ascii=True, indent=2))
```

입력 파일 `5699-draft-1.py` ([저장된 파일](../../agent-b/inputs/5699-draft-1.py.txt)):

```python
import sys

if sys.argv[1] == "builtin":
    ZeroDivisionErrrrr
elif sys.argv[1] == "stdlib":
    io.StringIO()
elif sys.argv[1] == "zero":
    1 / 0
else:
    raise ExceptionGroup("uncaught group", [ValueError("v"), TypeError("t")])
```

```sh
"$RP" -B "$IN/5699-draft-0.py"
"$CP" -B "$IN/5699-draft-0.py"
PYTHON_COLORS=1 FORCE_COLOR=1 "$RP" -B "$IN/5699-draft-1.py" builtin
PYTHON_COLORS=1 FORCE_COLOR=1 "$CP" -B "$IN/5699-draft-1.py" builtin
PYTHON_COLORS=1 FORCE_COLOR=1 "$RP" -B "$IN/5699-draft-1.py" stdlib
PYTHON_COLORS=1 FORCE_COLOR=1 "$CP" -B "$IN/5699-draft-1.py" stdlib
PYTHON_COLORS=1 FORCE_COLOR=1 "$RP" -B "$IN/5699-draft-1.py" zero
PYTHON_COLORS=1 FORCE_COLOR=1 "$CP" -B "$IN/5699-draft-1.py" zero
PYTHON_COLORS=1 FORCE_COLOR=1 "$RP" -B "$IN/5699-draft-1.py" group
PYTHON_COLORS=1 FORCE_COLOR=1 "$CP" -B "$IN/5699-draft-1.py" group
```

실행별 결과와 입력 링크는 다음과 같다. stdout/stderr 원문은 JSON 기록에 연결되어 있다.

- [5699-blockers-rp](../../agent-b/records/5699-blockers-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/5699-draft-0.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [5699-blockers-cp](../../agent-b/records/5699-blockers-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/5699-draft-0.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [5699-uncaught-builtin-rp](../../agent-b/records/5699-uncaught-builtin-rp.json): 종료 1, timeout False; [입력](../../agent-b/inputs/5699-draft-1.py.txt). 실제 미처리 builtin 예외: 정상 예외 종료 1, ANSI 색상 존재, 해당 예외/제안 확인. 프로세스 충돌이 아니다.
- [5699-uncaught-builtin-cp](../../agent-b/records/5699-uncaught-builtin-cp.json): 종료 1, timeout False; [입력](../../agent-b/inputs/5699-draft-1.py.txt). 실제 미처리 builtin 예외: 정상 예외 종료 1, ANSI 색상 존재, 해당 예외/제안 확인. 프로세스 충돌이 아니다.
- [5699-uncaught-stdlib-rp](../../agent-b/records/5699-uncaught-stdlib-rp.json): 종료 1, timeout False; [입력](../../agent-b/inputs/5699-draft-1.py.txt). 실제 미처리 stdlib 예외: 정상 예외 종료 1, ANSI 색상 존재, 해당 예외/제안 확인. 프로세스 충돌이 아니다.
- [5699-uncaught-stdlib-cp](../../agent-b/records/5699-uncaught-stdlib-cp.json): 종료 1, timeout False; [입력](../../agent-b/inputs/5699-draft-1.py.txt). 실제 미처리 stdlib 예외: 정상 예외 종료 1, ANSI 색상 존재, 해당 예외/제안 확인. 프로세스 충돌이 아니다.
- [5699-uncaught-zero-rp](../../agent-b/records/5699-uncaught-zero-rp.json): 종료 1, timeout False; [입력](../../agent-b/inputs/5699-draft-1.py.txt). 실제 미처리 zero 예외: 정상 예외 종료 1, ANSI 색상 존재, 해당 예외/제안 확인. 프로세스 충돌이 아니다.
- [5699-uncaught-zero-cp](../../agent-b/records/5699-uncaught-zero-cp.json): 종료 1, timeout False; [입력](../../agent-b/inputs/5699-draft-1.py.txt). 실제 미처리 zero 예외: 정상 예외 종료 1, ANSI 색상 존재, 해당 예외/제안 확인. 프로세스 충돌이 아니다.
- [5699-uncaught-group-rp](../../agent-b/records/5699-uncaught-group-rp.json): 종료 1, timeout False; [입력](../../agent-b/inputs/5699-draft-1.py.txt). 실제 미처리 group 예외: 정상 예외 종료 1, ANSI 색상 존재, 해당 예외/제안 확인. 프로세스 충돌이 아니다.
- [5699-uncaught-group-cp](../../agent-b/records/5699-uncaught-group-cp.json): 종료 1, timeout False; [입력](../../agent-b/inputs/5699-draft-1.py.txt). 실제 미처리 group 예외: 정상 예외 종료 1, ANSI 색상 존재, 해당 예외/제안 확인. 프로세스 충돌이 아니다.

핵심 출력은 다음과 같다. 판정에 사용하는 값과 결과는 양쪽에서 같았다.

`5699-uncaught-builtin-rp`

```text
'Traceback (most recent call last):\n  File \x1b[35m"<closure24-audit>/agent-b/inputs/5699-draft-1.py"\x1b[0m, line \x1b[35m4\x1b[0m, in \x1b[35m<module>\x1b[0m\n    ZeroDivisionErrrrr\n\x1b[1;35mNameError\x1b[0m: \x1b[35mname \'ZeroDivisionErrrrr\' is not defined. Did you mean: \'ZeroDivisionError\'?\x1b[0m\n'
```

`5699-blockers-rp` 핵심 필드와 assertion 결과 발췌(양쪽 동일):

```json
{
  "class_match": 4,
  "builtins": true,
  "stdlib_module_names": true,
  "except_star": [
    [
      "value",
      1
    ],
    [
      "type",
      1
    ]
  ],
  "anchors": [
    0,
    2,
    0,
    3,
    "~",
    "^"
  ],
  "zero": {
    "ansi": true,
    "plain_and_color_asserts_passed": true
  },
  "builtins_typo": {
    "ansi": true,
    "plain_and_color_asserts_passed": true
  },
  "stdlib_missing": {
    "ansi": true,
    "plain_and_color_asserts_passed": true
  },
  "group": {
    "ansi": true,
    "plain_and_color_asserts_passed": true
  }
}
```

`5699-uncaught-stdlib-rp` stderr의 ANSI를 escape해 표시한 원문(양쪽 동일):

```text
'Traceback (most recent call last):\n  File \x1b[35m"<closure24-audit>/agent-b/inputs/5699-draft-1.py"\x1b[0m, line \x1b[35m6\x1b[0m, in \x1b[35m<module>\x1b[0m\n    \x1b[1;31mio\x1b[0m.StringIO()\n    \x1b[1;31m^^\x1b[0m\n\x1b[1;35mNameError\x1b[0m: \x1b[35mname \'io\' is not defined. Did you mean: \'id\'? Or did you forget to import \'io\'?\x1b[0m\n'
```

`5699-uncaught-zero-rp` stderr의 ANSI를 escape해 표시한 원문(양쪽 동일):

```text
'Traceback (most recent call last):\n  File \x1b[35m"<closure24-audit>/agent-b/inputs/5699-draft-1.py"\x1b[0m, line \x1b[35m8\x1b[0m, in \x1b[35m<module>\x1b[0m\n    \x1b[31m1 \x1b[0m\x1b[1;31m/\x1b[0m\x1b[31m 0\x1b[0m\n    \x1b[31m~~\x1b[0m\x1b[1;31m^\x1b[0m\x1b[31m~~\x1b[0m\n\x1b[1;35mZeroDivisionError\x1b[0m: \x1b[35mdivision by zero\x1b[0m\n'
```

`5699-uncaught-group-rp` stderr의 ANSI를 escape해 표시한 원문(양쪽 동일):

```text
'  + Exception Group Traceback (most recent call last):\n  |   File \x1b[35m"<closure24-audit>/agent-b/inputs/5699-draft-1.py"\x1b[0m, line \x1b[35m10\x1b[0m, in \x1b[35m<module>\x1b[0m\n  |     raise ExceptionGroup("uncaught group", [ValueError("v"), TypeError("t")])\n  | \x1b[1;35mExceptionGroup\x1b[0m: \x1b[35muncaught group (2 sub-exceptions)\x1b[0m\n  +-+---------------- 1 ----------------\n    | \x1b[1;35mValueError\x1b[0m: \x1b[35mv\x1b[0m\n    +---------------- 2 ----------------\n    | \x1b[1;35mTypeError\x1b[0m: \x1b[35mt\x1b[0m\n    +------------------------------------\n'
```

보충 기록: [원문 기반 검증 계획](../../agent-b/plans/5699.json), [파일 보존 검사](../../agent-b/environment/preservation.json).

본문의 두 Python 파일을 각각 실행했다. 첫 입력은 잡은 예외를 format_exception으로 확인하고, 둘째 입력은 예외를 잡지 않는 별도 프로세스다. 따라서 API 출력만 보고 실제 미처리 예외 출력을 성공으로 단정한 것이 아니다.

a7ad84827023의 저장 원시 입력 네 개는 각각 class pattern ValueError, f_builtins AttributeError, stdlib_module_names AttributeError, except* 미구현 SyntaxError를 보여 준다. 이번 실제 uncaught-color 경로는 그 단위 blocker 입력보다 넓다.

과거 로그는 [실제 입력·출력 대조 기록](../../agent-b/sources/historical-primary-audit.json)에서 확인했다. 그 과거 실행 파일은 이번에 다시 실행하지 않았다. 익명화된 export 36개는 기록된 export SHA-256과 모두 일치했으나, 이는 로그 보존을 확인하는 것이며 과거 빌드 출처를 독립 실행으로 재입증한 것은 아니다.

PR #6110/50c557419는 MatchClass의 positional count/속성 추출을, #6568/feb5066be는 f_builtins와 stdlib_module_names를, #6530/4a6e8fb29는 except*와 예외 그룹 dispatch를 추가한다.

[50c557419e9d diff](../../agent-b/logs/change-5699-50c557419.stdout)와 목표 조상 여부 [검사 기록](../../agent-b/records/ancestor-5699-50c557419.json)을 새로 확인했다. 인접 부모/변경 리비전을 실행하지 않았으므로 관련 변경으로만 분류한다.

[feb5066be2d4 diff](../../agent-b/logs/change-5699-feb5066be.stdout)와 목표 조상 여부 [검사 기록](../../agent-b/records/ancestor-5699-feb5066be.json)을 새로 확인했다. 인접 부모/변경 리비전을 실행하지 않았으므로 관련 변경으로만 분류한다.

[4a6e8fb29edf diff](../../agent-b/logs/change-5699-4a6e8fb29.stdout)와 목표 조상 여부 [검사 기록](../../agent-b/records/ancestor-5699-4a6e8fb29.json)을 새로 확인했다. 인접 부모/변경 리비전을 실행하지 않았으므로 관련 변경으로만 분류한다.

FORCE_COLOR=1/PYTHON_COLORS=1인 pipe 캡처다. 모든 터미널의 자동 색상 탐지나 모든 traceback edge case를 보장하지 않는다.

명시된 초안 동작 주장 중 실행하지 않은 항목은 없다. 관찰과 다른 설명이나 입력 구분은 위에 수정 대상으로 적었다. 전체 라이브러리 지원이나 최초 수정 시점은 이 판정에 포함하지 않는다.

권고 문구: 보고된 네 blocker와 확인한 네 실제 미처리 예외 경로가 동작하며, 강제 색상 설정에서 ANSI와 builtin/stdlib 제안이 CPython과 일치한다.

**기술 판정: 해결 확인**

**초안 판정: 유지**
