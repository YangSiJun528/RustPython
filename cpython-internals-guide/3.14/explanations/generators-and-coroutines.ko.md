# 제너레이터와 코루틴은 중단된 Frame을 객체 안에 보존한다

일반 함수는 반환하면 그 호출의 실행 상태를 다시 이어 가지 않는다. 제너레이터는
`PyGenObject` 안에 `_PyInterpreterFrame`을 내장한다. `yield`에서 명령어 위치와 지역
변수·평가 스택을 보존하고, `next()`나 `send()`가 호출되면 이 Frame을 현재 실행 체인에
다시 연결해 중단 지점 다음부터 실행한다.

제너레이터 객체와 내부 Frame은 같은 것이 아니다. `PyGenObject`는 참조 관리 대상인
`PyObject`다. 그 안의 `_PyInterpreterFrame`은 독립된 Python 객체가 아닌 실행
레코드다. 제너레이터를 가리키는 강한 참조가 남아 있으면 중단된 Frame과 그 Frame이
참조하는 지역 객체도 함께 보존된다.

## 제너레이터 호출은 본문을 끝까지 실행하지 않는다

`yield from`까지 한꺼번에 볼 수 있는 예제를 사용하자.

```python
def child():
    yield 1
    return 7

def parent():
    result = yield from child()
    yield result
```

CPython 3.14.6에서 `parent` CodeObject의 값은 다음과 같다.

```text
co_varnames=('result',)
co_names=('child',)
co_consts=(None,)
co_stacksize=3
co_flags=0x23
co_exceptiontable.hex()='820e1d0190011b04910b1d01'
```

`co_flags`의 `0x20` 비트는 generator code임을 나타낸다. `adaptive=False`,
`show_caches=False`로 확인한 실제 바이트코드는 다음과 같다.

```text
 0 RETURN_GENERATOR
 2 POP_TOP
 4 RESUME                   0
 6 LOAD_GLOBAL              1 (child + NULL)
16 CALL                     0
24 GET_YIELD_FROM_ITER
26 LOAD_CONST               0 (None)
28 SEND                     3 (to 38)
32 YIELD_VALUE              1
34 RESUME                   2
36 JUMP_BACKWARD_NO_INTERRUPT 5 (to 28)
38 END_SEND
40 STORE_FAST               0 (result)
42 LOAD_FAST_BORROW         0 (result)
44 YIELD_VALUE              0
46 RESUME                   5
48 POP_TOP
50 LOAD_CONST               0 (None)
52 RETURN_VALUE
54 CLEANUP_THROW
56 JUMP_BACKWARD_NO_INTERRUPT 10 (to 38)
58 CALL_INTRINSIC_1         3 (INTRINSIC_STOPITERATION_ERROR)
60 RERAISE                  1

ExceptionTable:
  4 to 32 -> 58 [0] lasti
  32 to 34 -> 54 [2]
  34 to 56 -> 58 [0] lasti
```

제너레이터 함수 호출은 일반 함수처럼 offset 4의 본문을 곧장 끝까지 실행하지
않는다. 앞의 `RETURN_GENERATOR`가 준비된 실행 상태를 내장 Frame을 가진
`PyGenObject`로 옮기고 객체를 호출자에게 돌려준다. 첫 `next()` 또는
`send(None)`이 들어오면 offset 2의 `POP_TOP`이 재개 값 `None`을 먼저 소비한다. 이어
offset 4의 `RESUME 0`에서 사용자 본문에 진입한다.

## `yield`는 값을 내보내면서 재개 지점을 남긴다

첫 `next(g)`는 `send(None)`과 같은 재개 요청이다. Frame이 실행되다가
`YIELD_VALUE`에 도달하면 값을 호출자에게 넘기고 제너레이터를 중단 상태로 바꾼다.
이때 다음에 실행할 명령 위치와 Frame의 값, 제너레이터 쪽 예외 상태가 보존된다.

```text
created ── next/send ─→ running ── yield ─→ suspended
                          ▲                       │
                          └──── next/send ────────┘
                          │
                          └──── return/예외 ─→ completed
```

`incoming = yield value`에는 양방향 흐름이 있다. `value`는 호출자가 받는다. 다음
`g.send(x)`의 `x`는 중단되었던 `yield` 표현식의 결과가 되어 `incoming`에 들어간다.
제너레이터의 `__next__()`가 `send(None)`으로 정의되는 이유도 이 공통 재개 경로에
있다.

이 예제의 두 `YIELD_VALUE` 인자도 yielded value 자체가 아니다. CPython 3.14에서
`oparg=1`은 `yield from` 중에 중단된 상태를, `oparg=0`은 일반 yield 중단 상태를
표시하는 데 쓰인다. 첫 yield가 값 `1`이라서 인자가 1인 것이 아니다.

## 실제 실행에서 Frame과 평가 스택이 함께 멈춘다

다음 관찰값은 CPython 3.14.6에서 `inspect.getgeneratorstate()`와 `gi_frame`으로
확인한 결과다.

```text
parent() 직후:
  GEN_CREATED,   f_lasti=2,  f_locals={}

첫 next(g) 반환값: 1
  GEN_SUSPENDED, f_lasti=34, f_locals={}

둘째 next(g) 반환값: 7
  GEN_SUSPENDED, f_lasti=46, f_locals={'result': 7}

셋째 next(g): StopIteration(None)
  GEN_CLOSED,    gi_frame=None
```

첫 `next(g)`의 opcode와 `parent` 평가 스택을 연결하면 다음과 같다.

| 구간 | 평가 스택의 개념적 상태 | Frame 변화 |
|---|---|---|
| `LOAD_GLOBAL child` | `[NULL, child]` | parent가 실행 중이다 |
| `CALL 0` | `[child_generator]` | child 객체가 만들어진다 |
| `GET_YIELD_FROM_ITER` | `[child_iter]` | 위임할 iterator를 준비한다 |
| `LOAD_CONST None` | `[child_iter, None]` | 첫 send 값은 `None`이다 |
| `SEND` | child가 1을 내놓아 `[child_iter, 1]` | 실행 중에는 child Frame이 parent에 연결된다 |
| `YIELD_VALUE 1` | 1은 호출자로 나가고 위임 상태는 보존된다 | parent Frame도 호출 체인에서 빠진다 |

관찰된 `f_lasti=34`는 단순히 직전에 실행한 `YIELD_VALUE`의 offset 32를 복사한
값이 아니다. 3.14의 Frame은 중단 상태에서 재개할 `RESUME 2` 위치를 가리키도록
명령 위치를 조정한다. `f_lasti`를 언제나 “방금 실행한 opcode”라고만 해석하면
generator에서 어긋난다.

둘째 `next(g)`는 `None`을 중단된 yield 표현식의 결과로 넣고 offset 28의
`SEND`로 돌아간다. child가 `return 7`을 실행하면 그 값은
`StopIteration(7)`의 종료 값이 된다. `SEND`는 이 정상 종료를 인식해 offset
38로 건너뛰고, `END_SEND`가 child iterator를 정리한 뒤 7만 남긴다.
`STORE_FAST result`가 지역 슬롯에 7을 저장하고 두 번째 `YIELD_VALUE 0`이 같은
값을 호출자에게 내놓는다. 그래서 두 번째 중단 상태의 `f_locals`에만
`{'result': 7}`이 보인다.

셋째 `next(g)`가 보낸 `None`은 `RESUME 5` 뒤 `POP_TOP`에서 소비된다. 이어
`LOAD_CONST None`, `RETURN_VALUE`가 parent를 정상 종료하고, 호출자는
`StopIteration(None)`을 본다. 종료 뒤 `gi_frame=None`이므로 이 실행은 다시
재개할 수 없다.

## 중단된 Frame은 활성 호출 체인에서 잠시 빠진다

제너레이터가 멈춰 있는 동안 내장 Frame은 객체 안에 있지만 현재 스레드의 활성 호출
체인에는 없다. 재개할 때 호출자 Frame과 링크되고, 다시 `yield`하면 실행 상태를
보존한 채 체인에서 빠진다. Frame의 `previous` 연결은 실행 중 호출 관계를 나타낼 뿐,
중단된 모든 제너레이터를 항상 매달아 두는 전역 목록이 아니다.

`yield from`은 이 재개 요청을 하위 이터레이터에 위임한다. `SEND`는 값과 실행 제어를
전달하며, 종료 값과 주입된 예외도 위임 경로를 따라 처리한다. `CLEANUP_THROW`는 특히
`throw()`나 `close()`로 예외를 주입한 경로를 정리한다. 모든 정상 종료를 이 명령
하나가 처리한다고 이해하면 안 된다.

사용자가 `try`를 쓰지 않았는데도 예외 테이블이 생긴 이유도 generator protocol에
있다. offset 32의 `YIELD_VALUE`에서 `throw()` 경로가 들어오면 depth 2를 보존한
채 `CLEANUP_THROW`로 이동해야 한다. generator 본문 밖으로 잘못 새어 나온
`StopIteration`은 offset 58의 intrinsic에서 별도 오류로 바뀐다. 이 테이블은
소스의 `except` 절만 표현하는 목록이 아니다.

## 세 객체는 재개 규약과 내보내는 값이 다르다

| 종류 | 런타임 객체 | 주된 중단 지점 | 바깥에서 재개하는 인터페이스 |
|---|---|---|---|
| 제너레이터 | `PyGenObject` | `yield`, `yield from` | `next()`, `send()`, `throw()` |
| 네이티브 코루틴 | `PyCoroObject` | `await` | await 구동기와 `send()` |
| 비동기 제너레이터 | `PyAsyncGenObject` | `yield`, `await` | `__anext__()`, `asend()`, `athrow()` |

세 타입은 Python 수준의 사용법과 종료 규약이 같지 않다. 다만 실행 중인 위치와
지역 값, 평가 스택을 객체 안의 Frame에 남겼다가 재개한다는 수명 모델은 공유한다.

## 관찰용 Frame이 제너레이터보다 오래 살 수 있다

`g.gi_frame`으로 보이는 것은 내장 C 레코드 자체가 아니라 Python에 노출되는
`PyFrameObject`다. 관찰이 필요할 때 지연 생성되며, 외부 코드가 이 객체를 보관할 수
있다.

제너레이터가 먼저 정리되는데 `PyFrameObject`가 계속 살아야 한다면 CPython은
`take_ownership()`으로 필요한 `_PyInterpreterFrame` 상태를 Frame 객체 쪽에 옮긴다.
이 과정은 제너레이터 메모리가 사라진 뒤 Frame 객체가 무효 주소를 가리키지 않게 한다.
Frame이 정리되어 지역 객체 참조를 놓더라도 다른 참조가 남은 지역 객체는 독립적으로
살아남는다.

`async def`가 만드는 네이티브 코루틴도 `await`에서 실행 상태를 보존한다. 제너레이터
기반 코루틴과 문법·타입은 다르지만, 중단된 실행을 다시 시작하려면 호출별 Frame이
객체 수명에 맞춰 살아 있어야 한다는 원리는 같다. 정확한 내부 필드와 소유자 상태는
[런타임 객체 참고 자료](../reference/runtime-objects.ko.md)를 참고한다.

## 흔한 오해와 버전 경계

- 제너레이터 호출은 “첫 yield까지 실행한 호출”이 아니다. 호출 직후 상태는
  `GEN_CREATED`이며 본문 `RESUME 0`도 아직 지나지 않았다.
- `yield`는 지역 변수를 딕셔너리에 복사해 두는 기능이 아니다. locals-plus 슬롯,
  평가 스택, 명령 위치가 내장 `_PyInterpreterFrame` 안에 함께 남는다.
- 중단된 Frame이 호출자 Frame chain에 계속 연결된 것도 아니다. 재개 중에만
  활성 체인에 붙고 yield할 때 다시 분리된다.
- `yield from`은 단순한 `for` 반복이 아니다. 값뿐 아니라 `send`, `throw`,
  `close`, 하위 generator의 반환값을 전달한다.
- `gi_frame`으로 보이는 `PyFrameObject`와 실행용 `_PyInterpreterFrame`은 역할과
  수명이 다른 표현이다.

여기의 opcode, `RESUME` 인자, offset과 exception table은 CPython 3.14.6
구현값이다. 다른 버전에서는 `SEND` 주변의 보조 명령과 중단 위치가 달라질 수
있다. 네이티브 코루틴과 비동기 제너레이터도 Frame 보존 원리는 공유하지만 종료
예외와 외부 재개 protocol까지 일반 generator와 같다고 보면 안 된다.

---

[설명 문서 목록](README.ko.md)

기준 글:

- [평가 루프와 세 가지 스택](evaluation-loop.ko.md)
- [바인딩과 객체 수명](objects-and-lifetimes.ko.md)

다른 갈래:

- [예외 처리](exceptions.ko.md)
- [특수화와 JIT](specialization-and-jit.ko.md)
- [문자열 인터닝](string-interning.ko.md)

관련 글:

- [런타임 객체 참고 자료](../reference/runtime-objects.ko.md)
