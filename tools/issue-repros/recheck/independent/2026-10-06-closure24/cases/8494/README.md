# #8494 독립 검증

Python 코드 블록은 커밋 훅으로 서식을 정리했고, 정리 전후의 AST가 같음을 확인했다. 정확한 실행 입력은 링크된 `.py.txt` 사본과 원본 해시를 기준으로 한다.

기술 판정은 **해결 확인**이다. 초안 판정은 **문구 축소·수정**이다. 아래에 한정한 관찰이며 최초 수정 커밋을 확정한 결과가 아니다.

[원본 이슈](https://github.com/RustPython/RustPython/issues/8494)는 2026-10-05T16:10:29.869464+00:00 UTC 조회 시 **open**였다. 본문과 댓글 3개를 확인했다. 현재 열린 상태이므로 기술적으로 해결된 범위의 종료 검토 요청은 의미가 있다.

PEP 749의 classmethod/staticmethod __annotations__ 및 __annotate__는 wrapper dict에 값을 cache하고 wrapper에 대한 대입은 wrapped function을 바꾸지 않아야 한다. 원문은 아직 정의되지 않은 Missing을 반환 annotation에 사용한다. 댓글의 #8701 해결 주장은 재실행 근거와 분리한다.

초안은 두 wrapper·두 속성의 읽기/cache/대입/삭제 격리, 원문 예제 및 기존 회귀 테스트 통과를 주장한다.

module-level 원문 그대로 양쪽을 실행해 cache True, wrapper {"x": str} 대입 뒤 f.__annotations__가 {"return": int}로 유지됨을 확인했다. 별도 local-function 변형과 annotated/unannotated × classmethod/staticmethod × 두 속성의 read/cache/assign/delete assert도 모두 통과했다. 원본 test_classmethod_staticmethod_annotations 1개가 skip/expectedFailure/unexpectedSuccess/오류/실패 없이 실행됐다.

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

입력 파일 `8494-original.py` ([저장된 파일](../../agent-b/inputs/8494-original.py.txt)):

```python
def f() -> Missing:
    pass


for wrapper in (classmethod(f), staticmethod(f)):
    Missing = int
    print(type(wrapper).__name__, wrapper.__annotations__)
    print("__annotations__" in wrapper.__dict__)

    wrapper.__annotations__ = {"x": str}
    print("wrapper:", wrapper.__annotations__)
    print("wrapped:", f.__annotations__)
```

입력 파일 `8494-draft-0.py` ([저장된 파일](../../agent-b/inputs/8494-draft-0.py.txt)):

```python
import sys, json


def issue8494():
    # This is the literal original, including creating both wrappers before Missing.
    def f() -> Missing:
        pass

    for wrapper in (classmethod(f), staticmethod(f)):
        Missing = int
        print(type(wrapper).__name__, wrapper.__annotations__)
        print("__annotations__" in wrapper.__dict__)
        wrapper.__annotations__ = {"x": str}
        print("wrapper:", wrapper.__annotations__)
        print("wrapped:", f.__annotations__)
    for decorator in (classmethod, staticmethod):

        def annotated(x: int) -> str:
            pass

        def unannotated(x):
            pass

        for function in (annotated, unannotated):
            wrapper = decorator(function)
            for name, replacement in [
                ("__annotations__", {"new": bytes}),
                ("__annotate__", lambda format: {"new": bytes}),
            ]:
                assert name not in wrapper.__dict__
                original = getattr(function, name)
                assert getattr(wrapper, name) is original
                assert wrapper.__dict__[name] is original
                setattr(wrapper, name, replacement)
                assert getattr(wrapper, name) is replacement
                assert getattr(function, name) is original
                delattr(wrapper, name)
                assert name not in wrapper.__dict__
                assert getattr(wrapper, name) is original
            print(
                decorator.__name__,
                function.__name__,
                "both attributes cache/write/delete isolation passed",
            )


globals()["issue" + sys.argv[1]]()
```

입력 파일 `unittest-probe.py` ([저장된 파일](../../agent-b/inputs/unittest-probe.py.txt)):

```python
import unittest, json, sys

suite = unittest.defaultTestLoader.loadTestsFromNames(sys.argv[1:])


def flat(item):
    return (
        [t for child in item for t in flat(child)]
        if isinstance(item, unittest.TestSuite)
        else [item]
    )


tests = flat(suite)
print(
    json.dumps(
        [
            dict(
                id=t.id(),
                skip=bool(
                    getattr(t, "__unittest_skip__", False)
                    or getattr(
                        getattr(t, t._testMethodName), "__unittest_skip__", False
                    )
                ),
                expected_failure=bool(
                    getattr(
                        getattr(t, t._testMethodName),
                        "__unittest_expecting_failure__",
                        False,
                    )
                ),
            )
            for t in tests
        ]
    ),
    flush=True,
)
result = unittest.TextTestRunner(verbosity=2).run(suite)
summary = dict(
    run=result.testsRun,
    skips=[(t.id(), reason) for t, reason in result.skipped],
    expected_failures=[t.id() for t, _ in result.expectedFailures],
    unexpected_successes=[t.id() for t in result.unexpectedSuccesses],
    errors=len(result.errors),
    failures=len(result.failures),
)
print(json.dumps(summary), flush=True)
sys.exit(
    0
    if result.wasSuccessful()
    and result.testsRun > 0
    and not result.skipped
    and not result.expectedFailures
    and not result.unexpectedSuccesses
    else 1
)
```

```sh
"$RP" -B "$IN/8494-original.py"
"$CP" -B "$IN/8494-original.py"
"$RP" -B "$IN/8494-draft-0.py" 8494
"$CP" -B "$IN/8494-draft-0.py" 8494
"$RP" -B "$IN/unittest-probe.py" test.test_descr.ClassPropertiesAndMethods.test_classmethod_staticmethod_annotations
```

실행별 결과와 입력 링크는 다음과 같다. stdout/stderr 원문은 JSON 기록에 연결되어 있다.

- [8494-original-rp](../../agent-b/records/8494-original-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/8494-original.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [8494-original-cp](../../agent-b/records/8494-original-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/8494-original.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [8494-draft-rp](../../agent-b/records/8494-draft-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/8494-draft-0.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [8494-draft-cp](../../agent-b/records/8494-draft-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/8494-draft-0.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [8494-regression-rp](../../agent-b/records/8494-regression-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/unittest-probe.py.txt). 원본 회귀 테스트 1개 실제 실행, 실패/오류/skip/expectedFailure/unexpectedSuccess 모두 0. 테스트나 마커를 변경하지 않았다.

핵심 출력은 다음과 같다. 판정에 사용하는 값과 결과는 양쪽에서 같았다.

`8494-draft-rp`

```text
classmethod {'return': <class 'int'>}
True
wrapper: {'x': <class 'str'>}
wrapped: {'return': <class 'int'>}
staticmethod {'return': <class 'int'>}
True
wrapper: {'x': <class 'str'>}
wrapped: {'return': <class 'int'>}
classmethod annotated both attributes cache/write/delete isolation passed
classmethod unannotated both attributes cache/write/delete isolation passed
staticmethod annotated both attributes cache/write/delete isolation passed
staticmethod unannotated both attributes cache/write/delete isolation passed
```

`8494-regression-rp`

```text
[{"id": "test.test_descr.ClassPropertiesAndMethods.test_classmethod_staticmethod_annotations", "skip": false, "expected_failure": false}]
{"run": 1, "skips": [], "expected_failures": [], "unexpected_successes": [], "errors": 0, "failures": 0}
```

제출용 요약의 기술 주장은 새 실행으로 뒷받침된다. 문구 수정 권고의 직접 대상은 상세 재현 보고서에서 local-function 변형에 붙인 “literal original” 표시다.

보충 기록: [원문 기반 검증 계획](../../agent-b/plans/8494.json), [파일 보존 검사](../../agent-b/environment/preservation.json).

본문에 “literal original”이라고 주석을 단 코드는 issue8494 함수 내부라 원문 module-level Missing lookup과 정확히 같은 코드가 아니다. 저장 shared probes.py에서 해당 함수만 분리한 것 자체는 의미를 유지하지만, 이 변형을 원문 그대로라고 부르는 문구는 수정해야 한다. 새 검증에는 module-level 원문 파일과 그 local 변형을 모두 보존·실행했다.

b304919a6301의 저장 원문은 module-level 코드와 같으며 cache False, wrapper 대입 뒤 underlying f도 x:str로 바뀐다. 종료 0은 성공이 아니다. 이번에는 원문 module-level 코드와 draft의 local-function 변형을 별개로 실행했다.

과거 로그는 [실제 입력·출력 대조 기록](../../agent-b/sources/historical-primary-audit.json)에서 확인했다. 그 과거 실행 파일은 이번에 다시 실행하지 않았다. 익명화된 export 36개는 기록된 export SHA-256과 모두 일치했으나, 이는 로그 보존을 확인하는 것이며 과거 빌드 출처를 독립 실행으로 재입증한 것은 아니다.

PR #8701의 목표 조상 73e547a9c는 공유 getter가 wrapper dict를 먼저 읽고 delegate 값을 거기에 저장하며, setter가 wrapper dict만 바꾸도록 수정한다. classmethod와 staticmethod의 두 annotation 속성 모두 이 함수를 사용한다.

[73e547a9c31f diff](../../agent-b/logs/change-8494-73e547a9c.stdout)와 목표 조상 여부 [검사 기록](../../agent-b/records/ancestor-8494-73e547a9c.json)을 새로 확인했다. 인접 부모/변경 리비전을 실행하지 않았으므로 관련 변경으로만 분류한다.

CPython 3.14.6 annotation 의미를 기준으로 한다. pre-3.14 eager annotation과 비교하지 않는다. CPython 배포의 test 패키지가 없어 repository 회귀 테스트는 RustPython에서만 실행했다.

명시된 초안 동작 주장 중 실행하지 않은 항목은 없다. 관찰과 다른 설명이나 입력 구분은 위에 수정 대상으로 적었다. 전체 라이브러리 지원이나 최초 수정 시점은 이 판정에 포함하지 않는다.

권고 문구: module-level 원문과 별도 local-function 변형을 각각 확인했다. 두 wrapper의 두 annotation 속성은 cache·대입·삭제를 wrapper에 격리하며 원본 회귀 테스트도 통과한다.

**기술 판정: 해결 확인**

**초안 판정: 문구 축소·수정**
