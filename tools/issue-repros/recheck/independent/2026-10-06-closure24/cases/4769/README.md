# #4769 독립 검증

Python 코드 블록은 커밋 훅으로 서식을 정리했고, 정리 전후의 AST가 같음을 확인했다. 정확한 실행 입력은 링크된 `.py.txt` 사본과 원본 해시를 기준으로 한다.

기술 판정은 **해결 확인**이다. 초안 판정은 **유지**다. 아래에 한정한 관찰이며 최초 수정 커밋을 확정한 결과가 아니다.

[원본 이슈](https://github.com/RustPython/RustPython/issues/4769)는 2026-10-05T16:10:20.920220+00:00 UTC 조회 시 **open**였다. 본문과 댓글 2개를 확인했다. 현재 열린 상태이므로 기술적으로 해결된 범위의 종료 검토 요청은 의미가 있다.

deque subclass를 pickle로 왕복할 때 __dict__가 보존되지 않는 문제이며 test_deque.TestSubclass.test_copy_pickle을 연결한다. 원문은 pickle.dumps(pickle.HIGHEST_PROTOCOL)로 정수 자체를 pickle하는 오타가 있다. 그 문장을 d를 넘긴 코드로 몰래 교체하면 안 된다.

초안은 원본 회귀 테스트 통과 및 protocol 0–5에서 subclass 타입·요소·maxlen·인스턴스 속성·slots 보존을 주장한다.

literal 원문은 양쪽 모두 int.__dict__ AttributeError, 종료 1이다. 별도 의도 입력은 Deque/DequeWithSlots × 세 가지 내용/maxlen × protocol 0–5, 총 36회 왕복에서 모든 assert를 통과했다. 원본 test_copy_pickle은 1개 실제 실행했고 skip/expectedFailure/unexpectedSuccess/오류/실패 모두 0이다.

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

입력 파일 `4769-original.py` ([저장된 파일](../../agent-b/inputs/4769-original.py.txt)):

```python
import pickle
from collections import deque


class Deque(deque):
    pass


d = Deque()
d.x = "value"
e = pickle.loads(pickle.dumps(pickle.HIGHEST_PROTOCOL))
e.__dict__
```

입력 파일 `4769-draft-0.py` ([저장된 파일](../../agent-b/inputs/4769-draft-0.py.txt)):

```python
import sys, json


def issue4769():
    import pickle, copy
    from collections import deque

    global Deque, DequeWithSlots

    class Deque(deque):
        pass

    class DequeWithSlots(deque):
        __slots__ = ("slot", "__dict__")

    # Names must be globally resolvable for pickle.
    Deque.__qualname__ = "Deque"
    DequeWithSlots.__qualname__ = "DequeWithSlots"
    literal = pickle.loads(pickle.dumps(pickle.HIGHEST_PROTOCOL))
    try:
        literal.__dict__
    except AttributeError:
        print("literal original: integer has no __dict__")
    total = 0
    for cls in (Deque, DequeWithSlots):
        for values, maxlen in (
            ([], None),
            (["a", "b", "c"], None),
            (["a", "b", "c"], 2),
        ):
            d = cls(values, maxlen=maxlen)
            d.x = "value"
            d.extra = ["list state"]
            if cls is DequeWithSlots:
                d.slot = ["slot state"]
            for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
                e = pickle.loads(pickle.dumps(d, protocol))
                assert type(e) is cls and e is not d
                assert list(e) == list(d) and e.maxlen == d.maxlen
                assert e.__dict__ == d.__dict__
                if cls is DequeWithSlots:
                    assert e.slot == d.slot
                total += 1
    print("pickle protocols:", list(range(pickle.HIGHEST_PROTOCOL + 1)))
    print("subclass roundtrips:", total)


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
"$RP" -B "$IN/4769-original.py"
"$CP" -B "$IN/4769-original.py"
"$RP" -B "$IN/4769-draft-0.py" 4769
"$CP" -B "$IN/4769-draft-0.py" 4769
"$RP" -B "$IN/unittest-probe.py" test.test_deque.TestSubclass.test_copy_pickle
```

실행별 결과와 입력 링크는 다음과 같다. stdout/stderr 원문은 JSON 기록에 연결되어 있다.

- [4769-literal-rp](../../agent-b/records/4769-literal-rp.json): 종료 1, timeout False; [입력](../../agent-b/inputs/4769-original.py.txt). 원문 오타는 정수를 pickle하므로 양쪽 모두 int.__dict__ AttributeError와 종료 1이 예상 결과다. deque 실패로 판정하지 않는다.
- [4769-literal-cp](../../agent-b/records/4769-literal-cp.json): 종료 1, timeout False; [입력](../../agent-b/inputs/4769-original.py.txt). 원문 오타는 정수를 pickle하므로 양쪽 모두 int.__dict__ AttributeError와 종료 1이 예상 결과다. deque 실패로 판정하지 않는다.
- [4769-draft-rp](../../agent-b/records/4769-draft-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4769-draft-0.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4769-draft-cp](../../agent-b/records/4769-draft-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4769-draft-0.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4769-regression-rp](../../agent-b/records/4769-regression-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/unittest-probe.py.txt). 원본 회귀 테스트 1개 실제 실행, 실패/오류/skip/expectedFailure/unexpectedSuccess 모두 0. 테스트나 마커를 변경하지 않았다.

핵심 출력은 다음과 같다. 판정에 사용하는 값과 결과는 양쪽에서 같았다.

`4769-draft-rp`

```text
literal original: integer has no __dict__
pickle protocols: [0, 1, 2, 3, 4, 5]
subclass roundtrips: 36
```

`4769-regression-rp`

```text
[{"id": "test.test_deque.TestSubclass.test_copy_pickle", "skip": false, "expected_failure": false}]
{"run": 1, "skips": [], "expected_failures": [], "unexpected_successes": [], "errors": 0, "failures": 0}
```

보충 기록: [원문 기반 검증 계획](../../agent-b/plans/4769.json), [파일 보존 검사](../../agent-b/environment/preservation.json).

본문은 여러 이슈가 들어 있는 저장 probes.py에서 issue4769 함수와 imports/dispatcher만 옮긴 것이다. 해당 함수의 dict/slots·36회 검증 연산은 유지된다. 정수를 pickle한 literal 입력과 d를 pickle한 의도 입력은 보고서에서도 분리한다.

25ca331dc81e의 과거 기록은 원본 test_copy_pickle에서 e.x AttributeError를 보여 준다. 당시 기록은 expectedFailure를 메모리에서 해제한 실행이므로, 마커를 그대로 둔 이번 원본 테스트와 동일 조건이라고 쓰지 않는다. 이번에는 파일과 마커를 전혀 변경하지 않았다.

과거 로그는 [실제 입력·출력 대조 기록](../../agent-b/sources/historical-primary-audit.json)에서 확인했다. 그 과거 실행 파일은 이번에 다시 실행하지 않았다. 익명화된 export 36개는 기록된 export SHA-256과 모두 일치했으나, 이는 로그 보존을 확인하는 것이며 과거 빌드 출처를 독립 실행으로 재입증한 것은 아니다.

PR #7699의 목표 조상 6182bbf22는 deque.__reduce__ 상태를 None에서 __getstate__ 호출 결과로 바꾼다. 이 상태가 __dict__와 __slots__를 포함한다.

[6182bbf22148 diff](../../agent-b/logs/change-4769-6182bbf22.stdout)와 목표 조상 여부 [검사 기록](../../agent-b/records/ancestor-4769-6182bbf22.json)을 새로 확인했다. 인접 부모/변경 리비전을 실행하지 않았으므로 관련 변경으로만 분류한다.

재귀 deque pickle 및 다른 collections 전체는 종료 판단 범위가 아니다.

명시된 초안 동작 주장 중 실행하지 않은 항목은 없다. 관찰과 다른 설명이나 입력 구분은 위에 수정 대상으로 적었다. 전체 라이브러리 지원이나 최초 수정 시점은 이 판정에 포함하지 않는다.

권고 문구: 원문 오타와 의도 입력을 구분해 확인했다. deque subclass 상태는 protocol 0–5에서 보존되며 기존 test_copy_pickle도 마커 변경 없이 통과한다.

**기술 판정: 해결 확인**

**초안 판정: 유지**
