# CPython은 관찰한 실행을 특수화된 opcode와 JIT trace로 바꾼다

컴파일러는 `obj.attr`의 실제 객체 타입이나 전역 이름이 어느 딕셔너리에 있을지
미리 알 수 없으므로 범용 바이트코드를 만든다. CPython의 적응형 인터프리터는
실행 중 반복되는 경우를 관찰해 opcode 하나를 더 좁고 빠른 형태로 특수화한다.
guard가 관찰 당시의 가정을 확인하므로 가정이 깨지면 범용 경로로 돌아갈 수
있다.

JIT는 같은 생각을 연속된 명령 경로로 넓힌다. 뜨거운 바이트코드 trace를 더 작은
uop 시퀀스로 바꾸고 여러 명령에 걸쳐 최적화한 뒤, uop 인터프리터나 네이티브
코드로 실행한다. opcode 특수화와 JIT는 별개 계층이지만 둘 다 관찰한 실행에만
비용을 쓴다. JIT의 `_DEOPT`나 차가운 출구는 기본 인터프리터로 돌아가고, 뜨거워진
side exit는 다른 executor로 이어질 수도 있다.

## 같은 CodeObject를 두 가지 `dis` 보기로 관찰한다

전역 정수와 인수를 더하는 함수는 이름 조회와 산술 specialization을 함께 보여
준다.

```python
GLOBAL_VALUE = 10

def hot(x):
    return GLOBAL_VALUE + x
```

CPython 3.14.6에서 확인한 CodeObject 값은 다음과 같다.

```text
co_names=('GLOBAL_VALUE',)
co_varnames=('x',)
co_consts=(None,)
co_stacksize=2
```

실행하기 전 `dis.dis(hot, adaptive=True, show_caches=True)`는 아직 범용 명령과
초기 cache를 보여 준다.

```text
RESUME                   0
LOAD_GLOBAL              0 (GLOBAL_VALUE)
CACHE                    0 (counter: 17)
CACHE                    0 (index: 0)
CACHE                    0 (module_keys_version: 0)
CACHE                    0 (builtin_keys_version: 0)
LOAD_FAST_BORROW         0 (x)
BINARY_OP                0 (+)
CACHE                    0 (counter: 17)
CACHE                    0 (descr: 0)
CACHE                    0
CACHE                    0
CACHE                    0
RETURN_VALUE
```

`hot(1)`을 20,000번 호출한 같은 프로세스에서 `adaptive=False`로 보면 여전히
논리적인 원래 명령열이 나온다.

```text
RESUME
LOAD_GLOBAL       0 (GLOBAL_VALUE)
CACHE             0 (counter: 0)
... 세 개의 LOAD_GLOBAL cache ...
LOAD_FAST_BORROW  0 (x)
BINARY_OP         0 (+)
CACHE             0 (counter: 0)
... 네 개의 BINARY_OP cache ...
RETURN_VALUE
```

반면 `adaptive=True`는 실행 중 바뀐 명령과 실제 cache 값을 보여 줬다.

```text
RESUME_CHECK             0
LOAD_GLOBAL_MODULE       0 (GLOBAL_VALUE)
CACHE                    0 (counter: 832)
CACHE                    0 (index: 54)
CACHE                    0 (module_keys_version: 0)
CACHE                    0 (builtin_keys_version: 10)
LOAD_FAST_BORROW         0 (x)
BINARY_OP_ADD_INT        0 (+)
CACHE                    0 (counter: 832)
CACHE                    0 (descr: 0)
CACHE                    0
CACHE                    0
CACHE                    0
RETURN_VALUE
```

`index=54`와 version 값은 이 실행의 module·builtins 딕셔너리 배치에서 나온
관찰값이다. 다른 프로세스에서도 같은 숫자가 나온다는 보장은 없다. 중요한
사실은 `co_names`가 그대로인 상태에서 내부 실행 명령이
`LOAD_GLOBAL_MODULE`, `BINARY_OP_ADD_INT`로 좁아졌다는 점이다.

`adaptive=False`는 specialization을 끄거나 cache를 초기화하지 않는다. CodeObject가
가진 논리적 바이트코드를 표시한다. `adaptive=True`가 quickened 명령열과 live
cache를 보여 준다. 두 출력이 다르다고 CodeObject나 함수 객체가 새로
생겼다고 해석하면 안 된다.

## opcode 하나는 관찰을 거쳐 빠른 형태로 바뀐다

특수화는 네 단계를 거친다.

```text
generic → adaptive 관찰 → specialized
   ↑                           │
   └──────── guard 실패 ───────┘
              deopt
```

이 그림의 `adaptive`는 관찰 단계를 가리키는 개념 이름이다. CPython 3.14에서
반드시 별도의 `*_ADAPTIVE` opcode가 있다는 뜻은 아니다. 대개 instruction family의
범용 명령 자체가 counter와 특수화 진입점을 가진다.

generic 명령은 가능한 모든 Python 값을 처리한다. adaptive 단계에서는 inline
cache의 counter가 특수화를 시도할 시점을 정한다. counter가 trigger에 도달하면
specializer가 그때의 operand·타입·딕셔너리 상태를 검사하고, 성공한 빠른 경로에
필요한 guard·index·version 데이터를 cache에 쓴다. 임의의 과거 실행 표본을 계속
쌓아 두는 profiling 표로 이해하면 안 된다.

`LOAD_GLOBAL`을 예로 들면 이름은 module globals에 있을 수도 있고 builtins에
있을 수도 있다. 반복 실행에서 module 딕셔너리의 같은 항목을 계속 읽는다면
딕셔너리 key 구조의 version과 찾은 index를 cache에 저장하고
`LOAD_GLOBAL_MODULE` 같은 빠른 경로를 사용할 수 있다. 다음 실행의 guard가
version을 확인하므로 key 구조가 바뀌지 않았다면 hash와 이름 탐색을 반복하지
않는다.

specialized 명령도 Python의 동적 변경을 무시할 수는 없다. 타입이나 딕셔너리
구조가 달라져 guard가 실패하면 de-optimize하여 더 일반적인 명령으로 돌아간다.
빠른 명령이 틀린 결과를 내는 대신, 가정이 유효한 동안만 검사를 줄이는 구조다.

instruction family의 구성원은 같은 수의 inline cache entry를 차지한다. 실행 중
opcode가 바뀌어도 뒤 명령의 위치와 점프 거리가 변하지 않아야 하기 때문이다.

두 실행 형태가 Frame에 주는 의미상 효과는 같다.

| 명령 단계 | 범용 실행 | 특수화 실행 | 평가 스택 |
|---|---|---|---|
| 전역 읽기 | `LOAD_GLOBAL`이 이름을 조회한다 | `LOAD_GLOBAL_MODULE`이 guard 뒤 cached index를 쓴다 | `[] → [10]` |
| 지역 읽기 | `LOAD_FAST_BORROW` | 같은 명령 | `[10] → [10, x]` |
| 덧셈 | `BINARY_OP`이 일반 숫자 protocol을 쓴다 | `BINARY_OP_ADD_INT`가 두 정확한 int를 확인한다 | `[10, x] → [10+x]` |
| 반환 | `RETURN_VALUE` | 같은 명령 | 결과를 호출자 Frame으로 전달 |

specialization은 지역 슬롯, 평가 스택, 반환값의 의미를 바꾸지 않는다. 그
값을 얻기까지 거치는 검사와 탐색을 줄인다. 전역 cache도 `GLOBAL_VALUE`가 항상
10이라고 가정하는 것이 아니다. 딕셔너리 구조와 cached index가 유효한지 확인한
뒤 그 위치의 현재 값을 읽는다.

guard miss가 한 번 났다고 specialized opcode를 즉시 지우는 것도 아니다. 위와
같이 int로 예열한 뒤 `hot(1.5)`를 한 번 호출했더니 결과는 `11.5`였고,
`BINARY_OP_ADD_INT`의 counter만 `832`에서 `816`으로 줄었다. 이 실행은 int 전용
경로를 벗어나 일반 의미로 계산했지만 명령은 다음 관찰을 위해 남았다. miss가
쌓이면 deoptimize하거나 다른 형태로 다시 특수화할 수 있다.

## JIT는 여러 명령의 반복 경로를 한꺼번에 본다

opcode 특수화는 한 명령 안의 빠른 경우를 찾는다. 그러나 앞 명령에서 확인한
타입 정보를 뒤 명령까지 이용하거나 여러 중간 검사를 함께 없애려면 더 긴 실행
단위가 필요하다. CPython 3.14의 실험적 JIT는 반복해서 실행된 trace를 그 단위로
사용한다.

대표적인 진입점은 반복문 끝의 뜨거운 `JUMP_BACKWARD`다. 실행 횟수가 임계값에
도달하면 옵티마이저가 현재 Frame과 명령 위치에서 trace를 만들고, 바이트코드를
uop 시퀀스로 펼친 뒤 분석한다. 준비된 executor는 CodeObject에 연결되고 이후
해당 지점에서 최적화된 경로로 들어간다.

```text
바이트코드 trace
    ↓ uop으로 펼치기
최적화된 uop 시퀀스
    ├─ uop 인터프리터에서 실행
    └─ JIT가 만든 네이티브 코드에서 실행
```

trace는 함수 전체나 모든 분기를 덮지 않는다. `_DEOPT`나 차갑거나 최적화하지 못한
출구는 적응형 인터프리터로 돌아간다. 반복해서 뜨거워진 side exit는 기존 executor나
새 executor에 연결되어 Tier 2 안에서 곧장 이어질 수도 있다.

경계를 실행 상태 관점에서 보면 다음과 같다.

```text
Tier 1의 현재 Frame·명령 위치·평가 스택
    ↓ 뜨거운 backedge에서 ENTER_EXECUTOR
같은 실행 상태를 입력으로 받는 uop trace
    ├─ _DEOPT·cold exit ─→ Tier 1이 이어받을 Frame·평가 스택
    └─ hot side exit ────→ 연결된 다른 executor
```

JIT가 별도의 Python Frame이나 다른 CodeObject 의미를 만드는 것은 아니다.
executor는 기존 CodeObject에 연결되고 trace 입구와 출구에서 같은 Frame 상태를
주고받는다. 이 계약이 있어야 최적화가 실패해도 일반 인터프리터가 정확한
바이트코드 위치에서 실행을 이어 갈 수 있다.

완전한 JIT는 미리 컴파일한 기계어 조각을 copy-and-patch해 trace별 네이티브
코드를 만든다. CPython 3.14에서는 실험적이며 안정적인 호환 규격이 아니다.

위 specialization 출력을 얻은 3.14.6 실행 환경에서는 다음 상태가 관찰됐다.

```text
sys._jit.is_available() -> True
sys._jit.is_enabled()   -> False
sys._jit.is_active()    -> False
```

JIT가 비활성화되어도 opcode specialization은 동작했다. 둘이 같은 기능의 다른
이름이 아니라는 직접적인 예다. `is_available()`은 이 빌드가 JIT 기능을 포함한다는
뜻이고, `is_enabled()`는 현재 프로세스에서 사용할 수 있게 설정됐는지를 말한다.
`is_active()`는 이 함수를 호출한 바로 그 순간 JIT code 안에서 실행 중인지에 관한
값이므로 일반 상태 확인 flag처럼 반복 사용하면 안 된다. `sys._jit` 자체가 CPython의
private·실험적 namespace이며, `is_active()`는 JIT 테스트와 디버깅 밖에서 사용하지
않는 편이 맞다.

inline cache의 필드, 특수화 통계, uop 생성 파일과 JIT stencil 생성 과정은 기존
[프로그램 실행 상세 노트](../../../cpython-internals-notes/3.14/program-execution/README.ko.md#특수화)에서
확인한다.

## 흔한 오해와 버전 경계

- inline cache의 `CACHE`는 독립적으로 실행할 Python opcode가 아니다. 앞 family가
  정한 형식으로 읽는 데이터 공간이다.
- `adaptive=False` 출력만 보고 specialization이 일어나지 않았다고 결론 내릴 수
  없다. live 실행 형태를 보려면 `adaptive=True`가 필요하다.
- specialized 이름은 정적 타입을 CodeObject에 확정했다는 뜻이 아니다. 매 실행의
  guard가 가정을 확인한다.
- JIT는 항상 함수 전체를 네이티브 코드로 만드는 전통적인 method JIT가 아니다.
  CPython 3.14은 관찰한 hot trace와 그 출구를 중심으로 구성한다.
- opcode deopt와 JIT trace exit는 범위가 다르다. `_DEOPT`는 일반 실행기가 이어
  받을 상태를 복구하고, hot side exit는 다른 executor로 연결될 수도 있다.

counter의 초기값과 감소 폭, specialized opcode 이름, cache 필드, JIT 진입 기준은
CPython 내부 정책이다. 여기의 숫자는 CPython 3.14.6 한 프로세스에서 확인한
값이며 build 옵션, workload, free-threaded 여부와 이후 버전에 따라 달라질 수
있다. 특히 JIT API와 executor 구조는 3.14에서 실험적이다.

---

[설명 문서 목록](README.ko.md)

기준 글:

- [평가 루프와 세 가지 스택](evaluation-loop.ko.md)

다른 갈래:

- [예외 처리](exceptions.ko.md)
- [제너레이터와 코루틴](generators-and-coroutines.ko.md)

관련 글:

- [CodeObject 필드와 바이트코드 인자](../reference/code-object-and-bytecode.ko.md)
