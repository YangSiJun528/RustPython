# #4856 독립 검증

Python 코드 블록은 커밋 훅으로 서식을 정리했고, 정리 전후의 AST가 같음을 확인했다. 정확한 실행 입력은 링크된 `.py.txt` 사본과 원본 해시를 기준으로 한다.

기술 판정은 **해결 확인**이다. 초안 판정은 **유지**다. 아래에 한정한 관찰이며 최초 수정 커밋을 확정한 결과가 아니다.

[원본 이슈](https://github.com/RustPython/RustPython/issues/4856)는 2026-10-05T16:10:21.959350+00:00 UTC 조회 시 **open**였다. 본문과 댓글 0개를 확인했다. 현재 열린 상태이므로 기술적으로 해결된 범위의 종료 검토 요청은 의미가 있다.

Ubuntu 18.04/RustPython 0.2.0에서 lambda가 들어 있는 class decorator를 컴파일할 때 table.sub_tables.is_empty() Rust assertion panic이 난다. 제공 코드는 BaseFTests가 정의되지 않았고 mock.patch 대상도 빈 문자열이므로 정상 애플리케이션 성공을 기대할 수 없다.

초안은 원문 컴파일 panic 해소와 실행 시 NameError를 구분하고, 유효한 mock.patch 및 nested capture 예제 성공을 주장한다.

원문 파일은 양쪽 모두 BaseFTests NameError로 종료 1이며 Rust panic은 없다. 별도 compile(source, ..., "exec")도 성공했다. 보정 예제는 대상 함수를 test 메서드 안에서 3으로 바꾸고 밖에서는 1을 유지한다. nested capture는 7, 밖은 1이다. 양쪽 stdout이 같다.

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

입력 파일 `4856-original.py` ([저장된 파일](../../agent-b/inputs/4856-original.py.txt)):

```python
import unittest
from unittest import mock


class MockedA(BaseFTests):
    pass


@mock.patch("", lambda: 3)
class MockedB(MockedA):
    def _asserts(self, val):
        pass
```

입력 파일 `original-4856.py` ([저장된 파일](../../agent-b/inputs/original-4856.py.txt)):

```python
import unittest
from unittest import mock


class MockedA(BaseFTests):
    pass


@mock.patch("", lambda: 3)
class MockedB(MockedA):
    def _asserts(self, val):
        pass
```

입력 파일 `4856-draft-1.py` ([저장된 파일](../../agent-b/inputs/4856-draft-1.py.txt)):

```python
from pathlib import Path

source = Path(__file__).with_name("original-4856.py").read_text()
code = compile(source, "original-4856.py", "exec")
print("original compile success")
try:
    exec(code, {})
except Exception as e:
    print("original execution", type(e).__name__, str(e))
from unittest import mock


class BaseFTests:
    pass


class MockedA(BaseFTests):
    pass


def target():
    return 1


@mock.patch("__main__.target", lambda: 3)
class MockedB(MockedA):
    def test_value(self):
        return target()


print("valid patch method", MockedB().test_value(), "outside", target())


def factory(value):
    @mock.patch("__main__.target", lambda: value)
    class Nested(MockedA):
        def test_value(self):
            return target()

    return Nested


print("nested capture", factory(7)().test_value(), "outside", target())
```

```sh
"$RP" -B "$IN/4856-original.py"
"$CP" -B "$IN/4856-original.py"
"$RP" -B "$IN/4856-draft-1.py"
"$CP" -B "$IN/4856-draft-1.py"
```

실행별 결과와 입력 링크는 다음과 같다. stdout/stderr 원문은 JSON 기록에 연결되어 있다.

- [4856-original-rp](../../agent-b/records/4856-original-rp.json): 종료 1, timeout False; [입력](../../agent-b/inputs/4856-original.py.txt). 원문 전체 컴파일 후 정의되지 않은 BaseFTests에서 NameError, 종료 1. Rust panic은 없으며 원문 앱 실행 성공을 주장하지 않는다.
- [4856-original-cp](../../agent-b/records/4856-original-cp.json): 종료 1, timeout False; [입력](../../agent-b/inputs/4856-original.py.txt). 원문 전체 컴파일 후 정의되지 않은 BaseFTests에서 NameError, 종료 1. Rust panic은 없으며 원문 앱 실행 성공을 주장하지 않는다.
- [4856-compile-corrected-rp](../../agent-b/records/4856-compile-corrected-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4856-draft-1.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4856-compile-corrected-cp](../../agent-b/records/4856-compile-corrected-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4856-draft-1.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.

핵심 출력은 다음과 같다. 판정에 사용하는 값과 결과는 양쪽에서 같았다.

`4856-compile-corrected-rp`

```text
original compile success
original execution NameError name 'BaseFTests' is not defined
valid patch method 3 outside 1
nested capture 7 outside 1
```

보충 기록: [원문 기반 검증 계획](../../agent-b/plans/4856.json), [파일 보존 검사](../../agent-b/environment/preservation.json).

본문은 original-4856.py와 그 파일을 읽는 compile/실행 harness 두 파일이다. 저장 executed source는 같은 원문 문자열을 직접 넣은 harness라 경로 공급 방식이 다르다. 이번에는 본문의 두 파일 구조를 그대로 실행했다. 유효한 예제는 BaseFTests 정의와 실제 patch target을 추가한 별도 보정 입력이다.

c7faae9b22/v0.2.0 저장 입력은 원문 문자열을 compile만 한 파생 harness이며, 실행 앱 자체가 아니다. 저장 종료 101과 compiler/codegen assertion panic이 확인된다. 이번에는 compile, 원문 실행, 유효한 예제를 모두 나누었다.

과거 로그는 [실제 입력·출력 대조 기록](../../agent-b/sources/historical-primary-audit.json)에서 확인했다. 그 과거 실행 파일은 이번에 다시 실행하지 않았다. 익명화된 export 36개는 기록된 export SHA-256과 모두 일치했으나, 이는 로그 보존을 확인하는 것이며 과거 빌드 출처를 독립 실행으로 재입증한 것은 아니다.

PR #8138의 a1ba6a662에서 symboltable의 class decorators 스캔을 class scope 진입 전에 수행하도록 바꾼 diff를 확인했다. codegen의 중첩 scope 순서 처리도 함께 바뀐다.

[a1ba6a662cff diff](../../agent-b/logs/change-4856-a1ba6a662.stdout)와 목표 조상 여부 [검사 기록](../../agent-b/records/ancestor-4856-a1ba6a662.json)을 새로 확인했다. 인접 부모/변경 리비전을 실행하지 않았으므로 관련 변경으로만 분류한다.

원문 앱은 여전히 잘못된 입력이다. “원문 프로그램이 정상 실행된다”는 결론은 내리지 않는다.

명시된 초안 동작 주장 중 실행하지 않은 항목은 없다. 관찰과 다른 설명이나 입력 구분은 위에 수정 대상으로 적었다. 전체 라이브러리 지원이나 최초 수정 시점은 이 판정에 포함하지 않는다.

권고 문구: 원문은 Rust 컴파일러 panic 없이 컴파일된다. 원문 실행의 BaseFTests NameError는 CPython과 같고, 별도로 보정한 mock.patch와 nested capture는 성공한다.

**기술 판정: 해결 확인**

**초안 판정: 유지**
