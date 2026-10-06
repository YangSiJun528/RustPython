# #5179 독립 검증

Python 코드 블록은 커밋 훅으로 서식을 정리했고, 정리 전후의 AST가 같음을 확인했다. 정확한 실행 입력은 링크된 `.py.txt` 사본과 원본 해시를 기준으로 한다.

기술 판정은 **해결 확인**이다. 초안 판정은 **유지**다. 아래에 한정한 관찰이며 최초 수정 커밋을 확정한 결과가 아니다.

[원본 이슈](https://github.com/RustPython/RustPython/issues/5179)는 2026-10-05T16:10:25.140900+00:00 UTC 조회 시 **open**였다. 본문과 댓글 0개를 확인했다. 현재 열린 상태이므로 기술적으로 해결된 범위의 종료 검토 요청은 의미가 있다.

PEP 688/Python 3.12의 builtin buffer 접근 메서드 지원 요청이다. bytes, array, memoryview 등에서 __buffer__를 실제로 사용하고 필요한 타입의 __release_buffer__가 동작해야 한다. 단순 hasattr 성공만으로는 부족하다.

초안은 builtin/subclass 메서드, 읽기·쓰기·release, export 중 resize 금지와 해제 후 resize 및 custom exporter callback을 주장한다.

bytes/bytearray/array/memoryview/bytes subclass/bytearray subclass/mmap 7종의 메서드·read payload·WRITABLE 요청 결과가 CPython과 같다. bytes 계열에 release 메서드가 없는 것도 CPython과 같다. 추가 실제 쓰기 입력은 bytearray/array/subclass의 원본 메모리를 바꾸고 export 중 append의 BufferError, release 뒤 view ValueError 및 append 성공을 assert했다. memoryview와 mmap 쓰기·해제, custom exporter get/release callback도 완료했다.

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

입력 파일 `5179-draft-0.py` ([저장된 파일](../../agent-b/inputs/5179-draft-0.py.txt)):

```python
import sys, json


def issue5179():
    import array, mmap, inspect

    class BytesSubclass(bytes):
        pass

    class BytearraySubclass(bytearray):
        pass

    objects = [
        bytes(b"abc"),
        bytearray(b"abc"),
        array.array("B", b"abc"),
        memoryview(b"abc"),
        BytesSubclass(b"abc"),
        BytearraySubclass(b"abc"),
    ]
    mapping = mmap.mmap(-1, 3)
    mapping[:] = b"abc"
    objects.append(mapping)
    rows = []
    for obj in objects:
        row = {
            "type": type(obj).__name__,
            "buffer": hasattr(obj, "__buffer__"),
            "release": hasattr(obj, "__release_buffer__"),
        }
        view = obj.__buffer__(0)
        assert isinstance(view, memoryview)
        row["data"] = view.tobytes().decode("ascii")
        row["readonly"] = view.readonly
        assert row["data"] == "abc"
        if hasattr(obj, "__release_buffer__"):
            obj.__release_buffer__(view)
            try:
                view.tobytes()
            except ValueError:
                row["released"] = True
            else:
                row["released"] = False
        else:
            view.release()
        try:
            writable = obj.__buffer__(inspect.BufferFlags.WRITABLE)
        except Exception as e:
            row["writable"] = type(e).__name__
        else:
            row["writable"] = not writable.readonly
            if hasattr(obj, "__release_buffer__"):
                obj.__release_buffer__(writable)
            else:
                writable.release()
        rows.append(row)
    objects[3].release()
    mapping.close()
    ba = bytearray(b"abc")
    view = ba.__buffer__(0)
    try:
        ba.append(100)
    except BufferError:
        pass
    else:
        raise AssertionError("resize while exported should be blocked")
    ba.__release_buffer__(view)
    ba.append(100)
    assert ba == b"abcd"
    events = []

    class Exporter:
        def __buffer__(self, flags):
            events.append(["get", flags])
            self.view = memoryview(bytearray(b"xyz"))
            return self.view

        def __release_buffer__(self, view):
            assert view is self.view
            events.append(["release"])
            view.release()

    obj = Exporter()
    with memoryview(obj) as view:
        assert view.tobytes() == b"xyz"
        view[0] = 65
        assert view.tobytes() == b"Ayz"
    assert events[-1] == ["release"]
    print(
        json.dumps(
            {"builtins": rows, "resize_after_release": True, "custom_exporter": events},
            sort_keys=True,
        )
    )


globals()["issue" + sys.argv[1]]()
```

입력 파일 `5179-write-resize.py` ([저장된 파일](../../agent-b/inputs/5179-write-resize.py.txt)):

```python
import array, inspect, mmap


class BytearrayChild(bytearray):
    pass


objects = [bytearray(b"abc"), array.array("B", b"abc"), BytearrayChild(b"abc")]
for obj in objects:
    view = obj.__buffer__(inspect.BufferFlags.WRITABLE)
    assert view.tobytes() == b"abc"
    view[0] = 65
    assert bytes(obj) == b"Abc"
    try:
        obj.append(100)
    except BufferError:
        print(type(obj).__name__, "write-through and resize blocked")
    else:
        raise AssertionError("export must prevent resize")
    obj.__release_buffer__(view)
    try:
        view.tobytes()
    except ValueError:
        pass
    else:
        raise AssertionError("released view still accessible")
    obj.append(100)
    assert bytes(obj) == b"Abcd"
    print(type(obj).__name__, "released view invalid and resize allowed")

data = bytearray(b"abc")
original = memoryview(data)
view = original.__buffer__(inspect.BufferFlags.WRITABLE)
view[1] = 66
assert data == b"aBc"
original.__release_buffer__(view)
original.release()
data.append(100)
assert data == b"aBcd"
print("memoryview write-through and release passed")

mapping = mmap.mmap(-1, 3)
mapping[:] = b"abc"
view = mapping.__buffer__(inspect.BufferFlags.WRITABLE)
view[2] = 67
assert mapping[:] == b"abC"
mapping.__release_buffer__(view)
mapping.close()
print("mmap write-through, release and close passed")
```

```sh
"$RP" -B "$IN/5179-draft-0.py" 5179
"$CP" -B "$IN/5179-draft-0.py" 5179
"$RP" -B "$IN/5179-write-resize.py"
"$CP" -B "$IN/5179-write-resize.py"
```

실행별 결과와 입력 링크는 다음과 같다. stdout/stderr 원문은 JSON 기록에 연결되어 있다.

- [5179-draft-rp](../../agent-b/records/5179-draft-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/5179-draft-0.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [5179-draft-cp](../../agent-b/records/5179-draft-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/5179-draft-0.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [5179-write-resize-rp](../../agent-b/records/5179-write-resize-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/5179-write-resize.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [5179-write-resize-cp](../../agent-b/records/5179-write-resize-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/5179-write-resize.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.

핵심 출력은 다음과 같다. 판정에 사용하는 값과 결과는 양쪽에서 같았다.

`5179-write-resize-rp`

```text
bytearray write-through and resize blocked
bytearray released view invalid and resize allowed
array write-through and resize blocked
array released view invalid and resize allowed
BytearrayChild write-through and resize blocked
BytearrayChild released view invalid and resize allowed
memoryview write-through and release passed
mmap write-through, release and close passed
```

`5179-draft-rp`의 builtin/custom exporter 출력(양쪽 동일):

```text
{"builtins": [{"buffer": true, "data": "abc", "readonly": true, "release": false, "type": "bytes", "writable": "BufferError"}, {"buffer": true, "data": "abc", "readonly": false, "release": true, "released": true, "type": "bytearray", "writable": true}, {"buffer": true, "data": "abc", "readonly": false, "release": true, "released": true, "type": "array", "writable": true}, {"buffer": true, "data": "abc", "readonly": true, "release": true, "released": true, "type": "memoryview", "writable": "BufferError"}, {"buffer": true, "data": "abc", "readonly": true, "release": false, "type": "BytesSubclass", "writable": "BufferError"}, {"buffer": true, "data": "abc", "readonly": false, "release": true, "released": true, "type": "BytearraySubclass", "writable": true}, {"buffer": true, "data": "abc", "readonly": false, "release": true, "released": true, "type": "mmap", "writable": true}], "custom_exporter": [["get", 284], ["release"]], "resize_after_release": true}
```

보충 기록: [원문 기반 검증 계획](../../agent-b/plans/5179.json), [파일 보존 검사](../../agent-b/environment/preservation.json).

본문은 shared probes.py의 issue5179를 분리한 입력이다. 기존 본문은 builtin의 WRITABLE 획득과 custom exporter 쓰기를 확인하지만 모든 builtin에 직접 쓰지는 않았다. 이번 별도 입력이 mutable builtin별 실제 쓰기와 array resize도 보강했다.

a8ab7dd388의 저장 코드는 4개 builtin의 hasattr를 출력하고 존재할 때만 payload를 읽는다. 모두 메서드 부재 False인데도 종료 0이었다. 이는 성공 기록이 아니다. 새 검증은 실제 호출·쓰기·수명 제한을 검증한다.

과거 로그는 [실제 입력·출력 대조 기록](../../agent-b/sources/historical-primary-audit.json)에서 확인했다. 그 과거 실행 파일은 이번에 다시 실행하지 않았다. 익명화된 export 36개는 기록된 export SHA-256과 모두 일치했으나, 이는 로그 보존을 확인하는 것이며 과거 빌드 출처를 독립 실행으로 재입증한 것은 아니다.

PR #8523의 목표 조상 c603eb7c9는 Python-facing buffer/release slot과 managed export, 타입별 release 노출을 추가한다. 저장 diff에서 slot_defs, descriptor, memory, buffer 구현을 확인했다.

[c603eb7c9ad7 diff](../../agent-b/logs/change-5179-c603eb7c9.stdout)와 목표 조상 여부 [검사 기록](../../agent-b/records/ancestor-5179-c603eb7c9.json)을 새로 확인했다. 인접 부모/변경 리비전을 실행하지 않았으므로 관련 변경으로만 분류한다.

C ABI 전체, 모든 buffer flag·수명/동시성 조합은 미검증이며 초안도 그 범위를 주장하지 않는다.

명시된 초안 동작 주장 중 실행하지 않은 항목은 없다. 관찰과 다른 설명이나 입력 구분은 위에 수정 대상으로 적었다. 전체 라이브러리 지원이나 최초 수정 시점은 이 판정에 포함하지 않는다.

권고 문구: 확인한 builtin/subclass의 buffer 메서드와 실제 쓰기·release가 동작하며, bytearray/array는 export 중 resize를 막고 해제 뒤 허용한다.

**기술 판정: 해결 확인**

**초안 판정: 유지**
