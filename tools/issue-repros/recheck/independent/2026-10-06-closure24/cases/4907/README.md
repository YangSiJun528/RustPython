# #4907 독립 검증

기술 판정은 **해결 확인**이다. 초안 판정은 **유지**다. 아래에 한정한 관찰이며 최초 수정 커밋을 확정한 결과가 아니다.

[원본 이슈](https://github.com/RustPython/RustPython/issues/4907)는 2026-10-05T16:10:22.988630+00:00 UTC 조회 시 **open**였다. 본문과 댓글 1개를 확인했다. 현재 열린 상태이므로 기술적으로 해결된 범위의 종료 검토 요청은 의미가 있다.

Ubuntu 18.04/RustPython 0.2.0에서 async 함수의 [await print(i) for i in [1,2,3]] 정의가 await outside async function SyntaxError로 거부된다. print 반환값은 await 불가능하므로 정의 성공과 함수 호출 성공을 구분해야 한다. 2025년 댓글은 실제 asyncio.sleep(1) 두 번을 기다리는 루프 예제를 제시했다.

초안은 원문 정의의 컴파일 성공과 댓글 예제의 실제 event loop 완료·lc done 출력을 주장한다.

원문 정의는 양쪽에서 종료 0. 따로 호출하면 1 출력 후 None을 await한 TypeError가 예상대로 발생한다. 댓글 원문은 실제 new_event_loop/create_task/wait/run_until_complete를 지나 lc done을 출력하고 종료 0이다. 확장 입력은 pending 없음, task.result() is None, 경과시간 1.9초 이상을 assert했다.

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

입력 파일 `4907-original.py` ([저장된 파일](../../agent-b/inputs/4907-original.py.txt)):

```python
async def bar():
    [await print(i) for i in [1, 2, 3]]
```

입력 파일 `4907-comment.py` ([저장된 파일](../../agent-b/inputs/4907-comment.py.txt)):

```python
import asyncio
import time


async def lc():
    [await asyncio.sleep(1) for _ in range(2)]
    print("lc done")


start = time.time()

loop = asyncio.new_event_loop()
tasks = [
    loop.create_task(lc()),
]
loop.run_until_complete(asyncio.wait(tasks))
loop.close()

end = time.time()
```

입력 파일 `4907-draft-0.py` ([저장된 파일](../../agent-b/inputs/4907-draft-0.py.txt)):

```python
import sys, json


def issue4907():
    import asyncio, time

    source = "async def bar():\n    [await print(i) for i in [1, 2, 3]]\n"
    namespace = {}
    exec(compile(source, "<original-4907>", "exec"), namespace)
    print("original compile: success")
    original = namespace["bar"]()
    try:
        original.send(None)
    except TypeError:
        print("original invocation: TypeError from awaiting print result")
    else:
        raise AssertionError("expected TypeError")

    async def lc():
        [await asyncio.sleep(1) for _ in range(2)]
        print("lc done")

    start = time.monotonic()
    loop = asyncio.new_event_loop()
    tasks = [loop.create_task(lc())]
    done, pending = loop.run_until_complete(asyncio.wait(tasks))
    assert not pending
    for task in done:
        assert task.result() is None
    loop.close()
    assert time.monotonic() - start >= 1.9
    print("comment execution: two awaited sleeps completed")


globals()["issue" + sys.argv[1]]()
```

```sh
"$RP" -B "$IN/4907-original.py"
"$CP" -B "$IN/4907-original.py"
"$RP" -B "$IN/4907-comment.py"
"$CP" -B "$IN/4907-comment.py"
"$RP" -B "$IN/4907-draft-0.py" 4907
"$CP" -B "$IN/4907-draft-0.py" 4907
```

실행별 결과와 입력 링크는 다음과 같다. stdout/stderr 원문은 JSON 기록에 연결되어 있다.

- [4907-original-rp](../../agent-b/records/4907-original-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4907-original.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4907-original-cp](../../agent-b/records/4907-original-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4907-original.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4907-comment-rp](../../agent-b/records/4907-comment-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4907-comment.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4907-comment-cp](../../agent-b/records/4907-comment-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4907-comment.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4907-draft-rp](../../agent-b/records/4907-draft-rp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4907-draft-0.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.
- [4907-draft-cp](../../agent-b/records/4907-draft-cp.json): 종료 0, timeout False; [입력](../../agent-b/inputs/4907-draft-0.py.txt). 동일 입력을 양쪽 인터프리터에서 실행했고 해당 경로의 출력/값 또는 실제 assert 완료를 확인했다. 종료 0이며 timeout 없음.

핵심 출력은 다음과 같다. 판정에 사용하는 값과 결과는 양쪽에서 같았다.

`4907-comment-rp`

```text
lc done
```

`4907-draft-rp`

```text
original compile: success
1
original invocation: TypeError from awaiting print result
lc done
comment execution: two awaited sleeps completed
```

보충 기록: [원문 기반 검증 계획](../../agent-b/plans/4907.json), [파일 보존 검사](../../agent-b/environment/preservation.json).

본문은 shared probes.py에서 해당 함수만 옮겼다. 댓글 원문보다 task 결과와 시간 assert가 추가된 버전이다. 이번에는 댓글 원문 파일과 확장 함수를 각각 실행해 생성만 한 coroutine을 성공으로 오인하지 않았다.

저장된 c7faae9b22/v0.2.0 및 3794c178be 입력은 같은 async 함수 정의이며 SyntaxError를 보여 준다. 이번 실제 asyncio 경로는 그 과거 정의-only 검증보다 넓다.

과거 로그는 [실제 입력·출력 대조 기록](../../agent-b/sources/historical-primary-audit.json)에서 확인했다. 그 과거 실행 파일은 이번에 다시 실행하지 않았다. 익명화된 export 36개는 기록된 export SHA-256과 모두 일치했으나, 이는 로그 보존을 확인하는 것이며 과거 빌드 출처를 독립 실행으로 재입증한 것은 아니다.

PR #5334의 7996a1011은 comprehension 요소의 await를 탐지하고 외부 async 문맥에 따라 async comprehension 및 호출 결과 await를 생성한다.

[7996a1011668 diff](../../agent-b/logs/change-4907-7996a1011.stdout)와 목표 조상 여부 [검사 기록](../../agent-b/records/ancestor-4907-7996a1011.json)을 새로 확인했다. 인접 부모/변경 리비전을 실행하지 않았으므로 관련 변경으로만 분류한다.

모든 asyncio·async generator 조합을 검증한 것은 아니다. Ubuntu의 OS 환경은 재현하지 않았다.

명시된 초안 동작 주장 중 실행하지 않은 항목은 없다. 관찰과 다른 설명이나 입력 구분은 위에 수정 대상으로 적었다. 전체 라이브러리 지원이나 최초 수정 시점은 이 판정에 포함하지 않는다.

권고 문구: 원문 async 함수 정의는 컴파일되며, 댓글의 실제 asyncio 이벤트 루프가 두 번의 sleep을 완료해 lc done을 출력한다.

**기술 판정: 해결 확인**

**초안 판정: 유지**
