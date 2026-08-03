# 예외 테이블과 Frame 되감기가 전파를 나눠 맡는다

CPython은 `try` 블록을 실행할 때마다 현재 handler를 별도 스택에 넣었다 빼지
않는다. 컴파일러가 보호 범위와 handler 위치를 CodeObject의
`co_exceptiontable`에 기록해 두고, opcode가 실제로 실패했을 때만 현재 명령
위치로 이 테이블을 조회한다. 이것이 CPython에서 말하는 zero-cost exception의
핵심이다.

opcode가 실패하면 공통 error 경로가 현재 Frame 위치를 traceback에 먼저 기록하고
예외 테이블에서 handler를 찾는다. handler가 있으면 평가 스택을 약속된 깊이로
복구하고 그 위치에서 실행을 재개한다. 현재 Frame에 handler가 없으면 Frame을
빠져나간다. 그러면 호출자의 `CALL`도 실패한 명령이 되므로, 호출자 error 경로가
그 Frame 위치를 기록하고 다시 handler를 찾는다.

## 컴파일러가 정상 경로 밖에 처리 정보를 둔다

다음 함수에는 정상 반환과 `ZeroDivisionError` 처리 경로가 함께 있다.

```python
def safe_div(x):
    try:
        return 10 // x
    except ZeroDivisionError:
        return None
```

CPython 3.14.6에서 `adaptive=False`, `show_caches=False`로 확인한 CodeObject와
바이트코드는 다음과 같다.

```text
co_names=('ZeroDivisionError',)
co_consts=(10, None)
co_stacksize=4
co_exceptiontable.hex()='82080b008b0b1a0399011a03'

 0 RESUME                   0
 2 NOP
 4 LOAD_SMALL_INT          10
 6 LOAD_FAST_BORROW         0 (x)
 8 BINARY_OP                2 (//)
20 RETURN_VALUE
22 PUSH_EXC_INFO
24 LOAD_GLOBAL              0 (ZeroDivisionError)
34 CHECK_EXC_MATCH
36 POP_JUMP_IF_FALSE        5 (to 50)
40 NOT_TAKEN
42 POP_TOP
44 POP_EXCEPT
46 LOAD_CONST               1 (None)
48 RETURN_VALUE
50 RERAISE                  0
52 COPY                     3
54 POP_EXCEPT
56 RERAISE                  1

ExceptionTable:
  4 to 20  -> 22 [0]
  22 to 44 -> 52 [1] lasti
  50 to 52 -> 52 [1] lasti
```

위 세 범위는 사람이 읽기 쉽게 쓴 반열린 구간이다. 실제로
`dis.Bytecode(safe_div).exception_entries`는 다음 세 값을 돌려줬다.

```text
(start=4,  end=20, target=22, depth=0, lasti=False)
(start=22, end=44, target=52, depth=1, lasti=True)
(start=50, end=52, target=52, depth=1, lasti=True)
```

첫 항목의 `[4, 20)`은 나눗셈을 준비하고 실행하는 명령을 보호한다.
`BINARY_OP //`에서 예외가 나면 offset 22의 handler 준비 코드로 이동한다.
`RETURN_VALUE`가 있는 offset 20은 범위에 포함되지 않는다. 뒤의 두 항목은
예외를 검사하고 다시 발생시키는 handler 자체에서 또 예외가 났을 때 정리할
경로다.

컴파일 과정에서는 `try`의 시작과 끝을 나타내는 의사 명령을 사용할 수 있지만,
최종 바이트코드에는 이를 매번 실행할 opcode로 남기지 않는다. 대신 예외
테이블에 보호 범위, handler 위치, 복구할 평가 스택 깊이와 `lasti` 여부를
압축해 저장한다. 이 예제의 테이블은 12바이트지만 handler를 찾는 데 필요한
세 범위를 모두 표현한다.

- 보호할 바이트코드 범위
- 예외를 넘길 handler 위치
- handler가 시작할 때 필요한 평가 스택 깊이
- 원래 실패한 명령 위치인 `lasti`를 스택에 보존할지 여부

예외가 발생하지 않는 동안에는 이 테이블을 조회할 이유가 없다.
zero-cost는 예외 객체 생성과 Frame 되감기(unwind)까지 공짜라는 뜻이 아니라, 정상
경로에서 handler 상태를 계속 관리하는 비용을 피한다는 뜻이다.

정상 입력인 `safe_div(2)`에서는 평가 스택이 다음처럼 변한다.

```text
[]
  -- LOAD_SMALL_INT 10 --> [10]
  -- LOAD_FAST_BORROW x --> [10, 2]
  -- BINARY_OP // --------> [5]
  -- RETURN_VALUE --------> 호출자에게 5 전달
```

`NOP`는 `try`의 의미를 런타임 stack에 넣는 명령이 아니다. 소스 위치와 컴파일된
제어 흐름에 남은 표시일 뿐, 정상 경로에서 handler를 push하지 않는다.

## 실패한 opcode가 공통 예외 경로를 연다

opcode 구현이 실패하면 예외 상태를 설정하고 평가 루프의 공통 unwind 경로로
이동한다. 이후 제어 흐름은 다음 순서로 갈린다.

```text
opcode 실패
    ↓
현재 Frame의 실패 위치를 traceback에 기록
    ↓
현재 명령 오프셋으로 co_exceptiontable 검색
    ├─ handler 있음 → 평가 스택 복구 → 예외 정보 push → handler로 점프
    └─ handler 없음 → 현재 Frame 되감기 → 호출자의 CALL 실패
                                            ↓
                           호출자 위치 기록 → 호출자 테이블 검색
```

예외는 표현식 계산 중에도 발생한다. 이때 평가 스택에는 아직 쓰지 못한
피연산자와 중간 결과가 남아 있을 수 있다. handler는 임의의 스택 모양에서
시작할 수 없으므로, 인터프리터는 테이블에 기록된 깊이까지 값을 버린다.
필요하면 `lasti`를 올리고 예외를 올린 뒤 handler의 첫 명령으로 이동한다.

`safe_div(0)`에서 `BINARY_OP //`가 실패한 뒤의 상태를 따라가 보자. 첫 예외
테이블 항목의 `depth=0`에 맞춰 불완전한 계산값을 모두 버리고 예외 객체를
올린 상태에서 target 22로 간다.

| opcode | 평가 스택의 개념적 변화 | 의미 |
|---|---|---|
| handler 진입 | `[] → [exc]` | unwind 경로가 발생한 예외를 전달한다 |
| `PUSH_EXC_INFO` | `[exc] → [previous_exc, exc]` | 이전 예외 상태를 보존하고 새 예외를 활성화한다 |
| `LOAD_GLOBAL` | `→ [previous_exc, exc, ZeroDivisionError]` | except 절의 타입을 읽는다 |
| `CHECK_EXC_MATCH` | 마지막 타입을 판정값으로 바꾼다 | 현재 예외가 해당 타입인지 검사한다 |
| `POP_JUMP_IF_FALSE` | 판정값을 소비한다 | 맞지 않으면 offset 50의 재발생 경로로 간다 |
| `POP_TOP`, `POP_EXCEPT` | 예외와 저장한 상태를 정리한다 | 일치한 except 절을 시작한다 |
| `LOAD_CONST None` | `[] → [None]` | handler의 반환값을 만든다 |
| `RETURN_VALUE` | `[None] → []` | 호출자에게 `None`을 돌려준다 |

예외 테이블은 어느 `except` 타입이 맞는지 직접 기록하지 않는다. 먼저 보호
범위에 대응하는 handler 진입점을 찾은 뒤 `CHECK_EXC_MATCH`가 Python의 예외
타입 규칙으로 절을 고른다. 예를 들어 `x`의 `//` 구현이 `TypeError`를 내면
`ZeroDivisionError`와 맞지 않으므로 `RERAISE` 경로로 넘어간다.

`lasti`는 특히 `finally`를 실행한 뒤 예외를 다시 발생시킬 때 필요하다.
현재 명령 위치는 이미 `finally` 안으로 이동했으므로, 원래 어느 명령에서
실패했는지를 별도로 보존해야 traceback과 디버깅 위치를 복구할 수 있다.

## handler가 없으면 Frame 단위로 전파된다

현재 CodeObject의 예외 테이블에 맞는 항목이 없으면 인터프리터는 그 Frame의
실행을 끝내고 호출자로 예외를 넘긴다. 이때 현재 Frame의 실패 위치는 handler
검색보다 앞선 error 경로에서 이미 traceback에 기록됐다. 호출자에서는 피호출자를
실행하던 `CALL` 위치가 새 실패 위치다. 호출자 쪽 error 경로도 그 위치를
traceback에 보탠 뒤 예외 테이블을 찾는다. `try`가 해당 호출을 감싸고 있었다면 그
handler가 예외를 받을 수 있다.

인터프리터는 handler를 찾거나 최상위 Frame에 도달할 때까지 이 과정을 반복한다.
끝까지 handler가 없으면 평가 함수는 실패를 나타내고, 사용자는 각 Frame의 실패
경로에서 기록된 호출 경로를 traceback으로 보게 된다. 같은 Frame 안에서 예외를
잡더라도 최초 실패 위치를 기록하는 단계 자체는 이미 지나간다.

예외 전파는 일반 이름 조회와 다르다. 이름을 찾을 때는 호출자 Frame을 탐색하지
않지만, 처리되지 않은 예외는 실제 호출 관계를 따라 올라간다. Frame stack이
필요한 대표적인 이유가 이 되감기와 traceback 구성이다.

예외 테이블의 가변 길이 인코딩, code unit 기준 오프셋, `__context__`와
`__cause__` 설정까지 확인하려면 기존
[예외 처리 상세 노트](../../../cpython-internals-notes/3.14/program-execution/README.ko.md#제4부-예외-처리)를
참고한다.

## 흔한 오해와 버전 경계

- 예외 테이블의 `depth`는 Frame stack 깊이가 아니라 현재 Frame의 평가 스택
  깊이다.
- 예외 전파만 호출자 Frame을 따라간다. 일반 변수 이름을 찾으려고 같은 경로를
  걷는 것은 아니다.
- traceback은 예외가 처음 생긴 순간 완성된 고정 목록이 아니다. opcode 실패의
  error 경로가 현재 Frame을 먼저 기록하고, 예외가 전파되어 호출자의 `CALL`도
  실패하면 호출자 error 경로가 그 Frame을 차례로 더한다.
- `dis`가 보여 주는 exception entry의 오프셋은 바이트 단위다. 내부 압축
  테이블은 code unit 단위 값을 저장하고 parser가 표시용 오프셋으로 바꾼다.
- `co_exceptiontable`만 다른 CodeObject에 복사하거나 바이트코드 오프셋을 임의로
  바꾸면 보호 범위와 stack depth가 어긋난다. 둘은 한 컴파일 결과로 다뤄야 한다.

이 구조는 CPython 3.11 이후의 table-driven 예외 처리에 해당한다. 이전 버전의
`SETUP_FINALLY`와 block stack을 현재 실행 모델에 그대로 대입하면 안 된다.
여기에 적은 opcode, offset, table bytes는 CPython 3.14.6 결과이며 다른 버전의
내부 형식과 호환된다고 가정할 수 없다.

---

[설명 문서 목록](README.ko.md)

기준 글:

- [평가 루프와 세 가지 스택](evaluation-loop.ko.md)

다른 갈래:

- [제너레이터와 코루틴](generators-and-coroutines.ko.md)
- [특수화와 JIT](specialization-and-jit.ko.md)

관련 글:

- [CodeObject 필드와 바이트코드 인자](../reference/code-object-and-bytecode.ko.md)
