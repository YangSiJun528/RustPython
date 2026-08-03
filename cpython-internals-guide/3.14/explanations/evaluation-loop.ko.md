# 평가 루프는 Frame의 상태를 바꾸며 바이트코드를 실행한다

CodeObject만으로는 프로그램이 실행되지 않는다. CodeObject에는 바이트코드와
상수·이름 같은 정적 정보가 있고, Frame에는 이번 호출의 인수, 지역 변수,
평가 스택, 현재 명령 위치가 있다. CPython의 평가 루프는 현재 Frame에서 명령을
가져와 해독하고 실행하면서 이 상태를 갱신한다.

정상 실행은 `fetch → decode → execute`의 반복이다. 평가 루프가 다음 code unit에서
`opcode`와 `oparg`를 읽고, opcode가 요구하는 값을 Frame에서 꺼내 연산한 뒤 결과와
다음 명령 위치를 기록한다. Python 함수를 Python에서 호출할 때도 별도의 실행 엔진을
시작하는 대신 현재 Frame을 피호출자의 Frame으로 바꾸는 방식으로 이 반복 안에서
처리한다. built-in이나 확장 callable은 새 Python Frame 없이 vectorcall 같은 C 경로로
실행될 수 있다.

## 한 명령은 현재 Frame에 적용된다

호출까지 보이는 작은 예제를 사용하자.

```python
def square(x):
    return x * x

def compute(n):
    return square(n) + 1
```

CPython 3.14.6에서 `adaptive=False`, `show_caches=False`로 확인한 결과다.

```text
compute metadata:
  co_varnames=('n',)
  co_names=('square',)
  co_consts=(1,)
  co_stacksize=3

 0 RESUME                   0
 2 LOAD_GLOBAL              1 (square + NULL)
12 LOAD_FAST_BORROW         0 (n)
14 CALL                     1
22 LOAD_SMALL_INT           1
24 BINARY_OP                0 (+)
36 RETURN_VALUE

square metadata:
  co_varnames=('x',)
  co_names=()
  co_consts=(None,)
  co_stacksize=2

 0 RESUME                   0
 2 LOAD_FAST_BORROW_LOAD_FAST_BORROW 0 (x, x)
 4 BINARY_OP                5 (*)
16 RETURN_VALUE
```

`compute(3)`의 평가 스택을 아래에서 위 순서로 적으면 실행 과정이 선명해진다.
`[]`는 현재 Frame의 빈 평가 스택이다.

| opcode | 현재 Frame에서 일어나는 일 | 실행 뒤 평가 스택 |
|---|---|---|
| `RESUME` | Frame 실행을 시작한다 | `[]` |
| `LOAD_GLOBAL 1` | `co_names[0]`의 `square`를 읽고 호출 표식 `NULL`도 올린다 | `[NULL, square]` |
| `LOAD_FAST_BORROW 0` | 지역 슬롯 0의 `n`, 곧 `3`을 읽는다 | `[NULL, square, 3]` |
| `CALL 1` | 세 항목을 소비해 `square` Frame으로 전환한다 | 반환 뒤 `[9]` |
| `LOAD_SMALL_INT 1` | 작은 정수 `1`을 올린다 | `[9, 1]` |
| `BINARY_OP +` | 두 값을 소비해 덧셈 결과를 만든다 | `[10]` |
| `RETURN_VALUE` | 결과를 꺼내 `compute`의 호출자에게 넘긴다 | Frame 종료 |

`LOAD_GLOBAL`의 원시 인자 `1`은 `co_names[1]`을 뜻하지 않는다. 3.14에서는
`co_names[oparg >> 1]`로 이름을 고르고 하위 비트로 `NULL` push 여부를 표시한다.
이 경우 이름 인덱스는 `1 >> 1`인 0이다. `NULL`은 일반 Python 값이
아니라 `CALL`이 호출 규약을 구분하는 내부 표식이다.

피호출자 `square` Frame은 지역 슬롯 `x=3`과 빈 평가 스택으로 시작한다.
`LOAD_FAST_BORROW_LOAD_FAST_BORROW`는 3.14의 합쳐진 명령으로 슬롯 0을 두 번 읽어
`[3, 3]`을 만든다. `BINARY_OP *`가 이를 `[9]`로 바꾸고 `RETURN_VALUE`가 9를
호출자 Frame에 전달한다. `compute.co_stacksize == 3`과
`square.co_stacksize == 2`는 각 Frame의 최대 평가 스택 깊이와 정확히 맞는다.

이름의 `BORROW`는 CPython이 참조 소유권 이동을 줄이기 위한 내부 구분이다.
Python 코드에서 별도 종류의 값이 보인다는 뜻은 아니다. CodeObject의
`co_stacksize`도 Frame 개수나 Python 호출 깊이가 아니라 한 Frame 안의 평가
스택 최대치다.

## 세 가지 스택은 맡은 일이 다르다

| 구분 | 무엇을 보관하는가 | 언제 변하는가 |
|---|---|---|
| 평가 스택 | 한 Frame 안의 피연산자와 중간 결과 | 대부분의 opcode를 실행할 때 |
| Frame stack | 호출별 `_PyInterpreterFrame`과 호출 관계 | Python 함수를 호출하거나 반환할 때 |
| C stack | CPython을 구현한 C 함수의 호출 상태 | C 함수가 다른 C 함수를 호출할 때 |

평가 스택은 함수 호출 관계를 나타내지 않는다. 반대로 Frame stack은 `a + b`의
두 피연산자를 보관하지 않는다. CPython 3.11 이후의 일반적인 Python-to-Python
호출은 같은 평가 루프에서 현재 Frame을 바꾸므로, Python 호출 하나마다
`_PyEval_EvalFrameDefault()`의 C 호출이 하나씩 중첩되지도 않는다.

Frame 연결은 이름 조회 경로도 아니다. `LOAD_FAST`는 현재 Frame의 슬롯을 읽고,
`LOAD_GLOBAL`은 globals와 builtins를 조회한다. 호출자의 지역 변수를 찾으려고
Frame stack을 거슬러 올라가지 않는다. 자세한 규칙은
[이름 분류가 저장소와 opcode를 정한다](names-and-closures.ko.md)에서 설명한다.

## Python 함수 CALL은 현재 Frame을 바꾼다

정상적인 Python 함수 호출은 이 경로를 지난다.

```text
호출자의 평가 스택에 callable과 인수를 준비한다
    ↓
CALL이 함수의 CodeObject·globals·closure를 확인한다
    ↓
인수를 지역 슬롯에 연결한 새 Frame을 만든다
    ↓
같은 평가 루프가 피호출자 Frame의 첫 명령부터 실행한다
    ↓
RETURN_VALUE가 Frame을 끝내고 결과를 호출자 평가 스택에 올린다
```

같은 함수를 재귀 호출하면 CodeObject는 하나지만 Frame은 호출마다 하나씩 생긴다.
각 Frame이 서로 다른 인수, 지역 변수, 평가 스택과 복귀 위치를 보관하기 때문이다.
CPython 3.14은 내부 Frame의 소유권과 복귀 위치로 평가 루프의 경계를 처리한다.

`compute`가 `CALL 1`에 도달했을 때 두 Frame의 상태는 한꺼번에 섞이지 않는다.

```text
호출자 compute Frame
  localsplus: n=3
  평가 스택: [NULL, square, 3] -- CALL이 소비
  실행 위치: square가 돌아올 때 이어 갈 위치를 보존

피호출자 square Frame
  CodeObject: square.__code__
  localsplus: x=3
  평가 스택: []
  실행 위치: 첫 RESUME
```

평가 루프는 `square`를 현재 Frame으로 삼아 실행한다. `RETURN_VALUE`가 나오면
`square` Frame을 정리하고 `compute` Frame을 다시 현재 Frame으로 바꾼 뒤 반환값
9를 그 평가 스택에 올린다. 여기서 inline call은 함수 본문을 호출자 코드에
복사한다는 뜻이 아니다. C 평가 함수를 재귀 호출하지 않고 같은 dispatch 루프가
다른 Frame을 실행한다는 뜻이다.

호출 도중 opcode가 실패하면 정상 반환 대신 예외 경로로 들어간다. 현재 Frame의
처리기를 찾고, 없으면 호출자 Frame으로 전파하는 과정은
[예외 테이블과 Frame 되감기가 전파를 나눠 맡는다](exceptions.ko.md)에서 이어진다.
제너레이터는 Frame을 없애지 않고 객체 안에 보관한다는 점에서 일반 반환과 다르다.
그 과정은 [제너레이터와 코루틴은 중단된 Frame을 보관한다](generators-and-coroutines.ko.md)에서
다룬다.

## 더 깊이 볼 지점

`_Py_CODEUNIT`, `EXTENDED_ARG`, inline cache의 정확한 배치와 Frame 필드는 각각
[CodeObject 필드와 바이트코드 인자](../reference/code-object-and-bytecode.ko.md),
[Frame·위치 테이블·문자열 인터닝 내부 구조](../reference/runtime-objects.ko.md)에서 찾을 수
있다. 평가 루프의 생성 DSL과 C 구현까지 확인하려면 기존
[프로그램 실행 상세 노트](../../../cpython-internals-notes/3.14/program-execution/README.ko.md)를
참고한다.

## 이 모델이 설명하는 것과 설명하지 않는 것

- `FAST`가 붙은 opcode는 상수를 뜻하지 않는다. 컴파일 때 번호가 정해진 현재
  Frame의 지역 슬롯을 빠르게 읽는다는 뜻이다.
- Frame stack은 lexical scope 검색 목록이 아니다. closure는 cell을 공유하고,
  전역 이름은 globals와 builtins에서 찾는다.
- Python-to-Python 호출이 보통 C 재귀를 늘리지 않는다고 해서 C stack이 사라진
  것은 아니다. C 확장 호출, 평가 루프 재진입, 내부 helper 호출은 C stack을 쓴다.
- `adaptive=False`는 `dis`가 런타임 특수화 대신 논리적 바이트코드를 보여 달라는
  옵션이다. 실행 자체의 특수화를 끄는 스위치가 아니다.
- `LOAD_SMALL_INT`와 합쳐진 `LOAD_FAST_BORROW_LOAD_FAST_BORROW`처럼
  `adaptive=False`에서도 보이는 3.14 명령이 있다. 이를 실행 중 specialization의
  증거로 오해하면 안 된다.

이 글의 출력과 opcode 이름은 CPython 3.14.6 기준이다. 바이트코드는 Python 언어
규격이나 버전 간 ABI가 아니므로 다른 CPython 버전에서는 명령 결합, 오프셋,
호출 규약이 달라질 수 있다. 그래도 CodeObject의 정적 정보와 호출별 Frame,
Frame 안의 평가 스택을 구분하는 실행 모델은 변화를 읽는 기준으로 쓸 수 있다.

---

[설명 문서 목록](README.ko.md)

이전:

[이름과 저장소](names-and-closures.ko.md)

다음:

[바인딩과 객체 수명](objects-and-lifetimes.ko.md)

관련 글:

- [예외](exceptions.ko.md)
- [제너레이터와 코루틴](generators-and-coroutines.ko.md)
- [특수화와 JIT](specialization-and-jit.ko.md)
