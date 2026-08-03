# 제너레이터와 코루틴은 중단된 Frame을 객체 안에 보존한다

일반 함수는 반환하면 그 호출의 실행 상태를 다시 이어 가지 않는다. 제너레이터는 `PyGenObject` 안에 `_PyInterpreterFrame`을 내장하고, `yield`에서 명령어 위치와 지역 변수·평가 스택을 보존한다. `next()`나 `send()`가 호출되면 이 Frame을 현재 실행 체인에 다시 연결해 중단 지점 다음부터 실행한다.

제너레이터 객체와 내부 Frame은 같은 것이 아니다. `PyGenObject`는 참조 관리 대상인 `PyObject`이고, 그 안의 `_PyInterpreterFrame`은 독립된 Python 객체가 아닌 실행 레코드다. 제너레이터를 가리키는 강한 참조가 남아 있으면 중단된 Frame과 그 Frame이 참조하는 지역 객체도 함께 보존된다.

네이티브 코루틴과 비동기 제너레이터는 각각 `PyCoroObject`, `PyAsyncGenObject`라는 별도 타입이지만, 객체 안에 Frame을 두고 중단·재개한다는 핵심 구조를 공유한다. 이 글은 CPython 3.14의 그 공통 수명 모델에 집중한다.

## 제너레이터 호출은 본문을 끝까지 실행하지 않는다

```py
def counter(start):
    value = start
    while True:
        incoming = yield value
        value = value + 1 if incoming is None else incoming
```

CPython 3.14의 제너레이터 코드 앞부분에는 `RETURN_GENERATOR`가 있다. `counter(10)`을 호출하면 이 명령이 내장 Frame을 가진 제너레이터 객체를 만들고 호출자에게 돌려준다. 나머지 본문은 첫 `next()` 또는 `send(None)`이 들어올 때 실행된다.

```text
counter(10)
    ↓
PyGenObject
├── 실행·중단 상태
├── 예외 상태
└── 내장 _PyInterpreterFrame
    ├── CodeObject 참조
    ├── localsplus: start, value, incoming, ...
    ├── 평가 스택
    └── instr_ptr
```

## `yield`는 값을 내보내면서 재개 지점을 남긴다

첫 `next(g)`는 `send(None)`과 같은 재개 요청이다. Frame이 실행되다가 `YIELD_VALUE`에 도달하면 값을 호출자에게 넘기고 제너레이터를 중단 상태로 바꾼다. 이때 다음에 실행할 명령 위치와 Frame의 값, 제너레이터 쪽 예외 상태가 보존된다.

```text
created ── next/send ─→ running ── yield ─→ suspended
                          ▲                       │
                          └──── next/send ────────┘
                          │
                          └──── return/예외 ─→ completed
```

`incoming = yield value`에는 양방향 흐름이 있다. `value`는 호출자가 받고, 다음 `g.send(x)`의 `x`는 중단되었던 `yield` 표현식의 결과가 되어 `incoming`에 들어간다. 제너레이터의 `__next__()`가 `send(None)`으로 정의되는 이유도 이 공통 재개 경로에 있다.

## 중단된 Frame은 활성 호출 체인에서 잠시 빠진다

제너레이터가 멈춰 있는 동안 내장 Frame은 객체 안에 있지만 현재 스레드의 활성 호출 체인에는 없다. 재개할 때 호출자 Frame과 링크되고, 다시 `yield`하면 실행 상태를 보존한 채 체인에서 빠진다. 따라서 Frame의 `previous` 연결은 실행 중 호출 관계를 나타낼 뿐, 중단된 모든 제너레이터를 항상 매달아 두는 전역 목록이 아니다.

`yield from`은 이 재개 요청을 하위 이터레이터에 위임한다. `SEND`는 값과 실행 제어를 전달하고, 종료 값과 주입된 예외도 위임 경로를 따라 처리한다. `CLEANUP_THROW`는 특히 `throw()`나 `close()`로 예외를 주입한 경로를 정리하므로 모든 정상 종료를 이 명령 하나가 처리한다고 이해하면 안 된다.

## 세 객체는 재개 규약과 내보내는 값이 다르다

| 종류 | 런타임 객체 | 주된 중단 지점 | 바깥에서 재개하는 인터페이스 |
|---|---|---|---|
| 제너레이터 | `PyGenObject` | `yield`, `yield from` | `next()`, `send()`, `throw()` |
| 네이티브 코루틴 | `PyCoroObject` | `await` | await 구동기와 `send()` |
| 비동기 제너레이터 | `PyAsyncGenObject` | `yield`, `await` | `__anext__()`, `asend()`, `athrow()` |

세 타입은 Python 수준의 사용법과 종료 규약이 같지 않다. 다만 실행 중인 위치와
지역 값, 평가 스택을 객체 안의 Frame에 남겼다가 재개한다는 수명 모델은 공유한다.

## 관찰용 Frame이 제너레이터보다 오래 살 수 있다

`g.gi_frame`으로 보이는 것은 내장 C 레코드 자체가 아니라 Python에 노출되는 `PyFrameObject`다. 관찰이 필요할 때 지연 생성되며, 외부 코드가 이 객체를 보관할 수 있다.

제너레이터가 먼저 정리되는데 `PyFrameObject`가 계속 살아야 한다면 CPython은 `take_ownership()`으로 필요한 `_PyInterpreterFrame` 상태를 Frame 객체 쪽에 옮긴다. 이 과정은 제너레이터 메모리가 사라진 뒤 Frame 객체가 무효 주소를 가리키지 않게 한다. Frame이 정리되어 지역 객체 참조를 놓더라도, 다른 참조가 남은 지역 객체는 독립적으로 살아남는다.

`async def`가 만드는 네이티브 코루틴도 `await`에서 실행 상태를 보존한다. 제너레이터
기반 코루틴과 문법·타입은 다르지만, 중단된 실행을 다시 시작하려면 호출별 Frame이
객체 수명에 맞춰 살아 있어야 한다는 원리는 같다. 정확한 내부 필드와 소유자 상태는
[런타임 객체 참고 자료](../reference/runtime-objects.ko.md)를 참고한다.

[가이드 홈](../README.ko.md) · 기준 흐름: [평가 루프와 세 가지 스택](evaluation-loop.ko.md) · 관련 설명: [바인딩과 객체 수명](objects-and-lifetimes.ko.md)
