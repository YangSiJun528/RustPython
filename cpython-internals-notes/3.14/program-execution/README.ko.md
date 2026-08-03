# CPython 3.14 프로그램 실행

이 문서는 CPython 3.14 저장소의 `InternalDocs` 중 **Program
Execution** 아래에 있는 네 문서를 한 흐름으로 읽기 위한 한국어
번역·해설서다.

- [The Bytecode Interpreter](https://github.com/python/cpython/blob/3.14/InternalDocs/interpreter.md)
- [The JIT](https://github.com/python/cpython/blob/3.14/InternalDocs/jit.md)
- [Garbage Collector Design](https://github.com/python/cpython/blob/3.14/InternalDocs/garbage_collector.md)
- [Exception Handling](https://github.com/python/cpython/blob/3.14/InternalDocs/exception_handling.md)

## 대상 독자와 읽는 방법

독자가 nand2tetris를 수료해 스택 기반 VM의 명령어 실행 루프, 함수
호출 프레임, 힙 객체와 기본적인 메모리 관리 개념은 알고 있다고
가정한다. 따라서 일반적인 VM을 다시 설명하기보다는 CPython의
adaptive interpreter, 명령 특수화, tracing JIT, 참조 횟수와 순환
GC, 예외 테이블처럼 구체적인 실행 기술에 집중한다.

원문의 제목, 문장, 목록, 표와 수식을 원래 순서대로 모두 번역하고,
코드와 다이어그램은 구조와 내용을 보존한다. 문맥만으로 뜻이 충분한
부분에는 번역만 제시하고, CPython 고유의 자료 구조나 최적화처럼
별도 배경지식이 필요한 부분에는 다음 형식의 해설을 붙인다.

> **해설:** 이 형식의 문단은 원문 번역이 아니라 독자를 위한 추가 설명이다.

이 문서는 Python 언어 명세가 아니라 **CPython 3.14의 내부 구현**
설명이다. 특히 JIT와 자유 스레딩(free-threaded) 빌드의 세부사항은
실험적이거나
버전에 따라 빠르게 바뀔 수 있다.

### 문서 구조

- [전체 지도](#전체-지도)
- [제1부: 바이트코드 인터프리터](#제1부-바이트코드-인터프리터)
- [제2부: JIT](#제2부-jit)
- [제3부: 가비지 컬렉터 설계](#제3부-가비지-컬렉터-설계)
- [제4부: 예외 처리](#제4부-예외-처리)

## 전체 지도

네 문서는 실행 중인 CPython의 서로 다른 경로를 설명한다.

1. **The Bytecode Interpreter**: code object의 바이트코드를 어떤
   실행 루프와 최적화 계층으로 처리하는가?
2. **The JIT**: 자주 실행되는 바이트코드 경로를 어떻게 추적하고
   기계어로 바꾸는가?
3. **Garbage Collector Design**: 객체의 수명을 어떻게 추적하고 참조
   순환으로 남은 객체를 어떻게 회수하는가?
4. **Exception Handling**: 정상 실행 경로에 비용을 거의 추가하지
   않으면서 예외 처리기로 어떻게 이동하는가?

```text
code object의 바이트코드
          │
          ▼
바이트코드 인터프리터 ── 뜨거운 실행 경로 ──→ 선택적 JIT 기계어
          │
          ├─ 객체 생성·참조 변경 ──→ 참조 횟수 + 순환 GC
          │
          └─ 예외 발생 ──→ 예외 테이블 조회 ──→ handler 또는 stack unwinding
```

> **nand2tetris와의 대응:** nand2tetris CPU나 VM 구현에서
> `fetch → decode → execute`를 반복했다면 CPython 인터프리터도
> 기본적으로 다음 바이트코드 명령을 읽어 해당 동작을 실행한다.
> CPython은 여기에 실행 중 관찰한 타입을 이용한 특수화, 여러
> 명령을 더 작은 micro-op으로 바꾸는 계층, 선택적 JIT, 자동 객체
> 수명 관리와 예외 복구 경로를 덧붙인다.

---

## 제1부: 바이트코드 인터프리터

> 원문: [CPython 3.14 `InternalDocs/interpreter.md`](https://github.com/python/cpython/blob/3.14/InternalDocs/interpreter.md)

이 문서는 컴파일된 Python 코드를 실행하는 구성 요소인 바이트코드 인터프리터의 동작과
구현을 설명한다. 진입점은
[`Python/ceval.c`](https://github.com/python/cpython/blob/3.14/Python/ceval.c)에 있다.

높은 수준에서 보면 인터프리터는 바이트코드 명령을 차례로 순회하는 루프로 구성된다. 루프
안의 `switch` 문에는 각 opcode를 구현하는 `case`가 있으며, 해당 `case`를 실행해 명령을
처리한다. 이 `switch` 문은
[`Python/bytecodes.c`](https://github.com/python/cpython/blob/3.14/Python/bytecodes.c)에
기술된 명령 정의로부터 생성된다. 명령 정의는 이 목적을 위해 만든
[DSL](https://github.com/python/cpython/blob/3.14/Tools/cases_generator/interpreter_definition.md)로
작성되어 있다.

> **해설 — 생성되는 인터프리터 코드와 tier**
>
> `Python/bytecodes.c`는 실행할 C 코드 자체처럼 보이지만, 동시에 코드 생성기의 입력인
> DSL 파일이다. `make regen-cases`가 이를 읽어 실제 dispatch `case`와 메타데이터를
> 생성한다. 생성된 파일보다 DSL 정의가 원본이다.
>
> 여기서 설명하는 바이트코드 dispatch 루프는 CPython 실행 계층의 기본 tier인
> **tier 1**에 해당한다. “tier”는 같은 Python 코드를 서로 다른 수준의 실행 표현으로
> 처리하는 단계를 뜻한다.
> 이 문서는 바이트코드 명령을 실행하고 특수화하는 기본 인터프리터를 중심으로 하며, 더 높은
> tier의 uop 실행이나 JIT 세부사항은 다루지 않는다.

[Python 컴파일러](https://github.com/python/cpython/blob/3.14/InternalDocs/compiler.md)는
[`CodeObject`](https://github.com/python/cpython/blob/3.14/InternalDocs/code_objects.md)를
만든다는 점을 기억하자. 코드 객체에는 바이트코드 명령어와 함께 실행에 필요한 정적 데이터가
들어 있다. 예를 들면 상수 목록, 변수 이름,
[예외 테이블](https://github.com/python/cpython/blob/3.14/InternalDocs/exception_handling.md#format-of-the-exception-table)
등이다.

인터프리터의
[`PyEval_EvalCode()`](https://docs.python.org/3.14/c-api/veryhigh.html#c.PyEval_EvalCode)가
`CodeObject`를 실행하도록 호출되면,
[`Frame`](https://github.com/python/cpython/blob/3.14/InternalDocs/frames.md)을 만들고
[`_PyEval_EvalFrame()`](https://docs.python.org/3.14/c-api/veryhigh.html#c.PyEval_EvalCode)을
호출하여 그 프레임 안에서 코드 객체를 실행한다. 프레임은 명령어 포인터, 전역 이름 공간,
내장 이름 공간처럼 `CodeObject` 실행 중 변하는 상태를 보관한다. 프레임은 실행 중인
`CodeObject` 자체도 참조한다.

> **해설 — 코드 객체와 프레임의 역할 분리**
>
> 코드 객체는 여러 호출에서 재사용할 수 있는 명령과 정적 데이터다. 프레임은 특정 한 번의
> 호출에서만 생기는 지역 변수, 평가 스택, 현재 실행 위치를 담는다. nand2tetris에서 함수
> 명령은 하나지만 호출할 때마다 새로운 스택 프레임이 생기는 것과 같은 구분이다.

> **해설 — 원문의 평가 함수 링크**
>
> 원문에서 `_PyEval_EvalFrame()` 링크는 `PyEval_EvalCode()`의 공개 C API 문서로 연결되어
> 있어 대상이 맞지 않는다. `_PyEval_EvalFrame()`과 `_PyEval_EvalFrameDefault()`는
> CPython 내부 평가 경로이므로 정확한 구현은 `Python/ceval.c`와 생성된 interpreter
> cases에서 확인해야 한다. 이 번역에서는 원래 링크를 보존하고, 대상이 없던
> `_PyEval_EvalFrameDefault()` 참조에는 `Python/ceval.c` 링크를 보완했다.

`_PyEval_EvalFrame()`은 프레임 외에도 `tstate`라는
[`Thread State`](https://docs.python.org/3/c-api/init.html#c.PyThreadState) 객체를 받는다.
여기에는 예외 상태, 재귀 깊이 같은 스레드별 정보가 들어 있다. 스레드 상태를 통해
인터프리터별 상태인 `tstate->interp`에 접근할 수 있고, 여기에서 다시 런타임별, 즉 정말
전역인 상태 `tstate->interp->runtime`에 접근할 수 있다.

> **해설 — 상태의 범위**
>
> `tstate`는 현재 OS 스레드에 속한 실행 상태이고, `tstate->interp`는 하나의 Python
> 인터프리터 인스턴스에 속한 상태이며, `tstate->interp->runtime`은 CPython 런타임 전체가
> 공유하는 상태다. subinterpreter가 여러 개 있더라도 런타임 상태는 그보다 바깥 범위다.

마지막으로 `_PyEval_EvalFrame()`은 정수 인자 `throwflag`를 받는다. 이 값이 0이 아니면
인터프리터는 현재 예외를 즉시 발생시켜야 한다. 이 인자는
[`gen.throw`](https://docs.python.org/3.14/reference/expressions.html#generator.throw)
구현에 사용된다.

> **해설 — 정지된 제너레이터 안으로 예외를 넣기**
>
> `gen.throw(exc)`는 호출자 자리에서 예외를 올리는 것이 아니라, 멈춰 있던 제너레이터가
> 재개되는 지점에서 예외가 발생한 것처럼 만들어야 한다. `throwflag`는 정상 명령 실행 대신
> 이미 준비된 예외를 프레임 안에서 올리는 경로를 선택하게 한다.

기본 설정에서
[`_PyEval_EvalFrame()`](https://docs.python.org/3.14/c-api/veryhigh.html#c.PyEval_EvalCode)은
단순히
[`_PyEval_EvalFrameDefault()`](https://github.com/python/cpython/blob/3.14/Python/ceval.c)을
호출하여 프레임을 실행한다. 하지만
[`PEP 523`](https://peps.python.org/pep-0523/)에 따라 `interp->eval_frame`을 설정하면 이
동작을 바꿀 수 있다. 이하에서는 기본 함수인 `_PyEval_EvalFrameDefault()`를 설명한다.

> **해설 — 평가 프레임 훅**
>
> `interp->eval_frame`은 “이 프레임을 어떤 실행기가 처리할 것인가”를 교체하는 내부
> 확장 지점이다. 디버깅·프로파일링 도구나 별도 실행 엔진이 기본 평가 함수 대신 프레임
> 실행을 가로챌 수 있다. Python 함수 자체의 의미를 바꾸는 일반 사용자용 hook은 아니다.

### 명령어 디코딩

인터프리터의 첫 작업은 바이트코드 명령어를 해독하는 것이다. 바이트코드는 16비트 code
unit인 `_Py_CODEUNIT`의 배열로 저장된다. 각 code unit에는 부호 없는 8비트 `opcode`와
8비트 인자 `oparg`가 들어 있다. 디스크에 저장된 바이트코드 형식이 기계의 바이트 순서에
영향받지 않도록 `opcode`는 항상 첫 번째 바이트, `oparg`는 항상 두 번째 바이트에 둔다.
code unit에서 두 값을 꺼낼 때는 `_Py_OPCODE(word)`와 `_Py_OPARG(word)` 매크로를
사용한다. `NOP`, `POP_TOP`처럼 인자가 없는 명령에서는 `oparg`를 무시한다.

> **해설 — code unit과 명령어는 아직 같은 말이 아니다**
>
> `_Py_CODEUNIT` 하나는 정확히 2바이트의 저장 단위다. 대부분은 code unit 하나가 주
> opcode 하나를 담지만, 큰 인자를 위한 `EXTENDED_ARG`와 뒤에서 설명할 inline cache도
> code unit 배열을 차지한다. 따라서 바이트코드 배열의 2바이트 한 칸과 논리적 명령 한 개를
> 항상 같은 것으로 보면 안 된다.

인터프리터 주 루프를 단순화하면 다음과 같다.

```c
    _Py_CODEUNIT *first_instr = code->co_code_adaptive;
    _Py_CODEUNIT *next_instr = first_instr;
    while (1) {
        _Py_CODEUNIT word = *next_instr++;
        unsigned char opcode = _Py_OPCODE(word);
        unsigned int oparg = _Py_OPARG(word);
        switch (opcode) {
        // ... 각 opcode를 위한 case ...
        }
    }
```

이 루프는 명령어를 순회하며 각 명령에서 `opcode`와 `oparg`를 해독한 다음, 해당
`opcode`를 구현하는 `switch`의 `case`를 실행한다.

명령 형식은 서로 다른 opcode 256개를 지원하며, 이 수는 충분하다. 하지만 `oparg`도
8비트로 제한되므로 인자 표현 범위는 너무 작다. 이 제한을 넘기 위해 `EXTENDED_ARG`
opcode를 사용한다. 본 명령 앞에 `EXTENDED_ARG`를 하나 이상 붙이고, 각 명령의 추가 데이터
바이트를 결합하여 더 큰 `oparg`를 만든다. 예를 들어 다음 code unit 열을 보자.

```text
    EXTENDED_ARG  1
    EXTENDED_ARG  0
    LOAD_CONST    2
```

이 명령을 해독하면 `opcode`는 `LOAD_CONST`, `oparg`는 65538, 즉 `0x1_00_02`가 된다.
컴파일러는 `oparg`가 32비트 안에 들어가도록 `EXTENDED_ARG` 접두사를 최대 세 개까지만
만들어야 한다. 인터프리터 자체는 이 제한을 검사하지 않는다.

> **해설 — 바이트를 왼쪽에서 이어 붙인다**
>
> 위 인자 바이트 `1`, `0`, `2`는 16진수 자릿수 `0x01`, `0x00`, `0x02`로 이어진다.
> 결과는 `(1 << 16) | (0 << 8) | 2`, 즉 65538이다. 주 opcode는 마지막
> `LOAD_CONST`이고 앞의 `EXTENDED_ARG`들은 그 명령의 인자 폭만 넓힌다.

이하에서 `code unit`은 항상 2바이트를 뜻한다. `instruction`은 `EXTENDED_ARG` 0개에서
3개 뒤에 주 opcode 하나가 이어지는 code unit 열을 뜻한다.

앞의 단순 루프에서 `switch` 바로 위에 다음 루프를 삽입하면 완전한 instruction 하나를
해독할 수 있다.

```c
    while (opcode == EXTENDED_ARG) {
        word = *next_instr++;
        opcode = _Py_OPCODE(word);
        oparg = (oparg << 8) | _Py_OPARG(word);
    }
```

뒤에서 설명할 여러 이유 때문에 실제 구현은 이 코드와 다르다. 가장 큰 이유는
`EXTENDED_ARG`가 드물다는 점을 활용한 효율성이다.

> **해설 — 흔한 경로를 짧게 만든다**
>
> 모든 명령마다 `while` 조건을 반복 검사하는 단순 구현은 이해하기 쉽지만,
> `EXTENDED_ARG`가 없는 압도적으로 흔한 경로에도 비용을 더한다. 실제 생성 인터프리터는
> dispatch 구조와 예측 가능성을 고려해 드문 확장 인자 경로를 분리한다.

### 점프

`switch` 문에 도착했을 때 `next_instr`, 즉 “명령 오프셋”은 이미 다음 명령을 가리킨다는
점에 주의해야 한다. 따라서 점프 명령은 `next_instr`를 조정하는 방식으로 구현할 수 있다.

- 앞으로 점프하는 `JUMP_FORWARD`는 `next_instr += oparg`를 실행한다.
- 뒤로 점프하는 `JUMP_BACKWARD`는 `next_instr -= oparg`를 실행한다.

> **해설 — 기준점은 현재 명령이 아니라 다음 명령**
>
> 명령을 읽을 때 `*next_instr++`로 포인터가 먼저 증가했다. 따라서 상대 오프셋은 이미
> 다음 명령을 가리키는 위치를 기준으로 적용된다. nand2tetris에서 PC를 증가시킨 뒤 분기
> 주소를 적용하는 규칙과 비슷하게, 기준점을 혼동하면 한 code unit만큼 어긋난다.

### Inline cache entry

특수화되었거나 특수화할 수 있는 일부 명령에는 “inline cache”가 붙는다. inline cache는
2바이트 entry 하나 이상으로 구성되며, 바이트코드 배열에서 `opcode`/`oparg` 쌍 바로 뒤에
추가 word로 들어간다. 특정 명령의 inline cache 크기는 그 `opcode`에 따라 고정된다.
또한 [특수화 명령 family](#특수화)의 모든 구성원, 예를 들면 `LOAD_ATTR`,
`LOAD_ATTR_SLOT`, `LOAD_ATTR_MODULE`은 cache 크기가 같아야 한다. 컴파일러는 cache
entry 공간을 예약하고 0으로 초기화한다. cache entry는 code unit으로 표현되지만
`opcode`/`oparg` 형식을 따르지는 않는다.

> **해설 — 명령 바로 옆에 실행 관찰값을 둔다**
>
> 속성 조회에서 최근에 본 타입이나 딕셔너리 버전처럼 다음 실행을 빠르게 할 정보를 명령
> 바로 뒤에 저장한다. 명령과 cache가 메모리에서 가까우므로 별도 표를 찾아가는 비용을
> 줄일 수 있다. family 구성원의 cache 크기가 모두 같아야 generic 명령이 specialized
> 명령으로 바뀌어도 뒤 명령들의 위치가 변하지 않는다.

명령에 inline cache가 있다면 cache 배치는
[`Python/bytecodes.c`](https://github.com/python/cpython/blob/3.14/Python/bytecodes.c)의
명령 정의에 기술된다.
[`pycore_code.h`](https://github.com/python/cpython/blob/3.14/Include/internal/pycore_code.h)에
정의된 구조체를 사용하면 `next_instr`를 알맞은 `struct` 포인터로 캐스팅하여 cache에
접근할 수 있다. 이 `struct`의 크기는 기계 아키텍처, word 크기, 정렬 요구사항에 따라
달라지면 안 된다. 32비트 필드는 `_Py_CODEUNIT field[2]`처럼 선언해야 한다.

> **해설 — 평범한 `uint32_t` 필드가 아닌 code unit 배열**
>
> C 컴파일러는 아키텍처에 따라 구조체 필드 사이에 padding을 넣거나 정렬을 달리할 수 있다.
> cache는 바이트코드 배열 안에 놓이고 디스크 형식과도 관계되므로 배치가 플랫폼마다
> 달라지면 안 된다. 32비트 값을 16비트 code unit 두 개로 명시하면 고정된 저장 크기를
> 유지할 수 있다.

명령 구현은 `next_instr`가 inline cache를 지나가도록 직접 전진시켜야 한다. 예를 들어
cache가 4바이트, 즉 code unit 두 개라면 명령 코드에 `next_instr += 2;`가 있어야 한다.
이는 해당 code unit 수만큼 앞으로 상대 점프하는 것과 같다. 인터프리터 정의 DSL에서는
이를 `JUMPBY(n)`으로 작성한다. `n`은 건너뛸 code unit 수이며, 보통 이름 있는 상수로
주어진다.

0이 아닌 cache entry를 직렬화하면 문제가 생긴다. 직렬화 형식인 `marshal`은 기계의
바이트 순서와 무관해야 하기 때문이다.

> **해설 — 디스크에는 런타임 특수화 상태를 그대로 두지 않는다**
>
> inline cache는 실행 중 관찰한 플랫폼 종속 값이나 여러 code unit에 걸친 정수를 담을
> 수 있다. 이를 메모리 그대로 저장하면 endian이 다른 기계에서 해석이 달라질 수 있다.
> 컴파일 결과는 cache 공간을 0으로 예약하고, 코드 객체를 메모리에 올리는 과정과 실행 중
> 특수화가 필요한 초기값과 관찰값을 채운다.

inline cache 사용에 관한 자세한 내용은
[`PEP 659`](https://peps.python.org/pep-0659/#ancillary-data)를 참고한다.

### 평가 스택

대부분의 명령은 객체 참조 `PyObject *` 형태의 데이터를 읽거나 쓴다. CPython 바이트코드
인터프리터는 스택 머신이므로, 명령은 데이터를 스택에 push하고 pop하는 방식으로 동작한다.
스택은 코드 객체를 실행하는 프레임의 일부다. 스택의 최대 깊이는 컴파일러가 계산하여 코드
객체의 `co_stacksize` 필드에 저장한다. 따라서 프레임을 만들 때 스택을 `PyObject *`
포인터의 연속 배열로 미리 할당할 수 있다.

> **해설 — nand2tetris VM 스택과의 대응**
>
> `BINARY_OP` 같은 명령은 피연산자를 명령 안에 직접 담지 않고 평가 스택에서 꺼낸다.
> 다만 이 평가 스택은 함수 호출 관계를 저장하는 call stack과 개념적으로 구분된다.
> CPython 프레임은 해당 호출의 지역 변수 영역과 평가 스택 영역을 함께 가진다.

각 명령의 stack effect는
[opcode 메타데이터](https://github.com/python/cpython/blob/3.14/Include/internal/pycore_opcode_metadata.h)를
통해서도 노출된다. `_PyOpcode_num_popped`와 `_PyOpcode_num_pushed` 두 함수는 명령이
스택 원소를 몇 개 소비하고 몇 개 생성하는지 알려 준다. 예를 들어 `BINARY_OP`는 객체 두
개를 pop하고 결과를 스택에 push한다.

스택은 메모리의 높은 주소 방향으로 자란다. `PUSH(x)`는
`*stack_pointer++ = x`와 같고, `x = POP()`은 `x = *--stack_pointer`와 같다.
overflow와 underflow 검사는 debug 모드에서는 활성화되지만, 그 밖의 빌드에서는
최적화로 제거된다.

실행 중 어느 시점이든 명령어 포인터만으로 스택 높이를 알 수 있다. 스택의 각 원소가 가진
일부 성질도 알려져 있다. 특히 `NULL`을 스택에 push할 수 있는 명령은 소수이며,
`NULL`일 가능성이 있는 위치도 알려져 있다. `GET_ITER`, `FOR_ITER` 같은 일부 명령은
iterator임이 알려진 객체를 push하거나 pop한다.

> **해설 — 컴파일 시점의 스택 데이터 흐름**
>
> 실제 객체 값은 실행 전에는 모르지만, 각 opcode의 pop/push 개수와 제어 흐름을 결합하면
> 각 명령 시작점의 스택 높이를 계산할 수 있다. 특정 슬롯이 `NULL` 표식인지 iterator인지
> 같은 제한된 타입 성질도 opcode 규칙으로 추적한다. 이는 완전한 정적 타입 분석이 아니라
> 바이트코드 실행 안전성과 최적화에 필요한 형태 분석이다.

스택 깊이를 정적으로 알 수 없는 명령어 열은 유효하지 않은 것으로 간주한다. 바이트코드
컴파일러는 이런 명령어 열을 만들지 않는다. 예를 들어 다음 명령어 열은 반복할 때마다 스택에
항목을 계속 push하므로 유효하지 않다.

```text
    LOAD_FAST 0
    JUMP_BACKWARD 2
```

> **참고**
>
> 평가 스택과 call stack을 혼동하지 말아야 한다. call stack은 함수 호출과 반환을
> 구현하는 데 사용한다.

### 오류 처리

opcode 구현에서 예외를 발생시키면
[`Python/ceval.c`](https://github.com/python/cpython/blob/3.14/Python/ceval.c)의
`exception_unwind` 레이블로 점프한다. 그 뒤의 예외 처리는
[예외 처리 문서](https://github.com/python/cpython/blob/3.14/InternalDocs/exception_handling.md#handling-exceptions)에
설명되어 있다.

> **해설 — C의 공통 오류 경로**
>
> 각 opcode가 예외 전파와 handler 검색을 모두 따로 구현하지 않는다. 실패한 opcode는
> 예외 상태를 설정한 뒤 공통 `exception_unwind` 경로로 이동한다. 이 경로가 현재 바이트코드
> 위치에 맞는 예외 handler를 찾고, 없으면 프레임을 되감는다.

### Python에서 Python으로의 호출

인터프리터가 어떤 C 함수를 호출하고, 그 C 함수가 다시 인터프리터를 호출할 수 있으므로
`_PyEval_EvalFrameDefault()` 함수는 재귀적으로 호출될 수 있다. Python 3.10 이하에서는
Python 함수가 다른 Python 함수를 호출할 때에도 이런 재귀가 일어났다. `CALL` opcode는
피호출자의 `tp_call` dispatch 함수를 호출했다. 이 함수가 코드 객체를 꺼내고 call stack에
새 프레임을 만든 다음 인터프리터를 다시 호출했다. 이 방식은 매우 범용적이지만, 중첩된
Python 호출 하나마다 C 스택 프레임을 여러 개 소비하여 복구할 수 없는 C 스택 overflow
위험을 높였다.

> **해설 — Python 호출 깊이와 C 호출 깊이를 분리한다**
>
> 과거에는 Python 함수 A가 B를 호출할 때 C 함수 호출도 중첩되었다. Python 재귀가 깊어지면
> 운영체제의 제한된 C stack도 함께 소모된다. 3.11 이후의 기본 경로는 하나의 평가 루프
> 안에서 Python 프레임만 교체하므로 Python call stack이 C call stack과 일대일로 자라지
> 않는다.

3.11부터 `CALL` 명령은 함수 객체를 특별 처리하여 호출을 “inline”한다. 호출을 inline하면
새 프레임을 call stack에 push하고, 인터프리터는 피호출자 바이트코드의 시작으로 “점프”한다.
inline된 피호출자가 `RETURN_VALUE`를 실행하면 call stack에서 프레임을 pop하고, 반환 주소로
“점프”하여 호출자로 돌아간다. 프레임에는 해당 프레임이 inline되었는지를 나타내는
`frame->is_entry` flag가 있다. inline되지 않은 프레임에서 이 flag가 설정된다.
`RETURN_VALUE`가 설정된 flag를 발견하면 일반적인 정리를 수행하고
`_PyEval_EvalFrameDefault()` 자체에서 C 호출자로 완전히 반환한다.

> **해설 — 여기서 inline은 함수 본문 복사가 아니다**
>
> 컴파일러 최적화의 함수 inlining처럼 피호출자 코드를 호출자 코드에 복사한다는 뜻이 아니다.
> C 함수를 재귀 호출하지 않고 같은 dispatch 루프 안에서 프레임을 바꾸고 피호출자의 첫
> 명령으로 이동한다는 뜻이다.

> **해설 — 3.14 구현과 다른 오래된 설명**
>
> CPython 3.14의 `_PyInterpreterFrame`에는 `is_entry` 필드가 없다. 현재 경계 처리는
> `frame->owner`, `INTERPRETER_EXIT`를 가진 shim frame, `return_offset`을 이용한다.
> `RETURN_VALUE`는 `frame->owner != FRAME_OWNED_BY_INTERPRETER`임을 확인하고 현재 frame을
> 이전 frame에서 분리한 뒤 정리·pop한다. 이어 호출자 frame의 `return_offset`을 적용하고
> 반환값을 호출자의 평가 스택에 넘긴다. 최상위 Python frame이 돌아갈 대상은
> `FRAME_OWNED_BY_INTERPRETER`인 shim frame이며, 그 frame의 `INTERPRETER_EXIT`가 C
> 호출자에게 최종 반환한다.
>
> 이 문단은 3.11 초기 구현의 설명이 남은 것으로 보인다. 호출을 C 재귀 없이 같은 평가
> 루프에서 처리한다는 큰 구조는 유효하지만, 3.14의 정확한 반환 경계는
> [`frames.md`](https://github.com/python/cpython/blob/3.14/InternalDocs/frames.md)의
> “Shim frames”와 “The Instruction Pointer” 절을 따라야 한다.

처리되지 않은 예외가 발생할 때에도 이와 비슷한 검사를 수행한다.

### Call stack

3.10까지 call stack은
[frame 객체](https://github.com/python/cpython/blob/3.14/InternalDocs/frames.md)의 단일
연결 리스트로 구현되었다. 호출할 때마다 stack frame을 heap에 할당해야 했으므로 비용이
컸다.

3.11부터 frame은 더 이상 항상 완전한 객체로 만들어지지 않는다. 대신 더 가벼운 내부
`_PyInterpreterFrame` 구조체를 사용한다. 대부분의 frame은 스레드별 stack에 연속해서
할당된다. 자세한 내용은
[`Python/pystate.c`](https://github.com/python/cpython/blob/3.14/Python/pystate.c)의
`_PyThreadState_PushFrame`을 참고한다. 이 방식은 메모리 지역성을 높이고 오버헤드를
줄인다. 현재 `datastack_chunk`에 공간이 충분하면
`_PyThreadState_HasStackSpace`로 확인한 뒤 `_PyThreadState_PushFrame` 대신 더 가벼운
`_PyFrame_PushUnchecked`를 사용할 수 있다.

> **해설 — frame stack의 빠른 할당 경로**
>
> 스레드별로 확보한 연속 메모리 덩어리가 `datastack_chunk`다. 남은 공간이 충분하다는
> 사실을 이미 확인했다면, 새 덩어리를 확보할 가능성까지 처리하는 일반 함수 대신
> `_PyFrame_PushUnchecked`로 포인터를 전진시키는 빠른 경로를 사용할 수 있다.

Python 코드가 `sys._getframe()`을 호출하거나 확장 모듈이
[`PyEval_GetFrame()`](https://docs.python.org/3/c-api/reflection.html#c.PyEval_GetFrame)을
호출하는 경우처럼 실제 `PyFrameObject`가 필요할 때도 있다. 이 경우 정식
`PyFrameObject`를 할당하고 `_PyInterpreterFrame`의 정보로 초기화한다.

제너레이터는 push/pop 모델을 따르지 않으므로 상황이 더 복잡하다. 같은 메커니즘에 기반한
async 함수도 여기에 포함된다. 제너레이터 객체에는 지역 변수와 평가 스택에 쓰이는 가변 크기
부분을 포함한 `_PyInterpreterFrame` 공간이 있다. 제너레이터 함수나 async 함수를 처음
호출하면 특수 opcode `RETURN_GENERATOR`를 실행한다. 이 opcode는 제너레이터 객체를 만들
책임이 있다. 제너레이터 객체의 `_PyInterpreterFrame`은 현재 stack frame을 복사하여
초기화한다. 그런 다음 현재 stack frame을 frame stack에서 pop하고 제너레이터 객체를
반환한다. 세부 동작은 `is_entry` flag에 따라 달라진다. 제너레이터를 재개하면 인터프리터가
제너레이터의 `_PyInterpreterFrame`을 frame stack에 push하고 실행을 계속한다.
[제너레이터 문서](https://github.com/python/cpython/blob/3.14/InternalDocs/generators.md)도
참고한다.

> **해설 — 생성과 실행을 분리하는 `RETURN_GENERATOR`**
>
> 제너레이터 함수를 호출했다고 본문을 곧바로 실행하지 않는다. 우선 호출용으로 준비한 현재
> frame 상태를 제너레이터 객체 안으로 옮기고 객체를 반환한다. 이후 `next()`나 `send()`로
> 재개할 때 그 내장 frame을 실행 stack에 연결한다.

> **해설 — 이 문단의 `is_entry`도 오래된 설명이다**
>
> 앞 문단과 마찬가지로 3.14 `_PyInterpreterFrame`에는 `is_entry`가 없다. 제너레이터가
> frame을 소유하고 중단·재개 때 frame stack과 연결된다는 핵심은 맞지만, 경계별 세부 처리는
> 현재 `RETURN_GENERATOR` 구현과 shim frame 규칙을 확인해야 한다.

> **원문 주석 — 미완성 절**
>
> 다음 “여러 종류의 변수” 절은 원문에서 HTML 주석 처리되어 렌더링되지 않는 미완성
> 내용이다. 빠짐없이 옮기기 위해 여기에서는 보이도록 번역한다.

### 여러 종류의 변수

바이트코드 컴파일러는 각 변수 이름이 정의된 scope를 판정하고, 그에 맞는 명령을 생성한다.
예를 들어 지역 변수를 stack에 올릴 때는 `LOAD_FAST`를 사용하고, 전역 변수를 올릴 때는
`LOAD_GLOBAL`을 사용한다. 주요 변수 종류는 다음과 같다.

- fast locals: 함수에서 사용한다.
- 느린 또는 일반 locals: 클래스와 최상위 수준에서 사용한다.
- globals와 builtins: 컴파일러는 둘을 구분할 수 없다. 실행 시 특수화 인터프리터는
  구분할 수 있다.
- cells: nonlocal 참조에 사용한다.

> **해설 — 이름 하나가 서로 다른 opcode를 만드는 이유**
>
> 함수 지역 변수는 컴파일 때 슬롯 번호를 정할 수 있어 `LOAD_FAST`로 배열처럼 접근한다.
> 전역 이름은 모듈 globals에서 먼저 찾고 없으면 builtins에서 찾기 때문에
> `LOAD_GLOBAL`이 두 이름 공간을 런타임에 다룬다. cell은 중첩 함수가 바깥 scope의 값을
> 공유하도록 간접 저장소 역할을 한다.

이 절은 실행기 관점의 개요다. local·cell·free·global 분류가 CodeObject의 이름 표,
이름 딕셔너리와 Frame 슬롯, `LOAD`·`STORE` 계열로 연결되는 전체 과정은
[컴파일에서 실행까지](../compilation-to-execution/README.ko.md#이름-분류에서-저장소와-opcode까지)를
참고한다.

(TODO: 이 절의 나머지를 작성해야 한다. 하지만 저자가 다른 일에 정신이 팔려 한동안 계속
작성할 시간이 없게 되었다.)

> **원문 주석 — 미완성 절**
>
> 다음 “기타 주제” 절도 원문에서 HTML 주석 처리되어 렌더링되지 않는 TODO 목록이다.

### 기타 주제

(TODO: 다음 항목은 각각 별도의 절이 필요할 것이다.)

- `co_consts`, `co_names`, `co_varnames`와 그와 비슷한 필드
- 호출의 동작 방식: 인자 전달, 반환, 예외
- eval breaker: interrupt, GIL
- tracing
- 현재 줄 번호 설정: 디버거가 유도하는 점프
- specialization, inline cache 등

> **해설 — eval breaker**
>
> eval breaker는 평가 루프가 “곧 처리해야 할 비정상·비동기 작업이 있는가?”를 빠르게
> 확인하는 신호다. signal, pending call, 스레드 전환이나 GIL 관련 요청 같은 일을 모든
> opcode 구현에 각각 넣는 대신, 안전한 지점에서 이 상태를 검사하고 필요한 느린 경로로
> 들어간다. 원문은 이름만 TODO로 남기고 실제 동작은 설명하지 않는다.

### 새 바이트코드 명령 도입

새 기능을 구현하거나 기존 기능의 컴파일 방식을 바꾸기 위해 새 opcode를 추가해야 할 때가
있다. 이 절은 이 작업에 필요한 변경 사항을 설명한다.

먼저 바이트코드 이름을 정하고
[`Python/bytecodes.c`](https://github.com/python/cpython/blob/3.14/Python/bytecodes.c)에
구현한 뒤
[`Doc/library/dis.rst`](https://github.com/python/cpython/blob/3.14/Doc/library/dis.rst)에
문서 항목을 추가해야 한다. 그다음 `make regen-cases`를 실행한다. 이 명령은 opcode 번호를
할당하고
[`Include/opcode_ids.h`](https://github.com/python/cpython/blob/3.14/Include/opcode_ids.h)를
갱신하며, 실제 바이트코드 구현을 담는
[`Python/generated_cases.c.h`](https://github.com/python/cpython/blob/3.14/Python/generated_cases.c.h)와
추가 메타데이터 파일들을 재생성한다.

> **해설 — generated cases는 결과물이다**
>
> `generated_cases.c.h`의 `case`를 직접 고치는 것이 아니라 `Python/bytecodes.c`의 DSL
> 정의를 고친 뒤 재생성해야 한다. opcode 번호, 실행 코드, stack effect 같은 여러 생성물이
> 같은 정의에서 나오므로 수동 편집하면 서로 불일치하기 쉽다.

새 바이트코드를 추가하면 `.pyc` 파일의 “magic number”도 바꿔야 한다.
[`Lib/importlib/_bootstrap_external.py`](https://github.com/python/cpython/blob/3.14/Lib/importlib/_bootstrap_external.py)의
`MAGIC_NUMBER` 값을 올린다. 이 번호를 바꾸면 예전 `MAGIC_NUMBER`를 가진 모든 `.pyc`
파일을 import할 때 인터프리터가 다시 컴파일한다. `MAGIC_NUMBER`를 바꾸면
[`PC/launcher.c`](https://github.com/python/cpython/blob/3.14/PC/launcher.c)의
`magic_values` 배열 범위도 갱신해야 할 수 있다.
[`Lib/importlib/_bootstrap_external.py`](https://github.com/python/cpython/blob/3.14/Lib/importlib/_bootstrap_external.py)
변경은 `make regen-importlib`을 실행한 뒤에야 적용된다.

> **해설 — 바이트코드 버전 표식**
>
> 같은 숫자 opcode라도 인터프리터 버전에 따라 의미나 배치가 달라질 수 있다. magic
> number는 디스크 cache가 현재 실행기와 호환되는지 알려 주는 버전 표식이다. 이를 올리지
> 않으면 새 인터프리터가 오래된 `.pyc`를 새 형식으로 오해할 수 있다.

> **참고**
>
> 새 바이트코드 대상을
> [`Python/bytecodes.c`](https://github.com/python/cpython/blob/3.14/Python/bytecodes.c)에
> 추가하고 `make regen-cases`를 실행하기 전에 `make regen-importlib`부터 실행하면 오류가
> 난다. 새 바이트코드 대상을 먼저 추가한 뒤에만 `make regen-importlib`을 실행해야 한다.

> **참고**
>
> Windows에서는 `./build.bat` 스크립트를 실행하면 별도 인자 없이 필요한 파일을 자동으로
> 재생성한다.

마지막으로 새 바이트코드를 실제로 사용하게 해야 한다.
[`Python/codegen.c`](https://github.com/python/cpython/blob/3.14/Python/codegen.c)가 이
바이트코드를 방출하도록 갱신한다.
[`Python/flowgraph.c`](https://github.com/python/cpython/blob/3.14/Python/flowgraph.c)의
최적화도 갱신해야 할 수 있다. 새 opcode가 제어 흐름이나 block stack에 영향을 준다면
[`Objects/frameobject.c`](https://github.com/python/cpython/blob/3.14/Objects/frameobject.c)의
`frame_setlineno()`도 갱신해야 할 수 있다. 새 opcode가 `FORMAT_VALUE`나
`MAKE_FUNCTION`처럼 인자를 특별한 방식으로 해석한다면
[`Lib/dis.py`](https://github.com/python/cpython/blob/3.14/Lib/dis.py)도 수정해야 할 수 있다.

이미 존재하는 바이트코드 출력에 영향을 주는 변경을 했지만 아직 magic number를 바꾸지
않았다면, 예전 `.pyc`와 `.pyo` 파일을 반드시 삭제해야 한다. 최종적으로 바이트코드를
바꾸면 magic number도 바꾸게 되지만, 작업을 디버깅하는 동안에는 매번 magic number를
올리지 않은 채 바이트코드 출력을 여러 번 바꿀 수 있다. 그러면 다시 생성되지 않는 오래된
`.pyc` 파일이 남을 수 있다.
`find . -name '*.py[co]' -exec rm -f '{}' +`를 실행하면 보유한 `.pyc` 파일을 모두
삭제하여 새 파일 생성을 강제할 수 있고, 새 바이트코드를 제대로 시험할 수 있다. frozen
importlib 파일의 바이트코드를 갱신하려면 `make regen-importlib`을 실행한다. 그 뒤 생성된
C 파일을 다시 컴파일하려면 `make`를 한 번 더 실행해야 한다.

> **해설 — 재생성 순서와 stale cache**
>
> DSL 변경, cases 재생성, importlib 재생성, C 재빌드는 서로 다른 산출물을 갱신한다.
> 개발 중 magic number를 계속 바꾸지 않는다면 소스보다 오래된 `.pyc`가 실행되어 수정이
> 반영되지 않은 것처럼 보일 수 있다. 제시된 `find` 명령은 파일을 삭제하므로 저장소 위치와
> 대상 패턴을 확인한 뒤 실행해야 한다.

### 특수화

[`PEP 659`](https://peps.python.org/pep-0659/)에서 도입한 바이트코드 specialization은
런타임 정보에 따라 명령을 다시 써 프로그램 실행 속도를 높인다. 프로그램에서 실제로 만난
경우에만 동작하는 더 빠른 버전으로 generic 명령을 교체한다. 특수화할 수 있는 각 명령은
[inline cache](#inline-cache-entry)를 장부처럼 사용하면서 자신을 다시 쓸 책임이 있다.

> **해설 — 컴파일러 최적화와 다른 런타임 최적화**
>
> 컴파일 시점에는 `obj.attr`에서 `obj`의 실제 타입을 모를 수 있다. 실행하면서 같은 타입과
> 같은 구조가 반복된다는 사실을 관찰하면 generic 조회를 그 경우에 맞는 빠른 명령으로
> 바꿀 수 있다. 코드를 실행하며 수집한 정보에 기반하므로 adaptive specialization이다.

adaptive instruction이 실행될 때 인자와 cache 내용에 따라 스스로 특수화를 시도할 수 있다.
이 작업은
[`Python/specialize.c`](https://github.com/python/cpython/blob/3.14/Python/specialize.c)의
`_Py_Specialize_XXX` 함수 중 하나를 호출하여 수행한다.

specialized instruction은 특별한 경우에 대한 가정이 여전히 성립하는지 검사할 책임이 있다.
가정이 더 이상 맞지 않으면 generic 버전으로 de-optimize해야 한다.

> **해설 — guard와 de-optimization**
>
> 빠른 명령은 “객체 타입과 딕셔너리 구조가 이전과 같다” 같은 가정 아래 검사를 생략한다.
> 실행 전의 작은 guard가 그 가정을 확인한다. 실패하면 틀린 빠른 경로를 계속 쓰지 않고
> generic 명령으로 돌아간다. Python의 동적 변경 가능성을 유지하면서 흔한 경우만 빠르게
> 만드는 장치다.

### 명령 family

명령 *family*는 adaptive instruction과, 그것이 교체될 수 있는 specialized instruction을
묶은 것이다. family에는 다음과 같은 기본 성질이 있다.

- 바이트코드 컴파일러가 생성한 코드에서는 단일 명령 하나에 대응한다.
- 실행 횟수를 기록하고 일정한 간격으로 자기 특수화를 시도하는 adaptive instruction이
  정확히 하나 있다. 특수화하지 않을 때는 base 구현을 실행한다.
- 특정 런타임 값 또는 값 집합에 맞춘 specialized form이 하나 이상 있다.
- 올바르게 실행하려면 모든 family 구성원의 inline cache entry 수가 같아야 한다. 각
  구성원이 모든 entry를 사용할 필요는 없지만, 실행할 때 사용하지 않는 entry도
  건너뛰어야 한다.

> **해설 — opcode를 바꿔도 명령 폭을 유지한다**
>
> 실행 중 `LOAD_GLOBAL`을 `LOAD_GLOBAL_MODULE`로 바꿀 때 뒤의 명령 위치까지 움직일 수는
> 없다. family 전체가 같은 cache 공간을 차지하면 opcode만 교체해도 바이트코드 배열의
> 배치와 점프 목적지가 그대로 유지된다.

현재 구현은 다음 조건도 요구한다. 다만 이 조건들은 본질적인 성질은 아니므로 바뀔 수 있다.

- 모든 family는 inline cache entry를 하나 이상 사용하며 첫 entry는 항상 counter다.
- 모든 명령 이름은 adaptive instruction의 이름으로 시작해야 한다.
- specialized form의 이름은 무엇에 특수화했는지 설명해야 한다.

### Family 예제

[`Python/bytecodes.c`](https://github.com/python/cpython/blob/3.14/Python/bytecodes.c)의
`LOAD_GLOBAL` 명령에는 비교적 단순한 예제로 볼 수 있는 adaptive family가 이미 있다.

`LOAD_GLOBAL` 명령은 adaptive specialization을 수행하며, counter가 0에 도달하면
`_Py_Specialize_LoadGlobal()`을 호출한다.

family에는 specialized instruction 두 개가 있다. `LOAD_GLOBAL_MODULE`은 모듈의 전역
변수에 특수화되어 있고, `LOAD_GLOBAL_BUILTIN`은 builtin 변수에 특수화되어 있다.

> **해설 — counter가 0이 될 때까지 기다리는 이유**
>
> 처음 한두 번 실행한 관찰만으로 특수화하면 초기화 비용을 회수하지 못하거나 우연한 타입에
> 과도하게 맞출 수 있다. counter는 실행 빈도를 누적하거나 다음 특수화 시도 시점을 조절해,
> 충분히 뜨거운 명령에서만 특수화 비용을 지불하게 한다.

### 성능 분석

특수화의 이익은 다음 비율로 평가할 수 있다. `Tbase/Tadaptive`.

여기서 `Tbase`는 base instruction의 평균 실행 시간이고, `Tadaptive`는 specialized form과
adaptive form을 실행하는 데 걸리는 평균 시간이다.

`Tadaptive = (sum(Ti*Ni) + Tmiss*Nmiss)/(sum(Ni)+Nmiss)`

`Ti`는 family의 `i`번째 명령을 실행하는 시간이고, `Ni`는 그 명령을 실행한 횟수다.
`Tmiss`는 miss를 처리하는 시간이며, de-optimization과 base instruction 실행 시간을
포함한다.

> **해설 — 가중 평균과 이익 비율**
>
> 분자는 각 실행 형태의 시간에 발생 횟수를 곱해 모두 더하고, 분모는 전체 실행 횟수다.
> `Tbase/Tadaptive`가 1보다 크면 adaptive family의 평균 실행 시간이 base보다 짧다는
> 뜻이다. specialized instruction 자체가 빨라도 miss와 특수화 관리 비용이 많으면 전체
> 평균은 나빠질 수 있다.

이상적인 상황은 miss가 드물고 specialized form이 base instruction보다 훨씬 빠른 경우다.
`LOAD_GLOBAL`은 거의 이상적이며 `Nmiss/sum(Ni) ≈ 0`이다. 이때
`Tadaptive ≈ sum(Ti*Ni)`가 된다. specialized form인 `LOAD_GLOBAL_MODULE`과
`LOAD_GLOBAL_BUILTIN`은 adaptive base instruction보다 훨씬 빠를 것으로 예상할 수 있으므로,
`LOAD_GLOBAL` 특수화는 이익이 있을 것으로 기대한다.

> **해설 — 원문의 마지막 근사식에는 분모가 빠져 있다**
>
> `Tadaptive`는 평균 시간이므로 miss를 무시하더라도 차원이 맞는 식은
> `Tadaptive ≈ sum(Ti*Ni) / sum(Ni)`다. 원문의 `≈ sum(Ti*Ni)`는 전체 누적 시간이며
> 평균이 아니다. 원문이 말하려는 핵심은 miss 항을 무시할 수 있고 빠른 specialized form의
> 가중 평균이 지배한다는 것이다.

### 설계 고려사항

`LOAD_GLOBAL`은 이상적인 경우에 가깝지만 `LOAD_ATTR`, `CALL_FUNCTION` 같은 명령은 그렇지
않다. 성능을 최대화하려면 모든 specialized instruction의 `Ti`를 낮게 유지하고 `Nmiss`도
가능한 한 낮게 유지해야 한다.

> **해설 — `CALL_FUNCTION` 명칭**
>
> 이 절의 `CALL_FUNCTION`은 설계 예시로 남은 이전 명칭이다. CPython 3.14의 일반 호출
> opcode family는 `CALL`을 중심으로 정의되어 있으며, 독립된 현재 opcode 이름으로
> `CALL_FUNCTION`을 찾으면 안 된다. `CALL_FUNCTION_EX`는 별도의 이름으로 존재한다.

`Nmiss`를 낮게 유지하려면 base instruction이 만나는 거의 모든 값에 대한 특수화가 있어야
한다. `sum(Ti*Ni)`를 낮게 유지하려면 `Ti`가 낮아야 하므로 분기와 의존적 메모리 접근,
즉 pointer chasing을 최소화해야 한다. 두 목표가 충돌할 수 있으므로 instruction family를
설계할 때 판단과 실험이 필요하다.

> **해설 — 넓게 대응하기와 빠르게 실행하기의 충돌**
>
> 특수화 종류를 많이 만들면 더 다양한 값을 hit로 처리해 miss를 줄일 수 있다. 하지만 각
> fast path가 복잡해지거나 어떤 특수화를 선택할지 분기가 늘면 `Ti`가 커진다. 반대로 매우
> 좁은 경우만 빠르게 만들면 각 hit는 빠르지만 miss가 잦아진다.

inline cache 크기는 성능을 해치지 않는 범위에서 가능한 한 작아야 한다. 그래야 점프에 필요한
`EXTENDED_ARG` 수를 줄이고 CPU data cache의 부담도 줄일 수 있다.

> **해설 — cache 크기가 점프 인자에도 영향을 준다**
>
> inline cache가 커지면 바이트코드 배열이 길어지고 점프 거리가 커진다. 8비트 `oparg`
> 범위를 넘는 점프가 많아지면 `EXTENDED_ARG`가 더 필요하다. 동시에 더 큰 명령 stream은
> CPU cache에 들어갈 유효 코드의 양을 줄인다.

#### 데이터 수집

명령을 어떻게 특수화할지 정하기 전에 데이터를 모으는 것이 중요하다. base instruction은
어떤 사용 패턴을 보이는가? 가장 좋은 방법은 인터프리터에 instrumentation을 추가하여
데이터를 얻는 것이다. 어차피 specialization 함수와 adaptive instruction이 필요하므로,
specialization 함수에 instrumentation을 추가하는 방식이 가장 쉽다.

> **해설 — 추측보다 실제 workload**
>
> 어떤 타입과 객체 배치가 흔한지는 프로그램 종류에 따라 다르다. benchmark와 실제
> workload에서 hit·miss·deferred 횟수와 실행 시간을 수집해야, 드문 경우를 위해 복잡한
> 특수화를 추가하는 실수를 피할 수 있다.

#### 특수화 선택

특수화 adaptive interpreter의 성능은 특수화의 품질과 낮은 특수화 오버헤드에 달려 있다.

specialized instruction은 빨라야 한다. 특정 값 집합에 맞춰 다음 두 조건을 만족하도록
specialized instruction을 설계해야 한다.

1. 들어온 값이 그 집합에 속하는지 적은 오버헤드로 확인한다.
2. 연산을 빠르게 수행한다.

이를 위해 membership을 빠르게 검사할 수 있고, 그 집합에 속한다는 사실만으로 연산을 빠르게
수행하기에 충분한 값 집합을 선택해야 한다.

예를 들어 `LOAD_GLOBAL_MODULE`은 keys가 예상 version을 가진 `globals()` 딕셔너리에
특수화되어 있다.

다음 조건은 빠르게 검사할 수 있다.

- `globals->keys->dk_version == expected_version`

연산도 다음과 같이 빠르게 수행할 수 있다.

- `value = entries[cache->index].me_value;`.

> **해설 — dictionary version을 guard로 사용한다**
>
> 딕셔너리의 key 구조가 바뀔 때 version도 바뀐다. cache에 저장한 예상 version과 현재
> version이 같다면 이전에 찾은 `index`가 여전히 같은 전역 이름을 가리킨다고 빠르게
> 판단할 수 있다. key를 다시 hash하고 탐색하지 않고 entry 배열의 위치에서 값을 바로
> 읽는다.

명령 하나의 성능을 측정할 때 관련 없는 요인의 시간까지 함께 측정할 수밖에 없으므로,
특수화 품질을 평가하려면 어느 정도 판단이 필요하다.

일반적으로 specialized instruction은 base instruction보다 훨씬 빨라야 한다.

#### Specialized instruction 구현

일반적으로 specialized instruction은 두 부분으로 구현해야 한다.

1. 각각 `DEOPT_IF(guard-condition-is-false, BASE_NAME)` 형태인 guard의 연속.
2. 가능한 한 분기가 없고 의존적 메모리 접근이 최소인 연산.

실제로는 guard에 필요한 데이터를 연산에서도 다시 사용할 수 있으므로 두 부분이 겹칠 수 있다.

연산 안에 분기가 있다면 그 분기를 없애기 위해 더 세분화된 특수화를 고려한다.

> **해설 — pointer chasing**
>
> 어떤 값을 얻기 위해 포인터 A가 가리키는 객체를 읽고, 거기서 포인터 B를 얻고, 다시 B가
> 가리키는 메모리를 읽는 식의 연쇄 접근이다. 뒤 주소가 앞 메모리 읽기 결과에 의존하므로
> CPU가 여러 읽기를 병렬로 진행하기 어렵다. cache에 최종 index나 version을 가까이 저장하는
> 이유가 여기에 있다.

#### 통계 유지

마지막으로 통계가 올바르게 수집되도록 주의해야 한다. 마지막 `DEOPT_IF`까지 통과한 뒤에는
`STAT_INC(BASE_INSTRUCTION, hit)`로 hit를 기록해야 한다. adaptive instruction에서 최적화를
나중으로 미뤘다면 `STAT_INC(BASE_INSTRUCTION, deferred)`로 기록해야 한다.

> **해설 — hit, miss, deferred를 구분한다**
>
> hit는 specialized guard가 모두 성공한 실행이고, miss는 가정이 깨져 de-optimize한
> 실행이다. deferred는 아직 자료가 부족하거나 재시도 시점이 아니어서 특수화를 미룬
> 경우다. 이를 구분해야 특수화가 실제로 빨라서 유지되는지, 계속 실패하거나 미뤄지는지
> 판단할 수 있다.

### 추가 자료

- Brandt Bucher가 PyCon US 2023에서 발표한 specializing interpreter 강연:
  [슬라이드](https://github.com/brandtbucher/brandtbucher/blob/master/2023/04/21/inside_cpython_311s_new_specializing_adaptive_interpreter.pdf),
  [영상](https://www.youtube.com/watch?v=PGZPSWZSkJI&t=1470s)

---

## 제2부: JIT

> 원문: [CPython 3.14 — The JIT](https://github.com/python/cpython/blob/3.14/InternalDocs/jit.md)

[적응형 인터프리터](https://github.com/python/cpython/blob/3.14/InternalDocs/interpreter.md)는 [바이트코드 컴파일러](https://github.com/python/cpython/blob/3.14/InternalDocs/compiler.md)가 생성한 바이트코드 명령어와 그 명령어의 [특수화 버전](https://github.com/python/cpython/blob/3.14/InternalDocs/interpreter.md#specialization)을 실행하는 메인 루프로 이루어진다. 이 인터프리터에서 런타임 최적화는 한 번에 명령어 하나에 대해서만 수행할 수 있다. JIT는 바이트코드 명령어의 전체 시퀀스를 교체하는 메커니즘을 기반으로 하며, 덕분에 여러 명령어에 걸친 최적화가 가능하다.

> **해설 — 명령어 하나의 특수화와 trace 전체 최적화**
>
> 적응형 인터프리터는 예를 들어 일반 덧셈 명령어를 “두 정수의 덧셈”에 특화된 명령어로 바꿀 수 있다. 하지만 각 명령어를 따로 최적화하면 앞 명령어가 만든 값에 관한 정보를 뒤 명령어까지 계속 활용하기 어렵다.
>
> JIT 쪽은 자주 실행되는 연속 경로인 trace를 하나의 단위로 다룬다. 그래서 여러 명령어 사이의 불필요한 검사나 중간 작업을 함께 분석하고 제거할 수 있다. 여기서 JIT는 처음부터 함수 전체를 기계어로 컴파일하는 전통적인 방식보다는 실행 중 관찰한 경로를 컴파일하는 tracing JIT에 가깝다.

역사적으로 적응형 인터프리터는 `tier 1`, JIT는 `tier 2`라고 불렸다. 코드에서 이 명칭의 흔적을 볼 수 있다.

> **해설**
>
> `tier`는 실행 계층을 뜻한다. 프로그램은 먼저 범용적이고 시작 비용이 낮은 계층에서 실행되다가, 충분히 자주 실행된 코드만 더 비싸지만 빠른 최적화 계층으로 올라간다. 현재 문서와 코드에서 `tier 2`가 uop 실행 계층 또는 JIT 경로를 가리키는 이름으로 남아 있을 수 있다.

### 옵티마이저와 실행기

프로그램은 적응형 인터프리터에서 실행되기 시작한다. 그러다가 어떤 `JUMP_BACKWARD` 명령어의 [인라인 캐시](https://github.com/python/cpython/blob/3.14/InternalDocs/interpreter.md#inline-cache-entries)에 든 카운터가 그 명령어가 임계 횟수보다 많이 실행되었음을 나타내면, 해당 명령어는 자신이 “뜨겁다(hot)”고 판단한다. [`backoff_counter_triggers`](https://github.com/python/cpython/blob/3.14/Include/internal/pycore_backoff.h)를 참고하라. 그러면 현재 [프레임](https://github.com/python/cpython/blob/3.14/InternalDocs/frames.md)과 명령어 포인터를 넘겨 [`Python/optimizer.c`](https://github.com/python/cpython/blob/3.14/Python/optimizer.c)의 `_PyOptimizer_Optimize()` 함수를 호출한다. `_PyOptimizer_Optimize()`는 이 점프에서 시작하는 명령어 trace의 최적화된 버전을 구현하는 [`_PyExecutorObject`](https://github.com/python/cpython/blob/3.14/Include/internal/pycore_optimizer.h) 타입 객체를 만든다.

> **해설 — 왜 `JUMP_BACKWARD`가 hot 지점인가**
>
> 뒤로 점프하는 명령어는 대개 반복문의 다음 반복으로 돌아가는 지점이다. 같은 `JUMP_BACKWARD`가 여러 번 실행되었다면 그 주변 경로도 반복 실행되었을 가능성이 높다. 따라서 이 지점의 인라인 캐시 카운터를 hotness 측정기로 사용하면 별도의 전역 프로파일러 없이 최적화할 후보를 찾을 수 있다.
>
> “임계 횟수”를 두는 이유는 한두 번만 실행되는 코드에 최적화 비용을 쓰지 않기 위해서다. `_PyExecutorObject`는 이 hot 지점에서 시작하는 최적화 경로와 그 실행에 필요한 정보를 담는 객체다.

옵티마이저는 trace가 끝나는 위치를 결정한다. 실행기(executor)는 적응형 인터프리터로 돌아가 실행을 재개하거나, 다른 실행기로 제어를 넘기도록 구성된다. `Include/internal/pycore_optimizer.h`의 `_PyExitData`를 참고하라.

> **해설 — trace에는 출구가 필요하다**
>
> trace는 프로그램 전체가 아니라 실제로 자주 관찰된 한 실행 경로다. 조건이 예상과 다르거나 trace의 끝에 도달하면 원래 인터프리터로 복귀해야 한다. 연결할 수 있는 다른 최적화 trace가 있다면 그 실행기로 곧바로 넘어갈 수도 있다. `_PyExitData`는 이런 출구에서 어디로, 어떤 상태로 이동할지 표현하는 내부 데이터다.

실행기는 프레임의 [`코드 객체`](https://github.com/python/cpython/blob/3.14/InternalDocs/code_objects.md)에 저장된다. 코드 객체의 `co_executors` 필드는 실행기 배열이다. trace의 시작 명령어인 `JUMP_BACKWARD`는 `ENTER_EXECUTOR` 명령어로 교체되며, 이 명령어의 `oparg`는 `co_executors` 안에서 해당 실행기가 있는 인덱스와 같다.

> **해설 — 바이트코드에서 실행기로 들어가는 연결**
>
> 처음에는 `JUMP_BACKWARD`가 반복문의 원래 바이트코드 경로를 실행한다. 최적화가 준비되면 그 자리를 `ENTER_EXECUTOR n`으로 바꾸고, `n`으로 코드 객체의 실행기 배열을 조회한다.
>
> ```text
> 최적화 전: ... → JUMP_BACKWARD → 바이트코드 반복
> 최적화 후: ... → ENTER_EXECUTOR n → co_executors[n]
> ```
>
> 이 교체 덕분에 다음 반복부터는 hot trace의 최적화 실행기로 바로 진입할 수 있다.

### 마이크로 연산 옵티마이저

마이크로 연산은 `μop`과 비슷하게 보이도록 줄여서 `uop`이라고 쓴다. 마이크로 연산 옵티마이저는 [`Python/optimizer.c`](https://github.com/python/cpython/blob/3.14/Python/optimizer.c)에 `_PyOptimizer_Optimize`로 정의되어 있다. 이 옵티마이저는 각 바이트코드를 동등한 마이크로 연산 시퀀스로 교체하여 명령어 trace를 마이크로 연산 시퀀스로 번역한다. [`Python/bytecodes.c`](https://github.com/python/cpython/blob/3.14/Python/bytecodes.c)에서 생성되는 [`pycore_opcode_metadata.h`](https://github.com/python/cpython/blob/3.14/Include/internal/pycore_opcode_metadata.h)의 `_PyOpcode_macro_expansion`을 참고하라. 그런 다음 [`Python/optimizer_analysis.c`](https://github.com/python/cpython/blob/3.14/Python/optimizer_analysis.c)의 `_Py_uop_analyze_and_optimize`가 마이크로 연산 시퀀스를 최적화하고, 그 시퀀스를 담을 `_PyUOpExecutor_Type` 인스턴스를 만든다.

> **해설 — 바이트코드와 uop의 관계**
>
> Python 바이트코드는 파일에 저장되고 인터프리터가 보는 비교적 큰 명령 단위다. 하나의 바이트코드 구현 내부에는 검사, 캐시 처리, 실제 연산, 오류 분기처럼 더 작은 작업이 들어 있다. uop은 이를 최적화기가 분석하기 쉬운 더 세분화된 내부 연산으로 펼친 것이다.
>
> ```text
> 바이트코드 trace
>     ↓ macro expansion
> uop 시퀀스
>     ↓ 분석·최적화
> 최적화된 uop 시퀀스를 담은 executor
> ```
>
> uop은 사용자가 `.pyc`나 `dis`에서 보는 안정적인 바이트코드 형식이 아니라 CPython 내부 최적화 표현이다.

### JIT 인터프리터

`JUMP_BACKWARD` 명령어가 uop 옵티마이저를 호출하여 uop 실행기를 만든 뒤에는 `GOTO_TIER_TWO` 매크로를 통해 그 실행기로 제어를 넘긴다.

CPython은 실행기 두 종류를 구현한다. 여기서는 둘 중 더 단순하여 uop 생성·최적화 단계를 디버깅하고 분석하는 데 유용한 JIT 인터프리터를 설명한다. JIT가 자신의 인터프리터에서 실행되도록 하려면, 즉 Python을 [`--enable-experimental-jit=interpreter`](https://docs.python.org/dev/using/configure.html#cmdoption-enable-experimental-jit) 옵션으로 구성하면 된다.

> **해설 — “JIT 인터프리터”라는 이름**
>
> 이 모드는 최적화된 uop 시퀀스를 만들지만, 그 시퀀스를 곧바로 네이티브 기계어로 바꾸지는 않는다. 별도의 uop 인터프리터 루프가 uop을 실행한다. 그래서 uop 생성과 최적화가 올바른지 먼저 확인하기 쉽다.
>
> 문서가 말하는 두 실행기는 대략 다음과 같다.
>
> - uop 인터프리터 실행기: 최적화된 uop을 switch 루프로 해석한다.
> - 완전한 JIT 실행기: 같은 uop 논리를 네이티브 코드로 만들어 실행한다.

실행기가 호출되면 [`Python/ceval.c`](https://github.com/python/cpython/blob/3.14/Python/ceval.c)의 `tier2_dispatch:` 레이블로 점프한다. 그곳에는 마이크로 연산을 실행하는 루프가 있다. 이 루프의 본문은 uop ID를 기준으로 분기하는 switch 문이며, 적응형 인터프리터에서 사용하는 switch 문과 유사하다.

uop을 구현하는 switch 문은 [`Python/executor_cases.c.h`](https://github.com/python/cpython/blob/3.14/Python/executor_cases.c.h)에 있다. 이 파일은 빌드 스크립트 [`Tools/cases_generator/tier2_generator.py`](https://github.com/python/cpython/blob/3.14/Tools/cases_generator/tier2_generator.py)가 [`Python/bytecodes.c`](https://github.com/python/cpython/blob/3.14/Python/bytecodes.c)의 바이트코드 정의로부터 생성한다.

> **해설 — 생성 파일의 계보**
>
> uop 실행 switch를 직접 수작업으로 유지하지 않는다.
>
> ```text
> Python/bytecodes.c
>     ↓ Tools/cases_generator/tier2_generator.py
> Python/executor_cases.c.h
>     ↓ ceval.c의 tier2_dispatch 루프에서 포함·실행
> ```
>
> 바이트코드와 uop 정의의 공통 원천을 `Python/bytecodes.c`에 두어 두 구현이 어긋날 위험을 줄인다.

`_EXIT_TRACE` 또는 `_DEOPT` uop에 도달하면 uop 인터프리터를 빠져나오고 실행은 적응형 인터프리터로 돌아간다.

> **해설 — 정상 출구와 탈최적화**
>
> `_EXIT_TRACE`는 trace의 계획된 끝이나 출구에 도달했다는 뜻이다. `_DEOPT`는 최적화할 때 세운 가정이 더 이상 맞지 않아 범용 실행 경로로 돌아가야 한다는 뜻이다. 예를 들어 “이 값은 항상 정수다”라는 가정과 다른 타입을 만나면 특화된 연산을 계속 실행할 수 없다.
>
> 두 경우 모두 Python 프로그램을 중단하는 오류가 아니라, 더 일반적인 적응형 인터프리터로 안전하게 복귀하는 제어 흐름이다.

### 실행기 무효화

각 실행기는 코드 객체에 저장될 뿐 아니라 모든 실행기를 모은 목록에도 삽입된다. 이 목록은 인터프리터 상태의 `executor_list_head` 필드에 저장된다. 실행기를 구성할 때 사용한 값이 변경되었을 수 있어 실행기를 무효화해야 하는 경우, 이 목록을 사용한다.

> **해설 — 최적화 가정의 수명**
>
> 최적화된 코드는 타입, 함수, 전역 값 등 당시 관찰한 상태가 유지된다고 가정할 수 있다. 관련 값이 바뀌면 그 가정에 의존하는 실행기를 더 이상 사용해서는 안 된다. 인터프리터가 모든 실행기 목록을 갖고 있으면 영향을 받는 실행기를 찾아 무효로 표시하거나 정리할 수 있다.

### JIT

완전한 JIT가 활성화되어 있으면, 즉 Python이 [`--enable-experimental-jit`](https://docs.python.org/dev/using/configure.html#cmdoption-enable-experimental-jit) 옵션으로 구성되어 있으면, uop 실행기의 `jit_code` 필드에는 실행기 로직을 구현하는 컴파일된 C 함수의 포인터가 들어간다. 이 함수의 시그니처는 [`pycore_jit.h`](https://github.com/python/cpython/blob/3.14/Include/internal/pycore_jit.h)의 `jit_func`로 정의된다. `ENTER_EXECUTOR`가 실행기를 호출하면 실행기는 `tier2_dispatch`의 uop 인터프리터로 점프하는 대신 `jit_code`가 가리키는 함수를 실행한다. 이 함수는 다음에 실행해야 하는 Tier 1 명령어의 명령어 포인터를 반환한다.

> **해설 — 같은 executor의 두 실행 방식**
>
> 앞 절의 인터프리터 모드에서는 executor 안의 uop 시퀀스를 공통 switch 루프로 보낸다. 완전한 JIT에서는 executor에 대응하는 네이티브 함수 주소를 `jit_code`에 넣고 그 함수를 직접 호출한다. JIT 코드가 trace 실행을 마치면 적응형 인터프리터가 이어서 실행할 바이트코드 위치를 반환한다.
>
> 원문에는 `--enable-experimental-jit` 링크 뒤의 닫는 괄호 `)`가 하나 빠져 있다. 위 번역에서는 문장 의도에 맞게 괄호를 닫았다.

JIT 함수 생성에는 [Haoran Xu의 글](https://sillycross.github.io/2023/05/12/2023-05-12/)에서 설명한 copy-and-patch 기법을 사용한다. 이 기법의 핵심은 마이크로 연산 구현을 위해 정적으로 생성한 `stencil`이다. [`_PyJIT_Compile`](https://github.com/python/cpython/blob/3.14/Python/jit.c)이 실행기의 JIT 코드를 구성할 때 이 stencil을 런타임 정보로 완성한다.

> **해설 — copy-and-patch와 stencil**
>
> 일반적인 JIT는 런타임에 기계어 명령을 하나씩 선택하고 인코딩할 수 있다. copy-and-patch는 자주 필요한 기계어 조각을 빌드할 때 미리 컴파일해 stencil로 보관한다. 런타임에는 필요한 조각을 복사하고, 비워 둔 자리만 실제 상수·주소·분기 대상으로 패치한다.
>
> ```text
> 빌드 시:
> uop 구현 C 코드 → LLVM → [미리 컴파일된 기계어 stencil + 패치 위치]
>
> 런타임:
> stencil 복사 → 현재 executor의 값과 주소 패치 → 실행 가능한 JIT 함수
> ```
>
> 따라서 런타임 컴파일러가 완전한 C/LLVM 컴파일 파이프라인을 다시 실행하지 않아도 되므로 JIT 코드 생성 지연을 낮출 수 있다.

stencil은 빌드 시점에 Makefile의 `regen-jit` 대상과 [`/Tools/jit`](https://github.com/python/cpython/tree/3.14/Tools/jit)의 스크립트를 통해 생성된다. 이 생성 스크립트는 [`Python/bytecodes.c`](https://github.com/python/cpython/blob/3.14/Python/bytecodes.c)에서 생성된 [`Python/executor_cases.c.h`](https://github.com/python/cpython/blob/3.14/Python/executor_cases.c.h)를 읽는다. 각 opcode에 대해 해당 opcode를 구현하는 함수를 포함하고 일부 런타임 정보가 주입된 `.c` 파일을 만든다. 이 작업은 템플릿 파일 [`Tools/jit/template.c`](https://github.com/python/cpython/blob/3.14/Tools/jit/template.c)의 `CASE`를 바이트코드 정의로 교체하는 방식으로 수행한다.

> **해설 — 빌드 시 생성 단계**
>
> `executor_cases.c.h`에는 각 uop 실행 케이스가 C 코드로 생성되어 있다. JIT 생성 스크립트는 템플릿의 `CASE` 자리에 각 케이스 구현을 넣어, 개별 연산을 함수처럼 컴파일할 수 있는 임시 `.c` 단위를 만든다. “런타임 정보가 주입된다”는 말은 나중에 executor별 실제 값을 채울 자리를 코드 조각에 마련한다는 뜻이다.
>
> 원문의 링크 대상 `/Tools/jit`는 저장소 루트가 아닌 웹 사이트 루트로 해석될 수 있다. 위 링크는 의도한 CPython 3.14의 `Tools/jit` 디렉터리를 가리키도록 절대 URL로 정리했다.

각 `.c` 파일은 LLVM으로 컴파일되어 해당 opcode를 실행하는 함수를 담은 오브젝트 파일을 만든다. 이렇게 컴파일된 함수들을 사용해 [`jit_stencils.h`](https://github.com/python/cpython/blob/3.14/jit_stencils.h) 파일을 생성한다. 이 파일에는 JIT가 각 바이트코드의 코드를 방출할 때 사용할 수 있는 함수들이 들어 있다.

> **해설 — 오브젝트 파일에서 헤더로**
>
> LLVM이 만든 오브젝트 파일에는 완성된 실행 파일만 있는 것이 아니라 기계어 바이트, 심볼, 재배치 정보가 들어 있다. 생성 스크립트는 여기서 stencil 바이트와 패치해야 할 위치를 추출해 `jit_stencils.h`의 정적 데이터로 만든다. 런타임 JIT는 이 데이터를 복사하고 패치하여 코드를 방출한다.
>
> `jit_stencils.h`는 빌드 과정에서 생성되는 파일이라 CPython Git
> 저장소에 완성본이 들어 있지 않다. 따라서 원문의 상대 링크를
> GitHub에서 열면 파일을 찾지 못할 수 있다.

Python 유지보수자에게 이는 바이트코드와 그 구현을 변경해도 stencil과 관련된 변경을 따로 할 필요가 없다는 뜻이다. 모든 것이 빌드 시점에 [`Python/bytecodes.c`](https://github.com/python/cpython/blob/3.14/Python/bytecodes.c)에서 자동 생성되기 때문이다.

> **해설**
>
> 관리해야 할 단일 원천은 `Python/bytecodes.c`다. 관련 생성 명령을 실행하면 uop 실행 코드와 JIT stencil이 같은 정의에서 다시 만들어지므로, 별도의 손수 작성한 stencil 구현을 동기화할 필요가 없다.

함께 보기:

- [Copy-and-Patch Compilation: 고수준 언어와 바이트코드를 위한 빠른 컴파일 알고리즘](https://arxiv.org/abs/2011.13127)

- [PyCon 2024: CPython용 JIT 컴파일러 만들기](https://www.youtube.com/watch?v=kMO3Ju0QCDo)

---

## 제3부: 가비지 컬렉터 설계

> 원문: [CPython 3.14 `InternalDocs/garbage_collector.md`](https://github.com/python/cpython/blob/3.14/InternalDocs/garbage_collector.md)

### 개요

CPython이 사용하는 주된 가비지 컬렉션 알고리즘은 **참조 횟수 관리(reference counting)**이다. 기본 아이디어는 어떤 객체를 참조하는 장소가 서로 몇 군데인지 CPython이 세는 것이다. 이러한 장소는 다른 객체일 수도 있고, 전역 또는 정적 C 변수일 수도 있으며, 어떤 C 함수의 지역 변수일 수도 있다. 객체의 참조 횟수가 0이 되면 그 객체를 해제한다. 객체가 다른 객체를 참조하고 있었다면 그 객체들의 참조 횟수도 감소한다. 이 감소로 다른 객체의 참조 횟수까지 0이 되면 그 객체도 이어서 해제하며, 이 과정이 계속될 수 있다.

참조 횟수 필드는 `sys.getrefcount()` 함수로 살펴볼 수 있다. 이 함수를 호출하는 순간 함수 자체도 객체에 대한 참조 하나를 가지므로, 반환값은 항상 관찰하려는 참조 횟수보다 1 크다는 점에 유의해야 한다.

```pycon
>>> x = object()
>>> sys.getrefcount(x)
2
>>> y = x
>>> sys.getrefcount(x)
3
>>> del y
>>> sys.getrefcount(x)
2
```

> **해설 — 참조 횟수 관리와 예제의 전제**
>
> nand2tetris에서 메모리 블록을 명시적으로 해제했다면, CPython은 “이 객체로 들어오는 참조가 몇 개인가”를 객체마다 기록해 수명을 판단한다. 위 코드는 `sys`가 이미 import되어 있다고 가정한다. 새 세션에서는 먼저 `import sys`가 필요하다. 또한 불멸 객체처럼 특수한 내부 정책을 쓰는 객체에서는 `getrefcount()` 값을 일반 객체와 똑같이 해석하면 안 된다.
>
> 원문의 “항상 1 크다”는 위와 같은 일반 객체의 단순한 예를 설명한
> 표현이다. [공식 `sys.getrefcount()` 문서](https://docs.python.org/3.14/library/sys.html#sys.getrefcount)는
> 임시 인자 참조 때문에 **대체로** 예상보다 1 크다고 설명하며,
> 불멸 객체를 비롯한 내부 참조 관리 방식 때문에 반환값이 실제 참조
> 수를 정확히 나타내지 않을 수 있다고 경고한다. 따라서 `0`이나
> `1`인지 확인하는 경우 외에는 이 값을 정확한 참조 수로 간주하면 안
> 된다.

참조 횟수 관리 방식의 주된 문제는 **참조 순환(reference cycle)**을 처리하지 못한다는 점이다. 다음 코드를 보자.

```pycon
>>> container = []
>>> container.append(container)
>>> sys.getrefcount(container)
3
>>> del container
```

이 예에서 `container`는 자기 자신을 참조한다. 따라서 우리가 가진 참조, 즉 `container` 변수를 제거해도 객체 내부의 자기 참조가 남아 있어 참조 횟수가 0으로 떨어지지 않는다. 단순한 참조 횟수 관리만으로는 이 객체를 영원히 정리할 수 없다. 그러므로 객체들이 외부에서 도달할 수 없는 상태가 된 뒤, 객체 사이의 참조 순환을 찾아 정리할 추가 장치가 필요하다. 이것이 **순환 가비지 컬렉터(cyclic garbage collector)**다. 참조 횟수 관리도 가비지 컬렉션의 한 형태이지만, 보통 CPython에서 “가비지 컬렉터” 또는 “GC”라고 하면 이 순환 가비지 컬렉터를 가리킨다.

> **해설 — 참조 횟수와 도달 가능성은 다르다**
>
> 참조 횟수 관리는 각 객체로 들어오는 화살표 수만 본다. 순환 안의 객체들은 서로 화살표를 유지하므로 횟수가 0이 되지 않는다. 개념적으로 순환 GC가 판별하려는 것은 프로그램이 실제로 사용할 수 있는 루트에서 그 객체까지 경로가 남아 있는가이다. “참조가 존재한다”와 “프로그램에서 도달할 수 있다”를 구분하는 것이 이 문서의 핵심이다.
>
> 다만 기본 빌드의 실제 순환 탐지는 모든 루트를 직접 열거하지 않는다.
> 후보 집합 내부에서 들어오는 참조를 임시 참조 횟수에서 빼고, 그래도
> 참조가 남은 객체를 외부에서 도달 가능한 시작점으로 삼는다. 뒤에서
> 설명하는 자유 스레딩 빌드의 mark-alive 단계는 살아 있다고 알려진
> 객체에서 실제로 그래프를 순회하는 별도 최적화다.

CPython 3.13부터 GC 구현은 두 종류다.

- 기본 빌드 구현은 스레드 안전성을 위해 [전역 인터프리터 잠금(global interpreter lock, GIL)](https://docs.python.org/3/glossary.html#term-global-interpreter-lock)에 의존한다.
- 자유 스레딩 빌드 구현은 컬렉션을 수행하는 동안 실행 중인 다른 스레드를 일시 중지하여 스레드 안전성을 확보한다.

두 구현은 기본 알고리즘은 같지만 서로 다른 자료 구조 위에서 동작한다. 자세한 내용은 [GC 구현의 차이](#gc-구현의-차이) 절에서 설명한다.

> **해설 — 같은 알고리즘, 다른 동기화 조건**
>
> 기본 빌드에서는 GIL 덕분에 GC가 객체 상태를 조사하는 동안 다른 Python 스레드가 동시에 그 상태를 바꾸지 않는다. 자유 스레딩 빌드에는 이 전제가 없으므로, 안전하게 전체 객체 그래프를 보아야 하는 구간에서 다른 실행 스레드를 멈추는 별도 절차가 필요하다.

### 메모리 배치와 객체 구조

가비지 컬렉터가 동작하려면 Python 객체에 GC를 지원하는 추가 필드가 필요하다. 기본 빌드와 자유 스레딩 빌드는 서로 다른 추가 필드를 사용한다.

#### 기본 빌드의 GC

일반적인 Python 객체를 지원하는 C 구조체는 보통 다음과 같은 모양이다.

```
    object -----> +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ \
                  |                    ob_refcnt                  | |
                  +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ | PyObject_HEAD
                  |                    *ob_type                   | |
                  +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ /
                  |                      ...                      |
```

GC를 지원하기 위해 객체의 메모리 배치를 바꾸고, 정상적인 객체 배치 **앞쪽**에 추가 정보를 넣는다.

```
                  +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ \
                  |                    *_gc_next                  | |
                  +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ | PyGC_Head
                  |                    *_gc_prev                  | |
    object -----> +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ /
                  |                    ob_refcnt                  | \
                  +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ | PyObject_HEAD
                  |                    *ob_type                   | |
                  +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ /
                  |                      ...                      |
```

이렇게 하면 객체는 평범한 Python 객체로 다룰 수 있고, GC와 관련된 추가 정보가 필요할 때에는 원래 객체 포인터를 단순히 형 변환하여 앞쪽 필드에 접근할 수 있다. 이때 사용하는 표현은 `((PyGC_Head *)(the_object)-1)`이다.

> **해설 — 포인터가 객체 본체를 가리키는 이유**
>
> 외부 C API는 계속 `PyObject *`가 `PyObject_HEAD`의 시작을 가리킨다고 생각할 수 있다. GC가 필요할 때만 포인터를 `PyGC_Head *`로 해석하고 한 칸 앞으로 이동해 숨겨진 머리말을 찾는다. 즉 공개되는 객체 주소는 바뀌지 않는 것처럼 보이지만, 실제 할당 블록에는 그 앞에 GC 전용 공간이 붙어 있다.

뒤의 [최적화: 메모리 절약을 위한 필드 재사용](#최적화-메모리-절약을-위한-필드-재사용) 절에서 설명하듯, 이 두 추가 필드는 보통 GC가 추적하는 모든 객체의 이중 연결 리스트를 유지하는 데 사용한다. 이러한 리스트가 GC 세대이며, 자세한 내용은 [최적화: 세대](#최적화-세대) 절에서 다룬다. 다만 완전한 이중 연결 리스트 구조가 필요하지 않은 때에는 메모리를 아끼기 위해 이 필드들을 다른 목적으로도 재사용한다.

이중 연결 리스트를 쓰는 이유는 GC에서 가장 자주 필요한 연산을 효율적으로 지원하기 때문이다. 일반적으로 GC가 추적하는 모든 객체의 집합은 서로 겹치지 않는 여러 부분집합으로 나뉘며, 각 부분집합은 자기 이중 연결 리스트를 가진다. 컬렉션 사이에는 객체가 컬렉션을 몇 번 살아남았는지를 나타내는 “세대”별로 나뉜다. 컬렉션 중에는 수집 대상 세대를 도달 가능한 객체와 도달 불가능한 객체 같은 집합으로 다시 나눈다.

이중 연결 리스트에서는 객체를 한 부분집합에서 다른 부분집합으로 옮기기, 새 객체 추가하기, 객체를 완전히 제거하기, 부분집합 합치기를 모두 적은 수의 포인터 갱신만으로 처리할 수 있다. GC가 추적하는 객체도 실제로는 GC가 전혀 실행 중이지 않을 때 참조 횟수 관리에 의해 회수되는 경우가 가장 많다. 구현에 주의를 기울이면 GC 실행 중 자주 필요한, 객체가 추가되고 제거되는 동시에 한 부분집합을 순회하는 동작도 지원할 수 있다.

> **해설 — 왜 배열이나 집합이 아니라 연결 리스트인가**
>
> 이 알고리즘은 객체를 “젊은 세대”, “도달 가능”, “잠정적으로 도달 불가능” 같은 목록 사이에서 계속 이동한다. 이중 연결 리스트는 현재 노드의 앞뒤 포인터 몇 개만 바꾸면 이동과 병합을 할 수 있다. 객체 수에 비례하는 별도 작업 배열을 만들지 않고, 객체 앞의 `PyGC_Head` 자체를 작업 공간으로 활용한다.

#### 자유 스레딩 빌드의 GC

자유 스레딩 빌드의 Python 객체에는 GC 관련 상태를 추적하는 1바이트 필드 `ob_gc_bits`가 들어 있다. 순환 가비지 컬렉션을 지원하지 않는 객체를 포함하여 모든 객체에 이 필드가 존재한다. 컬렉터가 추적하는 객체인지 식별하고, 객체마다 finalizer가 한 번만 호출되도록 보장하며, 컬렉션 중 도달 가능한 객체와 도달 불가능한 객체를 구분하는 데 이 필드를 사용한다.

```
    object -----> +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ \
                  |                     ob_tid                    | |
                  +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ |
                  | pad | ob_mutex | ob_gc_bits |  ob_ref_local   | |
                  +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ | PyObject_HEAD
                  |                  ob_ref_shared                | |
                  +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ |
                  |                    *ob_type                   | |
                  +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+ /
                  |                      ...                      |
```

그림의 모든 필드가 실제 크기 비율대로 그려진 것은 아니다. `pad`는 2바이트, `ob_mutex`와 `ob_gc_bits`는 각각 1바이트, `ob_ref_local`은 4바이트다. 나머지 `ob_tid`, `ob_ref_shared`, `ob_type`은 모두 포인터 크기이며, 64비트 플랫폼에서는 8바이트다.

가비지 컬렉터는 컬렉션 중에 `ob_tid`(스레드 ID)와 `ob_ref_local`(로컬 참조 횟수) 필드도 일시적으로 다른 목적으로 재사용한다.

> **해설 — 자유 스레딩 객체의 참조 횟수**
>
> 여러 스레드가 같은 참조 횟수를 계속 원자적으로 갱신하면 비용이 커진다. 자유 스레딩 객체는 소유 스레드 쪽의 로컬 참조 횟수와 공유 참조 상태를 나누어 관리하며, `ob_tid`는 소유 스레드를 식별한다. GC는 모든 실행 스레드를 멈춘 구간에서 이 필드들이 안정적이라는 점을 이용해 임시 작업 공간으로도 쓴다.

#### C API

GC를 지원하는 객체를 할당·해제·초기화·추적·추적 해제하기 위한 전용 API가 제공된다. 해당 API는 [Garbage Collector C API 문서](https://docs.python.org/3/c-api/gcsupport.html)에서 확인할 수 있다.

객체 구조 외에도, 가비지 컬렉션을 지원하는 객체의 타입 객체는 `tp_flags` 슬롯에 `Py_TPFLAGS_HAVE_GC`를 포함하고 `tp_traverse` 핸들러를 구현해야 한다. 같은 타입의 객체들만으로 참조 순환을 만들 수 없다는 점을 증명할 수 있거나 타입이 불변인 경우가 아니라면, `tp_clear`도 구현해야 한다.

> **해설 — `tp_traverse`와 `tp_clear`**
>
> `tp_traverse`는 컨테이너가 내부에서 어떤 Python 객체를 참조하는지 GC에 열거해 준다. GC는 객체의 C 구조체 배치를 타입마다 알 수 없으므로 이 콜백이 필요하다. `tp_clear`는 내부 참조를 끊어 순환을 깨는 콜백이다. 둘을 빠뜨리면 객체가 GC 목록에 있어도 그래프의 간선이 보이지 않거나, 순환을 찾아 놓고도 실제 참조 횟수를 0으로 내릴 수 없다.

### 참조 순환 식별

CPython이 참조 순환을 찾는 알고리즘은 `gc` 모듈에 구현되어 있다. 가비지 컬렉터는 **컨테이너 객체**, 즉 하나 이상의 객체에 대한 참조를 담을 수 있는 객체만 정리 대상으로 삼는다. 배열, 딕셔너리, 리스트, 사용자 정의 클래스 인스턴스, 확장 모듈의 클래스 등이 이에 해당한다.

참조 순환이 드물다고 생각할 수도 있지만, 인터프리터에 필요한 내부 참조는 곳곳에서 순환을 만든다. 대표적인 예는 다음과 같다.

- 예외는 traceback 객체를 포함하고, traceback은 프레임 목록을 포함하며, 그 프레임이 다시 예외 자체를 포함한다.
- 모듈 수준 함수는 전역 이름을 찾는 데 필요한 모듈의 딕셔너리를 참조하고, 그 딕셔너리는 다시 모듈 수준 함수를 항목으로 가진다.
- 인스턴스는 자기 클래스를 참조하고, 클래스는 자기 모듈을 참조하며, 모듈은 그 안의 모든 것과 다른 모듈까지 참조할 수 있다. 이 경로가 원래 인스턴스로 돌아올 수 있다.
- 그래프 같은 자료 구조를 표현할 때에는 내부 링크가 자기 자신으로 이어지는 경우가 매우 흔하다.

도달할 수 없게 된 객체들을 올바르게 폐기하려면 먼저 이들을 식별해야 한다. 알고리즘을 이해하기 위해, 변수 `A`가 고리 하나를 참조하는 원형 연결 리스트와 완전히 도달 불가능한 자기 참조 객체가 함께 있는 경우를 살펴보자.

```pycon
>>> import gc
>>>
>>> class Link:
...    def __init__(self, next_link=None):
...        self.next_link = next_link
...
>>> link_3 = Link()
>>> link_2 = Link(link_3)
>>> link_1 = Link(link_2)
>>> link_3.next_link = link_1
>>> A = link_1
>>> del link_1, link_2, link_3
>>>
>>> link_4 = Link()
>>> link_4.next_link = link_4
>>> del link_4
>>>
>>> # 도달 불가능한 Link 객체와 그 객체의 .__dict__ 딕셔너리를 수집한다.
>>> gc.collect()
2
```

GC는 검사하려는 후보 객체 집합에서 시작한다. 기본 빌드에서 이 “검사할 객체”는 모든 컨테이너 객체일 수도 있고, 더 작은 부분집합인 한 “세대”일 수도 있다. 자유 스레딩 빌드의 컬렉터는 항상 모든 컨테이너 객체를 검사한다.

목표는 도달 불가능한 객체를 모두 알아내는 것이다. 컬렉터는 도달 가능한 객체를 식별하고, 남은 객체는 도달 불가능하다고 판단하는 방식으로 목표를 달성한다. 첫 단계에서는 후보 객체 집합 **바깥에서 직접** 도달할 수 있는 검사 대상 객체를 모두 찾는다. 이러한 객체는 후보 집합 내부에서 들어오는 참조의 수보다 실제 참조 횟수가 더 크다.

> **해설 — 후보 집합 안쪽 간선을 먼저 제거한다**
>
> 후보 객체마다 실제 참조 횟수에서 “후보들끼리 주고받는 참조”를 빼면, 집합 바깥에서 들어오는 참조만 남는다. 값이 양수인 객체는 외부에서 직접 붙잡고 있는 객체다. 이는 그래프에서 내부 간선을 모두 지운 뒤 외부에서 들어오는 간선의 시작점을 찾는 것과 같다.

가비지 컬렉션을 지원하는 모든 객체는 알고리즘 시작 시점에 그 객체의 실제 참조 횟수로 초기화한 추가 참조 횟수 필드를 갖는다. 그림에서는 이 값을 `gc_ref`라고 표시한다. 계산 과정에서 참조 횟수를 변경해야 하므로, 인터프리터가 사용하는 실제 참조 횟수 필드는 건드리지 않고 복사본을 사용하는 것이다.

> **해설 — `gc_ref`는 계산용 그림자 값이다**
>
> 실제 `ob_refcnt`를 줄였다가 되돌리는 방식은 중간에 객체를 잘못 파괴할 수 있다. 따라서 GC는 기본 빌드에서는 `PyGC_Head` 필드 같은 기존 공간을 재사용하고, 자유 스레딩 빌드에서는 그 구현에 맞는 임시 상태를 사용해 논리적인 참조 횟수 복사본을 만든다.

![gc-image1](https://raw.githubusercontent.com/python/cpython/3.14/InternalDocs/images/python-cyclic-gc-1-new-page.png)

그다음 GC는 첫 번째 리스트의 모든 컨테이너를 순회한다. 컨테이너가 다른 객체를 참조할 때마다 그 대상 객체의 `gc_ref` 필드를 1씩 줄인다. 각 컨테이너가 무엇을 참조하는지는 해당 컨테이너 클래스의 `tp_traverse` 슬롯을 사용해 알아낸다. 이 슬롯은 C API로 구현하거나 상위 클래스에서 상속받을 수 있다. 모든 객체를 검사하고 나면 “검사할 객체” 리스트 바깥에서 참조를 받는 객체만 `gc_ref > 0` 상태로 남는다.

![gc-image2](https://raw.githubusercontent.com/python/cpython/3.14/InternalDocs/images/python-cyclic-gc-2-new-page.png)

`gc_ref == 0`이라고 해서 그 객체가 도달 불가능하다는 뜻은 아니다. 외부에서 도달 가능한 다른 객체(`gc_ref > 0`)가 그 객체를 참조할 수 있기 때문이다. 예제의 `link_2`는 최종적으로 `gc_ref == 0`이지만, 외부에서 도달 가능한 `link_1`이 여전히 이를 참조한다.

정말 도달 불가능한 객체 집합을 구하기 위해 가비지 컬렉터는 `tp_traverse` 슬롯을 사용하여 컨테이너 객체를 다시 검사한다. 이번에는 `gc_ref == 0`인 객체를 “잠정적으로 도달 불가능”하다고 표시하고 잠정적 도달 불가능 리스트로 옮기는 다른 순회 함수를 사용한다. 다음 그림은 GC가 `link_3`과 `link_4`는 처리했지만 `link_1`과 `link_2`는 아직 처리하지 않은 순간의 리스트 상태를 보여 준다.

![gc-image3](https://raw.githubusercontent.com/python/cpython/3.14/InternalDocs/images/python-cyclic-gc-3-new-page.png)

다음으로 GC는 `link_1`을 검사한다. 이 객체는 `gc_ref == 1`이므로 특별한 작업을 하지 않는다. 도달 가능하다는 사실을 이미 알며, 앞으로 도달 가능 리스트가 될 원래 리스트에도 이미 들어 있기 때문이다.

![gc-image4](https://raw.githubusercontent.com/python/cpython/3.14/InternalDocs/images/python-cyclic-gc-4-new-page.png)

GC가 도달 가능한 객체(`gc_ref > 0`)를 만나면 그 객체의 참조를 `tp_traverse` 슬롯으로 순회한다. 여기에서 도달할 수 있는 모든 객체를 찾아 원래 시작 위치이자 도달 가능 객체 리스트가 될 리스트의 끝으로 옮기고, 각 객체의 `gc_ref` 필드를 1로 설정한다.

아래에서는 `link_1`에서 도달할 수 있는 `link_2`와 `link_3`에 이 과정이 일어난다. 이전 그림의 상태에서 `link_1`이 참조하는 객체들을 검사하고 나면, GC는 `link_3`도 결국 도달 가능하다는 사실을 알게 된다. 따라서 `link_3`을 원래 리스트로 되돌리고 `gc_ref`를 1로 설정한다. 나중에 다시 방문하더라도 도달 가능한 객체임을 알 수 있게 하기 위해서다.

같은 객체를 두 번 처리하지 않도록 GC는 한 번 방문한 모든 객체에서 `PREV_MASK_COLLECTING` 플래그를 해제하여 방문 완료를 표시한다. 그러면 이미 처리한 객체를 다른 객체가 참조하더라도 다시 처리하지 않는다.

![gc-image5](https://raw.githubusercontent.com/python/cpython/3.14/InternalDocs/images/python-cyclic-gc-5-new-page.png)

“잠정적으로 도달 불가능”하다고 표시되었다가 나중에 도달 가능 리스트로 돌아간 객체는 GC가 다시 방문한다. 이제 그 객체가 가진 모든 참조도 처리해야 하기 때문이다. 이 과정은 실제로 객체 그래프에 대한 **너비 우선 탐색(breadth-first search)**이다. 모든 객체를 검사하고 나면 잠정적 도달 불가능 리스트의 모든 컨테이너 객체는 정말로 도달 불가능하다는 사실을 알 수 있고, 이들을 가비지 컬렉션할 수 있다.

> **해설 — 0인 객체를 바로 버리지 않고 도달 가능성을 전파하는 이유**
>
> `gc_ref > 0`인 객체들은 외부에서 직접 도달 가능한 탐색 시작점이다. 이 시작점에서 간선을 따라가면 직접 외부 참조는 없어도 간접적으로 살아 있는 객체를 찾을 수 있다. 따라서 첫 계산은 후보를 좁힐 뿐이고, 이어지는 그래프 탐색이 최종 생존 집합을 정한다.

실용적인 관점에서 이 모든 과정에는 재귀가 필요하지 않으며, 객체 수·포인터 수·포인터 사슬 길이에 비례하는 추가 메모리도 필요하지 않다는 점이 중요하다. 내부 C 처리에 필요한 `O(1)` 저장 공간을 제외하면, GC 알고리즘이 요구하는 저장 공간은 객체 자체에 들어 있다.

> **해설 — 재귀 없는 그래프 탐색**
>
> 일반적인 BFS는 별도 큐가 필요하지만, 이 절에서 설명하는 기본 빌드
> 구현은 GC 헤더의 리스트 포인터와 상태 비트를 재사용해 작업 목록과
> 분할 상태를 표현한다. 그래서 객체 그래프가 깊어도 C 호출 스택이
> 넘치지 않고, 객체 수에 비례하는 별도 배열도 만들지 않는다.
> 자유 스레딩 구현은 `PyGC_Head`를 사용하지 않으며, 뒤에서 설명하는
> 객체 헤더 필드와 mark-alive 작업 목록을 이용한다.

#### 도달 불가능한 객체를 옮기는 편이 나은 이유

대부분의 객체가 보통 도달 가능하다는 전제라면 도달 불가능한 객체를 옮기는 것이 논리적으로 들린다. 하지만 조금 더 생각해 보면 이 방식이 왜 이득인지는 실제로 자명하지 않다.

객체 A, B, C를 이 순서로 만들었다고 하자. 젊은 세대에도 같은 순서로 들어간다. B는 A를 가리키고, C는 B를 가리키며, C는 외부에서 도달 가능하다고 하자. 알고리즘 첫 단계를 실행해 참조 횟수를 조정하면 A, B, C의 값은 각각 0, 0, 1이 된다. 외부에서 직접 참조되는 객체는 C뿐이기 때문이다.

다음 단계에서 A를 만나면 A를 도달 불가능 리스트로 옮긴다. B를 처음 만났을 때도 똑같이 처리한다. 그 뒤 C를 순회하면 B를 도달 가능 리스트로 *되돌린다*. 나중에 B를 순회하면 A도 도달 가능 리스트로 돌아간다.

결국 아무것도 옮기지 않는 대신, 도달 가능한 B와 A를 각각 두 번씩 옮긴 셈이다. 그런데 왜 이것이 이득일까? 반대로 도달 가능한 객체를 옮기는 단순한 알고리즘은 A, B, C를 각각 한 번씩 옮기면 된다.

핵심은 앞의 이동 과정이 객체 순서를 C, B, A로 만든다는 점이다. 원래 순서의 역순이다. 이후의 *모든* 검사에서는 이 객체들이 하나도 이동하지 않는다. 대부분의 객체는 순환에 들어 있지 않으므로, 뒤따르는 컬렉션이 아무리 많아져도 이동 횟수를 계속 절약할 수 있다. 비용이 더 높을 수 있는 때는 이 참조 사슬을 처음 검사할 때뿐이다.

> **해설 — 한 번의 추가 비용으로 다음 컬렉션을 정렬한다**
>
> 외부에서 살아 있는 쪽 C부터 참조 방향을 따라 B, A 순서로 배치되면 다음 검사에서는 먼저 생존 루트를 만나고 그 뒤의 객체들을 곧바로 생존으로 확인한다. 첫 검사에서 두 번 이동하는 비용을 내지만, 이후에는 같은 사슬을 반복해서 옮기지 않는다.

### 도달 불가능한 객체 파괴

GC가 도달 불가능한 객체 리스트를 알아내고 나면, 이 객체들을 완전히 파괴하기 위한 매우 섬세한 과정이 시작된다. 대략 다음 단계를 순서대로 수행한다.

1. 약한 참조가 있다면 이를 처리하고 지운다. 도달 불가능한 객체를 가리키는 약한 참조는 `None`으로 설정한다. 약한 참조에 콜백이 연결되어 있으면, 모든 약한 참조를 지운 뒤 호출하도록 콜백을 큐에 넣는다. 약한 참조 객체 자체가 도달 가능한 경우에만 콜백을 호출한다. 약한 참조와 그 대상 객체가 모두 도달 불가능하면 콜백을 실행하지 않는다. 이는 일부는 역사적인 이유 때문이다. 콜백이 도달 불가능한 객체를 부활시킬 수 있는데, 약한 참조 지원이 객체 부활 지원보다 먼저 생겼다. 객체와 약한 참조가 모두 사라질 예정이므로 약한 참조가 먼저 사라졌다고 보는 것은 타당하며, 그 콜백을 무시해도 된다.
2. 객체가 이전 방식의 finalizer인 `tp_del` 슬롯을 가지면 그 객체를 `gc.garbage` 리스트로 옮긴다.
3. finalizer인 `tp_finalize` 슬롯을 호출한다. 객체가 부활했거나 다른 finalizer가 먼저 객체를 제거했더라도 finalizer를 두 번 호출하지 않도록, 이미 finalization을 거쳤다고 객체에 표시한다.
4. 부활한 객체를 처리한다. 일부 객체가 부활했다면 순환 탐지 알고리즘을 다시 실행해 여전히 도달 불가능한 새로운 부분집합을 찾고, 그 객체들에 대해 작업을 계속한다.
5. 모든 객체의 `tp_clear` 슬롯을 호출한다. 내부 연결을 모두 끊으면 참조 횟수가 0으로 떨어지고, 도달 불가능한 객체가 모두 파괴된다.

> **해설 — 파괴 순서가 중요한 이유**
>
> 약한 참조 콜백과 finalizer는 Python 코드를 실행할 수 있고, 그 코드가 죽을 예정이던 객체를 전역 변수 등에 다시 저장해 부활시킬 수 있다. 그래서 GC는 곧바로 모든 참조를 끊지 않는다. 관찰 가능한 콜백을 정해진 순서로 처리하고, 부활 여부를 다시 계산한 뒤, 끝까지 도달 불가능한 객체에만 `tp_clear`를 적용한다.

### 최적화: 세대

각 가비지 컬렉션에 걸리는 시간을 제한하기 위해 기본 빌드의 GC 구현은 널리 쓰이는 **세대(generation)** 최적화를 사용한다.

세대별 가비지 컬렉션은 “대부분의 객체는 젊을 때 죽는다”는 **약한 세대 가설(weak generational hypothesis)**을 활용한다. Python 프로그램은 임시 객체를 많이 만들고 매우 빠르게 파괴하므로, 이 가설은 실제 동작에 매우 가까운 것으로 입증되었다.

이 사실을 이용하기 위해 모든 컨테이너 객체를 세 개의 공간, 즉 세대로 나눈다. 새 객체는 모두 첫 세대인 0세대에서 시작한다. 앞서 설명한 알고리즘은 특정 세대의 객체에 대해서만 실행한다. 객체가 자기 세대의 컬렉션을 살아남으면 다음 세대인 1세대로 이동하며, 그곳에서는 컬렉션 검사 빈도가 더 낮다. 같은 객체가 1세대에서도 한 번 더 GC를 살아남으면 마지막 세대인 2세대로 이동하고, 이 세대에서는 가장 드물게 검사한다.

> **참고**
>
> 자유 스레딩 빌드의 GC 구현은 세대별 컬렉션을 사용하지 않는다. 모든 컬렉션이 전체 힙을 대상으로 동작한다.

> **해설 — Python 3.14 안에서도 세대 수가 달랐다**
>
> 이 3.14 브랜치의 현재 문서는 Python 3.14.5 이후 기본 빌드를
> 설명한다. 3.14.0부터 3.14.4까지는 젊은 세대와 오래된 세대만 둔
> 점진적 GC가 들어 있었지만, 실제 운영 환경에서 메모리 압박 문제가
> 보고되어 3.14.5에서 3.13의 세 세대 방식으로 되돌아갔다. 따라서
> 초기 3.14 자료와 이 절의 설명이 다를 수 있다. 자세한 변경 이력은
> [Python 3.14의 Garbage collection 절](https://docs.python.org/3.14/whatsnew/3.14.html#garbage-collection)에서
> 확인할 수 있다.

> **해설 — 왜 젊은 객체를 더 자주 검사하는가**
>
> 함수 안에서 잠깐 만드는 리스트나 튜플처럼 짧게 사는 객체가 많다면, 새 객체가 모인 작은 영역만 자주 검사하는 편이 전체 힙을 매번 훑는 것보다 싸다. 여러 번 살아남은 객체는 앞으로도 오래 살 가능성이 높다고 보고 검사 빈도를 낮춘다.

컬렉터는 실행 시점을 정하기 위해 마지막 컬렉션 이후 객체 할당 횟수와 해제 횟수를 추적한다. 할당 횟수에서 해제 횟수를 뺀 값이 `threshold0`을 넘으면 컬렉션을 시작한다. 처음에는 0세대만 검사한다. 1세대를 마지막으로 검사한 뒤 0세대를 검사한 횟수가 `threshold_1`보다 많아지면 1세대도 함께 검사한다. 2세대는 조금 더 복잡하며, 자세한 내용은 [가장 오래된 세대 수집](#가장-오래된-세대-수집) 절에서 설명한다.

> **해설 — 임계값은 살아 있는 객체 수가 아니다**
>
> 이 카운터는 전체 객체 개수를 직접 뜻하지 않는다. 컬렉션 뒤에 얼마나 많은 할당 활동이 순증했는지를 근사해 “다시 검사할 만큼 변화가 쌓였는가”를 판단한다. 원문은 같은 문단에서 `threshold0`과 `threshold_1`처럼 서로 다른 표기 방식을 사용하지만, 아래 공개 API에서는 세 임계값을 순서대로 반환한다.

이 임계값은 [`gc.get_threshold()`](https://docs.python.org/3/library/gc.html#gc.get_threshold) 함수로 확인할 수 있다.

```pycon
>>> import gc
>>> gc.get_threshold()
(2000, 10, 10)
```

각 세대의 내용은 `gc.get_objects(generation=NUM)` 함수로 살펴볼 수 있고, `gc.collect(generation=NUM)`을 호출하면 특정 세대의 컬렉션을 실행할 수 있다.

```pycon
>>> import gc
>>> class MyObj:
...     pass
...
>>> # 더 젊은 세대를 쉽게 살펴볼 수 있도록 모든 객체를
>>> # 가장 오래된 세대로 옮긴다.
>>> gc.collect()
0
>>> # 참조 순환을 만든다.
>>> x = MyObj()
>>> x.self = x
>>>
>>> # 처음에는 객체가 가장 젊은 세대에 있다.
>>> gc.get_objects(generation=0)
[..., <__main__.MyObj object at 0x7fbcc12a3400>, ...]
>>>
>>> # 가장 젊은 세대를 수집하면 객체가
>>> # 다음 세대로 이동한다.
>>> gc.collect(generation=0)
0
>>> gc.get_objects(generation=0)
[]
>>> gc.get_objects(generation=1)
[..., <__main__.MyObj object at 0x7fbcc12a3400>, ...]
```

#### 가장 오래된 세대 수집

여러 설정 가능한 임계값 외에도, GC는 `long_lived_pending / long_lived_total` 비율이 정해진 값보다 클 때에만 가장 오래된 세대를 완전히 수집한다. 이 값은 25%로 고정되어 있다.

완전 컬렉션이 아닌 젊은 세대와 중간 세대 컬렉션은 앞서 말한 임계값에 따라 대략 비슷한 수의 객체를 검사한다. 반면 완전 컬렉션의 비용은 사실상 상한이 없는 장수 객체의 총수에 비례한다. 실제로 객체를 일정한 개수만큼 생성할 때마다 완전 컬렉션을 수행하면, 장수 객체를 대량으로 만들고 저장하는 워크로드의 성능이 극적으로 떨어지는 것으로 알려져 있다. 예를 들어 GC가 추적하는 객체의 큰 리스트를 만들면 예상하는 선형 성능이 아니라 이차 성능을 보일 수 있다.

앞의 비율을 사용하면 전체 객체 수에 대해 분할 상환된 선형 성능을 얻을 수 있다. 효과를 요약하면 “객체 수가 늘수록 한 번의 완전 가비지 컬렉션은 점점 비싸지지만, 완전 컬렉션을 점점 덜 실행한다”는 것이다.

> **해설 — `long_lived_pending / long_lived_total`**
>
> 오래된 세대에 새로 합류해 아직 완전 검사 비용에 반영되지 않은 객체의 비율이 충분히 커졌을 때만 전체를 훑는다. 매번 비싼 작업을 하는 대신, 그 작업을 정당화할 만큼 변화가 누적될 때까지 기다려 총비용을 선형에 가깝게 분산한다.

### 최적화: 도달 가능한 객체 제외

도달할 수 있는 객체는 가비지가 될 수 없다. 자유 스레딩 빌드는 전체 힙에서 참조 순환을 식별해야 하는 부담을 줄이기 위해, 먼저 살아 있다고 확실히 아는 객체에서 도달 가능한 객체를 찾는다. 이 객체들은 일반적인 순환 탐지 과정에서 제외한다.

#### 자유 스레딩 GC에서 도달 가능한 객체 찾기

`gc_free_threading.c` 구현에서는 이 과정을 “mark alive” 패스 또는 단계라고 부른다. 자유 스레딩 GC는 `ob_gc_bits`의 한 플래그를 사용하여 어떤 객체가 확실히 살아 있는지, 즉 가비지가 아닌지 기록한다.

살아 있다고 알려진 객체, 즉 “루트”에서 도달 가능한 객체를 찾을 때 `gc_mark_alive_from_roots()` 함수를 사용한다. 루트 객체에는 `interp->sysdict`(`sys` 모듈 딕셔너리), `interp->builtins`, `interp->types`가 포함된다. 실행 중인 Python 프레임이 참조하는 모든 객체도 루트에 포함된다. 이 객체들과 여기에서 도달 가능한 객체의 전이적 폐쇄 전체에는 `_PyGC_BITS_ALIVE`를 설정한다. 이 비트가 설정된 객체는 도달 불가능할 수 없다는 사실을 알고 있으므로, 나머지 순환 가비지 탐지 과정에서 제외한다.

> **해설 — 루트와 전이적 폐쇄**
>
> 루트는 인터프리터가 현재 직접 사용 중이라고 확실히 아는 출발점이다. 전이적 폐쇄는 루트가 직접 가리키는 객체뿐 아니라, 그 객체가 가리키는 객체를 계속 따라가 도달할 수 있는 모든 객체의 집합이다. 그래프 탐색으로 이 집합을 먼저 표시하면 순환 여부를 계산할 후보가 줄어든다.

> **참고**
>
> `gc.freeze()` 함수를 사용했다면 컬렉터는 이 단계를 건너뛴다. 이유는 두 가지다. 첫째, 대부분의 객체가 동결되었다면 이 작업이 성능상 이득일 가능성이 낮다. 동결 객체는 이 추가 작업을 하지 않아도 순환 가비지 탐지에서 제외되기 때문이다. 둘째, `gc.freeze()`를 사용하는 목적 중 하나는 동결 객체가 들어 있는 메모리 페이지를 변경하지 않는 것이다. 이 단계를 실행해 `ob_gc_bits` 플래그를 켰다 끄면 페이지가 변경된 것으로 표시되어 그 목적을 무너뜨린다.

> **해설 — 메모리 페이지를 “더럽힌다”는 뜻**
>
> 운영체제의 copy-on-write 메모리에서는 읽기만 한 페이지를 여러 프로세스가 공유할 수 있지만, 비트 하나라도 쓰면 해당 페이지의 사본이 필요해질 수 있다. `gc.freeze()`는 장수 객체 페이지를 건드리지 않아 `fork()` 뒤의 메모리 공유를 유지하려는 용도로도 사용된다.

#### 소프트웨어 prefetch 힌트

자유 스레딩 GC의 “mark alive” 단계를 빠르게 하기 위해 **소프트웨어 prefetching**이라는 추가 최적화를 사용한다. GC는 메인 메모리에서 데이터를 불러오는 지연 시간을 줄이려고 명시적인 CPU prefetch 명령을 실행한다. 메인 메모리는 CPU 캐시의 데이터에 접근하는 것보다 훨씬 느리므로, 추가된 복잡성이 그만한 가치를 낼 수 있다. 이 기능은 장수 객체 수가 임계값을 넘을 때에만 활성화된다. 가비지 컬렉션 대상 객체 집합이 작으면 접근하는 메모리 전체가 CPU 캐시에 들어갈 가능성이 높고, 이때 소프트웨어 prefetch는 도움이 되지 않는다.

이 최적화의 세부 내용은 복잡하므로 소스 코드가 가장 좋은 참고 자료다. 다만 이 절의 나머지에서는 높은 수준에서 동작 방식을 설명하고 일부 설계 결정을 해설한다.

소프트웨어 prefetching은 GC의 “mark alive” 단계에서만 사용한다. 구체적으로는 객체의 “alive” 상태에 대한 전이적 폐쇄, 즉 살아 있다고 알려진 루트에서 도달 가능한 객체들을 계산할 때 사용한다. 객체 하나를 찾을 때마다 그 객체에서 직접 도달 가능한 모든 객체를 순회해야 한다. 참조 대상 객체들이 메모리 곳곳에 흩어져 있으면 하드웨어 prefetcher가 다음에 접근할 메모리 위치를 예측하기 어렵다.

> **해설 — 하드웨어 prefetch와 소프트웨어 prefetch**
>
> CPU는 연속 주소를 읽는 패턴 등을 자동으로 감지해 다음 데이터를 미리 가져오지만, 포인터 그래프는 다음 주소가 현재 객체 안의 포인터 값에 달려 있어 예측하기 어렵다. 소프트웨어 prefetch는 GC가 앞으로 방문할 포인터를 알고 있다는 점을 이용해 CPU에 미리 요청을 보낸다.

소프트웨어 prefetch를 잘 동작하게 하는 핵심 원칙은 특정 메모리 위치에 대한 prefetch 명령을 내린 시점과 실제로 그 위치의 데이터에 접근하는 시점 사이에 충분한 시간을 두는 것이다. 이 시간 차이를 **prefetch window**라고 부를 수 있다.

window가 너무 크면 아직 필요하지 않은 데이터로 CPU 캐시를 채운다. 더 나쁜 경우에는 실제 사용하기 전에 데이터가 캐시에서 밀려날 수 있다. window가 너무 작으면 메모리 시스템이 데이터 적재를 끝낼 시간이 부족해 CPU가 기다려야 한다. window는 뒤에서 설명할 prefetch buffer 매개변수를 이용해 간접적으로 조정한다.

prefetch buffer는 크기가 고정된 FIFO 큐다. 객체 참조를 버퍼에 넣을 때 그 메모리 위치에 대한 소프트웨어 prefetch 명령도 내린다. 객체 참조를 버퍼에서 꺼낼 때에는 메모리가 캐시에 적재될 만큼 충분한 시간이 지났다고 가정하거나 기대한다. 이 메커니즘이 prefetch window를 만든다.

> **해설 — FIFO가 시간 간격을 만드는 방법**
>
> 큐에 넣자마자 사용하지 않고 앞서 들어간 여러 항목을 처리한 뒤 꺼내므로, enqueue와 dequeue 사이의 작업 시간이 메모리 적재를 기다리는 시간이 된다. 별도로 잠들어 기다리는 것이 아니라 다른 객체를 처리하며 지연 시간을 가린다.

“alive” 상태의 전이적 폐쇄를 계산할 때 아직 방문하지 않은 객체 집합은 두 장소 중 하나에 저장한다. 첫 번째는 prefetch buffer이고, 두 번째는 크기 제한이 없는 LIFO 스택이다. `tp_traverse`로 객체 참조를 찾으면 버퍼가 가득 차지 않았을 때에는 버퍼에 넣고, 가득 찼다면 스택에 push한다.

객체 포인터가 가리키는 메모리는 그 참조를 prefetch buffer에서 꺼내기 전까지 접근하지 않도록 특별히 주의해야 한다. 즉 해당 객체가 컨테이너인지(`PyObject_IS_GC()` 검사가 참인지), 객체에 이미 “alive” 플래그가 설정되어 있는지도 미리 검사할 수 없다. 두 검사 모두 객체 메모리에 접근해야 하기 때문이다.

버퍼를 최적 크기로 채워 두기 위한 추가 장치도 있지만, 설명을 단순하게 유지하기 위해 여기서는 생략한다. 자세히 다루지 않는 “span”이라는 구조도 있으며, 이 구조는 스택 사용량을 줄이고 버퍼 크기를 더 쉽게 제어하도록 돕는다.

> **해설 — prefetch 뒤에 곧바로 객체를 검사하면 안 되는 이유**
>
> prefetch는 데이터가 즉시 도착한다는 보장이 아니라 비동기적인 힌트다. `PyObject_IS_GC()`처럼 객체 헤더를 읽는 순간 실제 메모리 접근이 발생한다. 버퍼에서 충분히 기다리기 전에 이 검사를 하면 prefetch window가 사라져 최적화의 목적을 잃는다.

앞서 말했듯 prefetch window는 버퍼에 넣으며 prefetch 명령을 낸 시점과 버퍼에서 꺼낸 뒤 메모리에 접근하는 시점 사이의 지연 시간이다. 몇 가지 버퍼 매개변수를 조정해 이를 튜닝한다. 모든 객체의 처리 시간이 같다면 버퍼 길이는 window에 비례할 것이다. 실제로 객체마다 처리 시간이 다르므로 버퍼 길이와 prefetch window의 관계는 근사치일 뿐이다. 하지만 구현은 이 비례 관계가 성립한다고 가정하여 객체 처리 시간을 실제로 측정하는 오버헤드를 피한다.

관련 매개변수는 최대 버퍼 크기와 버퍼를 채우기 위한 낮은 임계값·높은 임계값이다. 최대 길이는 256, 낮은 임계값은 8, 높은 임계값은 16으로 설정한다.

이 매개변수는 다음처럼 사용한다. 버퍼가 최대 크기에 도달하면 참조를 따라가며 새로 찾은 객체 포인터를 버퍼 대신 스택에 push한다. 버퍼에서 객체를 꺼내다가 현재 길이가 낮은 임계값 아래로 내려가면 버퍼를 “prime”한다. priming은 스택에서 객체를 pop하여 버퍼에 넣는다는 뜻이다. 이때 버퍼는 높은 임계값에 이를 때까지만 채운다.

> **해설 — 256, 8, 16이 서로 다른 역할을 한다**
>
> 256은 순간적으로 버퍼가 커질 수 있는 상한이다. 8 아래로 내려가면 보충을 시작하고 16에서 멈춘다. 낮은 값 하나만 기준으로 쓰지 않고 두 임계값 사이에 여유를 두면 항목 하나가 드나들 때마다 보충을 반복하는 현상을 줄일 수 있다.

버퍼의 효과를 측정하기 위해 몇 가지 벤치마크 프로그램을 prefetch와 메모리 접근 명령의 추적 로그를 남기며 실행했다. 처리한 각 객체의 prefetch window를 이 로그에서 계산했다. enqueue와 dequeue 연산은 각각 시간 1단위를 소비한다고 보았고, 객체 자체의 처리 시간은 0이라고 가정했다.

아래는 window의 히스토그램이다. 이 추적 결과에 따르면 버퍼 길이는 대부분 원하는 대로 낮은 임계값과 높은 임계값 사이에 유지된다. 버퍼 매개변수의 여러 조합을 벤치마크한 뒤 성능이 가장 좋은 값을 선택했다. 물론 이 매개변수가 모든 하드웨어와 프로그램에서 최적일 가능성은 낮다.

```
Prefetch window stats
mean 52.1
median 14.0
max 256
   25.60 |65,304  | ******************************
   51.20 |5,590   | **
   76.80 |3,562   | *
  102.40 |2,683   | *
  128.00 |2,278   | *
  153.60 |2,285   | *
  179.20 |2,377   | *
  204.80 |2,238   | *
  230.40 |2,753   | *
  256.00 |5,930   | **
-------- |------- | -------
      N= |95,000
```

소프트웨어 prefetch 명령은 GC가 검사하는 객체 집합이 CPU 캐시에 들어가지 않을 때에만 이득이다. 그렇지 않다면 버퍼와 prefetch 명령 자체가 오버헤드일 뿐이다. 장수 객체 수는 데이터가 캐시에 들어갈지를 추정하는 좋은 값으로 보인다. 64비트 플랫폼에서 최소 객체 크기는 32바이트다. 4MB L2 캐시에는 약 130,000개 객체가 들어간다.

현재 prefetch 활성화 임계값은 장수 객체 200,000개 초과다. 벤치마크 결과 이 부근부터 prefetch가 순이익을 내는 것으로 보인다. 물론 실제 결과는 하드웨어 세부 사항과 객체 그래프의 “모양”에 따라 달라진다.

예를 들어 객체 그래프를 만들 때 객체들이 메모리에 선형적으로 할당되었을 수 있다. 그러면 객체 그래프를 순회할 때 메모리도 대부분 순서대로 접근하게 된다. 이 경우 하드웨어 prefetcher만으로 거의 완벽하게 처리할 가능성이 높아 소프트웨어 prefetch 힌트가 필요하지 않다.

이 최적화는 2025년 3월 현재 다음 하드웨어 플랫폼에서 튜닝되었다.

- Apple M3 Pro, 32 GB RAM, 192+128 KB L1, 16 MB L2, Clang 19로 컴파일
- AMD Ryzen 5 7600X, 64 GB RAM, 384 KB L1, 6 GB L2, 32 MB L3, GCC 12.2.0으로 컴파일

> **해설 — 원문 단위 확인 필요**
>
> 원문의 `6 GB L2`를 그대로 보존했다. 그러나 [AMD의 Ryzen 5 7600X 공식 사양](https://www.amd.com/en/support/downloads/drivers.html/processors/ryzen/ryzen-7000-series/amd-ryzen-5-7600x.html)은 L2 캐시를 `6 MB`로 제시한다. 따라서 원문의 `GB`는 `MB`의 오타로 판단할 강한 근거가 있지만, 이 번역에서는 원문 값 자체를 조용히 교정하지 않았다.

이 최적화의 효과를 벤치마크하기는 특히 어렵다. CPU 캐시 크기와 메모리 지연 시간 같은 하드웨어 세부 사항뿐 아니라, 객체가 메모리 어디에 있고 mark alive 단계에서 어떤 순서로 접근하는지를 포함한 프로그램의 메모리 접근 패턴에도 결과가 좌우되기 때문이다.

프로그램의 메모리 접근 패턴이 prefetch에 유리한 경우, 즉 작업 데이터 집합이 CPU 캐시보다 크고 객체가 선형적이지 않은 접근 순서를 만들도록 할당된 경우에는 소프트웨어 prefetch를 사용하여 전체 완전 GC 컬렉션 속도를 20%에서 40%까지 높일 수 있다.

### 최적화: 메모리 절약을 위한 필드 재사용

메모리를 아끼기 위해 GC를 지원하는 모든 객체의 두 연결 리스트 포인터를 여러 용도로 재사용한다. 이것은 “fat pointer” 또는 “tagged pointer”라고 알려진 일반적인 최적화다. 포인터가 추가 데이터를 함께 운반하며, 그 데이터를 주소를 표현하는 비트 안에 “접어 넣어” 인라인으로 저장하는 방식이다. 메모리 주소 지정의 특정 성질을 이용한다.

대부분의 아키텍처는 특정 데이터 타입을 그 데이터의 크기, 흔히 한 word 또는 그 배수에 맞추어 정렬한다. 이 정렬 때문에 포인터의 최하위 비트 몇 개는 사용되지 않고 남는다. 메모리에 접근하기 전에 코드가 이 비트들을 마스킹하여 제거하기만 한다면, 남는 비트를 태그나 다른 정보에 사용할 수 있다. 가장 흔한 방식은 각 비트를 별도의 태그로 쓰는 비트 필드다.

예를 들어 주소와 word 크기가 모두 32비트인 아키텍처에서 한 word는 32비트, 즉 4바이트다. word 정렬 주소는 항상 4의 배수이므로 끝 두 비트가 `00`이고, 마지막 2비트를 사용할 수 있다. 64비트 아키텍처에서는 한 word가 64비트, 즉 8바이트이므로 word 정렬 주소가 `000`으로 끝나며 마지막 3비트를 사용할 수 있다.

> **해설 — 주소 정렬이 태그 공간을 만든다**
>
> 8바이트 경계에 놓인 객체의 주소는 이진수로 표현했을 때 하위 3비트가 항상 0이다. 실제 주소를 구할 때 이 비트가 필요하지 않으므로 상태 플래그를 잠시 넣을 수 있다. 단, 역참조 전에 반드시 `000`으로 되돌려야 한다.

CPython GC는 [메모리 배치와 객체 구조](#메모리-배치와-객체-구조) 절에서 설명한 `PyGC_Head`의 추가 필드에 해당하는 두 fat pointer를 사용한다.

> **경고**
>
> 추가 정보가 들어 있으므로 tagged pointer 또는 fat pointer를 그대로 역참조해서는 안 된다. 실제 메모리 주소를 얻기 전에 추가 정보를 반드시 제거해야 한다. 연결 리스트를 직접 조작하는 함수는 보통 리스트 안의 포인터가 일관된 상태라고 가정하므로, 이러한 함수에서는 특별히 주의해야 한다.

- `_gc_prev` 필드는 보통 이중 연결 리스트를 유지하는 “이전” 포인터로 사용하지만, 최하위 두 비트에는 `PREV_MASK_COLLECTING`과 `_PyGC_PREV_MASK_FINALIZED` 플래그를 저장한다. 컬렉션 사이에 존재할 수 있는 플래그는 `_PyGC_PREV_MASK_FINALIZED`뿐이며, 객체가 이미 finalization되었는지를 나타낸다. 컬렉션 중에는 `_gc_prev`를 두 플래그와 함께 참조 횟수의 복사본인 `gc_ref`를 저장하는 데 일시적으로 사용한다. `_gc_prev`가 복원될 때까지 GC 연결 리스트는 단일 연결 리스트가 된다.

- `_gc_next` 필드는 이중 연결 리스트를 유지하는 “다음” 포인터로 사용하지만, 컬렉션 중에는 최하위 비트에 `NEXT_MASK_UNREACHABLE` 플래그를 저장한다. 이 플래그는 순환 탐지 알고리즘에서 객체가 잠정적으로 도달 불가능한지를 나타낸다. 이는 부분집합을 이중 연결 리스트만으로 구현할 때 생기는 단점에 대응하는 장치다. 필요한 연산 대부분은 상수 시간에 처리할 수 있지만, 한 객체가 현재 어느 부분집합에 있는지를 효율적으로 알아낼 방법은 없다. 그래서 필요할 때 `NEXT_MASK_UNREACHABLE` 같은 임시 기법을 사용한다.

> **해설 — 같은 비트의 의미가 단계마다 달라진다**
>
> `_gc_prev`와 `_gc_next`는 평상시에는 리스트 포인터지만, GC가 리스트의 일부 기능만 필요로 하는 단계에서는 참조 횟수 복사본과 상태 플래그를 담는 작업 공간이 된다. 이 최적화가 앞서 말한 “객체 수에 비례하는 별도 메모리가 필요 없다”는 성질을 가능하게 한다.

### 최적화: 컨테이너 추적 해제 지연

일부 컨테이너 타입은 참조 순환에 참여할 수 없으므로 가비지 컬렉터가 추적할 필요가 없다. 이러한 객체의 추적을 해제하면 가비지 컬렉션 비용이 줄어든다. 그러나 어떤 객체의 추적을 해제해도 되는지 판정하는 작업도 공짜가 아니므로, 판정 비용과 GC에서 얻는 이득을 비교해야 한다. 컨테이너의 추적을 해제하는 시점에는 두 전략이 있다.

1. 컨테이너를 만들 때
2. 가비지 컬렉터가 컨테이너를 검사할 때

일반적으로 원자적 타입의 인스턴스는 추적하지 않고, 비원자적 타입의 인스턴스인 컨테이너와 사용자 정의 객체 등은 추적한다.

> **해설 — 여기서 “원자적”이라는 의미**
>
> 계산을 더 쪼갤 수 없다는 뜻이 아니라, GC가 따라가야 할 다른 Python 객체 참조를 내부에 담지 않는다는 뜻이다. 정수나 문자열만으로는 객체 참조 순환을 만들 수 없으므로 순환 GC 목록에 둘 필요가 없다.

불변 객체만 포함하는 튜플은 추적할 필요가 없다. 여기에는 정수, 문자열과 재귀적으로 불변 객체만 담은 튜플이 포함된다. 인터프리터는 매우 많은 튜플을 만들며, 그중 상당수는 가비지 컬렉션이 실행될 때까지 살아남지 않는다. 따라서 생성 시점에 추적 해제 가능한 튜플을 판정하는 것은 비용 대비 이득이 없다.

대신 빈 튜플을 제외한 모든 튜플은 생성할 때 추적한다. 가비지 컬렉션 중에 살아남은 튜플 가운데 추적을 해제할 수 있는 것이 있는지 판정한다. 튜플의 모든 내용물이 이미 추적 대상이 아닐 때 그 튜플도 추적 해제할 수 있다. 모든 가비지 컬렉션 주기에서 튜플의 추적 해제 가능성을 검사한다.

딕셔너리는 생성 시점부터 항상 추적하며, 가비지 컬렉터가 추적을 해제하지 않는다. 이전 버전인 3.13까지는 지연 추적을 사용했다. 비어 있거나 원자적 객체만 담은 딕셔너리는 생성할 때 추적하지 않았고, 추적할 수 있는 값을 삽입하면 `MAINTAIN_TRACKING`을 통해 다시 추적했다. 완전 컬렉션에서는 `_PyDict_MaybeUntrack`을 호출하여 값이 원자적 객체만 남은 딕셔너리를 추적 대상에서 제거했다.

이 장치는 3.14에서 제거되었다(GH-127010). 항목을 설정할 때마다 추적 불변 조건을 확인하는 비용이 완전 컬렉션에서 얻는 절감 효과보다 컸기 때문이다.

가비지 컬렉터 모듈은 객체의 현재 추적 상태를 반환하는 Python 함수 `is_tracked(obj)`를 제공한다. 이후의 가비지 컬렉션이 객체의 추적 상태를 바꿀 수 있다.

```pycon
>>> gc.is_tracked(0)
False
>>> gc.is_tracked("a")
False
>>> gc.is_tracked([])
True
>>> gc.is_tracked(())
False
>>> gc.is_tracked({})
True
>>> gc.is_tracked({"a": 1})
True
```

> **해설 — 추적 여부와 객체 수명은 별개다**
>
> “추적하지 않는다”는 참조 횟수 관리도 하지 않는다는 뜻이 아니다. 순환 가능성을 찾기 위한 GC 후보 목록에서 제외한다는 뜻이다. 참조 횟수가 0이 되면 추적 여부와 관계없이 일반 참조 횟수 관리로 해제된다.

### GC 구현의 차이

이 절은 기본 빌드의 GC 구현과 자유 스레딩 빌드의 구현이 어떻게 다른지 요약한다.

기본 빌드 구현은 `PyGC_Head` 자료 구조를 광범위하게 사용하지만, 자유 스레딩 빌드 구현은 이 자료 구조를 사용하지 않는다.

- 기본 빌드 구현은 `PyGC_Head`를 사용한 이중 연결 리스트에 추적 대상 객체를 모두 저장한다. 자유 스레딩 빌드 구현은 대신 내장된 mimalloc 메모리 할당자가 힙을 검사하여 추적 대상 객체를 찾게 한다.
- 기본 빌드 구현은 도달 불가능한 객체 리스트에도 `PyGC_Head`를 사용한다. 자유 스레딩 빌드 구현은 `ob_tid` 필드를 도달 불가능한 객체의 연결 리스트를 저장하는 용도로 바꿔 쓴다.
- 기본 빌드 구현은 플래그를 `PyGC_Head`의 `_gc_prev` 필드에 저장한다. 자유 스레딩 빌드 구현은 이 플래그들을 `ob_gc_bits`에 저장한다.

> **해설 — 자유 스레딩 빌드가 별도 GC 리스트를 유지하지 않는 이유**
>
> 기본 빌드처럼 모든 추적 객체를 하나의 전역 연결 리스트에 넣으면 여러 스레드의 객체 생성·파괴가 그 리스트를 동시에 수정해야 한다. 자유 스레딩 구현은 할당자가 이미 알고 있는 힙 배치를 이용해 객체를 찾고, 컬렉션 중 임시 상태는 객체 헤더 필드에 기록한다.

기본 빌드 구현은 스레드 안전성을 위해 [전역 인터프리터 잠금](https://docs.python.org/3/glossary.html#term-global-interpreter-lock)에 의존한다. 자유 스레딩 빌드 구현에는 두 번의 “stop the world” 일시 중지가 있다. 이 구간에는 GC가 참조 횟수와 객체 속성에 안전하게 접근할 수 있도록 실행 중인 다른 모든 스레드를 잠시 멈춘다.

기본 빌드 구현은 세대별 컬렉터다. 자유 스레딩 빌드는 세대별 컬렉터가 아니며, 컬렉션마다 전체 힙을 검사한다.

- 기본 빌드에서는 객체 세대를 추적하기가 단순하고 비용이 적다. 자유 스레딩 빌드는 추적 대상 객체를 찾는 데 mimalloc을 사용하므로, 전체 힙을 검사하지 않고 “젊은” 객체만 식별하기가 더 어렵다.

> **해설 — 두 번의 stop-the-world**
>
> 자유 스레딩 실행 전체가 항상 멈춘다는 뜻은 아니다. GC 알고리즘 중 일관된 전역 스냅샷이 필요한 두 구간에 한해 다른 스레드를 멈춘다. 대신 각 컬렉션이 전체 힙을 검사하므로, 앞서 설명한 mark-alive 제외와 prefetch 최적화가 중요해진다.

> **참고**
>
> **문서 이력**
>
> Pablo Galindo Salgado - 원저자
>
> Irit Katriel - Markdown으로 변환

---

## 제4부: 예외 처리

> 원문: [CPython 3.14 `InternalDocs/exception_handling.md`](https://github.com/python/cpython/blob/3.14/InternalDocs/exception_handling.md)

### 예외 처리 개요

Python은 “비용 제로(zero-cost)” 예외 처리라는 기법을 사용하여
예외 지원에 드는 비용을 최소화한다. 예외가 발생하지 않는 일반적인
경우에는 그 비용을 0 또는 0에 가까운 수준으로 줄인다. 예외를 실제로
발생시키는 비용은 늘어나지만, 큰 폭으로 늘어나지는 않는다.

> **해설 — 무엇의 비용이 제로인가**
>
> 예외 객체를 만들고 호출 스택을 되감는 작업이 공짜라는 뜻이 아니다.
> `try` 블록이 있어도 예외가 발생하지 않는 정상 경로에서는 매
> 명령마다 별도의 예외 처리 상태를 조작하지 않도록 한다는 뜻이다.
> 드문 예외 경로가 더 많은 일을 맡는 대신 흔한 정상 경로를 빠르게
> 유지한다.

다음 코드를 보자.

```python
try:
    g(0)
except:
    res = "fail"
```

이 코드는 대략 다음과 같은 중간 코드로 컴파일된다.

```text
                  RESUME                   0

     1            SETUP_FINALLY            8 (to L1)

     2            LOAD_NAME                0 (g)
                  PUSH_NULL
                  LOAD_CONST               0 (0)
                  CALL                     1
                  POP_TOP
                  POP_BLOCK

    --   L1:      PUSH_EXC_INFO

     3            POP_TOP

     4            LOAD_CONST               1 ('fail')
                  STORE_NAME               1 (res)
```

`SETUP_FINALLY`와 `POP_BLOCK`은 의사 명령어다. 즉, 중간 코드에는
나타날 수 있지만 실제 바이트코드 명령어는 아니다.

`SETUP_FINALLY`는 그 지점부터 발생하는 예외를 레이블 `L1`의 코드가
처리한다고 지정한다. `POP_BLOCK`은 마지막 `SETUP` 명령의 효과를
되돌려 활성 예외 처리기를 그 전 상태로 복구한다.

> **해설 — 의사 명령어는 컴파일용 경계 표시다**
>
> 컴파일러는 `try`가 보호하는 범위의 시작과 끝을
> `SETUP_FINALLY`와 `POP_BLOCK`으로 쉽게 표현한다. 최종 조립
> 단계에서는 이 두 명령을 실행 가능한 opcode로 남기지 않고, 그
> 사이의 범위를 예외 테이블 항목으로 옮긴다. 소스의 구조를 먼저
> 명령 형태로 표시한 뒤 최종 메타데이터로 낮추는 과정이다.

예외가 발생하지 않으면 `SETUP_FINALLY`와 `POP_BLOCK`은 아무 효과도
내지 않는다. 비용 제로 예외 처리의 핵심은 이 의사 명령어들을
바이트코드 옆에 저장해 두었다가 예외가 발생할 때만 조사하는
메타데이터로 바꾸는 것이다.

이 메타데이터가 **예외 테이블**이며 코드 객체의
`co_exceptiontable` 필드에 저장된다.

의사 명령어를 바이트코드로 변환할 때 `SETUP_FINALLY`와
`POP_BLOCK`은 제거된다. 동시에 각 명령어를 그 명령어를 감싸는
예외 처리기에 대응시키는 예외 테이블을 만든다. 같은 코드 객체의
바이트코드 안에 있는 어떤 예외 처리기도 보호하지 않는 명령어는
예외 테이블에 아예 나타나지 않는다.

앞의 예제 코드 객체에는 항목이 하나뿐이다. 이 항목은
`SETUP_FINALLY`와 `POP_BLOCK` 사이에 있던 모든 명령어를 레이블
`L1`의 예외 처리기가 보호한다고 지정한다.

> **해설 — 정상 경로에는 테이블 조회가 없다**
>
> `try` 영역을 실행하는 동안 매번 “현재 처리기는 L1”이라는 값을
> 푸시하거나 팝하지 않는다. 예외가 생겼을 때만 현재 명령어
> 오프셋으로 `co_exceptiontable`을 검색한다. 이것이 정상 실행
> 경로의 추가 비용을 거의 없애는 핵심이다.

### 예외 처리

런타임에서 예외가 발생하면 인터프리터는
[`Python/ceval.c`](https://github.com/python/cpython/blob/3.14/Python/ceval.c)의
`get_exception_handler()`를 호출하여 현재 명령어의 오프셋을 예외
테이블에서 찾는다.

처리기를 찾으면 제어 흐름을 그 위치로 옮긴다. 찾지 못하면 예외가
호출자에게 전파되고, 호출자 프레임에서 `CALL` 명령어를 보호하는
처리기를 다시 찾는다. 처리기를 찾거나 최상위 프레임에 도달할 때까지
이 과정을 반복한다.

처리기를 끝내 찾지 못하면 인터프리터 함수
`_PyEval_EvalFrameDefault()`가 `NULL`을 반환한다. 스택을 되감는
동안 각 프레임은
[`Python/traceback.c`](https://github.com/python/cpython/blob/3.14/Python/traceback.c)의
`PyTraceBack_Here()`에 의해 트레이스백에 추가된다.

> **해설 — 두 종류의 되감기**
>
> 먼저 현재 프레임 안에서 예외 테이블을 검색한다. 현재 함수의
> `try`가 잡을 수 없으면 그 프레임을 빠져나가 호출자의 `CALL`
> 위치에서 다시 검색한다. 이 프레임 단위의 반복이 stack
> unwinding이다. 각 프레임을 버리기 전에 그 위치를 트레이스백에
> 기록하므로 사용자는 예외가 전파된 호출 경로를 볼 수 있다.

예외 테이블의 각 항목에는 처리기 위치 외에도 `try` 명령어 시점의
스택 깊이와 `lasti` 불리언 값이 들어 있다. `lasti`는 예외를
발생시킨 명령어의 오프셋을 스택에 푸시해야 하는지를 나타낸다.

예외 테이블 항목을 찾은 뒤 예외를 처리하는 과정은 다음과 같다.

1. 스택 깊이가 해당 처리기에 기록된 값과 같아질 때까지 값을
   팝한다.
2. `lasti`가 참이면 예외가 발생한 오프셋을 푸시한다.
3. 예외를 스택에 푸시한다.
4. 대상 오프셋으로 점프하여 실행을 재개한다.

> **해설 — 왜 스택 깊이를 복구하는가**
>
> 예외는 표현식 계산 도중에도 발생할 수 있으므로 평가 스택에
> 피연산자나 중간 결과가 남아 있을 수 있다. 처리기는 자신이
> 컴파일될 때 가정한 스택 배치에서 시작해야 한다. 예외 테이블에
> 저장한 깊이까지 불완전한 계산값을 버린 뒤 예외와 필요한 위치
> 정보를 정해진 순서로 올린다.

### 예외를 다시 발생시키는 경우와 `lasti`

`lasti`를 스택에 푸시하는 목적은 예외를 다시 발생시킬 때 그 예외를
처음 발생시킨 명령어와 연결해야 하는 경우를 처리하기 위해서다.

예를 들어 `finally` 블록이 끝날 때 처리 중이던 예외를 계속
전파해야 하는 경우가 이에 해당한다. 이때 프레임의 명령어 포인터는
이미 `finally` 블록 안을 가리킨다. 따라서 `RERAISE` 명령어는
`oparg > 0`이면 스택의 `lasti` 값으로 명령어 포인터를 되돌린다.

> **해설 — 처리 위치와 발생 위치를 분리한다**
>
> `finally`를 실행하는 동안 현재 명령어 위치는 당연히 `finally`
> 내부로 이동한다. 이 상태에서 단순히 다시 예외를 올리면 원래 어느
> 명령에서 문제가 생겼는지 잃을 수 있다. 별도로 보존한 `lasti`를
> 사용해 트레이스백과 디버깅에 필요한 최초 발생 위치를 복구한다.

### 예외 테이블의 형식

개념적으로 예외 테이블은 다음 5-튜플이 이어진 구조다.

1. `start-offset`: 포함되는 시작점
2. `end-offset`: 포함되지 않는 끝점
3. `target`
4. `stack-depth`
5. `push-lasti`: 불리언

모든 오프셋과 길이는 바이트가 아니라 code unit 단위다.

> **해설 — 반열린 범위와 code unit**
>
> `[start, end)`는 `start`는 포함하고 `end`는 포함하지 않는 반열린
> 범위다. 인접한 범위를 겹치지 않게 표현하기 쉽다. code unit은
> CPython이 바이트코드 명령과 캐시를 배치할 때 사용하는 내부
> 단위이며, 이 문서의 뒤 설명대로 하나가 2바이트를 차지한다.

예외 테이블 형식은 작으면서도 빠르게 검색할 수 있어야 한다.

작은 형식을 만들려면 항목의 크기를 가변적으로 하여 흔히 나타나는
작은 오프셋은 작게 저장하면서도 필요하면 큰 오프셋도 처리할 수
있어야 한다.

빠르게 검색하려면 모든 경우에 `log(n)` 성능을 내는 이진 검색을
지원해야 한다. 이진 검색은 보통 고정 크기 항목을 전제로 하지만,
항목의 시작을 식별할 수만 있다면 반드시 그럴 필요는 없다.

> **해설 — 가변 길이 항목을 찾는 표식**
>
> 항목마다 필요한 바이트 수는 달라도 첫 바이트를 구별하는 비트가
> 있다면 임의 위치 근처에서 항목 경계를 찾을 수 있다. 이 경계
> 정보와 정렬된 시작 오프셋을 이용해 모든 항목을 앞에서부터
> 순차적으로 해석하지 않고 검색할 수 있다.

크기 `end - start`는 언제나 `end`보다 작다. 따라서 항목은 다음
순서로 인코딩한다.

```text
start, size, target, depth, push-lasti
```

또한 코드 길이는 `2**31`을 넘을 수 없고 code unit 하나가 2바이트를
차지하므로, 크기는 `2**30`으로 제한된다. `depth`는 일반적으로
상당히 작다.

따라서 다음 값들을 인코딩해야 한다.

```text
start   (최대 30비트)
size    (최대 30비트)
target  (최대 30비트)
depth   (대략 최대 8비트)
lasti   (1비트)
```

항목의 시작을 나타내는 표식이 필요하므로 각 항목의 첫 바이트는
최상위 비트를 1로 설정한다.

최상위 비트를 항목 시작 표시에 사용하므로 오프셋을 인코딩하는 데는
바이트당 7비트를 사용할 수 있다. 인코딩은 표준 varint 방식과
같지만, 보통의 8비트 대신 7비트만 사용한다.

한 바이트의 8비트를 최상위 비트부터 쓰면 `SXdddddd`다. `S`는 시작
비트이고 `X`는 해당 오프셋을 확장하려면 다음 바이트가 필요하다는
확장 비트다.

> **해설 — 실제 값은 한 바이트당 6비트씩 들어간다**
>
> 원문에서 “오프셋 인코딩에 7비트”라고 한 것은 시작 비트 `S`를
> 제외한 영역 전체를 가리킨다. 그 7비트 중 하나는 계속 여부를
> 나타내는 `X`이므로 실제 숫자 조각은 `dddddd`, 즉 6비트다.
> `S=1`이면 새 항목의 첫 바이트이고, `X=1`이면 같은 숫자의 다음
> 6비트 조각이 뒤따른다.

또한 `depth`와 `lasti`는 인코딩하기 전에
`((depth << 1) + lasti)`라는 하나의 값으로 합친다.

예를 들어 다음 예외 테이블 항목이 있다고 하자.

```text
start:              20
end:                28
target:             100
depth:              3
lasti:              False
```

먼저 더 간결한 네 값 형태로 바꾼다.

```text
start:              20
size:               8
target:             100
depth<<1+lasti:     6
```

그다음 다음과 같이 인코딩한다.

```text
148     (최상위 비트 + 시작값 20)
8       (크기)
65      (확장 비트 + 1)
36      (target의 나머지, 100 == (1<<6)+36)
6
```

전체 크기는 5바이트다.

> **해설 — 예제의 비트 계산**
>
> `148`은 `0b10010100`이므로 `S=1`, `X=0`, 데이터는 20이다.
> `target=100`은 6비트씩 나누어 상위 조각 1과 하위 조각 36으로
> 저장한다. 첫 조각의 확장 비트를 켜면 `64 + 1 = 65`가 되고, 다음
> 바이트 36을 합치면 `(1 << 6) + 36 = 100`이 된다. 마지막 6은
> `(3 << 1) + 0`으로, 스택 깊이 3과 거짓인 `lasti`를 함께 담는다.

예외 테이블을 만드는 코드는
[`Python/assemble.c`](https://github.com/python/cpython/blob/3.14/Python/assemble.c)의
`assemble_exception_table()`에 있다.

명령어 오프셋으로 테이블을 조회하는 인터프리터 함수는
[`Python/ceval.c`](https://github.com/python/cpython/blob/3.14/Python/ceval.c)의
`get_exception_handler()`다.

[`Lib/dis.py`](https://github.com/python/cpython/blob/3.14/Lib/dis.py)의
Python 함수 `_parse_exception_table()`은 예외 테이블 내용을
namedtuple 인스턴스의 리스트로 반환한다.

### 예외 연결 구현

[예외 연결](https://docs.python.org/dev/tutorial/errors.html#exception-chaining)은
예외를 발생시키는 동안 그 예외의 `__context__`와 `__cause__` 필드를
설정하는 것을 말한다.

`__context__` 필드는
[`Python/errors.c`](https://github.com/python/cpython/blob/3.14/Python/errors.c)의
`_PyErr_SetObject()`가 설정한다. 모든 `PyErr_Set*()` 함수는 결국 이
함수를 호출한다.

`__cause__` 필드, 즉 명시적 예외 연결은 `RAISE_VARARGS` 바이트코드가
설정한다.

> **해설 — `__context__`와 `__cause__`**
>
> 한 예외를 처리하던 중 다른 예외가 발생하면 CPython은 기존 예외를
> 새 예외의 `__context__`로 연결한다. `raise NewError() from
> original`처럼 사용자가 원인을 명시하면 그 예외가 `__cause__`가
> 된다. 둘 다 트레이스백에서 예외 사이의 관계를 설명하지만,
> `__cause__`는 코드가 의도적으로 지정한 연결이라는 차이가 있다.
