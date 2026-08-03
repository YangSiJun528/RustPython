# 이름 분류가 저장소와 opcode를 정한다

Python은 일반 이름을 찾으려고 호출자 Frame을 차례로 올라가지 않는다.
컴파일러가 코드 블록 전체를 살펴 이름을 local·cell·free·global로 분류하면,
바이트코드는 현재 Frame 슬롯, 공유 cell, globals·builtins, locals 매핑 중
한 경로를 택한다. 어느 경로를 쓸지는 컴파일할 때 정해진다. 그곳에 담긴
객체만 실행 중에 달라진다.

![렉시컬 이름 조회와 호출자 Frame 체인은 다른 경로다](../assets/05-name-resolution-and-frame-chain.png)

## 같은 이름도 코드 블록에 따라 분류가 달라진다

```python
tax = 10

def outer():
    rate = 2
    unused = 100

    def inner(price):
        result = price * rate + tax
        return result

    return inner
```

심볼 테이블은 이름이 등장한 한 줄만 보지 않는다. 함수 전체의 대입과
`global`·`nonlocal` 선언, 안쪽 렉시컬 코드 블록의 참조를 함께 분석한다.

| 이름을 보는 코드 | 분류 | 의미 |
|---|---|---|
| 모듈의 `tax` | 모듈 바인딩 | 모듈 네임스페이스에 저장한다. |
| `outer`의 `unused` | local | 현재 `outer` 호출에서만 쓰는 지역 이름이다. |
| `outer`의 `rate` | cell | 현재 함수의 local을 안쪽 코드와 공유한다. |
| `inner`의 `rate` | free | 바깥 렉시컬 영역의 cell을 받아 쓴다. |
| `inner`의 `price`, `result` | local | 현재 `inner` Frame의 지역 이름이다. |
| `inner`의 `tax` | implicit global | globals에서 찾고 없으면 builtins에서 찾는다. |

`global tax`는 함수 안의 이름을 global로 명시한다. `nonlocal rate`는 가장
가까운 바깥 함수의 cell 바인딩을 사용한다고 명시한다.

## CodeObject의 이름 표에는 현재 값이 없다

CPython 3.14.6에서 예제의 관련 필드는 이렇게 나뉜다.

```text
outer.__code__
  co_varnames = ('unused', 'inner')
  co_cellvars = ('rate',)

inner.__code__
  co_varnames = ('price', 'result')
  co_freevars = ('rate',)
  co_names    = ('tax',)
```

이 튜플에는 이름 문자열과 분류 결과만 들어 있다. `tax == 10`이나
`rate == 2` 같은 현재 바인딩은 없다. 심볼 테이블 객체 전체도 CodeObject에
남지 않고, 분석 결과만 이름 표와 opcode 선택에 반영된다.

공개 튜플이 항상 서로 배타적인 것도 아니다. 안쪽 코드가 캡처한
매개변수는 `co_varnames`와 `co_cellvars` 양쪽에 나타날 수 있다.

## opcode 계열마다 실제 저장소가 다르다

| 코드 블록과 분류 | 읽기 | 쓰기와 실제 저장소 |
|---|---|---|
| 최적화된 함수 local | `LOAD_FAST*` | `STORE_FAST`, 현재 Frame의 locals-plus 슬롯 |
| cell·free | `LOAD_DEREF` | `STORE_DEREF`, 공유 cell의 내용 |
| 함수의 global·builtin 후보 | `LOAD_GLOBAL`: globals → builtins | `STORE_GLOBAL`, globals에만 저장 |
| 모듈·클래스의 일반 매핑 기반 이름 | `LOAD_NAME`: locals → globals → builtins | `STORE_NAME`, 현재 locals에만 저장 |

읽기 명령에는 정해진 fallback 순서가 있을 수 있다. 쓰기 명령은 그 순서를
거슬러 기존 이름을 찾지 않는다. `STORE_GLOBAL`은 builtins에 같은 이름이
있어도 globals에 저장한다. 일반 함수의 `LOAD_FAST*` 역시 `frame.f_locals`
매핑에서 문자열 키를 검색하지 않고 정해진 슬롯을 읽는다.

`co_names`는 global 전용 표가 아니다. `LOAD_ATTR`이나 import 관련 명령이
쓸 문자열도 들어갈 수 있다. `obj.name`은 객체의 속성 조회 규칙을
사용하므로 locals → globals → builtins 경로와 다르다.

CPython 3.14의 raw 인자는 단순한 공개 튜플 인덱스가 아닐 수 있다.
`LOAD_GLOBAL n`은 이름을 `co_names[n >> 1]`에서 얻는다.
`LOAD_DEREF 2`의 `2`도 `co_freevars[2]`가 아니라 locals-plus 슬롯 2다.
정확한 인자 형식은 [CodeObject와 바이트코드 참조](../reference/code-object-and-bytecode.ko.md)에서
따로 정리한다.

## cell과 free는 같은 바인딩을 보는 두 관점이다

`outer`가 보는 `rate`는 cell variable이고, `inner`가 보는 `rate`는 free
variable이다. 값을 두 벌로 복사하지는 않는다.

```text
outer Frame의 rate 슬롯 ─→ cell ─→ 정수 객체 2
                                  ↑
inner.__closure__[0] ─────────────┤
                                  ↑
inner Frame의 free 슬롯 ──────────┘
```

`outer`의 `MAKE_CELL`은 cell 슬롯을 준비한다. 이때 만들어진 `inner` 함수
객체는 그 cell 참조를 `__closure__`에 보관한다. `inner`를 호출하면
`COPY_FREE_VARS 1`이 같은 cell 참조를 새 Frame의 free-variable 슬롯에
복사한다. 바깥 Frame을 다시 찾는 단계는 없다.

그래서 `outer` 실행이 끝난 뒤에도 `inner(5)`는 `rate == 2`를 읽는다.
cell의 수명은 종료된 Frame이 아니라 남아 있는 참조로 결정된다.

## 호출자 Frame 연결은 실행을 되돌리기 위한 관계다

```python
def caller():
    value = 100
    return callee()

def callee():
    return value
```

`callee`의 `value`는 global 후보로 컴파일된다. `callee`의 globals와
builtins에 없으면 `NameError`가 발생한다. `caller`의 지역 슬롯까지
올라가서 `100`을 찾지 않는다.

Frame에서 caller로 향하는 연결은 함수 반환, 예외 전파, traceback,
debugger·profiler·`inspect`에 쓰인다. 렉시컬 이름 조회는 이 실행 관계와
별개로 작동한다.

심볼 테이블이 분류를 만드는 과정은
[소스에서 CodeObject까지](source-to-code-object.ko.md), Frame의 역할은
[실행 설계와 호출 상태](execution-model.ko.md)에서 이어진다. 더 자세한
원문 대응 설명은 [기존 컴파일에서 실행까지 문서](../../../cpython-internals-notes/3.14/compilation-to-execution/README.ko.md#8-이름-분류네임스페이스와-호출-스택은-서로-다른-경로다)에
남아 있다.

[가이드 홈](../README.ko.md) · 이전: [실행 설계와 호출 상태](execution-model.ko.md) · 다음: [평가 루프와 세 가지 스택](evaluation-loop.ko.md)
