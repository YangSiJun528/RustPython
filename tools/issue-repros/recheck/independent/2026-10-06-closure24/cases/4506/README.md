# #4506 독립 검증

Python 코드 블록은 커밋 훅으로 서식을 정리했고, 정리 전후의 AST가 같음을 확인했다. 정확한 실행 입력은 링크된 `.py.txt` 사본과 원본 해시를 기준으로 한다.

기술 판정은 **해결 확인**이다. 초안 판정은 **유지**다. 아래에 한정한 관찰이며 최초 수정 커밋을 확정한 결과가 아니다.

[원본 이슈](https://github.com/RustPython/RustPython/issues/4506)는 2026-10-05T16:10:17.786141+00:00 UTC 조회 시 **open**였다. 본문과 댓글 3개를 확인했다. 현재 열린 상태이므로 기술적으로 해결된 범위의 종료 검토 요청은 의미가 있다.

macOS의 RustPython 0.2.0에서 SymPy 1.11.1과 mpmath 1.2.1을 설치한 뒤 import sympy가 power.py의 obj.is_commutative 대입에서 AttributeError로 중단된다. 0.3.0에서도 같다는 댓글이 있다. 최소 종료 범위는 해당 버전의 실제 패키지 import와 원래 Pow 처리 경로다.

초안은 두 패키지의 실제 버전, import 성공, power.py:378 대입 관찰, Pow(S.Exp1, -1, evaluate=False) 및 간단한 expand 성공을 주장한다.

원문 import와 확장 입력 모두 양쪽에서 종료 0. 실제 버전은 1.11.1/1.2.1이고 동일한 보존 패키지 경로에서 로드했다. trace에 ["__new__", 378]이 기록된 뒤 Pow가 1/E를 반환했고 is_commutative is True, expand 값도 assert를 통과했다. 양쪽 stderr에는 SymPy runtests.py:275의 return-in-finally SyntaxWarning이 동일하게 있다. import 실패는 아니다.

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

입력 파일 `4506-original.py` ([저장된 파일](../../agent-b/inputs/4506-original.py.txt)):

```python
import os, sys

sys.path.insert(0, os.environ["SYMPY_SITE"])
import sympy

print(sympy.__version__, sympy.__file__)
```

입력 파일 `4506-draft-0.py` ([저장된 파일](../../agent-b/inputs/4506-draft-0.py.txt)):

```python
import sys
import os
import json

site = os.environ["SYMPY_SITE"]
sys.path.insert(0, site)
import sympy
import mpmath
from sympy import Pow, S, Symbol, expand
from sympy.core.cache import clear_cache

assert sympy.__version__ == "1.11.1"
assert mpmath.__version__ == "1.2.1"
assert sympy.__file__.startswith(site + "/")
assert mpmath.__file__.startswith(site + "/")
clear_cache()
events = []


def trace(frame, event, arg):
    if (
        event == "line"
        and frame.f_code.co_filename == site + "/sympy/core/power.py"
        and frame.f_lineno == 378
    ):
        events.append([frame.f_code.co_name, frame.f_lineno])
    return trace


sys.settrace(trace)
value = Pow(S.Exp1, -1, evaluate=False)
sys.settrace(None)
assert value.is_commutative is True
assert events, "Original power.py assignment was not observed"
x = Symbol("x")
assert expand((x + 1) ** 2) == x**2 + 2 * x + 1
print(
    json.dumps(
        {
            "versions": [sympy.__version__, mpmath.__version__],
            "files": [sympy.__file__, mpmath.__file__],
            "original_assignment": events,
            "pow": str(value),
            "is_commutative": value.is_commutative,
            "expanded": str(expand((x + 1) ** 2)),
        },
        indent=2,
    )
)
```

```sh
"$RP" -B "$IN/4506-original.py"
"$CP" -B "$IN/4506-original.py"
"$RP" -B "$IN/4506-draft-0.py"
"$CP" -B "$IN/4506-draft-0.py"
```

실행별 결과와 입력 링크는 다음과 같다. stdout/stderr 원문은 JSON 기록에 연결되어 있다.

- [4506-original-rp](../../agent-b/records/4506-original-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4506-original.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음. SymPy 1.11.1/mpmath 1.2.1 실물 패키지 사용; 두 런타임의 return-in-finally SyntaxWarning은 동일하며 실패가 아니다.
- [4506-original-cp](../../agent-b/records/4506-original-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4506-original.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음. SymPy 1.11.1/mpmath 1.2.1 실물 패키지 사용; 두 런타임의 return-in-finally SyntaxWarning은 동일하며 실패가 아니다.
- [4506-draft-rp](../../agent-b/records/4506-draft-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4506-draft-0.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음. SymPy 1.11.1/mpmath 1.2.1 실물 패키지 사용; 두 런타임의 return-in-finally SyntaxWarning은 동일하며 실패가 아니다.
- [4506-draft-cp](../../agent-b/records/4506-draft-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4506-draft-0.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음. SymPy 1.11.1/mpmath 1.2.1 실물 패키지 사용; 두 런타임의 return-in-finally SyntaxWarning은 동일하며 실패가 아니다.

핵심 출력은 다음과 같다. 판정에 사용하는 값과 결과는 양쪽에서 같았다.

`4506-draft-rp`

```text
{
  "versions": [
    "1.11.1",
    "1.2.1"
  ],
  "files": [
    "<survey>/verification-tools/package-history-4506-original/site/sympy/__init__.py",
    "<survey>/verification-tools/package-history-4506-original/site/mpmath/__init__.py"
  ],
  "original_assignment": [
    [
      "__new__",
      378
    ]
  ],
  "pow": "1/E",
  "is_commutative": true,
  "expanded": "x**2 + 2*x + 1"
}
```

보충 기록: [원문 기반 검증 계획](../../agent-b/plans/4506.json), [파일 보존 검사](../../agent-b/environment/preservation.json).

초안 본문은 저장 입력의 익명화된 <survey>/… 상수를 SYMPY_SITE 환경변수로 바꿨다. 따옴표·서식 외 차이는 그 경로 공급 방식과 os import이며, 이번에는 본문 코드를 실제 경로로 실행해 버전·파일 경로·378행 trace assert까지 확인했다.

adc23253e4b5의 저장 로그는 실제 1.11.1/1.2.1 import가 원문과 같은 power.py:378에서 AttributeError로 끝난다. 과거 입력은 site 경로 삽입 후 import와 버전 출력을 추가한 코드다. 이번에는 원문 import와 대입 trace 입력을 별개로 실행했다.

과거 로그는 [실제 입력·출력 대조 기록](../../agent-b/sources/historical-primary-audit.json)에서 확인했다. 그 과거 실행 파일은 이번에 다시 실행하지 않았다. 익명화된 export 36개는 기록된 export SHA-256과 모두 일치했으나, 이는 로그 보존을 확인하는 것이며 과거 빌드 출처를 독립 실행으로 재입증한 것은 아니다.

PR #6390의 98fff96f1은 상속된 동명 속성이 있어도 __slots__ 멤버 디스크립터를 설치하도록 바꾼다. Pow.__slots__의 is_commutative 경로와 관련 있는 변경이다.

[98fff96f1c91 diff](../../agent-b/logs/change-4506-98fff96f1.stdout)와 목표 조상 여부 [검사 기록](../../agent-b/records/ancestor-4506-98fff96f1.json)을 새로 확인했다. 인접 부모/변경 리비전을 실행하지 않았으므로 관련 변경으로만 분류한다.

패키지 설치 과정과 SymPy 전체 테스트는 검증하지 않았다. 원래의 사용 단계인 import와 명시된 Pow/expand 범위만 확인했다.

명시된 초안 동작 주장 중 실행하지 않은 항목은 없다. 관찰과 다른 설명이나 입력 구분은 위에 수정 대상으로 적었다. 전체 라이브러리 지원이나 최초 수정 시점은 이 판정에 포함하지 않는다.

권고 문구: SymPy 1.11.1과 mpmath 1.2.1이 실제로 import되며, 원래 실패한 power.py:378 is_commutative 대입을 포함한 Pow 경로가 성공한다.

**기술 판정: 해결 확인**

**초안 판정: 유지**
