# #8052 독립 검증

Python 코드 블록은 커밋 훅으로 서식을 정리했고, 정리 전후의 AST가 같음을 확인했다. 정확한 실행 입력은 링크된 `.py.txt` 사본과 원본 해시를 기준으로 한다.

기술 판정은 **해결 확인**이다. 초안 판정은 **유지**다. 아래에 한정한 관찰이며 최초 수정 커밋을 확정한 결과가 아니다.

[원본 이슈](https://github.com/RustPython/RustPython/issues/8052)는 2026-10-05T16:10:28.795595+00:00 UTC 조회 시 **open**였다. 본문과 댓글 8개를 확인했다. 현재 열린 상태이므로 기술적으로 해결된 범위의 종료 검토 요청은 의미가 있다.

type(...).__name__과 repr이 ellipsis/<class 'ellipsis'>여야 하며 types.EllipsisType는 동일 타입의 alias다. 원문은 JSON test_bad_default와 PEP 678의 when serializing ellipsis object note도 명시한다.

초안은 name/repr, type alias, 기존 JSON 회귀 테스트 통과를 주장하며 사례 보고서는 네 JSON note가 같다고 적었다.

원문 name/repr는 CPython과 같다. types.EllipsisType 및 _types.EllipsisType 모두 type(...)와 동일하다. JSON default의 중첩 실패에서 ellipsis/list item 0/module/type의 네 note가 같은 순서로 나온다. 실제 TestPyDefault.test_bad_default와 TestCDefault.test_bad_default 2개가 마커 변경 없이 실행됐고 skip/expectedFailure/unexpectedSuccess/오류/실패 모두 0이다.

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

입력 파일 `8052-original.py` ([저장된 파일](../../agent-b/inputs/8052-original.py.txt)):

```python
print(type(...).__name__)
print(repr(type(...)))
```

입력 파일 `8052-draft-0.py` ([저장된 파일](../../agent-b/inputs/8052-draft-0.py.txt)):

```python
import types, json, collections

print(type(...).__name__)
print(repr(type(...)))
print("alias", types.EllipsisType is type(...))


def default(obj):
    if obj is NotImplemented:
        raise ValueError
    if obj is ...:
        return NotImplemented
    if obj is type:
        return collections
    return [...]


try:
    json.dumps(type, default=default)
except ValueError as e:
    print("notes", e.__notes__)
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

입력 파일 `8052-alias.py` ([저장된 파일](../../agent-b/inputs/8052-alias.py.txt)):

```python
import types

assert types.EllipsisType is type(...)
assert types.EllipsisType.__name__ == "ellipsis"
try:
    import _types
except ImportError:
    print("_types unavailable; public types alias verified")
else:
    assert _types.EllipsisType is types.EllipsisType
    print("_types and types aliases verified")
```

```sh
"$RP" -B "$IN/8052-original.py"
"$CP" -B "$IN/8052-original.py"
"$RP" -B -S "$IN/8052-draft-0.py"
"$CP" -B -S "$IN/8052-draft-0.py"
"$RP" -B "$IN/unittest-probe.py" test.test_json.test_default.TestPyDefault.test_bad_default test.test_json.test_default.TestCDefault.test_bad_default
"$RP" -B "$IN/8052-alias.py"
"$CP" -B "$IN/8052-alias.py"
```

실행별 결과와 입력 링크는 다음과 같다. stdout/stderr 원문은 JSON 기록에 연결되어 있다.

- [8052-original-rp](../../agent-b/records/8052-original-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/8052-original.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [8052-original-cp](../../agent-b/records/8052-original-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/8052-original.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [8052-draft-rp](../../agent-b/records/8052-draft-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/8052-draft-0.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [8052-draft-cp](../../agent-b/records/8052-draft-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/8052-draft-0.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [8052-regression-rp](../../agent-b/records/8052-regression-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/unittest-probe.py.txt). 원본 회귀 테스트 2개 실제 실행, 실패/오류/skip/expectedFailure/unexpectedSuccess 모두 0. 테스트나 마커를 변경하지 않았다.
- [8052-alias-rp](../../agent-b/records/8052-alias-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/8052-alias.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [8052-alias-cp](../../agent-b/records/8052-alias-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/8052-alias.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.

핵심 출력은 다음과 같다. 판정에 사용하는 값과 결과는 양쪽에서 같았다.

`8052-draft-rp`

```text
ellipsis
<class 'ellipsis'>
alias True
notes ['when serializing ellipsis object', 'when serializing list item 0', 'when serializing module object', 'when serializing type object']
```

`8052-regression-rp`

```text
[{"id": "test.test_json.test_default.TestPyDefault.test_bad_default", "skip": false, "expected_failure": false}, {"id": "test.test_json.test_default.TestCDefault.test_bad_default", "skip": false, "expected_failure": false}]
{"run": 2, "skips": [], "expected_failures": [], "unexpected_successes": [], "errors": 0, "failures": 0}
```

보충 기록: [원문 기반 검증 계획](../../agent-b/plans/8052.json), [파일 보존 검사](../../agent-b/environment/preservation.json).

본문은 이름 출력에 alias와 JSON note 관찰을 더한 별도 입력이다. 기존 최소 과거 재현만으로 alias/JSON까지 증명한 것으로 보지 않았고 새 실행·원본 두 회귀 테스트로 확인했다.

83fe92042112의 저장 입력은 원문의 두 print와 같고 stdout에 EllipsisType/<class 'EllipsisType'>가 있다. 종료 0은 타입 이름이 맞다는 뜻이 아니다. 원문에 링크한 8e35cc9e 소스와 그 과거 실행 리비전은 다르며 reporter의 동일 실행 파일로 간주하지 않는다.

과거 로그는 [실제 입력·출력 대조 기록](../../agent-b/sources/historical-primary-audit.json)에서 확인했다. 그 과거 실행 파일은 이번에 다시 실행하지 않았다. 익명화된 export 36개는 기록된 export SHA-256과 모두 일치했으나, 이는 로그 보존을 확인하는 것이며 과거 빌드 출처를 독립 실행으로 재입증한 것은 아니다.

PR #8580의 f87cfe7e7은 PyEllipsis의 pyclass 이름을 EllipsisType에서 ellipsis로 바꾼다. alias 동작은 새 실행으로 별도 검증했다.

[f87cfe7e7a24 diff](../../agent-b/logs/change-8052-f87cfe7e7.stdout)와 목표 조상 여부 [검사 기록](../../agent-b/records/ancestor-8052-f87cfe7e7.json)을 새로 확인했다. 인접 부모/변경 리비전을 실행하지 않았으므로 관련 변경으로만 분류한다.

CPython 배포에는 test 패키지가 없어 repository 회귀 테스트는 RustPython에서 실행했다. 같은 독립 JSON 입력은 양쪽에서 비교했다.

명시된 초안 동작 주장 중 실행하지 않은 항목은 없다. 관찰과 다른 설명이나 입력 구분은 위에 수정 대상으로 적었다. 전체 라이브러리 지원이나 최초 수정 시점은 이 판정에 포함하지 않는다.

권고 문구: ellipsis 이름과 repr, types/_types alias가 맞으며 네 JSON note와 기존 Py/C test_bad_default 회귀 테스트도 통과한다.

**기술 판정: 해결 확인**

**초안 판정: 유지**
