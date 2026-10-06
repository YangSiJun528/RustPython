# #4690 독립 검증

Python 코드 블록은 커밋 훅으로 서식을 정리했고, 정리 전후의 AST가 같음을 확인했다. 정확한 실행 입력은 링크된 `.py.txt` 사본과 원본 해시를 기준으로 한다.

기술 판정은 **해결 확인**이다. 초안 판정은 **문구 축소·수정**이다. 아래에 한정한 관찰이며 최초 수정 커밋을 확정한 결과가 아니다.

[원본 이슈](https://github.com/RustPython/RustPython/issues/4690)는 2026-10-05T16:10:18.848810+00:00 UTC 조회 시 **open**였다. 본문과 댓글 2개를 확인했다. 현재 열린 상태이므로 기술적으로 해결된 범위의 종료 검토 요청은 의미가 있다.

dict.__dict__["fromkeys"]의 원시 디스크립터 타입이 classmethod가 아닌 classmethod_descriptor여야 한다. 두 번째 원문 표현 type(dict.fromkeys)는 이미 builtin_function_or_method로 제시되어 있다. Python에서 정의한 @classmethod와 구분하는 것이 핵심이다.

초안은 “두 원문 조회가 모두 classmethod_descriptor”라고 쓰고, 바인딩과 추가 native 디스크립터도 CPython과 같다고 주장한다. 첫 문장은 원문 요구를 잘못 합쳤다.

원시 조회는 classmethod_descriptor, 바인딩된 조회는 builtin_function_or_method다. 두 출력은 CPython과 정확히 같다. types.ClassMethodDescriptorType 동일성, 메타데이터, dict/Child 바인딩, 잘못된 owner의 TypeError 및 Python classmethod 구분도 같았다. 추가로 int.from_bytes와 float.fromhex의 원시/바인딩 타입과 호출 결과까지 assert를 통과했다.

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

입력 파일 `4690-original.py` ([저장된 파일](../../agent-b/inputs/4690-original.py.txt)):

```python
print(type(dict.__dict__["fromkeys"]))
print(type(dict.fromkeys))
```

입력 파일 `4690-draft-boundaries.py` ([저장된 파일](../../agent-b/inputs/4690-draft-boundaries.py.txt)):

```python
import types

descriptor = dict.__dict__["fromkeys"]
print("types-identity", type(descriptor) is types.ClassMethodDescriptorType)
print(
    "metadata",
    descriptor.__name__,
    descriptor.__qualname__,
    descriptor.__objclass__ is dict,
)


class Child(dict):
    pass


class PythonClass:
    @classmethod
    def method(cls):
        return cls


print("python-classmethod", type(PythonClass.__dict__["method"]).__name__)
for owner in [dict, Child]:
    for instance in [None, owner()]:
        bound = descriptor.__get__(instance, owner)
        result = bound(["a"], 9)
        print(
            "bound",
            owner.__name__,
            instance is None,
            type(bound).__name__,
            type(result).__name__,
            result,
        )
print("direct-call", descriptor(dict, ["a"], 2))
for label, operation in [
    ("wrong-owner", lambda: descriptor.__get__(None, str)),
    ("non-type-owner", lambda: descriptor.__get__(None, 1)),
    ("no-receiver", lambda: descriptor()),
    ("wrong-direct", lambda: descriptor(str, ["a"])),
]:
    try:
        print(label, "accepted", operation())
    except Exception as error:
        print(label, type(error).__name__)
```

입력 파일 `4690-native-additional.py` ([저장된 파일](../../agent-b/inputs/4690-native-additional.py.txt)):

```python
import types

for owner, name, args, wanted in [
    (dict, "fromkeys", (["a"], 2), {"a": 2}),
    (int, "from_bytes", (b"\x01",), 1),
    (float, "fromhex", ("0x1.8p1",), 3.0),
]:
    raw = owner.__dict__[name]
    assert type(raw) is types.ClassMethodDescriptorType
    bound = getattr(owner, name)
    assert type(bound).__name__ == "builtin_function_or_method"
    assert bound(*args) == wanted
    print(
        owner.__name__,
        name,
        type(raw).__name__,
        type(bound).__name__,
        repr(bound(*args)),
    )
```

```sh
"$RP" -B "$IN/4690-original.py"
"$CP" -B "$IN/4690-original.py"
"$RP" -B "$IN/4690-draft-boundaries.py"
"$CP" -B "$IN/4690-draft-boundaries.py"
"$RP" -B "$IN/4690-native-additional.py"
"$CP" -B "$IN/4690-native-additional.py"
```

실행별 결과와 입력 링크는 다음과 같다. stdout/stderr 원문은 JSON 기록에 연결되어 있다.

- [4690-original-rp](../../agent-b/records/4690-original-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4690-original.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4690-original-cp](../../agent-b/records/4690-original-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4690-original.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4690-boundaries-rp](../../agent-b/records/4690-boundaries-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4690-draft-boundaries.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4690-boundaries-cp](../../agent-b/records/4690-boundaries-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4690-draft-boundaries.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4690-native-additional-rp](../../agent-b/records/4690-native-additional-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4690-native-additional.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4690-native-additional-cp](../../agent-b/records/4690-native-additional-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4690-native-additional.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.

핵심 출력은 다음과 같다. 판정에 사용하는 값과 결과는 양쪽에서 같았다.

`4690-original-rp`

```text
<class 'classmethod_descriptor'>
<class 'builtin_function_or_method'>
```

`4690-native-additional-rp`

```text
dict fromkeys classmethod_descriptor builtin_function_or_method {'a': 2}
int from_bytes classmethod_descriptor builtin_function_or_method 1
float fromhex classmethod_descriptor builtin_function_or_method 3.0
```

보충 기록: [원문 기반 검증 계획](../../agent-b/plans/4690.json), [파일 보존 검사](../../agent-b/environment/preservation.json).

본문의 짧은 원문 입력은 저장 원문 입력과 같은 두 조회다. 제출 초안의 “Both … classmethod_descriptor”는 새 결과와 모순된다. 원시/바인딩 결과를 분리해야 한다. 추가 디스크립터 범위는 이번에 확인한 dict.fromkeys, int.from_bytes, float.fromhex로 적는 편이 명확하다.

저장된 8ff947e83a65 근사 과거 입력은 타입 repr 대신 __name__ 두 개를 출력한다. stdout은 classmethod/method여서 원문 두 번째 출력과도 다르다. reporter의 실제 실행 파일로 간주할 수 없다. 이번에는 원문 타입 repr 두 개를 직접 비교했다.

과거 로그는 [실제 입력·출력 대조 기록](../../agent-b/sources/historical-primary-audit.json)에서 확인했다. 그 과거 실행 파일은 이번에 다시 실행하지 않았다. 익명화된 export 36개는 기록된 export SHA-256과 모두 일치했으나, 이는 로그 보존을 확인하는 것이며 과거 빌드 출처를 독립 실행으로 재입증한 것은 아니다.

PR #8780의 afad92bf1은 PyClassMethodDescriptor와 classmethod_descriptor 타입, native classmethod 생성·바인딩 경로를 추가한다.

[afad92bf1b78 diff](../../agent-b/logs/change-4690-afad92bf1.stdout)와 목표 조상 여부 [검사 기록](../../agent-b/records/ancestor-4690-afad92bf1.json)을 새로 확인했다. 인접 부모/변경 리비전을 실행하지 않았으므로 관련 변경으로만 분류한다.

모든 native classmethod와 오류 문구 전체가 동일하다고 주장하지 않는다.

명시된 초안 동작 주장 중 실행하지 않은 항목은 없다. 관찰과 다른 설명이나 입력 구분은 위에 수정 대상으로 적었다. 전체 라이브러리 지원이나 최초 수정 시점은 이 판정에 포함하지 않는다.

권고 문구: dict.__dict__["fromkeys"]는 classmethod_descriptor이고, dict.fromkeys는 builtin_function_or_method다. 바인딩과 확인한 추가 native 메서드의 동작도 CPython과 일치한다.

**기술 판정: 해결 확인**

**초안 판정: 문구 축소·수정**
