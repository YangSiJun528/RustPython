# 이름 분류가 closure의 저장 위치를 정한다

중첩 함수가 바깥 함수의 지역 이름을 사용하면 두 함수는 그 이름의 현재 값을 공유해야
한다. CPython은 이를 위해 바깥 Frame 전체를 보관하거나 호출할 때마다 바깥쪽 Frame을
검색하지 않는다. 대신 컴파일할 때 공유할 이름을 정하고, 실행할 때 그 이름의 값을
담는 cell을 두 함수에 연결한다.

이 문서는 아래 예제의 `rate`가 다음 네 단계를 거치는 과정을 추적한다.

1. 컴파일러가 `outer`의 `rate`를 cell, `inner`의 `rate`를 free로 분류한다.
2. `outer()`를 호출하면 새 cell이 생기고 그 안에 `2`가 저장된다.
3. `inner` 함수 객체를 만들 때 그 cell을 closure에 연결한다.
4. `inner(5)`를 호출하면 같은 cell에서 `2`를 읽어 `10`을 계산한다.

여기서 바인딩은 이름이 현재 객체를 가리키는 연결을 말한다. cell은 여러 함수가 같은
바인딩을 공유하기 위한 작은 저장소다. 컴파일러는 어느 이름이
local·cell·free·global인지와 어떤 opcode로 읽을지를 미리 정한다. 실제 cell과 그
안의 객체는 함수를 실행할 때 생긴다.

아래 opcode와 필드 값은 CPython 3.14.6에서 확인했다. 바이트코드와 내부 필드는 Python
언어의 공개 호환 규격이 아니므로 다른 버전에서는 달라질 수 있다.

![렉시컬 이름 조회와 호출자 Frame 체인은 다른 경로다](../assets/05-name-resolution-and-frame-chain.png)

## 같은 `rate`가 outer에서는 cell, inner에서는 free다

최소한의 closure 예제를 보자.

```python
def outer():
    rate = 2

    def inner(x):
        return x * rate

    return inner
```

심볼 테이블은 `rate = 2` 한 줄만 따로 보지 않는다. `outer`와 그 안의 `inner`를
각각 하나의 코드 블록으로 보고, 두 블록 사이에서 어떤 이름을 전달해야 하는지 함께
분석한다.

`rate`는 `outer`에서 대입되므로 `outer`의 local이다. 그런데 `inner`도 같은 이름을
읽는다. 따라서 `outer`에서는 일반 local 슬롯이 아니라 중첩 함수와 공유할 cell에
보관한다. 이런 이름을 cell variable이라고 한다.

반대로 `inner`는 `rate`를 직접 정의하지 않는다. 바깥 렉시컬 블록인 `outer`가 제공한
cell을 받아서 사용한다. `inner`의 관점에서 이런 이름을 free variable이라고 한다.

```text
outer의 rate: 현재 블록에서 정의하고 inner와 공유함 → CELL
inner의 rate: 바깥 블록에서 전달받아 사용함          → FREE
outer에서 inner: 일반 local
inner에서 x: 매개변수 local
```

cell과 free는 서로 다른 두 이름이 아니다. 하나의 `rate` 바인딩을 각 코드 블록의
관점에서 다르게 부르는 것이다. `outer`는 cell을 제공하고 `inner`는 그 cell을 free
variable로 전달받는다.

### 내부 심볼 값에는 같은 분류가 비트로 남는다

위 관계를 이해하는 데 내부 비트 형식까지 알 필요는 없다. CPython 구현과 대조할 때는
다음 대응만 확인하면 된다.

```text
outer.rate: 정의 플래그 DEF_LOCAL + 분석된 scope CELL
inner.rate: 사용 플래그 USE       + 분석된 scope FREE
```

raw `ste_symbols` 값은 scope를 `SCOPE_OFFSET`만큼 옮겨 각각
`DEF_LOCAL | (CELL << SCOPE_OFFSET)`, `USE | (FREE << SCOPE_OFFSET)`로 저장한다.

여기까지는 저장 방법을 정한 것뿐이다. 컴파일할 때는 `outer()`의 Frame도 cell도 아직
없다. 실제 cell은 `outer()`를 호출할 때 만들어지고, `rate = 2`가 실행될 때 그 cell이
정수 객체 `2`를 가리키게 된다.

## CodeObject에는 이름과 슬롯 종류가 남는다

심볼 테이블의 분류 결과는 CodeObject의 이름 목록과 바이트코드에 남는다. CodeObject는
여전히 실행 계획일 뿐이므로 현재 `rate` 값이나 실제 cell 객체를 담지는 않는다.

먼저 Python에서 조회할 수 있는 공개 필드만 보면 다음과 같다.

```text
outer.__code__
  co_varnames = ('inner',)
  co_cellvars = ('rate',)
  co_freevars = ()
  co_nlocals  = 1

inner.__code__
  co_varnames = ('x',)
  co_cellvars = ()
  co_freevars = ('rate',)
  co_nlocals  = 1
```

이 목록은 다음과 같이 읽는다.

- `outer.__code__.co_cellvars`의 `rate`: `outer`가 만들고 중첩 함수에 제공할
  cell이다.
- `inner.__code__.co_freevars`의 `rate`: `inner`가 함수 객체의 closure에서 받아야 할
  cell이다.
- `outer.__code__.co_varnames`의 `inner`와 `inner.__code__.co_varnames`의 `x`: 각
  함수만 사용하는 일반 local이다.

### opcode의 슬롯 번호는 통합 locals-plus 배열을 가리킨다

실제 Frame은 local·cell·free를 별도 배열 세 개에 두지 않는다. 이들을 하나의
locals-plus 영역에 배치한다. 다음은 Python 속성 조회 결과가 아니라 C
`PyCodeObject`의 `co_localsplusnames`·`co_localspluskinds`를 단순화한 보기다.

```text
PyCodeObject 내부 보기: outer
  co_localsplusnames = ('inner', 'rate')
  co_localspluskinds = [LOCAL, CELL]
outer slots: 0=inner, 1=rate cell

PyCodeObject 내부 보기: inner
  co_localsplusnames = ('x', 'rate')
  co_localspluskinds = [LOCAL, FREE]
inner slots: 0=x, 1=rate free cell
```

따라서 `inner`의 `LOAD_DEREF 1`에서 `1`은 `co_freevars[1]`이라는 뜻이 아니다.
`rate`는 `co_freevars`에서는 첫 번째 이름이지만, locals-plus에서는 `x` 다음인 슬롯
1에 있다. opcode의 raw operand는 이 통합 슬롯 번호를 가리킨다.

내부 kind 비트는 `CO_FAST_LOCAL(0x20)`, `CO_FAST_CELL(0x40)`,
`CO_FAST_FREE(0x80)`이다. 공개 `co_varnames`, `co_cellvars`, `co_freevars`는 통합
메타데이터에서 각 종류의 이름을 골라 보여 준다. 캡처된 매개변수처럼 하나의 슬롯이
`LOCAL | CELL`일 수도 있으며, 이때 같은 이름이 `co_varnames`와 `co_cellvars` 양쪽에
나타날 수 있다.

## `outer()`를 호출하면 cell이 생기고 `2`가 저장된다

이제 컴파일 결과를 실제로 실행해 보자. `outer()`를 호출하면 호출 전에는 없던 Frame이
생기고, 그 Frame의 locals-plus 슬롯도 준비된다. `outer`의 최종 바이트코드는 다음과
같다.

```text
MAKE_CELL                1 (rate)
RESUME                   0
LOAD_SMALL_INT           2
STORE_DEREF              1 (rate)

LOAD_FAST_BORROW         1 (rate)
BUILD_TUPLE              1
LOAD_CONST               1 (<code object inner>)
MAKE_FUNCTION
SET_FUNCTION_ATTRIBUTE   8 (closure)
STORE_FAST               0 (inner)

LOAD_FAST_BORROW         0 (inner)
RETURN_VALUE
```

먼저 앞의 네 명령만 보면 cell이 준비되는 과정이 보인다. 호출 직후 슬롯 0과 1은
미설정이다. `MAKE_CELL 1`은 슬롯 1에 빈 `PyCellObject`를 만든다.
`LOAD_SMALL_INT 2`가 정수 객체 참조를 평가 스택에 올리고, `STORE_DEREF 1`이 그
참조를 슬롯 1의 cell 안에 저장한다.

```text
호출 직후       slot 1: 미설정
MAKE_CELL 1     slot 1: cell → 비어 있음
STORE_DEREF 1   slot 1: cell → int 2
```

일반 local이라면 슬롯에 `2`를 직접 넣고 `STORE_FAST`를 사용한다. 여기서는 슬롯 1에
cell이 있고 실제 값은 cell 안에 있으므로 `STORE_DEREF`를 사용한다. 캡처된
매개변수처럼 `MAKE_CELL` 실행 전에 슬롯에 인수 객체가 들어 있다면, 새 cell은 그
객체를 초기 내용으로 가진다.

나중에 `nonlocal rate`로 다시 대입하면 새 local을 만드는 것이 아니라 이 cell의
내용을 바꾼다. 같은 cell을 공유하는 모든 `inner` 함수는 바뀐 내용을 읽는다.

## `inner` 함수 객체는 값 `2`가 아니라 cell을 캡처한다

`rate`를 저장한 다음에는 `inner` 함수 객체를 만든다. 이때 closure에 연결되는 것은
cell의 현재 내용 `2`가 아니라 cell 객체 자체다.

1. `LOAD_FAST_BORROW 1`이 슬롯 1의 cell 객체 참조를 평가 스택에 올린다.
2. `BUILD_TUPLE 1`이 그 참조로 `(rate_cell,)`을 만든다.
3. `MAKE_FUNCTION`이 inner CodeObject와 globals를 결합해 함수 객체를 만든다.
4. `SET_FUNCTION_ATTRIBUTE 8`이 cell 튜플을 함수의 `func_closure`, 즉 Python
   수준의 `__closure__`에 붙인다.

```text
outer slot 1 ─→ rate cell ─→ int 2
                    ↑
inner.__closure__[0]┘
```

cell을 연결하기 때문에 `rate`가 나중에 바뀌어도 `inner`는 같은 cell의 새 내용을 볼
수 있다. 만약 값 `2`만 복사했다면 `nonlocal rate`로 바뀐 값을 공유할 수 없다.

### 3.14의 최종 바이트코드에는 `LOAD_CLOSURE`가 남지 않는다

컴파일러의 `codegen_make_closure()`는 inner CodeObject의 free-variable 순서를 읽고
outer의 대응 슬롯마다 `LOAD_CLOSURE`를 방출한다. 그러나 CPython 3.14에서
`LOAD_CLOSURE`는 컴파일 중에만 사용하는 pseudo instruction이다. CFG 처리에서
`LOAD_FAST`로 낮아지고 load-fast 최적화를 거쳐 최종 `dis`에는
`LOAD_FAST_BORROW 1 (rate)`가 보인다.

이 opcode 이름만 보면 일반 local 값을 읽는 것처럼 보이지만, 슬롯 1의 kind는
`CELL`이다. 따라서 평가 스택에 올라가는 것은 cell 내용 `2`가 아니라 cell 객체
참조다.

closure tuple의 순서는 inner의 free-variable 순서와 같다. 이 예에서는 둘 다 하나라서
`inner.__code__.co_freevars[0] == 'rate'`와 `inner.__closure__[0]`이 짝을 이룬다.
이 순서가 어긋나면 이름이 다른 cell을 읽게 되므로 CodeObject와 함수 객체를 임의로
조립할 때도 길이와 순서가 맞아야 한다.

## `inner(5)`를 호출하면 같은 cell을 Frame에 연결한다

`outer()`가 반환한 `inner`를 `inner(5)`처럼 호출한다고 하자. inner의 최종
바이트코드는 다음과 같다.

```text
COPY_FREE_VARS           1
RESUME                   0
LOAD_FAST_BORROW         0 (x)
LOAD_DEREF               1 (rate)
BINARY_OP                5 (*)
RETURN_VALUE
```

호출을 시작하면 새 inner Frame이 생긴다. 인수 결합은 `x`의 슬롯 0에 정수 객체 `5`를
놓지만, `rate`의 free 슬롯 1은 아직 비어 있다. `COPY_FREE_VARS 1`이 함수 객체의
`func_closure[0]`에서 cell 객체 참조를 가져와 슬롯 1에 넣는다.

여기서 복사하는 것은 `2`라는 값도, 새로 만든 cell도 아니다. `outer`가 만든 기존
cell을 가리키는 참조를 복사한다. 따라서 `inner.__closure__[0]`과 inner Frame의 슬롯
1은 같은 cell을 가리킨다.

```text
Frame 초기화       slot 0: x → 5       slot 1: 미설정
COPY_FREE_VARS 1   slot 0: x → 5       slot 1: ─┐
inner.__closure__[0] ────────────────────────────┴→ 같은 rate cell → 2
LOAD_DEREF 1       평가 스택에 cell의 현재 내용 2를 올림
```

그다음 `LOAD_FAST_BORROW 0`은 일반 local 슬롯에서 `x == 5`를 읽고,
`LOAD_DEREF 1`은 cell을 한 번 더 따라가 현재 내용 `rate == 2`를 읽는다.
`BINARY_OP *`가 두 값을 곱해 `10`을 만든다.

`outer` Frame이 반환되어 사라진 뒤에도 `inner`가 동작하는 이유도 여기에 있다.
`inner.__closure__`가 cell을 계속 참조하므로 cell이 살아 있고, cell 안의 `2`도 계속
접근할 수 있다. 따라서 closure는 바깥 Frame 전체가 아니라 필요한 바인딩의 cell만
보관한다고 이해하는 편이 정확하다.

## 공유할 이름은 정적이고 cell의 현재 값은 동적이다

지금까지의 흐름은 컴파일할 때 정해지는 정보와 실행할 때 생기는 상태로 나눌 수 있다.

| 시점 | 정하거나 만드는 것 |
|---|---|
| 컴파일 | `rate`를 outer에서는 cell, inner에서는 free로 분류한다. |
| CodeObject 생성 | 이름 목록, locals-plus kind, 슬롯 번호와 opcode를 기록한다. |
| `outer()` 호출 | 이번 호출의 cell을 만들고 실행 결과인 `2`를 저장한다. |
| `inner` 함수 생성 | 함수 객체의 `__closure__`에 그 cell을 연결한다. |
| `inner(5)` 호출 | inner Frame에 같은 cell을 연결하고 현재 내용을 읽는다. |

따라서 바이트코드에 들어 있는 것은 어떤 이름과 슬롯을 공유할지에 대한 계획이다. cell
안의 현재 객체는 실행 결과이며 호출마다 달라질 수 있다.

이 예제에서는 숫자 `2`가 `LOAD_SMALL_INT 2`에도 보이지만, 이것이 closure 값을 따로
기록한 표라는 뜻은 아니다. `rate = read_config()`처럼 실행 중 값을 구하거나,
매개변수를 캡처하거나, 조건에 따라 대입하거나, `nonlocal`로 다시 대입해도 이름과
cell을 연결하는 기본 구조는 같다. 달라지는 것은 cell의 현재 내용이다.

## 호출자 Frame은 렉시컬 이름 조회 경로가 아니다

closure가 바깥 이름을 전달한다고 해서, Python이 실행 중인 호출자 Frame을 거슬러
올라가며 같은 이름을 찾는 것은 아니다. 다음 두 함수는 소스 구조상 서로 중첩되어 있지
않다.

```python
def caller():
    value = 100
    return callee()

def callee():
    return value
```

`callee`의 `value`는 free가 아니라 implicit global로 분류된다. `callee`의 바깥
렉시컬 블록은 `caller`가 아니라 모듈이기 때문이다. 따라서 `LOAD_GLOBAL`은 callee
함수의 globals와 builtins만 확인하고, 실행 중 자신을 호출한 `caller`의 local 슬롯은
확인하지 않는다.

Frame의 `previous` 연결은 호출이 끝났을 때 돌아갈 위치, 예외 전파, traceback 등을
위한 실행 관계다. closure의 렉시컬 이름 조회 경로와는 별개다.

## 이 설명의 적용 범위

여기서는 최적화된 일반 함수 scope를 중심으로 설명했다. 다른 코드 블록에는 추가 조회
경로가 있다.

- 모듈과 클래스 본문은 `LOAD_NAME`을 사용할 수 있다.
- annotation scope와 클래스 안의 free 이름은 `LOAD_FROM_DICT_OR_DEREF` 같은 명령을
  사용할 수 있다.
- opcode 이름과 `LOAD_CLOSURE`의 pseudo-op 처리는 CPython 버전에 따라 달라질 수
  있으며 공개 호환 규격이 아니다.
- GIL 빌드와 자유 스레딩 빌드는 cell의 의미는 공유하지만 내부 참조 증감과 동기화
  표현은 다를 수 있다.

---

[설명 문서 목록](README.ko.md)

이전:

[실행 설계와 호출 상태](execution-model.ko.md)

다음:

[평가 루프와 세 가지 스택](evaluation-loop.ko.md)

관련 글:

- [객체 참조와 수명](objects-and-lifetimes.ko.md)
- [CodeObject 필드와 바이트코드 인자](../reference/code-object-and-bytecode.ko.md)
