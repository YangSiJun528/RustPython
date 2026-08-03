# CPython 3.14: Python 컴파일에서 실행까지

이 문서는 짧은 Python 예제 하나가 CPython 3.14에서 컴파일되고
실행되는 과정을 따라간다. 컴파일러나 인터프리터의 C 구현보다 다음
세 가지를 이해하는 데 집중한다.

- Python 소스가 어떤 단계를 거쳐 `CodeObject`가 되는가?
- `dis`가 보여 주는 바이트코드와 `CodeObject`의 값은 어떻게 연결되는가?
- 함수를 호출하면 지역 변수와 평가 스택이 어떻게 변하는가?

CPython 내부 구현을 더 자세히 보고 싶다면 다음 문서를 참고한다.

- [Python 소스 코드 컴파일](../compiling-python-source-code/README.ko.md)
- [런타임 객체](../runtime-objects/README.ko.md)
- [프로그램 실행](../program-execution/README.ko.md)

이 문서의 출력은 **CPython 3.14.6**에서 확인했다. CPython 바이트코드는
버전 사이의 호환성을 보장하는 공개 명령어 규격이 아니므로, 다른
버전에서는 명령 이름과 배치가 달라질 수 있다.

## 전체 흐름

![Python 소스가 CodeObject로 컴파일되고 프레임에서 실행되는 전체 흐름](diagrams/01-compilation-pipeline.png)

큰 흐름만 먼저 쓰면 다음과 같다.

```text
.py 소스
  ↓ 토큰화와 파싱
AST
  ↓ 이름 범위 분석, 명령 생성, CFG 최적화, 조립
CodeObject
  ↓ 프레임 생성
바이트코드 평가 루프
  ↓
실행 결과
```

Java와 비교하면 `CodeObject`는 `.class`의 메서드 코드와 상수 풀을
한데 묶어 놓은 것과 비슷한 역할을 한다. 그러나 둘은 같은 파일
규격이 아니다.

- Java `.class`는 JVM이 읽는 명시적인 클래스 파일 형식이다.
- CPython의 `CodeObject`는 메모리에 존재하는 런타임 객체다.
- `.pyc`는 `CodeObject`를 다시 컴파일하지 않기 위해 저장한 캐시다.
- CPython은 Java의 클래스 로딩·검증·링크와 동일한 절차를 거치지 않는다.

## 끝까지 따라갈 예제

```python
BONUS = 1000

def calculate(price, quantity):
    subtotal = price * quantity
    return subtotal + BONUS

result = calculate(5, 3)
```

최종 결과는 다음과 같다.

```python
result == 1015
```

이 짧은 예제로도 다음을 모두 볼 수 있다.

- 모듈 전역 이름: `BONUS`, `calculate`, `result`
- 함수 인수: `price`, `quantity`
- 함수 지역 변수: `subtotal`
- 상수: `1000`
- 함수 생성과 호출
- 곱셈과 덧셈을 처리하는 평가 스택

## 1. 소스가 CodeObject가 되기까지

CPython 컴파일러의 주요 단계는 다음과 같다.

1. 소스를 토큰으로 나눈다.
2. 토큰을 파싱해 AST를 만든다.
3. 심볼 테이블을 만들며 각 이름이 지역·전역·자유 변수인지 결정한다.
4. AST를 바이트코드에 가까운 명령어 열로 바꾼다.
5. 제어 흐름 그래프를 구성하고 최적화한다.
6. 실제 바이트코드와 위치·예외 테이블을 조립해 `CodeObject`로 묶는다.

Python에서는 `compile()`로 이 결과를 직접 확인할 수 있다.

```python
source = """\
BONUS = 1000

def calculate(price, quantity):
    subtotal = price * quantity
    return subtotal + BONUS

result = calculate(5, 3)
"""

module_code = compile(source, "example.py", "exec")
```

`module_code`는 파일 전체를 나타내는 모듈 `CodeObject`다. 아직
`BONUS`에 `1000`이 저장되거나 `calculate(5, 3)`이 호출된 것은
아니다. 실행할 명령과 그 명령에 필요한 정적 정보만 만들어진 상태다.

```text
컴파일: 무엇을 실행할지 만든다.
실행:    그 명령을 실제 값으로 수행한다.
```

## 2. 모듈 CodeObject 읽기

예제의 모듈 `CodeObject`에서 우선 볼 값은 다음과 같다.

```text
co_name      = '<module>'
co_filename  = 'example.py'
co_argcount  = 0
co_nlocals   = 0
co_stacksize = 4
co_flags     = 0

co_consts = (
    1000,
    <code object calculate ...>,
    None,
)

co_names    = ('BONUS', 'calculate', 'result')
co_varnames = ()
```

각 값은 다음 의미다.

| 값 | 의미 |
|---|---|
| `co_name` | 이 코드 단위의 이름이다. 파일 전체이므로 `<module>`이다. |
| `co_consts` | 바이트코드가 사용할 상수와 중첩 코드 객체다. |
| `co_names` | 모듈 네임스페이스에서 읽거나 쓸 이름 목록이다. |
| `co_varnames` | 함수의 빠른 지역 변수 슬롯 이름이다. 모듈에는 없다. |
| `co_stacksize` | 이 코드를 실행할 때 필요한 평가 스택의 최대 깊이다. |
| `co_filename` | traceback과 디버깅에 사용할 원본 파일 이름이다. |

여기서 가장 중요한 점은 함수 본문도 별도의 `CodeObject`로 미리
컴파일되어 `module_code.co_consts[1]`에 들어 있다는 것이다.

```text
module CodeObject
├─ co_consts[0] = 1000
├─ co_consts[1] = calculate CodeObject
└─ co_consts[2] = None
```

`def calculate(...):`를 실행할 때 함수 본문을 다시 파싱하고 컴파일하는
것이 아니다. 이미 만들어진 `calculate CodeObject`를 꺼내 함수 객체로
감싼다.

## 3. 모듈 바이트코드 읽기

`dis` 모듈은 `co_code`의 바이트열을 사람이 읽을 수 있는 명령으로
풀어 준다.

```python
import dis

dis.dis(module_code, depth=0, adaptive=False, show_caches=False)
```

출력은 다음과 같다. 메모리 주소는 생략했다.

```text
  0           RESUME                   0

  1           LOAD_CONST               0 (1000)
              STORE_NAME               0 (BONUS)

  3           LOAD_CONST               1 (<code object calculate ...>)
              MAKE_FUNCTION
              STORE_NAME               1 (calculate)

  7           LOAD_NAME                1 (calculate)
              PUSH_NULL
              LOAD_SMALL_INT           5
              LOAD_SMALL_INT           3
              CALL                     2
              STORE_NAME               2 (result)
              LOAD_CONST               2 (None)
              RETURN_VALUE
```

바이트코드 인자는 값 자체보다 `CodeObject` 안의 테이블 인덱스인
경우가 많다.

```text
LOAD_CONST 0  → co_consts[0] → 1000
STORE_NAME 0  → co_names[0]  → 'BONUS'
LOAD_CONST 1  → co_consts[1] → calculate CodeObject
STORE_NAME 1  → co_names[1]  → 'calculate'
STORE_NAME 2  → co_names[2]  → 'result'
```

각 명령을 Python 코드로 다시 읽으면 다음과 같다.

| 바이트코드 | 의미 |
|---|---|
| `LOAD_CONST 0` | 상수 `1000`을 평가 스택에 올린다. |
| `STORE_NAME 0` | 스택의 값을 모듈 이름 `BONUS`에 저장한다. |
| `LOAD_CONST 1` | 미리 컴파일한 함수 코드 객체를 올린다. |
| `MAKE_FUNCTION` | 코드 객체와 현재 전역 환경을 연결해 함수 객체를 만든다. |
| `STORE_NAME 1` | 만든 함수를 `calculate`라는 이름에 저장한다. |
| `LOAD_NAME 1` | 호출할 `calculate` 함수를 올린다. |
| `PUSH_NULL` | CPython 내부 호출 규약에 필요한 표식을 올린다. `None`과 다르다. |
| `LOAD_SMALL_INT 5`, `3` | 작은 정수 인수를 올린다. |
| `CALL 2` | 인수 두 개로 함수를 호출한다. |
| `STORE_NAME 2` | 반환값을 `result`에 저장한다. |
| `RETURN_VALUE` | 모듈 코드의 실행을 끝낸다. |

`LOAD_SMALL_INT`는 CPython 3.14의 명령이다. 그래서 이 예제에서 정수
`5`와 `3`은 `co_consts`를 거치지 않는다. 다른 CPython 버전에서는
다른 명령이 나올 수 있다.

## 4. 함수 CodeObject 읽기

중첩된 함수 코드 객체는 다음처럼 찾을 수 있다.

```python
function_code = next(
    value
    for value in module_code.co_consts
    if isinstance(value, type(module_code))
)
```

주요 값은 다음과 같다.

```text
co_name       = 'calculate'
co_filename   = 'example.py'
co_firstlineno = 3
co_argcount   = 2
co_nlocals    = 3
co_stacksize  = 2
co_flags      = 3

co_consts   = (None,)
co_names    = ('BONUS',)
co_varnames = ('price', 'quantity', 'subtotal')
co_cellvars = ()
co_freevars = ()
```

![Python 소스와 함수 바이트코드 및 CodeObject 테이블의 대응](diagrams/02-code-object-and-bytecode.png)

### 지역 변수 슬롯

`co_varnames`의 인덱스는 함수 프레임의 지역 변수 슬롯 번호로 사용된다.

```text
co_varnames[0] = 'price'
co_varnames[1] = 'quantity'
co_varnames[2] = 'subtotal'
```

따라서 `co_argcount == 2`이고 `co_nlocals == 3`이다. 인수 두 개도
지역 변수에 포함된다.

### 전역 이름

`co_names == ('BONUS',)`에는 문자열 이름만 들어 있다. 현재 값
`1000`은 함수 코드 객체에 복사되지 않는다.

함수를 호출할 때 함수 객체가 참조하는 전역 네임스페이스에서
`BONUS`를 찾는다. 따라서 컴파일 뒤에 전역 `BONUS`를 바꾸면 다음
호출은 바뀐 값을 읽는다.

### 평가 스택 크기

`co_stacksize == 2`는 함수가 동시에 최대 두 값을 평가 스택에
올린다는 뜻이다.

```text
곱셈 직전: [price, quantity]
덧셈 직전: [subtotal, BONUS]
```

이는 지역 변수 개수나 Python 호출 스택 깊이가 아니다.

### 플래그

`co_flags`는 여러 상태를 비트로 묶은 값이다. 이 예제의 `3`은 다음
두 플래그가 설정되었다는 뜻이다.

```text
1: CO_OPTIMIZED
2: CO_NEWLOCALS
1 | 2 = 3
```

함수 실행에 빠른 지역 변수 슬롯을 사용하고, 호출마다 새 지역
네임스페이스를 만든다는 뜻으로 이해하면 충분하다.

## 5. 함수 바이트코드 읽기

```python
dis.dis(function_code, adaptive=False, show_caches=False)
```

```text
  3           RESUME                   0

  4           LOAD_FAST_BORROW_LOAD_FAST_BORROW 1 (price, quantity)
              BINARY_OP                5 (*)
              STORE_FAST               2 (subtotal)

  5           LOAD_FAST_BORROW         2 (subtotal)
              LOAD_GLOBAL              0 (BONUS)
              BINARY_OP                0 (+)
              RETURN_VALUE
```

이 출력도 `CodeObject`의 테이블과 연결해서 읽을 수 있다.

```text
STORE_FAST 2   → co_varnames[2] → 'subtotal'
LOAD_FAST ... 2→ co_varnames[2] → 'subtotal'
LOAD_GLOBAL 0  → co_names[0]    → 'BONUS'
```

`BINARY_OP` 뒤의 숫자는 상수가 아니라 연산 종류를 나타낸다.

```text
BINARY_OP 5 (*) → 곱셈
BINARY_OP 0 (+) → 덧셈
```

`LOAD_FAST_BORROW_LOAD_FAST_BORROW`는 지역 변수 두 개를 한 번에 읽는
CPython 3.14의 결합 명령이다. `BORROW`는 참조 관리 최적화와 관련된
이름이다. 이 글에서는 단순히 `price`와 `quantity`를 평가 스택에
올리는 명령으로 보면 된다.

### 바이트코드와 동작에 대한 부연 설명

바이트코드 평가 루프는 각 명령을 현재 프레임에 적용한다. 개념적으로는
다음 동작을 반복한다고 볼 수 있다.

```text
execute(opcode, argument, current_frame)
```

`CodeObject`에는 바이트코드와 상수·이름·지역 변수 구조가 있고,
프레임에는 이번 호출의 실제 지역 변수 값, 평가 스택, 전역
네임스페이스, 현재 실행 위치가 있다. 대표적인 연결 관계는 다음과
같다.

| 바이트코드 | CodeObject와 프레임에서 하는 일 |
|---|---|
| `LOAD_CONST n` | `frame.code.co_consts[n]`을 평가 스택에 올린다. |
| `LOAD_FAST n` | 프레임의 빠른 지역 변수 슬롯 `n`에 있는 값을 평가 스택에 올린다. `co_varnames[n]`은 그 슬롯의 이름이다. |
| `STORE_FAST n` | 평가 스택의 값을 꺼내 프레임의 지역 변수 슬롯 `n`에 저장한다. |
| `LOAD_GLOBAL n` | `co_names`에서 이름을 얻고 프레임이 참조하는 전역·내장 네임스페이스에서 실제 값을 찾는다. |
| `BINARY_OP n` | `n`이 나타내는 연산을 평가 스택의 두 값에 적용하고 결과를 다시 올린다. |
| `JUMP_* n` | 조건과 `n`에 따라 프레임의 현재 실행 위치를 바꾼다. |
| `CALL n` | 평가 스택에서 함수와 인수 `n`개를 꺼내 호출 대상의 새 프레임을 만든다. |
| `RETURN_VALUE` | 평가 스택의 값을 꺼내 현재 프레임을 끝내고 호출자에게 돌려준다. |

여기서 `FAST`는 상수를 뜻하지 않는다. 함수 지역 변수를 이름으로
딕셔너리에서 찾지 않고 프레임의 배열 슬롯으로 바로 접근한다는
뜻이다.

```text
co_varnames[0]       = 'price'  # 슬롯의 이름
frame.fast_locals[0] = 5        # 이번 호출의 실제 값

LOAD_FAST 0
→ frame.fast_locals[0]을 읽음
→ 5를 평가 스택에 올림
```

같은 함수라도 `calculate(8, 2)`를 호출하면 같은 `CodeObject`를
사용하면서 새 프레임의 슬롯에는 `8`과 `2`가 들어간다. 반면
`LOAD_CONST n`은 `co_consts[n]`을 읽고, `LOAD_SMALL_INT 5`는 정수 `5`를
명령에서 바로 사용한다.

바이트코드 뒤의 `n`도 항상 CodeObject 테이블의 인덱스인 것은 아니다.
명령에 따라 상수·이름 인덱스, 프레임 슬롯 번호, 연산 종류, 인수 개수,
점프 위치를 뜻한다. CPython 3.14의 일부 결합 명령은 여러 슬롯 번호나
플래그를 하나의 인자에 함께 담으며, `dis`는 이를 사람이 읽기 쉽게
풀어서 보여 준다.

## 6. 함수 호출과 프레임

`CodeObject`, 함수 객체, 프레임은 서로 다른 역할을 한다.

```text
CodeObject
  무엇을 실행할지 저장
  바이트코드, 상수, 이름, 지역 변수 구조

함수 객체
  CodeObject와 전역 네임스페이스 등을 연결
  실제로 호출할 수 있는 객체

프레임
  한 번의 호출에서 사용하는 실제 값 저장
  지역 변수, 평가 스택, 현재 실행 위치
```

모듈 실행 중 `MAKE_FUNCTION`이 `calculate CodeObject`를 함수 객체로
만든다. 이후 `CALL 2`가 실행되면 새 함수 프레임이 생긴다.

```text
calculate CodeObject 하나
       │
       ├─ calculate(5, 3) 호출 → 프레임 A
       └─ calculate(8, 2) 호출 → 프레임 B
```

두 호출은 같은 명령을 공유하지만 지역 변수와 평가 스택은 서로
다르다.

## 7. 평가 스택으로 실행 따라가기

`calculate(5, 3)`의 프레임은 다음 상태로 시작한다.

```text
지역 변수
slot 0 price    = 5
slot 1 quantity = 3
slot 2 subtotal = 아직 값 없음

평가 스택
[]
```

![calculate 함수의 바이트코드에 따른 지역 변수와 평가 스택 변화](diagrams/03-frame-evaluation-stack.png)

오른쪽을 평가 스택의 위쪽으로 보면 실행 과정은 다음과 같다.

| 명령 | 평가 스택 | 지역 변수 변화 |
|---|---|---|
| `LOAD_FAST_BORROW_LOAD_FAST_BORROW` | `[5, 3]` | 없음 |
| `BINARY_OP 5 (*)` | `[15]` | 없음 |
| `STORE_FAST 2` | `[]` | `subtotal = 15` |
| `LOAD_FAST_BORROW 2` | `[15]` | 없음 |
| `LOAD_GLOBAL 0` | `[15, 1000]` | 전역에서 `BONUS`를 읽음 |
| `BINARY_OP 0 (+)` | `[1015]` | 없음 |
| `RETURN_VALUE` | `[]` | 호출자에게 `1015` 반환 |

여기까지가 스택 기반 바이트코드 인터프리터의 핵심 동작이다.

1. 필요한 값을 지역 변수·전역 이름·상수 테이블에서 스택으로 가져온다.
2. 연산 명령이 값을 꺼내 계산한다.
3. 결과를 다시 스택에 올린다.
4. 저장 명령은 스택의 값을 변수에 넣는다.
5. 반환 명령은 스택의 값을 호출자에게 돌려준다.

## Java 글과 대응해서 보기

Java 컴파일·실행 글에서 다룬 개념과 대략 대응시키면 다음과 같다.

| Java/JVM | CPython |
|---|---|
| Java 소스 | Python 소스 |
| `javac` | CPython 파서와 컴파일러 |
| `.class` 바이트코드와 constant pool | `CodeObject`의 바이트코드, `co_consts`, `co_names` |
| `javap` | `dis` |
| JVM frame의 local variables | CPython 프레임의 지역 변수 슬롯 |
| JVM operand stack | CPython 프레임의 평가 스택 |
| JVM instruction 실행 | CPython evaluation loop의 opcode 실행 |

공통점은 둘 다 바이트코드와 프레임별 스택을 이용한다는 것이다.
차이점은 파일 형식, 타입·링크 규칙, 명령어 구성, 최적화 방식이다.
따라서 개념 비교에는 유용하지만 세부 구조를 일대일로 같다고 보면
안 된다.

## 정리

예제의 전체 생명 주기를 다시 연결하면 다음과 같다.

```text
1. 파일 전체가 모듈 CodeObject로 컴파일된다.
2. calculate 본문도 별도의 CodeObject로 미리 컴파일된다.
3. 모듈 바이트코드가 BONUS를 저장한다.
4. MAKE_FUNCTION이 calculate CodeObject로 함수 객체를 만든다.
5. CALL 2가 calculate용 프레임을 만든다.
6. 인수는 price와 quantity 지역 슬롯에 들어간다.
7. 바이트코드가 평가 스택에서 곱셈과 덧셈을 수행한다.
8. RETURN_VALUE가 1015를 모듈 프레임으로 돌려준다.
9. 모듈 프레임이 반환값을 result에 저장한다.
```

가장 중요한 구분은 다음 한 줄이다.

> `CodeObject`는 실행할 명령이고, 프레임은 그 명령을 이번 호출에서
> 실행하는 상태다.

## 참고 자료

- [CPython 3.14 Compiler design](https://github.com/python/cpython/blob/3.14/InternalDocs/compiler.md)
- [CPython 3.14 Code Objects](https://github.com/python/cpython/blob/3.14/InternalDocs/code_objects.md)
- [CPython 3.14 Frames](https://github.com/python/cpython/blob/3.14/InternalDocs/frames.md)
- [CPython 3.14 The Bytecode Interpreter](https://github.com/python/cpython/blob/3.14/InternalDocs/interpreter.md)
- [Python 3.14 `dis` 문서](https://docs.python.org/3.14/library/dis.html)
- [Python 3.14 데이터 모델의 code object](https://docs.python.org/3.14/reference/datamodel.html#code-objects)
- [Back to the Essence - Java 컴파일에서 실행까지 - (1)](https://github.com/HomoEfficio/dev-tips/blob/master/Back%20to%20the%20Essence%20-%20Java%20%EC%BB%B4%ED%8C%8C%EC%9D%BC%EC%97%90%EC%84%9C%20%EC%8B%A4%ED%96%89%EA%B9%8C%EC%A7%80%20-%20%281%29.md)
- [Back to the Essence - Java 컴파일에서 실행까지 - (2)](https://github.com/HomoEfficio/dev-tips/blob/master/Back%20to%20the%20Essence%20-%20Java%20%EC%BB%B4%ED%8C%8C%EC%9D%BC%EC%97%90%EC%84%9C%20%EC%8B%A4%ED%96%89%EA%B9%8C%EC%A7%80%20-%20%282%29.md)
